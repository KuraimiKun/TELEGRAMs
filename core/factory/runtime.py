"""Lazily-built runtimes (context + dispatcher) of user-created bots, shared by the gateway and scheduler.

Thousands of user bots cannot each hold a context in memory forever, so runtimes live in an LRU cache and are
built on their first update. Changes made through the factory (pause, token rotation, deletion…) are
published on Redis and every process drops its cached copy.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from aiogram import Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramUnauthorizedError
from sqlalchemy import select

from core.config import PlatformConfig
from core.db.models import Bot as BotRecord
from core.db.models import ChildBot
from core.factory.children import CHANGED_CHANNEL
from core.factory.crypto import decrypt_token
from core.log import get_logger
from core.observability import CHILD_BOTS
from core.sdk.context import BotContext, ChildInfo
from core.sdk.module import BotModule
from core.sdk.registry import SharedInfra, factory_templates, init_context

log = get_logger(__name__)

NEGATIVE_TTL = 30.0  # seconds an unknown/paused bot id is remembered as "nothing to run"


@dataclass(slots=True)
class ChildRuntime:
    ctx: BotContext
    dp: Dispatcher


class ChildRegistry:
    def __init__(
        self,
        platform: PlatformConfig,
        infra: SharedInfra,
        stop: asyncio.Event,
        *,
        max_loaded: int = 2000,
        build_dispatcher: Callable[[BotContext], Dispatcher] | None = None,
        templates: dict[str, BotModule] | None = None,
    ) -> None:
        self.platform = platform
        self.infra = infra
        self.stop = stop
        self.max_loaded = max_loaded
        self.templates = templates if templates is not None else factory_templates()
        if build_dispatcher is None:
            from core.runtime.dispatcher import build_dispatcher as default_builder

            build_dispatcher = default_builder
        self._build_dispatcher = build_dispatcher
        self._loaded: OrderedDict[int, ChildRuntime] = OrderedDict()
        self._missing: dict[int, float] = {}
        self._locks: dict[int, asyncio.Lock] = {}
        # One HTTP session for every child bot when there is no shared local Bot API session.
        self._own_session: BaseSession | None = None
        self._listeners: list[Callable[[int], Awaitable[None]]] = []

    @property
    def enabled(self) -> bool:
        return self.platform.factory_secret_key is not None and bool(self.templates)

    def _session(self) -> BaseSession:
        if self.infra.session is not None:
            return self.infra.session
        if self._own_session is None:
            self._own_session = AiohttpSession()
        return self._own_session

    def on_change(self, callback: Callable[[int], Awaitable[None]]) -> None:
        """Called with the bot id after a factory change was applied (used by the dev polling supervisor)."""
        self._listeners.append(callback)

    def loaded(self) -> list[ChildRuntime]:
        return list(self._loaded.values())

    async def get(self, bot_id: int) -> ChildRuntime | None:
        runtime = self._loaded.get(bot_id)
        if runtime is not None:
            self._loaded.move_to_end(bot_id)
            return runtime
        if time.monotonic() < self._missing.get(bot_id, 0):
            return None
        lock = self._locks.setdefault(bot_id, asyncio.Lock())
        async with lock:
            runtime = self._loaded.get(bot_id)
            if runtime is None:
                runtime = await self._build(bot_id)
            self._locks.pop(bot_id, None)
            return runtime

    async def _build(self, bot_id: int) -> ChildRuntime | None:
        async with self.infra.sm() as session:
            row = (
                await session.execute(
                    select(ChildBot, BotRecord.username)
                    .join(BotRecord, BotRecord.id == ChildBot.factory_bot_id)
                    .where(ChildBot.bot_id == bot_id)
                )
            ).first()
        if row is None or row[0].status != "active":
            self._missing[bot_id] = time.monotonic() + NEGATIVE_TTL
            return None
        child, factory_username = row[0], row[1] or ""
        module = self.templates.get(child.template)
        token = decrypt_token(self.platform, child.token_enc, expected_bot_id=child.bot_id)
        if module is None or token is None:
            log.error("factory_child_unloadable", bot_id=bot_id, template=child.template, has_token=bool(token))
            self._missing[bot_id] = time.monotonic() + NEGATIVE_TTL
            return None

        env = module.env_model.model_validate({"token": token, "admin_ids": [child.owner_id]})
        info = ChildInfo(
            owner_id=child.owner_id, template=child.template, factory_username=factory_username, branding=child.branding
        )
        try:
            ctx = await init_context(module, self.platform, self.infra, env, child=info, session=self._session())
            ctx.shutdown = self.stop
            dp = self._build_dispatcher(ctx)
        except TelegramUnauthorizedError:
            log.warning("factory_child_token_revoked", bot_id=bot_id)
            await self._mark_error(bot_id, "token revoked in @BotFather")
            self._missing[bot_id] = time.monotonic() + NEGATIVE_TTL
            return None
        except Exception as e:
            log.exception("factory_child_build_failed", bot_id=bot_id, error=str(e))
            self._missing[bot_id] = time.monotonic() + NEGATIVE_TTL
            return None

        runtime = ChildRuntime(ctx=ctx, dp=dp)
        self._loaded[bot_id] = runtime
        self._missing.pop(bot_id, None)
        # Evicting only drops references: storage, Redis and the HTTP session are shared by every bot in the
        # process (RedisStorage.close() would close the shared pool), and in-flight updates finish normally.
        while len(self._loaded) > self.max_loaded:
            self._loaded.popitem(last=False)
        CHILD_BOTS.set(len(self._loaded))
        log.info("factory_child_loaded", bot_id=bot_id, template=child.template)
        return runtime

    async def _mark_error(self, bot_id: int, error: str) -> None:
        from sqlalchemy import update

        with contextlib.suppress(Exception):
            async with self.infra.sm() as session:
                await session.execute(
                    update(ChildBot).where(ChildBot.bot_id == bot_id).values(status="error", last_error=error)
                )
                await session.commit()

    async def evict(self, bot_id: int) -> None:
        self._missing.pop(bot_id, None)
        if self._loaded.pop(bot_id, None) is not None:
            CHILD_BOTS.set(len(self._loaded))
        for callback in self._listeners:
            with contextlib.suppress(Exception):
                await callback(bot_id)

    async def listen(self) -> None:
        """Apply factory changes published by any process until ``stop`` fires."""
        pubsub = self.infra.redis.pubsub()
        await pubsub.subscribe(CHANGED_CHANNEL)
        try:
            while not self.stop.is_set():
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if not msg:
                    continue
                with contextlib.suppress(ValueError, TypeError):
                    raw = msg["data"]
                    await self.evict(int(raw.decode() if isinstance(raw, bytes) else raw))
        finally:
            with contextlib.suppress(Exception):
                await pubsub.unsubscribe(CHANGED_CHANNEL)
                await pubsub.aclose()

    async def active_ids(self) -> list[int]:
        async with self.infra.sm() as session:
            return [int(x) for x in (await session.execute(select(ChildBot.bot_id).where(ChildBot.status == "active"))).scalars()]

    async def close(self) -> None:
        self._loaded.clear()
        if self._own_session is not None:
            await self._own_session.close()
