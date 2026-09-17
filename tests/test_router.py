import pytest

from phoboi.intent import create_router
from phoboi.intent.gemini import GeminiIntentRouter, HybridIntentRouter
from phoboi.models import ExtractionResult, Intent, LogisticsType, RouterResult


@pytest.fixture
def router():
    return create_router("rule_based")


def test_router_greeting_detection(router):
    for msg in ["Chào mọi người", "hello", "hi", "chào buổi sáng"]:
        res = router.classify(msg)
        assert Intent.GREETING in res.intents
        assert len(res.intents) == 1


def test_router_deadline_detection(router):
    for msg in ["deadline lab 2", "hạn nộp lab 2 khi nào"]:
        res = router.classify(msg)
        assert Intent.LOGISTICS_DEADLINE in res.intents
        assert res.extraction.task_normalized == "lab-02"


def test_router_link_detection(router):
    msg = "link nộp lab 2"
    res = router.classify(msg)
    assert Intent.LOGISTICS_LINK in res.intents
    assert res.extraction.logistics_type == LogisticsType.LINK


def test_router_submission_detection(router):
    msg = "cách nộp lab 2"
    res = router.classify(msg)
    assert Intent.LOGISTICS_SUBMISSION in res.intents


def test_router_personal_detection(router):
    msg = "điểm danh của tôi thế nào"
    res = router.classify(msg)
    assert Intent.PERSONAL_RESTRICTED in res.intents


def test_router_learning_detection(router):
    msg = "cài đặt CVAT thế nào"
    res = router.classify(msg)
    assert Intent.LEARNING in res.intents


def test_router_multi_intent(router):
    msg = "hạn nộp lab 2 và cách cài đặt CVAT"
    res = router.classify(msg)
    assert Intent.LOGISTICS_DEADLINE in res.intents
    assert Intent.LEARNING in res.intents
    assert res.extraction.task_normalized == "lab-02"


def test_router_out_of_scope(router):
    msg = "thời tiết hôm nay"
    res = router.classify(msg)
    assert Intent.OUT_OF_SCOPE in res.intents


def test_router_entity_extraction(router):
    msg = "hạn nộp lab 2 k4 l3-4"
    res = router.classify(msg)
    assert res.extraction.task_normalized == "lab-02"
    assert res.extraction.cohort == "K4"
    assert res.extraction.class_scope == "L3-4"


def test_router_extracts_non_k4_cohort(router):
    res = router.classify("deadline lab 1 K5")
    assert res.extraction.cohort == "K5"


def test_gemini_router_falls_back_transparently_without_key():
    router = create_router(
        "gemini",
        api_key="",
        model="gemini-test-model",
        timeout_seconds=1,
    )
    res = router.classify("deadline lab 2")

    assert Intent.LOGISTICS_DEADLINE in res.intents
    assert res.provider == "rule_based"
    assert res.used_fallback is True
    assert res.fallback_reason == "missing_api_key"
    assert res.model == "gemini-test-model"


def test_gemini_router_normalizes_provider_label_variants():
    intents = GeminiIntentRouter._normalize_intents(
        ["deadline", " learning ", "LOGISTICS-DEADLINE", "not-a-real-intent"]
    )

    assert intents == [Intent.LOGISTICS_DEADLINE, Intent.LEARNING]
    assert (
        GeminiIntentRouter._normalize_logistics_type("LOGISTICS_DEADLINE")
        == LogisticsType.DEADLINE
    )


def test_gemini_router_uses_unknown_when_provider_returns_no_valid_intent():
    assert GeminiIntentRouter._normalize_intents([]) == [Intent.UNKNOWN]
    assert GeminiIntentRouter._normalize_intents(["not-a-real-intent"]) == [
        Intent.UNKNOWN
    ]


def test_hybrid_router_uses_deterministic_entity_canonicalization():
    class StaticRouter:
        def __init__(self, result):
            self.result = result

        def classify(self, _text):
            return self.result

    primary = StaticRouter(
        RouterResult(
            intents=[Intent.LOGISTICS_DEADLINE],
            extraction=ExtractionResult(
                task="lập đội",
                task_normalized="lap-doi",
                logistics_type=LogisticsType.DEADLINE,
            ),
            provider="gemini",
            model="gemini-test",
        )
    )
    deterministic = StaticRouter(
        RouterResult(
            intents=[Intent.LOGISTICS_DEADLINE],
            extraction=ExtractionResult(
                task="lập đội",
                task_normalized="team-formation",
                logistics_type=LogisticsType.DEADLINE,
            ),
        )
    )

    result = HybridIntentRouter(primary=primary, fallback=deterministic).classify(
        "deadline lập đội"
    )

    assert result.provider == "gemini"
    assert result.used_fallback is False
    assert result.extraction.task_normalized == "team-formation"
