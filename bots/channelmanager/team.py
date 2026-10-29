"""Channel-scoped delegation verified against the grantor's current native authority."""

import uuid

from sqlalchemy import delete, func, select, update

from bots.channelmanager.content import ContentError
from bots.channelmanager.growth_specs import DelegateSpec
from bots.channelmanager.models import (
    Channel,
    ChannelRole,
    Delivery,
    Event,
    Operation,
    Post,
    PostSchedule,
    VirtualGrant,
)
from bots.channelmanager.permissions import AccessDenied, operator_rights
from core.db.base import upsert


async def grantor_rights(ctx, channel_id, user_id):
    rights = await operator_rights(ctx, channel_id, user_id)
    member = await ctx.bot.get_chat_member(channel_id, user_id)
    if member.status != "creator" and not getattr(member, "can_promote_members", False):
        raise AccessDenied("delegation_authority")
    return rights


def delegated_rights(rights, spec):
    if ((spec.edit_all or spec.settings) and not rights["can_edit_messages"]) or (spec.delete_all and not rights["can_delete_messages"]):
        raise AccessDenied("delegation_ceiling")


class TeamService:
    def __init__(self, ctx):
        self.ctx = ctx

    async def list(self, channel_id, actor_id):
        await grantor_rights(self.ctx, channel_id, actor_id)
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(VirtualGrant).where(VirtualGrant.bot_id == self.ctx.bot_id,
                VirtualGrant.channel_id == channel_id).order_by(VirtualGrant.user_id))).all())

    async def save(self, channel_id, actor_id, user_id, spec: DelegateSpec, *, generation=0, active=True):
        if user_id <= 0 or user_id == self.ctx.bot_id:
            raise ContentError("delegate_user")
        rights = await grantor_rights(self.ctx, channel_id, actor_id)
        if active:
            delegated_rights(rights, spec)
        from bots.channelmanager.billing import limits_for
        limits = await limits_for(self.ctx, channel_id)
        async with self.ctx.sm() as session:
            channel = await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            if channel is None or channel.status != "active":
                raise AccessDenied("channel_inactive")
            row = await session.get(VirtualGrant, (self.ctx.bot_id, channel_id, user_id), with_for_update=True)
            if (row.generation if row else 0) != generation:
                raise ContentError("stale")
            count = int(await session.scalar(select(func.count()).select_from(VirtualGrant).where(VirtualGrant.bot_id == self.ctx.bot_id,
                VirtualGrant.channel_id == channel_id, VirtualGrant.active.is_(True), VirtualGrant.user_id != user_id)) or 0)
            if active and count >= limits.delegates:
                raise ContentError("plan_limit")
            if row is None:
                row = VirtualGrant(bot_id=self.ctx.bot_id, channel_id=channel_id, user_id=user_id, grantor_id=actor_id, permissions=spec.model_dump())
                session.add(row)
            else:
                row.generation += 1
            row.active, row.grantor_id, row.permissions = active, actor_id, spec.model_dump()
            if active:
                await session.execute(upsert(session, ChannelRole).values(bot_id=self.ctx.bot_id, channel_id=channel_id,
                    user_id=user_id, source="virtual", permissions={}).on_conflict_do_nothing())
            else:
                await session.execute(delete(ChannelRole).where(ChannelRole.bot_id == self.ctx.bot_id,
                    ChannelRole.channel_id == channel_id, ChannelRole.user_id == user_id, ChannelRole.source == "virtual"))
            session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=channel_id, actor_id=actor_id,
                action="team.granted" if active else "team.revoked", details={"user_id": user_id}))
            await session.commit()
            return row

    async def adopt(self, post_id, actor_id):
        view = await self.ctx.extras["posts"].view(post_id, actor_id, "edit")
        for channel_id in view.post.target_ids:
            rights = await operator_rights(self.ctx, channel_id, actor_id)
            if not rights["can_edit_messages"]:
                raise AccessDenied("adoption_right")
        async with self.ctx.sm() as session:
            post = await session.get(Post, (self.ctx.bot_id, post_id), with_for_update=True)
            if post is None or post.detached:
                raise ContentError("stale")
            targets = list((await session.scalars(select(Delivery).where(Delivery.bot_id == self.ctx.bot_id,
                Delivery.post_id == post.id).with_for_update())).all())
            if await session.scalar(select(Operation.id).where(Operation.bot_id == self.ctx.bot_id,
                Operation.delivery_id.in_([d.id for d in targets]), Operation.status == "running", Operation.dispatched.is_(True)).limit(1)):
                raise ContentError("busy")
            previous = post.creator_id
            post.creator_id, post.generation = actor_id, post.generation + 1
            for target in targets:
                if target.state in {"pending", "held", "failed", "cancelled"}:
                    target.actor_id, target.state, target.error_code = actor_id, "held", "adopted_review_required"
            await session.execute(update(Operation).where(Operation.bot_id == self.ctx.bot_id,
                Operation.delivery_id.in_([d.id for d in targets]), Operation.kind.in_({"publish", "edit", "pin", "markup"}),
                Operation.status.in_({"pending", "running"}), Operation.dispatched.is_(False)).values(status="cancelled", error_code="adopted"))
            schedule = await session.get(PostSchedule, (self.ctx.bot_id, post.id))
            if schedule and schedule.status == "pending":
                schedule.status = "held"
            session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=post.channel_id, actor_id=actor_id,
                action="post.adopted", details={"post_id": post.id, "previous_creator": previous}))
            await session.commit()
            return post
