from __future__ import annotations

import os
import re
from dataclasses import dataclass

from phoboi.models import Decision
from phoboi.security import escape_mentions


@dataclass(frozen=True)
class DiscordConfig:
    bot_token: str
    guild_id: int
    ta_role_id: int
    handoff_channel_id: int

    @classmethod
    def from_env(cls) -> "DiscordConfig":
        values = {name: os.getenv(name, "") for name in (
            "DISCORD_BOT_TOKEN", "DISCORD_GUILD_ID", "DISCORD_TA_ROLE_ID", "DISCORD_HANDOFF_CHANNEL_ID"
        )}
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ValueError(f"missing Discord configuration: {', '.join(missing)}")
        for name in ("DISCORD_GUILD_ID", "DISCORD_TA_ROLE_ID", "DISCORD_HANDOFF_CHANNEL_ID"):
            if not re.fullmatch(r"\d{15,22}", values[name]):
                raise ValueError(f"invalid {name}")
        return cls(
            bot_token=values["DISCORD_BOT_TOKEN"],
            guild_id=int(values["DISCORD_GUILD_ID"]),
            ta_role_id=int(values["DISCORD_TA_ROLE_ID"]),
            handoff_channel_id=int(values["DISCORD_HANDOFF_CHANNEL_ID"]),
        )


def public_reply(decision: Decision) -> str:
    return escape_mentions(decision.response)


def handoff_message(decision: Decision, config: DiscordConfig) -> str | None:
    if decision.handoff is None or decision.handoff.deduplicated:
        return None
    handoff = decision.handoff
    sources = ", ".join(handoff.related_source_ids) or "không có nguồn chính thức"
    return (
        f"<@&{config.ta_role_id}> cần kiểm tra logistics. "
        f"Ref: `{handoff.question_ref}` · reason: `{handoff.reason_code}` · "
        f"task: `{handoff.entities.task or 'unknown'}` · sources: `{sources}`. "
        "Không có dữ liệu cá nhân hoặc nội dung raw trong handoff này."
    )


def create_discord_client(config: DiscordConfig, on_message_callback):
    """Create the optional Discord runtime without connecting during import/tests."""
    import discord

    intents = discord.Intents.none()
    intents.guilds = True
    intents.guild_messages = True
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_message(message):
        if message.author.bot or message.guild is None or message.guild.id != config.guild_id:
            return
        if client.user not in message.mentions:
            return
        decision = await on_message_callback(str(message.id), message.content)
        await message.reply(public_reply(decision), mention_author=False, allowed_mentions=discord.AllowedMentions.none())
        handoff = handoff_message(decision, config)
        if handoff:
            channel = client.get_channel(config.handoff_channel_id)
            if channel is not None:
                await channel.send(handoff, allowed_mentions=discord.AllowedMentions(roles=True, users=False, everyone=False))
    return client

