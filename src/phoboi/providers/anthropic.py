from __future__ import annotations

import json
import time
from typing import TypeVar

from pydantic import BaseModel

from phoboi.models import StructuredModelResponse
from phoboi.providers.gemini import ProviderError
from phoboi.security import sanitize_exception

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, *, timeout_seconds: float = 60):
        if not api_key:
            raise ProviderError("ANTHROPIC_API_KEY is not configured")
        from anthropic import Anthropic

        self._client = Anthropic(api_key=api_key, timeout=timeout_seconds)

    def complete_structured(self, messages: list[dict[str, str]], schema: type[SchemaT], *, model: str, temperature: float = 0.0) -> StructuredModelResponse:
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        user_messages = [m for m in messages if m["role"] != "system"]
        tool = {"name": "analyze_discord_batch", "description": "Return only validated analysis", "input_schema": schema.model_json_schema()}
        started = time.perf_counter()
        try:
            response = self._client.messages.create(
                model=model,
                max_tokens=4096,
                temperature=temperature,
                system=system,
                messages=user_messages,
                tools=[tool],
                tool_choice={"type": "tool", "name": "analyze_discord_batch"},
            )
            block = next((item for item in response.content if getattr(item, "type", None) == "tool_use"), None)
            if block is None:
                raise ProviderError("Anthropic returned no structured tool result")
            data = schema.model_validate(json.loads(json.dumps(block.input)))
            return StructuredModelResponse(
                data=data,
                provider=self.name,
                model=response.model,
                latency_ms=(time.perf_counter() - started) * 1000,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                request_id=response.id,
                live=True,
            )
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Anthropic request failed: {sanitize_exception(exc)}") from exc

