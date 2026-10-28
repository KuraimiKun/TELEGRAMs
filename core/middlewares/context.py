"""BotContext injection middleware: injects per-bot context and services into event data."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from core.observability import UPDATE_SECONDS, UPDATES
from core.sdk.context import BotContext


class BotContextMiddleware(BaseMiddleware):
    def __init__(self, ctx: BotContext) -> None:
        self.ctx = ctx

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["ctx"] = self.ctx
        data["config"] = self.ctx.platform
        data["bot_env"] = self.ctx.env
        data["redis"] = self.ctx.redis
        data["users"] = self.ctx.users
        data["settings_service"] = self.ctx.settings
        data["subs"] = self.ctx.subs
        data["vip"] = self.ctx.subs  # compatibility alias
        data["payments"] = self.ctx.payments
        data["stats"] = self.ctx.stats
        data["broadcast"] = self.ctx.broadcast
        data["groups"] = self.ctx.groups

        # Inject extra bot-specific services attached in module.setup()
        for k, v in self.ctx.extras.items():
            data[k] = v

        update_type = getattr(event, "event_type", "unknown") if isinstance(event, Update) else type(event).__name__
        tg_user = data.get("event_from_user")
        structlog.contextvars.bind_contextvars(
            bot=self.ctx.slug,
            update_id=getattr(event, "update_id", None),
            user_id=tg_user.id if tg_user else None,
        )
        UPDATES.labels(self.ctx.metric_name, update_type).inc()
        started = time.perf_counter()
        try:
            return await handler(event, data)
        finally:
            UPDATE_SECONDS.labels(self.ctx.metric_name).observe(time.perf_counter() - started)
            structlog.contextvars.unbind_contextvars("bot", "update_id", "user_id")
