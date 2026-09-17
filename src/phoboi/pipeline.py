"""End-to-end pipeline orchestrator.

Connects all components: sanitize → route → policy → render → audit/handoff.
This is the single entry point for processing a student message.
"""

from __future__ import annotations

from pathlib import Path

from phoboi.config import Config, get_config
from phoboi.discord_pack import DiscordPackRepository
from phoboi.handoff import HandoffHandler
from phoboi.intent import IntentRouterProvider, create_router
from phoboi.models import (
    AuditRecord,
    Intent,
    PipelineResponse,
    PolicyDecision,
    PolicyOutcome,
)
from phoboi.policy import PolicyEngine
from phoboi.rendering import render_response
from phoboi.security import contains_system_leak_request, escape_mentions, sanitize_input
from phoboi.sources import SourceRepository


class Pipeline:
    """Main pipeline — processes a message and returns a response."""

    def __init__(
        self,
        config: Config | None = None,
        router: IntentRouterProvider | None = None,
        source_repo: SourceRepository | None = None,
        discord_pack_repo: DiscordPackRepository | None = None,
        handoff_handler: HandoffHandler | None = None,
    ) -> None:
        self._config = config or get_config()
        self._router = router or create_router(
            self._config.llm_provider,
            api_key=self._config.llm_api_key,
            model=self._config.llm_model,
            timeout_seconds=self._config.llm_timeout_seconds,
        )
        self._source_repo = source_repo or self._default_source_repo()
        self._discord_pack = discord_pack_repo or self._default_discord_pack()
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

    def _default_discord_pack(self) -> DiscordPackRepository:
        """Load optional historical context; it never becomes official source data."""
        repo = DiscordPackRepository()
        pack_path = Path(self._config.discord_pack_path)
        if self._config.discord_pack_enabled and pack_path.exists():
            repo.load_from_csv(pack_path)
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

        # 2. Security signals are recorded, but cannot change source policy.
        security_flags: list[str] = []
        if sanitized.is_injection_attempt:
            security_flags.append("prompt_injection")
        if sanitized.contains_pii:
            security_flags.append("pii_detected")
        if contains_system_leak_request(sanitized.cleaned):
            security_flags.append("system_leak_request")
        if sanitized.was_truncated:
            security_flags.append("input_truncated")

        # 3. Route intents and extract entities
        router_result = self._router.classify(sanitized.cleaned)

        # Local-only retrieval. Raw peer messages are never sent to the LLM.
        context_query = " ".join(
            value
            for value in (
                sanitized.cleaned,
                router_result.extraction.task_normalized,
                router_result.extraction.logistics_type.value
                if router_result.extraction.logistics_type
                else None,
            )
            if value
        )
        pack_matches = self._discord_pack.search(context_query, limit=5)
        pack_message_ids = [match.msg_id for match in pack_matches]

        # 4. Evaluate policy for each intent
        decisions = self._policy.evaluate(router_result)

        # 6. Check if any decisions need handoff
        handoff_payloads = []
        for decision in decisions:
            payload = self._handoff.try_handoff(
                decision,
                original_message=sanitized.cleaned[:200],
                original_message_url=message_url,
                extraction=router_result.extraction,
                related_discord_message_ids=pack_message_ids,
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
            router_provider=router_result.provider,
            router_model=router_result.model,
            router_used_fallback=router_result.used_fallback,
            router_latency_ms=router_result.latency_ms,
            router_fallback_reason=router_result.fallback_reason,
            decisions=decisions,
            response_outcome=decisions[0].outcome if decisions else None,
            source_ids_used=[
                d.source.source_id
                for d in decisions
                if d.source is not None
            ],
            discord_pack_message_ids=pack_message_ids,
            discord_pack_total=self._discord_pack.count,
            handoff_sent=len(handoff_payloads) > 0,
            is_fixture_data=is_fixture,
            security_flags=security_flags,
        )

        return PipelineResponse(
            decisions=decisions,
            rendered_text=rendered,
            is_fixture_data=is_fixture,
            handoffs=handoff_payloads,
            audit=audit,
        )

