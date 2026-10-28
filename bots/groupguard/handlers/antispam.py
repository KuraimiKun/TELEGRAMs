"""Independent sourced flood/raid policies, frozen authorized activation and visible status."""

from __future__ import annotations

import json
from datetime import timedelta

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bots.groupguard import actions, authz, flood, perms, raids
from bots.groupguard.handlers.content import config_operation
from bots.groupguard.handlers.tools import FALSE, boolean
from bots.groupguard.keyboards import GgCb
from bots.groupguard.operations import execute, operation_for, submit
from bots.groupguard.scope import GroupMessages, target_chat
from core.sdk.context import BotContext


def parsed_seconds(raw: str, low=1, high=30 * 86400) -> int | None:
    value = perms.parse_duration(raw)
    return int(value.total_seconds()) if value is not None and low <= value.total_seconds() <= high else None


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_antispam_settings")
    router.message.filter(GroupMessages())
    svc = ctx.extras["guard"]

    @router.message(Command("flood", "antiflood", "setflood", "setfloodtimer", "setfloodmode", "clearflood"))
    async def flood_settings(message: Message, command: CommandObject):
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        name, args = command.command, (command.args or "").strip().lower()
        patch: dict = {}
        if name == "antiflood" and args:
            await message.reply(t("gg-setting-invalid"))
            return
        if name in {"flood", "antiflood"} or not args:
            duration = flood.duration(cfg)
            await message.reply(
                t(
                    "gg-flood-status",
                    consecutive=str(cfg.flood_consecutive_count),
                    count=str(cfg.flood_count),
                    seconds=str(cfg.flood_seconds),
                    mode=cfg.flood_action,
                    duration=perms.human(duration) if duration else t("gg-duration-permanent"),
                    clear=t("gg-on") if cfg.clear_flood else t("gg-off"),
                )
            )
            return
        if name == "setflood" and args in FALSE:
            patch = {"flood_consecutive_count": 0}
        elif name == "setflood" and args.isdigit() and 1 <= int(args) <= 50:
            patch = {"flood_consecutive_count": int(args)}
        elif name == "setfloodtimer" and args in FALSE:
            patch = {"flood_count": 0}
        elif name == "setfloodtimer":
            parts = args.split()
            seconds = parsed_seconds(parts[1], high=86400) if len(parts) == 2 else None
            if len(parts) == 2 and parts[0].isdigit() and 1 <= int(parts[0]) <= 50 and seconds is not None:
                patch = {"flood_count": int(parts[0]), "flood_seconds": seconds}
        elif name == "clearflood":
            value = boolean(args)
            if value is not None:
                patch = {"clear_flood": value}
        elif name == "setfloodmode":
            parts = args.split()
            chosen = parts[0]
            silent = chosen.startswith("s")
            if silent:
                chosen = chosen[1:]
            seconds = parsed_seconds(parts[1], low=60, high=365 * 86400) if len(parts) == 2 else None
            temporary = chosen in {"tban", "tmute"}
            if chosen in {"kick", "ban", "mute", "tban", "tmute"} and (
                (temporary and seconds is not None) or (not temporary and len(parts) == 1)
            ):
                if silent and (not cfg.silent_actions_allowed or cfg.log_chat_id is None):
                    await message.reply(t("gg-silent-consent-required"))
                    return
                patch = {
                    "flood_action": chosen.removeprefix("t"),
                    "flood_duration_seconds": seconds,
                    "flood_legacy_duration": False,
                    "flood_silent": silent,
                }
        if not patch:
            await message.reply(t("gg-setting-invalid"))
            return
        await config_operation(ctx, message, patch, "gg-setting-saved", setting=name)

    @router.message(Command("antiraid", "raidtime", "raidactiontime", "autoantiraid"))
    async def raid_settings(message: Message, command: CommandObject):
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        name, args = command.command, (command.args or "").strip().lower()
        if not args:
            current = await raids.state(ctx, target_chat(message).id)
            enabled = raids.active(current)
            generation = current.generation if current is not None else None
            kb = (
                None
                if enabled
                else InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=t("gg-btn-enable-raid"),
                                callback_data=GgCb(
                                    action="ra", chat=target_chat(message).id, arg=generation or "initial"
                                ).pack(),
                            )
                        ]
                    ]
                )
            )
            sent = await message.reply(
                t(
                    "gg-raid-status",
                    active=t("gg-on") if raids.active(current) else t("gg-off"),
                    until=current.deadline.isoformat()
                    if raids.active(current) and current is not None
                    else t("gg-off"),
                    period=perms.human(timedelta(seconds=cfg.raid_seconds)),
                    ban=perms.human(timedelta(seconds=cfg.raid_ban_seconds)),
                    auto=str(cfg.auto_raid_count),
                ),
                reply_markup=kb,
            )
            if kb is not None:
                await authz.bind_message(
                    ctx,
                    sent,
                    target_chat_id=target_chat(message).id,
                    owner_id=None,
                    kind="raid",
                    data=generation or "initial",
                    slot="raid",
                )
            return
        if name == "antiraid":
            seconds = cfg.raid_seconds if args in {"on", "yes", "true"} else parsed_seconds(args, low=60)
            if args in FALSE:
                seconds = None
            elif seconds is None:
                await message.reply(t("gg-setting-invalid"))
                return
            await submit(
                ctx,
                message,
                operation_for(message, "raid_change", duration_seconds=seconds, loud=seconds is not None),
            )
            return
        patch: dict = {}
        if name == "autoantiraid":
            if args in FALSE:
                patch = {"auto_raid_count": 0}
            elif args.isdigit() and 1 <= int(args) <= 10000:
                patch = {"auto_raid_count": int(args)}
        else:
            seconds = parsed_seconds(args, low=60)
            if seconds is not None:
                patch = {"raid_seconds" if name == "raidtime" else "raid_ban_seconds": seconds}
        if not patch:
            await message.reply(t("gg-setting-invalid"))
            return
        await config_operation(ctx, message, patch, "gg-setting-saved", setting=name)

    @router.callback_query(GgCb.filter(F.action == "ra"))
    async def enable_raid(query: CallbackQuery, callback_data: GgCb):
        cfg = await svc.config(callback_data.chat, fresh=True)
        t = actions.group_t(ctx, cfg)
        if not isinstance(query.message, Message) or not await authz.bound_message(
            ctx, query, target_chat_id=callback_data.chat, kind="raid", data=callback_data.arg, slot="raid"
        ):
            await query.answer(t("gg-auth-denied"), show_alert=True)
            return
        from bots.groupguard.operations import Operation

        op = Operation(
            kind="raid_change",
            source_chat_id=query.message.chat.id,
            target_chat_id=callback_data.chat,
            message_id=query.message.message_id,
            chat_title=query.message.chat.title,
            duration_seconds=cfg.raid_seconds,
            loud=True,
            options_json=json.dumps(
                {"expected_generation": None if callback_data.arg == "initial" else callback_data.arg}
            ),
        )
        result = await execute(ctx, authz.actor_from_callback(ctx, query), op)
        await query.answer(
            t("gg-done") if result.primary_completed else t("gg-auth-denied"),
            show_alert=not result.primary_completed,
        )

    return router
