from __future__ import annotations

import pytest

from phoboi.config import Settings
from phoboi.providers.factory import create_provider
from phoboi.providers.gemini import ProviderError


def test_missing_live_key_fails_closed(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    settings = Settings(
        app_env="production", source_mode="dataset", llm_provider="gemini", llm_model="gemini-test",
        llm_temperature=0, llm_batch_size=20, llm_max_retries=0, request_timeout_seconds=1, max_concurrency=1,
    )
    with pytest.raises(ProviderError, match="not configured"):
        create_provider(settings)

