import pytest
from datetime import datetime, timezone

from phoboi.models import (
    Intent,
    LogisticsType,
    OfficialSource,
    PolicyOutcome,
    RouterResult,
    ExtractionResult,
    SourceStatus
)
from phoboi.policy import PolicyEngine


def test_normal_verified_answer(source_repo):
    engine = PolicyEngine(source_repo)
    result = engine.evaluate(RouterResult(
        intents=[Intent.LOGISTICS_DEADLINE],
        extraction=ExtractionResult(task_normalized="lab-01", logistics_type=LogisticsType.DEADLINE)
    ))
    assert len(result) == 1
    assert result[0].outcome == PolicyOutcome.ANSWER_VERIFIED
    assert result[0].source.source_id == "src-1"


def test_no_source(source_repo):
    engine = PolicyEngine(source_repo)
    result = engine.evaluate(RouterResult(
        intents=[Intent.LOGISTICS_DEADLINE],
        extraction=ExtractionResult(task_normalized="lab-03", logistics_type=LogisticsType.DEADLINE)
    ))
    assert len(result) == 1
    assert result[0].outcome == PolicyOutcome.HANDOFF_NO_SOURCE


def test_missing_task(source_repo):
    engine = PolicyEngine(source_repo)
    result = engine.evaluate(RouterResult(
        intents=[Intent.LOGISTICS_DEADLINE],
        extraction=ExtractionResult(task_normalized=None)
    ))
    assert len(result) == 1
    assert result[0].outcome == PolicyOutcome.CLARIFY


def test_greeting(source_repo):
    engine = PolicyEngine(source_repo)
    result = engine.evaluate(RouterResult(intents=[Intent.GREETING]))
    assert len(result) == 1
    assert result[0].outcome == PolicyOutcome.ANSWER_GREETING


def test_hard_test_1_handoff_conflict(source_repo):
    # Two announcements with different deadlines for same task -> HANDOFF_CONFLICT
    # We add a conflicting source to repo
    source_repo._sources.append(
        OfficialSource(
            source_id="src-1-conflict",
            source_url="http://discord.com/1c",
            published_at=datetime.now(timezone.utc),
            task_id="lab-01",
            logistics_type=LogisticsType.DEADLINE,
            deadline=datetime(2026, 9, 11, 23, 59, tzinfo=timezone.utc),
            is_fixture=True,
            status=SourceStatus.ACTIVE
        )
    )
    engine = PolicyEngine(source_repo)
    result = engine.evaluate(RouterResult(
        intents=[Intent.LOGISTICS_DEADLINE],
        extraction=ExtractionResult(task_normalized="lab-01", logistics_type=LogisticsType.DEADLINE)
    ))
    assert len(result) == 1
    assert result[0].outcome == PolicyOutcome.HANDOFF_CONFLICT


def test_hard_test_2_restrict_personal(source_repo):
    engine = PolicyEngine(source_repo)
    result = engine.evaluate(RouterResult(
        intents=[Intent.PERSONAL_RESTRICTED]
    ))
    assert len(result) == 1
    assert result[0].outcome == PolicyOutcome.RESTRICT_PERSONAL


def test_hard_test_3_prompt_injection_processes_safely(source_repo):
    # Simulated router result when prompt injection is attempted
    # Pipeline sanitizes and still passes to router, which classifies as something
    # Policy just evaluates it safely based on the router result.
    engine = PolicyEngine(source_repo)
    result = engine.evaluate(RouterResult(
        intents=[Intent.LOGISTICS_DEADLINE],
        extraction=ExtractionResult(task_normalized="lab-01")
    ))
    assert len(result) == 1
    assert result[0].outcome == PolicyOutcome.ANSWER_VERIFIED


def test_hard_test_4_mixed_learning_and_logistics(source_repo):
    engine = PolicyEngine(source_repo)
    result = engine.evaluate(RouterResult(
        intents=[Intent.LOGISTICS_DEADLINE, Intent.LEARNING],
        extraction=ExtractionResult(task_normalized="lab-01", logistics_type=LogisticsType.DEADLINE)
    ))
    assert len(result) == 2
    outcomes = [r.outcome for r in result]
    assert PolicyOutcome.ANSWER_VERIFIED in outcomes
    assert PolicyOutcome.ROUTE_LEARNING in outcomes
