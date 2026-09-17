"""TA handoff handler with deduplication/cooldown.

Builds handoff payloads and tracks recent handoffs to prevent
spamming TAs with duplicate questions.
"""

from __future__ import annotations

import time
from typing import Optional

from phoboi.models import (
    ExtractionResult,
    HandoffPayload,
    PolicyDecision,
    PolicyOutcome,
)
from phoboi.security import redact_pii


class HandoffHandler:
    """Manages TA handoff payloads and deduplication."""

    def __init__(self, cooldown_seconds: int = 300) -> None:
        self._cooldown_seconds = cooldown_seconds
        # Key: dedup_key → timestamp of last handoff
        self._recent_handoffs: dict[str, float] = {}

    def should_handoff(self, decision: PolicyDecision) -> bool:
        """Check if this decision requires a TA handoff."""
        return decision.outcome in (
            PolicyOutcome.HANDOFF_NO_SOURCE,
            PolicyOutcome.HANDOFF_CONFLICT,
            PolicyOutcome.HANDOFF_LOW_CONFIDENCE,
        )

    def create_payload(
        self,
        decision: PolicyDecision,
        *,
        original_message: str = "",
        original_message_url: str = "",
        extraction: ExtractionResult | None = None,
        related_discord_message_ids: list[str] | None = None,
    ) -> HandoffPayload:
        """Create a handoff payload from a policy decision."""
        # Build dedup key from extraction + outcome
        dedup_parts = [decision.outcome.value]
        if extraction and extraction.task_normalized:
            dedup_parts.append(extraction.task_normalized)
        if extraction and extraction.cohort:
            dedup_parts.append(extraction.cohort)
        dedup_key = ":".join(dedup_parts)

        return HandoffPayload(
            reason_code=decision.outcome,
            original_message=_truncate(redact_pii(original_message), 200),
            original_message_url=original_message_url,
            extracted_entities=extraction or ExtractionResult(),
            related_source_ids=[
                s.source_id for s in decision.sources_considered
            ],
            related_discord_message_ids=related_discord_message_ids or [],
            dedup_key=dedup_key,
        )

    def is_duplicate(self, payload: HandoffPayload) -> bool:
        """Check if this handoff was recently sent (within cooldown)."""
        now = time.time()
        last_sent = self._recent_handoffs.get(payload.dedup_key)

        if last_sent is not None:
            if now - last_sent < self._cooldown_seconds:
                return True

        return False

    def record_handoff(self, payload: HandoffPayload) -> None:
        """Record that a handoff was sent."""
        self._recent_handoffs[payload.dedup_key] = time.time()

        # Cleanup old entries
        now = time.time()
        expired = [
            key
            for key, ts in self._recent_handoffs.items()
            if now - ts > self._cooldown_seconds * 2
        ]
        for key in expired:
            del self._recent_handoffs[key]

    def try_handoff(
        self,
        decision: PolicyDecision,
        *,
        original_message: str = "",
        original_message_url: str = "",
        extraction: ExtractionResult | None = None,
        related_discord_message_ids: list[str] | None = None,
    ) -> Optional[HandoffPayload]:
        """Create and check handoff — returns payload if should send, None if duplicate."""
        if not self.should_handoff(decision):
            return None

        payload = self.create_payload(
            decision,
            original_message=original_message,
            original_message_url=original_message_url,
            extraction=extraction,
            related_discord_message_ids=related_discord_message_ids,
        )

        if self.is_duplicate(payload):
            return None

        self.record_handoff(payload)
        return payload


def _truncate(text: str, max_len: int) -> str:
    """Truncate text for safe inclusion in handoff payload."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."

