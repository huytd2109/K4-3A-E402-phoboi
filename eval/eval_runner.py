"""Eval runner — runs golden set through the pipeline and reports results.

Usage: python eval/eval_runner.py
Run from the repo root directory.
"""

import json
import os
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

# Ensure we can import phoboi
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

os.environ["APP_ENV"] = "test"
os.environ["LLM_PROVIDER"] = "rule_based"

from phoboi.pipeline import Pipeline
from phoboi.config import Config
from phoboi.models import PolicyOutcome


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    golden_set_path = base_dir / "eval" / "golden_set.jsonl"
    results_dir = base_dir / "eval" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    json_report_path = results_dir / "latest.json"
    md_report_path = results_dir / "latest.md"

    # Set up configuration
    os.environ["APP_ENV"] = "test"
    os.environ["LLM_PROVIDER"] = "rule_based"
    os.environ["OFFICIAL_SOURCES_PATH"] = str(
        base_dir / "data" / "official" / "sources.json"
    )
    config = Config()

    source_path = Path(config.official_sources_path)
    if not source_path.exists():
        print(f"Error: {source_path} does not exist. Cannot run eval.")
        sys.exit(1)

    pipeline = Pipeline(config=config)

    # Load golden set
    test_cases: list[dict] = []
    with open(golden_set_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                test_cases.append(json.loads(line))

    results: list[dict] = []
    category_stats: dict[str, dict[str, int]] = {}
    passed = 0
    failed = 0
    hard_total = 0
    hard_passed = 0

    # Quality gate counters
    incorrect_deadline = 0
    uncited_deadline = 0
    unsafe_personal_answer = 0
    unhandled_conflict = 0

    for tc in test_cases:
        category = tc["category"]
        if category not in category_stats:
            category_stats[category] = {"total": 0, "passed": 0}

        category_stats[category]["total"] += 1
        if tc.get("hard_test"):
            hard_total += 1

        try:
            response = pipeline.process(tc["input"])
            # Get the primary outcome (first decision)
            actual_outcome = response.decisions[0].outcome.value
            actual_outcomes = [decision.outcome.value for decision in response.decisions]
            actual_intents = (
                [i.value for i in response.audit.intents]
                if response.audit
                else []
            )
            actual_text = response.rendered_text

            is_pass = True
            reasons: list[str] = []

            # Check outcome
            if actual_outcome != tc["expected_outcome"]:
                is_pass = False
                reasons.append(
                    f"Expected outcome {tc['expected_outcome']}, got {actual_outcome}"
                )
                # Track quality gate violations
                if tc["expected_outcome"] == "HANDOFF_CONFLICT":
                    unhandled_conflict += 1
                if (
                    tc["category"] == "personal_restricted"
                    and actual_outcome == "ANSWER_VERIFIED"
                ):
                    unsafe_personal_answer += 1

            expected_outcomes = tc.get("expected_outcomes", [])
            for expected in expected_outcomes:
                if expected not in actual_outcomes:
                    is_pass = False
                    reasons.append(
                        f"Missing expected outcome {expected}, got {actual_outcomes}"
                    )

            # Check intents
            if "expected_intents" in tc and tc["expected_intents"]:
                for expected_intent in tc["expected_intents"]:
                    if expected_intent not in actual_intents:
                        is_pass = False
                        reasons.append(
                            f"Missing expected intent {expected_intent}, got {actual_intents}"
                        )

            # Check must_contain
            if "must_contain" in tc:
                for req in tc["must_contain"]:
                    if req and req not in actual_text:
                        is_pass = False
                        reasons.append(f"Missing required string: '{req}'")
                        # If it's a deadline-related string, count as incorrect
                        if any(c.isdigit() for c in req):
                            incorrect_deadline += 1

            # Check must_not_contain
            if "must_not_contain" in tc:
                for req in tc["must_not_contain"]:
                    if req and req in actual_text:
                        is_pass = False
                        reasons.append(f"Contains forbidden string: '{req}'")

            # Check for uncited deadline (ANSWER_VERIFIED without source URL)
            if actual_outcome == "ANSWER_VERIFIED":
                source = response.decisions[0].source
                if not source or not source.source_url:
                    is_pass = False
                    uncited_deadline += 1
                    reasons.append("ANSWER_VERIFIED without source URL")

            if is_pass:
                passed += 1
                category_stats[category]["passed"] += 1
                if tc.get("hard_test"):
                    hard_passed += 1
                results.append({"id": tc["id"], "status": "PASS"})
            else:
                failed += 1
                results.append(
                    {
                        "id": tc["id"],
                        "category": category,
                        "status": "FAIL",
                        "expected": tc["expected_outcome"],
                        "actual": actual_outcome,
                        "reason": "; ".join(reasons),
                    }
                )

        except Exception as e:
            failed += 1
            results.append(
                {
                    "id": tc["id"],
                    "category": category,
                    "status": "ERROR",
                    "expected": tc.get("expected_outcome", "?"),
                    "actual": "EXCEPTION",
                    "reason": str(e),
                }
            )

    total = passed + failed
    pass_rate = passed / total if total > 0 else 0

    # ── JSON report ──
    report = {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(pass_rate, 4),
            "hard_tests": {"total": hard_total, "passed": hard_passed},
        },
        "quality_gates": {
            "incorrect_deadline": incorrect_deadline,
            "uncited_deadline": uncited_deadline,
            "unsafe_personal_answer": unsafe_personal_answer,
            "unhandled_conflict": unhandled_conflict,
        },
        "category_stats": category_stats,
        "failures": [r for r in results if r["status"] != "PASS"],
    }

    with open(json_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ── Markdown report ──
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write("# Eval Results\n\n")
        f.write(
            f"**Total:** {total} | **Passed:** {passed} | "
            f"**Failed:** {failed} | **Pass Rate:** {pass_rate*100:.1f}%\n\n"
        )
        f.write(f"**Hard tests:** {hard_passed}/{hard_total}\n\n")

        f.write("## Quality Gates\n\n")
        f.write("| Gate | Value | Status |\n")
        f.write("|------|-------|--------|\n")
        f.write(
            f"| incorrect_deadline | {incorrect_deadline} | {'✅' if incorrect_deadline == 0 else '❌'} |\n"
        )
        f.write(
            f"| uncited_deadline | {uncited_deadline} | {'✅' if uncited_deadline == 0 else '❌'} |\n"
        )
        f.write(
            f"| unsafe_personal_answer | {unsafe_personal_answer} | {'✅' if unsafe_personal_answer == 0 else '❌'} |\n"
        )
        f.write(
            f"| unhandled_conflict | {unhandled_conflict} | {'✅' if unhandled_conflict == 0 else '❌'} |\n"
        )
        f.write(
            f"| overall_pass_rate | {pass_rate*100:.1f}% | {'✅' if pass_rate >= 0.95 else '❌'} |\n"
        )

        f.write("\n## Pass Rate by Category\n\n")
        f.write("| Category | Total | Passed | Pass Rate |\n")
        f.write("|----------|-------|--------|----------|\n")
        for cat, stats in sorted(category_stats.items()):
            cat_pr = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
            f.write(
                f"| {cat} | {stats['total']} | {stats['passed']} | {cat_pr*100:.1f}% |\n"
            )

        if failed > 0:
            f.write("\n## Failures\n\n")
            f.write("| ID | Category | Expected | Actual | Reason |\n")
            f.write("|----|----------|----------|--------|--------|\n")
            for r in results:
                if r["status"] != "PASS":
                    f.write(
                        f"| {r['id']} | {r.get('category','')} | "
                        f"{r.get('expected','')} | {r.get('actual','')} | "
                        f"{r.get('reason','')} |\n"
                    )

    print(f"\nEval completed: {passed}/{total} ({pass_rate*100:.1f}%)")
    print(f"Reports: {results_dir}")

    # Quality gate checks
    failed_gates: list[str] = []
    if incorrect_deadline > 0:
        failed_gates.append(f"incorrect_deadline={incorrect_deadline}")
    if uncited_deadline > 0:
        failed_gates.append(f"uncited_deadline={uncited_deadline}")
    if unsafe_personal_answer > 0:
        failed_gates.append(f"unsafe_personal_answer={unsafe_personal_answer}")
    if unhandled_conflict > 0:
        failed_gates.append(f"unhandled_conflict={unhandled_conflict}")
    if pass_rate < 0.95:
        failed_gates.append(f"Overall pass rate {pass_rate*100:.1f}% < 95%")
    if hard_total != 4 or hard_passed != hard_total:
        failed_gates.append(f"Hard tests {hard_passed}/{hard_total}, expected 4/4")

    if failed_gates:
        print("\n❌ Quality gates FAILED:")
        for gate in failed_gates:
            print(f"  - {gate}")
        sys.exit(1)
    else:
        print("\n✅ All quality gates PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()
