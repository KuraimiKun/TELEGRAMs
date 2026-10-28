"""Banning and maintenance middlewares.

Registered as *outer* middlewares on the message / callback_query / inline_query observers so that the
event they receive is the concrete object (not the wrapping ``Update``).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from core.db.models import BotUser
from core.middlewares._event import is_payment_event, notify
from core.sdk.context import BotContext


class BanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: BotUser | None = data.get("user")
        if user and (user.is_banned or (user.profile and user.profile.is_globally_banned)):
            if is_payment_event(event):
                # Never lose a payment that Telegram already charged.
                return await handler(event, data)
            t = data.get("t")
            await notify(event, t("banned") if t else "🚫 You are banned.")
            return None
        return await handler(event, data)


class MaintenanceMiddleware(BaseMiddleware):
    def __init__(self, ctx: BotContext) -> None:
        self.ctx = ctx

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        if (tg_user and self.ctx.is_admin(tg_user.id)) or is_payment_event(event):
            return await handler(event, data)

        stg = await self.ctx.settings.get()
        if stg.maintenance:
            t = data.get("t")
            await notify(event, t("maintenance") if t else "🛠 The bot is under maintenance.")
            return None
        return await handler(event, data)
