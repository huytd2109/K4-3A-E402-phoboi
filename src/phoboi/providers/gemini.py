from __future__ import annotations

import json
import random
import ssl
import time
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from phoboi.models import StructuredModelResponse
from phoboi.security import sanitize_exception

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class ProviderError(RuntimeError):
    """A redacted, user-safe provider failure."""


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, *, timeout_seconds: float = 60, max_retries: int = 3):
        if not api_key:
            raise ProviderError("GEMINI_API_KEY is not configured")
        import truststore
        from google import genai
        from google.genai import types

        system_ssl = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                client_args={"verify": system_ssl},
                async_client_args={"verify": system_ssl},
            ),
        )
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    @staticmethod
    def _retryable(exc: BaseException) -> bool:
        status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
        return status in {429, 500, 502, 503, 504} or isinstance(exc, (TimeoutError, ConnectionError))

    def complete_structured(
        self,
        messages: list[dict[str, str]],
        schema: type[SchemaT],
        *,
        model: str,
        temperature: float = 0.0,
    ) -> StructuredModelResponse:
        from google.genai import types

        if temperature != 0:
            raise ProviderError("structured analysis requires temperature=0")
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        user = "\n\n".join(m["content"] for m in messages if m["role"] != "system")
        last_error: BaseException | None = None
        for attempt in range(self.max_retries + 1):
            started = time.perf_counter()
            try:
                response = self._client.models.generate_content(
                    model=model,
                    contents=user,
                    config=types.GenerateContentConfig(
                        system_instruction=system,
                        temperature=temperature,
                        response_mime_type="application/json",
                        response_schema=schema,
                        http_options=types.HttpOptions(timeout=int(self.timeout_seconds * 1000)),
                    ),
                )
                parsed = response.parsed
                if isinstance(parsed, schema):
                    data = parsed
                elif parsed is not None:
                    data = schema.model_validate(parsed)
                else:
                    data = schema.model_validate_json(response.text)
                usage = getattr(response, "usage_metadata", None)
                sdk_response = getattr(response, "sdk_http_response", None)
                headers = getattr(sdk_response, "headers", {}) or {}
                return StructuredModelResponse(
                    data=data,
                    provider=self.name,
                    model=model,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    input_tokens=getattr(usage, "prompt_token_count", None),
                    output_tokens=getattr(usage, "candidates_token_count", None),
                    request_id=headers.get("x-request-id") if hasattr(headers, "get") else None,
                    live=True,
                )
            except (ValidationError, json.JSONDecodeError) as exc:
                # Schema failures are not transport retries. Ask the model exactly once
                # to repair its own JSON, validate again, then fail the case closed.
                try:
                    bad_text = (getattr(response, "text", "") or "")[:12_000]
                    repaired = self._client.models.generate_content(
                        model=model,
                        contents=(
                            "Repair the following output so it conforms exactly to the supplied JSON schema. "
                            "Do not add facts or infer missing values; return JSON only.\n<invalid_output>\n"
                            + bad_text
                            + "\n</invalid_output>"
                        ),
                        config=types.GenerateContentConfig(
                            temperature=0,
                            response_mime_type="application/json",
                            response_schema=schema,
                            http_options=types.HttpOptions(timeout=int(self.timeout_seconds * 1000)),
                        ),
                    )
                    repaired_data = repaired.parsed
                    if isinstance(repaired_data, schema):
                        data = repaired_data
                    elif repaired_data is not None:
                        data = schema.model_validate(repaired_data)
                    else:
                        data = schema.model_validate_json(repaired.text)
                    usage = getattr(repaired, "usage_metadata", None)
                    sdk_response = getattr(repaired, "sdk_http_response", None)
                    headers = getattr(sdk_response, "headers", {}) or {}
                    return StructuredModelResponse(
                        data=data,
                        provider=self.name,
                        model=model,
                        latency_ms=(time.perf_counter() - started) * 1000,
                        input_tokens=getattr(usage, "prompt_token_count", None),
                        output_tokens=getattr(usage, "candidates_token_count", None),
                        request_id=headers.get("x-request-id") if hasattr(headers, "get") else None,
                        live=True,
                    )
                except Exception as repair_exc:
                    raise ProviderError("provider returned invalid structured output after one repair") from repair_exc
            except Exception as exc:  # SDK exception hierarchy changes between releases.
                last_error = exc
                if not self._retryable(exc) or attempt >= self.max_retries:
                    break
                time.sleep(min(8.0, (2**attempt) + random.random()))
        raise ProviderError(f"Gemini request failed: {sanitize_exception(last_error or RuntimeError('unknown error'))}")
