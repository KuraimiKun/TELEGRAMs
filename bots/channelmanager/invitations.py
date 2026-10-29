"""Native invite attribution credits distinct first observed joins to one live request."""

import hashlib
import uuid
from datetime import timedelta

from sqlalchemy import select

from bots.channelmanager.growth import enqueue, unseal
from bots.channelmanager.models import Channel, InviteCredit, JoinRequest, MemberHead, MemberInvite
from core.db.base import upsert, utcnow


def link_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def satisfied(request, spec, now=None):
    if spec.invite_threshold == 0 or request.invite_count >= spec.invite_threshold:
        return True
    return bool(spec.invite_timeout_bypass and spec.invite_timeout_seconds and (
        (now or utcnow()) >= request.requested_at + timedelta(seconds=spec.invite_timeout_seconds)))


async def ensure(session, ctx, channel, request):
    row = await session.scalar(select(MemberInvite).where(MemberInvite.bot_id == ctx.bot_id,
        MemberInvite.request_id == request.id, MemberInvite.epoch == request.invite_epoch))
    if row is None:
        row = MemberInvite(bot_id=ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=channel.channel_id,
            request_id=request.id, user_id=request.user_id, epoch=request.invite_epoch)
        session.add(row)
        await session.flush()
        await enqueue(session, ctx, channel, kind="invite", actor_id=request.actor_id, user_id=request.user_id,
            resource_id=row.id, generation=request.invite_epoch, key=f"invite:{request.id}:{request.invite_epoch}")
    return row


async def active_link(ctx, request):
    async with ctx.sm() as session:
        row = await session.scalar(select(MemberInvite).where(MemberInvite.bot_id == ctx.bot_id,
            MemberInvite.request_id == request.id, MemberInvite.epoch == request.invite_epoch, MemberInvite.status == "active"))
    return unseal(ctx, row.link_enc) if row and row.link_enc else None


async def revoke_for(session, ctx, channel, request):
    for row in (await session.scalars(select(MemberInvite).where(MemberInvite.bot_id == ctx.bot_id,
        MemberInvite.request_id == request.id, MemberInvite.status == "active"))).all():
        await enqueue(session, ctx, channel, kind="revoke_invite", actor_id=request.actor_id, user_id=request.user_id,
            resource_id=row.id, generation=row.epoch, key=f"revoke:{row.id}")
        row.status = "revoking"


async def credit(session, ctx, event, request, *, previous_join):
    if previous_join or event.new_chat_member.user.is_bot:
        return False
    native = event.invite_link
    digest = link_hash(native.invite_link) if native and native.creator.id == ctx.bot_id and not native.is_revoked else request.referral_hash if request else None
    if not digest:
        return False
    user_id = event.new_chat_member.user.id
    return await _credit(session, ctx, event.chat.id, user_id, digest)


async def credit_request(session, ctx, request):
    from bots.channelmanager.member_specs import MemberSpec
    spec = MemberSpec.model_validate(request.spec)
    if not request.captcha_solved or request.required_index != len(spec.required) or not request.referral_eligible or not request.referral_hash or request.filter_code or request.expires_at <= utcnow():
        return False
    return await _credit(session, ctx, request.channel_id, request.user_id, request.referral_hash)


async def _credit(session, ctx, channel_id, user_id, digest):
    invite = await session.scalar(select(MemberInvite).where(MemberInvite.bot_id == ctx.bot_id,
        MemberInvite.channel_id == channel_id, MemberInvite.link_hash == digest, MemberInvite.status == "active"))
    if invite is None or invite.user_id == user_id:
        return False
    owner = await session.get(JoinRequest, (ctx.bot_id, invite.request_id), with_for_update=True)
    head = await session.get(MemberHead, (ctx.bot_id, channel_id, invite.user_id), with_for_update=True)
    if owner is None or head is None or head.request_id != owner.id or owner.status != "pending" or owner.expires_at <= utcnow() or owner.invite_epoch != invite.epoch:
        return False
    inserted = await session.execute(upsert(session, InviteCredit).values(bot_id=ctx.bot_id, channel_id=channel_id,
        invitee_id=user_id, invite_id=invite.id, request_id=owner.id).on_conflict_do_nothing().returning(InviteCredit.invitee_id))
    if inserted.scalar_one_or_none() is None:
        return False
    owner.invite_count, owner.next_check = owner.invite_count + 1, utcnow()
    return True


async def cleanup_one(ctx):
    async with ctx.sm() as session:
        row = await session.scalar(select(MemberInvite).join(JoinRequest, (JoinRequest.bot_id == MemberInvite.bot_id) &
            (JoinRequest.id == MemberInvite.request_id)).where(MemberInvite.bot_id == ctx.bot_id, MemberInvite.status == "active",
                (JoinRequest.status != "pending") | (JoinRequest.invite_epoch != MemberInvite.epoch)).order_by(MemberInvite.id).limit(1))
        if row is None:
            return False
        channel = await session.get(Channel, (ctx.bot_id, row.channel_id), with_for_update=True)
        request = await session.get(JoinRequest, (ctx.bot_id, row.request_id))
        await revoke_for(session, ctx, channel, request)
        await session.commit()
        return True
