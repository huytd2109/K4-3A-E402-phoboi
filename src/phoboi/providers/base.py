from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel

from phoboi.models import StructuredModelResponse

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMProvider(Protocol):
    def complete_structured(
        self,
        messages: list[dict[str, str]],
        schema: type[SchemaT],
        *,
        model: str,
        temperature: float = 0.0,
    ) -> StructuredModelResponse: ...

