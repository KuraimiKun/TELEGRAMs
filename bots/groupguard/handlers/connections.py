"""Member connections and bound personal links, revalidating every selected group."""

from __future__ import annotations

import json
import re
import secrets
import time

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from redis.exceptions import RedisError

from bots.groupguard import authz, connections
from core.sdk.context import BotContext
from core.ui.text import esc


async def link(ctx: BotContext, chat_id: int, user_id: int) -> str | None:
    nonce = secrets.token_urlsafe(16)
    try:
        if not await ctx.redis.set(
            ctx.keys("connection_link", nonce),
            json.dumps(dict(created=time.time(),bot_id=ctx.bot_id, chat_id=chat_id, user_id=user_id)),
            ex=3600,
            nx=True,
        ):
            return None
    except RedisError:
        return None
    return f"https://t.me/{ctx.username}?start=gc_{nonce}"


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_connections")
    router.message.filter(F.chat.type.in_({"private", "group", "supergroup"}))

    @router.message(Command("connect", "reconnect", "disconnect", "connection"))
    async def command(message: Message, command: CommandObject, t):
        user = message.from_user
        if user is None or user.is_bot or message.sender_chat is not None:
            await message.reply(t("gg-human-required"))
            return
        if command.command == "disconnect":
            if message.chat.type != "private" or message.chat.id != user.id:
                await message.reply(t("gg-connection-private"))
                return
            await connections.change(ctx, user.id, None)
            await message.reply(t("gg-connection-disconnected"))
            return
        if command.command == "connection":
            current = await connections.current(ctx, user.id)
            await message.reply(
                t("gg-connection-current", group=esc(current.title or str(current.id)))
                if current
                else t("gg-connection-none")
            )
            return
        if message.chat.type in {"group", "supergroup"}:
            url = await link(ctx, message.chat.id, user.id)
            if url is None:
                await message.reply(t("gg-outcome-failed"))
                return
            await message.reply(
                t("gg-connection-open"),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text=t("gg-btn-connect"), url=url)]]
                ),
            )
            return
        if message.chat.id != user.id:
            return
        raw = (command.args or "").strip()
        if not raw:
            state = await connections.get(ctx, user.id)
            ids = state.history if state else []
            rows = []
            for chat_id in ids:
                url = await link(ctx, chat_id, user.id)
                if url:
                    rows.append([InlineKeyboardButton(text=str(chat_id), url=url)])
            await message.reply(
                t("gg-connection-history"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=rows) if rows else None,
            )
            return
        chat = await connections.resolve(ctx, raw, user.id)
        from bots.groupguard import policies
        if (chat is None or not await policies.allowed(ctx,"connect",chat.id,authz.actor_from_message(ctx,message))
                or not await connections.change(ctx, user.id, chat.id)):
            await message.reply(t("gg-connection-unavailable"))
            return
        await message.reply(t("gg-connection-current", group=esc(chat.title or str(chat.id))))

    @router.message(
        F.chat.type == "private",
        CommandStart(deep_link=True),
        F.text.regexp(r"^/start(?:@\w+)? gc_[A-Za-z0-9_-]{22}$"),
    )
    async def private_connect(message: Message, command: CommandObject, t):
        user = message.from_user
        if user is None or user.is_bot or message.chat.id != user.id:
            return
        nonce = (command.args or "")[3:]
        if not re.fullmatch(r"[A-Za-z0-9_-]{22}", nonce):
            return
        try:
            raw = await ctx.redis.get(ctx.keys("connection_link", nonce))
            state = json.loads(raw) if raw else {}
            valid = (
                state.get("bot_id") == ctx.bot_id
                and state.get("user_id") == user.id
                and isinstance(state.get("chat_id"), int)
            )
        except (RedisError, ValueError, TypeError):
            valid = False
        chat = await connections.resolve(ctx, state["chat_id"], user.id) if valid else None
        if chat is None:
            await message.answer(t("gg-connection-unavailable"))
            return
        # Source Group Guard policy must allow connecting even when this link/history exists.
        from bots.groupguard import policies

        actor = authz.actor_from_message(ctx, message)
        if not await policies.allowed(ctx, "connect", chat.id, actor) or not await connections.change(
            ctx, user.id, chat.id
        ):
            await message.answer(t("gg-connection-unavailable"))
            return
        await message.answer(t("gg-connection-current", group=esc(chat.title or str(chat.id))))

    return router
