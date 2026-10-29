"""Recurring templates materialize independent SQL posts and retain cleanup per occurrence."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import func, select, update

from bots.channelmanager import outbox
from bots.channelmanager.content import ContentError, PostSpec
from bots.channelmanager.models import (
    BatchItem,
    Channel,
    Delivery,
    Occurrence,
    Operation,
    Post,
    PostSchedule,
    PostVersion,
    Recurrence,
)
from bots.channelmanager.permissions import AccessDenied, publishing_access
from bots.channelmanager.posts import PostView
from bots.channelmanager.timing import Rule
from core.db.base import utcnow
from core.db.models import Bot as BotRecord
from core.sdk.context import BotContext


class RecurrenceService:
    def __init__(self, ctx: BotContext):
        self.ctx = ctx
        self.posts = ctx.extras["posts"]

    async def list_for(self, user_id: int) -> list[Recurrence]:
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(Recurrence).join(Post,
                (Post.bot_id == Recurrence.bot_id) & (Post.id == Recurrence.post_id)).where(
                    Post.bot_id == self.ctx.bot_id, Post.creator_id == user_id).order_by(Recurrence.id).limit(100))).all())

    async def get(self, series_id: str, user_id: int) -> Recurrence:
        async with self.ctx.sm() as session:
            row = await session.get(Recurrence, (self.ctx.bot_id, series_id))
        if row is None:
            raise ContentError("stale")
        await self.posts.view(row.post_id, user_id)
        return row

    async def configure(self, post_id: str, user_id: int, generation: int, rule: Rule, *, replace_previous=False) -> Recurrence:
        view = await self.posts.view(post_id, user_id, "edit")
        if view.post.creator_id != user_id:
            raise AccessDenied("series_creator")
        if view.deliveries:
            raise ContentError("series_draft")
        await self.posts.authorize_targets(view, user_id)
        for channel_id in view.post.target_ids:
            await publishing_access(self.ctx, channel_id, user_id, action="schedule")
        upcoming = rule.next(utcnow(), 5, inclusive=True)
        if not upcoming:
            raise ContentError("time")
        async with self.ctx.sm() as session:
            await session.get(BotRecord, self.ctx.bot_id, with_for_update=True)
            root = await self.posts.locked(session, post_id, generation)
            if await session.scalar(select(BatchItem.post_id).where(BatchItem.bot_id == self.ctx.bot_id, BatchItem.post_id == root.id)):
                raise ContentError("series_draft")
            row = await session.scalar(select(Recurrence).where(Recurrence.bot_id == self.ctx.bot_id,
                Recurrence.post_id == post_id).with_for_update())
            if row is None:
                count = await session.scalar(select(func.count()).select_from(Recurrence).join(Post,
                    (Post.bot_id == Recurrence.bot_id) & (Post.id == Recurrence.post_id)).where(
                        Recurrence.bot_id == self.ctx.bot_id, Post.creator_id == user_id))
                if int(count or 0) >= (await self.ctx.settings.get()).max_recurrences_per_operator:
                    raise ContentError("limit")
                row = Recurrence(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], post_id=post_id, rule=rule.model_dump(mode="json"))
                session.add(row)
            else:
                await self.cancel_pending(session, row)
                row.generation += 1
            row.rule, row.next_at, row.replace_previous = rule.model_dump(mode="json"), upcoming[0], replace_previous
            row.status, row.error_code = "active", None
            root.generation += 1
            self.posts.audit(session, root, user_id, "recurrence.configured")
            await session.commit()
            return row

    async def cancel_pending(self, session, row: Recurrence) -> None:
        children = (await session.scalars(select(Post).join(Occurrence,
            (Occurrence.bot_id == Post.bot_id) & (Occurrence.post_id == Post.id)).join(PostSchedule,
                (PostSchedule.bot_id == Post.bot_id) & (PostSchedule.post_id == Post.id)).where(
                    Occurrence.bot_id == self.ctx.bot_id, Occurrence.recurrence_id == row.id,
                    PostSchedule.status.in_({"pending", "held"})).order_by(Post.id))).all()
        for child in children:
            child = await self.posts.locked(session, child.id, child.generation)
            await self.posts.cancel_ops(session, child)
            child.generation += 1
            for target in await self.posts.deliveries(session, child):
                if target.state in {"pending", "held", "failed"}:
                    target.state = "cancelled"
            schedule = await session.get(PostSchedule, (self.ctx.bot_id, child.id))
            assert schedule is not None
            schedule.status = "cancelled"

    async def toggle(self, series_id: str, user_id: int, generation: int, *, active: bool) -> Recurrence:
        initial = await self.get(series_id, user_id)
        view = await self.posts.view(initial.post_id, user_id, "edit")
        if view.post.creator_id != user_id:
            raise AccessDenied("series_creator")
        if active:
            await self.posts.authorize_targets(view, user_id)
            for channel_id in view.post.target_ids:
                await publishing_access(self.ctx, channel_id, user_id, action="schedule")
        async with self.ctx.sm() as session:
            root = await self.posts.locked(session, view.post.id, view.post.generation)
            row = await session.get(Recurrence, (self.ctx.bot_id, series_id), with_for_update=True)
            if row is None or row.generation != generation:
                raise ContentError("stale")
            await self.cancel_pending(session, row)
            following = Rule.model_validate(row.rule).next(utcnow(), 1) if active else []
            row.status = "active" if following else "finished" if active else "paused"
            row.next_at = following[0] if following else None
            row.generation, row.error_code = row.generation + 1, None
            root.generation += 1
            self.posts.audit(session, root, user_id, "recurrence.resumed" if active else "recurrence.paused")
            await session.commit()
            return row

    async def sweep(self, limit: int = 25, *, now: datetime | None = None) -> int:
        now = now or utcnow()
        settings = await self.ctx.settings.get()
        if settings.maintenance:
            return 0
        grace = settings.recurrence_lateness_grace_seconds
        async with self.ctx.sm() as session:
            if not await session.scalar(select(BotRecord.active).where(BotRecord.id == self.ctx.bot_id)):
                return 0
            due = (await session.execute(select(Recurrence.id, Recurrence.post_id).where(Recurrence.bot_id == self.ctx.bot_id,
                Recurrence.status == "active", Recurrence.next_at <= now).order_by(Recurrence.next_at).limit(limit))).all()
        made = 0
        for series_id, root_id in due:
            async with self.ctx.sm() as session:
                # Same order as configuration and pause/resume: template, recurrence, children.
                root = await session.get(Post, (self.ctx.bot_id, root_id), with_for_update=True)
                row = await session.get(Recurrence, (self.ctx.bot_id, series_id), with_for_update=True)
                if root is None or row is None or row.status != "active" or row.next_at is None or row.next_at > now:
                    continue
                if root.detached:
                    row.status, row.error_code = "paused", "template_detached"
                    await session.commit()
                    continue
                rule = Rule.model_validate(row.rule)
                point = row.next_at
                if point < now - timedelta(seconds=grace):
                    row.last_skipped_at = point
                    fresh = rule.next(now, 1, inclusive=True)
                    row.next_at = fresh[0] if fresh else None
                    if row.next_at is None:
                        row.status = "finished"
                    await session.commit()
                    continue
                version = await session.get(PostVersion, (self.ctx.bot_id, root.id, root.version))
                assert version is not None
                spec = PostSpec.model_validate(version.spec)
                try:
                    await self.posts.authorize_targets(PostView(root, spec, [], None), root.creator_id)
                    for channel_id in root.target_ids:
                        await publishing_access(self.ctx, channel_id, root.creator_id, action="schedule")
                    await self.posts.validate_buttons(spec, root.creator_id)
                except AccessDenied:
                    row.status, row.error_code = "paused", "rights_lost"
                    await session.commit()
                    continue
                existing = await session.get(Occurrence, (self.ctx.bot_id, row.id, point))
                if existing is None:
                    child = Post(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=root.channel_id,
                        creator_id=root.creator_id, target_ids=list(root.target_ids), source_key=f"occ:{row.id}:{point.isoformat()}")
                    session.add(child)
                    await session.flush()
                    session.add(PostVersion(bot_id=self.ctx.bot_id, post_id=child.id, number=1, spec=version.spec))
                    await session.flush()
                    session.add(Occurrence(bot_id=self.ctx.bot_id, recurrence_id=row.id, scheduled_at=point,
                        post_id=child.id, root_version=root.version))
                    await self.posts.queue(session, child, root.creator_id, point)
                    self.posts.audit(session, child, root.creator_id, "recurrence.occurrence")
                    made += 1
                following = rule.next(point, 1)
                row.next_at = following[0] if following else None
                if row.next_at is None:
                    row.status = "finished"
                await session.commit()
        return made


async def replace_previous(session, ctx: BotContext, current: Delivery, actor_id: int) -> None:
    occurrence = await session.scalar(select(Occurrence).where(Occurrence.bot_id == ctx.bot_id, Occurrence.post_id == current.post_id))
    if occurrence is None:
        return
    series = await session.get(Recurrence, (ctx.bot_id, occurrence.recurrence_id))
    if series is None or not series.replace_previous:
        return
    # Persist first. Locking an older post while holding the current post could
    # deadlock with a pause that locks several occurrences in sorted order.
    current.replace_pending = True


async def settle_replacements(ctx: BotContext, limit: int = 100, *, target_id: str | None = None) -> None:
    async with ctx.sm() as session:
        conditions = [Delivery.bot_id == ctx.bot_id, Delivery.replace_pending.is_(True)]
        if target_id:
            conditions.append(Delivery.id == target_id)
        ids = (await session.scalars(select(Delivery.id).where(*conditions).order_by(Delivery.created_at).limit(limit))).all()
    for delivery_id in ids:
        async with ctx.sm() as session:
            current = await session.get(Delivery, (ctx.bot_id, delivery_id))
            if current is None:
                continue
            occurrence = await session.scalar(select(Occurrence).where(Occurrence.bot_id == ctx.bot_id, Occurrence.post_id == current.post_id))
            if occurrence is None:
                continue
            previous = await session.scalar(select(Delivery).join(Occurrence,
                (Occurrence.bot_id == Delivery.bot_id) & (Occurrence.post_id == Delivery.post_id)).where(
                    Occurrence.bot_id == ctx.bot_id, Occurrence.recurrence_id == occurrence.recurrence_id,
                    Occurrence.scheduled_at < occurrence.scheduled_at, Delivery.channel_id == current.channel_id,
                    Delivery.state == "sent", Delivery.message_id.is_not(None)).order_by(Occurrence.scheduled_at.desc()).limit(1))
            post_ids = sorted({current.post_id, *([previous.post_id] if previous else [])})
            locked = list((await session.scalars(select(Post).where(Post.bot_id == ctx.bot_id, Post.id.in_(post_ids))
                .order_by(Post.id).with_for_update(skip_locked=True))).all())
            if len(locked) != len(post_ids):
                continue
            current = await session.get(Delivery, (ctx.bot_id, delivery_id), with_for_update=True, populate_existing=True)
            if current is None or not current.replace_pending:
                continue
            current_post = next(p for p in locked if p.id == current.post_id)
            channel = await session.get(Channel, (ctx.bot_id, current.channel_id))
            if previous is None or current_post.detached or current.state not in {"sent", "deleted"} or channel is None or channel.status == "disconnected":
                current.replace_pending = False
                await session.commit()
                continue
            previous = await session.get(Delivery, (ctx.bot_id, previous.id), with_for_update=True, populate_existing=True)
            if previous is None or previous.state != "sent":
                continue
            if previous.delete_op:
                old = await session.get(Operation, (ctx.bot_id, previous.delete_op))
                if old and old.status == "running" and old.dispatched:
                    continue
                await session.execute(update(Operation).where(Operation.bot_id == ctx.bot_id, Operation.id == previous.delete_op,
                    Operation.status.in_({"pending", "running"}), Operation.dispatched.is_(False)).values(status="cancelled"))
            previous.delete_status = "pending"
            previous.delete_op = await outbox.enqueue(session, ctx, channel, kind="delete", dedupe_key=f"replace:{current.id}:{previous.id}",
                payload={"delivery_id": previous.id, "version": previous.version, "actor_id": current.actor_id, "automatic": True})
            current.replace_pending = False
            await session.commit()
