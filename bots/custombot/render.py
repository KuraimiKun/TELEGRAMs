"""Showing a page to a visitor: its content plus its children as buttons."""

from __future__ import annotations

import contextlib

from aiogram.exceptions import TelegramAPIError
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bots.custombot.models import CbNode
from bots.custombot.service import PageService
from core.factory.branding import credit
from core.i18n import Translate
from core.sdk.context import BotContext


class PageCb(CallbackData, prefix="pg"):
    id: int


async def page_markup(svc: PageService, node: CbNode, t: Translate) -> InlineKeyboardMarkup | None:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for child in await svc.children(node.id):
        if child.url:
            row.append(InlineKeyboardButton(text=child.title, url=child.url))
        else:
            row.append(InlineKeyboardButton(text=child.title, callback_data=PageCb(id=child.id).pack()))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    if node.parent_id is not None:
        rows.append([InlineKeyboardButton(text=t("btn-back"), callback_data=PageCb(id=node.parent_id).pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


def page_text(ctx: BotContext, node: CbNode, t: Translate) -> str:
    text = node.text or (t("cb-default-home") if node.parent_id is None else node.title)
    return text + (credit(ctx, t) if node.parent_id is None else "")


async def send_page(ctx: BotContext, svc: PageService, chat_id: int, node: CbNode, t: Translate) -> None:
    kb = await page_markup(svc, node, t)
    text = page_text(ctx, node, t)
    if node.media_kind and node.file_id:
        send = getattr(ctx.bot, f"send_{node.media_kind}")
        if node.media_kind in ("sticker", "video_note"):
            await send(chat_id, node.file_id)
            await ctx.bot.send_message(chat_id, text, reply_markup=kb)
        else:
            await send(chat_id, node.file_id, caption=text[:1024], reply_markup=kb)
        return
    await ctx.bot.send_message(chat_id, text, reply_markup=kb, disable_web_page_preview=False)


async def open_page(ctx: BotContext, svc: PageService, query: CallbackQuery, node: CbNode, t: Translate) -> None:
    """Edit the current message in place for text pages; media pages are sent as a new message."""
    message = query.message
    if not node.media_kind and isinstance(message, Message) and message.text is not None:
        with contextlib.suppress(TelegramAPIError):
            await message.edit_text(page_text(ctx, node, t), reply_markup=await page_markup(svc, node, t))
            await query.answer()
            return
    await query.answer()
    await send_page(ctx, svc, query.from_user.id, node, t)
