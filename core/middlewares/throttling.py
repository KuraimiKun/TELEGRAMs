"""Throttling (rate limiting) middleware using bot-scoped Redis keys."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import Message, TelegramObject

from core.db.models import BotUser
from core.middlewares._event import is_payment_event, notify
from core.sdk.context import BotContext

BACKLOG_AGE = timedelta(seconds=10)


def _is_group_message(event: TelegramObject) -> bool:
    """Group traffic is not throttled: moderation bots must see every message (flood/lock checks), and a
    "slow down" reply in a group would itself be spam. Bots ration group work with their own quotas."""
    return isinstance(event, Message) and event.chat.type != ChatType.PRIVATE


def _is_backlog(event: TelegramObject) -> bool:
    """Messages queued while the bot was down/redeploying arrive in a burst: they are real requests,
    not flooding, so they must not be throttled away."""
    return isinstance(event, Message) and event.date is not None and event.date < datetime.now(UTC) - BACKLOG_AGE


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, ctx: BotContext) -> None:
        self.ctx = ctx

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: BotUser | None = data.get("user")
        if (
            not user
            or self.ctx.is_admin(user.id)
            or is_payment_event(event)
            or _is_backlog(event)
            or _is_group_message(event)
            or self.ctx.module.throttle_exempt(event)
        ):
            return await handler(event, data)

        rate_ms = max(1, int(self.ctx.module.throttle_rate(user) * 1000))
        key = self.ctx.keys("throttle", type(event).__name__, user.id)

        # Atomic: only the first event inside the window acquires the key.
        if not await self.ctx.redis.set(key, "1", nx=True, px=rate_ms):
            # Warn once per window instead of on every dropped event.
            warn_key = self.ctx.keys("throttle_warned", user.id)
            if await self.ctx.redis.set(warn_key, "1", nx=True, px=max(rate_ms, 3000)):
                t = data.get("t")
                await notify(event, t("throttled") if t else "🐢 Slow down!", alert=False)
            return None

        return await handler(event, data)
