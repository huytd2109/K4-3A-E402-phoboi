from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class Intent(str, Enum):
    GREETING = "GREETING"
    LOGISTICS_DEADLINE = "LOGISTICS_DEADLINE"
    LOGISTICS_LINK = "LOGISTICS_LINK"
    LOGISTICS_SUBMISSION = "LOGISTICS_SUBMISSION"
    LEARNING = "LEARNING"
    PERSONAL_RESTRICTED = "PERSONAL_RESTRICTED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    UNKNOWN = "UNKNOWN"


class Outcome(str, Enum):
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
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"


class Entities(BaseModel):
    task: str | None = None
    cohort: str | None = None
    class_scope: str | None = None
    logistics_type: str | None = None


class Analysis(BaseModel):
    msg_id: str
    is_question: bool
    intents: list[Intent]
    entities: Entities = Field(default_factory=Entities)
    personal_data_request: bool = False
    prompt_injection_detected: bool = False
    needs_clarification: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    reason_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def clarification_is_consistent(self) -> "Analysis":
        if self.needs_clarification != bool(self.missing_fields):
            raise ValueError("needs_clarification must match missing_fields")
        return self


class AnalysisBatch(BaseModel):
    results: list[Analysis]


class OfficialSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_url: HttpUrl | None = None
    source_type: str
    guild_id: str | None = None
    channel_id: str | None = None
    message_id: str | None = None
    published_by_role: str
    published_at: datetime
    effective_from: datetime
    task_id: str
    task_aliases: list[str] = Field(default_factory=list)
    cohort: str
    class_scope: str
    logistics_type: str
    deadline: datetime | None = None
    submission_url: HttpUrl | None = None
    supersedes: list[str] = Field(default_factory=list)
    status: SourceStatus = SourceStatus.ACTIVE
    is_fixture: bool

    @property
    def provenance_url(self) -> str | None:
        if self.source_url:
            return str(self.source_url)
        if self.guild_id and self.channel_id and self.message_id:
            return f"https://discord.com/channels/{self.guild_id}/{self.channel_id}/{self.message_id}"
        return None

    @property
    def has_resolvable_provenance(self) -> bool:
        return self.provenance_url is not None

    @model_validator(mode="after")
    def validate_source_contract(self) -> "OfficialSource":
        if self.source_type == "synthetic_demo" and not self.is_fixture:
            raise ValueError("synthetic_demo sources must be fixtures")
        if self.is_fixture and self.source_type != "synthetic_demo":
            raise ValueError("fixtures must use source_type=synthetic_demo")
        if self.source_type != "dataset_candidate" and not self.has_resolvable_provenance:
            raise ValueError("official/demo sources require resolvable provenance")
        if self.deadline and self.deadline.utcoffset() is None:
            raise ValueError("deadline must include timezone")
        return self


class CandidateFact(BaseModel):
    source_id: str
    source_type: str = "dataset_candidate"
    trust_label: str = "UNVERIFIED CANDIDATE"
    task_id: str | None = None
    cohort: str | None = None
    class_scope: str | None = None
    logistics_type: str | None = None
    is_fixture: bool = False


class Handoff(BaseModel):
    handoff_id: str
    reason_code: str
    question_ref: str
    entities: Entities
    related_source_ids: list[str] = Field(default_factory=list)
    original_message_url: str | None = None
    ta_role_id: str | None = None
    deduplicated: bool = False


class Decision(BaseModel):
    msg_id: str
    intents: list[Intent]
    outcome: Outcome
    response: str
    prompt_injection_detected: bool = False
    source_ids: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    badge: str | None = None
    handoff: Handoff | None = None
    learning_route: str | None = None

    @model_validator(mode="after")
    def verified_requires_provenance(self) -> "Decision":
        if self.outcome == Outcome.ANSWER_VERIFIED and not self.source_urls:
            raise ValueError("ANSWER_VERIFIED requires resolvable provenance")
        return self


class StructuredModelResponse(BaseModel):
    data: Any
    provider: str
    model: str
    latency_ms: float = Field(ge=0)
    input_tokens: int | None = None
    output_tokens: int | None = None
    request_id: str | None = None
    live: bool


class JudgeAssessment(BaseModel):
    intent_alignment: int = Field(ge=1, le=5)
    conciseness: int = Field(ge=1, le=5)
    personal_data_boundary: int = Field(ge=1, le=5)
    escalation_appropriateness: int = Field(ge=1, le=5)
    injection_robustness: int = Field(ge=1, le=5)
    passed: bool
    reason_codes: list[str] = Field(default_factory=list)


class DatasetMessage(BaseModel):
    record_id: str
    msg_id: str
    guild: str
    channel: str
    author: str
    is_bot: bool
    msg_type: str
    created_at_vn: str
    reply_to: str | None = None
    mentions_bot: bool
    n_attachments: int
    n_chars: int
    content: str
