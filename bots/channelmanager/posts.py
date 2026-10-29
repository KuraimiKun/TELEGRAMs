"""Durable post versions, schedules and independently managed target deliveries."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bots.channelmanager import outbox
from bots.channelmanager.content import ContentError, PostSpec, TextBody, utf16len
from bots.channelmanager.models import (
    CalendarReservation,
    Channel,
    ChannelStyle,
    Delivery,
    Entitlement,
    Event,
    Operation,
    Post,
    PostSchedule,
    PostVersion,
    Recurrence,
)
from bots.channelmanager.permissions import (
    AccessDenied,
    bot_post_rights,
    operator_rights,
    post_rights,
    publishing_access,
)
from core.db.base import upsert, utcnow
from core.db.models import Bot as BotRecord
from core.sdk.context import BotContext


def parse_time(value: str, timezone: str) -> datetime:
    try:
        point = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if point.tzinfo is None:
            zone = ZoneInfo(timezone)
            candidates = [point.replace(tzinfo=zone, fold=fold) for fold in (0, 1)]
            valid = [p for p in candidates if p.astimezone(UTC).astimezone(zone).replace(tzinfo=None) == point]
            if not valid or len({p.utcoffset() for p in valid}) != 1:
                raise ContentError("time")
            point = valid[0]
        return point.astimezone(UTC)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise ContentError("time") from exc


@dataclass
class PostView:
    post: Post
    spec: PostSpec
    deliveries: list[Delivery]
    schedule: PostSchedule | None

    @property
    def state(self) -> str:
        if self.post.detached:
            return "detached"
        states = {d.state for d in self.deliveries}
        if not states:
            return "draft"
        if "uncertain" in states:
            return "uncertain"
        if "sent" in states:
            return "sent" if states == {"sent"} else "partial"
        if "pending" in states:
            return "queued"
        if "held" in states:
            return "held"
        if "failed" in states:
            return "failed"
        return "deleted" if states == {"deleted"} else "cancelled"


class PostService:
    def __init__(self, ctx: BotContext):
        self.ctx = ctx

    async def view(self, post_id: str, user_id: int, action: str = "view") -> PostView:
        async with self.ctx.sm() as session:
            post = await session.get(Post, (self.ctx.bot_id, post_id))
            if post is None:
                raise AccessDenied("post_not_found")
            version = await session.get(PostVersion, (self.ctx.bot_id, post.id, post.version))
            deliveries = list((await session.scalars(select(Delivery).where(
                Delivery.bot_id == self.ctx.bot_id, Delivery.post_id == post.id,
                Delivery.channel_id.in_(post.target_ids)).order_by(Delivery.channel_id))).all())
            schedule = await session.get(PostSchedule, (self.ctx.bot_id, post.id))
        for channel_id in post.target_ids:
            rights = await post_rights(self.ctx, channel_id, user_id, post.creator_id, action)
            if (post.source_key or "").startswith("auto:") and action in {"edit", "delete"}:
                rights = await operator_rights(self.ctx, channel_id, user_id)
            if (post.source_key or "").startswith("auto:") and action in {"edit", "delete"} and not rights[
                    "can_delete_messages" if action == "delete" else "can_edit_messages"]:
                raise AccessDenied("manual_source_right")
        if version is None:
            raise ContentError("content")
        return PostView(post, PostSpec.model_validate(version.spec), deliveries, schedule)

    async def list_posts(self, user_id: int, channel_id: int | None = None, offset: int = 0, category: str = "all") -> list[Post]:
        conditions = [Post.bot_id == self.ctx.bot_id, Post.detached.is_(False)]
        if category == "draft":
            conditions.append(~exists().where(Delivery.bot_id == Post.bot_id, Delivery.post_id == Post.id))
        elif category == "scheduled":
            conditions.append(exists().where(PostSchedule.bot_id == Post.bot_id, PostSchedule.post_id == Post.id,
                                              PostSchedule.status.in_({"pending", "held"})))
        elif category == "sent":
            conditions.append(exists().where(Delivery.bot_id == Post.bot_id, Delivery.post_id == Post.id, Delivery.state == "sent"))
        elif category != "all":
            raise ContentError("content")
        if channel_id is None:
            conditions.append(Post.creator_id == user_id)
        else:
            rights = await publishing_access(self.ctx, channel_id, user_id)
            if not (rights["can_edit_messages"] or rights["can_delete_messages"]):
                conditions.append(Post.creator_id == user_id)
            conditions.append((Post.channel_id == channel_id) | exists().where(
                Delivery.bot_id == Post.bot_id, Delivery.post_id == Post.id, Delivery.channel_id == channel_id))
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(Post).where(*conditions)
                .order_by(Post.created_at.desc(), Post.id).offset(offset).limit(10))).all())

    async def signature(self, channel_id: int) -> TextBody:
        async with self.ctx.sm() as session:
            row = await session.get(ChannelStyle, (self.ctx.bot_id, channel_id))
        return TextBody.model_validate(row.signature) if row and row.signature else TextBody()

    async def configure(self, channel_id: int, user_id: int, *, signature: TextBody | None = None,
                        timezone: str | None = None) -> None:
        await publishing_access(self.ctx, channel_id, user_id, action="settings")
        if signature and utf16len(signature.text) > 250:
            raise ContentError("length")
        if timezone is not None:
            try:
                ZoneInfo(timezone)
            except (ZoneInfoNotFoundError, ValueError) as exc:
                raise ContentError("time") from exc
        async with self.ctx.sm() as session:
            channel = await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            if channel is None or channel.status != "active":
                raise AccessDenied("channel_inactive")
            if signature is not None:
                await session.execute(upsert(session, ChannelStyle).values(bot_id=self.ctx.bot_id,
                    channel_id=channel_id, signature=signature.model_dump(mode="json")).on_conflict_do_update(
                        index_elements=["bot_id", "channel_id"], set_={"signature": signature.model_dump(mode="json")}))
            if timezone is not None:
                channel.timezone = timezone
            session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=channel_id,
                actor_id=user_id, action="channel.style", details={"signature": signature is not None, "timezone": timezone}))
            await session.commit()

    def check_media(self, spec: PostSpec) -> None:
        if spec.kind != "text" and spec.media_bot_id != self.ctx.bot_id:
            raise ContentError("media")

    async def validate_buttons(self, spec: PostSpec, user_id: int) -> None:
        for row in spec.buttons:
            for button in row:
                if button.required_channel:
                    await publishing_access(self.ctx, button.required_channel, user_id)
                    async with self.ctx.sm() as session:
                        channel = await session.get(Channel, (self.ctx.bot_id, button.required_channel))
                    member = await self.ctx.bot.get_chat_member(button.required_channel, self.ctx.bot_id)
                    if channel is None or channel.status != "active" or member.status != "administrator":
                        raise AccessDenied("membership_channel_unavailable")

    async def create(self, channel_id: int, user_id: int, spec: PostSpec, *, source_key: str | None = None) -> Post:
        self.check_media(spec)
        await publishing_access(self.ctx, channel_id, user_id, action="create")
        await self.validate_buttons(spec, user_id)
        settings = await self.ctx.settings.get()
        async with self.ctx.sm() as session:
            await session.execute(select(BotRecord.id).where(BotRecord.id == self.ctx.bot_id).with_for_update())
            channel = await session.get(Channel, (self.ctx.bot_id, channel_id))
            if not channel or channel.status != "active":
                raise AccessDenied("channel_inactive")
            if source_key:
                previous = await session.scalar(select(Post).where(Post.bot_id == self.ctx.bot_id, Post.source_key == source_key))
                if previous:
                    if previous.creator_id != user_id or previous.channel_id != channel_id:
                        raise AccessDenied("source_mismatch")
                    return previous
            count = await session.scalar(select(func.count()).select_from(Post).where(Post.bot_id == self.ctx.bot_id,
                Post.creator_id == user_id, Post.detached.is_(False), ~exists().where(Delivery.bot_id == Post.bot_id, Delivery.post_id == Post.id)))
            if int(count or 0) >= settings.max_drafts_per_operator:
                raise ContentError("limit")
            post = Post(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=channel_id,
                creator_id=user_id, target_ids=[channel_id], source_key=source_key)
            session.add(post)
            await session.flush()
            session.add(PostVersion(bot_id=self.ctx.bot_id, post_id=post.id, number=1, spec=spec.model_dump(mode="json")))
            self.audit(session, post, user_id, "post.created")
            await session.commit()
            return post

    async def locked(self, session: AsyncSession, post_id: str, generation: int) -> Post:
        post = await session.get(Post, (self.ctx.bot_id, post_id), with_for_update=True, populate_existing=True)
        if post is None or post.generation != generation or post.detached:
            raise ContentError("stale")
        busy = await session.scalar(select(Operation.id).join(Delivery,
            (Operation.bot_id == Delivery.bot_id) & (Operation.delivery_id == Delivery.id)).where(
                Delivery.bot_id == self.ctx.bot_id, Delivery.post_id == post.id,
                Operation.status == "running", Operation.dispatched.is_(True)).limit(1))
        if busy:
            raise ContentError("busy")
        return post

    def audit(self, session: AsyncSession, post: Post, user_id: int, action: str) -> None:
        session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=post.channel_id,
            actor_id=user_id, action=action, details={"post_id": post.id, "generation": post.generation, "version": post.version}))

    async def deliveries(self, session: AsyncSession, post: Post) -> list[Delivery]:
        return list((await session.scalars(select(Delivery).where(
            Delivery.bot_id == self.ctx.bot_id, Delivery.post_id == post.id).order_by(Delivery.channel_id))).all())

    async def release_slots(self, session: AsyncSession, post: Post) -> None:
        rows = await self.deliveries(session, post)
        if not any(row.state in {"sent", "uncertain", "deleted", "detached"} for row in rows):
            await session.execute(delete(CalendarReservation).where(CalendarReservation.bot_id == self.ctx.bot_id,
                CalendarReservation.post_id == post.id))

    async def cancel_ops(self, session: AsyncSession, post: Post, *, all_kinds: bool = False) -> None:
        ids = select(Delivery.id).where(Delivery.bot_id == self.ctx.bot_id, Delivery.post_id == post.id)
        where = [Operation.bot_id == self.ctx.bot_id, Operation.delivery_id.in_(ids),
                 Operation.status.in_({"pending", "running"}), Operation.dispatched.is_(False)]
        if not all_kinds:
            where.append(Operation.kind.in_({"publish", "edit", "pin", "markup"}))
        await session.execute(update(Operation).where(*where).values(status="cancelled", error_code="post_changed", updated_at=utcnow()))

    async def authorize_targets(self, view: PostView, user_id: int, target_ids: list[int] | None = None) -> None:
        from bots.channelmanager.release import require
        await require(self.ctx, "publishing")
        from bots.channelmanager.senders import allowed
        for channel_id in target_ids or view.post.target_ids:
            async with self.ctx.sm() as session:
                if not await allowed(self.ctx, channel_id, session=session):
                    raise AccessDenied("sender_changed")
            rights = await post_rights(self.ctx, channel_id, user_id, view.post.creator_id, "publish")
            await bot_post_rights(self.ctx, channel_id, "publish")
            if view.spec.pin:
                if not rights["can_edit_messages"]:
                    raise AccessDenied("pin_right")
                await bot_post_rights(self.ctx, channel_id, "pin")

    async def quota(self, session: AsyncSession, post: Post, run_at: datetime) -> None:
        for channel_id in sorted(post.target_ids):
            channel = await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            if not channel or channel.status != "active":
                raise AccessDenied("channel_inactive")
            if run_at <= utcnow():
                continue
            entitlement = await session.get(Entitlement, (self.ctx.bot_id, channel_id))
            if entitlement is None:
                raise ContentError("limit")
            count = await session.scalar(select(func.count()).select_from(Delivery).join(PostSchedule,
                (PostSchedule.bot_id == Delivery.bot_id) & (PostSchedule.post_id == Delivery.post_id)).where(
                    Delivery.bot_id == self.ctx.bot_id, Delivery.channel_id == channel_id, Delivery.post_id != post.id,
                    Delivery.state == "pending", PostSchedule.status == "pending", PostSchedule.run_at > utcnow()))
            from bots.channelmanager.billing import limits_for
            if int(count or 0) >= (await limits_for(self.ctx, channel_id, session=session)).schedules:
                raise ContentError("limit")

    async def queue(self, session: AsyncSession, post: Post, user_id: int, run_at: datetime) -> None:
        await self.quota(session, post, run_at)
        ids = select(Delivery.id).where(Delivery.bot_id == self.ctx.bot_id, Delivery.post_id == post.id)
        await session.execute(update(Operation).where(Operation.bot_id == self.ctx.bot_id, Operation.delivery_id.in_(ids),
            Operation.kind == "publish", Operation.status.in_({"pending", "running"}), Operation.dispatched.is_(False)).values(status="cancelled"))
        existing = {row.channel_id: row for row in await self.deliveries(session, post)}
        candidates = [c for c in post.target_ids if c not in existing or existing[c].state in {"pending", "held", "failed", "cancelled"}]
        if not candidates:
            raise ContentError("already_sent")
        schedule = await session.get(PostSchedule, (self.ctx.bot_id, post.id))
        if schedule is None:
            schedule = PostSchedule(bot_id=self.ctx.bot_id, post_id=post.id, generation=post.generation, run_at=run_at)
            session.add(schedule)
        schedule.run_at, schedule.generation, schedule.status = run_at, post.generation, "pending"
        for channel_id in candidates:
            channel = await session.get(Channel, (self.ctx.bot_id, channel_id))
            assert channel is not None
            delivery = existing.get(channel_id)
            if delivery is None:
                delivery = Delivery(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, post_id=post.id,
                    channel_id=channel_id, version=post.version, generation=post.generation, actor_id=user_id)
                session.add(delivery)
            delivery.version, delivery.generation, delivery.actor_id = post.version, post.generation, user_id
            delivery.state, delivery.error_code = "pending", None
            await session.flush()
            delivery.publish_op = await outbox.enqueue(session, self.ctx, channel, kind="publish",
                dedupe_key=f"publish:{delivery.id}:{post.generation}", run_at=run_at,
                payload={"delivery_id": delivery.id, "version": post.version, "actor_id": user_id, "automatic": False})

    async def publish(self, post_id: str, user_id: int, generation: int, *, run_at: datetime | None = None) -> Post:
        view = await self.view(post_id, user_id, "publish")
        await self.authorize_targets(view, user_id)
        await self.validate_buttons(view.spec, user_id)
        when = run_at or utcnow()
        if run_at and (run_at.tzinfo is None or run_at <= utcnow()):
            raise ContentError("time")
        if run_at:
            for channel_id in view.post.target_ids:
                await publishing_access(self.ctx, channel_id, user_id, action="schedule")
        if view.spec.reply_message_id and view.post.target_ids != [view.post.channel_id]:
            raise ContentError("reply")
        async with self.ctx.sm() as session:
            post = await self.locked(session, post_id, generation)
            if await session.scalar(select(Recurrence.id).where(Recurrence.bot_id == self.ctx.bot_id, Recurrence.post_id == post.id)):
                raise ContentError("series_template")
            await self.release_slots(session, post)
            post.generation, post.updated_at = post.generation + 1, utcnow()
            await self.queue(session, post, user_id, when)
            self.audit(session, post, user_id, "post.scheduled" if run_at else "post.publish")
            await session.commit()
            return post

    async def edit(self, post_id: str, user_id: int, generation: int, spec: PostSpec) -> Post:
        self.check_media(spec)
        await self.validate_buttons(spec, user_id)
        view = await self.view(post_id, user_id, "edit")
        for delivery in view.deliveries:
            if delivery.state == "sent":
                await bot_post_rights(self.ctx, delivery.channel_id, "edit")
                async with self.ctx.sm() as read:
                    old = await read.get(PostVersion, (self.ctx.bot_id, post_id, delivery.version))
                assert old is not None
                previous = PostSpec.model_validate(old.spec)
                if previous.kind != "text" and spec.kind == "text":
                    raise ContentError("conversion")
                if any(getattr(previous, key) != getattr(spec, key) for key in (
                        "notifications", "protected", "pin", "reply_message_id", "delete_after_seconds")):
                    raise ContentError("published_settings")
        if spec.reply_message_id and view.post.target_ids != [view.post.channel_id]:
            raise ContentError("reply")
        async with self.ctx.sm() as session:
            post = await self.locked(session, post_id, generation)
            await self.invalidate_template(session, post)
            post.version, post.generation, post.updated_at = post.version + 1, post.generation + 1, utcnow()
            session.add(PostVersion(bot_id=self.ctx.bot_id, post_id=post.id, number=post.version, spec=spec.model_dump(mode="json")))
            await session.flush()
            await self.cancel_ops(session, post)
            schedule = await session.get(PostSchedule, (self.ctx.bot_id, post.id))
            rows = await self.deliveries(session, post)
            for delivery in rows:
                if delivery.state == "sent":
                    channel = await session.get(Channel, (self.ctx.bot_id, delivery.channel_id))
                    assert channel is not None
                    delivery.generation, delivery.edit_status = post.generation, "pending"
                    delivery.edit_op = await outbox.enqueue(session, self.ctx, channel, kind="edit",
                        dedupe_key=f"edit:{delivery.id}:{post.generation}", payload={"delivery_id": delivery.id,
                            "version": post.version, "actor_id": user_id, "automatic": False})
            if schedule and schedule.status == "pending" and any(d.state == "pending" for d in rows):
                await self.queue(session, post, user_id, max(schedule.run_at, utcnow()))
            self.audit(session, post, user_id, "post.edited")
            await session.commit()
            return post

    async def targets(self, post_id: str, user_id: int, generation: int, target_ids: list[int]) -> Post:
        if not 1 <= len(set(target_ids)) <= 10:
            raise ContentError("targets")
        view = await self.view(post_id, user_id, "edit")
        if any(d.state not in {"pending", "cancelled", "held", "failed"} for d in view.deliveries):
            raise ContentError("published_settings")
        if view.spec.reply_message_id and set(target_ids) != {view.post.channel_id}:
            raise ContentError("reply")
        await self.authorize_targets(view, user_id, list(set(target_ids)))
        async with self.ctx.sm() as session:
            post = await self.locked(session, post_id, generation)
            if user_id != post.creator_id and await session.scalar(select(Recurrence.id).where(
                Recurrence.bot_id == self.ctx.bot_id, Recurrence.post_id == post.id)):
                raise AccessDenied("series_creator")
            await self.invalidate_template(session, post)
            await self.release_slots(session, post)
            await self.cancel_ops(session, post)
            post.target_ids = sorted(set(target_ids))
            post.generation, post.updated_at = post.generation + 1, utcnow()
            for delivery in await self.deliveries(session, post):
                if delivery.channel_id not in post.target_ids:
                    delivery.state = "cancelled"
            schedule = await session.get(PostSchedule, (self.ctx.bot_id, post.id))
            if schedule and schedule.status == "pending":
                await self.queue(session, post, user_id, max(schedule.run_at, utcnow()))
            self.audit(session, post, user_id, "post.targets")
            await session.commit()
            return post

    async def cancel(self, post_id: str, user_id: int, generation: int, *, detach: bool = False) -> None:
        await self.view(post_id, user_id, "edit")
        async with self.ctx.sm() as session:
            post = await self.locked(session, post_id, generation)
            await self.pause_template(session, post)
            await self.release_slots(session, post)
            post.generation, post.detached = post.generation + 1, detach
            await self.cancel_ops(session, post, all_kinds=detach)
            for delivery in await self.deliveries(session, post):
                if detach:
                    delivery.state = "detached"
                elif delivery.state in {"pending", "held", "failed"}:
                    delivery.state = "cancelled"
            schedule = await session.get(PostSchedule, (self.ctx.bot_id, post.id))
            if schedule:
                schedule.status = "cancelled"
            self.audit(session, post, user_id, "post.detached" if detach else "post.cancelled")
            await session.commit()

    async def delete(self, post_id: str, user_id: int, generation: int) -> None:
        view = await self.view(post_id, user_id, "delete")
        for delivery in view.deliveries:
            if delivery.state == "sent":
                await bot_post_rights(self.ctx, delivery.channel_id, "delete")
        async with self.ctx.sm() as session:
            post = await self.locked(session, post_id, generation)
            await self.pause_template(session, post)
            await self.release_slots(session, post)
            post.generation += 1
            await self.cancel_ops(session, post)
            for delivery in await self.deliveries(session, post):
                if delivery.state in {"pending", "held", "failed"}:
                    delivery.state = "cancelled"
                if delivery.state != "sent":
                    continue
                if delivery.delete_op:
                    await session.execute(update(Operation).where(Operation.bot_id == self.ctx.bot_id,
                        Operation.id == delivery.delete_op, Operation.dispatched.is_(False), Operation.status == "pending").values(status="cancelled"))
                channel = await session.get(Channel, (self.ctx.bot_id, delivery.channel_id))
                assert channel is not None
                reminder = delivery.sent_at is None or (utcnow() - delivery.sent_at).total_seconds() >= 172800
                delivery.delete_status = "pending"
                delivery.delete_op = await outbox.enqueue(session, self.ctx, channel,
                    kind="delete_reminder" if reminder else "delete", dedupe_key=f"delete:{delivery.id}:{post.generation}",
                    payload={"delivery_id": delivery.id, "version": delivery.version, "actor_id": user_id, "automatic": False})
            schedule = await session.get(PostSchedule, (self.ctx.bot_id, post.id))
            if schedule:
                schedule.status = "cancelled"
            self.audit(session, post, user_id, "post.delete_requested")
            await session.commit()

    async def invalidate_template(self, session: AsyncSession, post: Post) -> None:
        row = await session.scalar(select(Recurrence).where(Recurrence.bot_id == self.ctx.bot_id,
            Recurrence.post_id == post.id).with_for_update())
        if row:
            await self.ctx.extras["recurring"].cancel_pending(session, row)
            row.generation += 1

    async def pause_template(self, session: AsyncSession, post: Post) -> None:
        row = await session.scalar(select(Recurrence).where(Recurrence.bot_id == self.ctx.bot_id,
            Recurrence.post_id == post.id).with_for_update())
        if row:
            await self.ctx.extras["recurring"].cancel_pending(session, row)
            row.status, row.next_at, row.generation = "paused", None, row.generation + 1

    async def retry_followups(self, post_id: str, user_id: int, generation: int) -> None:
        view = await self.view(post_id, user_id, "edit")
        candidates = []
        for delivery in view.deliveries:
            if delivery.state != "sent":
                continue
            for kind in ("edit", "pin", "delete", "markup"):
                if getattr(delivery, f"{kind}_status") != "failed":
                    continue
                rights = await post_rights(self.ctx, delivery.channel_id, user_id, view.post.creator_id,
                                          "delete" if kind == "delete" else "edit")
                if kind == "pin" and not rights["can_edit_messages"]:
                    raise AccessDenied("pin_right")
                await bot_post_rights(self.ctx, delivery.channel_id, kind)
                candidates.append((delivery.id, kind))
        async with self.ctx.sm() as session:
            post = await self.locked(session, post_id, generation)
            queued = False
            for delivery_id, kind in candidates:
                fresh = await session.get(Delivery, (self.ctx.bot_id, delivery_id), with_for_update=True)
                if fresh is None or fresh.state != "sent" or getattr(fresh, f"{kind}_status") != "failed":
                    continue
                delivery = fresh
                channel = await session.get(Channel, (self.ctx.bot_id, delivery.channel_id))
                assert channel is not None
                previous = await session.get(Operation, (self.ctx.bot_id, getattr(delivery, f"{kind}_op")))
                actual_kind = previous.kind if kind == "delete" and previous else kind
                version = post.version if kind == "edit" else delivery.version
                operation_id = await outbox.enqueue(session, self.ctx, channel, kind=actual_kind,
                    dedupe_key=f"retry:{delivery_id}:{kind}:{uuid.uuid4().hex[:16]}",
                    payload={"delivery_id": delivery_id, "version": version, "actor_id": user_id, "automatic": False})
                setattr(delivery, f"{kind}_status", "pending")
                setattr(delivery, f"{kind}_op", operation_id)
                queued = True
            if not queued:
                raise ContentError("already_sent")
            self.audit(session, post, user_id, "post.followups_retried")
            await session.commit()
