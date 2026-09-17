"""Discord bot adapter — complete skeleton with event handling.

Importable and testable without a Discord token.
To run: set DISCORD_BOT_TOKEN in .env and run `python -m phoboi.adapters.discord_bot`.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from phoboi.config import Config
from phoboi.pipeline import Pipeline
from phoboi.security import escape_mentions

logger = logging.getLogger(__name__)

# discord.py is optional — only import when actually running
if TYPE_CHECKING:
    import discord


class PhobotClient:
    """Discord bot client wrapper.

    Separates bot logic from discord.py to allow testing without the library.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.pipeline = Pipeline(config=config)

    def should_respond(self, message_content: str, bot_mentioned: bool, is_bot: bool) -> bool:
        """Determine if the bot should respond to this message."""
        if is_bot:
            return False
        return bot_mentioned

    def process_message(self, content: str, message_url: str = "") -> str:
        """Process a message and return the response text."""
        result = self.pipeline.process(content, message_url=message_url)
        return result.rendered_text

    def get_handoff_text(self, content: str, message_url: str = "") -> str | None:
        """Get handoff notification text if needed."""
        result = self.pipeline.process(content, message_url=message_url)
        if result.audit and result.audit.handoff_sent:
            ta_role = self.config.discord_ta_role_id
            role_mention = f"<@&{ta_role}>" if ta_role else "TA"
            return (
                f"📨 **Handoff** — {role_mention}\n"
                f"Câu hỏi: {content[:200]}\n"
                f"Lý do: {result.decisions[0].outcome.value}\n"
                f"Link: {message_url}"
            )
        return None


def create_discord_bot(config: Config) -> "discord.Client":
    """Create a discord.py client wired to the phoboi pipeline.

    Requires discord.py to be installed: pip install phoboi[discord]
    """
    try:
        import discord
    except ImportError as e:
        raise ImportError(
            "discord.py is required for Discord mode. "
            "Install with: pip install phoboi[discord]"
        ) from e

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    phobot = PhobotClient(config)

    @client.event
    async def on_ready() -> None:
        logger.info(f"Bot connected as {client.user}")
        if config.discord_guild_id:
            guild = discord.utils.get(client.guilds, id=int(config.discord_guild_id))
            if guild:
                logger.info(f"Connected to guild: {guild.name}")

    @client.event
    async def on_message(message: discord.Message) -> None:
        # Never respond to self
        if message.author == client.user:
            return

        # Check if bot is mentioned
        bot_mentioned = client.user in message.mentions if client.user else False

        if not phobot.should_respond(
            message.content,
            bot_mentioned=bot_mentioned,
            is_bot=message.author.bot,
        ):
            return

        # Process and reply
        try:
            message_url = message.jump_url if hasattr(message, "jump_url") else ""
            response = phobot.process_message(message.content, message_url=message_url)
            response = escape_mentions(response)

            # Reply in thread or same channel
            await message.reply(response, mention_author=False)

            # Check for handoff
            handoff_text = phobot.get_handoff_text(message.content, message_url=message_url)
            if handoff_text and config.discord_handoff_channel_id:
                handoff_channel = client.get_channel(
                    int(config.discord_handoff_channel_id)
                )
                if handoff_channel and hasattr(handoff_channel, "send"):
                    await handoff_channel.send(escape_mentions(handoff_text))

        except Exception:
            logger.exception("Error processing message")
            try:
                await message.reply(
                    "Xin lỗi, mình gặp lỗi khi xử lý câu hỏi. Vui lòng thử lại.",
                    mention_author=False,
                )
            except Exception:
                logger.exception("Error sending error reply")

    return client


def run_discord_bot() -> None:
    """Entry point for running the Discord bot."""
    config = Config()
    if not config.discord_bot_token:
        print("❌ DISCORD_BOT_TOKEN chưa được cấu hình.")
        print("   Đặt token trong file .env (xem .env.example)")
        return

    client = create_discord_bot(config)
    client.run(config.discord_bot_token)


if __name__ == "__main__":
    run_discord_bot()

