"""Typed lock and evidence-specific allowlist settings with execution-time authorization."""

from __future__ import annotations

import json

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, Message

from bots.groupguard import actions, locks
from bots.groupguard.handlers.content import config_operation
from bots.groupguard.handlers.tools import boolean
from bots.groupguard.lock_types import CANONICAL_LOCKS, expand
from bots.groupguard.operations import operation_for, submit
from bots.groupguard.scope import GroupMessages, target_chat
from core.sdk.context import BotContext
from core.ui.text import esc


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_lock_settings")
    router.message.filter(GroupMessages())
    svc = ctx.extras["guard"]

    @router.message(Command("lock", "unlock", "locktypes", "locks", "lockwarns"))
    async def commands(message: Message, command: CommandObject):
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        name = command.command
        args = (command.args or "").strip()
        if name == "locktypes":
            await message.reply(t("gg-locktypes", types="all, "+", ".join(CANONICAL_LOCKS)))
            return
        if name == "locks":
            configured = set(expand(cfg.locks))
            names = CANONICAL_LOCKS if args == "list" else sorted(configured)
            body = "\n".join(
                f"{'🔒' if kind in configured else '🔓'} <code>{kind}</code> "
                + esc(cfg.lock_policies.get(kind, {}).get("action", "delete"))
                for kind in names
            )
            await message.reply(t("gg-locks-title") + "\n" + (body or t("gg-none")))
            return
        if name == "lockwarns":
            if not args:
                await message.reply(
                    t("gg-setting-value", setting=name, value=t("gg-on") if cfg.lock_warns else t("gg-off"))
                )
                return
            value = boolean(args.lower())
            if value is None:
                await message.reply(t("gg-setting-invalid"))
                return
            await config_operation(ctx, message, {"lock_warns": value}, "gg-setting-saved", setting=name)
            return
        try:
            wanted, policy = locks.policy_arguments(args)
        except ValueError:
            await message.reply(t("gg-lock-usage", types=", ".join(CANONICAL_LOCKS)))
            return
        await submit(
            ctx,
            message,
            operation_for(
                message,
                "lock_change",
                keys=tuple(wanted),
                options_json=policy.model_dump_json(),
                loud=name == "lock",
            ),
        )

    @router.message(Command("allowlist", "rmallowlist", "rmallowlistall"))
    async def allowlist(message: Message, command: CommandObject):
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        args = (command.args or "").strip()
        if command.command == "rmallowlistall":
            if args != "confirm":
                await message.reply(t("gg-clearall-confirm", command=command.command))
                return
            # This operation adds creator to the common frozen operation rights contract.
            await submit(ctx, message, operation_for(message, "allowlist_clear"))
            return
        if not args:
            text = "\n".join(json.dumps(e, ensure_ascii=False, sort_keys=True) for e in cfg.allowlist)
            if len(text) > 3000:
                await message.reply_document(
                    BufferedInputFile(text.encode(), filename="allowlist.txt"),
                    caption=t("gg-allowlist-title"),
                )
            else:
                await message.reply(
                    t("gg-allowlist-title") + "\n<pre>" + esc(text or t("gg-none")) + "</pre>"
                )
            return
        try:
            if args in {"stickerpack:<>", "emojipack:<>"}:
                reply = message.reply_to_message
                if reply is None:
                    raise ValueError("reply_required")
                if args.startswith("stickerpack"):
                    if reply.sticker is None or not reply.sticker.set_name:
                        raise ValueError("pack_unknown")
                    entries = [locks.allow_entry("stickerpack:" + reply.sticker.set_name)]
                else:
                    from bots.groupguard.lock_runtime import emoji_packs

                    packs = await emoji_packs(ctx, reply)
                    if not packs:
                        raise ValueError("pack_unknown")
                    entries = [locks.allow_entry("emojipack:" + pack) for pack in sorted(set(packs.values()))]
            else:
                entries = [locks.allow_entry(part) for part in args.splitlines()]
        except ValueError:
            await message.reply(t("gg-allowlist-invalid"))
            return
        await submit(
            ctx,
            message,
            operation_for(
                message,
                "allowlist_change",
                options_json=json.dumps(entries),
                loud=command.command == "allowlist",
            ),
        )

    return router
