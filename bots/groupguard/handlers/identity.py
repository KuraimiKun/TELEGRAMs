"""Available user/chat information without pretending arbitrary usernames are resolvable."""
from __future__ import annotations

import json

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject
from aiogram.types import Chat, Message, MessageOriginUser, User
from redis.exceptions import RedisError

from bots.groupguard import actions, authz, federations, perms
from bots.groupguard.federations import FedError
from bots.groupguard.handlers.fed_bans import status_text
from bots.groupguard.scope import target_chat
from core.sdk.context import BotContext
from core.ui.text import esc


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_identity")
    router.message.filter(F.chat.type.in_({"private", "group", "supergroup"}))

    @router.message(Command("id", "info"))
    async def identity(message: Message, command: CommandObject,t):
        cfg = await ctx.extras["guard"].config(target_chat(message).id) if target_chat(message).id < 0 else None
        t = actions.group_t(ctx, cfg) if cfg is not None else t
        value: User | Chat | None = message.sender_chat or message.from_user
        if command.command == "id" and message.chat.type == "private" and target_chat(message).id < 0 and not command.args and message.reply_to_message is None:
            value = target_chat(message)
        reply = message.reply_to_message
        arg = (command.args or "").strip()
        if reply is not None:
            value = reply.sender_chat or (reply.forward_origin.sender_user if isinstance(reply.forward_origin, MessageOriginUser) else reply.from_user)
        elif arg:
            if arg.startswith("@"):
                try:
                    raw = await ctx.redis.get(ctx.keys("uname", arg[1:].lower()))
                    saved = json.loads(raw) if raw else None
                    uid = int(saved["id"] if isinstance(saved, dict) else saved) if saved and not (isinstance(saved, dict) and saved.get("ambiguous")) else None
                except (ValueError, TypeError, KeyError, RedisError):
                    uid = None
            else:
                uid = int(arg) if arg.lstrip("-").isdigit() and len(arg) <= 16 else None
            value = None
            if uid is not None:
                member = await perms.fresh_member(ctx, target_chat(message).id, uid) if target_chat(message).id < 0 and uid > 0 else None
                if member is not None:
                    value = member.user
                else:
                    try:
                        chat = await ctx.bot.get_chat(uid)
                        if chat.id == uid:
                            value = chat
                    except TelegramAPIError:
                        pass
                if arg.startswith("@") and value is not None and (value.username or "").lower() != arg[1:].lower():
                    value = None
        if value is None:
            await message.reply(t("gg-target-invalid"))
            return
        membership = "—"
        if target_chat(message).id < 0 and value.id > 0:
            member = await perms.fresh_member(ctx, target_chat(message).id, value.id)
            membership = str(member.status) if member else t("gg-unknown")
        name = value.full_name if isinstance(value, User) else value.title or value.full_name or str(value.id)
        text = t("gg-info", name=esc(name), username=esc("@" + value.username if value.username else "—"),
                 id=str(value.id), membership=membership)
        if command.command == "id" and not arg and reply is None and target_chat(message).id < 0:
            text += "\n" + t("gg-chat-id", id=str(target_chat(message).id))
        await message.reply(text)
        if command.command == 'info' and value.id > 0:
            try:
                await federations.public_actor(ctx,authz.actor_from_message(ctx,message))
            except FedError:
                return
            summary = await status_text(ctx,value.id,t,empty=False)
            if summary is not None:
                # Keep the complete profile and bounded source page independently
                # within Telegram's message limit, using the same native language.
                await message.reply(summary)

    return router
