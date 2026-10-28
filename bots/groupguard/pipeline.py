"""Actual source messages with scoped connected targets, common command policy and post-processing."""

from __future__ import annotations

import hashlib

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from redis.exceptions import RedisError

from bots.groupguard import actions, authz, cleanup, command_metadata, connections, perms, policies, scope
from bots.groupguard.protect import ProtectMiddleware
from core.sdk.context import BotContext

# These private commands keep their own platform/owner context even with a chat connection.
NEUTRAL_PM = frozenset(
    {
        "admin",
        "admins",
        "lang",
        "language",
        "connect",
        "reconnect",
        "connection",
        "disconnect",
        "privacy",
        "help",
        "broadcast",
        "newfed",
        "renamefed",
        "delfed",
        "fedpromote",
        "feddemote",
        "feddemoteme",
        "fedreason",
        "fednotif",
        "setfedlog",
        "unsetfedlog",
        "fedinfo",
        "fedadmins",
        "myfeds",
        "fban",
        "unfban",
        "fedstat",
        "fbanstat",
        "fbanlist",
        "importfbans",
        "subfed",
        "unsubfed",
        "fedsubs",
    }
)


class CommandPolicy(BaseMiddleware):
    def __init__(self, ctx: BotContext):
        self.ctx = ctx

    async def __call__(self, handler, event: TelegramObject, data):
        if not isinstance(event, Message) or event.chat.type not in {"private", "group", "supergroup"}:
            return await handler(event, data)
        ctx = self.ctx
        actor = authz.actor_from_message(ctx, event)
        parsed = command_metadata.parse(event)
        group = event.chat if event.chat.id < 0 else None
        if event.chat.type == "private" and actor.kind == "bot" and parsed is not None:
            return None  # Private human/owner flows cannot be acquired by a bot sender.
        if (
            group is None
            and event.chat.type == "private"
            and actor.kind == "human"
            and actor.human_id == event.chat.id
            and parsed is not None
            and parsed.name in command_metadata.REGISTRY
            and parsed.name not in NEUTRAL_PM
        ):
            group = await connections.current(ctx, actor.human_id)
            if group is None:
                return await handler(event, data)
            if not command_metadata.REGISTRY[parsed.name].pm:
                await event.reply(
                    ctx.translator.bind(event.from_user.language_code if event.from_user else None)(
                        "gg-group-message-required"
                    )
                )
                return None
        if group is None:
            return await handler(event, data)
        state = scope.MessageScope(ctx.bot_id, event, group)
        token = scope.CURRENT.set(state)
        other = (
            parsed is not None
            and parsed.addressed_to is not None
            and parsed.addressed_to != (ctx.username or "").lower()
        )
        deleted = False
        try:
            cfg = await ctx.extras["guard"].config(group.id, fresh=True)
            # Handlers still receive the original Message. Group-response language is explicit.
            data["guard_target_chat"] = group
            if cfg.lang is not None or "t" not in data:
                data["t"] = actions.group_t(ctx, cfg)
            if parsed is not None and not other:
                if actor.kind == "bot":
                    if actor.bot_sender_id == ctx.bot_id:
                        return None
                    if (
                        event.reply_to_message
                        and event.reply_to_message.from_user
                        and event.reply_to_message.from_user.is_bot
                    ):
                        return None
                    member = await perms.fresh_member(ctx, group.id, actor.bot_sender_id or 0)
                    enabled = (
                        cfg.bot2bot_mode != "off"
                        and member is not None
                        and member.user.is_bot
                        and member.status not in {"creator", "left", "kicked"}
                        and not (member.status == "restricted" and not member.is_member)
                        and (cfg.bot2bot_mode == "all" or perms.member_rights(member).is_admin)
                    )
                    if not enabled:
                        # Explicit slash-filter opt-in is independent from command bot2bot mode.
                        item = await ctx.extras["guard"].get_item(group.id,"filter","/"+parsed.name) if parsed.name not in command_metadata.REGISTRY else None
                        enabled = item is not None and item.options.get("allow_bot") is True and item.options.get("command") is True
                    if not enabled:
                        return None
                    digest = hashlib.sha256(
                        (command_metadata.purpose(parsed.name, parsed.args) + " " + parsed.args).encode()
                    ).hexdigest()
                    try:
                        rate_key = ctx.keys("bot_command_rate",group.id,actor.bot_sender_id)
                        count = await ctx.redis.eval("local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],60) end; return n",1,rate_key)  # type: ignore[misc]
                        if int(count) > 10:
                            return None
                        if not await ctx.redis.set(
                            ctx.keys("bot_command", group.id, actor.bot_sender_id, digest),
                            "1",
                            ex=60,
                            nx=True,
                        ):
                            return None
                    except RedisError:
                        return None
                name = command_metadata.purpose(parsed.name, parsed.args)
                if not await policies.allowed(ctx, name, group.id, actor):
                    if cfg.disabled_delete:
                        await cleanup.delete_source(ctx, event)
                        deleted = True
                    await cleanup.after(ctx, event, group.id, actor, parsed, already_deleted=deleted)
                    return None
                if parsed.name in command_metadata.UNRESOLVED:
                    await event.reply(data["t"]("gg-catalog-unresolved", command=parsed.name))
                    await cleanup.after(ctx, event, group.id, actor, parsed)
                    return None
            result = None if other else await handler(event, data)
            if event.pinned_message is not None:
                from bots.groupguard.handlers.tools import linked_controls
                await linked_controls(ctx,event)
            # A functional handler failure propagates before deleting recoverable service/payment data.
            await cleanup.after(ctx, event, group.id, actor, parsed, other=other)
            return result
        finally:
            scope.CURRENT.reset(token)


class GroupPipeline(BaseMiddleware):
    def __init__(self, ctx: BotContext):
        self.protect = ProtectMiddleware(ctx, ctx.extras["guard"])
        self.policy = CommandPolicy(ctx)

    async def __call__(self, handler, event: TelegramObject, data):
        async def protected(inner, values):
            return await self.policy(handler, inner, values)

        return await self.protect(protected, event, data)
