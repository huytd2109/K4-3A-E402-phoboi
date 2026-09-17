from __future__ import annotations

import json
from pathlib import Path

from phoboi.models import Analysis, Decision, JudgeAssessment
from phoboi.providers.base import LLMProvider
from phoboi.security import redact_for_model

JUDGE_PROMPT_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "prompts" / "ai_judge_v1.md"


class AIJudge:
    """Optional live qualitative judge, kept separate from deterministic safety metrics."""

    def __init__(self, provider: LLMProvider, *, model: str):
        self.provider = provider
        self.model = model
        self.prompt = JUDGE_PROMPT_PATH.read_text(encoding="utf-8")

    def evaluate(self, message: str, analysis: Analysis, decision: Decision) -> JudgeAssessment:
        payload = {
            "message": "[REDACTED_PERSONAL_REQUEST]" if analysis.personal_data_request else redact_for_model(message),
            "observed_intents": [item.value for item in analysis.intents],
            "personal_data_request": analysis.personal_data_request,
            "prompt_injection_detected": analysis.prompt_injection_detected,
            "outcome": decision.outcome.value,
            "response": decision.response,
            "has_provenance": bool(decision.source_urls),
        }
        response = self.provider.complete_structured(
            [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            JudgeAssessment,
            model=self.model,
            temperature=0,
        )
        if not response.live:
            raise RuntimeError("AI judge requires a live provider")
        return JudgeAssessment.model_validate(response.data)
