from __future__ import annotations

from phoboi.analyzer import deterministic_analysis
from phoboi.discord_adapter import DiscordConfig, handoff_message, public_reply
from phoboi.policy import decide
from phoboi.sources import RealDatasetSourceStore


def test_public_reply_escapes_mentions():
    analysis = deterministic_analysis("X", "Lab 2 deadline?")
    decision = decide(analysis, "Lab 2 deadline?", RealDatasetSourceStore())
    decision.response += " @everyone"
    assert "@\u200beveryone" in public_reply(decision)


def test_handoff_tags_only_configured_role_and_contains_no_raw_query():
    text = "Lab 2 deadline? raw-do-not-copy"
    analysis = deterministic_analysis("X", text)
    decision = decide(analysis, text, RealDatasetSourceStore())
    config = DiscordConfig("not-logged", 111111111111111, 222222222222222, 333333333333333)
    rendered = handoff_message(decision, config)
    assert rendered and rendered.startswith("<@&222222222222222>")
    assert text not in rendered
    assert "@everyone" not in rendered
