from __future__ import annotations

import os

from phoboi.config import Settings
from phoboi.providers.anthropic import AnthropicProvider
from phoboi.providers.gemini import GeminiProvider, ProviderError
from phoboi.providers.openai_compatible import OpenAICompatibleProvider


def create_provider(settings: Settings):
    if not settings.api_key_configured:
        raise ProviderError(f"{settings.api_key_name or 'provider API key'} is not configured")
    key = os.environ[settings.api_key_name]
    if settings.llm_provider == "gemini":
        return GeminiProvider(key, timeout_seconds=settings.request_timeout_seconds, max_retries=settings.llm_max_retries)
    if settings.llm_provider == "openrouter":
        return OpenAICompatibleProvider(key, provider="openrouter", base_url="https://openrouter.ai/api/v1", timeout_seconds=settings.request_timeout_seconds)
    if settings.llm_provider == "openai":
        return OpenAICompatibleProvider(key, provider="openai", base_url=os.getenv("OPENAI_BASE_URL") or None, timeout_seconds=settings.request_timeout_seconds)
    if settings.llm_provider == "anthropic":
        return AnthropicProvider(key, timeout_seconds=settings.request_timeout_seconds)
    raise ProviderError(f"unsupported provider: {settings.llm_provider}")

