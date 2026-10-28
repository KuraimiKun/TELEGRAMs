"""Feedback / contact bot: visitors write, the owner (or their team group) replies by replying."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select

from bots.feedback.models import FeedbackThread
from bots.feedback.settings import FeedbackSettings
from core.db.base import upsert
from core.factory.branding import credit, factory_link
from core.i18n import Translate
from core.log import get_logger
from core.sdk.context import BotContext
from core.ui.text import esc

log = get_logger(__name__)

CAPTIONABLE = ("photo", "video", "animation", "voice", "audio", "document")


def build_router(ctx: BotContext) -> Router:
    router = Router(name="feedback")
    owner_id = ctx.child.owner_id if ctx.child else (ctx.env.admin_ids[0] if ctx.env.admin_ids else 0)

    async def settings() -> FeedbackSettings:
        stg = await ctx.settings.get()
        assert isinstance(stg, FeedbackSettings)
        return stg

    async def inbox() -> int:
        return (await settings()).inbox_chat_id or owner_id

    async def remember(inbox_chat: int, inbox_msg: int, user_id: int) -> None:
        async with ctx.sm() as s:
            await s.execute(
                upsert(s, FeedbackThread)
                .values(bot_id=ctx.bot_id, inbox_chat_id=inbox_chat, inbox_msg_id=inbox_msg, user_id=user_id)
                .on_conflict_do_nothing()
            )
            await s.commit()

    async def user_for(inbox_chat: int, inbox_msg: int) -> int | None:
        async with ctx.sm() as s:
            stmt = select(FeedbackThread.user_id).where(
                FeedbackThread.bot_id == ctx.bot_id,
                FeedbackThread.inbox_chat_id == inbox_chat,
                FeedbackThread.inbox_msg_id == inbox_msg,
            )
            return (await s.execute(stmt)).scalar_one_or_none()

    def is_inbox_side(message: Message, inbox_chat: int) -> bool:
        uid = message.from_user.id if message.from_user else 0
        return message.chat.id == inbox_chat or uid == owner_id

    # ------------------------------------------------------------------ owner side
    @router.message(Command("setinbox"), F.chat.type.in_({"group", "supergroup"}))
    async def cmd_setinbox(message: Message, t: Translate) -> None:
        if message.from_user is None or message.from_user.id != owner_id:
            return
        await ctx.settings.set("inbox_chat_id", message.chat.id)
        await message.reply(t("fb-inbox-group"))

    @router.message(Command("unsetinbox"))
    async def cmd_unsetinbox(message: Message, t: Translate) -> None:
        if message.from_user is None or message.from_user.id != owner_id:
            return
        await ctx.settings.set("inbox_chat_id", 0)
        await message.reply(t("fb-inbox-private"))

    @router.message(Command("ban", "unban"))
    async def cmd_ban(message: Message, command: CommandObject, t: Translate) -> None:
        inbox_chat = await inbox()
        if not is_inbox_side(message, inbox_chat):
            return
        target = None
        if message.reply_to_message is not None:
            target = await user_for(message.chat.id, message.reply_to_message.message_id)
        elif (command.args or "").strip().isdigit():
            target = int((command.args or "").strip())
        if target is None:
            await message.reply(t("fb-ban-usage"))
            return
        banned = command.command == "ban"
        await ctx.users.set_banned(target, banned, reason="feedback owner")
        await message.reply(t("fb-banned" if banned else "fb-unbanned", id=str(target)))

    @router.message(CommandStart())
    async def cmd_start(message: Message, t: Translate) -> None:
        uid = message.from_user.id if message.from_user else 0
        if uid == owner_id:
            await message.answer(t("fb-owner-home", link=f"https://t.me/{ctx.username}"))
            return
        stg = await settings()
        text = stg.greeting or t("fb-greeting")
        await message.answer(text + credit(ctx, t))

    @router.message(lambda m: m.reply_to_message is not None)
    async def on_reply(message: Message, t: Translate) -> None:
        inbox_chat = await inbox()
        reply = message.reply_to_message
        assert reply is not None
        if not is_inbox_side(message, inbox_chat) or reply.from_user is None or reply.from_user.id != ctx.bot_id:
            if message.chat.type == "private":
                await on_visitor(message, t)  # a visitor replying to one of the bot's messages
            return
        target = await user_for(message.chat.id, reply.message_id)
        if target is None:
            await message.reply(t("fb-reply-unknown"))
            return
        try:
            await ctx.bot.copy_message(chat_id=target, from_chat_id=message.chat.id, message_id=message.message_id)
        except TelegramForbiddenError:
            await message.reply(t("fb-user-blocked"))
            return
        except TelegramAPIError as e:
            await message.reply(t("fb-reply-failed", error=esc(str(e))))
            return
        await message.reply(t("fb-reply-sent"))

    # ------------------------------------------------------------------ visitors
    @router.message(F.chat.type == "private")
    async def on_visitor(message: Message, t: Translate) -> None:
        uid = message.from_user.id if message.from_user else 0
        if uid == owner_id:
            await message.answer(t("fb-owner-hint"))
            return
        stg = await settings()
        inbox_chat = await inbox()
        sender = message.from_user
        assert sender is not None
        if stg.show_profile:
            handle = f" · @{esc(sender.username)}" if sender.username else ""
            header = f'💬 <a href="tg://user?id={uid}">{esc(sender.full_name)}</a>{handle} · <code>{uid}</code>'
        else:
            header = f"💬 <code>{uid}</code>"
        try:
            if message.text:
                sent = await ctx.bot.send_message(inbox_chat, f"{header}\n\n{esc(message.text)}")
                ids = [sent.message_id]
            elif any(getattr(message, k, None) for k in CAPTIONABLE):
                caption = header + (f"\n\n{esc(message.caption)}" if message.caption else "")
                copied = await ctx.bot.copy_message(inbox_chat, message.chat.id, message.message_id,
                                                    caption=caption[:1024])
                ids = [copied.message_id]
            else:
                head = await ctx.bot.send_message(inbox_chat, header)
                copied = await ctx.bot.copy_message(inbox_chat, message.chat.id, message.message_id,
                                                    reply_to_message_id=head.message_id)
                ids = [head.message_id, copied.message_id]
        except TelegramAPIError as e:
            log.warning("feedback_inbox_failed", bot=ctx.slug, error=str(e))
            await message.answer(t("fb-unavailable"))
            return
        for mid in ids:
            await remember(inbox_chat, mid, uid)
        if stg.away:
            await message.answer(stg.away_text or t("fb-away"))
        else:
            kb = None
            if url := factory_link(ctx):
                kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t("fb-btn-own"), url=url)]])
            await message.answer(t("fb-delivered"), reply_markup=kb if ctx.child and ctx.child.branding else None)

    return router
