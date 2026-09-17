from __future__ import annotations

import time
from typing import TypeVar

from pydantic import BaseModel

from phoboi.models import StructuredModelResponse
from phoboi.providers.gemini import ProviderError
from phoboi.security import sanitize_exception

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class OpenAICompatibleProvider:
    def __init__(self, api_key: str, *, provider: str, base_url: str | None = None, timeout_seconds: float = 60):
        if not api_key:
            raise ProviderError(f"{provider} API key is not configured")
        from openai import OpenAI

        self.name = provider
        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_seconds)

    def complete_structured(self, messages: list[dict[str, str]], schema: type[SchemaT], *, model: str, temperature: float = 0.0) -> StructuredModelResponse:
        started = time.perf_counter()
        try:
            completion = self._client.beta.chat.completions.parse(
                model=model, messages=messages, response_format=schema, temperature=temperature
            )
            choice = completion.choices[0].message
            if choice.refusal or choice.parsed is None:
                raise ProviderError("provider refused or omitted structured output")
            return StructuredModelResponse(
                data=choice.parsed,
                provider=self.name,
                model=completion.model or model,
                latency_ms=(time.perf_counter() - started) * 1000,
                input_tokens=getattr(completion.usage, "prompt_tokens", None),
                output_tokens=getattr(completion.usage, "completion_tokens", None),
                request_id=getattr(completion, "id", None),
                live=True,
            )
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"{self.name} request failed: {sanitize_exception(exc)}") from exc

