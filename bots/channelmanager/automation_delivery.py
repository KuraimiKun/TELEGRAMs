"""One fenced Telegram side effect per automation operation, with independent outcomes."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)
from aiogram.methods import (
    DeleteMessage,
    EditMessageCaption,
    ForwardMessage,
    ForwardMessages,
    SendMediaGroup,
    SendMessage,
    SendSticker,
)
from aiogram.types import InputMediaPhoto, InputMediaVideo, Message, MessageId
from sqlalchemy import exists, select, update

from bots.channelmanager import outbox
from bots.channelmanager.auto_content import SourceItem, routed_spec
from bots.channelmanager.automation import (
    AUTO_KINDS,
    CLEANUP,
    destination_rights,
    enqueue_action,
    source_rights,
)
from bots.channelmanager.content import ContentError, PostSpec
from bots.channelmanager.models import (
    AutoAction,
    AutomationControl,
    AutoOutput,
    AutoPart,
    AutoRule,
    AutoSource,
    Channel,
    Delivery,
    ForwardRoute,
    Operation,
    Post,
)
from bots.channelmanager.permissions import AccessDenied, post_rights
from core.db.base import affected, upsert, utcnow
from core.db.models import Bot as BotRecord
from core.db.models import BotUser
from core.sdk.context import BotContext


async def mark(ctx: BotContext, op: Operation, action: AutoAction) -> bool:
    async with ctx.sm() as session:
        from bots.channelmanager.release import operation_allowed
        if not await operation_allowed(ctx, op.kind, session=session, channel_id=op.channel_id):
            return False
        source = await session.get(AutoSource, (ctx.bot_id, action.source_id), with_for_update=True)
        if source is None:
            return False
        if op.delivery_id:
            target = await session.get(Delivery, (ctx.bot_id, op.delivery_id))
            if target is None:
                return False
            post = await session.get(Post, (ctx.bot_id, target.post_id), with_for_update=True)
            await session.get(Delivery, (ctx.bot_id, target.id), with_for_update=True)
            if post is None or post.detached or post.generation != action.payload.get("mirror_generation"):
                return False
            if await session.scalar(select(Operation.id).where(Operation.bot_id == ctx.bot_id, Operation.delivery_id == target.id,
                Operation.id != op.id, Operation.status == "running", Operation.dispatched.is_(True), Operation.lease_until > utcnow()).limit(1)):
                raise outbox.DispatchBusy
        await session.get(AutoAction, (ctx.bot_id, action.id), with_for_update=True)
        channel_ids = {action.channel_id}
        if action.payload.get("destination_type") == "channel":
            channel_ids.add(action.destination_id)
        await session.execute(select(Channel).where(Channel.bot_id == ctx.bot_id, Channel.channel_id.in_(channel_ids))
            .order_by(Channel.channel_id).with_for_update())
        control = await session.get(AutomationControl, (ctx.bot_id, action.channel_id), with_for_update=True)
        checks = [exists().where(BotRecord.id == ctx.bot_id, BotRecord.active.is_(True)),
            exists().where(Channel.bot_id == ctx.bot_id, Channel.channel_id == action.channel_id,
                Channel.status != "disconnected" if op.kind in CLEANUP else Channel.status == "active")]
        if op.kind not in CLEANUP:
            from bots.channelmanager.billing import resource_allowed
            from bots.channelmanager.senders import allowed
            if not await allowed(ctx, action.channel_id, session=session):
                return False
            if action.rule_id and not await resource_allowed(ctx, action.channel_id, "rule", action.rule_id, session=session):
                return False
            if action.route_id and not await resource_allowed(ctx, action.channel_id, "route", action.route_id, session=session):
                return False
            if source.generation != action.version or control is None or control.generation != action.control_generation:
                return False
            checks.append(exists().where(Channel.bot_id == ctx.bot_id, Channel.channel_id == action.channel_id, Channel.generation == op.generation))
            if action.rule_id:
                checks.append(exists().where(AutoRule.bot_id == ctx.bot_id, AutoRule.id == action.rule_id, AutoRule.active.is_(True),
                    AutoRule.generation == action.payload.get("rule_generation")))
            if action.route_id:
                checks.append(exists().where(ForwardRoute.bot_id == ctx.bot_id, ForwardRoute.id == action.route_id, ForwardRoute.active.is_(True),
                    ForwardRoute.generation == action.payload.get("route_generation")))
            if action.payload.get("destination_type") == "channel":
                checks.append(exists().where(Channel.bot_id == ctx.bot_id, Channel.channel_id == action.destination_id,
                    Channel.status == "active", Channel.generation == action.payload.get("destination_generation")))
        # Source edits and route propagation to the same message never overlap.
        others = (await session.scalars(select(AutoAction).join(Operation, (Operation.bot_id == AutoAction.bot_id) &
            (Operation.automation_id == AutoAction.id)).where(AutoAction.bot_id == ctx.bot_id, AutoAction.source_id == action.source_id,
                AutoAction.destination_id == action.destination_id, AutoAction.id != action.id, Operation.status == "running",
                Operation.dispatched.is_(True), Operation.lease_until > utcnow()).limit(1))).first()
        if others:
            raise outbox.DispatchBusy
        changed = await session.execute(update(Operation).where(*outbox.fence(ctx, op), *checks).values(dispatched=True))
        await session.commit()
        return affected(changed) == 1


async def finish(ctx: BotContext, op: Operation, action: AutoAction, status: str, *, code=None, ids: list[int] | None = None,
                 result=None, delay=0, refund=False) -> None:
    async with ctx.sm() as session:
        source = await session.get(AutoSource, (ctx.bot_id, action.source_id), with_for_update=True)
        target = await session.get(Delivery, (ctx.bot_id, op.delivery_id)) if op.delivery_id else None
        post = await session.get(Post, (ctx.bot_id, target.post_id), with_for_update=True) if target else None
        if target:
            target = await session.get(Delivery, (ctx.bot_id, target.id), with_for_update=True, populate_existing=True)
        current = await session.get(AutoAction, (ctx.bot_id, action.id), with_for_update=True)
        if current is None or source is None:
            return
        await session.get(Channel, (ctx.bot_id, action.channel_id), with_for_update=True)
        if not await outbox.finish(ctx, op, status, code=code, delay=delay, refund_attempt=refund,
            message_id=ids[0] if ids else None, session=session):
            return
        current.status = status
        current.error_code = code
        if ids is not None:
            current.remote_ids = ids
        if status == "succeeded" and action.kind == "edit":
            for raw in action.payload.get("items", []):
                item = SourceItem.model_validate(raw)
                part = await session.get(AutoPart, (ctx.bot_id, action.source_id, item.message_id))
                if part:
                    part.affixes = action.payload.get("affixes", {})
            if target and post:
                previous = target.version
                target.version, target.edit_status, target.error_code = action.payload["mirror_version"], "succeeded", None
                from bots.channelmanager.interactions import published
                await published(session, ctx, target, PostSpec.model_validate(action.payload["spec"]), action.actor_id, previous)
        elif target:
            target.edit_status, target.error_code = status, code
        if status in {"succeeded", "uncertain"} and ids and action.kind in {"copy", "forward", "sticker"} and not action.payload.get("prior_ids"):
            for message_id in ids:
                await session.execute(upsert(session, AutoOutput).values(bot_id=ctx.bot_id, chat_id=action.destination_id,
                    message_id=message_id, action_id=action.id).on_conflict_do_nothing())
        if status == "succeeded" and action.kind in {"edit", "sticker"} and action.payload.get("delete_after_seconds"):
            # Existing source messages keep their original send instant.
            sent_at = result.date if action.kind == "sticker" and isinstance(result, Message) else datetime.fromisoformat(action.payload["sent_at"])
            when = sent_at + timedelta(seconds=action.payload["delete_after_seconds"])
            control = await session.get(AutomationControl, (ctx.bot_id, source.channel_id))
            rule = await session.get(AutoRule, (ctx.bot_id, action.rule_id)) if action.rule_id else None
            assert control is not None
            for message_id in ids or []:
                # A newer source version replaces only a never-dispatched timer.
                old = (await session.scalars(select(AutoAction).where(AutoAction.bot_id == ctx.bot_id,
                    AutoAction.source_id == source.id, AutoAction.kind.in_({"delete", "reminder"}),
                    AutoAction.destination_id == action.destination_id))).all()
                already_obligated = False
                for timer in old:
                    if timer.payload.get("message_id") == message_id and timer.operation_id:
                        timer_op = await session.scalar(select(Operation).where(Operation.bot_id == ctx.bot_id,
                            Operation.id == timer.operation_id).with_for_update(skip_locked=True))
                        if timer_op is None or timer_op.status in {"succeeded", "uncertain"} or timer_op.dispatched:
                            already_obligated = True
                        elif timer_op.status in {"pending", "running"}:
                            timer_op.status, timer.status = "cancelled", "cancelled"
                if already_obligated:
                    continue
                await enqueue_action(session, ctx, source, control, key=f"delete:{message_id}", kind="delete", actor=action.actor_id,
                    destination=action.destination_id, rule=rule, payload={"message_id": message_id, "sent_at": sent_at.isoformat(),
                        "own": action.kind == "sticker", "dependencies": []}, run_at=when, version=action.version)
        await session.flush()
        await session.commit()


async def bot_delete_rights(ctx: BotContext, destination_id: int, *, own: bool) -> None:
    member = await ctx.bot.get_chat_member(destination_id, ctx.bot_id)
    if member.status != "administrator":
        raise AccessDenied("bot_not_admin")
    chat = await ctx.bot.get_chat(destination_id)
    if not own and not getattr(member, "can_delete_messages", False):
        raise AccessDenied("bot_cannot_delete_source")
    if own and chat.type == "channel" and not (getattr(member, "can_delete_messages", False) or getattr(member, "can_post_messages", False)):
        raise AccessDenied("bot_cannot_delete")


async def execute(ctx: BotContext, op: Operation) -> None:
    action = None
    ids = None
    try:
        job = outbox.AutoJob.model_validate(op.payload)
        if op.kind not in AUTO_KINDS or op.automation_id != job.action_id:
            raise ValueError("invalid_automation")
        async with ctx.sm() as session:
            action = await session.get(AutoAction, (ctx.bot_id, job.action_id))
            if action is None or action.channel_id != op.channel_id or action.operation_id != op.id or op.kind != f"auto_{action.kind}":
                raise ValueError("action_scope")
            dependencies = list((await session.scalars(select(AutoAction).where(AutoAction.bot_id == ctx.bot_id,
                AutoAction.id.in_(action.payload.get("dependencies", []))))).all())
            source = await session.get(AutoSource, (ctx.bot_id, action.source_id))
            user = await session.get(BotUser, (ctx.bot_id, action.actor_id))
            lang = ctx.translator.resolve(user.lang if user else None)
        if len(dependencies) != len(action.payload.get("dependencies", [])):
            raise ContentError("missing_dependency")
        if any(a.status == "pending" for a in dependencies):
            await finish(ctx, op, action, "pending", code="waiting_dependency", delay=1, refund=True)
            return
        if action.payload.get("require_success") and any(a.status != "succeeded" for a in dependencies):
            await finish(ctx, op, action, "failed", code="source_edit_failed")
            return
        cleanup = op.kind in CLEANUP
        reminder = action.kind == "reminder" or (action.kind == "delete" and (
            utcnow() - datetime.fromisoformat(action.payload["sent_at"])).total_seconds() >= 172800)
        if not cleanup:
            await source_rights(ctx, action.channel_id, action.actor_id)
            if action.destination_id == action.channel_id:
                if action.kind == "edit":
                    await ctx.extras["posts"].validate_buttons(PostSpec.model_validate(action.payload["spec"]), action.actor_id)
                bot = await ctx.bot.get_chat_member(action.channel_id, ctx.bot_id)
                if bot.status != "administrator" or not getattr(bot, "can_edit_messages", False):
                    raise AccessDenied("bot_cannot_edit_source")
            else:
                await destination_rights(ctx, action.destination_id, action.actor_id,
                    action="edit" if action.payload.get("prior_ids") else "send")
                if action.payload.get("prior_ids") and action.payload.get("destination_type") == "channel":
                    await post_rights(ctx, action.destination_id, action.actor_id, action.payload.get("publisher_id", action.actor_id), "edit")
            if source is None or (action.destination_id != source.channel_id and (action.destination_id in source.provenance or len(source.provenance) > action.payload.get("max_hops", 4))):
                raise ContentError("provenance_limit")
        elif not reminder:
            await bot_delete_rights(ctx, action.destination_id, own=bool(action.payload.get("own")))
        recipient = action.actor_id if reminder else action.destination_id
        try:
            delay = await outbox.reserve_budget(ctx, recipient)
        except Exception:
            await finish(ctx, op, action, "pending", code="rate_store_unavailable", delay=5, refund=True)
            return
        if delay:
            await finish(ctx, op, action, "pending", code="local_rate", delay=delay, refund=True)
            return
        items = [SourceItem.model_validate(i) for i in action.payload.get("items", [])]
        method: Any
        if reminder:
            method = SendMessage(chat_id=recipient, text=ctx.translator.get(lang, "chm-delete-reminder",
                channel=str(action.destination_id), id=str(action.payload["message_id"])), parse_mode="HTML")
        elif action.kind == "delete":
            method = DeleteMessage(chat_id=action.destination_id, message_id=action.payload["message_id"])
        elif action.kind == "sticker":
            ref = action.payload["reference"]
            if ref["bot_id"] != ctx.bot_id:
                raise ContentError("media")
            method = SendSticker(chat_id=action.destination_id, sticker=ref["file_id"], disable_notification=True)
        elif action.kind == "forward":
            if any(item.protected for item in items):
                raise ContentError("protected_source")
            if len(items) > 1:
                method = ForwardMessages(chat_id=action.destination_id, from_chat_id=action.channel_id,
                    message_ids=[i.message_id for i in items])
            else:
                method = ForwardMessage(chat_id=action.destination_id, from_chat_id=action.channel_id, message_id=items[0].message_id)
        elif action.kind == "edit":
            spec = PostSpec.model_validate(action.payload["spec"])
            if action.payload.get("album"):
                method = EditMessageCaption(chat_id=action.destination_id, message_id=items[0].message_id,
                    caption=items[0].body.text, caption_entities=items[0].body.entities, parse_mode=None)
            else:
                markup = spec.keyboard(delivery_id=op.delivery_id, version=action.payload.get("mirror_version", 1),
                    channel_id=action.destination_id, message_id=items[0].message_id)
                method = spec.edit_method(action.destination_id, items[0].message_id, markup=markup)
        elif action.kind == "copy":
            if any(item.protected for item in items):
                raise ContentError("protected_source")
            prior = action.payload.get("prior_ids", [])
            if prior:
                if len(items) != 1 or len(prior) != 1:
                    raise ContentError("album_layout_changed")
                value = items[0].model_copy(update={"buttons": []}) if action.payload.get("album") else items[0]
                method = routed_spec(value, ctx.bot_id).edit_method(action.destination_id, prior[0])
            elif len(items) > 1:
                media: list[Any] = []
                for item in items:
                    cls = InputMediaPhoto if item.kind == "photo" else InputMediaVideo if item.kind == "video" else None
                    if cls is None or not item.file_id:
                        raise ContentError("unsupported_album")
                    media.append(cls(media=item.file_id, caption=item.body.text or None, caption_entities=item.body.entities or None, parse_mode=None))
                method = SendMediaGroup(chat_id=action.destination_id, media=media)
            else:
                method = routed_spec(items[0], ctx.bot_id).send_method(action.destination_id)
        else:
            raise ValueError("unknown_action")
        if action.kind in {"copy", "forward"}:
            live_source = await ctx.bot.get_chat(action.channel_id)
            if getattr(live_source, "has_protected_content", False):
                raise ContentError("protected_source")
        if not await mark(ctx, op, action):
            await finish(ctx, op, action, "cancelled", code="stale_automation")
            return
        op.dispatched = True
        result = await ctx.bot(method, request_timeout=30)
        if (action.kind == "edit" or action.payload.get("prior_ids")) and result is not True and not isinstance(result, Message):
            raise ValueError("invalid_edit_result")
        if reminder and not isinstance(result, Message):
            raise ValueError("invalid_reminder_result")
        if action.kind == "delete" and not reminder and result is not True:
            raise ValueError("invalid_delete_result")
        if action.kind in {"copy", "forward", "sticker"} and not action.payload.get("prior_ids"):
            values = result if isinstance(result, list) else [result]
            if not all(isinstance(value, (Message, MessageId)) for value in values):
                raise ValueError("invalid_send_result")
            ids = [value.message_id for value in values]
            if action.kind != "sticker" and len(ids) != len(items):
                await finish(ctx, op, action, "uncertain", code="partial_album_result", ids=ids)
                return
        elif action.kind == "edit":
            ids = [items[0].message_id]
        elif action.payload.get("prior_ids"):
            ids = action.payload["prior_ids"]
    except asyncio.CancelledError:
        raise
    except outbox.DispatchBusy:
        if action:
            await finish(ctx, op, action, "pending", code="delivery_busy", delay=1, refund=True)
    except TelegramRetryAfter as exc:
        if action:
            await finish(ctx, op, action, "pending" if op.attempts < op.max_attempts else "failed", code="TelegramRetryAfter", delay=max(1, exc.retry_after))
    except (TelegramNetworkError, TelegramServerError, TimeoutError):
        if action:
            await finish(ctx, op, action, "uncertain" if op.dispatched else "failed", code="delivery_unknown", ids=ids)
    except TelegramBadRequest as exc:
        if action:
            unchanged = (action.kind == "edit" or action.payload.get("prior_ids")) and "message is not modified" in exc.message.lower()
            await finish(ctx, op, action, "succeeded" if unchanged else "failed", code="already_current" if unchanged else "TelegramBadRequest",
                ids=([action.payload["items"][0]["message_id"]] if action.kind == "edit" else action.payload.get("prior_ids")) if unchanged else None)
    except (ValueError, AccessDenied, TelegramForbiddenError) as exc:
        if action:
            code = str(exc) if isinstance(exc, ContentError) else type(exc).__name__
            await finish(ctx, op, action, "failed", code=code)
        else:
            await outbox.finish(ctx, op, "failed", code="invalid_automation")
    except Exception:
        if action:
            await finish(ctx, op, action, "uncertain" if op.dispatched else "failed", code="invalid_automation", ids=ids)
        else:
            await outbox.finish(ctx, op, "failed", code="invalid_automation")
    else:
        assert action is not None
        await finish(ctx, op, action, "succeeded", ids=ids, result=result, code="manual_reminder" if reminder else None)


async def reconcile(ctx: BotContext, limit=100) -> None:
    async with ctx.sm() as session:
        rows = (await session.execute(select(AutoAction.id, AutoAction.source_id).join(Operation,
            (Operation.bot_id == AutoAction.bot_id) & (Operation.id == AutoAction.operation_id)).where(
                AutoAction.bot_id == ctx.bot_id, AutoAction.status == "pending",
                Operation.status.in_({"failed", "uncertain", "cancelled"})).limit(limit))).all()
    for action_id, source_id in rows:
        async with ctx.sm() as session:
            await session.get(AutoSource, (ctx.bot_id, source_id), with_for_update=True)
            initial = await session.get(AutoAction, (ctx.bot_id, action_id))
            if initial is None:
                continue
            post = await session.get(Post, (ctx.bot_id, initial.payload["mirror_post"]), with_for_update=True) if initial.payload.get("mirror_post") else None
            target = await session.scalar(select(Delivery).where(Delivery.bot_id == ctx.bot_id,
                Delivery.post_id == post.id).with_for_update()) if post else None
            row = await session.get(AutoAction, (ctx.bot_id, action_id), with_for_update=True, populate_existing=True)
            op = await session.get(Operation, (ctx.bot_id, row.operation_id)) if row and row.operation_id else None
            if op and row and row.status == "pending" and op.status in {"failed", "uncertain", "cancelled"}:
                row.status, row.error_code = op.status, op.error_code
                if target and post and post.generation == row.payload.get("mirror_generation") and target.edit_status == "pending":
                    target.edit_status, target.error_code = op.status, op.error_code
            await session.commit()
