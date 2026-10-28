"""Tracks where the bot lives: users blocking/unblocking it, and groups adding/removing it."""

from __future__ import annotations

import contextlib

from aiogram import Router
from aiogram.enums import ChatType
from aiogram.types import ChatMemberUpdated

from core.log import get_logger
from core.sdk.context import BotContext

log = get_logger(__name__)

GONE = {"left", "kicked"}
PRESENT = {"member", "administrator", "creator", "restricted"}


def build_router(ctx: BotContext) -> Router:
    router = Router(name=f"core_membership_{ctx.slug}")

    @router.my_chat_member()
    async def bot_membership_changed(event: ChatMemberUpdated) -> None:
        new, old = event.new_chat_member.status, event.old_chat_member.status
        chat = event.chat

        if chat.type == ChatType.PRIVATE:
            if new in GONE:
                await ctx.users.set_blocked(chat.id, True)
                log.info("user_blocked_bot", bot=ctx.slug, user_id=chat.id)
            elif new in PRESENT:
                await ctx.users.set_blocked(chat.id, False)
            return

        if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
            return
        if new in GONE:
            await ctx.groups.set_active(chat.id, False, chat.title)
            log.info("bot_removed_from_group", bot=ctx.slug, chat_id=chat.id)
        elif new in PRESENT and old in GONE:
            await ctx.groups.set_active(chat.id, True, chat.title)
            log.info("bot_added_to_group", bot=ctx.slug, chat_id=chat.id)
            stg = await ctx.settings.get()
            adder = await ctx.users.get(event.from_user.id) if event.from_user else None
            lang = ctx.translator.resolve(adder.lang if adder else (event.from_user.language_code if event.from_user else None))
            key = "group-welcome" if stg.groups_enabled else "group-disabled"
            with contextlib.suppress(Exception):
                await ctx.bot.send_message(chat.id, ctx.translator.get(lang, key))

    return router
