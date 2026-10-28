"""Building blocks shared by every admin screen."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, TelegramObject

from core.callback_data import AdminNavCb
from core.filters import IsAdmin
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.respond import show

__all__ = [
    "PER_PAGE",
    "ClearStateOnNavigation",
    "actor",
    "admin_router",
    "back_row",
    "btn",
    "markup",
    "nav",
    "pager",
    "show",
]

PER_PAGE = 10


class ClearStateOnNavigation:
    """Leaving a screen abandons any half-finished admin input (search, value edit, broadcast draft...).

    Without this an admin who opened "search" and walked away would have their next normal message
    swallowed as a search query.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, CallbackQuery) and (event.data or "").startswith(AdminNavCb.__prefix__ + ":"):
            state: FSMContext | None = data.get("state")
            if state is not None:
                await state.clear()
        return await handler(event, data)


def admin_router(ctx: BotContext, name: str) -> Router:
    router = Router(name=f"core_admin_{name}_{ctx.slug}")
    router.message.filter(IsAdmin())
    router.callback_query.filter(IsAdmin())
    return router


def btn(text: str, callback_data: str | None = None, url: str | None = None) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback_data, url=url)


def nav(tab: str, text: str, page: int = 1) -> InlineKeyboardButton:
    return btn(text, AdminNavCb(tab=tab, page=page).pack())


def markup(*rows: list[InlineKeyboardButton] | None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[r for r in rows if r])


def back_row(t: Translate, tab: str = "home") -> list[InlineKeyboardButton]:
    return [nav(tab, t("btn-back"))]


def pager(t: Translate, page: int, pages: int, make_cb: Callable[[int], str]) -> list[InlineKeyboardButton] | None:
    if pages <= 1:
        return None
    row = []
    if page > 1:
        row.append(btn("◀️", make_cb(page - 1)))
    row.append(btn(f"{page}/{pages}", make_cb(page)))
    if page < pages:
        row.append(btn("▶️", make_cb(page + 1)))
    return row


def actor(event: Message | CallbackQuery) -> int:
    return event.from_user.id if event.from_user else 0
