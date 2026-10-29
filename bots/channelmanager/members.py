"""Durable membership observation, policy changes and admission planning."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import timedelta

from aiogram.types import ChatJoinRequest, ChatMemberUpdated, Message, User
from sqlalchemy import func, select, update

from bots.channelmanager import outbox
from bots.channelmanager.content import ContentError
from bots.channelmanager.member_specs import MEMBER_CLEANUP, MEMBER_KINDS, MemberSpec
from bots.channelmanager.models import (
    Channel,
    Event,
    JoinRequest,
    MemberAction,
    MemberBan,
    MemberBulk,
    MemberConfig,
    MemberHead,
    MemberLead,
    Operation,
)
from bots.channelmanager.permissions import AccessDenied, bot_post_rights, operator_rights
from core.db.base import upsert, utcnow
from core.sdk.context import BotContext
from core.ui.text import esc


def profile(user: User) -> dict:
    return user.model_dump(mode="json", include={"first_name", "last_name", "username", "language_code"}, exclude_none=True)


def is_member(member) -> bool:
    return member.status in {"creator", "administrator", "member"} or (member.status == "restricted" and bool(getattr(member, "is_member", False)))


async def rights(ctx, channel_id, actor_id, *, restrict=False):
    allowed = await operator_rights(ctx, channel_id, actor_id)
    if not allowed["can_invite_users"] or (restrict and not allowed["can_restrict_members"]):
        raise AccessDenied("member_right")
    channel = await ctx.extras["channelmanager"].get(channel_id)
    if channel is None or channel.status != "active":
        raise AccessDenied("channel_inactive")


async def head_for(session, ctx, channel_id, user_id):
    await session.execute(upsert(session, MemberHead).values(bot_id=ctx.bot_id, channel_id=channel_id, user_id=user_id).on_conflict_do_nothing())
    return await session.get(MemberHead, (ctx.bot_id, channel_id, user_id), with_for_update=True, populate_existing=True)


async def lead_for(session, ctx, channel_id, user_id):
    await session.execute(upsert(session, MemberLead).values(bot_id=ctx.bot_id, channel_id=channel_id, user_id=user_id).on_conflict_do_nothing())
    row = await session.get(MemberLead, (ctx.bot_id, channel_id, user_id), with_for_update=True, populate_existing=True)
    from bots.channelmanager.growth import opted_out
    if await opted_out(session, ctx, channel_id, user_id):
        row.opted_out, row.campaign_opt_in = True, False
    return row


async def action(session, ctx, channel, config, *, kind, key, user_id=None, request=None, payload=None, run_at=None, cleanup=False,
                 status="pending", code=None):
    key = f"member:{key}"
    old = await session.scalar(select(MemberAction).where(MemberAction.bot_id == ctx.bot_id, MemberAction.dedupe_key == key))
    if old:
        return old
    row = MemberAction(bot_id=ctx.bot_id, id=uuid.uuid4().hex, channel_id=channel.channel_id,
        request_id=request.id if request else None, user_id=user_id, actor_id=request.actor_id if request else config.actor_id,
        generation=config.generation, kind=kind, dedupe_key=key, payload=payload or {}, cleanup=cleanup, status=status, error_code=code)
    session.add(row)
    await session.flush()
    if status == "pending":
        row.operation_id = await outbox.enqueue(session, ctx, channel, kind=f"member_{kind}", dedupe_key=key,
            payload={"action_id": row.id}, run_at=run_at, member_action_id=row.id)
    return row


async def audit(session, ctx, channel, config, event, *, user_id=None, request=None, code=None, key=None):
    event_id = key or uuid.uuid4().hex
    if await session.get(Event, (ctx.bot_id, event_id)):
        return
    session.add(Event(bot_id=ctx.bot_id, id=event_id, channel_id=channel.channel_id, actor_id=user_id,
        action=f"members.{event}", details={"request_id": request.id if request else None, "code": code}))
    spec = MemberSpec.model_validate(config.spec)
    if spec.enabled and spec.log_channel and event in spec.log_events:
        destination = await session.get(Channel, (ctx.bot_id, spec.log_channel))
        text = ctx.translator.get(spec.log_language, "chm5-log", channel=str(channel.channel_id), user=str(user_id or "—"),
            event=ctx.translator.get(spec.log_language, f"chm5-event-{event}"), code=esc(code or "—"))
        await action(session, ctx, channel, config, kind="log", key=f"log:{event_id}", user_id=user_id,
            payload={"event": event, "code": code, "language": spec.log_language, "destination": spec.log_channel,
                "destination_generation": destination.generation if destination else None, "text": text})


async def invalidate(session, ctx, *, channel_id, request_id=None, code):
    query = select(Operation.id).join(MemberAction, (MemberAction.bot_id == Operation.bot_id) & (MemberAction.id == Operation.member_action_id)).where(
        Operation.bot_id == ctx.bot_id, Operation.channel_id == channel_id, Operation.kind.in_(MEMBER_KINDS - MEMBER_CLEANUP),
        Operation.status.in_({"pending", "running"}), Operation.dispatched.is_(False))
    if request_id:
        query = query.where(MemberAction.request_id == request_id)
    ids = (await session.scalars(query.with_for_update(of=Operation, skip_locked=True))).all()
    await session.execute(update(Operation).where(Operation.bot_id == ctx.bot_id, Operation.id.in_(ids)).values(status="cancelled", error_code=code))


async def observe_request(session, ctx, event: ChatJoinRequest, update_id: int, received_at):
    channel = await session.get(Channel, (ctx.bot_id, event.chat.id), with_for_update=True)
    if channel is None or channel.status != "active" or channel.connected_by is None or event.from_user.is_bot:
        return
    config = await session.get(MemberConfig, (ctx.bot_id, channel.channel_id))
    if config is None:
        config = MemberConfig(bot_id=ctx.bot_id, channel_id=channel.channel_id, actor_id=channel.connected_by, spec=MemberSpec().model_dump(mode="json"))
        session.add(config)
        await session.flush()
    head = await head_for(session, ctx, channel.channel_id, event.from_user.id)
    previous_lead = await session.get(MemberLead, (ctx.bot_id, channel.channel_id, event.from_user.id))
    first_request = head.last_request_at is None and (previous_lead is None or previous_lead.last_join_at is None)
    # A same-second rejoin needs an intervening observed departure.
    duplicate = head.last_request_at and (event.date < head.last_request_at or (
        event.date == head.last_request_at and head.state not in {"left", "kicked"}))
    if duplicate or (head.observed_at and (event.date, update_id) <= (head.observed_at, head.update_id)):
        return
    if head.request_id:
        old = await session.get(JoinRequest, (ctx.bot_id, head.request_id), with_for_update=True)
        if old and old.status in {"pending", "held"}:
            old.status, old.error_code = "superseded", "new_request"
            await invalidate(session, ctx, channel_id=channel.channel_id, request_id=old.id, code="new_request")
    head.generation += 1
    head.last_request_at, head.observed_at, head.update_id, head.state = event.date, event.date, update_id, "pending"
    head.last_actor_id = event.from_user.id
    spec = MemberSpec.model_validate(config.spec)
    special_query = bool(getattr(event, "query_id", None))
    user_profile = profile(event.from_user)
    if special_query:
        user_profile["query_unsupported"] = True
    count = int(await session.scalar(select(func.count()).select_from(JoinRequest).where(JoinRequest.bot_id == ctx.bot_id,
        JoinRequest.channel_id == channel.channel_id, JoinRequest.created_at >= utcnow() - timedelta(seconds=10))) or 0) + 1
    rejection = spec.profile.rejects(profile(event.from_user), count)
    left, right = secrets.randbelow(8) + 2, secrets.randbelow(8) + 2
    choices = {left + right}
    while len(choices) < 4:
        choices.add(secrets.randbelow(25) + 1)
    options = list(choices)
    secrets.SystemRandom().shuffle(options)
    row = JoinRequest(bot_id=ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=channel.channel_id, user_id=event.from_user.id,
        generation=head.generation, actor_id=config.actor_id, config_generation=config.generation, spec=config.spec,
        profile=user_profile, requested_at=event.date, contact_chat_id=event.user_chat_id,
        contact_deadline=event.date + timedelta(seconds=300), expires_at=event.date + timedelta(seconds=spec.expires_seconds),
        approve_after=event.date + timedelta(seconds=spec.delay_seconds if spec.mode == "timed" else 0),
        captcha_solved=not spec.captcha, challenge={"a": left, "b": right, "choices": options, "answer": options.index(left + right)},
        filter_code=rejection, status="pending" if spec.enabled and received_at >= config.active_since and not special_query else "held",
        error_code="query_id_unsupported" if special_query else None if spec.enabled and received_at >= config.active_since else "workflow_disabled")
    session.add(row)
    row.referral_eligible = first_request
    native_link = event.invite_link
    if native_link and native_link.creator.id == ctx.bot_id and not native_link.is_revoked:
        from bots.channelmanager.invitations import link_hash
        row.referral_hash = link_hash(native_link.invite_link)
    head.request_id = row.id
    await lead_for(session, ctx, channel.channel_id, row.user_id)
    await session.flush()
    await audit(session, ctx, channel, config, "request", user_id=row.user_id, request=row)


async def observe_member(session, ctx, event: ChatMemberUpdated, update_id: int):
    channel = await session.get(Channel, (ctx.bot_id, event.chat.id), with_for_update=True)
    if channel is None or channel.status != "active" or event.new_chat_member.user.is_bot:
        return
    user_id = event.new_chat_member.user.id
    head = await head_for(session, ctx, channel.channel_id, user_id)
    if head.observed_at and (event.date, update_id) <= (head.observed_at, head.update_id):
        return
    was, now = is_member(event.old_chat_member), is_member(event.new_chat_member)
    head.observed_at, head.update_id = event.date, update_id
    head.last_actor_id = event.from_user.id
    head.state = "member" if now else event.new_chat_member.status
    config = await session.get(MemberConfig, (ctx.bot_id, channel.channel_id))
    if config is None:
        return
    spec = MemberSpec.model_validate(config.spec)
    lead = await lead_for(session, ctx, channel.channel_id, user_id)
    request = await session.get(JoinRequest, (ctx.bot_id, head.request_id), with_for_update=True) if head.request_id else None
    if now and not was:
        head.generation += 1
        from bots.channelmanager.invitations import credit
        await credit(session, ctx, event, request, previous_join=lead.last_join_at is not None)
        lead.last_join_at = event.date
        if request and request.status in {"pending", "held", "uncertain"}:
            request.status, request.error_code = "approved", "external_approval"
            await invalidate(session, ctx, channel_id=channel.channel_id, request_id=request.id, code="external_approval")
        await audit(session, ctx, channel, config, "joined", user_id=user_id, request=request)
        if spec.enabled:
            count = int(await session.scalar(select(func.count()).select_from(Event).where(Event.bot_id == ctx.bot_id,
                Event.channel_id == channel.channel_id, Event.action == "members.joined", Event.created_at >= utcnow() - timedelta(seconds=10))) or 0)
            rejection = spec.profile.rejects(profile(event.new_chat_member.user), count)
            if rejection:
                await queue_ban(session, ctx, channel, config, user_id, f"join:{update_id}", seconds=60 if spec.profile.outcome == "decline" else None, code=rejection)
                await audit(session, ctx, channel, config, "filter_rejected", user_id=user_id, code=rejection)
            elif request and request.status == "approved":
                await welcome(session, ctx, channel, config, request)
    elif was and not now:
        lead.last_leave_at = event.date
        voluntary = event.from_user.id == user_id and event.new_chat_member.status == "left"
        event_type = "left" if voluntary else "removed"
        await audit(session, ctx, channel, config, event_type, user_id=user_id, code="bot_enforcement" if event.from_user.id == ctx.bot_id else None)
        if spec.enabled and voluntary:
            if spec.goodbye:
                await action(session, ctx, channel, config, kind="goodbye", key=f"goodbye:{update_id}", user_id=user_id,
                    payload={"spec": spec.goodbye.model_dump(mode="json")}, status="pending" if lead.reachable and not lead.opted_out and lead.private_interacted_at else "skipped",
                    code=None if lead.reachable and not lead.opted_out and lead.private_interacted_at else "no_private_interaction")
            if spec.departure_ban:
                await queue_ban(session, ctx, channel, config, user_id, f"leave:{update_id}", seconds=spec.ban_seconds)
                if spec.linked_group:
                    await queue_ban(session, ctx, channel, config, user_id, f"leave-group:{update_id}", seconds=spec.ban_seconds, destination=spec.linked_group)


async def queue_ban(session, ctx, channel, config, user_id, key, *, seconds=None, destination=None, code=None, request=None):
    destination = destination or channel.channel_id
    until = (utcnow() + timedelta(seconds=seconds)).replace(microsecond=0) if seconds else None
    row = await action(session, ctx, channel, config, kind="ban", key=key, user_id=user_id, request=request,
        payload={"destination": destination, "until_date": until.isoformat() if until else None, "code": code})
    head = await session.get(MemberHead, (ctx.bot_id, channel.channel_id, user_id))
    if head and request is None:
        row.payload = {**row.payload, "head_update_id": head.update_id, "head_generation": head.generation}
    if not await session.scalar(select(MemberBan.id).where(MemberBan.bot_id == ctx.bot_id, MemberBan.action_id == row.id)):
        session.add(MemberBan(bot_id=ctx.bot_id, id=uuid.uuid4().hex, channel_id=channel.channel_id, chat_id=destination,
            user_id=user_id, action_id=row.id, until_date=until))
    return row


async def welcome(session, ctx, channel, config, request, *, interactive=False):
    spec = MemberSpec.model_validate(request.spec)
    if spec.welcome is None:
        return
    existing = await session.scalar(select(MemberAction.id).where(MemberAction.bot_id == ctx.bot_id, MemberAction.request_id == request.id,
        MemberAction.kind == "welcome", MemberAction.status.in_({"pending", "succeeded", "uncertain"})).limit(1))
    if existing:
        return
    lead = await session.get(MemberLead, (ctx.bot_id, channel.channel_id, request.user_id))
    reachable = lead and lead.private_interacted_at and lead.reachable and not lead.opted_out
    await action(session, ctx, channel, config, kind="welcome", key=f"welcome:{request.id}:{int(interactive)}", user_id=request.user_id,
        request=request, payload={"spec": spec.welcome.model_dump(mode="json")}, status="pending" if reachable else "skipped",
        code=None if reachable else "no_private_interaction")


async def observe_service(session, ctx, message: Message):
    config = await session.get(MemberConfig, (ctx.bot_id, message.chat.id))
    channel = await session.get(Channel, (ctx.bot_id, message.chat.id))
    if config is None or channel is None or channel.status != "active":
        return
    spec = MemberSpec.model_validate(config.spec)
    kind = message.content_type
    if spec.enabled and kind in spec.cleanup:
        await action(session, ctx, channel, config, kind="clean", key=f"clean:{message.chat.id}:{message.message_id}", cleanup=True,
            payload={"message_id": message.message_id, "service": kind, "sent_at": message.date.isoformat()})


def start_token(ctx, request):
    expires = int(request.expires_at.timestamp())
    value = f"{ctx.bot_id}:{request.id}:{request.user_id}:{expires}"
    signature = hmac.new(ctx.bot.token.encode(), value.encode(), hashlib.sha256).hexdigest()[:20]
    return f"chj_{request.id}_{expires}_{signature}"


class MemberService:
    def __init__(self, ctx: BotContext):
        self.ctx = ctx

    async def config(self, channel_id, actor_id):
        await rights(self.ctx, channel_id, actor_id)
        async with self.ctx.sm() as session:
            return await session.get(MemberConfig, (self.ctx.bot_id, channel_id))

    async def save(self, channel_id, actor_id, spec: MemberSpec, generation=0):
        await rights(self.ctx, channel_id, actor_id, restrict=spec.enabled and (spec.departure_ban or spec.profile.outcome == "ban"))
        from bots.channelmanager.billing import limits_for
        if spec.enabled and spec.invite_threshold > (await limits_for(self.ctx, channel_id)).invite_threshold:
            raise ContentError("plan_limit")
        for content in (spec.introduction, spec.welcome, spec.goodbye):
            if content and content.media_bot_id not in {None, self.ctx.bot_id}:
                raise ContentError("media")
        if not spec.enabled:
            return await self._store(channel_id, actor_id, spec, generation)
        bot = await self.ctx.bot.get_chat_member(channel_id, self.ctx.bot_id)
        if bot.status != "administrator" or not getattr(bot, "can_invite_users", False):
            raise AccessDenied("bot_member_right")
        if (spec.departure_ban or spec.profile.outcome == "ban") and not getattr(bot, "can_restrict_members", False):
            raise AccessDenied("bot_restrict_right")
        if spec.cleanup and not getattr(bot, "can_delete_messages", False):
            raise AccessDenied("bot_delete_right")
        for required in spec.required:
            if required.chat_id == channel_id:
                raise ContentError("required_chat")
            member = await self.ctx.bot.get_chat_member(required.chat_id, self.ctx.bot_id)
            if member.status != "administrator":
                raise AccessDenied("required_chat_admin")
        if spec.linked_group:
            chat = await self.ctx.bot.get_chat(channel_id)
            group = await self.ctx.bot.get_chat(spec.linked_group)
            if getattr(chat, "linked_chat_id", None) != spec.linked_group or group.type != "supergroup":
                raise ContentError("linked_group")
            for who in (actor_id, self.ctx.bot_id):
                member = await self.ctx.bot.get_chat_member(spec.linked_group, who)
                if member.status not in {"creator", "administrator"} or (member.status != "creator" and not getattr(member, "can_restrict_members", False)):
                    raise AccessDenied("linked_group_right")
        if spec.log_channel:
            if spec.log_channel == channel_id:
                raise ContentError("log_channel")
            await operator_rights(self.ctx, spec.log_channel, actor_id)
            await bot_post_rights(self.ctx, spec.log_channel, "publish")
        return await self._store(channel_id, actor_id, spec, generation)

    async def _store(self, channel_id, actor_id, spec, generation):
        async with self.ctx.sm() as session:
            await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            row = await session.get(MemberConfig, (self.ctx.bot_id, channel_id), with_for_update=True)
            if (row.generation if row else 0) != generation:
                raise ContentError("stale")
            if row is None:
                row = MemberConfig(bot_id=self.ctx.bot_id, channel_id=channel_id, actor_id=actor_id, spec=spec.model_dump(mode="json"))
                session.add(row)
            else:
                row.generation += 1
            row.actor_id, row.spec, row.active_since = actor_id, spec.model_dump(mode="json"), utcnow()
            await session.execute(update(JoinRequest).where(JoinRequest.bot_id == self.ctx.bot_id, JoinRequest.channel_id == channel_id,
                JoinRequest.status == "pending").values(status="held", error_code="configuration_changed"))
            await invalidate(session, self.ctx, channel_id=channel_id, code="configuration_changed")
            session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=channel_id, actor_id=actor_id, action="members.policy_saved", details={}))
            await session.commit()
            return row

    async def requests(self, channel_id, actor_id, offset=0):
        await rights(self.ctx, channel_id, actor_id)
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(JoinRequest).where(JoinRequest.bot_id == self.ctx.bot_id, JoinRequest.channel_id == channel_id)
                .order_by(JoinRequest.created_at.desc(), JoinRequest.id).offset(offset).limit(10))).all())

    async def request(self, request_id, actor_id):
        async with self.ctx.sm() as session:
            row = await session.get(JoinRequest, (self.ctx.bot_id, request_id))
            actions = list((await session.scalars(select(MemberAction).where(MemberAction.bot_id == self.ctx.bot_id,
                MemberAction.request_id == request_id).order_by(MemberAction.created_at).limit(30))).all())
        if row is None:
            raise ContentError("stale")
        await rights(self.ctx, row.channel_id, actor_id)
        return row, actions

    async def decide(self, request_id, actor_id, decision):
        initial, _ = await self.request(request_id, actor_id)
        async with self.ctx.sm() as session:
            channel = await session.get(Channel, (self.ctx.bot_id, initial.channel_id), with_for_update=True)
            if channel is None:
                raise ContentError("stale")
            head = await head_for(session, self.ctx, initial.channel_id, initial.user_id)
            row = await session.get(JoinRequest, (self.ctx.bot_id, request_id), with_for_update=True)
            config = await session.get(MemberConfig, (self.ctx.bot_id, initial.channel_id))
            if row is None or config is None or head.request_id != row.id or row.status not in {"pending", "held"} or utcnow() >= row.expires_at:
                raise ContentError("stale")
            spec = MemberSpec.model_validate(config.spec)
            if decision == "adopt":
                if row.profile.get("query_unsupported"):
                    raise ContentError("unsupported_join_query")
                if not spec.enabled:
                    raise ContentError("member_disabled")
                old_spec = MemberSpec.model_validate(row.spec)
                row.spec, row.config_generation, row.actor_id, row.status, row.error_code = config.spec, config.generation, actor_id, "pending", None
                row.captcha_solved = row.captcha_solved if spec.captcha and old_spec.captcha else not spec.captcha
                row.approve_after = row.requested_at + timedelta(seconds=spec.delay_seconds if spec.mode == "timed" else 0)
                row.expires_at = min(row.expires_at, row.requested_at + timedelta(seconds=spec.expires_seconds))
                row.filter_code = spec.profile.rejects(row.profile, 1)
                row.required_index, row.manual_release = 0, False
                row.invite_epoch += 1
            elif decision == "release":
                if row.status != "pending" or row.config_generation != config.generation or not spec.enabled:
                    raise ContentError("stale")
                row.manual_release = True
                row.actor_id = actor_id
            elif decision == "decline":
                row.actor_id = actor_id
                await invalidate(session, self.ctx, channel_id=channel.channel_id, request_id=row.id, code="manual_decline")
                await action(session, self.ctx, channel, config, kind="decline", key=f"manual-decline:{row.id}", user_id=row.user_id,
                    request=row, payload={"reason": "manual_decline", "generation": row.generation, "manual": True})
            else:
                raise ContentError("member_policy")
            row.next_check = utcnow()
            session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=row.channel_id, actor_id=actor_id,
                action=f"members.{decision}", details={"request_id": row.id}))
            await session.commit()

    async def prepare_bulk(self, channel_id, actor_id, limit=500):
        await rights(self.ctx, channel_id, actor_id)
        if not 1 <= limit <= 5000:
            raise ContentError("limit")
        async with self.ctx.sm() as session:
            await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            config = await session.get(MemberConfig, (self.ctx.bot_id, channel_id))
            if config is None or not MemberSpec.model_validate(config.spec).enabled:
                raise ContentError("member_disabled")
            ids = list((await session.scalars(select(JoinRequest.id).where(JoinRequest.bot_id == self.ctx.bot_id,
                JoinRequest.channel_id == channel_id, JoinRequest.status.in_({"pending", "held"})).order_by(JoinRequest.created_at, JoinRequest.id).limit(limit))).all())
            row = MemberBulk(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=channel_id, actor_id=actor_id,
                config_generation=config.generation, request_ids=ids, expires_at=utcnow() + timedelta(minutes=15))
            session.add(row)
            await session.commit()
            return row

    async def confirm_bulk(self, bulk_id, actor_id):
        async with self.ctx.sm() as session:
            initial = await session.get(MemberBulk, (self.ctx.bot_id, bulk_id))
        if initial is None or initial.actor_id != actor_id:
            raise ContentError("stale")
        await rights(self.ctx, initial.channel_id, actor_id)
        async with self.ctx.sm() as session:
            await session.get(Channel, (self.ctx.bot_id, initial.channel_id), with_for_update=True)
            bulk = await session.get(MemberBulk, (self.ctx.bot_id, bulk_id), with_for_update=True)
            if bulk is None:
                raise ContentError("stale")
            config = await session.get(MemberConfig, (self.ctx.bot_id, initial.channel_id))
            if bulk.status == "queued":
                return bulk
            if config is None or bulk.config_generation != config.generation or bulk.expires_at <= utcnow() or not MemberSpec.model_validate(config.spec).enabled:
                raise ContentError("stale")
            result = {"selected": len(bulk.request_ids), "released": 0, "skipped": 0}
            for request_id in bulk.request_ids:
                row = await session.get(JoinRequest, (self.ctx.bot_id, request_id), with_for_update=True)
                head = await session.get(MemberHead, (self.ctx.bot_id, initial.channel_id, row.user_id)) if row else None
                if row and row.status == "pending" and row.config_generation == config.generation and row.expires_at > utcnow() and head and head.request_id == row.id:
                    row.manual_release, row.next_check, row.actor_id = True, utcnow(), actor_id
                    result["released"] += 1
                else:
                    result["skipped"] += 1
            bulk.status, bulk.result = "queued", result
            session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=bulk.channel_id, actor_id=actor_id,
                action="members.bulk_release", details={"bulk_id": bulk.id, **result}))
            await session.commit()
            return bulk

    async def actions(self, channel_id, actor_id):
        await rights(self.ctx, channel_id, actor_id)
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(MemberAction).where(MemberAction.bot_id == self.ctx.bot_id,
                MemberAction.channel_id == channel_id).order_by(MemberAction.created_at.desc()).limit(30))).all())

    async def retry(self, action_id, actor_id):
        async with self.ctx.sm() as session:
            initial = await session.get(MemberAction, (self.ctx.bot_id, action_id))
        if initial is None:
            raise ContentError("stale")
        await rights(self.ctx, initial.channel_id, actor_id, restrict=initial.kind == "ban")
        async with self.ctx.sm() as session:
            channel = await session.get(Channel, (self.ctx.bot_id, initial.channel_id), with_for_update=True)
            if channel is None:
                raise ContentError("stale")
            head = await head_for(session, self.ctx, initial.channel_id, initial.user_id) if initial.user_id else None
            request = await session.get(JoinRequest, (self.ctx.bot_id, initial.request_id), with_for_update=True) if initial.request_id else None
            config = await session.get(MemberConfig, (self.ctx.bot_id, initial.channel_id))
            row = await session.get(MemberAction, (self.ctx.bot_id, action_id), with_for_update=True)
            if row is None or row.status != "failed" or config is None or (not row.cleanup and config.generation != row.generation):
                raise ContentError("no_safe_retry")
            if request and row.kind != "welcome" and (head is None or head.request_id != request.id or request.status != "pending" or request.expires_at <= utcnow()):
                raise ContentError("stale")
            row.actor_id, row.status, row.error_code = actor_id, "pending", None
            row.operation_id = await outbox.enqueue(session, self.ctx, channel, kind=f"member_{row.kind}",
                dedupe_key=f"member-retry:{row.id}:{uuid.uuid4().hex[:8]}", payload={"action_id": row.id}, member_action_id=row.id)
            session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=row.channel_id, actor_id=actor_id,
                action="members.retry", details={"action_id": row.id}))
            await session.commit()


async def plan_one(ctx):
    if (await ctx.settings.get()).maintenance:
        return False
    async with ctx.sm() as session:
        initial = await session.scalar(select(JoinRequest).where(JoinRequest.bot_id == ctx.bot_id, JoinRequest.status == "pending",
            JoinRequest.next_check <= utcnow()).order_by(JoinRequest.next_check, JoinRequest.id).limit(1))
        if initial is None:
            return False
        channel = await session.get(Channel, (ctx.bot_id, initial.channel_id), with_for_update=True)
        head = await head_for(session, ctx, initial.channel_id, initial.user_id)
        row = await session.get(JoinRequest, (ctx.bot_id, initial.id), with_for_update=True, populate_existing=True)
        config = await session.get(MemberConfig, (ctx.bot_id, initial.channel_id))
        if row.status != "pending" or row.next_check > utcnow():
            return True
        from bots.channelmanager.release import allowed as release_allowed
        if not await release_allowed(ctx, "members", session=session, channel_id=row.channel_id):
            row.status, row.error_code = "held", "release_stage"
            await session.commit()
            return True
        if config is None or channel.status != "active" or row.config_generation != config.generation or not MemberSpec.model_validate(config.spec).enabled:
            row.status, row.error_code = "held", "configuration_changed"
        elif head.request_id != row.id:
            row.status, row.error_code = "superseded", "new_request"
        else:
            spec = MemberSpec.model_validate(row.spec)
            from bots.channelmanager.billing import limits_for
            from bots.channelmanager.invitations import credit_request, ensure, satisfied
            from bots.channelmanager.senders import allowed
            if not await allowed(ctx, source_id := row.channel_id, session=session) or spec.invite_threshold > (await limits_for(ctx, source_id, session=session)).invite_threshold:
                row.status, row.error_code = "held", "sender_or_plan_changed"
                await session.commit()
                return True
            waiting = await session.scalar(select(MemberAction.id).join(Operation, (Operation.bot_id == MemberAction.bot_id) &
                (Operation.id == MemberAction.operation_id)).where(MemberAction.bot_id == ctx.bot_id, MemberAction.request_id == row.id,
                MemberAction.kind.in_({"approve", "decline", "ban"}), Operation.status.in_({"pending", "running"})).limit(1))
            if not waiting:
                reason = row.filter_code or ("captcha_attempts" if row.captcha_attempts >= spec.captcha_attempts and not row.captcha_solved else None)
                reason = reason or ("expired" if utcnow() >= row.expires_at else None)
                if reason:
                    if row.filter_code and spec.profile.outcome == "ban":
                        await queue_ban(session, ctx, channel, config, row.user_id, f"reject-ban:{row.id}", code=reason, request=row)
                    else:
                        await action(session, ctx, channel, config, kind="decline", key=f"decline:{row.id}", user_id=row.user_id,
                            request=row, payload={"reason": reason, "generation": row.generation})
                else:
                    if not spec.captcha and not spec.required:
                        await credit_request(session, ctx, row)
                    if spec.invite_threshold:
                        await ensure(session, ctx, channel, row)
                    await action(session, ctx, channel, config, kind="contact", key=f"contact:{row.id}:{config.generation}", user_id=row.user_id,
                        request=row, payload={"generation": row.generation})
                    if row.captcha_solved and row.required_index == len(spec.required) and satisfied(row, spec) and (spec.mode != "manual" or row.manual_release) and utcnow() >= row.approve_after:
                        await action(session, ctx, channel, config, kind="approve", key=f"approve:{row.id}:{config.generation}", user_id=row.user_id,
                            request=row, payload={"generation": row.generation})
            row.next_check = utcnow() + timedelta(seconds=30)
            if row.expires_at > utcnow():
                row.next_check = min(row.next_check, row.expires_at)
            if row.approve_after > utcnow():
                row.next_check = min(row.next_check, row.approve_after)
        await session.commit()
        return True
