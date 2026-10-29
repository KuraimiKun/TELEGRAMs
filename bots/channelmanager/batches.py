"""Durable multipost collection and all-or-nothing weekly-slot allocation."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import delete, exists, func, select

from bots.channelmanager.content import ContentError, PostSpec
from bots.channelmanager.models import (
    Batch,
    BatchItem,
    Calendar,
    CalendarReservation,
    Channel,
    Delivery,
    Post,
    PostSchedule,
    PostVersion,
)
from bots.channelmanager.permissions import AccessDenied, publishing_access
from bots.channelmanager.timing import WeeklySlot, calendar_times
from core.db.base import utcnow
from core.db.models import Bot as BotRecord
from core.sdk.context import BotContext


class BatchService:
    def __init__(self, ctx: BotContext):
        self.ctx = ctx
        self.posts = ctx.extras["posts"]

    async def list_for(self, user_id: int) -> list[Batch]:
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(Batch).where(Batch.bot_id == self.ctx.bot_id,
                Batch.creator_id == user_id).order_by(Batch.id).limit(100))).all())

    async def get(self, batch_id: str, user_id: int) -> Batch:
        async with self.ctx.sm() as session:
            row = await session.get(Batch, (self.ctx.bot_id, batch_id))
            if row is None or row.creator_id != user_id:
                raise AccessDenied("batch_owner")
        await publishing_access(self.ctx, row.channel_id, user_id)
        return row

    async def items(self, batch_id: str, user_id: int) -> list[BatchItem]:
        await self.get(batch_id, user_id)
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(BatchItem).where(BatchItem.bot_id == self.ctx.bot_id,
                BatchItem.batch_id == batch_id, BatchItem.active.is_(True)).order_by(BatchItem.position))).all())

    async def create(self, channel_id: int, user_id: int, defaults: dict | None = None,
                     *, buttons_mode: str = "shared", reactions_mode: str = "shared") -> Batch:
        await publishing_access(self.ctx, channel_id, user_id, action="create")
        if buttons_mode not in {"shared", "per_item", "none"} or reactions_mode not in {"shared", "per_item", "none"}:
            raise ContentError("content")
        values = defaults or {"signature": (await self.posts.signature(channel_id)).model_dump(mode="json"),
                              "reactions": await self.ctx.extras["presets"].reactions(channel_id)}
        allowed = {"buttons", "reactions", "signature", "include_signature", "notifications", "protected", "pin", "link_preview", "delete_after_seconds"}
        if set(values) - allowed:
            raise ContentError("content")
        spec = PostSpec.model_validate({"body": {"text": "validation"}, **values})
        await self.posts.validate_buttons(spec, user_id)
        async with self.ctx.sm() as session:
            await session.get(BotRecord, self.ctx.bot_id, with_for_update=True)
            count = await session.scalar(select(func.count()).select_from(Batch).where(Batch.bot_id == self.ctx.bot_id,
                Batch.creator_id == user_id, Batch.status.in_({"collecting", "ready"})))
            if int(count or 0) >= (await self.ctx.settings.get()).max_batches_per_operator:
                raise ContentError("limit")
            row = Batch(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=channel_id, creator_id=user_id,
                defaults=values, buttons_mode=buttons_mode, reactions_mode=reactions_mode)
            session.add(row)
            await session.commit()
            return row

    async def locked(self, session, batch_id: str, user_id: int, generation: int) -> Batch:
        row = await session.get(Batch, (self.ctx.bot_id, batch_id), with_for_update=True)
        if row is None or row.creator_id != user_id or row.generation != generation or row.status == "cancelled":
            raise ContentError("stale")
        return row

    async def configure(self, batch_id: str, user_id: int, generation: int, *, defaults: dict | None = None,
                        buttons_mode: str | None = None, reactions_mode: str | None = None) -> Batch:
        initial = await self.get(batch_id, user_id)
        values = {**initial.defaults, **(defaults or {})}
        if set(values) - {"buttons", "reactions", "signature", "include_signature", "notifications", "protected", "pin", "link_preview", "delete_after_seconds"}:
            raise ContentError("content")
        spec = PostSpec.model_validate({"body": {"text": "validation"}, **values})
        await self.posts.validate_buttons(spec, user_id)
        if any(mode is not None and mode not in {"shared", "per_item", "none"} for mode in (buttons_mode, reactions_mode)):
            raise ContentError("content")
        async with self.ctx.sm() as session:
            row = await self.locked(session, batch_id, user_id, generation)
            if row.status not in {"collecting", "ready"}:
                raise ContentError("batch_queued")
            row.defaults = values
            if buttons_mode:
                row.buttons_mode = buttons_mode
            if reactions_mode:
                row.reactions_mode = reactions_mode
            row.generation += 1
            await session.commit()
            return row

    async def add(self, batch_id: str, user_id: int, generation: int, spec: PostSpec, input_key: str) -> Post:
        await self.get(batch_id, user_id)
        self.posts.check_media(spec)
        if not 1 <= len(input_key) <= 64:
            raise ContentError("content")
        async with self.ctx.sm() as session:
            await session.get(BotRecord, self.ctx.bot_id, with_for_update=True)
            row = await self.locked(session, batch_id, user_id, generation)
            existing = await session.scalar(select(BatchItem).where(BatchItem.bot_id == self.ctx.bot_id,
                BatchItem.batch_id == batch_id, BatchItem.input_key == input_key))
            if existing:
                if not existing.active:
                    raise ContentError("stale")
                result = await session.get(Post, (self.ctx.bot_id, existing.post_id))
                assert result is not None
                return result
            if row.status not in {"collecting", "ready"}:
                raise ContentError("batch_queued")
            items = list((await session.scalars(select(BatchItem).where(BatchItem.bot_id == self.ctx.bot_id, BatchItem.batch_id == batch_id))).all())
            if sum(item.active for item in items) >= (await self.ctx.settings.get()).max_batch_items:
                raise ContentError("limit")
            drafts = await session.scalar(select(func.count()).select_from(Post).where(Post.bot_id == self.ctx.bot_id,
                Post.creator_id == user_id, Post.detached.is_(False), ~exists().where(Delivery.bot_id == Post.bot_id, Delivery.post_id == Post.id)))
            if int(drafts or 0) >= (await self.ctx.settings.get()).max_drafts_per_operator:
                raise ContentError("limit")
            values = spec.model_dump(mode="json")
            for key, value in row.defaults.items():
                if key not in {"buttons", "reactions"} or getattr(row, f"{key}_mode") == "shared":
                    values[key] = value
            for key in ("buttons", "reactions"):
                if getattr(row, f"{key}_mode") == "none":
                    values[key] = []
            content = PostSpec.model_validate(values)
            await self.posts.validate_buttons(content, user_id)
            post = Post(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=row.channel_id,
                creator_id=user_id, target_ids=[row.channel_id], source_key=f"batch:{batch_id}:{input_key}")
            session.add(post)
            await session.flush()
            session.add(PostVersion(bot_id=self.ctx.bot_id, post_id=post.id, number=1, spec=content.model_dump(mode="json")))
            session.add(BatchItem(bot_id=self.ctx.bot_id, batch_id=batch_id, position=max((i.position for i in items), default=0) + 1,
                post_id=post.id, input_key=input_key))
            row.status, row.generation = "collecting", row.generation + 1
            self.posts.audit(session, post, user_id, "batch.item_added")
            await session.commit()
            return post

    async def remove(self, batch_id: str, user_id: int, generation: int, position: int | None = None) -> None:
        await self.get(batch_id, user_id)
        async with self.ctx.sm() as session:
            row = await self.locked(session, batch_id, user_id, generation)
            if row.status not in {"collecting", "ready"}:
                raise ContentError("batch_queued")
            conditions = [BatchItem.bot_id == self.ctx.bot_id, BatchItem.batch_id == batch_id, BatchItem.active.is_(True)]
            if position is not None:
                conditions.append(BatchItem.position == position)
            item = await session.scalar(select(BatchItem).where(*conditions).order_by(BatchItem.position.desc()).limit(1))
            if item is None:
                raise ContentError("content")
            post = await session.get(Post, (self.ctx.bot_id, item.post_id), with_for_update=True)
            assert post is not None
            if await self.posts.deliveries(session, post):
                raise ContentError("batch_queued")
            post.detached, item.active = True, False
            row.generation += 1
            await session.commit()

    async def ready(self, batch_id: str, user_id: int, generation: int) -> Batch:
        await self.get(batch_id, user_id)
        async with self.ctx.sm() as session:
            row = await self.locked(session, batch_id, user_id, generation)
            if row.status not in {"collecting", "ready"}:
                raise ContentError("batch_queued")
            row.status, row.generation = "ready", row.generation + 1
            await session.commit()
            return row

    async def calendars(self, channel_id: int, user_id: int) -> list[Calendar]:
        await publishing_access(self.ctx, channel_id, user_id, action="schedule")
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(Calendar).where(Calendar.bot_id == self.ctx.bot_id,
                Calendar.channel_id == channel_id).order_by(Calendar.name).limit(100))).all())

    async def save_calendar(self, channel_id: int, user_id: int, name: str, timezone: str, slots: list[dict],
                            *, calendar_id: str | None = None, generation: int | None = None) -> Calendar:
        await publishing_access(self.ctx, channel_id, user_id, action="settings")
        name = name.strip()
        if not 1 <= len(name) <= 64:
            raise ContentError("name")
        calendar_times(slots, timezone, utcnow(), 1)
        normalized = [WeeklySlot.model_validate(s).model_dump(mode="json") for s in slots]
        async with self.ctx.sm() as session:
            row = await session.get(Calendar, (self.ctx.bot_id, calendar_id), with_for_update=True) if calendar_id else None
            await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            if calendar_id and (row is None or row.channel_id != channel_id or row.generation != generation):
                raise ContentError("stale")
            duplicate = await session.scalar(select(Calendar.id).where(Calendar.bot_id == self.ctx.bot_id,
                Calendar.channel_id == channel_id, Calendar.name == name))
            if duplicate and (row is None or duplicate != row.id):
                raise ContentError("name")
            if row is None:
                count = await session.scalar(select(func.count()).select_from(Calendar).where(
                    Calendar.bot_id == self.ctx.bot_id, Calendar.channel_id == channel_id))
                if int(count or 0) >= (await self.ctx.settings.get()).max_calendars_per_channel:
                    raise ContentError("limit")
                row = Calendar(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=channel_id, name=name, timezone=timezone, slots=normalized)
                session.add(row)
            else:
                row.name, row.timezone, row.slots, row.generation = name, timezone, normalized, row.generation + 1
            await session.commit()
            return row

    async def planned(self, session, batch: Batch, start: datetime, calendar_id: str | None) -> list[datetime]:
        items = list((await session.scalars(select(BatchItem).where(BatchItem.bot_id == self.ctx.bot_id,
            BatchItem.batch_id == batch.id, BatchItem.active.is_(True)).order_by(BatchItem.position))).all())
        if not items:
            raise ContentError("content")
        if calendar_id:
            calendar = await session.get(Calendar, (self.ctx.bot_id, calendar_id), with_for_update=True)
            if calendar is None or calendar.channel_id != batch.channel_id:
                raise ContentError("targets")
            occupied = set((await session.scalars(select(CalendarReservation.run_at).where(
                CalendarReservation.bot_id == self.ctx.bot_id, CalendarReservation.calendar_id == calendar.id,
                CalendarReservation.run_at >= start))).all())
            return calendar_times(calendar.slots, calendar.timezone, start, len(items), occupied)
        return [start + timedelta(seconds=index) for index in range(len(items))]

    async def preview(self, batch_id: str, user_id: int, *, start: datetime, calendar_id: str | None = None) -> list[datetime]:
        row = await self.get(batch_id, user_id)
        async with self.ctx.sm() as session:
            return await self.planned(session, row, start, calendar_id)

    async def schedule(self, batch_id: str, user_id: int, generation: int, *, start: datetime | None = None,
                       calendar_id: str | None = None, expected: list[datetime] | None = None,
                       expected_posts: dict[str, int] | None = None) -> Batch:
        initial = await self.get(batch_id, user_id)
        when = start or utcnow()
        if when.tzinfo is None or (calendar_id is None and start is not None and start <= utcnow()):
            raise ContentError("time")
        items = await self.items(batch_id, user_id)
        # Authorize every immutable payload before taking scheduling locks.
        for item in items:
            view = await self.posts.view(item.post_id, user_id, "edit")
            if view.post.target_ids != [initial.channel_id]:
                raise ContentError("targets")
            await self.posts.authorize_targets(view, user_id)
            await self.posts.validate_buttons(view.spec, user_id)
        async with self.ctx.sm() as session:
            row = await self.locked(session, batch_id, user_id, generation)
            if row.status not in {"collecting", "ready"}:
                raise ContentError("batch_queued")
            times = await self.planned(session, row, max(when, utcnow()) if calendar_id else when, calendar_id)
            if calendar_id and (expected is None or times != expected):
                raise ContentError("stale_plan")
            fresh_items = list((await session.scalars(select(BatchItem).where(BatchItem.bot_id == self.ctx.bot_id,
                BatchItem.batch_id == batch_id, BatchItem.active.is_(True)).order_by(BatchItem.position))).all())
            for item, run_at in zip(fresh_items, times, strict=True):
                post = await session.get(Post, (self.ctx.bot_id, item.post_id), with_for_update=True)
                assert post is not None
                post = await self.posts.locked(session, post.id, post.generation)
                if expected_posts is not None and expected_posts.get(post.id) != post.generation:
                    raise ContentError("stale_plan")
                if post.detached or post.target_ids != [row.channel_id] or await self.posts.deliveries(session, post):
                    raise ContentError("batch_queued")
                post.generation += 1
                await self.posts.queue(session, post, user_id, run_at)
                if calendar_id:
                    session.add(CalendarReservation(bot_id=self.ctx.bot_id, calendar_id=calendar_id, run_at=run_at, post_id=post.id))
                self.posts.audit(session, post, user_id, "batch.scheduled")
            row.status, row.generation = "queued", row.generation + 1
            await session.commit()
            return row

    async def cancel(self, batch_id: str, user_id: int, generation: int) -> None:
        await self.get(batch_id, user_id)
        async with self.ctx.sm() as session:
            batch = await self.locked(session, batch_id, user_id, generation)
            items = (await session.scalars(select(BatchItem).where(BatchItem.bot_id == self.ctx.bot_id,
                BatchItem.batch_id == batch_id, BatchItem.active.is_(True)).order_by(BatchItem.post_id))).all()
            for item in items:
                post = await session.get(Post, (self.ctx.bot_id, item.post_id), with_for_update=True)
                assert post is not None
                post = await self.posts.locked(session, post.id, post.generation)
                await self.posts.cancel_ops(session, post)
                targets = await self.posts.deliveries(session, post)
                post.generation += 1
                if not targets:
                    post.detached = True
                for target in targets:
                    if target.state in {"pending", "held", "failed"}:
                        target.state = "cancelled"
                schedule = await session.get(PostSchedule, (self.ctx.bot_id, post.id))
                if schedule:
                    schedule.status = "cancelled"
                if not any(target.state in {"sent", "uncertain", "deleted"} for target in targets):
                    await session.execute(delete(CalendarReservation).where(CalendarReservation.bot_id == self.ctx.bot_id,
                        CalendarReservation.post_id == post.id))
            batch.status, batch.generation = "cancelled", batch.generation + 1
            await session.commit()
