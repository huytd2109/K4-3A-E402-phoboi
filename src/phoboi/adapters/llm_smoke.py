"""Live LLM connectivity check that never prints the API key."""

from __future__ import annotations

import json

from phoboi.config import Config
from phoboi.intent import create_router


def main() -> None:
    config = Config()
    router = create_router(
        config.llm_provider,
        api_key=config.llm_api_key,
        model=config.llm_model,
        timeout_seconds=config.llm_timeout_seconds,
    )
    result = router.classify(
        "Bai thuc hanh thu hai toi nay co phai nop khong, va em chua hieu cach lam?"
    )
    payload = {
        "provider": result.provider,
        "model": result.model,
        "used_fallback": result.used_fallback,
        "fallback_reason": result.fallback_reason,
        "latency_ms": result.latency_ms,
        "intents": [intent.value for intent in result.intents],
        "extraction": result.extraction.model_dump(mode="json"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if result.used_fallback or result.provider != "gemini":
        raise SystemExit("Gemini smoke test failed: the rule-based fallback was used.")


if __name__ == "__main__":
    main()
