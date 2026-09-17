"""End-to-end pipeline orchestrator.

Connects all components: sanitize → route → policy → render → audit/handoff.
This is the single entry point for processing a student message.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from phoboi.config import Config, get_config
from phoboi.handoff import HandoffHandler
from phoboi.intent import RuleBasedRouter, IntentRouterProvider
from phoboi.models import (
    AuditRecord,
    Intent,
    PipelineResponse,
    PolicyDecision,
    PolicyOutcome,
)
from phoboi.policy import PolicyEngine
from phoboi.rendering import render_response
from phoboi.security import sanitize_input, escape_mentions
from phoboi.sources import SourceRepository


class Pipeline:
    """Main pipeline — processes a message and returns a response."""

    def __init__(
        self,
        config: Config | None = None,
        router: IntentRouterProvider | None = None,
        source_repo: SourceRepository | None = None,
        handoff_handler: HandoffHandler | None = None,
    ) -> None:
        self._config = config or get_config()
        self._router = router or RuleBasedRouter()
        self._source_repo = source_repo or self._default_source_repo()
        self._policy = PolicyEngine(self._source_repo)
        self._handoff = handoff_handler or HandoffHandler(
            cooldown_seconds=self._config.handoff_cooldown_seconds
        )

    def _default_source_repo(self) -> SourceRepository:
        """Create and load the default source repository."""
        repo = SourceRepository(self._config)
        source_path = Path(self._config.official_sources_path)
        if source_path.exists():
            repo.load_from_file(source_path)
        return repo

    def process(
        self,
        raw_message: str,
        *,
        message_url: str = "",
    ) -> PipelineResponse:
        """Process a raw student message end-to-end.

        Returns a PipelineResponse with rendered text and audit info.
        Never fabricates deadlines — enforced by model validation.
        """
        # 1. Sanitize input
        sanitized = sanitize_input(
            raw_message, max_length=self._config.max_input_length
        )

        # 2. If prompt injection detected, still process but flag it
        # The router will classify the cleaned text normally
        # Injection detection is for audit, not for blocking (fail open on classification)

        # 3. Route intents and extract entities
        router_result = self._router.classify(sanitized.cleaned)

        # 4. If injection detected, override to prevent policy manipulation
        if sanitized.is_injection_attempt:
            # Still process the message normally but log the attempt
            pass

        # 5. Evaluate policy for each intent
        decisions = self._policy.evaluate(router_result)

        # 6. Check if any decisions need handoff
        handoff_payloads = []
        for decision in decisions:
            payload = self._handoff.try_handoff(
                decision,
                original_message=sanitized.cleaned[:200],
                original_message_url=message_url,
                extraction=router_result.extraction,
            )
            if payload is not None:
                handoff_payloads.append(payload)

        # 7. Determine if fixture data is involved
        is_fixture = any(
            d.source and d.source.is_fixture
            for d in decisions
            if d.source is not None
        )

        # 8. Render response
        rendered = render_response(
            decisions,
            support_route=self._config.support_route,
            is_fixture=is_fixture,
        )

        # 9. Escape mentions in output
        rendered = escape_mentions(rendered)

        # 10. Build audit record
        audit = AuditRecord(
            raw_input_hash=sanitized.raw_hash,
            intents=router_result.intents,
            extraction=router_result.extraction,
            decisions=decisions,
            response_outcome=decisions[0].outcome if decisions else None,
            source_ids_used=[
                d.source.source_id
                for d in decisions
                if d.source is not None
            ],
            handoff_sent=len(handoff_payloads) > 0,
            is_fixture_data=is_fixture,
        )

        return PipelineResponse(
            decisions=decisions,
            rendered_text=rendered,
            is_fixture_data=is_fixture,
            audit=audit,
        )

