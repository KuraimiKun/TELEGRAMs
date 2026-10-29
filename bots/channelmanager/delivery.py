"""One Telegram side effect per durable operation; publish and follow-up results remain separate."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)
from aiogram.methods import DeleteMessage, EditMessageReplyMarkup, PinChatMessage, SendMessage
from aiogram.methods.base import TelegramMethod
from aiogram.types import Message
from sqlalchemy import and_, exists, or_, select

from bots.channelmanager import outbox
from bots.channelmanager.content import PostSpec
from bots.channelmanager.models import (
    Channel,
    Delivery,
    Operation,
    Post,
    PostSchedule,
    PostVersion,
    VirtualGrant,
)
from bots.channelmanager.permissions import (
    AccessDenied,
    bot_post_rights,
    operator_rights,
    post_rights,
    publishing_access,
)
from core.db.base import utcnow
from core.db.models import BotUser
from core.sdk.context import BotContext

FIELDS = {"publish": "publish_op", "edit": "edit_op", "pin": "pin_op", "delete": "delete_op", "delete_reminder": "delete_op", "markup": "markup_op"}


async def schedule_state(session, ctx: BotContext, post_id: str) -> None:
    schedule = await session.get(PostSchedule, (ctx.bot_id, post_id))
    if schedule is None or schedule.status != "pending":
        return
    states = set((await session.scalars(select(Delivery.state).where(Delivery.bot_id == ctx.bot_id,
                                                                   Delivery.post_id == post_id))).all())
    if "pending" not in states:
        schedule.status = "held" if "held" in states else "fired"


async def complete(ctx: BotContext, op: Operation, job: outbox.PostJob, status: str, *, code: str | None = None,
                   result: Any = None, delay: int = 0, refund_attempt: bool = False, held: bool = False,
                   reminder: bool = False) -> None:
    if op.delivery_id != job.delivery_id:
        await outbox.finish(ctx, op, "failed", code="delivery_mismatch")
        return
    async with ctx.sm() as session:
        # Consistent lock order with operator mutations: post, delivery, operation.
        delivery = await session.get(Delivery, (ctx.bot_id, job.delivery_id))
        if delivery is None:
            await outbox.finish(ctx, op, "failed", code="invalid_delivery", session=session)
            await session.commit()
            return
        post = await session.get(Post, (ctx.bot_id, delivery.post_id), with_for_update=True)
        delivery = await session.get(Delivery, (ctx.bot_id, job.delivery_id), with_for_update=True, populate_existing=True)
        if delivery is None:
            return
        message_id = result.message_id if isinstance(result, Message) else None
        if not await outbox.finish(ctx, op, status, code=code, delay=delay, refund_attempt=refund_attempt,
                                   message_id=message_id, session=session):
            return
        if getattr(delivery, FIELDS[op.kind]) != op.id:
            await session.commit()
            return
        previous_version = delivery.version if op.kind == "edit" else None
        if op.kind == "publish":
            delivery.state = "sent" if status == "succeeded" else "held" if held else (
                "pending" if status == "pending" else status)
            delivery.error_code = code
            if status == "succeeded":
                delivery.message_id, delivery.sent_at, delivery.version = result.message_id, result.date, job.version
        else:
            name = "delete_status" if op.kind in {"delete", "delete_reminder"} else f"{op.kind}_status"
            setattr(delivery, name, "reminder" if reminder and status == "succeeded" else status)
            if status == "succeeded" and op.kind == "edit":
                delivery.version = job.version
            if status == "succeeded" and op.kind == "delete" and not reminder:
                delivery.state = "deleted"
        if status == "succeeded" and op.kind in {"publish", "edit"} and post and not post.detached:
            version = await session.get(PostVersion, (ctx.bot_id, post.id, job.version))
            assert version is not None
            spec = PostSpec.model_validate(version.spec)
            channel = await session.get(Channel, (ctx.bot_id, delivery.channel_id))
            assert channel is not None
            if channel.status != "disconnected":
                from bots.channelmanager.interactions import published
                await published(session, ctx, delivery, spec, job.actor_id, previous_version)
                if op.kind == "publish":
                    from bots.channelmanager.recurring import replace_previous
                    await replace_previous(session, ctx, delivery, job.actor_id)
            if spec.pin and delivery.pin_status != "succeeded":
                delivery.pin_status = "cancelled" if channel.status == "disconnected" else "pending"
                if channel.status != "disconnected":
                    delivery.pin_op = await outbox.enqueue(session, ctx, channel, kind="pin",
                        dedupe_key=f"pin:{delivery.id}:{job.version}", payload={"delivery_id": delivery.id,
                            "version": job.version, "actor_id": job.actor_id, "automatic": False})
            if op.kind == "publish" and spec.delete_after_seconds:
                assert delivery.sent_at is not None
                delivery.delete_status = "cancelled" if channel.status == "disconnected" else "pending"
                if channel.status != "disconnected":
                    delivery.delete_op = await outbox.enqueue(session, ctx, channel,
                        kind="delete_reminder" if spec.delete_after_seconds >= 172800 else "delete",
                        dedupe_key=f"autodelete:{delivery.id}", run_at=delivery.sent_at + timedelta(seconds=spec.delete_after_seconds),
                        payload={"delivery_id": delivery.id, "version": job.version, "actor_id": job.actor_id, "automatic": True})
        await session.flush()
        await schedule_state(session, ctx, delivery.post_id)
        await session.commit()
    if status == "succeeded" and op.kind == "publish":
        from bots.channelmanager.recurring import settle_replacements
        await settle_replacements(ctx, target_id=job.delivery_id)


async def execute(ctx: BotContext, op: Operation) -> None:
    try:
        job = outbox.PostJob.model_validate(op.payload)
        if job.delivery_id != op.delivery_id:
            raise ValueError("delivery_mismatch")
        async with ctx.sm() as session:
            target = await session.get(Delivery, (ctx.bot_id, job.delivery_id))
            if target is None or target.channel_id != op.channel_id:
                raise ValueError("delivery_mismatch")
            post = await session.get(Post, (ctx.bot_id, target.post_id))
            version = await session.get(PostVersion, (ctx.bot_id, target.post_id, job.version))
            schedule = await session.get(PostSchedule, (ctx.bot_id, target.post_id))
            recipient_user = await session.get(BotUser, (ctx.bot_id, job.actor_id))
            recipient_lang = ctx.translator.resolve(recipient_user.lang if recipient_user else None)
            if post is None or version is None:
                raise ValueError("invalid_post")
            spec = PostSpec.model_validate(version.spec)
        if post.detached or getattr(target, FIELDS[op.kind]) != op.id:
            await complete(ctx, op, job, "cancelled", code="stale_operation")
            return
        if op.kind in {"publish", "edit"} and post.generation != target.generation:
            await complete(ctx, op, job, "cancelled", code="stale_generation")
            return
        if op.kind == "markup" and target.version != job.version:
            await complete(ctx, op, job, "cancelled", code="stale_version")
            return
        if op.kind == "publish":
            scheduled_job = job.scheduled or ("scheduled" not in op.payload and schedule and schedule.run_at > op.created_at + timedelta(seconds=1))
            if scheduled_job:
                from bots.channelmanager.billing import schedule_allowed
                async with ctx.sm() as session:
                    eligible = await schedule_allowed(ctx, target.channel_id, target.id, session=session)
                if not eligible:
                    await complete(ctx, op, job, "cancelled", code="plan_limit", held=True)
                    return
            grace = (await ctx.settings.get()).schedule_lateness_grace_seconds
            if schedule and (utcnow() - schedule.run_at).total_seconds() > grace:
                await complete(ctx, op, job, "cancelled", code="schedule_late", held=True)
                return
        reminder = op.kind == "delete_reminder" or (op.kind == "delete" and target.sent_at is not None and (
            utcnow() - target.sent_at).total_seconds() >= 172800)
        delegated_generation = None
        if op.kind != "delete_reminder" and not (job.automatic and op.kind in {"delete", "markup"}):
            rights = await post_rights(ctx, target.channel_id, job.actor_id, post.creator_id,
                                      "delete" if op.kind == "delete" else "publish" if op.kind == "publish" else "edit")
            delegated_generation = rights.get("_grant_generation")
            if rights.get("_virtual") and (job.grant_generation != delegated_generation):
                raise AccessDenied("delegation_changed")
            if job.scheduled:
                await publishing_access(ctx, target.channel_id, job.actor_id, action="schedule")
            if (post.source_key or "").startswith("auto:"):
                rights = await operator_rights(ctx, target.channel_id, job.actor_id)
            if (post.source_key or "").startswith("auto:") and not rights[
                    "can_delete_messages" if op.kind == "delete" else "can_edit_messages"]:
                raise AccessDenied("manual_source_right")
            if op.kind == "pin" and not rights["can_edit_messages"]:
                raise AccessDenied("pin_right")
        if not reminder:
            await bot_post_rights(ctx, target.channel_id, op.kind)
            if op.kind == "delete" and (post.source_key or "").startswith("auto:"):
                member = await ctx.bot.get_chat_member(target.channel_id, ctx.bot_id)
                if not getattr(member, "can_delete_messages", False):
                    raise AccessDenied("bot_cannot_delete_source")
        if op.kind in {"publish", "edit"}:
            await ctx.extras["posts"].validate_buttons(spec, job.actor_id)
        recipient = job.actor_id if reminder else target.channel_id
        try:
            wait = await outbox.reserve_budget(ctx, recipient)
        except Exception:
            await complete(ctx, op, job, "pending", code="rate_store_unavailable", delay=5, refund_attempt=True)
            return
        if wait:
            await complete(ctx, op, job, "pending", code="local_rate", delay=wait, refund_attempt=True)
            return
        checks = [exists().where(Post.bot_id == ctx.bot_id, Post.id == post.id, Post.detached.is_(False))]
        if delegated_generation is not None:
            checks.append(exists().where(VirtualGrant.bot_id == ctx.bot_id, VirtualGrant.channel_id == target.channel_id,
                VirtualGrant.user_id == job.actor_id, VirtualGrant.active.is_(True), VirtualGrant.generation == delegated_generation))
        if op.kind in {"publish", "edit"}:
            checks.append(exists().where(Post.bot_id == ctx.bot_id, Post.id == post.id, Post.generation == target.generation))
        if op.kind == "markup":
            checks.append(exists().where(Delivery.bot_id == ctx.bot_id, Delivery.id == target.id, Delivery.version == job.version))
        checks.append(exists().where(Delivery.bot_id == ctx.bot_id, Delivery.id == target.id,
                                     getattr(Delivery, FIELDS[op.kind]) == op.id))
        method: TelegramMethod[Any]
        if reminder:
            text = ctx.translator.get(recipient_lang, "chm-delete-reminder", channel=str(target.channel_id), id=str(target.message_id))
            method = SendMessage(chat_id=recipient, text=text, parse_mode="HTML")
        elif op.kind == "publish":
            method = spec.send_method(target.channel_id, markup=spec.keyboard(delivery_id=target.id, version=job.version))
        elif op.kind == "edit":
            assert target.message_id is not None
            from bots.channelmanager.interactions import keyboard
            method = spec.edit_method(target.channel_id, target.message_id, markup=await keyboard(ctx, target, spec, job.version))
        elif op.kind == "markup":
            assert target.message_id is not None
            from bots.channelmanager.interactions import keyboard
            method = EditMessageReplyMarkup(chat_id=target.channel_id, message_id=target.message_id,
                reply_markup=await keyboard(ctx, target, spec, job.version))
        elif op.kind == "pin":
            assert target.message_id is not None
            method = PinChatMessage(chat_id=target.channel_id, message_id=target.message_id, disable_notification=True)
        else:
            assert target.message_id is not None
            method = DeleteMessage(chat_id=target.channel_id, message_id=target.message_id)
        if not await outbox.mark_dispatched(ctx, op, require_generation=op.kind in {"publish", "edit", "pin", "markup"}, conditions=checks):
            await complete(ctx, op, job, "cancelled", code="stale_generation", held=op.kind == "publish")
            return
        op.dispatched = True
        result = await ctx.bot(method, request_timeout=30)
        if op.kind == "publish" and not isinstance(result, Message):
            raise ValueError("invalid_send_result")
        if op.kind == "edit" and result is not True and not isinstance(result, Message):
            raise ValueError("invalid_edit_result")
    except asyncio.CancelledError:
        raise
    except outbox.DispatchBusy:
        await complete(ctx, op, job, "pending", code="delivery_busy", delay=1, refund_attempt=True)
    except TelegramRetryAfter as exc:
        await complete(ctx, op, job, "pending" if op.attempts < op.max_attempts else "failed",
                       code="TelegramRetryAfter", delay=max(1, exc.retry_after))
    except (TelegramNetworkError, TelegramServerError, TimeoutError):
        await complete(ctx, op, job, "uncertain" if op.dispatched else "failed", code="delivery_unknown")
    except TelegramBadRequest as exc:
        if op.kind in {"edit", "markup"} and "message is not modified" in exc.message.lower():
            await complete(ctx, op, job, "succeeded", code="already_current")
        else:
            await complete(ctx, op, job, "failed", code="TelegramBadRequest")
    except AccessDenied as exc:
        await complete(ctx, op, job, "cancelled" if op.kind == "publish" else "failed", code=str(exc), held=op.kind == "publish")
    except TelegramForbiddenError as exc:
        await complete(ctx, op, job, "failed", code=type(exc).__name__)
    except Exception:
        if "job" not in locals():
            await outbox.finish(ctx, op, "failed", code="invalid_operation")
        else:
            await complete(ctx, op, job, "uncertain" if op.dispatched else "failed", code="invalid_operation")
    else:
        await complete(ctx, op, job, "succeeded", result=result, reminder=reminder)


async def reconcile(ctx: BotContext, limit: int = 100) -> None:
    """Reflect lease recovery and external channel invalidation in destination reports."""
    unresolved = []
    for kind in ("publish", "edit", "pin", "delete", "markup"):
        waiting = Delivery.state == "pending" if kind == "publish" else getattr(Delivery, f"{kind}_status").in_({"pending", "running"})
        unresolved.append(and_(waiting, exists().where(Operation.bot_id == Delivery.bot_id,
            Operation.id == getattr(Delivery, FIELDS[kind]), Operation.status.in_({"failed", "uncertain", "cancelled"}))))
    async with ctx.sm() as session:
        rows = (await session.execute(select(Delivery.id, Delivery.post_id).where(Delivery.bot_id == ctx.bot_id,
            or_(*unresolved))
            .order_by(Delivery.created_at).limit(limit))).all()
    for delivery_id, post_id in rows:
        async with ctx.sm() as session:
            await session.get(Post, (ctx.bot_id, post_id), with_for_update=True)
            row = await session.get(Delivery, (ctx.bot_id, delivery_id), with_for_update=True)
            if row is None:
                continue
            for kind in ("publish", "edit", "pin", "delete", "markup"):
                operation_id = getattr(row, FIELDS[kind])
                if not operation_id:
                    continue
                operation = await session.get(Operation, (ctx.bot_id, operation_id))
                if operation and operation.status in {"failed", "uncertain", "cancelled"}:
                    if kind == "publish" and row.state == "pending":
                        row.state, row.error_code = operation.status, operation.error_code
                    elif kind != "publish" and getattr(row, f"{kind}_status") in {"pending", "running"}:
                        setattr(row, f"{kind}_status", operation.status)
            await session.flush()
            await schedule_state(session, ctx, post_id)
            await session.commit()
