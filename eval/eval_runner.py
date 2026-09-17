"""Run the golden set through the live LLM-backed evaluation pipeline.

Usage: python eval/eval_runner.py
Run from the repository root.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

# Keep evaluation live by default while allowing explicit shell overrides.
os.environ.setdefault("APP_ENV", "demo")
os.environ.setdefault("SOURCE_MODE", "synthetic_demo")
os.environ.setdefault("LLM_PROVIDER", "gemini")

from phoboi.config import Settings
from phoboi.evaluation import run_golden


def main() -> None:
    settings = Settings.from_env()
    report = run_golden(
        settings,
        require_live=True,
        suite_path=BASE_DIR / "eval" / "golden_set.jsonl",
        output_dir=BASE_DIR / "eval" / "results",
    )

    total = report["total"]
    passed = report["passed"]
    pass_rate = report["pass_rate"]
    print(f"\nLive eval completed: {passed}/{total} ({pass_rate:.1%})")
    print(f"Provider: {report['provider']} / {report['model']}")
    print(f"Provider requests: {report['provider_requests']}")
    print(f"Reports: {BASE_DIR / 'eval' / 'results'}")

    if passed != total:
        print("\nQuality gate FAILED: live evaluation has failures.")
        sys.exit(1)

    print("\nAll live evaluation cases PASSED.")


if __name__ == "__main__":
    main()
