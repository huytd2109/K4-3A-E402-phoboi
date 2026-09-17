from phoboi.adapters.discord_bot import PhobotClient


def test_discord_handoff_uses_existing_pipeline_result(config, pipeline):
    client = PhobotClient(config)
    client.pipeline = pipeline

    result = client.process("câu hỏi lạ này là gì?", message_url="https://discord.com/message")
    handoff_text = client.get_handoff_text(result)

    assert handoff_text is not None
    assert "HANDOFF_LOW_CONFIDENCE" in handoff_text
    assert "https://discord.com/message" in handoff_text
