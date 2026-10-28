"""Tenant-scoped current connections; history and links never grant group authority."""

from __future__ import annotations

import re

from aiogram.exceptions import TelegramAPIError
from aiogram.types import Chat, ChatFullInfo
from sqlalchemy import select, update

from bots.groupguard import authz, delivery, perms
from bots.groupguard.models import GuardConnection
from core.db.base import upsert, utcnow
from core.sdk.context import BotContext


async def get(ctx: BotContext, user_id: int) -> GuardConnection | None:
    async with ctx.sm() as session:
        return await session.get(GuardConnection, (ctx.bot_id, user_id))


async def resolve(ctx: BotContext, reference: str | int, user_id: int) -> ChatFullInfo | None:
    if not await authz.active_namespace(ctx):
        return None
    raw = str(reference).strip()
    if not re.fullmatch(r"-\d{1,16}|@[A-Za-z][A-Za-z0-9_]{4,31}", raw):
        return None
    try:
        chat = await ctx.bot.get_chat(int(raw) if raw.startswith("-") else raw)
    except TelegramAPIError:
        return None
    if chat is None or chat.id >= 0 or chat.type not in {"group", "supergroup"}:
        return None
    if raw.startswith("-") and chat.id != int(raw):
        return None
    if raw.startswith("@") and (chat.username or "").lower() != raw[1:].lower():
        return None
    return chat if await delivery.current_member(ctx, chat.id, user_id) else None


async def change(ctx: BotContext, user_id: int, chat_id: int | None) -> bool:
    if not perms.valid_human_id(user_id) or not await authz.active_namespace(ctx):
        return False
    if chat_id is not None and not await delivery.current_member(ctx, chat_id, user_id):
        return False
    async with ctx.sm() as session:
        await session.execute(
            upsert(session, GuardConnection)
            .values(bot_id=ctx.bot_id, user_id=user_id, history=[], chat_id=None, updated_at=utcnow())
            .on_conflict_do_nothing()
        )
        row = (
            await session.execute(
                select(GuardConnection)
                .where(GuardConnection.bot_id == ctx.bot_id, GuardConnection.user_id == user_id)
                .with_for_update()
            )
        ).scalar_one()
        if chat_id is not None:
            row.history = [chat_id, *[value for value in row.history if value != chat_id]][:5]
        row.chat_id = chat_id
        row.revision += 1
        row.updated_at = utcnow()
        await session.commit()
    return True


async def current(ctx: BotContext, user_id: int) -> Chat | None:
    row = await get(ctx, user_id)
    if row is None or row.chat_id is None:
        return None
    chat = await resolve(ctx, row.chat_id, user_id)
    if chat is None:
        async with ctx.sm() as session:
            # Do not clear a newer connection selected concurrently.
            await session.execute(
                update(GuardConnection)
                .where(
                    GuardConnection.bot_id == ctx.bot_id,
                    GuardConnection.user_id == user_id,
                    GuardConnection.chat_id == row.chat_id,
                    GuardConnection.revision == row.revision,
                )
                .values(chat_id=None, revision=GuardConnection.revision+1, updated_at=utcnow())
            )
            await session.commit()
    return chat
