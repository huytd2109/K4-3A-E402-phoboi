from __future__ import annotations

import json

from phoboi.analyzer import deterministic_analysis
from phoboi.judge import AIJudge
from phoboi.models import JudgeAssessment, StructuredModelResponse
from phoboi.policy import decide
from phoboi.sources import SyntheticDemoSourceStore


class CapturingProvider:
    def __init__(self):
        self.messages = []

    def complete_structured(self, messages, schema, *, model, temperature=0):
        self.messages = messages
        return StructuredModelResponse(
            data=JudgeAssessment(
                intent_alignment=5, conciseness=5, personal_data_boundary=5,
                escalation_appropriateness=5, injection_robustness=5, passed=True,
                reason_codes=["OK"],
            ),
            provider="fake-live", model=model, latency_ms=1, live=True,
        )


def test_ai_judge_payload_does_not_include_expected_label():
    text = "Lab 2 deadline?"
    analysis = deterministic_analysis("J", text)
    decision = decide(analysis, text, SyntheticDemoSourceStore())
    provider = CapturingProvider()
    result = AIJudge(provider, model="judge-model").evaluate(text, analysis, decision)
    payload = json.loads(provider.messages[1]["content"])
    assert result.passed
    assert "expected" not in payload
    assert "chain" not in json.dumps(payload).casefold()

