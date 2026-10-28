"""Point a user-created bot's updates at the platform (webhook) or clear it (polling / paused / deleted)."""

from __future__ import annotations

from aiogram import Bot

from core.config import PlatformConfig
from core.factory.crypto import webhook_secret

# Everything a template may handle. chat_member / chat_join_request must be requested explicitly.
CHILD_UPDATE_TYPES = [
    "message",
    "edited_message",
    "channel_post",
    "message_reaction",
    "message_reaction_count",
    "callback_query",
    "inline_query",
    "chosen_inline_result",
    "my_chat_member",
    "chat_member",
    "chat_join_request",
]


def child_webhook_path(bot_id: int) -> str:
    return f"/webhook/c/{bot_id}"


async def attach(bot: Bot, bot_id: int, platform: PlatformConfig) -> None:
    """Start delivering updates: a webhook in production, nothing to do for polling (dev)."""
    if not platform.webhook_base_url:
        await bot.delete_webhook(drop_pending_updates=False)
        return
    await bot.set_webhook(
        url=platform.webhook_base_url.rstrip("/") + child_webhook_path(bot_id),
        secret_token=webhook_secret(platform, bot_id),
        allowed_updates=CHILD_UPDATE_TYPES,
        drop_pending_updates=False,
        max_connections=min(platform.webhook_max_connections, 20),
    )


async def detach(bot: Bot) -> None:
    """Stop deliveries: Telegram keeps updates for 24 h, so a resumed bot picks up where it left off."""
    await bot.delete_webhook(drop_pending_updates=False)
