"""Official source repository — loads, validates, and queries OfficialSource records.

Sources are loaded from a JSON file. In production mode, fixtures are rejected.
Queries match by task_id (or alias), cohort, class_scope, and logistics_type.
"""

from __future__ import annotations

import json
from pathlib import Path

from phoboi.config import Config
from phoboi.models import LogisticsType, OfficialSource, SourceQueryResult, SourceStatus


class SourceRepository:
    """In-memory official source store with strict validation."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._sources: list[OfficialSource] = []

    def load_from_file(self, path: str | Path | None = None) -> None:
        """Load and validate sources from a JSON file."""
        if path is None:
            path = self._config.official_sources_path

        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Official source file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        sources_data = raw_data if isinstance(raw_data, list) else raw_data.get("sources", [])

        loaded: list[OfficialSource] = []
        for item in sources_data:
            source = OfficialSource.model_validate(item)

            # Production mode: reject fixtures
            if self._config.is_production and source.is_fixture:
                raise ValueError(
                    f"Fixture source '{source.source_id}' is not allowed in production mode. "
                    f"Set APP_ENV=demo or APP_ENV=test to use fixtures."
                )

            if self._config.is_production:
                self._validate_production_source(source)

            loaded.append(source)

        self._sources = loaded

    def load_from_list(self, sources: list[OfficialSource]) -> None:
        """Load sources directly (for testing)."""
        if self._config.is_production:
            for s in sources:
                if s.is_fixture:
                    raise ValueError(
                        f"Fixture source '{s.source_id}' not allowed in production."
                    )
                self._validate_production_source(s)
        self._sources = list(sources)

    def _validate_production_source(self, source: OfficialSource) -> None:
        """Reject production records that are outside configured trust lists."""
        if not self._config.authorized_channel_ids or not self._config.authorized_role_ids:
            raise ValueError(
                "Production sources require non-empty AUTHORIZED_CHANNEL_IDS and "
                "AUTHORIZED_ROLE_IDS whitelists."
            )
        if source.channel_id not in self._config.authorized_channel_ids:
            raise ValueError(
                f"Source '{source.source_id}' comes from an unauthorized channel."
            )
        if source.published_by_role not in self._config.authorized_role_ids:
            raise ValueError(
                f"Source '{source.source_id}' comes from an unauthorized publisher role."
            )

    def query(
        self,
        *,
        task_id: str | None = None,
        cohort: str | None = None,
        class_scope: str | None = None,
        logistics_type: LogisticsType | None = None,
    ) -> SourceQueryResult:
        """Query sources by scope. Only returns active sources."""
        results: list[OfficialSource] = []

        for source in self._sources:
            # Skip non-active
            if source.status != SourceStatus.ACTIVE:
                continue

            # Match task
            if task_id:
                task_match = (
                    source.task_id == task_id
                    or task_id in [a.lower() for a in source.task_aliases]
                    or task_id.replace("-", "").replace(" ", "")
                    == source.task_id.replace("-", "").replace(" ", "")
                )
                if not task_match:
                    continue

            # Match cohort (if specified in query)
            if cohort and source.cohort:
                if source.cohort.lower() != cohort.lower():
                    continue

            # Match class scope (if specified in both)
            if class_scope and source.class_scope:
                if source.class_scope.lower() != class_scope.lower():
                    continue

            # Match logistics type
            if logistics_type and source.logistics_type != logistics_type:
                continue

            results.append(source)

        return SourceQueryResult(
            sources=results,
            query_scope={
                "task_id": task_id,
                "cohort": cohort,
                "class_scope": class_scope,
                "logistics_type": logistics_type.value if logistics_type else None,
            },
        )

    def get_by_id(self, source_id: str) -> OfficialSource | None:
        """Get a single source by ID."""
        for source in self._sources:
            if source.source_id == source_id:
                return source
        return None

    @property
    def all_sources(self) -> list[OfficialSource]:
        """All loaded sources (for inspection/testing)."""
        return list(self._sources)

    @property
    def active_sources(self) -> list[OfficialSource]:
        """Only active sources."""
        return [s for s in self._sources if s.status == SourceStatus.ACTIVE]

