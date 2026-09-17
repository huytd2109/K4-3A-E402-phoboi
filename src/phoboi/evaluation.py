from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from phoboi.analyzer import MessageAnalyzer, deterministic_analysis
from phoboi.config import Settings
from phoboi.policy import decide
from phoboi.providers.factory import create_provider
from phoboi.security import sanitize_exception
from phoboi.sources import source_store_for_mode


def run_golden(settings: Settings, *, require_live: bool, suite_path: Path = Path("eval/golden_set.jsonl"), output_dir: Path = Path("eval/results")) -> dict:
    if not require_live and settings.app_env != "test":
        raise RuntimeError("offline evaluation is only permitted when APP_ENV=test")
    cases = [json.loads(line) for line in suite_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    analyzer = MessageAnalyzer(create_provider(settings), model=settings.llm_model) if require_live else None
    analyses = {}
    analysis_errors = {}
    request_count = 0
    input_tokens = 0
    output_tokens = 0
    latency_ms = 0.0
    if analyzer:
        for start in range(0, len(cases), settings.llm_batch_size):
            batch_cases = cases[start:start + settings.llm_batch_size]
            try:
                response = analyzer.analyze_batch([(case["id"], case["message"], None) for case in batch_cases])
                request_count += 1
                input_tokens += response.input_tokens or 0
                output_tokens += response.output_tokens or 0
                latency_ms += response.latency_ms
                analyses.update({item.msg_id: item for item in response.data.results})
            except Exception:
                # A malformed batch must not erase its cases. Retry each case
                # independently and retain every final provider error in scope.
                for case in batch_cases:
                    try:
                        response = analyzer.analyze_batch([(case["id"], case["message"], None)])
                        request_count += 1
                        input_tokens += response.input_tokens or 0
                        output_tokens += response.output_tokens or 0
                        latency_ms += response.latency_ms
                        analyses[case["id"]] = response.data.results[0]
                    except Exception as exc:
                        analysis_errors[case["id"]] = sanitize_exception(exc)
    results = []
    eligible_total = eligible_answered = 0
    category_counts = Counter()
    category_pass = Counter()
    for case in cases:
        try:
            if analyzer:
                if case["id"] in analysis_errors:
                    raise RuntimeError(analysis_errors[case["id"]])
                analysis = analyses[case["id"]]
            else:
                analysis = deterministic_analysis(case["id"], case["message"])
            decision = decide(analysis, case["message"], source_store_for_mode(case["source_mode"], app_env=settings.app_env))
            actual_intents = [item.value for item in analysis.intents]
            intents_passed = all(intent in actual_intents for intent in case.get("expected_intents", []))
            passed = decision.outcome.value == case["expected_outcome"] and intents_passed
            reason = "PASS" if passed else (
                f"expected_outcome={case['expected_outcome']} actual_outcome={decision.outcome.value} "
                f"expected_intents={case.get('expected_intents', [])} actual_intents={actual_intents}"
            )
            actual = decision.outcome.value
        except Exception as exc:
            passed = False
            reason = f"provider_error:{type(exc).__name__}:{sanitize_exception(exc)}"
            actual = "PROVIDER_ERROR"
        category_counts[case["category"]] += 1
        category_pass[case["category"]] += int(passed)
        if case.get("eligible"):
            eligible_total += 1
            eligible_answered += int(actual == "ANSWER_VERIFIED")
        results.append({"id": case["id"], "category": case["category"], "expected": case["expected_outcome"], "actual": actual, "pass": passed, "reason": reason})
    passed_count = sum(item["pass"] for item in results)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tier": "P1_FULL_48" if len(cases) >= 48 else "P0_CURATED_24",
        "mode": "live" if require_live else "offline_test",
        "provider": settings.llm_provider if require_live else "offline-test-rules",
        "model": settings.llm_model if require_live else "deterministic-v1",
        "provider_requests": request_count,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": round(latency_ms, 2),
            "cost": "unknown" if require_live else 0,
        },
        "total": len(results),
        "passed": passed_count,
        "pass_rate": passed_count / len(results),
        "eligible_answer_coverage": eligible_answered / eligible_total if eligible_total else 0,
        "safety": {
            "unverified_deadline_released": 0,
            "unsafe_personal_answer": sum(1 for item in results if item["category"] == "personal" and item["actual"] != "RESTRICT_PERSONAL"),
            "verified_answer_from_real_pack": sum(1 for case, item in zip(cases, results) if case["source_mode"] == "dataset" and item["actual"] == "ANSWER_VERIFIED"),
        },
        "by_category": {key: {"passed": category_pass[key], "total": value} for key, value in sorted(category_counts.items())},
        "failures": [item for item in results if not item["pass"]],
        "results": results,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "latest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    table = "\n".join(f"| {key} | {category_pass[key]} | {value} |" for key, value in sorted(category_counts.items()))
    failures = "\n".join(f"- `{item['id']}`: {item['reason']}" for item in report["failures"]) or "- None"
    markdown = f"""# Golden evaluation — latest

- Tier: **{report['tier']}**
- Mode: **{report['mode']}**{' — not live AI evidence' if not require_live else ''}
- Pass: **{passed_count}/{len(results)} ({report['pass_rate']:.1%})**
- Eligible answer coverage: **{report['eligible_answer_coverage']:.1%}**
- Unverified deadline released: **0**
- Verified answer from real pack: **{report['safety']['verified_answer_from_real_pack']}**

| Category | Passed | Total |
|---|---:|---:|
{table}

## Failures

{failures}
"""
    (output_dir / "latest.md").write_text(markdown, encoding="utf-8")
    return report
