"""Core domain models for the phoboi logistics assistant.

All Pydantic models used across the pipeline: intents, outcomes,
official source schema, extraction results, policy decisions, and handoff payloads.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Intent taxonomy ───────────────────────────────────────────────


class Intent(str, Enum):
    """Multi-label intent categories for student messages."""

    GREETING = "GREETING"
    LOGISTICS_DEADLINE = "LOGISTICS_DEADLINE"
    LOGISTICS_LINK = "LOGISTICS_LINK"
    LOGISTICS_SUBMISSION = "LOGISTICS_SUBMISSION"
    LEARNING = "LEARNING"
    PERSONAL_RESTRICTED = "PERSONAL_RESTRICTED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    UNKNOWN = "UNKNOWN"


class PolicyOutcome(str, Enum):
    """Possible outcomes from the policy engine."""

    ANSWER_VERIFIED = "ANSWER_VERIFIED"
    CLARIFY = "CLARIFY"
    HANDOFF_NO_SOURCE = "HANDOFF_NO_SOURCE"
    HANDOFF_CONFLICT = "HANDOFF_CONFLICT"
    HANDOFF_LOW_CONFIDENCE = "HANDOFF_LOW_CONFIDENCE"
    RESTRICT_PERSONAL = "RESTRICT_PERSONAL"
    ANSWER_GREETING = "ANSWER_GREETING"
    ROUTE_LEARNING = "ROUTE_LEARNING"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class SourceStatus(str, Enum):
    """Lifecycle status of an official source."""

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"


class LogisticsType(str, Enum):
    """Type of logistics information."""

    DEADLINE = "deadline"
    LINK = "link"
    SUBMISSION = "submission"
    SCHEDULE = "schedule"
    OTHER = "other"


# ── Official Source schema (§5) ───────────────────────────────────


class OfficialSource(BaseModel):
    """A single official source record — the only trusted origin for deadlines.

    Every field that touches student-facing answers is validated here.
    Production sources must come from whitelisted channels and roles.
    """

    source_id: str = Field(..., min_length=1, description="Unique identifier for this source")
    source_url: str = Field(..., min_length=1, description="URL to the original announcement")
    source_type: str = Field(
        default="discord_message",
        description="Type of source: discord_message, document, etc.",
    )

    # Discord provenance
    guild_id: str = Field(default="", description="Discord guild/server ID")
    channel_id: str = Field(default="", description="Discord channel ID")
    message_id: str = Field(default="", description="Discord message ID")
    published_by_role: str = Field(default="", description="Role of the publisher (BTC, TA, etc.)")
    published_at: datetime = Field(..., description="When the source was published")

    # Scope
    effective_from: Optional[datetime] = Field(
        default=None, description="When this source becomes effective"
    )
    task_id: str = Field(..., min_length=1, description="Canonical task identifier, e.g. 'lab-02'")
    task_aliases: list[str] = Field(
        default_factory=list,
        description="Alternative names: 'Lab 2', 'lab2', 'bài lab 2', etc.",
    )
    cohort: str = Field(default="K4", description="Cohort identifier, e.g. 'K4'")
    class_scope: str = Field(default="", description="Class scope, e.g. 'L2-3', 'L3-4', or '' for all")
    logistics_type: LogisticsType = Field(..., description="Type of logistics info")

    # Content
    deadline: Optional[datetime] = Field(
        default=None,
        description="Deadline datetime (must include timezone, displayed as UTC+7)",
    )
    submission_url: Optional[str] = Field(default=None, description="Submission URL if applicable")

    # Lifecycle
    supersedes: Optional[str] = Field(
        default=None,
        description="source_id this record supersedes",
    )
    status: SourceStatus = Field(default=SourceStatus.ACTIVE)
    is_fixture: bool = Field(
        default=False,
        description="True for demo/test data. Must be True for synthetic data.",
    )

    @field_validator("deadline", mode="before")
    @classmethod
    def parse_deadline(cls, v: str | datetime | None) -> datetime | None:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        # Accept ISO format strings
        return datetime.fromisoformat(v)

    @field_validator("published_at", mode="before")
    @classmethod
    def parse_published_at(cls, v: str | datetime) -> datetime:
        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(v)


# ── Pipeline data structures ─────────────────────────────────────


class ExtractionResult(BaseModel):
    """Entities extracted from a student message."""

    task: Optional[str] = Field(default=None, description="Extracted task name, e.g. 'lab 2'")
    task_normalized: Optional[str] = Field(
        default=None, description="Normalized task ID, e.g. 'lab-02'"
    )
    cohort: Optional[str] = Field(default=None, description="Extracted cohort, e.g. 'K4'")
    class_scope: Optional[str] = Field(
        default=None, description="Extracted class scope, e.g. 'L3-4'"
    )
    logistics_type: Optional[LogisticsType] = Field(
        default=None, description="Detected logistics type"
    )
    raw_entities: dict[str, str] = Field(
        default_factory=dict, description="Additional raw extracted entities"
    )


class RouterResult(BaseModel):
    """Output from the multi-label intent router."""

    intents: list[Intent] = Field(..., min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    extraction: ExtractionResult = Field(default_factory=ExtractionResult)


class SourceQueryResult(BaseModel):
    """Result of querying the official source repository."""

    sources: list[OfficialSource] = Field(default_factory=list)
    query_scope: dict[str, str | None] = Field(default_factory=dict)


class PolicyDecision(BaseModel):
    """A single decision from the policy engine for one intent."""

    outcome: PolicyOutcome
    intent: Intent
    source: Optional[OfficialSource] = None
    sources_considered: list[OfficialSource] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    reason: str = Field(default="")


class PipelineResponse(BaseModel):
    """Complete response from the pipeline."""

    decisions: list[PolicyDecision] = Field(..., min_length=1)
    rendered_text: str = Field(..., min_length=1)
    is_fixture_data: bool = Field(default=False)
    audit: AuditRecord | None = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def _ensure_no_fabricated_deadline(cls, data: dict) -> dict:
        """Invariant: ANSWER_VERIFIED must have a source with source_url."""
        decisions = data.get("decisions", [])
        for d in decisions:
            if isinstance(d, dict):
                if d.get("outcome") == PolicyOutcome.ANSWER_VERIFIED.value:
                    src = d.get("source")
                    if not src or not (src.get("source_url") if isinstance(src, dict) else getattr(src, "source_url", None)):
                        raise ValueError(
                            "ANSWER_VERIFIED requires a source with a valid source_url. "
                            "Deadlines must never be fabricated."
                        )
            elif isinstance(d, PolicyDecision):
                if d.outcome == PolicyOutcome.ANSWER_VERIFIED:
                    if not d.source or not d.source.source_url:
                        raise ValueError(
                            "ANSWER_VERIFIED requires a source with a valid source_url."
                        )
        return data


class HandoffPayload(BaseModel):
    """Payload sent to TA when the bot cannot answer."""

    reason_code: PolicyOutcome
    original_message: str = Field(default="", description="Sanitized original message excerpt")
    original_message_url: str = Field(default="", description="Link to the original message")
    extracted_entities: ExtractionResult = Field(default_factory=ExtractionResult)
    related_source_ids: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    dedup_key: str = Field(default="", description="Key for deduplication/cooldown")


class AuditRecord(BaseModel):
    """Audit log entry for every pipeline invocation."""

    timestamp: datetime = Field(default_factory=datetime.now)
    raw_input_hash: str = Field(default="", description="SHA256 hash of raw input (not the content)")
    intents: list[Intent] = Field(default_factory=list)
    extraction: ExtractionResult = Field(default_factory=ExtractionResult)
    decisions: list[PolicyDecision] = Field(default_factory=list)
    response_outcome: PolicyOutcome | None = None
    source_ids_used: list[str] = Field(default_factory=list)
    handoff_sent: bool = False
    is_fixture_data: bool = False


# Forward reference resolution
PipelineResponse.model_rebuild()

