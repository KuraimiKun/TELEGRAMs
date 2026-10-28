"""Buttons of the anonymous inbox."""

from __future__ import annotations

from urllib.parse import urlencode

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from core.callback_data import CoreVipCb
from core.i18n import Translate


class AnonCb(CallbackData, prefix="an"):
    # reply | block | report | hint | again | home | link | card | stats | settings | pause | prompt | reset
    # | unblock | ban (admin)
    action: str
    id: int = 0


def cb(action: str, id: int = 0) -> str:
    return AnonCb(action=action, id=id).pack()


def btn(text: str, action: str, id: int = 0) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=cb(action, id))


def share_url(link: str, text: str) -> str:
    return "https://t.me/share/url?" + urlencode({"url": link, "text": text})


def home_kb(t: Translate, link: str, *, vip: bool, lang: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t("anon-btn-share"), url=share_url(link, t("anon-share-text")))],
        [btn(t("anon-btn-card"), "card"), InlineKeyboardButton(text=t("anon-btn-inline"), switch_inline_query="")],
        [btn(t("anon-btn-stats"), "stats"), btn(t("anon-btn-settings"), "settings")],
    ]
    extra = []
    if vip:
        extra.append(InlineKeyboardButton(text=t("btn-vip"), callback_data=CoreVipCb(action="info").pack()))
    if lang:
        extra.append(InlineKeyboardButton(text=t("btn-lang"), callback_data="nav:lang"))
    if extra:
        rows.append(extra)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def incoming_kb(t: Translate, message_id: int, *, from_anonymous: bool, hints: bool) -> InlineKeyboardMarkup:
    """Buttons under a delivered message. Only the inbox owner can block/report/hint an anonymous sender."""
    rows = [[btn(t("anon-btn-reply"), "reply", message_id)]]
    if from_anonymous:
        rows[0].append(btn(t("anon-btn-block"), "block", message_id))
        second = [btn(t("anon-btn-report"), "report", message_id)]
        if hints:
            second.append(btn(t("anon-btn-hint"), "hint", message_id))
        rows.append(second)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def sent_kb(t: Translate, message_id: int, own_link: InlineKeyboardButton | None) -> InlineKeyboardMarkup:
    rows = [[btn(t("anon-btn-again"), "again", message_id)]]
    if own_link is not None:
        rows.append([own_link])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_kb(t: Translate) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[btn(t("btn-back"), "home")]])
