"""Typed blocklist management with independent deletion, reasons and entry modes."""

from __future__ import annotations

import json
import re

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, Message

from bots.groupguard import actions, perms
from bots.groupguard.blocklist_matcher import tokens
from bots.groupguard.blocklist_types import MODES, trigger
from bots.groupguard.content_commands import triggers
from bots.groupguard.handlers.content import config_operation
from bots.groupguard.handlers.tools import boolean
from bots.groupguard.operations import operation_for, submit
from bots.groupguard.scope import GroupMessages, target_chat
from core.sdk.context import BotContext
from core.ui.text import esc


def entry_options(raw: str):
    action, seconds, silent = None, None, False
    found = re.search(
        r"\{(nothing|warn|kick|ban|tban|mute|tmute|swarn|skick|sban|smute|stban|stmute)(?:\s+(\S+))?\}\s*$",
        raw,
    )
    if found:
        action = found[1]
        if action.startswith("s"):
            silent = True
            action = action[1:]
        if action in {"tban", "tmute"}:
            parsed = perms.parse_action_duration(found[2] or "", required=True)
            if parsed.kind != "valid" or parsed.value is None:
                raise ValueError("blocklist_duration_invalid")
            seconds = int(parsed.value.total_seconds())
        elif found[2]:
            raise ValueError("blocklist_duration_invalid")
        raw = raw[: found.start()].strip()
    elif "{" in raw or "}" in raw:
        raise ValueError("blocklist_action_invalid")
    return raw, action, seconds, silent


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_blocklists")
    router.message.filter(GroupMessages())
    svc = ctx.extras["guard"]

    @router.message(
        Command(
            "addblocklist", "blocklist", "rmblocklist", "rmblocklistall", "addblock", "rmblock", "unblocklist"
        )
    )
    async def commands(message: Message, command: CommandObject):
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        args = (command.args or "").strip()
        name = command.command
        if name == "rmblocklistall":
            if args != "confirm":
                await message.reply(t("gg-clearall-confirm", command=name))
                return
            await submit(ctx, message, operation_for(message, "blocklist_clear"))
            return
        if not args:
            text = "\n".join(
                entry["key"] + (" — " + entry["reason"] if entry.get("reason") else "")
                for entry in cfg.blocklist_entries
            )
            if len(text) > 3000:
                await message.reply_document(
                    BufferedInputFile(text.encode(), filename="blocklist.txt"),
                    caption=t("gg-blocklist-title"),
                )
            else:
                await message.reply(
                    t("gg-blocklist-title") + "\n<pre>" + esc(text or t("gg-none")) + "</pre>"
                )
            return
        try:
            if (
                name in {"addblock", "rmblock", "unblocklist"}
                and "," in args
                and not args.startswith(("(", '"', "'"))
            ):
                keys = [part.strip().lower() for part in args.split(",") if part.strip()]
                rest = ""
            else:
                keys, used = triggers(args, note=False, max_key=256, preserve_escapes=True)
                rest = args[used:]
            reason, mode, seconds, silent = entry_options(rest)
            records = []
            for key in keys:
                if key == "stickerpack:<>":
                    reply = message.reply_to_message
                    if reply is None:
                        raise ValueError("reply_required")
                    if reply.sticker and reply.sticker.set_name:
                        expanded = ["stickerpack:" + reply.sticker.set_name]
                    else:
                        from bots.groupguard.lock_runtime import emoji_packs

                        packs = await emoji_packs(ctx, reply)
                        if not packs:
                            raise ValueError("pack_unknown")
                        expanded = ["stickerpack:" + pack for pack in set(packs.values())]
                else:
                    expanded = [key]
                for value in expanded:
                    entry = trigger(
                        value, reason=reason, action=mode, duration_seconds=seconds, silent=silent
                    )
                    if entry.kind in {"text", "prefix", "exact", "lookalike", "name", "username", "file"}:
                        tokens(entry.pattern)
                    records.append(entry.model_dump())
            op = operation_for(
                message,
                "blocklist_change",
                options_json=json.dumps(records),
                loud=name in {"addblocklist", "blocklist", "addblock"},
            )
        except ValueError:
            await message.reply(t("gg-blocklist-invalid"))
            return
        await submit(ctx, message, op)

    @router.message(Command("blocklistmode", "blocklistdelete", "setblocklistreason", "resetblocklistreason"))
    async def settings(message: Message, command: CommandObject):
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        args = (command.args or "").strip()
        name = command.command
        patch: dict = {}
        if not args and name != "resetblocklistreason":
            await message.reply(
                t(
                    "gg-blocklist-settings",
                    mode=cfg.blocklist_mode,
                    delete=t("gg-on") if cfg.blocklist_delete else t("gg-off"),
                )
            )
            return
        if name == "blocklistdelete":
            value = boolean(args.lower())
            if value is not None:
                patch = {"blocklist_delete": value}
        elif name == "resetblocklistreason":
            patch = {"blocklist_reason": ""}
        elif name == "setblocklistreason" and len(args) <= 256:
            patch = {"blocklist_reason": args}
        elif name == "blocklistmode":
            pieces = args.split()
            if pieces and pieces[0] in MODES:
                mode = pieces[0]
                seconds = None
                if mode in {"tban", "tmute"} and len(pieces) == 2:
                    parsed = perms.parse_action_duration(pieces[1], required=True)
                    if parsed.kind == "valid" and parsed.value is not None:
                        seconds = int(parsed.value.total_seconds())
                if (mode in {"tban", "tmute"} and seconds is not None) or (
                    mode not in {"tban", "tmute"} and len(pieces) == 1
                ):
                    patch = {
                        "blocklist_mode": mode,
                        "blocklist_duration_seconds": seconds,
                        "blocklist_warn": mode == "warn",
                    }
        if not patch:
            await message.reply(t("gg-setting-invalid"))
            return
        await config_operation(ctx, message, patch, "gg-setting-saved", setting=name)

    return router
