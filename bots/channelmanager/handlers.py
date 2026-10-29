"""Private operator menus. Every resource callback binds its actor and channel generation."""

from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bots.channelmanager.models import Channel
from bots.channelmanager.permissions import AccessDenied, publishing_access
from bots.channelmanager.service import ChannelService
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.respond import show
from core.ui.text import esc


class ChannelCb(CallbackData, prefix="chm"):
    a: str
    c: int
    g: int
    u: int


def button(text: str, action: str, user_id: int, channel_id: int = 0, generation: int = 0) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=ChannelCb(a=action, c=channel_id, g=generation, u=user_id).pack())


def markup(*rows: list[InlineKeyboardButton]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=list(rows))


def build_router(ctx: BotContext) -> Router:
    from bots.channelmanager.automation_ui import button as auto_button
    from bots.channelmanager.member_ui import button as member_button
    from bots.channelmanager.publishing_ui import btn as post_button
    router = Router(name=f"channelmanager_{ctx.slug}")
    router.message.filter(F.chat.type == "private")
    router.callback_query.filter(F.message.chat.type == "private")
    svc: ChannelService = ctx.extras["channelmanager"]

    async def listing(event: Message | CallbackQuery, user_id: int, t: Translate, offset: int = 0) -> None:
        rows = []
        channels = await svc.known(user_id, offset=offset)
        for channel in channels:
            try:
                await publishing_access(ctx, channel.channel_id, user_id)
            except (AccessDenied, TelegramAPIError):
                continue
            rows.append([button(channel.title[:60], "view", user_id, channel.channel_id, channel.generation)])
        nav = []
        if offset:
            nav.append(button("◀️", "list", user_id, max(0, offset - 10)))
        if len(channels) == 10:
            nav.append(button("▶️", "list", user_id, offset + 10))
        if nav:
            rows.append(nav)
        rows.append([button(t("chm-btn-connect"), "help", user_id)])
        await show(event, t("chm-list") if rows[:-1] else t("chm-empty"), markup(*rows))

    async def panel(query: CallbackQuery, row: Channel, t: Translate) -> None:
        names = {
            "can_post_messages": t("chm-right-post"), "can_edit_messages": t("chm-right-edit"),
            "can_delete_messages": t("chm-right-delete"), "can_invite_users": t("chm-right-invite"),
            "can_restrict_members": t("chm-right-restrict"),
        }
        missing = ", ".join(label for right, label in names.items() if not row.rights.get(right)) or t("chm-none")
        text = t("chm-channel", title=esc(row.title), id=str(row.channel_id),
                 status=t(f"chm-state-{row.status}"), missing=missing)
        await show(query, text, markup(
            [post_button(t("chm-btn-new-post"), "new", str(row.channel_id), row.generation, query.from_user.id),
             post_button(t("chm-btn-posts"), "list", str(row.channel_id), 0, query.from_user.id)],
            [auto_button(t("chm4-menu"), "chan", row.channel_id, row.generation, query.from_user.id)],
            [member_button(t("chm5-menu"), "chan", row.channel_id, 0, query.from_user.id)],
            [button(t("chm-btn-refresh"), "refresh", query.from_user.id, row.channel_id, row.generation)],
            [button(t("chm-btn-disconnect"), "ask", query.from_user.id, row.channel_id, row.generation)],
            [button(t("btn-back"), "list", query.from_user.id)]))

    @router.message(Command("start", "help"))
    async def start(message: Message, t: Translate, state: FSMContext) -> None:
        await state.clear()
        if message.from_user:
            await show(message, t("chm-start"), markup(
                [post_button(t("chm-btn-new-post"), "choose", "0", 0, message.from_user.id),
                 post_button(t("chm-btn-posts"), "list", "mine", 0, message.from_user.id)],
                [button(t("chm-btn-channels"), "list", message.from_user.id)],
                [auto_button(t("chm4-menu"), "choose", "0", 0, message.from_user.id)],
                [member_button(t("chm5-menu"), "choose", "0", 0, message.from_user.id)],
                [button(t("chm-btn-connect"), "help", message.from_user.id)]))

    @router.message(Command("channels"))
    async def channels(message: Message, t: Translate, state: FSMContext) -> None:
        await state.clear()
        if message.from_user:
            await listing(message, message.from_user.id, t)

    @router.message(Command("connect"))
    async def connect(message: Message, t: Translate, state: FSMContext) -> None:
        await state.clear()
        if not message.from_user:
            return
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) != 2 or not re.fullmatch(r"-\d{1,19}|@[A-Za-z][A-Za-z0-9_]{4,31}", parts[1]):
            await show(message, t("chm-connect-help"))
            return
        reference: int | str = int(parts[1]) if parts[1].startswith("-") else parts[1]
        try:
            await svc.connect(reference, message.from_user.id)
        except (AccessDenied, TelegramAPIError):
            await show(message, t("chm-connect-denied"))
            return
        await show(message, t("chm-connected"), markup(
            [button(t("chm-btn-channels"), "list", message.from_user.id)]))

    @router.callback_query(ChannelCb.filter())
    async def callback(query: CallbackQuery, callback_data: ChannelCb, t: Translate, state: FSMContext) -> None:
        cb = callback_data
        if cb.u != query.from_user.id:
            await query.answer(t("chm-denied"), show_alert=True)
            return
        await state.clear()
        if cb.a == "help":
            await show(query, t("chm-connect-help"))
        elif cb.a == "list" and 0 <= cb.c <= 10000:
            await listing(query, query.from_user.id, t, cb.c)
        elif cb.a in {"view", "refresh", "ask", "disconnect"} and cb.c < 0:
            try:
                await publishing_access(ctx, cb.c, query.from_user.id)
                row = await svc.get(cb.c)
                if row is None or row.generation != cb.g:
                    raise AccessDenied("stale_menu")
                if cb.a == "disconnect":
                    await svc.disconnect(cb.c, query.from_user.id, cb.g)
                    await show(query, t("chm-disconnected"))
                elif cb.a == "ask":
                    await show(query, t("chm-disconnect-confirm", title=esc(row.title)), markup(
                        [button(t("chm-btn-confirm"), "disconnect", cb.u, cb.c, cb.g)],
                        [button(t("btn-back"), "view", cb.u, cb.c, cb.g)]))
                else:
                    if cb.a == "refresh":
                        row = await svc.refresh(cb.c, cb.u, cb.g)
                    await panel(query, row, t)
            except (AccessDenied, TelegramAPIError):
                await query.answer(t("chm-denied"), show_alert=True)
                return
        else:
            await query.answer(t("chm-denied"), show_alert=True)
            return
        await query.answer()

    @router.callback_query(F.data.startswith("chm:"))
    async def malformed(query: CallbackQuery, t: Translate) -> None:
        await query.answer(t("chm-denied"), show_alert=True)

    return router
