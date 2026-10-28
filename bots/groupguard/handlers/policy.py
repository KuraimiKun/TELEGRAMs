"""Disabling, cleanup, automated silence and bot acceptance settings through frozen operations."""

from __future__ import annotations

import json

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bots.groupguard import actions, cleanup, command_metadata
from bots.groupguard.handlers.content import config_operation
from bots.groupguard.handlers.tools import boolean
from bots.groupguard.scope import GroupMessages, target_chat
from core.sdk.context import BotContext
from core.ui.text import esc


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_policy")
    router.message.filter(GroupMessages())
    svc = ctx.extras["guard"]

    @router.message(Command("disabled", "disableable", "disable", "enable", "disabledel", "disableadmin"))
    async def disabling(message: Message, command: CommandObject):
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        name, args = command.command, (command.args or "").lower().split()
        if name in {"disabled", "disableable"}:
            values = cfg.disabled_commands if name == "disabled" else sorted(command_metadata.DISABLEABLE)
            await message.reply(t("gg-disabled-list", commands=esc(", ".join(values) or t("gg-none"))))
            return
        patch: dict = {}
        if name in {"disabledel", "disableadmin"}:
            if not args:
                value = cfg.disabled_delete if name == "disabledel" else cfg.disable_admin
                await message.reply(
                    t("gg-setting-value", setting=name, value=t("gg-on") if value else t("gg-off"))
                )
                return
            value = boolean(args[0]) if len(args) == 1 else None
            if value is not None:
                patch = {"disabled_delete" if name == "disabledel" else "disable_admin": value}
        elif args:
            roots = {value.lstrip("/") for value in args}
            if roots <= command_metadata.DISABLEABLE:
                # Frozen delta preserves intervening edits at execution/review.
                from bots.groupguard.operations import operation_for, submit

                await submit(
                    ctx,
                    message,
                    operation_for(
                        message,
                        "policy_change",
                        options_json=json.dumps(
                            dict(
                                field="disabled_commands",
                                values=sorted({command_metadata.purpose(v) for v in roots}),
                            )
                        ),
                        loud=name == "disable",
                    ),
                )
                return
        if not patch:
            await message.reply(t("gg-setting-invalid"))
            return
        await config_operation(ctx, message, patch, "gg-setting-saved", setting=name)

    @router.message(
        Command(
            "cleancommand",
            "keepcommand",
            "cleancommandtypes",
            "cleanmsg",
            "keepmsg",
            "cleanmsgtypes",
            "cleanservice",
            "nocleanservice",
            "cleanservicetypes",
        )
    )
    async def cleaning(message: Message, command: CommandObject):
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        name = command.command
        family = "command" if "command" in name else "bot" if "msg" in name else "service"
        known = (
            cleanup.COMMAND_TYPES
            if family == "command"
            else cleanup.BOT_TYPES
            if family == "bot"
            else cleanup.SERVICE_TYPES
        )
        field = {
            "command": "command_clean_types",
            "bot": "bot_clean_types",
            "service": "service_clean_types",
        }[family]
        args = (command.args or "").lower().split()
        if name.endswith("types"):
            await message.reply(t("gg-cleanup-types", types=", ".join(sorted(known))))
            return
        if not args:
            selected = getattr(cfg, field)
            if selected is None:
                selected = ["join", "leave"] if cfg.clean_service else []
            await message.reply(t("gg-cleanup-selected", types=", ".join(selected) or t("gg-none")))
            return
        add = name.startswith("clean")
        if args == ["all"] or (family == "service" and len(args) == 1 and boolean(args[0]) is True):
            values = set(known)
        elif family == "service" and len(args) == 1 and boolean(args[0]) is False:
            values = set(known)
            add = False
        else:
            values = set(args)
        if not values <= known:
            await message.reply(t("gg-setting-invalid"))
            return
        from bots.groupguard.operations import operation_for, submit

        await submit(
            ctx,
            message,
            operation_for(
                message,
                "policy_change",
                options_json=json.dumps(dict(field=field, values=sorted(values))),
                loud=add,
            ),
        )

    @router.message(Command("silentactions", "bot2bot", "bot2botskipreview"))
    async def advanced(message: Message, command: CommandObject):
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        name, args = command.command, (command.args or "").strip().lower()
        field = {
            "silentactions": "silent_actions_allowed",
            "bot2bot": "bot2bot_mode",
            "bot2botskipreview": "bot2bot_skip_review",
        }[name]
        if not args:
            await message.reply(t("gg-advanced-status", setting=name, value=str(getattr(cfg, field))))
            return
        value = (
            args
            if name == "bot2bot" and args in {"off", "admin", "all"}
            else boolean(args)
            if name != "bot2bot"
            else None
        )
        if value is None:
            await message.reply(t("gg-setting-invalid"))
            return
        if (
            name == "silentactions"
            and value
            and (cfg.log_chat_id is None or "automated" not in cfg.log_categories)
        ):
            await message.reply(t("gg-silent-consent-required"))
            return
        await config_operation(ctx, message, {field: value}, "gg-setting-saved", setting=name)

    return router
