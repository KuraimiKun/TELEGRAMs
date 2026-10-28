"""Existing moderation commands use normalized operations and fresh authorization."""
from __future__ import annotations

from datetime import timedelta
from typing import cast

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from pydantic import ValidationError

from bots.groupguard import actions, authz, durable, perms
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.contracts import ActionResult, StepResult, result_of
from bots.groupguard.keyboards import GgCb
from bots.groupguard.operations import Kind, operation_for, submit
from bots.groupguard.scope import GroupMessages, target_chat
from bots.groupguard.service import GuardService
from core.db.base import utcnow
from core.sdk.context import BotContext
from core.ui.text import esc

GROUPS = F.chat.type.in_({"group", "supergroup"})


def warning_duration(cfg: ChatConfig) -> int | None:
    return cfg.effective_warning_duration()


async def apply_warn(ctx: BotContext, svc: GuardService, cfg: ChatConfig, chat: Chat, user_id: int, name: str,
                     reason: str | None, by_id: int | None, *, ancillary_steps: tuple[StepResult, ...] = (),
                     silent: bool = False, assumed_anonymous: bool = False) -> ActionResult:
    """Serialize warning identities and claim one durable threshold intent per generation."""
    cfg = await svc.config(chat.id, fresh=True)
    cap = await authz.internal_authorize(ctx, chat.id, frozenset({"restrict_members"}))
    if not cap.allowed or (reason is not None and len(reason) > 256):
        return actions.failure("warn", cap.code if not cap.allowed else "reason_long")
    t = actions.group_t(ctx, cfg)
    who = actions.mention(user_id, name)
    duration_seconds = warning_duration(cfg)
    decision = await durable.record_warning(ctx, chat.id, user_id, reason, by_id, limit=cfg.warn_limit,
        action=cfg.warn_action, duration_seconds=duration_seconds, name=name, silent=silent, assumed_anonymous=assumed_anonymous,
        current_expiry_policy=True,
        expires_at=utcnow() + timedelta(seconds=cfg.warn_time_seconds) if cfg.warn_time_seconds is not None else None)
    count = decision.count
    if decision.job_id is not None:
        result = await durable.execute_warning(ctx, decision.job_id)
        return result.with_steps(*ancillary_steps) if result is not None else result_of(
            StepResult("warn", "applied")).with_steps(*ancillary_steps, StepResult("threshold", "skipped", "already_claimed"))
    if count >= cfg.warn_limit:
        result = result_of(StepResult("warn", "applied")).with_steps(*ancillary_steps)
        return result if silent else result.with_steps(await actions.notify(ctx, chat.id, t("gg-warn-pending")))
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
        text=t("gg-btn-unwarn"), callback_data=GgCb(action="unwarn", chat=chat.id, user=user_id, arg=str(decision.warning_id)).pack())]])
    text = t("gg-warned", user=who, count=str(count), limit=str(cfg.warn_limit), reason=esc(reason or "—"))
    if silent:
        return result_of(StepResult("warn", "applied")).with_steps(*ancillary_steps,
            await actions.log_event(ctx, cfg, chat.title, text, category="admin" if by_id is not None else "automated"))
    sent: Message | None = None

    async def send() -> Message:
        nonlocal sent
        sent = await ctx.bot.send_message(chat.id, text, reply_markup=kb)
        return sent

    notice = await actions.perform("notification", send)
    binding = StepResult("warning_binding", "skipped")
    if sent is not None:
        bound = await authz.bind_message(ctx, sent, target_chat_id=chat.id, owner_id=None,
                                         kind="warning", data=f"{user_id}:{decision.warning_id}")
        binding = StepResult("warning_binding", "applied" if bound else "failed", None if bound else "state_failed")
    audit = await actions.log_event(ctx, cfg, chat.title, text, category="admin" if by_id is not None else "automated")
    result = result_of(StepResult("warn", "applied"), primary_count=1).with_steps(*ancillary_steps, notice, binding, audit)
    if sent is not None:
        from bots.groupguard import cleanup
        result = result.with_steps(await cleanup.schedule(ctx,chat.id,sent,"action"))
    if result.status == "partial":
        result = result.with_steps(await actions.notify(ctx, chat.id, t("gg-outcome-ancillary")))
    return result


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_moderation")
    router.message.filter(GroupMessages())
    svc: GuardService = ctx.extras["guard"]

    @router.message(Command("ban", "tban", "dban", "sban", "mute", "tmute", "dmute", "smute",
                            "kick", "dkick", "skick", "kickme", "unban", "unmute", "warn", "dwarn",
                            "swarn", "unwarn", "rmwarn", "resetwarn", "resetwarns", "promote", "demote",
                            "approve", "unapprove"))
    async def restrictions(message: Message, command: CommandObject) -> None:
        cfg = await svc.config(target_chat(message).id)
        t = actions.group_t(ctx, cfg)
        try:
            if command.command == "kickme":
                if command.args or message.sender_chat is not None or message.from_user is None or message.from_user.is_bot:
                    await message.reply(t("gg-target-invalid"))
                    return
                await submit(ctx, message, operation_for(message, "kick", target_id=message.from_user.id,
                    target_name=message.from_user.first_name, self_only=True))
                return
            if command.command in {"dban", "dmute", "dkick", "dwarn"} and message.reply_to_message is None:
                await message.reply(t("gg-purge-reply"))
                return
            target = await perms.resolve_target(ctx, message, command.args or "")
            if target is None:
                await message.reply(t("gg-need-target"))
                return
            kind = {"tban": "ban", "dban": "ban", "sban": "ban", "tmute": "mute", "dmute": "mute",
                "smute": "mute", "dkick": "kick", "skick": "kick", "dwarn": "warn", "swarn": "warn",
                "rmwarn": "unwarn", "resetwarn": "resetwarns", "approve": "approve_user"}.get(
                command.command, command.command)
            duration = None
            reason = target.remaining
            if kind in {"ban", "mute"}:
                parsed, reason = perms.split_action_args(reason, temporary_required=command.command in {"tban", "tmute"})
                if parsed.kind == "invalid":
                    await message.reply(t("gg-duration-invalid"))
                    return
                duration = int(parsed.value.total_seconds()) if parsed.value is not None else None
            op = operation_for(message, cast(Kind, kind), target_id=target.user_id, target_name=target.name, reason=reason,
                               duration_seconds=duration, silent=command.command in {"sban", "smute", "skick", "swarn"},
                               delete_reply=command.command in {"dban", "dmute", "dkick", "dwarn"},
                               reply_id=message.reply_to_message.message_id if message.reply_to_message else None)
        except perms.TargetError:
            await message.reply(t("gg-target-invalid"))
            return
        except ValidationError:
            await message.reply(t("gg-reason-invalid"))
            return
        await submit(ctx, message, op)

    @router.message(Command("warns"))
    async def cmd_warns(message: Message, command: CommandObject) -> None:
        cfg = await svc.config(target_chat(message).id)
        t = actions.group_t(ctx, cfg)
        try:
            target = await perms.resolve_target(ctx, message, command.args or "")
        except perms.TargetError:
            await message.reply(t("gg-target-invalid"))
            return
        if target is None and message.from_user is not None and message.sender_chat is None and not message.from_user.is_bot:
            target = perms.Target(message.from_user.id, message.from_user.first_name, [])
        if target is None:
            return
        warns = await svc.list_warns(target_chat(message).id, target.user_id)
        lines = [t("gg-warns", user=actions.mention(target.user_id, target.name), count=str(len(warns)), limit=str(cfg.warn_limit))]
        lines.extend(t("gg-warning-row", id=str(w.id), reason=esc(w.reason or "—"),
                       expiry=w.expires_at.isoformat() if w.expires_at is not None else t("gg-duration-permanent")) for w in warns)
        text = "\n".join(lines)
        if len(text) > 3500 or len(warns) > 30:
            rows = "\n".join(f"{w.id}\t{w.created_at.isoformat()}\t{w.expires_at.isoformat() if w.expires_at else '-'}\t{w.reason or '-'}" for w in warns)
            step = await actions.perform("warning_file", lambda: message.answer_document(
                BufferedInputFile(rows.encode(), filename="warnings.txt")))
            if not step.completed:
                await message.reply(t("gg-outcome-failed"))
        else:
            await message.reply(text)

    @router.callback_query(GgCb.filter(F.action == "unwarn"))
    async def cb_unwarn(query: CallbackQuery, callback_data: GgCb) -> None:
        t = actions.group_t(ctx, await svc.config(callback_data.chat))
        if not callback_data.arg.isdigit() or not await authz.bound_message(
                ctx, query, target_chat_id=callback_data.chat, kind="warning",
                data=f"{callback_data.user}:{callback_data.arg}") or not isinstance(query.message, Message):
            await query.answer(t("gg-auth-denied"), show_alert=True)
            return
        actor = authz.actor_from_callback(ctx, query)
        authorization = await authz.authorize(ctx, actor, target_chat_id=callback_data.chat,
            caller_rights=frozenset({"restrict_members"}), bot_rights=frozenset({"restrict_members"}))
        protected = await perms.target_error(ctx, callback_data.chat, callback_data.user)
        if not authorization.allowed or protected is not None:
            await query.answer(t("gg-auth-denied"), show_alert=True)
            return
        removed = await svc.remove_warning(callback_data.chat, callback_data.user, int(callback_data.arg))
        result = result_of(StepResult("unwarn", "applied" if removed else "skipped"))
        if removed:
            msg = query.message
            result = result.with_steps(await actions.perform("warning_notice", lambda: msg.edit_text(t("gg-warning-removed"))))
        await ctx.audit.record(query.from_user.id, "gg_unwarn", target=callback_data.chat,
                               warning_id=int(callback_data.arg), outcome=result.status)
        await query.answer(t("gg-warning-removed") if result.primary_completed else t("gg-item-missing"))

    @router.message(Command("purge", "spurge", "del", "pin", "unpin", "unpinall", "permapin"))
    async def messages(message: Message, command: CommandObject) -> None:
        cfg = await svc.config(target_chat(message).id)
        t = actions.group_t(ctx, cfg)
        reply = message.reply_to_message
        if command.command in {"purge", "spurge", "del", "pin"} and reply is None:
            await message.reply(t("gg-pin-reply" if command.command == "pin" else "gg-purge-reply"))
            return
        ids: tuple[int, ...] = ()
        kind = {"del": "delete", "spurge": "purge"}.get(command.command, command.command)
        if kind == "purge" and reply is not None:
            from bots.groupguard.settings import GuardSettings
            stg = await ctx.settings.get()
            assert isinstance(stg, GuardSettings)
            first = reply.message_id
            if (command.args or "").strip():
                if not (command.args or "").isdigit() or not 1 <= int(command.args or "0") <= stg.max_purge:
                    await message.reply(t("gg-range-invalid", cap=str(stg.max_purge)))
                    return
                last = min(message.message_id, first + int(command.args or "0") - 1)
            else:
                last = message.message_id
            if not 0 < last - first + 1 <= stg.max_purge:
                await message.reply(t("gg-range-invalid", cap=str(stg.max_purge)))
                return
            ids = tuple(range(first, last + 1))
        elif command.command == "del" and reply is not None:
            ids = (reply.message_id, message.message_id)
        text = None
        content_fields = {}
        if kind == "permapin":
            from bots.groupguard.content_commands import argument_start, content_of, valid
            from bots.groupguard.formatting import ContentError
            content = content_of(reply) if reply else content_of(message, argument_start(message))
            try:
                valid(content, target_chat(message).id, "pin")
            except ContentError:
                await message.reply(t("gg-content-needed"))
                return
            text = content.raw
            content_fields = dict(content_format=content.format, media_kind=content.media_kind, file_id=content.file_id)
        op = operation_for(message, cast(Kind, kind), reply_id=reply.message_id if reply else None, message_ids=ids, text=text,
                           silent=command.command == "spurge",
                           loud=(command.args or "").strip().lower() in {"loud", "notify"}, **content_fields)
        await submit(ctx, message, op)

    @router.message(Command("report", "admin", "admins"))
    @router.message(F.text.regexp(r"(?i)(?:^|\s)@admin(?:\s|$)"))
    async def cmd_report(message: Message) -> None:
        cfg = await svc.config(target_chat(message).id)
        if not cfg.reports:
            return
        t = actions.group_t(ctx, cfg)
        if message.reply_to_message is None or message.reply_to_message.from_user is None:
            await message.reply(t("gg-report-reply"))
            return
        offender = message.reply_to_message.from_user
        from bots.groupguard.administration import public_admins
        members = await public_admins(ctx, target_chat(message).id)
        if members is None:
            await message.reply(t("gg-outcome-failed"))
            return
        ids = [member.user.id for member in members]
        pings = "".join(f'<a href="tg://user?id={uid}">​</a>' for uid in ids[:20])
        await message.reply_to_message.reply(t("gg-reported", user=actions.mention(offender.id, offender.first_name)) + pings)
        step = await actions.log_event(ctx, cfg, target_chat(message).title,
                                       t("gg-log-report", user=actions.mention(offender.id, offender.first_name)), category="reports")
        if step.status == "failed":
            await actions.notify(ctx, message.chat.id, t("gg-outcome-ancillary"))

    @router.message(Command("setlog", "unsetlog"))
    async def logs(message: Message, command: CommandObject) -> None:
        t = actions.group_t(ctx, await svc.config(target_chat(message).id))
        try:
            destination = int(command.args or "") if command.command == "setlog" else None
            op = operation_for(message, cast(Kind, command.command), log_chat_id=destination)
        except (ValueError, ValidationError):
            await message.reply(t("gg-setlog-usage"))
            return
        await submit(ctx, message, op)

    return router
