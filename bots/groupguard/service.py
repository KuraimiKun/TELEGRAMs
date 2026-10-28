"""Group Guard storage: group configs (cached), warnings, notes and filters."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any
from weakref import WeakKeyDictionary, WeakValueDictionary

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.models import GuardApproval, GuardChat, GuardItem, GuardMember, GuardWarn
from core.db.base import affected, upsert, utcnow

CACHE_TTL = 30.0
_MEMBER_TX: ContextVar[tuple | None] = ContextVar("gg_member_transaction", default=None)
_SQLITE_LOCKS: WeakKeyDictionary = WeakKeyDictionary()
_MEMBER_CAPACITY: WeakKeyDictionary = WeakKeyDictionary()


class ConfigConflict(RuntimeError):
    pass



class LimitReached(Exception):
    pass


class GuardService:
    def __init__(self, sm: async_sessionmaker[AsyncSession], bot_id: int) -> None:
        self.sm = sm
        self.bot_id = bot_id
        self._configs: dict[int, tuple[float, ChatConfig]] = {}
        self._filters: dict[int, tuple[float, list[GuardItem]]] = {}

    async def approval(self, chat_id: int, user_id: int) -> GuardApproval | None:
        async with self.sm() as session:
            return await session.get(GuardApproval, (self.bot_id, chat_id, user_id))

    async def approve(self, chat_id: int, user_id: int, reason: str | None, by_id: int | None) -> None:
        async with self.member_session(chat_id, user_id) as (session, _member):
            await session.execute(upsert(session, GuardApproval).values(bot_id=self.bot_id, chat_id=chat_id,
                user_id=user_id, reason=reason, by_id=by_id, created_at=utcnow()).on_conflict_do_update(
                    index_elements=["bot_id", "chat_id", "user_id"],
                    set_=dict(reason=reason, by_id=by_id, created_at=utcnow())))

    async def unapprove(self, chat_id: int, user_id: int | None) -> int:
        where = [GuardApproval.bot_id == self.bot_id, GuardApproval.chat_id == chat_id]
        if user_id is not None:
            where.append(GuardApproval.user_id == user_id)
        async with self.sm() as session:
            result = await session.execute(delete(GuardApproval).where(*where))
            await session.commit()
            return affected(result)

    async def approvals(self, chat_id: int, page: int = 1) -> list[GuardApproval]:
        async with self.sm() as session:
            return list((await session.execute(select(GuardApproval).where(GuardApproval.bot_id == self.bot_id,
                GuardApproval.chat_id == chat_id).order_by(GuardApproval.user_id).offset((page - 1) * 1000)
                .limit(1001))).scalars())

    # ------------------------------------------------------------------ chats & config
    async def ensure_chat(self, chat_id: int, title: str | None = None, lang: str | None = None) -> None:
        """Create the group's row on first sight (with ``lang``); later calls only refresh title/active."""
        changes: dict[str, Any] = {"active": True}
        if title:
            changes["title"] = title
        async with self.sm() as s:
            await s.execute(
                upsert(s, GuardChat)
                .values(bot_id=self.bot_id, chat_id=chat_id, title=title, active=True,
                        config=ChatConfig(lang=lang).model_dump())
                .on_conflict_do_update(index_elements=[GuardChat.bot_id, GuardChat.chat_id], set_=changes)
            )
            await s.commit()

    async def config(self, chat_id: int, *, fresh: bool = False) -> ChatConfig:
        # SQL revision/data is authoritative across replicas; process TTL is never authorization.
        async with self.sm() as session:
            row = await session.get(GuardChat, (self.bot_id, chat_id))
            payload, revision = (dict(row.config or {}), row.revision) if row is not None else ({}, 0)
        cfg = ChatConfig.from_storage(payload)
        cfg._revision = revision
        cfg._base = cfg.model_dump()
        return cfg

    async def save_config(self, chat_id: int, cfg: ChatConfig) -> ChatConfig:
        # A previously loaded/model-copied config retains its base; save only changed fields.
        changes = {k: v for k, v in cfg.model_dump().items() if k not in cfg._base or cfg._base[k] != v}
        return await self.update_config(chat_id, **changes)

    async def update_config(self, chat_id: int, **changes: Any) -> ChatConfig:
        await self.ensure_chat(chat_id)
        requested_changes = changes
        for _ in range(16):
            changes = dict(requested_changes)
            async with self.sm() as session:
                row = await session.get(GuardChat, (self.bot_id, chat_id))
                assert row is not None
                revision = row.revision
                base = ChatConfig.normalized_storage(row.config or {})
                if any(key in changes and changes[key] != base.get(key) for key in ("night", "night_start", "night_end", "tz_offset")):
                    changes["night_policy_version"] = base.get("night_policy_version", 0) + 1
                if "blocklist" in changes and "blocklist_entries" not in changes:
                    # Existing callers replace legacy text phrases only; keep new typed kinds.
                    from bots.groupguard.blocklist_types import Entry
                    changes = {**changes, "blocklist_entries": [
                        entry for entry in base.get("blocklist_entries", []) if entry["kind"] != "text"
                    ] + [Entry(key=text, pattern=text, legacy=True).model_dump() for text in changes["blocklist"]]}
                if "blocklist_warn" in changes and "blocklist_mode" not in changes:
                    changes = {**changes, "blocklist_mode": "warn" if changes["blocklist_warn"] else "nothing",
                               "blocklist_duration_seconds": None}
                payload = {**base, **changes}
                cfg = ChatConfig.model_validate(payload)
                result = await session.execute(update(GuardChat).where(
                    GuardChat.bot_id == self.bot_id, GuardChat.chat_id == chat_id,
                    GuardChat.revision == revision).values(config=cfg.model_dump(), revision=revision + 1,
                                                           night=cfg.night, updated_at=utcnow()))
                if affected(result) == 1:
                    if "warn_time_seconds" in changes and cfg.warn_time_seconds is None:
                        # Off cancels pending age expiry without resurrecting already-expired history.
                        await session.execute(update(GuardWarn).where(GuardWarn.bot_id == self.bot_id,
                            GuardWarn.chat_id == chat_id, GuardWarn.expires_at > utcnow()).values(expires_at=None))
                    await session.commit()
                    cfg._revision = revision + 1
                    cfg._base = cfg.model_dump()
                    return cfg
                await session.rollback()
            await asyncio.sleep(0)
        raise ConfigConflict("configuration_revision_conflict")

    @asynccontextmanager
    async def member_session(self, chat_id: int, user_id: int) -> AsyncIterator[tuple[AsyncSession, GuardMember]]:
        scope = (self.bot_id, chat_id, user_id)
        active = _MEMBER_TX.get()
        if active is not None and active[0] == scope:
            yield active[1], active[2]
            return
        engine = self.sm.kw["bind"]
        capacity = _MEMBER_CAPACITY.get(engine)
        if capacity is None:
            pool_size = engine.pool.size() if hasattr(engine.pool, "size") else 2
            overflow = max(getattr(engine.pool, "_max_overflow", 0), 0)
            capacity = asyncio.Semaphore(max(1, min(4, (pool_size + overflow) // 2)))
            _MEMBER_CAPACITY[engine] = capacity
        # Nested owned-state restoration can lock a member while the same task
        # holds the group transaction. Count only the outer task toward engine
        # capacity; reacquiring a one-slot semaphore would deadlock that task.
        capacity_acquired = active is None or active[1].bind is not engine
        if capacity_acquired:
            await capacity.acquire()
        lock = None
        if engine.dialect.name == "sqlite":
            locks = _SQLITE_LOCKS.setdefault(engine, WeakValueDictionary())
            lock = locks.get(scope)
            if lock is None:
                lock = asyncio.Lock()
                locks[scope] = lock
        lock_acquired = False
        try:
            if lock is not None:
                await lock.acquire()
                lock_acquired = True
            async with self.sm() as session:
                await session.execute(upsert(session, GuardMember).values(
                    bot_id=self.bot_id, chat_id=chat_id, user_id=user_id, last_seen=utcnow()).on_conflict_do_nothing())
                member = (await session.execute(select(GuardMember).where(
                    GuardMember.bot_id == self.bot_id, GuardMember.chat_id == chat_id,
                    GuardMember.user_id == user_id).with_for_update())).scalar_one()
                token = _MEMBER_TX.set((scope, session, member))
                try:
                    yield session, member
                    await session.commit()
                except BaseException:
                    await session.rollback()
                    raise
                finally:
                    _MEMBER_TX.reset(token)
        finally:
            if lock_acquired and lock is not None:
                lock.release()
            if capacity_acquired:
                capacity.release()

    async def set_active(self, chat_id: int, active: bool, title: str | None = None) -> None:
        await self.ensure_chat(chat_id, title)
        if not active:
            async with self.sm() as s:
                await s.execute(
                    update(GuardChat)
                    .where(GuardChat.bot_id == self.bot_id, GuardChat.chat_id == chat_id)
                    .values(active=False)
                )
                await s.commit()

    async def title(self, chat_id: int) -> str | None:
        async with self.sm() as s:
            row = await s.get(GuardChat, (self.bot_id, chat_id))
            return row.title if row else None

    async def night_chats(self) -> list[tuple[int, ChatConfig]]:
        async with self.sm() as s:
            stmt = select(GuardChat).where(
                GuardChat.bot_id == self.bot_id, GuardChat.night.is_(True), GuardChat.active.is_(True)
            )
            return [(row.chat_id, ChatConfig.from_storage(row.config or {})) for row in (await s.execute(stmt)).scalars()]

    # ------------------------------------------------------------------ warnings
    async def add_warn(self, chat_id: int, user_id: int, reason: str | None, by_id: int | None) -> int:
        async with self.member_session(chat_id, user_id) as (session, _member):
            session.add(GuardWarn(bot_id=self.bot_id, chat_id=chat_id, user_id=user_id, reason=reason, by_id=by_id))
            await session.flush()
            return int((await session.execute(select(func.count()).select_from(GuardWarn).where(
                *self._warns(chat_id, user_id), self._live_warns()))).scalar_one())

    def _warns(self, chat_id: int, user_id: int):
        return (GuardWarn.bot_id == self.bot_id, GuardWarn.chat_id == chat_id, GuardWarn.user_id == user_id)

    def _live_warns(self):
        return or_(GuardWarn.expires_at.is_(None), GuardWarn.expires_at > utcnow())

    async def count_warns(self, chat_id: int, user_id: int) -> int:
        async with self.sm() as session:
            return int((await session.execute(select(func.count()).select_from(GuardWarn).where(
                *self._warns(chat_id, user_id), self._live_warns()))).scalar_one())

    async def list_warns(self, chat_id: int, user_id: int) -> list[GuardWarn]:
        async with self.sm() as session:
            return list((await session.execute(select(GuardWarn).where(
                *self._warns(chat_id, user_id), self._live_warns()).order_by(GuardWarn.id))).scalars())

    async def remove_warning(self, chat_id: int, user_id: int, warning_id: int) -> bool:
        async with self.member_session(chat_id, user_id) as (session, _member):
            result = await session.execute(delete(GuardWarn).where(*self._warns(chat_id, user_id), GuardWarn.id == warning_id))
            return affected(result) == 1

    async def remove_last_warn(self, chat_id: int, user_id: int) -> bool:
        async with self.member_session(chat_id, user_id) as (session, _member):
            last = (await session.execute(select(GuardWarn.id).where(*self._warns(chat_id, user_id),
                self._live_warns()).order_by(GuardWarn.id.desc()).limit(1))).scalar_one_or_none()
            if last is None:
                return False
            return await self.remove_warning(chat_id, user_id, int(last))

    async def reset_warns(self, chat_id: int, user_id: int) -> int:
        async with self.member_session(chat_id, user_id) as (session, _member):
            result = await session.execute(delete(GuardWarn).where(*self._warns(chat_id, user_id)))
            return affected(result)

    # ------------------------------------------------------------------ notes & filters
    async def save_item(
        self, chat_id: int, kind: str, key: str, *, text: str | None, media_kind: str | None, file_id: str | None,
        limit: int, content_format: str = "html", options: dict | None = None,
    ) -> None:
        await self.save_items(chat_id, kind, [key], text=text, media_kind=media_kind, file_id=file_id,
            limit=limit, content_format=content_format, options=options)

    async def save_items(self, chat_id: int, kind: str, keys: list[str], *, text: str | None,
                         media_kind: str | None, file_id: str | None, limit: int,
                         content_format: str = "html", options: dict | None = None) -> list[GuardItem]:
        normalized = list(dict.fromkeys(key.lower() for key in keys))
        if not normalized or any(not key or len(key) > 64 for key in normalized):
            raise ValueError("item_key_invalid")
        async with self.member_session(chat_id, 0) as (session, _member):
            current = set((await session.execute(select(GuardItem.key).where(GuardItem.bot_id == self.bot_id,
                GuardItem.chat_id == chat_id, GuardItem.kind == kind))).scalars())
            count = int((await session.execute(select(func.count()).select_from(GuardItem).where(
                GuardItem.bot_id == self.bot_id, GuardItem.chat_id == chat_id))).scalar_one())
            if count + len(set(normalized) - current) > limit:
                raise LimitReached
            values = dict(text=text, media_kind=media_kind, file_id=file_id, format=content_format, options=options or {})
            for key in normalized:
                await session.execute(upsert(session, GuardItem).values(bot_id=self.bot_id, chat_id=chat_id,
                    kind=kind, key=key, **values).on_conflict_do_update(index_elements=["bot_id", "chat_id", "kind", "key"], set_=values))
            return list((await session.execute(select(GuardItem).where(GuardItem.bot_id == self.bot_id,
                GuardItem.chat_id == chat_id, GuardItem.kind == kind, GuardItem.key.in_(normalized)))).scalars())

    async def get_item(self, chat_id: int, kind: str, key: str) -> GuardItem | None:
        async with self.sm() as s:
            stmt = select(GuardItem).where(
                GuardItem.bot_id == self.bot_id, GuardItem.chat_id == chat_id, GuardItem.kind == kind,
                GuardItem.key == key.lower(),
            )
            return (await s.execute(stmt)).scalar_one_or_none()

    async def delete_item(self, chat_id: int, kind: str, key: str) -> bool:
        from bots.groupguard.models import GuardJob, GuardRepeat
        async with self.member_session(chat_id, 0) as (s, _member):
            ids = list((await s.execute(select(GuardItem.id).where(GuardItem.bot_id == self.bot_id,
                GuardItem.chat_id == chat_id, GuardItem.kind == kind, GuardItem.key == key.lower()))).scalars())
            generations = list((await s.execute(select(GuardRepeat.generation).where(GuardRepeat.bot_id == self.bot_id,
                GuardRepeat.chat_id == chat_id, GuardRepeat.item_id.in_(ids)))).scalars())
            await s.execute(update(GuardJob).where(GuardJob.bot_id == self.bot_id, GuardJob.kind == "repeat_note",
                GuardJob.generation.in_(generations), GuardJob.dispatched.is_(False)).values(status="cancelled"))
            await s.execute(delete(GuardRepeat).where(GuardRepeat.bot_id == self.bot_id,
                GuardRepeat.chat_id == chat_id, GuardRepeat.item_id.in_(ids)))
            res = await s.execute(
                delete(GuardItem).where(
                    GuardItem.bot_id == self.bot_id, GuardItem.chat_id == chat_id, GuardItem.kind == kind,
                    GuardItem.key == key.lower(),
                )
            )
        self._filters.pop(chat_id, None)
        return affected(res) > 0

    async def list_items(self, chat_id: int, kind: str) -> list[GuardItem]:
        async with self.sm() as s:
            stmt = (
                select(GuardItem)
                .where(GuardItem.bot_id == self.bot_id, GuardItem.chat_id == chat_id, GuardItem.kind == kind)
                .order_by(GuardItem.key)
            )
            return list((await s.execute(stmt)).scalars())

    async def filters(self, chat_id: int) -> list[GuardItem]:
        return await self.list_items(chat_id, "filter")

    # ------------------------------------------------------------------ stats
    async def totals(self) -> dict[str, int]:
        async with self.sm() as s:

            async def count(model, *cond) -> int:
                stmt = select(func.count()).select_from(model).where(model.bot_id == self.bot_id, *cond)
                return int((await s.execute(stmt)).scalar_one())

            return {
                "groups": await count(GuardChat, GuardChat.active.is_(True)),
                "warns": await count(GuardWarn),
                "items": await count(GuardItem),
            }
