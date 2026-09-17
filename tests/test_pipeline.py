import pytest
from phoboi.models import PolicyOutcome, Intent


def test_pipeline_greeting(pipeline):
    res = pipeline.process("Chào mọi người")
    assert any(d.outcome == PolicyOutcome.ANSWER_GREETING for d in res.decisions)
    # Output should be short, not a full response about a task
    assert len(res.rendered_text) > 0


def test_pipeline_verified_deadline(pipeline):
    res = pipeline.process("hạn nộp lab 1")
    # lab-01 is in the sample_official_sources
    assert any(d.outcome == PolicyOutcome.ANSWER_VERIFIED for d in res.decisions)
    assert "2026" in res.rendered_text
    assert "discord.com/1" in res.rendered_text


def test_pipeline_personal_question(pipeline):
    res = pipeline.process("điểm danh của tôi thế nào")
    assert any(d.outcome == PolicyOutcome.RESTRICT_PERSONAL for d in res.decisions)


def test_pipeline_unknown_task(pipeline):
    res = pipeline.process("hạn nộp lab 10") # unknown task
    outcomes = [d.outcome for d in res.decisions]
    assert PolicyOutcome.HANDOFF_NO_SOURCE in outcomes or PolicyOutcome.CLARIFY in outcomes


def test_fixture_banner_shown_in_demo_mode(pipeline):
    res = pipeline.process("hạn nộp lab 1")
    assert res.is_fixture_data is True
    # The fixture warning banner should be in the rendered text
    assert "demo" in res.rendered_text.lower() or "dữ liệu mẫu" in res.rendered_text.lower()


def test_no_fabricated_deadline_possible(pipeline, monkeypatch):
    # If the policy incorrectly returns ANSWER_VERIFIED without a valid source,
    # PipelineResponse must catch it during validation
    
    class MockPolicyEngine:
        def __init__(self, *args, **kwargs):
            pass
        def evaluate(self, *args, **kwargs):
            from phoboi.models import PolicyDecision, OfficialSource, LogisticsType, PolicyOutcome, Intent
            from datetime import datetime, timezone
            return [
                PolicyDecision(
                    outcome=PolicyOutcome.ANSWER_VERIFIED,
                    intent=Intent.LOGISTICS_DEADLINE,
                    source=OfficialSource(
                        source_id="mock-1",
                        source_url="", # Invalid empty source URL
                        published_at=datetime.now(timezone.utc),
                        task_id="lab",
                        logistics_type=LogisticsType.DEADLINE
                    )
                )
            ]

    import phoboi.pipeline
    monkeypatch.setattr(phoboi.pipeline, "PolicyEngine", MockPolicyEngine)
    
    # Needs a new pipeline to pick up the monkeypatched PolicyEngine
    from phoboi.pipeline import Pipeline
    mock_pipeline = Pipeline(config=pipeline._config, source_repo=pipeline._source_repo)
    
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        mock_pipeline.process("hạn nộp lab 1")


def test_pipeline_does_not_answer_from_another_cohort(pipeline):
    res = pipeline.process("deadline lab 1 K5")
    assert res.decisions[0].outcome == PolicyOutcome.HANDOFF_NO_SOURCE


def test_pipeline_handles_deadline_and_link_independently(pipeline):
    res = pipeline.process("deadline và link nộp lab 1")
    assert [decision.outcome for decision in res.decisions] == [
        PolicyOutcome.ANSWER_VERIFIED,
        PolicyOutcome.ANSWER_VERIFIED,
    ]
    assert res.rendered_text.count("Hạn nộp Lab 1") == 1
    assert "Link cho Lab 1" in res.rendered_text


def test_handoff_payload_redacts_pii(pipeline):
    res = pipeline.process("giúp câu lạ 0987654321?")
    assert res.decisions[0].outcome == PolicyOutcome.HANDOFF_LOW_CONFIDENCE
    assert res.handoffs
    assert "0987654321" not in res.handoffs[0].original_message
    assert "[IDENTIFIER]" in res.handoffs[0].original_message
    assert "pii_detected" in res.audit.security_flags
