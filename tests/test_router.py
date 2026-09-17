import pytest

from phoboi.intent import create_router
from phoboi.models import Intent, LogisticsType


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
