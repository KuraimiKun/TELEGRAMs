"""Administrator settings, public inventories and actor-bound purge endpoints."""
from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, Message, MessageOriginChannel
from redis.exceptions import RedisError

from bots.groupguard import actions, authz, perms
from bots.groupguard.administration import public_admins
from bots.groupguard.contracts import result_of
from bots.groupguard.handlers.content import config_operation
from bots.groupguard.handlers.moderation import warning_duration
from bots.groupguard.operations import operation_authorization, operation_for, submit
from bots.groupguard.reviews import CLAIM
from bots.groupguard.scope import GroupMessages, target_chat
from bots.groupguard.service import GuardService
from bots.groupguard.settings import GuardSettings
from core.sdk.context import BotContext
from core.ui.text import esc

LOG_CATEGORIES = ("settings", "admin", "user", "automated", "reports", "other")
TRUE = {"on", "yes", "true"}
FALSE = {"off", "no", "false"}


def boolean(value: str) -> bool | None:
    return True if value.lower() in TRUE else False if value.lower() in FALSE else None


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_tools")
    router.message.filter(GroupMessages())
    svc: GuardService = ctx.extras["guard"]

    @router.message(Command("warnings", "adminerror", "anonadmin", "reports", "antichannelpin", "cleanlinked",
                            "setwarnlimit", "setwarnmode", "setwarntime", "warntime"))
    async def settings(message: Message, command: CommandObject):
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        args = (command.args or "").strip().lower()
        if command.command == "warnings":
            seconds = warning_duration(cfg)
            await message.reply(t("gg-warning-settings", limit=str(cfg.warn_limit), mode=cfg.warn_action,
                duration=perms.human(timedelta(seconds=seconds)) if seconds else t("gg-duration-permanent"),
                expiry=perms.human(timedelta(seconds=cfg.warn_time_seconds)) if cfg.warn_time_seconds else t("gg-off")))
            return
        patch: dict[str, Any] = {}
        if command.command == "setwarnlimit":
            if args.isdigit() and 1 <= int(args) <= 20:
                patch = {"warn_limit": int(args)}
        elif command.command == "setwarnmode":
            parts = args.split()
            if parts and parts[0] in {"ban", "mute", "kick", "tban", "tmute"}:
                mode = parts[0]
                if mode.startswith("t") and len(parts) == 2:
                    duration = perms.parse_action_duration(parts[1], required=True)
                    if duration.kind == "valid" and duration.value is not None:
                        patch = {"warn_action": mode[1:], "warn_duration_seconds": int(duration.value.total_seconds()), "warn_legacy_duration": False}
                elif len(parts) == 1 and not mode.startswith("t"):
                    patch = {"warn_action": mode, "warn_duration_seconds": None, "warn_legacy_duration": False}
        elif command.command in {"setwarntime", "warntime"}:
            age = perms.parse_duration(args)
            if args in FALSE:
                patch = {"warn_time_seconds": None}
            elif age is not None:
                patch = {"warn_time_seconds": int(age.total_seconds())}
        else:
            if not args:
                await message.reply(t("gg-setting-value", setting=command.command, value=t("gg-on") if getattr(cfg, command.command) else t("gg-off")))
                return
            value = boolean(args)
            if value is not None:
                patch = {command.command: value}
        if not patch:
            await message.reply(t("gg-setting-invalid"))
            return
        await config_operation(ctx, message, patch, "gg-anon-enabled" if patch.get("anonadmin") is True else "gg-setting-saved", setting=command.command)

    @router.message(Command("adminlist", "admincache"))
    async def admins(message: Message, command: CommandObject):
        t = actions.group_t(ctx, await svc.config(target_chat(message).id))
        if command.command == "admincache":
            actor = authz.actor_from_message(ctx, message)
            permission = await authz.authorize(ctx, actor, target_chat_id=target_chat(message).id,
                caller_rights=frozenset({"change_info"}), bot_rights=frozenset())
            if not permission.allowed:
                await message.reply(t("gg-auth-denied"))
                return
            await perms.forget_admins(ctx, target_chat(message).id)
        members = await public_admins(ctx, target_chat(message).id)
        if members is None:
            await message.reply(t("gg-outcome-failed"))
            return
        lines = [actions.mention(member.user.id, member.user.full_name) for member in members]
        chunks: list[str] = []
        chunk: list[str] = []
        for line in lines:
            if len("\n".join([*chunk, line])) > 3000:
                chunks.append("\n".join(chunk))
                chunk = []
            chunk.append(line)
        chunks.append("\n".join(chunk) or "—")
        for part in chunks:
            await message.reply(t("gg-admin-list", admins=part))

    @router.message(Command("approval", "approved", "unapproveall"))
    async def approvals(message: Message, command: CommandObject):
        t = actions.group_t(ctx, await svc.config(target_chat(message).id))
        if command.command == "unapproveall":
            await submit(ctx, message, operation_for(message, "unapproveall"))
            return
        if command.command == "approved":
            arg = (command.args or "1").strip()
            if not arg.isdigit() or not 1 <= int(arg) <= 100000:
                await message.reply(t("gg-setting-invalid"))
                return
            rows = await svc.approvals(target_chat(message).id, int(arg))
            text = "\n".join(f"{row.user_id}: {row.reason or '—'}" for row in rows[:1000]) or "—"
            if len(rows) > 1000:
                text += "\n" + t("gg-next-page", command=f"/approved {int(arg) + 1}")
            if len(rows) > 30 or len(text) > 3000:
                result = await actions.perform("approval_file", lambda: message.answer_document(
                    BufferedInputFile(text.encode(), filename="approved.txt")))
                if not result.completed:
                    await message.reply(t("gg-outcome-failed"))
            else:
                await message.reply(t("gg-approval-list", approvals=esc(text)))
            return
        try:
            target = await perms.resolve_target(ctx, message, command.args or "")
        except perms.TargetError:
            await message.reply(t("gg-target-invalid"))
            return
        user_id = target.user_id if target else message.from_user.id if message.from_user else None
        if user_id is None:
            await message.reply(t("gg-need-target"))
            return
        row = await svc.approval(target_chat(message).id, user_id)
        await message.reply(t("gg-approval-status", user=str(user_id), status=t("gg-on") if row else t("gg-off"), reason=esc(row.reason or "—") if row else "—"))

    @router.message(Command("purgefrom", "purgeto"))
    async def endpoints(message: Message, command: CommandObject):
        t = actions.group_t(ctx, await svc.config(target_chat(message).id))
        actor = authz.actor_from_message(ctx, message)
        reply = message.reply_to_message
        if actor.kind != "human" or actor.human_id is None or reply is None:
            await message.reply(t("gg-purge-reply"))
            return
        op = operation_for(message, "purge")
        permission = await operation_authorization(ctx, actor, op)
        if not permission.allowed:
            await message.reply(t("gg-auth-denied"))
            return
        key = ctx.keys("purge_range", target_chat(message).id, actor.human_id, message.message_thread_id or 0)
        if command.command == "purgefrom":
            try:
                await ctx.redis.set(key, json.dumps({"first": reply.message_id}), ex=600)
            except RedisError:
                await message.reply(t("gg-outcome-failed"))
                return
            await message.reply(t("gg-range-start"))
            return
        try:
            raw = await ctx.redis.get(key)
        except RedisError:
            await message.reply(t("gg-outcome-failed"))
            return
        if not raw:
            await message.reply(t("gg-range-missing"))
            return
        try:
            first, last = int(json.loads(raw)["first"]), reply.message_id
        except (ValueError, TypeError, KeyError):
            await message.reply(t("gg-range-missing"))
            return
        stg = await ctx.settings.get()
        assert isinstance(stg, GuardSettings)
        if not 0 < last - first + 1 <= stg.max_purge:
            await message.reply(t("gg-range-invalid", cap=str(stg.max_purge)))
            return
        try:
            claimed = await ctx.redis.eval(CLAIM, 1, key, raw)  # type: ignore[misc]
        except RedisError:
            await message.reply(t("gg-outcome-failed"))
            return
        if not claimed:
            return
        await submit(ctx, message, operation_for(message, "purge", message_ids=tuple(range(first, last + 1))))

    @router.message(Command("logchannel", "logcategories", "log", "nolog"))
    async def logs(message: Message, command: CommandObject):
        cfg = await svc.config(target_chat(message).id)
        t = actions.group_t(ctx, cfg)
        if command.command in {"logchannel", "logcategories"}:
            await message.reply(t("gg-log-status", destination=str(cfg.log_chat_id or "—"), categories=", ".join(cfg.log_categories)))
            return
        names = (command.args or "").lower().split()
        if names == ["all"]:
            names = list(LOG_CATEGORIES)
        if not names or not set(names) <= set(LOG_CATEGORIES):
            await message.reply(t("gg-setting-invalid"))
            return
        current = set(cfg.log_categories)
        categories = current | set(names) if command.command == "log" else current - set(names)
        await config_operation(ctx, message, {"log_categories": sorted(categories)}, "gg-setting-saved", setting=command.command)

    @router.message(F.forward_origin, F.text == "/setlog")
    async def forwarded_setup(message: Message):
        t = actions.group_t(ctx, await svc.config(target_chat(message).id))
        origin = message.forward_origin
        if not isinstance(origin, MessageOriginChannel):
            await message.reply(t("gg-setlog-usage"))
            return
        key = ctx.keys("log_setup", origin.chat.id, origin.message_id)
        try:
            received = await ctx.redis.get(key)
        except RedisError:
            received = None
        if received is None:
            await message.reply(t("gg-log-unverified"))
            return
        await submit(ctx, message, operation_for(message, "setlog", log_chat_id=origin.chat.id))

    return router


async def linked_controls(ctx: BotContext, message: Message) -> bool:
    target = message if message.is_automatic_forward else message.pinned_message
    if isinstance(target, Message) and target.is_automatic_forward:
        cfg = await ctx.extras["guard"].config(target_chat(message).id, fresh=True)
        if cfg.antichannelpin:
            cap = await authz.internal_authorize(ctx, target_chat(message).id, frozenset({"pin_messages"}))
            result = actions.failure("unpin", cap.code) if not cap.allowed else result_of(await actions.perform(
                "unpin", lambda: ctx.bot.unpin_chat_message(target_chat(message).id, message_id=target.message_id)))
            if not result.primary_completed:
                await actions.announce(ctx, cfg, target_chat(message).id, target_chat(message).title, result, "")
        if cfg.cleanlinked:
            result = await actions.delete(ctx, target_chat(message).id, target.message_id)
            if not result.primary_completed:
                await actions.announce(ctx, cfg, target_chat(message).id, target_chat(message).title, result, "")

        return cfg.cleanlinked and message.is_automatic_forward is True
    return False


def log_setup_router(ctx: BotContext) -> Router:
    router = Router(name="gg_log_setup")

    @router.channel_post(Command("setlog"))
    async def setup(message: Message):
        bot = await perms.fresh_rights(ctx, target_chat(message).id, ctx.bot_id)
        if bot is None or not bot.allows("post_messages"):
            return
        try:
            await ctx.redis.set(ctx.keys("log_setup", target_chat(message).id, message.message_id), "received", ex=86400)
        except RedisError:
            return
        t = ctx.translator.bind(None)
        await message.reply(t("gg-log-forward"))

    return router
