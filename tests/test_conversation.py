import json
import uuid
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from phoboi.analyzer import deterministic_analysis
from phoboi.api import ApiHandler
from phoboi.conversation import ConversationStore
from phoboi.sources import SyntheticDemoSourceStore


@pytest.fixture
def chat(monkeypatch):
    store = ConversationStore()
    monkeypatch.setattr("phoboi.api.conversations", store)
    monkeypatch.setattr("phoboi.api.Settings.from_env", lambda: SimpleNamespace(source_mode="synthetic_demo", app_env="demo", llm_model="test"))
    monkeypatch.setattr("phoboi.api.source_store_for_mode", lambda *args, **kwargs: SyntheticDemoSourceStore())
    monkeypatch.setattr("phoboi.api.create_provider", lambda settings: None)
    calls = []

    def analyze(self, items):
        msg_id, message, context = items[0]
        calls.append((message, context))
        if message == "fail429":
            error = RuntimeError("quota")
            error.code = 429
            raise error
        return SimpleNamespace(data=SimpleNamespace(results=[deterministic_analysis(msg_id, message)]), provider="test", model="test", live=False, latency_ms=0)

    monkeypatch.setattr("phoboi.api.MessageAnalyzer.analyze_batch", analyze)

    def send(message, session):
        handler = object.__new__(ApiHandler)
        body = json.dumps({"message": message, "session_id": session}).encode()
        handler.path = "/api/chat"
        handler.headers = {"Content-Length": str(len(body))}
        handler.rfile = BytesIO(body)
        handler._send_json = Mock()
        handler.do_POST()
        return handler._send_json.call_args.args

    return send, calls, store


def test_clarification_retains_intent_and_sessions_are_isolated(chat):
    send, calls, _ = chat
    session = str(uuid.uuid4())
    assert send("Hạn nộp lab khi nào?", session)[1]["decision"]["outcome"] == "CLARIFY"
    result = send("Lab 6", session)[1]["decision"]
    assert result["outcome"] == "ANSWER_VERIFIED"
    assert "26/09/2026" in result["response"]
    assert result["handoff"] is None
    assert "Hạn nộp" in calls[-1][0] and calls[-1][1]
    send("Lab 6", str(uuid.uuid4()))
    assert calls[-1] == ("Lab 6", None)


def test_topic_change_clears_pending_and_history_is_bounded(chat):
    send, calls, store = chat
    session = str(uuid.uuid4())
    for _ in range(5):
        send("Hạn nộp Lab 2?", session)
    assert len(store.get(session).turns) == 6
    send("Giải thích YOLO", session)
    send("Lab 6", session)
    assert calls[-1][0] == "Lab 6"
    assert "Hạn nộp" not in calls[-1][1]


def test_quota_does_not_consume_pending_question(chat):
    send, _, store = chat
    session = str(uuid.uuid4())
    send("Hạn nộp lab khi nào?", session)
    before = list(store.get(session).turns)
    status, payload = send("fail429", session)
    assert status == 429 and "decision" not in payload
    assert store.get(session).turns == before
    assert send("Lab 6", session)[1]["decision"]["outcome"] == "ANSWER_VERIFIED"


def test_sessions_expire_and_capacity_is_bounded():
    store = ConversationStore(max_sessions=2)
    first = store.get("first")
    first.touched -= 1801
    assert store.get("first") is not first
    store.get("second")
    store.get("third")
    assert list(store.sessions) == ["second", "third"]


def test_invalid_session_is_rejected(chat):
    send, calls, _ = chat
    assert send("hello", "invalid")[0] == 400
    assert not calls
