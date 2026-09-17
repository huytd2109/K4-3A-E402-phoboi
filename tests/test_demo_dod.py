from __future__ import annotations

from phoboi.analyzer import deterministic_analysis
from phoboi.handoff import HandoffRegistry
from phoboi.models import Outcome
from phoboi.policy import decide
from phoboi.sources import SyntheticDemoSourceStore


def run(text: str):
    analysis = deterministic_analysis("DEMO", text)
    return decide(analysis, text, SyntheticDemoSourceStore())


def test_demo_verified():
    result = run("Lab 2 deadline?")
    assert result.outcome is Outcome.ANSWER_VERIFIED
    assert result.badge == "DỮ LIỆU DEMO"
    assert result.source_urls == ["https://demo.invalid/official/DEMO-LAB02-DEADLINE-V2"]
    assert "23:59, 18/09/2026 (UTC+7)" in result.response


def test_demo_clarify_exactly_one_question():
    result = run("Hạn nộp lab khi nào?")
    assert result.outcome is Outcome.CLARIFY
    assert result.response.count("?") == 1


def test_demo_no_source():
    result = run("Lab 99 deadline?")
    assert result.outcome is Outcome.HANDOFF_NO_SOURCE
    assert "không đoán" in result.response


def test_demo_conflict():
    result = run("Lab 3 deadline?")
    assert result.outcome is Outcome.HANDOFF_CONFLICT
    assert len(result.source_ids) == 2


def test_handoff_is_deduplicated():
    text = "Lab 99 deadline?"
    analysis = deterministic_analysis("DUP", text)
    registry = HandoffRegistry()
    first = decide(analysis, text, SyntheticDemoSourceStore(), registry)
    second = decide(analysis, text, SyntheticDemoSourceStore(), registry)
    assert first.handoff and not first.handoff.deduplicated
    assert second.handoff and second.handoff.deduplicated
