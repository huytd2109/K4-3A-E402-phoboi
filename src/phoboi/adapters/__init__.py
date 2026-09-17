"""Local CLI demo — interactive REPL for the phoboi assistant.

Runs fully offline without Discord token or API keys.
Usage: python -m phoboi.adapters.cli
   or: phoboi  (if installed via pip install -e .)
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """Run the interactive CLI demo."""
    import os
    os.environ.setdefault("APP_ENV", "demo")

    from phoboi.config import Config
    from phoboi.pipeline import Pipeline

    config = Config()
    print("=" * 60)
    print("  Phoboi — Trợ lý Logistics (Demo CLI)")
    print("=" * 60)

    if config.allows_fixtures:
        print("  ⚠️  Chế độ DEMO — dữ liệu mẫu, không phải deadline thật")
    else:
        print("  🔒 Chế độ PRODUCTION")

    print(f"  APP_ENV={config.app_env}")
    print(f"  Sources: {config.official_sources_path}")
    print()
    print("  Gõ câu hỏi để thử. Gõ 'quit' hoặc Ctrl+C để thoát.")
    print("=" * 60)
    print()

    try:
        pipeline = Pipeline(config=config)
    except FileNotFoundError as e:
        print(f"❌ Không tìm thấy file nguồn: {e}")
        print(f"   Tạo file {config.official_sources_path} hoặc chạy từ thư mục gốc repo.")
        sys.exit(1)

    while True:
        try:
            user_input = input("🎓 Học viên: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Tạm biệt!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("\n👋 Tạm biệt!")
            break

        # Process through pipeline
        result = pipeline.process(user_input)

        # Display response
        print(f"\n🤖 Bot:\n{result.rendered_text}")
        print()

        # Show debug info
        intents = ", ".join(i.value for i in result.audit.intents) if result.audit else "?"
        outcomes = ", ".join(d.outcome.value for d in result.decisions)
        print(f"   [Intent: {intents} | Outcome: {outcomes}]")

        if result.audit and result.audit.handoff_sent:
            print("   📨 Handoff đã được gửi cho TA")

        print()


if __name__ == "__main__":
    main()


def web_main():
    from phoboi.adapters.web_demo import run_web_demo
    run_web_demo()

