"""Scoped automation configuration, durable source collection and versioned planning."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message
from sqlalchemy import BigInteger, cast, func, select, update

from bots.channelmanager import outbox
from bots.channelmanager.auto_content import (
    RouteSpec,
    RuleSpec,
    SourceItem,
    from_source,
    strip_affixes,
    transform,
)
from bots.channelmanager.content import ContentError, PostSpec, validation_code
from bots.channelmanager.models import (
    AutoAction,
    AutomationControl,
    AutoOutput,
    AutoPart,
    AutoRule,
    AutoSnapshot,
    AutoSource,
    Channel,
    Delivery,
    Event,
    ForwardRoute,
    MemberAction,
    Operation,
    Post,
    PostVersion,
)
from bots.channelmanager.permissions import AccessDenied, bot_post_rights, operator_rights
from core.db.base import upsert, utcnow
from core.db.models import Bot as BotRecord
from core.sdk.context import BotContext

AUTO_KINDS = frozenset({"auto_edit", "auto_copy", "auto_forward", "auto_sticker", "auto_delete", "auto_reminder"})
CLEANUP = frozenset({"auto_delete", "auto_reminder"})


async def source_rights(ctx: BotContext, channel_id: int, user_id: int) -> None:
    rights = await operator_rights(ctx, channel_id, user_id)
    if not rights["can_edit_messages"]:
        raise AccessDenied("automation_right")
    channel = await ctx.extras["channelmanager"].get(channel_id)
    if channel is None or channel.status != "active":
        raise AccessDenied("channel_inactive")


async def destination_rights(ctx: BotContext, destination_id: int, user_id: int, *, action="send") -> str:
    try:
        chat = await ctx.bot.get_chat(destination_id)
        if chat.type == "channel":
            await operator_rights(ctx, destination_id, user_id)
            await bot_post_rights(ctx, destination_id, "edit" if action == "edit" else "delete" if action == "delete" else "publish")
            return "channel"
        if chat.type not in {"group", "supergroup"}:
            raise AccessDenied("destination_type")
        actor = await ctx.bot.get_chat_member(destination_id, user_id)
        bot = await ctx.bot.get_chat_member(destination_id, ctx.bot_id)
        if actor.status not in {"creator", "administrator"} or bot.status != "administrator":
            raise AccessDenied("group_admin")
        return "group"
    except TelegramAPIError as exc:
        raise AccessDenied("destination_unavailable") from exc


class AutomationService:
    def __init__(self, ctx: BotContext):
        self.ctx = ctx

    async def rules(self, channel_id: int, user_id: int) -> list[AutoRule]:
        await source_rights(self.ctx, channel_id, user_id)
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(AutoRule).where(AutoRule.bot_id == self.ctx.bot_id,
                AutoRule.channel_id == channel_id).order_by(AutoRule.priority, AutoRule.id).limit(100))).all())

    async def routes(self, channel_id: int, user_id: int) -> list[ForwardRoute]:
        await source_rights(self.ctx, channel_id, user_id)
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(ForwardRoute).where(ForwardRoute.bot_id == self.ctx.bot_id,
                ForwardRoute.channel_id == channel_id).order_by(ForwardRoute.name).limit(100))).all())

    async def get(self, kind: str, resource_id: str, user_id: int):
        model = AutoRule if kind == "rule" else ForwardRoute
        async with self.ctx.sm() as session:
            row: Any = await session.get(model, (self.ctx.bot_id, resource_id))
        if row is None:
            raise ContentError("stale")
        await source_rights(self.ctx, row.channel_id, user_id)
        return row

    async def changed(self, session, channel_id: int, actor_id: int, action: str) -> None:
        control = await session.get(AutomationControl, (self.ctx.bot_id, channel_id), with_for_update=True)
        if control is None:
            control = AutomationControl(bot_id=self.ctx.bot_id, channel_id=channel_id)
            session.add(control)
        else:
            control.generation += 1
        ids = (await session.scalars(select(Operation.id).where(Operation.bot_id == self.ctx.bot_id, Operation.channel_id == channel_id,
            Operation.kind.in_(AUTO_KINDS - CLEANUP), Operation.status.in_({"pending", "running"}), Operation.dispatched.is_(False))
            .with_for_update(skip_locked=True))).all()
        await session.execute(update(Operation).where(Operation.bot_id == self.ctx.bot_id, Operation.id.in_(ids)).values(
                status="cancelled", error_code="automation_changed", updated_at=utcnow()))
        session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=channel_id, actor_id=actor_id, action=action, details={}))

    async def save_rule(self, channel_id: int, user_id: int, name: str, spec: RuleSpec, *, priority=100,
                        active=False, resource_id: str | None = None, generation: int | None = None) -> AutoRule:
        await source_rights(self.ctx, channel_id, user_id)
        if not 1 <= len(name.strip()) <= 64 or not 0 <= priority <= 10000:
            raise ContentError("name")
        for ref in (spec.attachment, spec.separator):
            if ref and ref.bot_id != self.ctx.bot_id:
                raise ContentError("media")
        await self.ctx.extras["posts"].validate_buttons(PostSpec(body={"text": "validation"}, buttons=spec.buttons), user_id)
        if spec.delete_after_seconds:
            rights = await operator_rights(self.ctx, channel_id, user_id)
            bot = await self.ctx.bot.get_chat_member(channel_id, self.ctx.bot_id)
            if not rights["can_delete_messages"] or not getattr(bot, "can_delete_messages", False):
                raise AccessDenied("source_deletion_right")
        async with self.ctx.sm() as session:
            await session.get(BotRecord, self.ctx.bot_id, with_for_update=True)
            await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            row = await session.get(AutoRule, (self.ctx.bot_id, resource_id), with_for_update=True) if resource_id else None
            if resource_id and (row is None or row.channel_id != channel_id or row.generation != generation):
                raise ContentError("stale")
            duplicate = await session.scalar(select(AutoRule.id).where(AutoRule.bot_id == self.ctx.bot_id,
                AutoRule.channel_id == channel_id, AutoRule.name == name.strip()))
            if duplicate and (row is None or duplicate != row.id):
                raise ContentError("name")
            if row is None:
                count = await session.scalar(select(func.count()).select_from(AutoRule).where(AutoRule.bot_id == self.ctx.bot_id,
                    AutoRule.channel_id == channel_id))
                from bots.channelmanager.billing import limits_for
                if int(count or 0) >= (await limits_for(self.ctx, channel_id, session=session)).rules:
                    raise ContentError("limit")
                row = AutoRule(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=channel_id, creator_id=user_id,
                    name=name.strip(), spec=spec.model_dump(mode="json"))
                session.add(row)
            else:
                row.generation += 1
            row.name, row.spec, row.priority, row.active = name.strip(), spec.model_dump(mode="json"), priority, active
            # The current editor adopts authorization for newly queued automation.
            row.creator_id = user_id
            row.active_since = utcnow()
            await self.changed(session, channel_id, user_id, "automation.rule_saved")
            await session.commit()
            return row

    async def save_route(self, channel_id: int, user_id: int, name: str, destination_id: int, spec: RouteSpec, *,
                         active=False, resource_id: str | None = None, generation: int | None = None) -> ForwardRoute:
        await source_rights(self.ctx, channel_id, user_id)
        destination_type = await destination_rights(self.ctx, destination_id, user_id)
        if destination_id == channel_id:
            raise ContentError("route_cycle")
        if not 1 <= len(name.strip()) <= 64:
            raise ContentError("name")
        async with self.ctx.sm() as session:
            await session.get(BotRecord, self.ctx.bot_id, with_for_update=True)
            await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            row = await session.get(ForwardRoute, (self.ctx.bot_id, resource_id), with_for_update=True) if resource_id else None
            if resource_id and (row is None or row.channel_id != channel_id or row.generation != generation):
                raise ContentError("stale")
            duplicate = await session.scalar(select(ForwardRoute.id).where(ForwardRoute.bot_id == self.ctx.bot_id,
                ForwardRoute.channel_id == channel_id, ForwardRoute.name == name.strip()))
            if duplicate and (row is None or duplicate != row.id):
                raise ContentError("name")
            if active and destination_type == "channel":
                graph: dict[int, list[int]] = {}
                for edge in (await session.scalars(select(ForwardRoute).where(ForwardRoute.bot_id == self.ctx.bot_id,
                    ForwardRoute.active.is_(True), ForwardRoute.destination_type == "channel"))).all():
                    if row is None or row.id != edge.id:
                        graph.setdefault(edge.channel_id, []).append(edge.destination_id)
                stack, seen = [destination_id], set()
                while stack:
                    node = stack.pop()
                    if node == channel_id:
                        raise ContentError("route_cycle")
                    if node not in seen:
                        seen.add(node)
                        stack.extend(graph.get(node, []))
            if row is None:
                count = await session.scalar(select(func.count()).select_from(ForwardRoute).where(ForwardRoute.bot_id == self.ctx.bot_id,
                    ForwardRoute.channel_id == channel_id))
                from bots.channelmanager.billing import limits_for
                if int(count or 0) >= (await limits_for(self.ctx, channel_id, session=session)).routes:
                    raise ContentError("limit")
                row = ForwardRoute(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=channel_id,
                    creator_id=user_id, name=name.strip(), destination_id=destination_id, destination_type=destination_type, spec=spec.model_dump(mode="json"))
                session.add(row)
            else:
                row.generation += 1
            row.name, row.destination_id, row.destination_type, row.spec, row.active = name.strip(), destination_id, destination_type, spec.model_dump(mode="json"), active
            row.creator_id = user_id
            row.active_since = utcnow()
            await self.changed(session, channel_id, user_id, "automation.route_saved")
            await session.commit()
            return row

    async def stop(self, kind: str, resource_id: str, user_id: int, generation: int) -> None:
        initial = await self.get(kind, resource_id, user_id)
        async with self.ctx.sm() as session:
            await session.get(BotRecord, self.ctx.bot_id, with_for_update=True)
            await session.get(Channel, (self.ctx.bot_id, initial.channel_id), with_for_update=True)
            model = AutoRule if kind == "rule" else ForwardRoute
            row: Any = await session.get(model, (self.ctx.bot_id, resource_id), with_for_update=True)
            if row is None or row.generation != generation:
                raise ContentError("stale")
            row.active, row.generation = False, row.generation + 1
            await self.changed(session, initial.channel_id, user_id, "automation.disabled")
            await session.commit()

    async def reports(self, channel_id: int, user_id: int, offset=0) -> list[AutoSource]:
        await source_rights(self.ctx, channel_id, user_id)
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(AutoSource).where(AutoSource.bot_id == self.ctx.bot_id,
                AutoSource.channel_id == channel_id).order_by(AutoSource.created_at.desc(), AutoSource.id).offset(offset).limit(10))).all())

    async def report(self, source_id: str, user_id: int):
        async with self.ctx.sm() as session:
            source = await session.get(AutoSource, (self.ctx.bot_id, source_id))
            if source is None:
                raise ContentError("stale")
            actions = list((await session.scalars(select(AutoAction).where(AutoAction.bot_id == self.ctx.bot_id,
                AutoAction.source_id == source_id).order_by(AutoAction.version.desc(), AutoAction.created_at).limit(50))).all())
            snapshot = await session.get(AutoSnapshot, (self.ctx.bot_id, source.id, source.generation))
        await source_rights(self.ctx, source.channel_id, user_id)
        return source, snapshot, actions

    async def retry(self, action_id: str, user_id: int) -> None:
        async with self.ctx.sm() as session:
            initial = await session.get(AutoAction, (self.ctx.bot_id, action_id))
        if initial is None:
            raise ContentError("stale")
        await source_rights(self.ctx, initial.channel_id, user_id)
        if initial.kind in {"copy", "forward"}:
            await destination_rights(self.ctx, initial.destination_id, user_id, action="edit" if initial.payload.get("prior_ids") else "send")
        if initial.kind == "delete" and not initial.payload.get("own") and not (
                await operator_rights(self.ctx, initial.channel_id, user_id))["can_delete_messages"]:
            raise AccessDenied("source_deletion_right")
        async with self.ctx.sm() as session:
            source = await session.get(AutoSource, (self.ctx.bot_id, initial.source_id), with_for_update=True)
            action = await session.get(AutoAction, (self.ctx.bot_id, action_id), with_for_update=True)
            control = await session.get(AutomationControl, (self.ctx.bot_id, initial.channel_id))
            if source is None or action is None or action.status != "failed" or control is None:
                raise ContentError("no_safe_retry")
            if action.kind not in {"delete", "reminder"} and (source.generation != action.version or control.generation != action.control_generation):
                raise ContentError("stale")
            channel = await session.get(Channel, (self.ctx.bot_id, action.channel_id))
            assert channel is not None
            target = None
            if action.payload.get("mirror_post"):
                target = await session.scalar(select(Delivery).where(Delivery.bot_id == self.ctx.bot_id, Delivery.post_id == action.payload["mirror_post"]))
            action.actor_id, action.status, action.error_code = user_id, "pending", None
            action.operation_id = await outbox.enqueue(session, self.ctx, channel, kind=f"auto_{action.kind}",
                dedupe_key=f"auto-retry:{action.id}:{uuid.uuid4().hex[:12]}", payload={"action_id": action.id},
                automation_id=action.id, delivery_id=target.id if target else None)
            session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=channel.channel_id, actor_id=user_id,
                action="automation.retry", details={"action_id": action.id}))
            await session.commit()


async def managed_message(session, ctx: BotContext, message: Message, item: SourceItem) -> bool:
    if (message.from_user and message.from_user.is_bot) or message.via_bot:
        return True
    if await session.get(AutoOutput, (ctx.bot_id, message.chat.id, message.message_id)):
        return True
    member_log = [MemberAction.bot_id == ctx.bot_id, MemberAction.kind == "log",
        cast(MemberAction.payload["destination"].as_string(), BigInteger) == message.chat.id]
    if await session.scalar(select(MemberAction.id).where(*member_log, MemberAction.remote_id == message.message_id).limit(1)):
        return True
    inflight_logs = (await session.scalars(select(MemberAction).join(Operation,
        (Operation.bot_id == MemberAction.bot_id) & (Operation.member_action_id == MemberAction.id)).where(*member_log,
            Operation.status == "running", Operation.dispatched.is_(True)).limit(100))).all()
    if any(effect.payload.get("text") == message.text for effect in inflight_logs):
        return True
    origin = message.forward_origin
    origin_chat, origin_id = getattr(origin, "chat", None), getattr(origin, "message_id", None)
    if origin_chat and origin_id and await session.get(AutoOutput, (ctx.bot_id, origin_chat.id, origin_id)):
        return True
    source_key = f"album:{message.media_group_id}" if message.media_group_id else f"message:{message.message_id}"
    source_id = await session.scalar(select(AutoSource.id).where(AutoSource.bot_id == ctx.bot_id,
        AutoSource.channel_id == message.chat.id, AutoSource.source_key == source_key))
    if source_id:
        effects = (await session.scalars(select(AutoAction).where(AutoAction.bot_id == ctx.bot_id,
            AutoAction.source_id == source_id, AutoAction.kind == "edit", AutoAction.status == "succeeded")
            .order_by(AutoAction.version.desc()).limit(50))).all()
        for effect in effects:
            for raw_item in effect.payload.get("items", []):
                candidate = SourceItem.model_validate(raw_item)
                if candidate.message_id == item.message_id and candidate.fingerprint() == item.fingerprint():
                    return True
    target = await session.scalar(select(Delivery).where(Delivery.bot_id == ctx.bot_id, Delivery.channel_id == message.chat.id,
        Delivery.message_id == message.message_id).limit(1))
    if target:
        post = await session.get(Post, (ctx.bot_id, target.post_id))
        if post and not (post.source_key or "").startswith("auto:"):
            return True
        if post:
            version = await session.get(PostVersion, (ctx.bot_id, post.id, post.version))
            if version:
                spec = PostSpec.model_validate(version.spec)
                text, entities = spec.render()
                expected = SourceItem.model_validate({**item.model_dump(mode="json"), "kind": spec.kind,
                    "protected": spec.protected,
                    "body": {"text": text, "entities": [e.model_dump(mode="json") for e in entities]}})
                if item.kind == spec.kind and item.file_id == spec.file_id and item.fingerprint(media=False) == expected.fingerprint(media=False):
                    return True
    # Suppress output events that beat the RPC result transaction. Matching is
    # deliberately conservative; ambiguous identical manual messages are not rerouted.
    candidates = (await session.scalars(select(AutoAction).join(Operation,
        (Operation.bot_id == AutoAction.bot_id) & (Operation.automation_id == AutoAction.id)).where(
            AutoAction.bot_id == ctx.bot_id, AutoAction.destination_id == message.chat.id,
            Operation.status == "running", Operation.dispatched.is_(True)).limit(100))).all()
    for action in candidates:
        for expected in action.payload.get("items", []):
            candidate = SourceItem.model_validate(expected)
            if candidate.fingerprint(privacy=action.kind == "edit") == item.fingerprint(privacy=action.kind == "edit") and (action.kind != "edit" or item.message_id == candidate.message_id):
                return True
    # Ordinary composer publications use the same source-ingress protection.
    pending = (await session.execute(select(PostVersion.spec).join(Delivery,
        (Delivery.bot_id == PostVersion.bot_id) & (Delivery.post_id == PostVersion.post_id) & (Delivery.version == PostVersion.number)).join(Operation,
            (Operation.bot_id == Delivery.bot_id) & (Operation.delivery_id == Delivery.id)).where(Delivery.bot_id == ctx.bot_id,
                Delivery.channel_id == message.chat.id, Operation.kind.in_({"publish", "edit"}), Operation.status == "running",
                Operation.dispatched.is_(True)).limit(100))).scalars().all()
    for raw in pending:
        spec = PostSpec.model_validate(raw)
        text, entities = spec.render()
        candidate = SourceItem.model_validate({**item.model_dump(mode="json"), "kind": spec.kind,
            "body": {"text": text, "entities": [e.model_dump(mode="json") for e in entities]}})
        if candidate.fingerprint(media=False, privacy=False) == item.fingerprint(media=False, privacy=False):
            return True
    return False


async def ingest(session, ctx: BotContext, message: Message, update_id: int, *, edited=False, received_at=None, collection_seconds=2) -> None:
    channel = await session.get(Channel, (ctx.bot_id, message.chat.id))
    if channel is None:
        return
    item = from_source(message)
    if await managed_message(session, ctx, message, item):
        return
    key = f"album:{message.media_group_id}" if message.media_group_id else f"message:{message.message_id}"
    await session.execute(upsert(session, AutoSource).values(bot_id=ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=channel.channel_id,
        source_key=key, album=bool(message.media_group_id), provenance=[channel.channel_id]).on_conflict_do_nothing(
            index_elements=["bot_id", "channel_id", "source_key"]))
    source = await session.scalar(select(AutoSource).where(AutoSource.bot_id == ctx.bot_id,
        AutoSource.channel_id == channel.channel_id, AutoSource.source_key == key).with_for_update())
    assert source is not None
    part = await session.get(AutoPart, (ctx.bot_id, source.id, message.message_id))
    observed = datetime.fromtimestamp(message.edit_date, UTC) if message.edit_date is not None else message.date
    if part and (observed, update_id) <= (part.observed_at, part.update_id):
        return
    fingerprint = item.fingerprint()
    if part and fingerprint == part.fingerprint:
        part.observed_at, part.update_id = observed, update_id
        return
    has_previous = await session.scalar(select(AutoSnapshot.number).where(AutoSnapshot.bot_id == ctx.bot_id,
        AutoSnapshot.source_id == source.id).limit(1))
    if has_previous is not None:
        source.generation += 1
        await session.execute(update(Operation).where(Operation.bot_id == ctx.bot_id, Operation.automation_id.in_(
            select(AutoAction.id).where(AutoAction.bot_id == ctx.bot_id, AutoAction.source_id == source.id)),
            Operation.kind.in_(AUTO_KINDS - CLEANUP), Operation.status.in_({"pending", "running"}), Operation.dispatched.is_(False)).values(
                status="cancelled", error_code="source_changed", updated_at=utcnow()))
    if part:
        inflight = await session.scalar(select(AutoAction).join(Operation, (Operation.bot_id == AutoAction.bot_id) &
            (Operation.automation_id == AutoAction.id)).where(AutoAction.bot_id == ctx.bot_id, AutoAction.source_id == source.id,
                AutoAction.kind == "edit", Operation.status == "running", Operation.dispatched.is_(True)).order_by(AutoAction.version.desc()).limit(1))
        saved = inflight.payload.get("affixes", {}) if inflight else part.affixes
        item = strip_affixes(item, saved)
        part.body, part.fingerprint, part.observed_at, part.update_id = item.model_dump(mode="json"), fingerprint, observed, update_id
        part.received_at = received_at or utcnow()
    else:
        session.add(AutoPart(bot_id=ctx.bot_id, source_id=source.id, message_id=item.message_id,
            body=item.model_dump(mode="json"), fingerprint=fingerprint, observed_at=observed, update_id=update_id, received_at=received_at or utcnow()))
    source.edited = source.edited or edited
    source.status, source.error_code = "collecting", None
    delay = collection_seconds if source.album else 0
    source.available_at = min(utcnow() + timedelta(seconds=delay), source.created_at + timedelta(seconds=30)) if source.album else utcnow()


async def enqueue_action(session, ctx: BotContext, source: AutoSource, control: AutomationControl, *, key: str,
                         kind: str, actor: int, destination: int, payload: dict, rule: AutoRule | None = None,
                         route: ForwardRoute | None = None, status="pending", code=None, delivery_id=None, run_at=None,
                         version: int | None = None) -> AutoAction:
    version = source.generation if version is None else version
    previous = await session.scalar(select(AutoAction).where(AutoAction.bot_id == ctx.bot_id, AutoAction.source_id == source.id,
        AutoAction.version == version, AutoAction.action_key == key))
    if previous:
        return previous
    action = AutoAction(bot_id=ctx.bot_id, id=uuid.uuid4().hex, channel_id=source.channel_id, source_id=source.id,
        version=version, action_key=key, kind=kind, actor_id=actor, destination_id=destination,
        rule_id=rule.id if rule else None, route_id=route.id if route else None, control_generation=control.generation,
        payload=payload, status=status, error_code=code, remote_ids=payload.get("prior_ids") or payload.get("known_ids", []))
    session.add(action)
    await session.flush()
    if status == "pending":
        channel = await session.get(Channel, (ctx.bot_id, source.channel_id))
        assert channel is not None
        action.operation_id = await outbox.enqueue(session, ctx, channel, kind=f"auto_{kind}",
            dedupe_key=f"auto:{action.id}", payload={"action_id": action.id}, run_at=run_at,
            automation_id=action.id, delivery_id=delivery_id)
    return action


async def mirror(session, ctx: BotContext, source: AutoSource, original: SourceItem, spec: PostSpec, actor: int):
    post = await session.get(Post, (ctx.bot_id, source.mirror_post_id), with_for_update=True) if source.mirror_post_id else None
    if post is None:
        post = Post(bot_id=ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=source.channel_id, creator_id=actor,
            target_ids=[source.channel_id], source_key=f"auto:{source.id}")
        session.add(post)
        await session.flush()
        session.add(PostVersion(bot_id=ctx.bot_id, post_id=post.id, number=1, spec=original.spec(ctx.bot_id).model_dump(mode="json")))
        await session.flush()
        target = Delivery(bot_id=ctx.bot_id, id=uuid.uuid4().hex, post_id=post.id, channel_id=source.channel_id,
            version=1, generation=1, actor_id=actor, state="sent", message_id=original.message_id, sent_at=original.sent_at)
        session.add(target)
        source.mirror_post_id = post.id
        await session.flush()
    else:
        target = await session.scalar(select(Delivery).where(Delivery.bot_id == ctx.bot_id, Delivery.post_id == post.id).with_for_update())
        assert target is not None
    post.version, post.generation = post.version + 1, post.generation + 1
    session.add(PostVersion(bot_id=ctx.bot_id, post_id=post.id, number=post.version, spec=spec.model_dump(mode="json")))
    target.generation, target.edit_status = post.generation, "pending"
    return post, target


async def plan_one(ctx: BotContext) -> bool:
    if (await ctx.settings.get()).maintenance:
        return False
    async with ctx.sm() as session:
        if not await session.scalar(select(BotRecord.active).where(BotRecord.id == ctx.bot_id)):
            return False
        source = await session.scalar(select(AutoSource).where(AutoSource.bot_id == ctx.bot_id,
            AutoSource.status == "collecting", AutoSource.available_at <= utcnow()).order_by(AutoSource.available_at, AutoSource.id)
            .limit(1).with_for_update(skip_locked=True))
        if source is None:
            return False
        from bots.channelmanager.release import allowed as release_allowed
        if not await release_allowed(ctx, "automation", session=session, channel_id=source.channel_id):
            source.status, source.error_code = "held", "release_stage"
            await session.commit()
            return True
        busy = await session.scalar(select(Operation.id).join(AutoAction, (AutoAction.bot_id == Operation.bot_id) &
            (AutoAction.id == Operation.automation_id)).where(AutoAction.bot_id == ctx.bot_id, AutoAction.source_id == source.id,
                Operation.status == "running", Operation.dispatched.is_(True)).limit(1))
        if busy:
            source.available_at = utcnow() + timedelta(seconds=1)
            await session.commit()
            return True
        parts = list((await session.scalars(select(AutoPart).where(AutoPart.bot_id == ctx.bot_id,
            AutoPart.source_id == source.id).order_by(AutoPart.message_id))).all())
        original = [SourceItem.model_validate(part.body) for part in parts]
        event_received = (max if source.edited else min)((p.received_at for p in parts), default=source.created_at)
        control = await session.get(AutomationControl, (ctx.bot_id, source.channel_id))
        channel = await session.get(Channel, (ctx.bot_id, source.channel_id))
        for item in original:
            output = await session.get(AutoOutput, (ctx.bot_id, source.channel_id, item.message_id))
            target = await session.scalar(select(Delivery).where(Delivery.bot_id == ctx.bot_id, Delivery.channel_id == source.channel_id,
                Delivery.message_id == item.message_id).limit(1))
            post = await session.get(Post, (ctx.bot_id, target.post_id)) if target else None
            if output or (post and not (post.source_key or "").startswith("auto:")):
                source.status, source.error_code = "ignored", "managed_output"
                await session.commit()
                return True
        if not original or (source.album and not 2 <= len(original) <= 10):
            source.status, source.error_code = "held", "album_incomplete"
            await session.commit()
            return True
        if channel is None or channel.status != "active" or control is None:
            source.status, source.error_code = "ignored", "automation_inactive"
            await session.commit()
            return True
        if source.album and any(item.kind not in {"photo", "video"} for item in original):
            source.status, source.error_code = "held", "unsupported_album"
            await session.commit()
            return True
        previous_actions = list((await session.scalars(select(AutoAction).where(AutoAction.bot_id == ctx.bot_id,
            AutoAction.source_id == source.id).order_by(AutoAction.version.desc()))).all())
        for action in previous_actions:
            previous_op = await session.get(Operation, (ctx.bot_id, action.operation_id)) if action.operation_id else None
            if previous_op and action.status == "pending" and previous_op.status in {"uncertain", "failed", "cancelled"}:
                action.status, action.error_code = previous_op.status, previous_op.error_code
        if source.album and any(a.remote_ids and a.kind in {"copy", "forward"} for a in previous_actions):
            old_snapshot = await session.get(AutoSnapshot, (ctx.bot_id, source.id, previous_actions[0].version))
            if old_snapshot and [item["message_id"] for item in old_snapshot.original] != [item.message_id for item in original]:
                source.status, source.error_code = "held", "album_layout_changed"
                await session.commit()
                return True
        rules = list((await session.scalars(select(AutoRule).where(AutoRule.bot_id == ctx.bot_id,
            AutoRule.channel_id == source.channel_id, AutoRule.active.is_(True)).order_by(AutoRule.priority, AutoRule.id))).all())
        from bots.channelmanager.billing import limits_for
        from bots.channelmanager.senders import allowed
        if not await allowed(ctx, source.channel_id, session=session):
            source.status, source.error_code = "held", "sender_changed"
            await session.commit()
            return True
        limits = await limits_for(ctx, source.channel_id, session=session)
        rules = rules[:limits.rules]
        selected, spec = None, None
        warnings, metadata, transformed = [], {}, original
        transform_error = None
        try:
            for rule in rules:
                if event_received < rule.active_since:
                    continue
                candidate = RuleSpec.model_validate(rule.spec)
                if candidate.filters.matches(original, album=source.album) and (not source.edited or candidate.on_edits):
                    selected, spec = rule, candidate
                    transformed, metadata, warnings = transform(original, spec, ctx.bot_id, album=source.album)
                    break
        except ValueError as exc:
            transform_error = validation_code(exc, "invalid_content")
            warnings.append(f"transform:{transform_error}")
        snapshot = AutoSnapshot(bot_id=ctx.bot_id, source_id=source.id, number=source.generation,
            original=[item.model_dump(mode="json") for item in original], transformed=[item.model_dump(mode="json") for item in transformed], warnings=warnings)
        session.add(snapshot)
        await session.flush()
        routes = list((await session.scalars(select(ForwardRoute).where(ForwardRoute.bot_id == ctx.bot_id,
            ForwardRoute.channel_id == source.channel_id, ForwardRoute.active.is_(True)).order_by(ForwardRoute.id))).all())
        routes = routes[:limits.routes]
        originals: list[AutoAction] = []
        transformed_forwards: list[AutoAction] = []
        for route in routes:
            if event_received < route.active_since:
                continue
            route_spec = RouteSpec.model_validate(route.spec)
            try:
                if not route_spec.filters.matches(original, album=source.album):
                    continue
                history = [a for a in previous_actions if a.route_id == route.id and a.destination_id == route.destination_id
                    and a.kind in {"copy", "forward"}]
                old = next((a for a in history if a.remote_ids), None)
                old_group = sorted((a for a in history if old and a.version == old.version), key=lambda a: a.payload.get("index", 0))
                prior_ids = [remote_id for a in old_group for remote_id in a.remote_ids]
                publication_mode = old.payload.get("publication_mode", old.kind) if old else route_spec.mode
                state, code = "pending", None
                if any(item.protected for item in original):
                    state, code = "failed", "protected_source"
                elif route.destination_id in source.provenance or len(source.provenance) > route_spec.max_hops:
                    state, code = "held", "provenance_limit"
                elif any(a.status == "uncertain" for a in history):
                    state, code = "held", "previous_delivery_uncertain"
                elif prior_ids and not route_spec.propagate_edits:
                    state, code = "skipped", "edit_propagation_off"
                elif prior_ids and publication_mode != route_spec.mode:
                    state, code = "held", "route_mode_changed"
                elif prior_ids and len(prior_ids) != len(original):
                    state, code = "held", "album_layout_changed"
                elif route_spec.content == "transformed" and transform_error:
                    state, code = "failed", "transformation_failed"
                items = transformed if route_spec.content == "transformed" else original
                destination = await session.get(Channel, (ctx.bot_id, route.destination_id)) if route.destination_type == "channel" else None
                editing = bool(prior_ids and route_spec.propagate_edits and len(prior_ids) == len(items))
                groups = [[i] for i in items] if editing else [items]
                for index, group in enumerate(groups):
                    action = await enqueue_action(session, ctx, source, control, key=f"route:{route.id}:{index}", kind=route_spec.mode,
                        actor=route.creator_id, destination=route.destination_id, route=route, status=state, code=code,
                        payload={"items": [i.model_dump(mode="json") for i in group], "content": route_spec.content,
                            "prior_ids": [prior_ids[index]] if editing else [], "known_ids": [] if editing else prior_ids, "index": index,
                            "publication_mode": publication_mode,
                            "publisher_id": old.payload.get("publisher_id", old.actor_id) if old else route.creator_id,
                            "dependencies": [], "destination_type": route.destination_type, "album": source.album,
                            "destination_generation": destination.generation if destination else None,
                            "path": [*source.provenance, route.destination_id], "max_hops": route_spec.max_hops,
                            "route_generation": route.generation})
                    if action.status == "pending" and action.kind == "forward":
                        (originals if route_spec.content == "original" else transformed_forwards).append(action)
            except ValueError:
                await enqueue_action(session, ctx, source, control, key=f"route:{route.id}", kind=route_spec.mode,
                    actor=route.creator_id, destination=route.destination_id, route=route, status="failed", code="invalid_route_content", payload={})
        edits = []
        if selected and spec:
            for index, item in enumerate(transformed):
                if source.album and item.body == original[index].body and spec.delete_after_seconds is None:
                    continue
                content = item.spec(ctx.bot_id)
                if not source.album:
                    content = PostSpec.model_validate({**content.model_dump(mode="json"), "reactions": spec.reactions})
                payload = {"items": [item.model_dump(mode="json")], "spec": content.model_dump(mode="json"), "album": source.album,
                    "dependencies": [a.id for a in originals], "rule_generation": selected.generation,
                    "affixes": metadata.get(item.message_id, {}), "index": index,
                    "delete_after_seconds": spec.delete_after_seconds, "sent_at": original[index].sent_at.isoformat(), "own": False}
                target_id = None
                if not source.album and not transform_error:
                    post, target = await mirror(session, ctx, source, original[0], content, selected.creator_id)
                    payload.update(mirror_post=post.id, mirror_version=post.version, mirror_generation=post.generation)
                    target_id = target.id
                action = await enqueue_action(session, ctx, source, control, key=f"edit:{item.message_id}", kind="edit", actor=selected.creator_id,
                    destination=source.channel_id, rule=selected, payload=payload, delivery_id=target_id,
                    status="failed" if transform_error else "pending", code="transformation_failed" if transform_error else None)
                edits.append(action)
            for action in transformed_forwards:
                action.payload = {**action.payload, "dependencies": [a.id for a in edits], "require_success": True}
            if spec.separator and not source.album and not any(a.kind == "sticker" and a.status in {"succeeded", "uncertain"} for a in previous_actions):
                await enqueue_action(session, ctx, source, control, key="separator", kind="sticker", actor=selected.creator_id,
                    destination=source.channel_id, rule=selected, payload={"reference": spec.separator.model_dump(mode="json"),
                        "dependencies": [a.id for a in edits], "require_success": True, "rule_generation": selected.generation,
                        "delete_after_seconds": spec.delete_after_seconds, "own": True})
        source.status, source.error_code = "planned", transform_error
        actions_count = await session.scalar(select(func.count()).select_from(AutoAction).where(AutoAction.bot_id == ctx.bot_id,
            AutoAction.source_id == source.id, AutoAction.version == source.generation))
        if not actions_count:
            source.status, source.error_code = "ignored", "unsupported_media" if any(i.kind == "unsupported" for i in original) else "filters_unmatched"
        session.add(Event(bot_id=ctx.bot_id, id=uuid.uuid4().hex, channel_id=source.channel_id, actor_id=None,
            action="automation.source_planned", details={"source_id": source.id, "version": source.generation, "rule": selected.id if selected else None}))
        await session.commit()
        return True
