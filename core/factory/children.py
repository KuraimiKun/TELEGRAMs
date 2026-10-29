"""Lifecycle of user-created bots: create, pause, resume, rotate token, delete, revoke."""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator
from dataclasses import dataclass

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramAPIError, TelegramUnauthorizedError
from aiogram.types import User
from redis.asyncio import Redis
from sqlalchemy import ColumnElement, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.config import TOKEN_RE, PlatformConfig
from core.db.base import upsert, utcnow
from core.db.models import Bot as BotRecord
from core.db.models import BotUser, ChildBot
from core.factory import webhooks
from core.factory.crypto import decrypt_token, encrypt_token
from core.log import get_logger
from core.redis import PLATFORM

log = get_logger(__name__)

CHANGED_CHANNEL = PLATFORM("factory", "changed")


class ChildError(Exception):
    """Expected failure with a stable ``code`` the factory bot translates (``factory-err-<code>``)."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(slots=True)
class ChildSummary:
    bot: ChildBot
    users: int


class ChildService:
    def __init__(
        self,
        sm: async_sessionmaker[AsyncSession],
        redis: Redis,
        platform: PlatformConfig,
        *,
        factory_bot_id: int,
        templates: set[str],
        session: BaseSession | None = None,
    ) -> None:
        self.sm = sm
        self.redis = redis
        self.platform = platform
        self.factory_bot_id = factory_bot_id
        self.templates = templates
        self.session = session

    # ------------------------------------------------------------------ helpers
    @contextlib.asynccontextmanager
    async def _bot(self, token: str) -> AsyncIterator[Bot]:
        own = self.session is None
        bot = Bot(token=token, session=self.session or AiohttpSession())
        try:
            yield bot
        finally:
            if own:
                await bot.session.close()

    async def _identify(self, token: str) -> User:
        token = token.strip()
        if not TOKEN_RE.fullmatch(token):
            raise ChildError("token_format")
        try:
            async with self._bot(token) as bot:
                me = await bot.get_me()
        except TelegramUnauthorizedError as e:
            raise ChildError("token_invalid") from e
        except TelegramAPIError as e:
            log.warning("factory_get_me_failed", error=str(e))
            raise ChildError("telegram") from e
        if not me.is_bot:
            raise ChildError("token_invalid")
        return me

    async def notify_changed(self, bot_id: int) -> None:
        """Tell every gateway / scheduler to drop the cached runtime of this bot."""
        with contextlib.suppress(Exception):
            await self.redis.publish(CHANGED_CHANNEL, str(bot_id))

    # ------------------------------------------------------------------ queries
    async def get(self, bot_id: int) -> ChildBot | None:
        async with self.sm() as session:
            return await session.get(ChildBot, bot_id)

    async def get_owned(self, owner_id: int, bot_id: int) -> ChildBot | None:
        child = await self.get(bot_id)
        return child if child is not None and child.owner_id == owner_id else None

    async def count_for_owner(self, owner_id: int) -> int:
        async with self.sm() as session:
            stmt = select(func.count()).select_from(ChildBot).where(
                ChildBot.owner_id == owner_id, ChildBot.status != "revoked"
            )
            return int((await session.execute(stmt)).scalar_one())

    async def list_for_owner(self, owner_id: int, *, offset: int = 0, limit: int = 8) -> list[ChildBot]:
        async with self.sm() as session:
            stmt = (
                select(ChildBot)
                .where(ChildBot.owner_id == owner_id, ChildBot.status != "revoked")
                .order_by(ChildBot.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            return list((await session.execute(stmt)).scalars())

    async def member_count(self, bot_id: int) -> int:
        async with self.sm() as session:
            stmt = select(func.count()).select_from(BotUser).where(BotUser.bot_id == bot_id)
            return int((await session.execute(stmt)).scalar_one())

    async def gallery(self, *, offset: int = 0, limit: int = 10) -> list[ChildSummary]:
        """Public bots, most used first: the factory's showcase."""
        async with self.sm() as session:
            users = func.count(BotUser.user_id).label("users")
            stmt = (
                select(ChildBot, users)
                .outerjoin(BotUser, BotUser.bot_id == ChildBot.bot_id)
                .where(ChildBot.public.is_(True), ChildBot.status == "active")
                .group_by(ChildBot.bot_id)
                .order_by(users.desc(), ChildBot.created_at)
                .offset(offset)
                .limit(limit)
            )
            return [ChildSummary(bot=row[0], users=int(row[1])) for row in (await session.execute(stmt)).all()]

    async def totals(self) -> dict[str, int]:
        async with self.sm() as session:
            stmt = select(ChildBot.template, ChildBot.status, func.count()).group_by(ChildBot.template, ChildBot.status)
            out: dict[str, int] = {}
            for template, status, n in (await session.execute(stmt)).all():
                out[f"{template}:{status}"] = int(n)
            return out

    async def search(self, query: str, limit: int = 10) -> list[ChildBot]:
        q = query.strip().lstrip("@")
        async with self.sm() as session:
            cond: list[ColumnElement[bool]] = [ChildBot.username.ilike(q.replace("%", r"\%").replace("_", r"\_") + "%", escape="\\")]
            if q.isdigit():
                cond += [ChildBot.bot_id == int(q), ChildBot.owner_id == int(q)]
            stmt = select(ChildBot).where(or_(*cond)).order_by(ChildBot.created_at.desc()).limit(limit)
            return list((await session.execute(stmt)).scalars())

    async def active_ids(self) -> list[int]:
        async with self.sm() as session:
            stmt = select(ChildBot.bot_id).where(ChildBot.status == "active")
            return [int(x) for x in (await session.execute(stmt)).scalars()]

    # ------------------------------------------------------------------ lifecycle
    async def _check_hosting(self, bot: Bot, bot_id: int, template: str, migrate_existing: bool) -> None:
        if template != "channelmanager" or migrate_existing:
            return
        info = await bot.get_webhook_info()
        expected = (self.platform.webhook_base_url or "").rstrip("/") + webhooks.child_webhook_path(bot_id)
        if info.url and (not self.platform.webhook_base_url or info.url != expected):
            raise ChildError("migration_required")

    async def create(self, owner_id: int, token: str, template: str, *, limit: int, migrate_existing: bool = False) -> ChildBot:
        if template not in self.templates:
            raise ChildError("template")
        me = await self._identify(token)

        async with self.sm() as session:
            record = await session.get(BotRecord, me.id)
            existing = await session.get(ChildBot, me.id)
            if record is not None and existing is None:
                raise ChildError("platform_bot")  # one of the platform's own bots
            if existing is not None and existing.status == "revoked":
                raise ChildError("revoked")  # blocked by platform moderation
            if existing is not None and existing.owner_id != owner_id:
                raise ChildError("taken")
        if existing is None and await self.count_for_owner(owner_id) >= limit:
            raise ChildError("limit")

        if template == "channelmanager" and not migrate_existing:
            async with self._bot(token) as bot:
                await self._check_hosting(bot, me.id, template, migrate_existing)

        token_enc = encrypt_token(self.platform, token.strip())
        title = (me.full_name or me.username or str(me.id))[:128]
        async with self.sm() as session:
            await session.execute(
                upsert(session, BotRecord)
                .values(id=me.id, slug=f"c{me.id}", title=title, username=me.username, active=True)
                .on_conflict_do_update(
                    index_elements=[BotRecord.id], set_={"title": title, "username": me.username, "active": True}
                )
            )
            values = {
                "owner_id": owner_id,
                "factory_bot_id": self.factory_bot_id,
                "template": template,
                "token_enc": token_enc,
                "username": me.username or "",
                "title": title,
                "status": "active",
                "last_error": None,
            }
            await session.execute(
                upsert(session, ChildBot)
                .values(bot_id=me.id, **values)
                .on_conflict_do_update(index_elements=[ChildBot.bot_id], set_={**values, "updated_at": utcnow()})
            )
            await session.commit()

        async with self._bot(token) as bot:
            try:
                await webhooks.attach(bot, me.id, self.platform)
            except TelegramAPIError as e:
                await self._set(me.id, status="error", last_error=str(e)[:500])
                raise ChildError("webhook") from e
        await self.notify_changed(me.id)
        child = await self.get(me.id)
        assert child is not None
        log.info("factory_bot_created", bot_id=me.id, owner=owner_id, template=template)
        return child

    async def _set(self, bot_id: int, **values: object) -> None:
        async with self.sm() as session:
            await session.execute(update(ChildBot).where(ChildBot.bot_id == bot_id).values(**values, updated_at=utcnow()))
            await session.commit()

    async def _token(self, child: ChildBot) -> str | None:
        token = decrypt_token(self.platform, child.token_enc, expected_bot_id=child.bot_id)
        if token is None and child.token_enc:
            await self._set(child.bot_id, last_error="token_identity_or_decryption_unavailable")
        return token

    async def pause(self, child: ChildBot) -> None:
        token = await self._token(child)
        # Fence cached dispatchers/queued work first; already-dispatched RPCs remain explicit uncertainty.
        await self._set(child.bot_id, status="paused")
        cleanup_error = None
        if child.template == "channelmanager":
            from bots.channelmanager.senders import stop_owned
            cleanup_error = await stop_owned(self.sm, child.bot_id, "pause")
        if token and child.template == "groupguard":
            from core.sdk.context import ChildInfo
            from core.sdk.registry import BotIdentityMismatch, SharedInfra, factory_templates, init_context
            module = factory_templates()[child.template]
            async with self._bot(token) as scoped_bot:
                try:
                    infra = SharedInfra(engine=self.sm.kw["bind"], sm=self.sm, redis=self.redis,
                                        cache_redis=self.redis, session=scoped_bot.session)
                    env = module.env_model.model_validate({"token": token, "admin_ids": [child.owner_id]})
                    ctx = await init_context(module, self.platform, infra, env, child=ChildInfo(
                        owner_id=child.owner_id, template=child.template, factory_username="", branding=child.branding),
                        session=scoped_bot.session)
                    ctx.extras["owned_maintenance"] = True
                    cleanup_error = await module.on_child_stopping(ctx, "pause")
                except TelegramAPIError:
                    cleanup_error = "owned_cleanup_api_unavailable"
                except BotIdentityMismatch:
                    cleanup_error = "owned_cleanup_identity_unavailable"
        if cleanup_error:
            await self._set(child.bot_id, last_error=cleanup_error[:500])
        if token:
            with contextlib.suppress(TelegramAPIError):
                async with self._bot(token) as bot:
                    await webhooks.detach(bot)
        await self._set(child.bot_id, status="paused")
        await self.notify_changed(child.bot_id)

    async def resume(self, child: ChildBot, *, migrate_existing: bool = False) -> None:
        token = await self._token(child)
        if not token:
            raise ChildError("token_invalid")
        try:
            async with self._bot(token) as bot:
                await self._check_hosting(bot, child.bot_id, child.template, migrate_existing)
                await webhooks.attach(bot, child.bot_id, self.platform)
        except TelegramUnauthorizedError as e:
            await self._set(child.bot_id, status="error", last_error="token revoked in @BotFather")
            raise ChildError("token_invalid") from e
        except TelegramAPIError as e:
            raise ChildError("webhook") from e
        await self._set(child.bot_id, status="active", last_error=None)
        await self.notify_changed(child.bot_id)

    async def rotate_token(self, child: ChildBot, token: str) -> None:
        me = await self._identify(token)
        if me.id != child.bot_id:
            raise ChildError("token_other_bot")
        await self._set(child.bot_id, token_enc=encrypt_token(self.platform, token.strip()))
        refreshed = await self.get(child.bot_id)
        assert refreshed is not None
        await self.resume(refreshed)

    async def set_flags(self, child: ChildBot, **flags: object) -> None:
        allowed = {"branding", "public", "description"}
        await self._set(child.bot_id, **{k: v for k, v in flags.items() if k in allowed})
        await self.notify_changed(child.bot_id)

    async def mark_error(self, bot_id: int, error: str) -> None:
        await self._set(bot_id, status="error", last_error=error[:500])

    async def delete(self, child: ChildBot) -> None:
        """Remove the bot and all its data (members, settings, template tables cascade from ``bots``)."""
        await self.pause(child)
        async with self.sm() as session:
            await session.execute(delete(ChildBot).where(ChildBot.bot_id == child.bot_id))
            await session.execute(delete(BotRecord).where(BotRecord.id == child.bot_id))
            await session.commit()
        await self.notify_changed(child.bot_id)
        log.info("factory_bot_deleted", bot_id=child.bot_id, owner=child.owner_id)

    async def revoke(self, child: ChildBot, reason: str) -> None:
        """Platform moderation: stop the bot and forget its token, keep the record for audit."""
        await self.pause(child)
        await self._set(child.bot_id, status="revoked", token_enc="", last_error=reason[:500], public=False)
        await self.notify_changed(child.bot_id)
        log.warning("factory_bot_revoked", bot_id=child.bot_id, owner=child.owner_id, reason=reason)
