"""Channel connection, snapshots and events; domain mutations and notices share a transaction."""

from __future__ import annotations

import uuid

from aiogram.enums import ChatType
from aiogram.types import ChatMemberUpdated
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bots.channelmanager import outbox
from bots.channelmanager.models import (
    AutoAction,
    AutoSource,
    Channel,
    ChannelRole,
    Entitlement,
    Event,
    Inbox,
    JoinRequest,
    MemberAction,
    Operation,
)
from bots.channelmanager.permissions import AccessDenied, operator_rights, rights_of
from core.db.base import upsert, utcnow
from core.db.models import Bot, BotUser
from core.sdk.context import BotContext
from core.ui.text import esc


class ChannelService:
    def __init__(self, ctx: BotContext) -> None:
        self.ctx = ctx

    async def get(self, channel_id: int) -> Channel | None:
        async with self.ctx.sm() as session:
            return await session.get(Channel, (self.ctx.bot_id, channel_id))

    async def known(self, user_id: int, *, offset: int = 0) -> list[Channel]:
        async with self.ctx.sm() as session:
            return list((await session.execute(select(Channel).join(ChannelRole,
                (ChannelRole.bot_id == Channel.bot_id) & (ChannelRole.channel_id == Channel.channel_id)).where(
                    Channel.bot_id == self.ctx.bot_id, ChannelRole.user_id == user_id,
                    ChannelRole.source.in_({"native", "virtual"})).order_by(Channel.channel_id).offset(offset).limit(10))).scalars())

    async def connect(self, reference: int | str, user_id: int) -> Channel:
        ctx = self.ctx
        chat = await ctx.bot.get_chat(reference)
        if chat.type != ChatType.CHANNEL:
            raise AccessDenied("not_channel")
        caller = await operator_rights(ctx, chat.id, user_id)
        member = await ctx.bot.get_chat_member(chat.id, ctx.bot_id)
        rights = rights_of(member)
        if member.status != "administrator" or not rights["can_post_messages"]:
            raise AccessDenied("bot_cannot_post")
        settings = await ctx.settings.get()
        async with ctx.sm() as session:
            # Serialize rare setup mutations within a bot, including per-operator quota checks.
            await session.execute(select(Bot.id).where(Bot.id == ctx.bot_id).with_for_update())
            row = await session.get(Channel, (ctx.bot_id, chat.id), with_for_update=True)
            role = await session.get(ChannelRole, (ctx.bot_id, chat.id, user_id))
            if role is None or row is None or row.status == "disconnected":
                count = await session.scalar(select(func.count()).select_from(ChannelRole).join(Channel,
                    (Channel.bot_id == ChannelRole.bot_id) & (Channel.channel_id == ChannelRole.channel_id)).where(
                        Channel.bot_id == ctx.bot_id, ChannelRole.user_id == user_id, Channel.status != "disconnected"))
                if int(count or 0) >= settings.max_channels_per_operator:
                    raise AccessDenied("channel_limit")
            await session.execute(upsert(session, Channel).values(bot_id=ctx.bot_id, channel_id=chat.id,
                title=chat.title or str(chat.id)).on_conflict_do_nothing())
            row = await session.get(Channel, (ctx.bot_id, chat.id), populate_existing=True)
            assert row is not None
            row.title, row.username = (chat.title or str(chat.id))[:256], chat.username
            row.connected_by, row.status, row.bot_status = user_id, "active", "administrator"
            row.rights, row.generation, row.updated_at = rights, row.generation + 1, utcnow()
            row.last_event_at = utcnow().replace(microsecond=0)
            row.last_update_id = None
            await session.flush()
            await session.execute(upsert(session, ChannelRole).values(bot_id=ctx.bot_id, channel_id=chat.id,
                user_id=user_id, permissions=caller).on_conflict_do_update(index_elements=["bot_id", "channel_id", "user_id"],
                    set_={"permissions": caller, "source": "native", "updated_at": utcnow()}))
            await session.execute(upsert(session, Entitlement).values(bot_id=ctx.bot_id, channel_id=chat.id,
                max_schedules=settings.free_max_schedules).on_conflict_do_nothing())
            await self.changed(session, row, "channel.connected", user_id)
            await session.commit()
            return row

    async def disconnect(self, channel_id: int, user_id: int, generation: int) -> Channel:
        await operator_rights(self.ctx, channel_id, user_id)
        async with self.ctx.sm() as session:
            row = await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            if row is None or row.generation != generation:
                raise AccessDenied("stale_menu")
            row.status, row.generation, row.updated_at = "disconnected", row.generation + 1, utcnow()
            await session.flush()
            await self.changed(session, row, "channel.disconnected", user_id)
            await session.commit()
            return row

    async def refresh(self, channel_id: int, user_id: int, generation: int) -> Channel:
        await operator_rights(self.ctx, channel_id, user_id)
        member = await self.ctx.bot.get_chat_member(channel_id, self.ctx.bot_id)
        async with self.ctx.sm() as session:
            row = await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            if row is None or row.generation != generation:
                raise AccessDenied("stale_menu")
            rights = rights_of(member)
            if row.rights != rights or row.bot_status != member.status:
                row.rights, row.bot_status = rights, str(member.status)
                if row.status != "disconnected":
                    row.status = "removed" if member.status in {"left", "kicked"} else (
                        "observed" if row.connected_by is None else "active" if rights["can_post_messages"] else "degraded")
                row.generation, row.updated_at = row.generation + 1, utcnow()
                await session.flush()
                await self.changed(session, row, "channel.refreshed", user_id)
            await session.commit()
            return row

    async def membership(self, session: AsyncSession, event: ChatMemberUpdated, update_id: int) -> None:
        ctx = self.ctx
        if event.chat.type != ChatType.CHANNEL or event.new_chat_member.user.id != ctx.bot_id:
            return
        await session.execute(upsert(session, Channel).values(bot_id=ctx.bot_id, channel_id=event.chat.id,
            title=(event.chat.title or str(event.chat.id))[:256]).on_conflict_do_nothing())
        row = await session.get(Channel, (ctx.bot_id, event.chat.id), with_for_update=True, populate_existing=True)
        assert row is not None
        if row.last_event_at and (event.date < row.last_event_at or (
                event.date == row.last_event_at and row.last_update_id is not None and update_id <= row.last_update_id)):
            return
        member = event.new_chat_member
        row.bot_status, row.rights = str(member.status), rights_of(member)
        if row.status != "disconnected":
            row.status = "removed" if member.status in {"left", "kicked"} else (
                "observed" if row.connected_by is None else "active" if row.rights["can_post_messages"] else "degraded")
        row.title = (event.chat.title or row.title)[:256]
        row.username, row.last_event_at, row.last_update_id = event.chat.username, event.date, update_id
        row.generation, row.updated_at = row.generation + 1, utcnow()
        await session.flush()
        await self.changed(session, row, "channel.membership", event.from_user.id)

    async def changed(self, session: AsyncSession, row: Channel, action: str, actor_id: int) -> None:
        ctx = self.ctx
        session.add(Event(bot_id=ctx.bot_id, id=uuid.uuid4().hex, channel_id=row.channel_id, actor_id=actor_id,
            action=action, details={"status": row.status, "generation": row.generation}))
        from bots.channelmanager.automation import AUTO_KINDS, CLEANUP
        from bots.channelmanager.growth_specs import GROWTH_CLEANUP, GROWTH_KINDS
        from bots.channelmanager.member_specs import MEMBER_CLEANUP, MEMBER_KINDS
        stale = (await session.scalars(select(Operation.id).where(Operation.bot_id == ctx.bot_id,
            Operation.channel_id == row.channel_id, Operation.generation != row.generation,
            Operation.status.in_({"pending", "running"}), Operation.dispatched.is_(False),
            Operation.kind.not_in(GROWTH_CLEANUP) if action == "channel.disconnected" else Operation.kind.in_({"notice", "publish", "edit", "pin", "markup", *(AUTO_KINDS - CLEANUP), *(MEMBER_KINDS - MEMBER_CLEANUP), *(GROWTH_KINDS - GROWTH_CLEANUP)}))
            .with_for_update(skip_locked=True))).all()
        await session.execute(update(Operation).where(Operation.bot_id == ctx.bot_id, Operation.id.in_(stale)).values(
                status="cancelled", error_code="channel_changed", updated_at=utcnow()))
        if row.connected_by is not None:
            lang = await session.scalar(select(BotUser.lang).where(BotUser.bot_id == ctx.bot_id,
                                                                  BotUser.user_id == row.connected_by))
            lang = ctx.translator.resolve(lang)
            state = ctx.translator.get(lang, f"chm-state-{row.status}")
            text = ctx.translator.get(lang, "chm-notice", title=esc(row.title), status=state)
            await outbox.enqueue(session, ctx, row, kind="notice", dedupe_key=f"status:{row.channel_id}:{row.generation}",
                                 payload={"recipient_id": row.connected_by, "text": text})

    async def totals(self) -> dict[str, int]:
        return await totals_for(self.ctx.sm, [self.ctx.bot_id])


async def totals_for(sm, bot_ids) -> dict[str, int]:
    async with sm() as session:
        channels = int(await session.scalar(select(func.count()).select_from(Channel).where(
            Channel.bot_id.in_(bot_ids), Channel.status == "active")) or 0)
        states = dict((await session.execute(select(Operation.status, func.count()).where(
            Operation.bot_id.in_(bot_ids)).group_by(Operation.status))).all())
        inbox = dict((await session.execute(select(Inbox.status, func.count()).where(
            Inbox.bot_id.in_(bot_ids)).group_by(Inbox.status))).all())
        sources = dict((await session.execute(select(AutoSource.status, func.count()).where(
            AutoSource.bot_id.in_(bot_ids)).group_by(AutoSource.status))).all())
        automation = dict((await session.execute(select(AutoAction.status, func.count()).where(
            AutoAction.bot_id.in_(bot_ids)).group_by(AutoAction.status))).all())
        members = dict((await session.execute(select(JoinRequest.status, func.count()).where(
            JoinRequest.bot_id.in_(bot_ids)).group_by(JoinRequest.status))).all())
        cleanup = await session.scalar(select(func.count()).select_from(MemberAction).where(MemberAction.bot_id.in_(bot_ids),
            MemberAction.cleanup.is_(True), MemberAction.status.in_({"pending", "failed", "uncertain"})))
    return {"channels": channels, "pending": int(states.get("pending", 0)),
            "failed": int(states.get("failed", 0)), "uncertain": int(states.get("uncertain", 0)),
            "inbox_pending": int(inbox.get("pending", 0)), "inbox_failed": int(inbox.get("failed", 0)),
            "auto_collecting": int(sources.get("collecting", 0)), "auto_held": int(sources.get("held", 0)),
            "auto_failed": int(automation.get("failed", 0)), "auto_uncertain": int(automation.get("uncertain", 0)),
            "members_pending": int(members.get("pending", 0)), "members_held": int(members.get("held", 0)),
            "members_uncertain": int(members.get("uncertain", 0)), "members_cleanup": int(cleanup or 0)}
