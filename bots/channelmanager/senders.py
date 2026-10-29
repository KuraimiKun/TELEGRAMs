"""Verified full-manager bindings to existing factory children; no token import here."""

import hashlib
import uuid

from sqlalchemy import func, select

from bots.channelmanager.content import ContentError
from bots.channelmanager.models import Channel, Event, MemberBan, MemberInvite, SenderBinding
from bots.channelmanager.permissions import AccessDenied, operator_rights
from core.db.models import Bot as BotRecord
from core.db.models import ChildBot
from core.factory.children import ChildService
from core.factory.runtime import ChildRegistry
from core.sdk.registry import SharedInfra


def token_epoch(child):
    return hashlib.sha256(child.token_enc.encode()).hexdigest()


async def allowed(ctx, channel_id, *, session):
    channel = await session.get(Channel, (ctx.bot_id, channel_id))
    if channel is None or channel.status != "active":
        return False
    from bots.channelmanager.release import allowed as release_allowed
    if not await release_allowed(ctx, "branded" if ctx.is_child else "publishing", session=session, channel_id=channel_id):
        return False
    if not ctx.is_child:
        return not channel.sender_paused
    binding = await session.scalar(select(SenderBinding).where(SenderBinding.sender_bot_id == ctx.bot_id,
        SenderBinding.channel_id == channel_id, SenderBinding.active.is_(True)))
    child = await session.get(ChildBot, ctx.bot_id)
    control = await session.get(BotRecord, binding.bot_id) if binding else None
    if binding is None or control is None or not control.active or child is None or child.status != "active" or child.template != "channelmanager" or child.owner_id != binding.owner_id or token_epoch(child) != binding.token_epoch:
        return False
    from bots.channelmanager.billing import limits_for
    return (await limits_for(ctx, channel_id, session=session)).branded


def registry_for(ctx):
    if "chm_child_registry" not in ctx.extras:
        infra = SharedInfra(engine=ctx.sm.kw["bind"], sm=ctx.sm, redis=ctx.redis,
            cache_redis=ctx.cache_redis or ctx.redis, session=ctx.bot.session, ai=ctx.ai)
        ctx.extras["chm_child_registry"] = ChildRegistry(ctx.platform, infra, ctx.shutdown)
    return ctx.extras["chm_child_registry"]


class SenderService:
    def __init__(self, ctx):
        self.ctx = ctx

    async def choices(self, actor_id):
        if self.ctx.is_child:
            return []
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(ChildBot).where(ChildBot.owner_id == actor_id,
                ChildBot.template == "channelmanager", ChildBot.status == "active").order_by(ChildBot.bot_id).limit(100))).all())

    async def bind(self, channel_id, actor_id, sender_id):
        from bots.channelmanager.release import require
        await require(self.ctx, "branded")
        if self.ctx.is_child:
            raise ContentError("control_sender_only")
        rights = await operator_rights(self.ctx, channel_id, actor_id)
        if not rights["can_edit_messages"]:
            raise AccessDenied("sender_right")
        from bots.channelmanager.billing import limits_for
        if not (await limits_for(self.ctx, channel_id)).branded:
            raise ContentError("plan_limit")
        async with self.ctx.sm() as session:
            child = await session.get(ChildBot, sender_id)
        if child is None:
            raise ContentError("sender_missing")
        service = ChildService(self.ctx.sm, self.ctx.redis, self.ctx.platform, factory_bot_id=child.factory_bot_id,
            templates={"channelmanager"}, session=self.ctx.bot.session)
        owned = await service.get_owned(actor_id, sender_id)
        if owned is None or owned.template != "channelmanager" or owned.status != "active":
            raise AccessDenied("sender_owner")
        registry = registry_for(self.ctx)
        await registry.evict(sender_id)
        runtime = await registry.get(sender_id)
        if runtime is None:
            raise ContentError("sender_unavailable")
        await operator_rights(runtime.ctx, channel_id, actor_id)
        child_channel = await runtime.ctx.extras["channelmanager"].get(channel_id)
        if child_channel is None or child_channel.status != "active":
            raise ContentError("connect_sender_first")
        bot = await runtime.ctx.bot.get_chat_member(channel_id, sender_id)
        if bot.status != "administrator" or not getattr(bot, "can_post_messages", False):
            raise AccessDenied("sender_right")
        username = self.ctx.username or (await self.ctx.bot.get_me()).username
        async with self.ctx.sm() as session:
            for bot_id in sorted({self.ctx.bot_id, sender_id}):
                await session.get(Channel, (bot_id, channel_id), with_for_update=True)
            parent = await session.get(Channel, (self.ctx.bot_id, channel_id))
            scoped = await session.get(Channel, (sender_id, channel_id))
            if parent is None or scoped is None or parent.status != "active" or scoped.status != "active":
                raise ContentError("stale")
            current = await session.get(ChildBot, sender_id, with_for_update=True)
            if current.owner_id != actor_id or current.status != "active" or token_epoch(current) != token_epoch(owned):
                raise ContentError("stale")
            row = await session.get(SenderBinding, (self.ctx.bot_id, channel_id), with_for_update=True)
            if row is None:
                row = SenderBinding(bot_id=self.ctx.bot_id, channel_id=channel_id, sender_bot_id=sender_id,
                    owner_id=actor_id, token_epoch=token_epoch(current), control_username=username)
                session.add(row)
            else:
                row.sender_bot_id, row.owner_id, row.token_epoch, row.active = sender_id, actor_id, token_epoch(current), True
                row.generation += 1
            parent.sender_paused = True
            # Fence work created before this binding, including an immediate unbind/rebind.
            parent.generation += 1
            await self.ctx.extras["channelmanager"].changed(session, parent, "sender.bound", actor_id)
            scoped.generation += 1
            await runtime.ctx.extras["channelmanager"].changed(session, scoped, "sender.bound", actor_id)
            session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=channel_id, actor_id=actor_id,
                action="sender.bound", details={"sender_id": sender_id, "role": "full_manager", "media_policy": "upload_to_sender"}))
            await session.commit()
            return row

    async def unbind(self, channel_id, actor_id):
        if self.ctx.is_child:
            raise ContentError("control_sender_only")
        rights = await operator_rights(self.ctx, channel_id, actor_id)
        if not rights["can_edit_messages"]:
            raise AccessDenied("sender_right")
        async with self.ctx.sm() as session:
            channel = await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            row = await session.get(SenderBinding, (self.ctx.bot_id, channel_id), with_for_update=True)
            if row:
                row.active, row.generation = False, row.generation + 1
            channel.sender_paused = False
            session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=channel_id, actor_id=actor_id,
                action="sender.unbound", details={"review_held_work": True}))
            await session.commit()

    async def stopping(self, reason):
        return await stop_owned(self.ctx.sm, self.ctx.bot_id, reason)


async def stop_owned(sm, sender_id, reason):
    """SQL-only lifecycle fencing, including when a token is lost or no longer decrypts."""
    async with sm() as session:
        bans = int(await session.scalar(select(func.count()).select_from(MemberBan).where(MemberBan.bot_id == sender_id,
            MemberBan.status.in_({"active", "pending", "uncertain"}))) or 0)
        invites = int(await session.scalar(select(func.count()).select_from(MemberInvite).where(MemberInvite.bot_id == sender_id,
            MemberInvite.status.in_({"active", "pending", "revoking", "uncertain"}))) or 0)
        rows = list((await session.scalars(select(SenderBinding).where(SenderBinding.sender_bot_id == sender_id,
            SenderBinding.active.is_(True)).with_for_update())).all())
        for row in rows:
            row.active, row.generation = False, row.generation + 1
            session.add(Event(bot_id=row.bot_id, id=uuid.uuid4().hex, channel_id=row.channel_id, actor_id=None,
                action="sender.stopped", details={"sender_id": sender_id, "reason": reason, "bans": bans, "invites": invites}))
        # Native timed bans expire at Telegram even when this sender is paused.
        residual = bans + invites
        await session.commit()
        return f"channelmanager_cleanup_review:{residual}" if residual else None


async def factory_sweep(registry):
    from bots.channelmanager import worker
    # One SQL aggregate for the template, rather than overwriting fleet gauges with each child.
    await worker.emit_metrics(registry.infra.sm, "factory_channelmanager", select(ChildBot.bot_id).where(ChildBot.template == "channelmanager"))
    async with registry.infra.sm() as session:
        ids = list((await session.scalars(select(ChildBot.bot_id).join(BotRecord, BotRecord.id == ChildBot.bot_id).where(
            ChildBot.template == "channelmanager", ChildBot.status == "active", BotRecord.active.is_(True)).order_by(ChildBot.bot_id))).all())
    if not ids:
        return
    cursor = getattr(registry, "_chm_cursor", 0) % len(ids)
    selected = (ids + ids)[cursor:cursor + min(5, len(ids))]
    registry._chm_cursor = (cursor + len(selected)) % len(ids)
    for bot_id in selected:
        runtime = await registry.get(bot_id)
        if runtime:
            await worker.sweep(runtime.ctx)
            await worker.tick(runtime.ctx)
