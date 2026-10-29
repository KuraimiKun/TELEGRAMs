"""Persisted, resumable, cancellable broadcasts.

Admins create a ``broadcasts`` row (status ``pending``); the scheduler process runs it (``BroadcastRunner``)
in user-id order, saving a cursor after every batch. A restart resumes from the cursor, never re-sending.
Only one runner per bot works at a time (owner-token lock with lease renewal).
"""

from __future__ import annotations

import asyncio
import contextlib
import secrets
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from redis.asyncio import Redis
from sqlalchemy import ColumnElement, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.db.base import affected, utcnow
from core.db.models import BotUser, Broadcast
from core.log import get_logger
from core.observability import BROADCAST_MESSAGES
from core.redis import KeySpace

log = get_logger(__name__)

BATCH = 200
CHECKPOINT = 50  # persist progress / notice cancellation every N recipients
RATE_PER_SEC = 25  # Telegram's global limit is ~30 msg/s per bot
LOCK_LEASE = 60
GONE_ERRORS = ("chat not found", "user is deactivated", "bot was blocked", "peer_id_invalid")
_RELEASE = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"
_EXTEND = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('expire', KEYS[1], ARGV[2]) else return 0 end"


@dataclass(slots=True)
class Target:
    """Audience spec encoded as a short string: all | free | vip | active7 | lang:<code>."""

    raw: str

    def conditions(self) -> list[ColumnElement[bool]]:
        now = utcnow()
        conds: list[ColumnElement[bool]] = [BotUser.is_banned.is_(False), BotUser.blocked_bot.is_(False)]
        if self.raw == "free":
            conds.append((BotUser.vip_until.is_(None)) | (BotUser.vip_until <= now))
        elif self.raw == "vip":
            conds.append(BotUser.vip_until > now)
        elif self.raw == "active7":
            conds.append(BotUser.last_seen >= now - timedelta(days=7))
        elif self.raw.startswith("lang:"):
            conds.append(BotUser.lang == self.raw.split(":", 1)[1])
        return conds


class BroadcastService:
    def __init__(
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
        bot_id: int,
        redis: Redis,
        keys: KeySpace,
        metric: str | None = None,
    ) -> None:
        self.sm = sessionmaker
        self.bot_id = bot_id
        self.metric = metric or keys.slug
        self.redis = redis
        self.keys = keys
        # Optional module-specific shared sender budget. Other bots keep existing behavior.
        self.before_send: Callable[[int], Awaitable[None]] | None = None

    async def count_audience(self, target: str) -> int:
        async with self.sm() as session:
            stmt = select(func.count()).select_from(BotUser).where(
                BotUser.bot_id == self.bot_id, *Target(target).conditions()
            )
            return int((await session.execute(stmt)).scalar_one() or 0)

    async def create(self, admin_id: int, target: str, from_chat_id: int, message_id: int) -> Broadcast:
        total = await self.count_audience(target)
        async with self.sm() as session:
            b = Broadcast(
                bot_id=self.bot_id,
                created_by=admin_id,
                status="pending",
                target=target,
                from_chat_id=from_chat_id,
                message_id=message_id,
                total=total,
                created_at=utcnow(),
            )
            session.add(b)
            await session.commit()
            return b

    async def get(self, broadcast_id: int) -> Broadcast | None:
        async with self.sm() as session:
            b = await session.get(Broadcast, broadcast_id)
            return b if b and b.bot_id == self.bot_id else None

    async def active(self) -> Broadcast | None:
        async with self.sm() as session:
            stmt = (
                select(Broadcast)
                .where(Broadcast.bot_id == self.bot_id, Broadcast.status.in_(("pending", "running")))
                .order_by(Broadcast.id)
                .limit(1)
            )
            return (await session.execute(stmt)).scalar_one_or_none()

    async def recent(self, limit: int = 5) -> list[Broadcast]:
        async with self.sm() as session:
            stmt = select(Broadcast).where(Broadcast.bot_id == self.bot_id).order_by(Broadcast.id.desc()).limit(limit)
            return list((await session.execute(stmt)).scalars().all())

    async def cancel(self, broadcast_id: int) -> bool:
        async with self.sm() as session:
            res = await session.execute(
                update(Broadcast)
                .where(
                    Broadcast.id == broadcast_id,
                    Broadcast.bot_id == self.bot_id,
                    Broadcast.status.in_(("pending", "running")),
                )
                .values(status="cancelled", finished_at=utcnow())
            )
            await session.commit()
            return bool(affected(res))

    async def _next_batch(self, b: Broadcast) -> list[int]:
        async with self.sm() as session:
            stmt = (
                select(BotUser.user_id)
                .where(BotUser.bot_id == self.bot_id, BotUser.user_id > b.cursor, *Target(b.target).conditions())
                .order_by(BotUser.user_id)
                .limit(BATCH)
            )
            return list((await session.execute(stmt)).scalars().all())

    async def _save(self, b: Broadcast, **values: object) -> str:
        """Persist progress; returns the current status (so an admin cancel is noticed)."""
        async with self.sm() as session:
            await session.execute(update(Broadcast).where(Broadcast.id == b.id).values(**values))
            await session.commit()
            status = (await session.execute(select(Broadcast.status).where(Broadcast.id == b.id))).scalar_one()
        return status

    async def _mark_gone(self, user_ids: list[int]) -> None:
        if not user_ids:
            return
        async with self.sm() as session:
            await session.execute(
                update(BotUser)
                .where(BotUser.bot_id == self.bot_id, BotUser.user_id.in_(user_ids))
                .values(blocked_bot=True)
            )
            await session.commit()

    async def _checkpoint(self, b: Broadcast, gone: list[int]) -> str:
        """Persist progress (cursor + counters) and return the current status, so a cancel is noticed fast."""
        await self._mark_gone(gone)
        return await self._save(b, sent=b.sent, blocked=b.blocked, failed=b.failed, cursor=b.cursor)

    async def _send(self, bot: Bot, b: Broadcast, uid: int) -> str:
        for _ in range(3):
            try:
                if self.before_send is not None:
                    await self.before_send(uid)
                await bot.copy_message(chat_id=uid, from_chat_id=b.from_chat_id, message_id=b.message_id)
                return "sent"
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after + 1)
            except TelegramForbiddenError:
                return "blocked"
            except TelegramBadRequest as e:
                if any(s in str(e).lower() for s in GONE_ERRORS):
                    return "blocked"
                log.info("broadcast_send_failed", user_id=uid, error=str(e))
                return "failed"
            except Exception as e:
                log.warning("broadcast_send_error", user_id=uid, error=str(e))
                return "failed"
        return "failed"

    async def run(self, bot: Bot, b: Broadcast, stop: asyncio.Event) -> Broadcast:
        """Process ``b`` from its cursor until done, cancelled or ``stop`` (resumable)."""
        if b.status not in ("pending", "running"):
            return b
        if b.status == "pending":
            await self._save(b, status="running", started_at=utcnow())
            b.status = "running"
        while not stop.is_set():
            batch = await self._next_batch(b)
            if not batch:
                await self._save(b, status="done", finished_at=utcnow())
                b.status = "done"
                break
            gone: list[int] = []
            for uid in batch:
                if stop.is_set():
                    break
                outcome = await self._send(bot, b, uid)
                BROADCAST_MESSAGES.labels(self.metric, outcome).inc()
                if outcome == "sent":
                    b.sent += 1
                elif outcome == "blocked":
                    b.blocked += 1
                    gone.append(uid)
                else:
                    b.failed += 1
                b.cursor = uid
                await asyncio.sleep(1 / RATE_PER_SEC)
                if (b.sent + b.blocked + b.failed) % CHECKPOINT == 0:
                    if await self._checkpoint(b, gone) == "cancelled":
                        b.status = "cancelled"
                        return b
                    gone = []
            if await self._checkpoint(b, gone) == "cancelled":
                b.status = "cancelled"
                break
        return b


class BroadcastRunner:
    """Runs pending broadcasts of one bot; one runner per bot across all scheduler replicas."""

    def __init__(self, service: BroadcastService, bot: Bot, poll: float = 5.0) -> None:
        self.service = service
        self.bot = bot
        self.poll = poll

    async def run(self, stop: asyncio.Event, on_finished=None, *, until_idle: bool = False) -> None:
        """Run broadcasts as they appear. With ``until_idle`` return once nothing is pending (user-created
        bots get a runner only while they have work, instead of one idle loop per bot)."""
        lock_key = self.service.keys("broadcast", "runner")
        while not stop.is_set():
            b = await self.service.active()
            if b is None:
                if until_idle:
                    return
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(stop.wait(), timeout=self.poll)
                continue
            token = secrets.token_hex(8)
            if not await self.service.redis.set(lock_key, token, nx=True, ex=LOCK_LEASE):
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(stop.wait(), timeout=self.poll)
                continue
            renew = asyncio.create_task(self._renew(lock_key, token))
            try:
                log.info("broadcast_started", broadcast_id=b.id, target=b.target, total=b.total, cursor=b.cursor)
                b = await self.service.run(self.bot, b, stop)
                log.info("broadcast_stopped", broadcast_id=b.id, status=b.status, sent=b.sent)
                if b.status in ("done", "cancelled") and on_finished:
                    with contextlib.suppress(Exception):
                        await on_finished(b)
            except Exception as e:
                log.exception("broadcast_failed", broadcast_id=b.id, error=str(e))
                await self.service._save(b, status="failed", error=str(e)[:500], finished_at=utcnow())
            finally:
                renew.cancel()
                with contextlib.suppress(Exception):
                    await self.service.redis.eval(_RELEASE, 1, lock_key, token)

    async def _renew(self, key: str, token: str) -> None:
        while True:
            await asyncio.sleep(LOCK_LEASE / 3)
            await self.service.redis.eval(_EXTEND, 1, key, token, LOCK_LEASE)
