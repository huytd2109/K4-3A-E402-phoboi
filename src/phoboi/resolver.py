from __future__ import annotations

from dataclasses import dataclass

from phoboi.models import OfficialSource, SourceStatus


@dataclass(frozen=True)
class Resolution:
    kind: str
    sources: list[OfficialSource]
    missing_field: str | None = None


def resolve_sources(sources: list[OfficialSource], *, cohort: str | None, class_scope: str | None) -> Resolution:
    active = [source for source in sources if source.status == SourceStatus.ACTIVE]
    superseded_ids = {old_id for source in active for old_id in source.supersedes}
    active = [source for source in active if source.source_id not in superseded_ids]
    if not active:
        return Resolution("no_source", [])

    if cohort is None and len({source.cohort for source in active}) > 1:
        return Resolution("clarify", active, "cohort")
    if class_scope is None and len({source.class_scope for source in active}) > 1:
        return Resolution("clarify", active, "class_scope")

    if len(active) == 1:
        return Resolution("resolved", active)

    deadlines = {source.deadline for source in active}
    submission_urls = {str(source.submission_url) for source in active}
    if len(deadlines) > 1 or len(submission_urls) > 1:
        return Resolution("conflict", active)
    if all(source.has_resolvable_provenance for source in active):
        return Resolution("resolved", active)
    return Resolution("no_source", [])

