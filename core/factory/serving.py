"""Delivering updates to user-created bots: one dynamic webhook route, or polling in development."""

from __future__ import annotations

import asyncio
import contextlib

from aiogram import Dispatcher
from aiohttp import web

from core.config import PlatformConfig
from core.factory.crypto import verify_webhook
from core.factory.runtime import ChildRegistry
from core.factory.webhooks import CHILD_UPDATE_TYPES
from core.log import get_logger

log = get_logger(__name__)

SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"


class ChildWebhook:
    """``POST /webhook/c/{bot_id}``: verify the per-bot secret, then process the update in the background."""

    def __init__(self, registry: ChildRegistry, platform: PlatformConfig) -> None:
        self.registry = registry
        self.platform = platform
        self._tasks: set[asyncio.Task] = set()

    def register(self, app: web.Application) -> None:
        app.router.add_post("/webhook/c/{bot_id:\\d+}", self.handle)

    async def handle(self, request: web.Request) -> web.Response:
        bot_id = int(request.match_info["bot_id"])
        if not verify_webhook(self.platform, bot_id, request.headers.get(SECRET_HEADER, "")):
            return web.Response(status=401)
        try:
            data = await request.json()
        except ValueError:
            return web.Response(status=400)
        runtime = await self.registry.get(bot_id)
        if runtime is not None:  # paused/unknown bots: acknowledge so Telegram stops retrying
            if runtime.ctx.module.durable_ingress:
                # Its durable inbox must be committed before acknowledging delivery.
                await runtime.dp.feed_raw_update(runtime.ctx.bot, data)
            else:
                task = asyncio.create_task(runtime.dp.feed_raw_update(runtime.ctx.bot, data))
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
        return web.json_response({})

    async def drain(self, timeout: float = 20.0) -> None:
        if self._tasks:
            await asyncio.wait(set(self._tasks), timeout=timeout)


class ChildPoller:
    """Development only (no WEBHOOK_BASE_URL): long-poll each active user bot, restarting it on changes."""

    def __init__(self, registry: ChildRegistry, limit: int) -> None:
        self.registry = registry
        self.limit = limit
        self._polls: dict[int, tuple[Dispatcher, asyncio.Task]] = {}
        registry.on_change(self.restart)

    async def start(self) -> None:
        for bot_id in (await self.registry.active_ids())[: self.limit]:
            await self._start(bot_id)

    async def _start(self, bot_id: int) -> None:
        if bot_id in self._polls or len(self._polls) >= self.limit:
            return
        runtime = await self.registry.get(bot_id)
        if runtime is None:
            return
        dp, bot = runtime.dp, runtime.ctx.bot
        with contextlib.suppress(Exception):
            await bot.delete_webhook(drop_pending_updates=False)
        task = asyncio.create_task(
            dp.start_polling(bot, handle_signals=False, close_bot_session=False, allowed_updates=CHILD_UPDATE_TYPES),
            name=f"polling:c{bot_id}",
        )
        self._polls[bot_id] = (dp, task)
        log.info("factory_child_polling", bot_id=bot_id)

    async def _stop(self, bot_id: int) -> None:
        entry = self._polls.pop(bot_id, None)
        if entry is None:
            return
        dp, task = entry
        with contextlib.suppress(RuntimeError):
            await dp.stop_polling()
        await asyncio.gather(task, return_exceptions=True)

    async def restart(self, bot_id: int) -> None:
        await self._stop(bot_id)
        await self._start(bot_id)

    async def close(self) -> None:
        for bot_id in list(self._polls):
            await self._stop(bot_id)
