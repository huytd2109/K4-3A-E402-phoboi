from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from phoboi.analyzer import MessageAnalyzer, deterministic_analysis
from phoboi.batch import run_batch
from phoboi.config import Settings
from phoboi.dataset import load_messages
from phoboi.evaluation import run_golden
from phoboi.policy import decide
from phoboi.preflight import run_preflight
from phoboi.providers.factory import create_provider
from phoboi.providers.gemini import ProviderError
from phoboi.security import sanitize_exception
from phoboi.sources import source_store_for_mode


def _analyze_one(message: str, msg_id: str, settings: Settings, require_live: bool):
    if require_live:
        response = MessageAnalyzer(create_provider(settings), model=settings.llm_model).analyze_batch([(msg_id, message, None)])
        if not response.live:
            raise RuntimeError("live mode received a non-live response")
        return response.data.results[0]
    if settings.app_env != "test":
        raise RuntimeError("offline analyzer is only permitted when APP_ENV=test")
    return deterministic_analysis(msg_id, message)


def cmd_preflight(args) -> int:
    settings = Settings.from_env()
    if not args.require_live:
        raise RuntimeError("preflight requires --require-live")
    report = run_preflight(settings)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def cmd_chat(args) -> int:
    settings = Settings.from_env()
    source_mode = args.source_mode.replace("-", "_") if args.source_mode else settings.source_mode
    if settings.app_env == "production" and source_mode != "dataset":
        raise RuntimeError("production can only use SOURCE_MODE=dataset")
    if settings.app_env == "demo" and source_mode != "synthetic_demo":
        raise RuntimeError("demo can only use SOURCE_MODE=synthetic_demo")
    store = source_store_for_mode(source_mode, app_env=settings.app_env)
    messages = [args.message] if args.message else iter(lambda: input("Bạn> ").strip(), "")
    for index, message in enumerate(messages, 1):
        analysis = _analyze_one(message, f"CLI-{index:05d}", settings, args.require_live)
        result = decide(analysis, message, store)
        print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0


def cmd_analyze_data(args) -> int:
    settings = Settings.from_env()
    require_live = args.require_live
    if not require_live and not args.offline_test:
        raise RuntimeError("choose --require-live, or --offline-test with APP_ENV=test")
    path = Path(args.input)
    human_count = sum(not row.is_bot for row in load_messages(path))
    calls = (human_count + settings.llm_batch_size - 1) // settings.llm_batch_size if require_live else 0
    print(f"Estimated API calls: {calls}; provider/model: {settings.llm_provider}/{settings.llm_model}; cost: unknown")
    run_dir = run_batch(path, settings, require_live=require_live, resume=args.resume, run_id=args.run_id)
    print(run_dir.as_posix())
    return 0


def cmd_report(args) -> int:
    runs = Path("runs")
    if args.run == "latest":
        candidates = sorted((path for path in runs.iterdir() if (path / "report.md").exists()), key=lambda path: path.stat().st_mtime)
        if not candidates:
            raise RuntimeError("no dataset reports found")
        run_dir = candidates[-1]
    else:
        run_dir = runs / args.run
    print((run_dir / "report.md").read_text(encoding="utf-8"))
    return 0


def cmd_eval(args) -> int:
    settings = Settings.from_env()
    if args.suite != "golden":
        raise RuntimeError("only the golden suite is implemented")
    if not args.require_live and not args.offline_test:
        raise RuntimeError("choose --require-live, or --offline-test with APP_ENV=test")
    case_count = sum(1 for line in Path("eval/golden_set.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())
    expected_calls = (case_count + settings.llm_batch_size - 1) // settings.llm_batch_size if args.require_live else 0
    print(f"Estimated API calls: {expected_calls} minimum (+ per-case fallback on batch error); provider/model: {settings.llm_provider}/{settings.llm_model}; cost: unknown")
    report = run_golden(settings, require_live=args.require_live)
    print(json.dumps({key: report[key] for key in ("mode", "total", "passed", "pass_rate", "eligible_answer_coverage", "safety")}, ensure_ascii=False, indent=2))
    if report["pass_rate"] < 0.95 or report["eligible_answer_coverage"] < 0.95 or any(report["safety"].values()):
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="phoboi", description="Verified logistics assistant")
    commands = parser.add_subparsers(dest="command", required=True)
    preflight = commands.add_parser("preflight")
    preflight.add_argument("--require-live", action="store_true")
    preflight.set_defaults(func=cmd_preflight)
    chat = commands.add_parser("chat")
    chat.add_argument("--require-live", action="store_true")
    chat.add_argument("--source-mode", choices=["dataset", "synthetic-demo", "synthetic_demo"])
    chat.add_argument("--message")
    chat.set_defaults(func=cmd_chat)
    analyze = commands.add_parser("analyze-data")
    analyze.add_argument("--input", required=True)
    analyze.add_argument("--require-live", action="store_true")
    analyze.add_argument("--offline-test", action="store_true")
    analyze.add_argument("--resume", action="store_true")
    analyze.add_argument("--run-id")
    analyze.set_defaults(func=cmd_analyze_data)
    report = commands.add_parser("report")
    report.add_argument("--run", default="latest")
    report.set_defaults(func=cmd_report)
    evaluate = commands.add_parser("eval")
    evaluate.add_argument("--suite", default="golden")
    evaluate.add_argument("--require-live", action="store_true")
    evaluate.add_argument("--offline-test", action="store_true")
    evaluate.set_defaults(func=cmd_eval)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        return args.func(args)
    except (ProviderError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {sanitize_exception(exc)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
