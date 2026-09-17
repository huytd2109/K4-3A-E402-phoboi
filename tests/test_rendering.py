from phoboi.models import Intent, PolicyDecision, PolicyOutcome
from phoboi.rendering import render_response


def test_duplicate_clarification_text_is_rendered_once():
    missing = ["task (ví dụ: Lab 2, Workshop 1)"]
    decisions = [
        PolicyDecision(
            outcome=PolicyOutcome.CLARIFY,
            intent=Intent.LOGISTICS_DEADLINE,
            missing_fields=missing,
        ),
        PolicyDecision(
            outcome=PolicyOutcome.CLARIFY,
            intent=Intent.LOGISTICS_SUBMISSION,
            missing_fields=missing,
        ),
    ]

    rendered = render_response(decisions)

    assert rendered.count("Mình cần thêm thông tin") == 1
