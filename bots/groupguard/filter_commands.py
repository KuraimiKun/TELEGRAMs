"""Publish stored slash filters in the actual group BotCommand scope."""
from __future__ import annotations

import re

from aiogram.types import BotCommand, BotCommandScopeChat

from bots.groupguard import actions
from core.runtime.gateway import command_specs
from core.sdk.context import BotContext

COMMAND = re.compile(r"^[a-z0-9_]{1,32}$")


async def sync(ctx: BotContext, chat_id: int):
    svc = ctx.extras["guard"]
    cfg = await svc.config(chat_id, fresh=True)
    filters = [item for item in await svc.filters(chat_id) if item.options.get("command")]
    scope = BotCommandScopeChat(chat_id=chat_id)
    if not filters:
        return await actions.perform("filter_commands", lambda: ctx.bot.delete_my_commands(scope=scope))
    commands = {}
    for command, key in command_specs(ctx):
        description = ctx.translator.get(cfg.lang or ctx.translator.default, key)
        commands[command] = BotCommand(command=command, description=(description if description != key else command)[:256])
    for item in filters:
        key = item.key.lstrip("/")
        if not COMMAND.fullmatch(key):
            return actions.failure("filter_commands", "invalid_command").steps[0]
        commands[key] = BotCommand(command=key, description=item.options.get("command_description") or key)
    if len(commands) > 100:
        return actions.failure("filter_commands", "command_limit").steps[0]
    return await actions.perform("filter_commands", lambda: ctx.bot.set_my_commands(list(commands.values()), scope=scope))
