from phoboi.discord_pack import DiscordPackRepository
from phoboi.models import PolicyOutcome
from phoboi.pipeline import Pipeline


def _write_pack(tmp_path):
    pack = tmp_path / "messages.csv"
    pack.write_text(
        "msg_id,guild,channel,author,is_bot,msg_type,created_at_vn,reply_to,"
        "mentions_bot,n_attachments,n_chars,content\n"
        'M00001,K4-L2-3,channel_02,D0001,False,message,2026-09-12 10:00,,False,0,30,"Hạn nộp lab 10 ở đâu?"\n'
        'M00002,K4-L2-3,channel_03,BOT,True,message,2026-09-12 10:01,,False,0,20,"Hãy kiểm tra thông báo"\n',
        encoding="utf-8",
    )
    return pack


def test_discord_pack_loads_and_returns_safe_metadata(tmp_path):
    repo = DiscordPackRepository()
    repo.load_from_csv(_write_pack(tmp_path))

    matches = repo.search("deadline hạn nộp lab 10")

    assert repo.count == 2
    assert matches[0].msg_id == "M00001"
    assert not hasattr(matches[0], "content")


def test_pipeline_attaches_pack_context_to_handoff(tmp_path, config, source_repo):
    repo = DiscordPackRepository()
    repo.load_from_csv(_write_pack(tmp_path))
    pipeline = Pipeline(
        config=config,
        source_repo=source_repo,
        discord_pack_repo=repo,
    )

    result = pipeline.process("hạn nộp lab 10 ở đâu")

    assert result.decisions[0].outcome == PolicyOutcome.HANDOFF_NO_SOURCE
    assert result.audit.discord_pack_message_ids[0] == "M00001"
    assert result.handoffs[0].related_discord_message_ids[0] == "M00001"
    assert result.audit.source_ids_used == []
