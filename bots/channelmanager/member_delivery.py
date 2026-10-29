"""Fenced membership side effects, fresh admission checks and durable cleanup."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any
from urllib.parse import quote

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)
from aiogram.methods import (
    ApproveChatJoinRequest,
    BanChatMember,
    DeclineChatJoinRequest,
    DeleteMessage,
    SendMessage,
    UnbanChatMember,
)
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import exists, select, update

from bots.channelmanager import outbox
from bots.channelmanager.content import ContentError, PostSpec, TextBody
from bots.channelmanager.member_specs import MEMBER_KINDS, MemberSpec
from bots.channelmanager.members import action as enqueue_action
from bots.channelmanager.members import (
    audit,
    head_for,
    is_member,
    lead_for,
    profile,
    rights,
    start_token,
    welcome,
)
from bots.channelmanager.models import (
    Channel,
    JoinRequest,
    MemberAction,
    MemberBan,
    MemberConfig,
    MemberLead,
    Operation,
)
from bots.channelmanager.permissions import AccessDenied, bot_post_rights, operator_rights
from core.db.base import affected, utcnow
from core.db.models import Bot as BotRecord
from core.ui.text import esc


async def required_state(ctx, spec, user_id):
    for index, required in enumerate(spec.required):
        bot = await ctx.bot.get_chat_member(required.chat_id, ctx.bot_id)
        if bot.status != "administrator":
            raise AccessDenied("required_chat_admin")
        if not is_member(await ctx.bot.get_chat_member(required.chat_id, user_id)):
            return index
    return len(spec.required)


async def mark(ctx, op, initial):
    async with ctx.sm() as session:
        from bots.channelmanager.release import operation_allowed
        if not await operation_allowed(ctx, op.kind, session=session, channel_id=op.channel_id):
            return False
        channel_ids = {initial.channel_id}
        if initial.kind == "log":
            channel_ids.add(initial.payload["destination"])
        await session.execute(select(Channel).where(Channel.bot_id == ctx.bot_id, Channel.channel_id.in_(channel_ids))
            .order_by(Channel.channel_id).with_for_update())
        channel = await session.get(Channel, (ctx.bot_id, initial.channel_id))
        if channel is None or channel.status == "disconnected":
            return False
        head = await head_for(session, ctx, initial.channel_id, initial.user_id) if initial.user_id else None
        request = await session.get(JoinRequest, (ctx.bot_id, initial.request_id), with_for_update=True) if initial.request_id else None
        config = await session.get(MemberConfig, (ctx.bot_id, initial.channel_id), with_for_update=True)
        row = await session.get(MemberAction, (ctx.bot_id, initial.id), with_for_update=True)
        if row is None or row.operation_id != op.id or row.status != "pending":
            return False
        if not row.cleanup:
            from bots.channelmanager.senders import allowed
            if not await allowed(ctx, row.channel_id, session=session):
                return False
            manual_decline = row.kind == "decline" and row.payload.get("manual")
            if channel.status != "active" or channel.generation != op.generation or config is None or config.generation != row.generation or (not MemberSpec.model_validate(config.spec).enabled and not manual_decline):
                return False
            if row.kind == "log":
                destination = await session.get(Channel, (ctx.bot_id, row.payload["destination"]))
                if destination is None or destination.status != "active" or destination.generation != row.payload.get("destination_generation"):
                    return False
            if row.kind == "welcome" and request and (head is None or head.request_id != request.id or request.status != "approved"):
                return False
            if request and not manual_decline and request.config_generation != row.generation:
                return False
            if request and row.kind != "welcome" and (head is None or head.request_id != request.id or request.status not in {"pending", "held"}):
                return False
            if row.kind in {"approve", "contact"} and (request is None or request.status != "pending" or utcnow() >= request.expires_at):
                return False
            if row.kind == "approve":
                assert request is not None
                spec = MemberSpec.model_validate(request.spec)
                from bots.channelmanager.billing import limits_for
                if spec.invite_threshold > (await limits_for(ctx, row.channel_id, session=session)).invite_threshold:
                    return False
                from bots.channelmanager.invitations import satisfied
                if not satisfied(request, spec):
                    return False
                if not request.captcha_solved or request.required_index != len(spec.required) or utcnow() < request.approve_after or (spec.mode == "manual" and not request.manual_release):
                    return False
            if row.kind == "ban" and row.payload.get("head_update_id") is not None:
                if head is None or head.generation != row.payload.get("head_generation"):
                    return False
                if head.update_id != row.payload["head_update_id"] and not (head.last_actor_id == ctx.bot_id and head.state == "kicked"):
                    return False
        busy = await session.scalar(select(Operation.id).join(MemberAction, (MemberAction.bot_id == Operation.bot_id) &
            (MemberAction.id == Operation.member_action_id)).where(Operation.bot_id == ctx.bot_id, Operation.id != op.id,
                MemberAction.channel_id == row.channel_id, MemberAction.user_id == row.user_id, Operation.status == "running",
                Operation.dispatched.is_(True), Operation.lease_until > utcnow()).limit(1)) if row.user_id else None
        if busy:
            raise outbox.DispatchBusy
        result = await session.execute(update(Operation).where(*outbox.fence(ctx, op), exists().where(BotRecord.id == ctx.bot_id,
            BotRecord.active.is_(True))).values(dispatched=True))
        await session.commit()
        return affected(result) == 1


async def finish(ctx, op, initial, status, *, code=None, delay=0, refund=False, result=None, required_index=None):
    async with ctx.sm() as session:
        channel = await session.get(Channel, (ctx.bot_id, initial.channel_id), with_for_update=True)
        if channel is None:
            return
        head = await head_for(session, ctx, initial.channel_id, initial.user_id) if initial.user_id else None
        request = await session.get(JoinRequest, (ctx.bot_id, initial.request_id), with_for_update=True) if initial.request_id else None
        config = await session.get(MemberConfig, (ctx.bot_id, initial.channel_id))
        current = await session.get(MemberAction, (ctx.bot_id, initial.id), with_for_update=True)
        if current is None or current.operation_id != op.id:
            return
        if not await outbox.finish(ctx, op, "succeeded" if status == "skipped" else status, code=code, delay=delay,
            refund_attempt=refund, message_id=result.message_id if isinstance(result, Message) else None, session=session):
            return
        current.status, current.error_code = status, code
        if isinstance(result, Message):
            current.remote_id = result.message_id
        if request and required_index is not None:
            request.required_index = required_index
        if status == "uncertain" and request and head and current.kind in {"approve", "decline", "ban"} and head.request_id == request.id:
            request.status, request.error_code = "uncertain", code
        if current.kind in {"welcome", "goodbye", "contact"} and status == "failed" and code == "TelegramForbiddenError" and current.user_id:
            lead = await lead_for(session, ctx, current.channel_id, current.user_id)
            lead.reachable = False
        if request and head and head.request_id == request.id and config:
            if current.kind == "approve" and status in {"succeeded", "skipped"}:
                request.status, request.error_code, head.state = "approved", code, "member"
                await audit(session, ctx, channel, config, "approved", user_id=request.user_id, request=request, code=code)
                await welcome(session, ctx, channel, config, request)
            elif current.kind in {"decline", "ban"} and status == "succeeded":
                request.status = "expired" if current.payload.get("reason") == "expired" else "declined"
                request.error_code = current.payload.get("reason") or current.payload.get("code")
                await audit(session, ctx, channel, config, "expired" if request.status == "expired" else "declined", user_id=request.user_id,
                    request=request, code=request.error_code)
            elif current.kind == "contact" and status in {"failed", "skipped"}:
                await audit(session, ctx, channel, config, "contact_failed", user_id=request.user_id, request=request, code=code)
        if current.kind == "ban":
            ban = await session.scalar(select(MemberBan).where(MemberBan.bot_id == ctx.bot_id, MemberBan.action_id == current.id).with_for_update())
            if ban:
                ban.status = "active" if status == "succeeded" else status
                if status == "succeeded" and config:
                    await audit(session, ctx, channel, config, "banned", user_id=current.user_id, code=current.payload.get("code"))
                    if ban.until_date:
                        await enqueue_action(session, ctx, channel, config, kind="unban", key=f"unban:{ban.id}", user_id=ban.user_id,
                            cleanup=True, run_at=ban.until_date, payload={"ban_id": ban.id, "destination": ban.chat_id, "until_date": ban.until_date.isoformat()})
        if current.kind == "unban" and status in {"succeeded", "skipped"}:
            ban = await session.get(MemberBan, (ctx.bot_id, current.payload["ban_id"]), with_for_update=True)
            if ban:
                ban.status = "released" if status == "succeeded" or code == "already_unbanned" else "review"
            if config:
                await audit(session, ctx, channel, config, "unbanned", user_id=current.user_id, code=code)
        if current.kind == "clean" and status == "failed" and config:
            await audit(session, ctx, channel, config, "cleanup_failed", code=code)
        await session.commit()


async def check_bot(ctx, destination, permission):
    bot = await ctx.bot.get_chat_member(destination, ctx.bot_id)
    if bot.status != "administrator" or not getattr(bot, permission, False):
        raise AccessDenied("bot_member_right")


async def contact_method(ctx, request, spec):
    language = ctx.translator.resolve(request.profile.get("language_code"))
    def t(key, **values):
        return ctx.translator.get(language, key, **values)
    username = ctx.username or (await ctx.bot.get_me()).username
    if not username:
        raise ContentError("sender_username")
    rows = [[InlineKeyboardButton(text=t("chm5-continue"), url=f"https://t.me/{username}?start={start_token(ctx, request)}")]]
    if spec.captcha and not request.captcha_solved:
        data = request.challenge
        from bots.channelmanager.member_interactions import GateCb
        rows += [[InlineKeyboardButton(text=str(value), callback_data=GateCb(r=request.id, g=request.generation, a=index, u=request.user_id).pack())
            for index, value in enumerate(data["choices"])]]
        footer = t("chm5-question", a=str(data["a"]), b=str(data["b"]))
    else:
        from bots.channelmanager.member_interactions import GateCb
        footer = t("chm5-ready")
        rows += [[InlineKeyboardButton(text=t("chm5-check"), callback_data=GateCb(r=request.id, g=request.generation, a=-1, u=request.user_id).pack())]]
    link = None
    if spec.invite_threshold:
        from bots.channelmanager.invitations import active_link
        link = await active_link(ctx, request)
        footer += "\n" + t("chm6-invite-progress", count=str(request.invite_count), required=str(spec.invite_threshold))
        if link:
            rows.insert(0, [InlineKeyboardButton(text=t("chm6-share-invite"), url="https://t.me/share/url?url=" + quote(link, safe=""))])
    if request.required_index < len(spec.required):
        required = spec.required[request.required_index]
        rows.insert(0, [InlineKeyboardButton(text=t("chm5-join-required", number=str(request.required_index + 1)), url=required.url)])
    content = spec.introduction
    if content:
        text, entities = content.render()
        from bots.channelmanager.auto_content import affix, splice
        try:
            body = TextBody(text=text, entities=entities)
            # Splice from right to left so Telegram UTF-16 entity boundaries remain valid.
            import re
            values = {"invite_count": str(request.invite_count), "invite_required": str(spec.invite_threshold), "invite_url": link or ""}
            for match in reversed(list(re.finditer(r"\{(invite_count|invite_required|invite_url)\}", body.text))):
                body = splice(body, match.start(), match.end(), values[match[1]])
            body, _ = affix(body, TextBody(), TextBody(text=footer))
            content = PostSpec.model_validate({**content.model_dump(mode="json"), "body": body.model_dump(mode="json"), "include_signature": False})
        except ValueError:
            content = PostSpec(body=TextBody(text=footer))
        keyboard = content.keyboard()
        rows = [*(keyboard.inline_keyboard if keyboard else []), *rows]
        return content.send_method(request.contact_chat_id, markup=InlineKeyboardMarkup(inline_keyboard=rows))
    return SendMessage(chat_id=request.contact_chat_id, text=footer, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode=None)


async def execute(ctx, op):
    current = None
    try:
        job = outbox.AutoJob.model_validate(op.payload)
        if op.kind not in MEMBER_KINDS or op.member_action_id != job.action_id:
            raise ContentError("member_action_scope")
        async with ctx.sm() as session:
            current = await session.get(MemberAction, (ctx.bot_id, job.action_id))
            if current is None or current.channel_id != op.channel_id or current.operation_id != op.id or op.kind != f"member_{current.kind}":
                raise ContentError("member_action_scope")
            request = await session.get(JoinRequest, (ctx.bot_id, current.request_id)) if current.request_id else None
            config = await session.get(MemberConfig, (ctx.bot_id, current.channel_id))
            lead = await session.get(MemberLead, (ctx.bot_id, current.channel_id, current.user_id)) if current.user_id else None
        if config is None:
            raise ContentError("member_policy")
        spec = MemberSpec.model_validate(request.spec if request else config.spec)
        method: Any
        destination = current.payload.get("destination", current.channel_id)
        if not current.cleanup:
            await rights(ctx, current.channel_id, current.actor_id, restrict=current.kind == "ban")
        if current.kind in {"approve", "decline"}:
            if request is None:
                raise ContentError("stale")
            await check_bot(ctx, current.channel_id, "can_invite_users")
            member = await ctx.bot.get_chat_member(current.channel_id, request.user_id)
            if is_member(member):
                await finish(ctx, op, current, "skipped" if current.kind == "approve" else "cancelled", code="already_member")
                return
            if current.kind == "approve":
                if utcnow() >= request.expires_at:
                    await finish(ctx, op, current, "cancelled", code="expired")
                    return
                latest_profile = profile(member.user)
                if not latest_profile.get("language_code") and request.profile.get("language_code"):
                    latest_profile["language_code"] = request.profile["language_code"]
                rejection = spec.profile.rejects(latest_profile, 1)
                if rejection:
                    await finish(ctx, op, current, "failed", code=rejection)
                    return
                index = await required_state(ctx, spec, request.user_id)
                async with ctx.sm() as session:
                    contacting = await session.scalar(select(MemberAction.id).where(MemberAction.bot_id == ctx.bot_id,
                        MemberAction.request_id == request.id, MemberAction.kind == "contact", MemberAction.status == "pending").limit(1))
                if index != len(spec.required) or contacting:
                    await finish(ctx, op, current, "pending", code="required_membership" if index != len(spec.required) else "waiting_contact",
                        delay=5, refund=True, required_index=index)
                    return
                method = ApproveChatJoinRequest(chat_id=current.channel_id, user_id=request.user_id)
            else:
                method = DeclineChatJoinRequest(chat_id=current.channel_id, user_id=request.user_id)
        elif current.kind == "contact":
            if request is None:
                raise ContentError("stale")
            if spec.invite_threshold:
                async with ctx.sm() as session:
                    from bots.channelmanager.models import MemberInvite
                    invite = await session.scalar(select(MemberInvite).where(MemberInvite.bot_id == ctx.bot_id,
                        MemberInvite.request_id == request.id, MemberInvite.epoch == request.invite_epoch))
                if invite is None or invite.status == "pending":
                    await finish(ctx, op, current, "pending", code="waiting_invite", delay=1, refund=True)
                    return
                if invite.status != "active":
                    await finish(ctx, op, current, "skipped", code="invite_unavailable")
                    return
            if lead and lead.reachable and lead.private_interacted_at and not lead.opted_out:
                request.contact_chat_id = request.user_id
            elif utcnow() >= request.contact_deadline:
                await finish(ctx, op, current, "skipped", code="contact_window_expired")
                return
            method = await contact_method(ctx, request, spec)
            destination = request.contact_chat_id
        elif current.kind in {"welcome", "goodbye"}:
            if lead is None or not lead.private_interacted_at or not lead.reachable or lead.opted_out:
                await finish(ctx, op, current, "skipped", code="no_private_interaction")
                return
            content = PostSpec.model_validate(current.payload["spec"])
            if content.media_bot_id not in {None, ctx.bot_id}:
                raise ContentError("media")
            destination = current.user_id
            method = content.send_method(destination)
        elif current.kind == "log":
            await operator_rights(ctx, destination, current.actor_id)
            await bot_post_rights(ctx, destination, "publish")
            language = current.payload["language"]
            text = ctx.translator.get(language, "chm5-log", channel=str(current.channel_id), user=str(current.user_id or "—"),
                event=ctx.translator.get(language, f"chm5-event-{current.payload['event']}"), code=esc(current.payload.get("code") or "—"))
            method = SendMessage(chat_id=destination, text=current.payload.get("text", text), parse_mode="HTML", disable_notification=True)
        elif current.kind == "clean":
            await check_bot(ctx, destination, "can_delete_messages")
            if (utcnow() - datetime.fromisoformat(current.payload["sent_at"])).total_seconds() >= 172800:
                raise ContentError("cleanup_window_expired")
            method = DeleteMessage(chat_id=destination, message_id=current.payload["message_id"])
        elif current.kind in {"ban", "unban"}:
            await check_bot(ctx, destination, "can_restrict_members")
            if current.kind == "ban" and destination != current.channel_id:
                channel = await ctx.bot.get_chat(current.channel_id)
                actor = await ctx.bot.get_chat_member(destination, current.actor_id)
                if getattr(channel, "linked_chat_id", None) != destination or actor.status not in {"creator", "administrator"} or (
                        actor.status != "creator" and not getattr(actor, "can_restrict_members", False)):
                    raise AccessDenied("linked_group_right")
            member = await ctx.bot.get_chat_member(destination, current.user_id)
            until = datetime.fromisoformat(current.payload["until_date"]) if current.payload.get("until_date") else None
            if current.kind == "unban":
                if until is None:
                    raise ContentError("invalid_unban")
                async with ctx.sm() as session:
                    owned = await session.get(MemberBan, (ctx.bot_id, current.payload["ban_id"]))
                if owned is None or owned.channel_id != current.channel_id or owned.chat_id != destination or owned.user_id != current.user_id or owned.status != "active":
                    raise ContentError("invalid_unban")
                if member.status != "kicked":
                    await finish(ctx, op, current, "skipped", code="already_unbanned")
                    return
                actual = getattr(member, "until_date", None)
                actual_timestamp = actual.timestamp() if isinstance(actual, datetime) else actual
                if actual_timestamp != int(until.timestamp()):
                    await finish(ctx, op, current, "skipped", code="ban_changed")
                    return
                method = UnbanChatMember(chat_id=destination, user_id=current.user_id, only_if_banned=True)
            else:
                if member.status in {"creator", "administrator"}:
                    raise AccessDenied("protected_member_role")
                if until and (until - utcnow()).total_seconds() < 30:
                    await finish(ctx, op, current, "cancelled", code="ban_window_expired")
                    return
                method = BanChatMember(chat_id=destination, user_id=current.user_id, until_date=until)
        else:
            raise ContentError("member_action_scope")
        try:
            delay = await outbox.reserve_budget(ctx, destination)
        except Exception:
            await finish(ctx, op, current, "pending", code="rate_store_unavailable", delay=5, refund=True)
            return
        if delay:
            await finish(ctx, op, current, "pending", code="local_rate", delay=delay, refund=True)
            return
        if not await mark(ctx, op, current):
            await finish(ctx, op, current, "cancelled", code="stale_member_action")
            return
        op.dispatched = True
        result = await ctx.bot(method, request_timeout=30)
        if (current.kind in {"contact", "welcome", "goodbye", "log"} and not isinstance(result, Message)) or (
                current.kind not in {"contact", "welcome", "goodbye", "log"} and result is not True):
            raise ValueError("invalid_member_result")
    except asyncio.CancelledError:
        raise
    except outbox.DispatchBusy:
        if current:
            await finish(ctx, op, current, "pending", code="member_busy", delay=1, refund=True)
    except TelegramRetryAfter as exc:
        if current:
            await finish(ctx, op, current, "pending" if op.attempts < op.max_attempts else "failed", code="TelegramRetryAfter", delay=max(1, exc.retry_after))
    except (TelegramNetworkError, TelegramServerError, TimeoutError):
        if current:
            await finish(ctx, op, current, "uncertain" if op.dispatched else "failed", code="member_delivery_unknown")
    except (TelegramBadRequest, TelegramForbiddenError, AccessDenied, ValueError) as exc:
        if current:
            await finish(ctx, op, current, "failed", code=str(exc) if isinstance(exc, ContentError) else type(exc).__name__)
        else:
            await outbox.finish(ctx, op, "failed", code="invalid_member_action")
    except Exception:
        if current:
            await finish(ctx, op, current, "uncertain" if op.dispatched else "failed", code="invalid_member_action")
        else:
            await outbox.finish(ctx, op, "failed", code="invalid_member_action")
    else:
        await finish(ctx, op, current, "succeeded", result=result)


async def reconcile(ctx, limit=100):
    async with ctx.sm() as session:
        rows = list((await session.scalars(select(MemberAction).join(Operation, (Operation.bot_id == MemberAction.bot_id) &
            (Operation.id == MemberAction.operation_id)).where(MemberAction.bot_id == ctx.bot_id, MemberAction.status == "pending",
                Operation.status.in_({"failed", "uncertain", "cancelled"})).limit(limit))).all())
    for initial in rows:
        async with ctx.sm() as session:
            await session.get(Channel, (ctx.bot_id, initial.channel_id), with_for_update=True)
            head = await head_for(session, ctx, initial.channel_id, initial.user_id) if initial.user_id else None
            request = await session.get(JoinRequest, (ctx.bot_id, initial.request_id), with_for_update=True) if initial.request_id else None
            row = await session.get(MemberAction, (ctx.bot_id, initial.id), with_for_update=True, populate_existing=True)
            op = await session.get(Operation, (ctx.bot_id, row.operation_id)) if row and row.operation_id else None
            if row and op and row.status == "pending" and op.status in {"failed", "uncertain", "cancelled"}:
                row.status, row.error_code = op.status, op.error_code
                if row.kind == "ban":
                    ban = await session.scalar(select(MemberBan).where(MemberBan.bot_id == ctx.bot_id, MemberBan.action_id == row.id).with_for_update())
                    if ban:
                        ban.status = op.status
                if op.status == "uncertain" and request and head and head.request_id == request.id and row.kind in {"approve", "decline", "ban"}:
                    request.status, request.error_code = "uncertain", op.error_code
            await session.commit()
