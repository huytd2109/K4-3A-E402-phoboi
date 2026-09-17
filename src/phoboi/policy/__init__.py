"""Policy engine — maps intents + sources + extraction → PolicyDecision.

This is the central decision-maker. It enforces all behavioral rules:
- Verified answers only from official sources
- Personal data always restricted
- Greeting handled minimally
- Missing entities → clarify
- No source → handoff
- Conflict → handoff
"""

from __future__ import annotations

from phoboi.models import (
    ExtractionResult,
    Intent,
    LogisticsType,
    OfficialSource,
    PolicyDecision,
    PolicyOutcome,
    RouterResult,
    SourceQueryResult,
)
from phoboi.sources import SourceRepository
from phoboi.sources.conflict_resolver import ConflictResult, resolve_conflicts


class PolicyEngine:
    """Deterministic policy engine for the logistics assistant."""

    def __init__(self, source_repo: SourceRepository) -> None:
        self._source_repo = source_repo

    def evaluate(self, router_result: RouterResult) -> list[PolicyDecision]:
        """Evaluate all intents and return a list of policy decisions."""
        decisions: list[PolicyDecision] = []

        for intent in router_result.intents:
            decision = self._evaluate_single(
                intent, router_result.extraction, router_result.intents
            )
            decisions.append(decision)

        return decisions

    def _evaluate_single(
        self,
        intent: Intent,
        extraction: ExtractionResult,
        all_intents: list[Intent],
    ) -> PolicyDecision:
        """Evaluate a single intent."""

        # ── Greeting ──
        if intent == Intent.GREETING:
            return PolicyDecision(
                outcome=PolicyOutcome.ANSWER_GREETING,
                intent=intent,
                reason="Pure greeting, no retrieval needed.",
            )

        # ── Personal / Restricted ──
        if intent == Intent.PERSONAL_RESTRICTED:
            return PolicyDecision(
                outcome=PolicyOutcome.RESTRICT_PERSONAL,
                intent=intent,
                reason="Personal data request — bot has no authority to access.",
            )

        # ── Out of scope ──
        if intent == Intent.OUT_OF_SCOPE:
            return PolicyDecision(
                outcome=PolicyOutcome.OUT_OF_SCOPE,
                intent=intent,
                reason="Message does not match any known category.",
            )

        # ── Unknown ──
        if intent == Intent.UNKNOWN:
            return PolicyDecision(
                outcome=PolicyOutcome.HANDOFF_LOW_CONFIDENCE,
                intent=intent,
                reason="Could not determine intent with confidence.",
            )

        # ── Learning (non-logistics) ──
        if intent == Intent.LEARNING:
            # If there are also logistics intents, don't duplicate — logistics handler covers it
            logistics_intents = [
                i for i in all_intents
                if i in (Intent.LOGISTICS_DEADLINE, Intent.LOGISTICS_LINK, Intent.LOGISTICS_SUBMISSION)
            ]
            if logistics_intents:
                return PolicyDecision(
                    outcome=PolicyOutcome.ROUTE_LEARNING,
                    intent=intent,
                    reason="Learning question alongside logistics — learning part routed separately.",
                )
            return PolicyDecision(
                outcome=PolicyOutcome.ROUTE_LEARNING,
                intent=intent,
                reason="Learning question — outside logistics scope.",
            )

        # ── Logistics (DEADLINE, LINK, SUBMISSION) ──
        return self._evaluate_logistics(intent, extraction)

    def _evaluate_logistics(
        self, intent: Intent, extraction: ExtractionResult
    ) -> PolicyDecision:
        """Evaluate a logistics intent against the source repository."""

        # Check if we have enough info to query
        missing: list[str] = []
        if not extraction.task_normalized:
            missing.append("task (ví dụ: Lab 2, Workshop 1)")

        # If missing exactly one field, ask for clarification
        if missing:
            return PolicyDecision(
                outcome=PolicyOutcome.CLARIFY,
                intent=intent,
                missing_fields=missing,
                reason=f"Missing required field(s): {', '.join(missing)}",
            )

        requested_type = {
            Intent.LOGISTICS_DEADLINE: LogisticsType.DEADLINE,
            Intent.LOGISTICS_LINK: LogisticsType.LINK,
            Intent.LOGISTICS_SUBMISSION: LogisticsType.SUBMISSION,
        }[intent]

        # Query the source repository
        query_result = self._source_repo.query(
            task_id=extraction.task_normalized,
            cohort=extraction.cohort,
            class_scope=extraction.class_scope,
            logistics_type=requested_type,
        )

        # Fallback: if no results with specific logistics_type, try without type filter
        # This handles cases like "deadline workshop 1" where source type is "schedule"
        if not query_result.sources:
            query_result = self._source_repo.query(
                task_id=extraction.task_normalized,
                cohort=extraction.cohort,
                class_scope=extraction.class_scope,
                logistics_type=None,
            )

        # Broad fallback records still need the fact required by this intent.
        if requested_type == LogisticsType.DEADLINE:
            query_result.sources = [s for s in query_result.sources if s.deadline]
        elif requested_type in (LogisticsType.LINK, LogisticsType.SUBMISSION):
            query_result.sources = [s for s in query_result.sources if s.submission_url]

        # No sources found
        if not query_result.sources:
            return PolicyDecision(
                outcome=PolicyOutcome.HANDOFF_NO_SOURCE,
                intent=intent,
                sources_considered=[],
                reason=f"No official source found for task='{extraction.task_normalized}'.",
            )

        # Resolve conflicts
        resolved = resolve_conflicts(query_result.sources)

        if resolved.result == ConflictResult.NO_SOURCE:
            return PolicyDecision(
                outcome=PolicyOutcome.HANDOFF_NO_SOURCE,
                intent=intent,
                sources_considered=resolved.all_sources,
                reason="All matching sources are revoked or superseded.",
            )

        if resolved.result == ConflictResult.CONFLICT:
            return PolicyDecision(
                outcome=PolicyOutcome.HANDOFF_CONFLICT,
                intent=intent,
                sources_considered=resolved.all_sources,
                reason="Multiple active sources with different deadlines and no supersedes relation.",
            )

        if resolved.result == ConflictResult.NEEDS_CLASS_CLARIFICATION:
            return PolicyDecision(
                outcome=PolicyOutcome.CLARIFY,
                intent=intent,
                missing_fields=["class_scope (ví dụ: L2-3 hoặc L3-4)"],
                sources_considered=resolved.all_sources,
                reason="Sources exist for different class scopes; need clarification.",
            )

        if resolved.result == ConflictResult.NEEDS_COHORT_CLARIFICATION:
            return PolicyDecision(
                outcome=PolicyOutcome.CLARIFY,
                intent=intent,
                missing_fields=["cohort (ví dụ: K4)"],
                sources_considered=resolved.all_sources,
                reason="Sources exist for different cohorts; need clarification.",
            )

        # Single source or resolved by supersede → ANSWER_VERIFIED
        winner = resolved.winner
        assert winner is not None, "Winner must exist for SINGLE_SOURCE/RESOLVED_BY_SUPERSEDE"

        return PolicyDecision(
            outcome=PolicyOutcome.ANSWER_VERIFIED,
            intent=intent,
            source=winner,
            sources_considered=resolved.all_sources,
            reason=f"Verified from source '{winner.source_id}'.",
        )
