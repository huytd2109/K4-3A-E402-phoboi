import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from phoboi.models import (
    OfficialSource,
    LogisticsType,
    PipelineResponse,
    PolicyDecision,
    PolicyOutcome,
    Intent,
)


def test_official_source_validates_correctly():
    source = OfficialSource(
        source_id="src-123",
        source_url="https://discord.com/msg",
        published_at=datetime.now(timezone.utc),
        task_id="lab-01",
        logistics_type=LogisticsType.DEADLINE,
        deadline=datetime.now(timezone.utc),
        is_fixture=True,
    )
    assert source.source_id == "src-123"


def test_official_source_rejects_missing_required_fields():
    with pytest.raises(ValidationError):
        OfficialSource(
            source_url="https://discord.com/msg",
            # missing source_id, published_at, task_id, logistics_type
        )


def test_policy_decision_answer_verified_requires_source_url():
    # If a decision is ANSWER_VERIFIED but missing a source (or source_url),
    # PipelineResponse must reject it
    with pytest.raises(ValidationError):
        PipelineResponse(
            decisions=[PolicyDecision(
                outcome=PolicyOutcome.ANSWER_VERIFIED,
                intent=Intent.LOGISTICS_DEADLINE,
                source=None # No source
            )],
            rendered_text="hạn nộp là..."
        )


def test_intent_and_policy_outcome_enum_values():
    assert Intent.GREETING.value == "GREETING"
    assert PolicyOutcome.ANSWER_VERIFIED.value == "ANSWER_VERIFIED"


def test_official_source_rejects_invalid_url_and_naive_deadline():
    with pytest.raises(ValidationError):
        OfficialSource(
            source_id="bad-url",
            source_url="not-a-url",
            published_at=datetime.now(timezone.utc),
            task_id="lab-01",
            logistics_type=LogisticsType.DEADLINE,
            deadline=datetime.now(timezone.utc),
        )

    with pytest.raises(ValidationError):
        OfficialSource(
            source_id="naive-time",
            source_url="https://discord.com/message",
            published_at=datetime.now(timezone.utc),
            task_id="lab-01",
            logistics_type=LogisticsType.DEADLINE,
            deadline=datetime.now(),
        )
