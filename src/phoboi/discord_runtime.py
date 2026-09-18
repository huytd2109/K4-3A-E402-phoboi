from __future__ import annotations

import asyncio

from phoboi.analyzer import MessageAnalyzer
from phoboi.config import Settings
from phoboi.conversation import conversations
from phoboi.discord_adapter import DiscordConfig, create_discord_client
from phoboi.policy import decide
from phoboi.providers.factory import create_provider
from phoboi.sources import source_store_for_mode


async def run() -> None:
    settings = Settings.from_env()
    config = DiscordConfig.from_env()
    store = source_store_for_mode(settings.source_mode, app_env=settings.app_env)
    analyzer = MessageAnalyzer(create_provider(settings), model=settings.llm_model)

    async def on_message(message_id: str, message: str):
        conversation = conversations.get(message_id)
        with conversation.lock:
            resolved = conversation.resolve_reply(message)
            response = await asyncio.to_thread(
                analyzer.analyze_batch,
                [(message_id, resolved, conversation.context())],
            )
            analysis = response.data.results[0]
            decision = decide(analysis, message, store)
            conversation.remember(resolved, analysis, decision)
            return decision

    client = create_discord_client(config, on_message)
    await client.start(config.bot_token)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()