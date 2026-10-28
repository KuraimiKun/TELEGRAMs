"""Custom aiogram filters for platform core."""

from __future__ import annotations

from aiogram.filters import Filter
from aiogram.types import Message, TelegramObject

from core.sdk.context import BotContext


class IsAdmin(Filter):
    """Filter that checks if the invoking user is a bot admin or super-admin."""

    async def __call__(self, event: TelegramObject, ctx: BotContext) -> bool:
        user = getattr(event, "from_user", None)
        return bool(user and ctx.is_admin(user.id))


class IsSuperAdmin(Filter):
    """Filter that checks if the invoking user is a platform super-admin."""

    async def __call__(self, event: TelegramObject, ctx: BotContext) -> bool:
        user = getattr(event, "from_user", None)
        return bool(user and ctx.is_super_admin(user.id))


class ChatType(Filter):
    """Filter for Telegram chat types ('private', 'group', 'supergroup', 'channel')."""

    def __init__(self, *types: str) -> None:
        self.types = set(types)

    async def __call__(self, message: Message) -> bool:
        return message.chat.type in self.types
