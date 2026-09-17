from __future__ import annotations

import hashlib
import json
import platform
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from phoboi.analyzer import MessageAnalyzer, PROMPT_PATH, deterministic_analysis
from phoboi.config import Settings
from phoboi.dataset import baseline_characteristics, load_messages, sha256_file
from phoboi.models import Analysis, DatasetMessage, Outcome
from phoboi.policy import decide
from phoboi.providers.factory import create_provider
from phoboi.security import sanitize_exception
from phoboi.sources import RealDatasetSourceStore


def _chunks(items: list[DatasetMessage], size: int) -> Iterable[list[DatasetMessage]]:
    for index in range(0, len(items), size):
        yield items[index:index + size]


def _jsonl_append(path: Path, items: Iterable[dict]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        for item in items:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def _read_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    result = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            result.add(item.get("record_id", item["msg_id"]))
    return result


def _cache_key(dataset_hash: str, row: DatasetMessage, prompt_hash: str, provider: str, model: str) -> str:
    content_hash = hashlib.sha256(row.content.encode("utf-8")).hexdigest()
    raw = f"{dataset_hash}|{content_hash}|{prompt_hash}|{provider}|{model}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_cache(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    cache: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            cache[item["key"]] = item["analysis"]
    return cache


def run_batch(
    input_path: Path,
    settings: Settings,
    *,
    require_live: bool,
    resume: bool = False,
    run_id: str | None = None,
    runs_root: Path = Path("runs"),
) -> Path:
    if not require_live and settings.app_env != "test":
        raise RuntimeError("offline batch is only permitted when APP_ENV=test")
    rows = load_messages(input_path)
    human = [row for row in rows if not row.is_bot]
    bots = [row for row in rows if row.is_bot]
    dataset_hash = sha256_file(input_path)
    prompt_hash = sha256_file(PROMPT_PATH)
    mode = "live" if require_live else "offline_test"
    actual_run_id = run_id or f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{mode}"
    run_dir = runs_root / actual_run_id
    run_dir.mkdir(parents=True, exist_ok=resume)
    classifications_path = run_dir / "classifications.jsonl"
    errors_path = run_dir / "errors.jsonl"
    decisions_path = run_dir / "policy_decisions.jsonl"
    completed = (_read_ids(classifications_path) | _read_ids(errors_path)) if resume else set()

    provider_name = settings.llm_provider if require_live else "offline-test-rules"
    model_name = settings.llm_model if require_live else "deterministic-v1"
    manifest = {
        "run_id": actual_run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "live": require_live,
        "provider": provider_name,
        "model": model_name,
        "dataset_path": input_path.as_posix(),
        "dataset_sha256": dataset_hash,
        "prompt_sha256": prompt_hash,
        "batch_size": settings.llm_batch_size,
        "max_concurrency": settings.max_concurrency,
        "python": platform.python_version(),
        "expected_rows": {"total": len(rows), "human": len(human), "bot": len(bots)},
        "usage": {"input_tokens": 0 if not require_live else None, "output_tokens": 0 if not require_live else None, "cost": "unknown"},
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    reply_index: dict[str, DatasetMessage] = {}
    for row in rows:
        reply_index.setdefault(row.msg_id, row)
    provider = create_provider(settings) if require_live else None
    analyzer = MessageAnalyzer(provider, model=settings.llm_model) if provider else None
    cache_dir = runs_root / "_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "classifications.jsonl"
    cache = _load_cache(cache_path)
    cache_hits = 0
    live_response_count = 0
    total_latency = 0.0
    usage_input = 0
    usage_output = 0

    pending = [row for row in human if row.record_id not in completed]
    for batch in _chunks(pending, settings.llm_batch_size):
        try:
            analyses_by_id: dict[str, Analysis] = {}
            missing_rows: list[DatasetMessage] = []
            row_keys: dict[str, str] = {}
            for row in batch:
                key = _cache_key(dataset_hash, row, prompt_hash, provider_name, model_name)
                row_keys[row.record_id] = key
                cached = cache.get(key)
                if cached:
                    analyses_by_id[row.record_id] = Analysis.model_validate(cached).model_copy(update={"msg_id": row.record_id})
                    cache_hits += 1
                else:
                    missing_rows.append(row)
            new_analyses: list[Analysis]
            if analyzer and missing_rows:
                payload = []
                for row in missing_rows:
                    parent = reply_index.get(row.reply_to) if row.reply_to else None
                    payload.append((row.record_id, row.content, parent.content if parent else None))
                response = analyzer.analyze_batch(payload)
                if not response.live:
                    raise RuntimeError("live batch returned non-live response")
                new_analyses = response.data.results
                live_response_count += 1
                total_latency += response.latency_ms
                usage_input += response.input_tokens or 0
                usage_output += response.output_tokens or 0
            else:
                new_analyses = [deterministic_analysis(row.record_id, row.content) for row in missing_rows]
            cache_rows = []
            for analysis in new_analyses:
                analyses_by_id[analysis.msg_id] = analysis
                key = row_keys[analysis.msg_id]
                serialized = analysis.model_dump(mode="json")
                cache[key] = serialized
                cache_rows.append({"key": key, "analysis": serialized})
            if cache_rows:
                _jsonl_append(cache_path, cache_rows)
            analyses = [analyses_by_id[row.record_id] for row in batch]
            by_id = {row.record_id: row for row in batch}
            classification_rows = []
            for analysis in analyses:
                record = by_id[analysis.msg_id]
                dumped = analysis.model_dump(mode="json")
                dumped["record_id"] = record.record_id
                dumped["msg_id"] = record.msg_id
                classification_rows.append(dumped)
            _jsonl_append(classifications_path, classification_rows)
            decisions = [decide(analysis, by_id[analysis.msg_id].content, RealDatasetSourceStore()) for analysis in analyses]
            decision_rows = []
            for item in decisions:
                record = by_id[item.msg_id]
                dumped = item.model_dump(mode="json")
                dumped["record_id"] = record.record_id
                dumped["msg_id"] = record.msg_id
                decision_rows.append(dumped)
            _jsonl_append(decisions_path, decision_rows)
        except Exception as exc:
            safe_error = sanitize_exception(exc)
            _jsonl_append(errors_path, [{"record_id": row.record_id, "msg_id": row.msg_id, "error": safe_error, "batch_failed": True} for row in batch])

    bot_replies = defaultdict(list)
    for bot in bots:
        if bot.reply_to:
            bot_replies[bot.reply_to].append(bot)
    baseline = []
    for human_row in human:
        for bot in bot_replies.get(human_row.msg_id, []):
            baseline.append({"msg_id": human_row.msg_id, "bot_msg_id": bot.msg_id, **baseline_characteristics(bot.content)})
    (run_dir / "baseline_pairs.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in baseline), encoding="utf-8"
    )

    classified_ids = _read_ids(classifications_path)
    error_ids = _read_ids(errors_path)
    decisions = []
    if decisions_path.exists():
        decisions = [json.loads(line) for line in decisions_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    outcomes = Counter(item["outcome"] for item in decisions)
    intent_outcomes: dict[str, Counter] = defaultdict(Counter)
    for item in decisions:
        for intent in item["intents"]:
            intent_outcomes[intent][item["outcome"]] += 1
    rates_by_intent = {}
    for intent, counts in sorted(intent_outcomes.items()):
        total = sum(counts.values())
        rates_by_intent[intent] = {
            "total": total,
            "verified_answer_rate": counts[Outcome.ANSWER_VERIFIED.value] / total,
            "clarification_rate": counts[Outcome.CLARIFY.value] / total,
            "handoff_rate": sum(value for key, value in counts.items() if key.startswith("HANDOFF_")) / total,
        }
    metrics = {
        "rows": {"total": len(rows), "human": len(human), "bot": len(bots)},
        "processed": {"classified": len(classified_ids), "errors": len(error_ids), "covered": len(classified_ids | error_ids)},
        "coverage": len(classified_ids | error_ids) / len(human) if human else 1,
        "verified_answer_from_real_pack": outcomes[Outcome.ANSWER_VERIFIED.value],
        "outcomes": outcomes,
        "rates": {
            "verified_answer_rate": outcomes[Outcome.ANSWER_VERIFIED.value] / len(decisions) if decisions else 0,
            "clarification_rate": outcomes[Outcome.CLARIFY.value] / len(decisions) if decisions else 0,
            "handoff_rate": sum(value for key, value in outcomes.items() if key.startswith("HANDOFF_")) / len(decisions) if decisions else 0,
        },
        "outcomes_by_intent": {intent: dict(counts) for intent, counts in sorted(intent_outcomes.items())},
        "rates_by_intent": rates_by_intent,
        "baseline_pairs": len(baseline),
        "groundedness": "unverifiable",
    }
    (run_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest["completed_at"] = datetime.now(timezone.utc).isoformat()
    manifest["usage"] = {"input_tokens": usage_input if require_live else 0, "output_tokens": usage_output if require_live else 0, "cost": "unknown"}
    manifest["total_latency_ms"] = round(total_latency, 2)
    manifest["cache_hits"] = cache_hits
    manifest["live_response_count"] = live_response_count
    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    intent_table = "\n".join(
        f"| `{intent}` | {values['total']} | {values['verified_answer_rate']:.1%} | {values['clarification_rate']:.1%} | {values['handoff_rate']:.1%} |"
        for intent, values in rates_by_intent.items()
    )
    report = f"""# Dataset analysis report

- Run: `{actual_run_id}`
- Mode: **{mode}** ({'live model' if require_live else 'TEST ONLY — deterministic rules, not live AI evidence'})
- Provider/model: `{provider_name}` / `{model_name}`
- Rows: {len(rows)} total · {len(human)} human · {len(bots)} bot
- Coverage: {len(classified_ids | error_ids)}/{len(human)} ({metrics['coverage']:.1%})
- Valid classifications: {len(classified_ids)} · errors: {len(error_ids)}
- Verified answers from real pack: **{metrics['verified_answer_from_real_pack']}**
- Groundedness/deadline correctness: **unverifiable** (real pack has no official provenance)
- API cost: unknown

## Outcome counts

{chr(10).join(f'- `{key}`: {value}' for key, value in sorted(outcomes.items()))}

## Rates by intent

| Intent | N | Verified | Clarify | Handoff |
|---|---:|---:|---:|---:|
{intent_table}
"""
    (run_dir / "report.md").write_text(report, encoding="utf-8")
    if require_live and (len(classified_ids | error_ids) != len(human) or not classified_ids or live_response_count < 1):
        raise RuntimeError("live batch did not account for every human row")
    return run_dir
