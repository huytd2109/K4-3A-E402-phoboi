from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from phoboi.models import Analysis, CandidateFact, OfficialSource


class SourceStore(Protocol):
    mode: str

    def search(self, analysis: Analysis) -> list[OfficialSource]: ...


def _matches(value: str | None, allowed: list[str]) -> bool:
    return value is None or value.casefold() in {item.casefold() for item in allowed}


class SyntheticDemoSourceStore:
    mode = "synthetic_demo"

    def __init__(self, path: Path | None = None):
        default = Path(__file__).resolve().parents[2] / "fixtures" / "synthetic_sources.json"
        raw = json.loads((path or default).read_text(encoding="utf-8"))
        self.sources = [OfficialSource.model_validate(item) for item in raw]
        if any(source.source_type != "synthetic_demo" or not source.is_fixture for source in self.sources):
            raise ValueError("synthetic store contains a non-demo source")

    def search(self, analysis: Analysis) -> list[OfficialSource]:
        entities = analysis.entities
        found = []
        for source in self.sources:
            aliases = [source.task_id, *source.task_aliases]
            if entities.task and not _matches(entities.task, aliases):
                continue
            if entities.cohort and source.cohort.casefold() != entities.cohort.casefold():
                continue
            if entities.class_scope and source.class_scope.casefold() != entities.class_scope.casefold():
                continue
            if entities.logistics_type and source.logistics_type != entities.logistics_type:
                continue
            found.append(source)
        return found


class RealDatasetSourceStore:
    """The real pack contains candidates only and can never return official sources."""

    mode = "dataset"

    def __init__(self, candidates: list[CandidateFact] | None = None):
        self.candidates = candidates or []

    def search(self, analysis: Analysis) -> list[OfficialSource]:
        del analysis
        return []

    def search_candidates(self, analysis: Analysis) -> list[CandidateFact]:
        task = analysis.entities.task
        return [item for item in self.candidates if task is None or item.task_id == task]


def source_store_for_mode(mode: str, *, app_env: str, fixture_path: Path | None = None) -> SourceStore:
    if mode == "synthetic_demo":
        if app_env not in {"test", "demo"}:
            raise ValueError("synthetic demo sources are forbidden in production")
        return SyntheticDemoSourceStore(fixture_path)
    if mode == "dataset":
        return RealDatasetSourceStore()
    raise ValueError("official_discord is not implemented for the hackathon")
