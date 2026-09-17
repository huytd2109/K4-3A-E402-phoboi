"""Deterministic conflict resolver for official sources.

Rules (§5):
1. Revoked or superseded sources are never used for answers.
2. If source A declares supersedes=B, use A.
3. If two active sources for same scope have different deadlines
   and no supersedes relation, return HANDOFF_CONFLICT.
4. If sources differ by cohort/class, require clarification.
"""

from __future__ import annotations

from enum import Enum

from phoboi.models import OfficialSource, SourceStatus


class ConflictResult(str, Enum):
    """Outcome of conflict resolution."""

    SINGLE_SOURCE = "SINGLE_SOURCE"
    NO_SOURCE = "NO_SOURCE"
    CONFLICT = "CONFLICT"
    RESOLVED_BY_SUPERSEDE = "RESOLVED_BY_SUPERSEDE"
    NEEDS_CLASS_CLARIFICATION = "NEEDS_CLASS_CLARIFICATION"
    NEEDS_COHORT_CLARIFICATION = "NEEDS_COHORT_CLARIFICATION"


class ResolvedSources:
    """Result of conflict resolution."""

    def __init__(
        self,
        result: ConflictResult,
        winner: OfficialSource | None = None,
        all_sources: list[OfficialSource] | None = None,
    ) -> None:
        self.result = result
        self.winner = winner
        self.all_sources = all_sources or []

    def __repr__(self) -> str:
        return f"ResolvedSources(result={self.result}, winner={self.winner.source_id if self.winner else None})"


def resolve_conflicts(sources: list[OfficialSource]) -> ResolvedSources:
    """Apply deterministic conflict resolution rules.

    Input: list of sources already filtered to the query scope.
    Output: resolution result with optional winning source.
    """
    if not sources:
        return ResolvedSources(result=ConflictResult.NO_SOURCE)

    # Step 1: Filter out revoked and superseded
    active = [s for s in sources if s.status == SourceStatus.ACTIVE]

    if not active:
        return ResolvedSources(result=ConflictResult.NO_SOURCE, all_sources=sources)

    # Step 2: Apply supersedes relations
    superseded_ids: set[str] = set()
    for source in active:
        if source.supersedes:
            superseded_ids.add(source.supersedes)

    # Remove superseded sources from active set
    remaining = [s for s in active if s.source_id not in superseded_ids]

    if not remaining:
        # All were superseded by each other? Shouldn't happen but fail safe
        return ResolvedSources(
            result=ConflictResult.CONFLICT, all_sources=active
        )

    if len(remaining) == 1:
        result_type = (
            ConflictResult.RESOLVED_BY_SUPERSEDE
            if len(active) > 1
            else ConflictResult.SINGLE_SOURCE
        )
        return ResolvedSources(
            result=result_type, winner=remaining[0], all_sources=sources
        )

    # Step 3: Never merge records from different cohorts.
    cohorts = {s.cohort for s in remaining if s.cohort}
    if len(cohorts) > 1:
        return ResolvedSources(
            result=ConflictResult.NEEDS_COHORT_CLARIFICATION,
            all_sources=remaining,
        )

    # Step 4: Check if remaining sources differ by class_scope
    class_scopes = {s.class_scope for s in remaining if s.class_scope}
    if len(class_scopes) > 1:
        return ResolvedSources(
            result=ConflictResult.NEEDS_CLASS_CLARIFICATION,
            all_sources=remaining,
        )

    # Step 4: Check if deadlines actually conflict
    deadlines = {s.deadline for s in remaining if s.deadline is not None}
    if len(deadlines) <= 1:
        # Same deadline or no deadline — pick the first
        return ResolvedSources(
            result=ConflictResult.SINGLE_SOURCE,
            winner=remaining[0],
            all_sources=remaining,
        )

    # Step 5: Different deadlines, no supersedes relation → CONFLICT
    # Important: we do NOT pick the newer one by timestamp alone
    return ResolvedSources(
        result=ConflictResult.CONFLICT, all_sources=remaining
    )

