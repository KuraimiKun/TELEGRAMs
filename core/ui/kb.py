"""Reusable keyboard builders conforming to the platform design system."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.callback_data import CoreLangCb, CoreVipCb
from core.db.models import Plan
from core.i18n import LANGUAGES, Translate
from core.ui.emoji import E


def nav_row(
    t: Translate | None = None,
    back_cb: str | None = "nav:main",
    close: bool = False,
) -> list[InlineKeyboardButton]:
    """Generate a standard back/close bottom row."""
    row: list[InlineKeyboardButton] = []
    back_label = (t("btn-back") if t else f"{E.BACK} Back") if back_cb else ""
    close_label = t("btn-close") if t else f"{E.CLOSE} Close"

    if back_cb:
        row.append(InlineKeyboardButton(text=back_label, callback_data=back_cb))
    if close:
        row.append(InlineKeyboardButton(text=close_label, callback_data="nav:close"))
    return row


def confirm_kb(
    yes_text: str,
    yes_cb: str,
    cancel_text: str,
    cancel_cb: str,
) -> InlineKeyboardMarkup:
    """Standard confirmation inline keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=yes_text, callback_data=yes_cb),
        InlineKeyboardButton(text=cancel_text, callback_data=cancel_cb),
    )
    return builder.as_markup()


def lang_picker_kb(
    current_code: str,
    back_to: str = "main",
    locales: list[str] | None = None,
) -> InlineKeyboardMarkup:
    """Consistent 2-column language selection keyboard (only installed locales are offered)."""
    builder = InlineKeyboardBuilder()
    buttons = []
    for code in locales if locales is not None else list(LANGUAGES):
        label = LANGUAGES.get(code, code)
        text = f"{E.OK} {label}" if code == current_code else label
        buttons.append(InlineKeyboardButton(text=text, callback_data=CoreLangCb(code=code).pack()))

    for i in range(0, len(buttons), 2):
        builder.row(*buttons[i : i + 2])

    builder.row(InlineKeyboardButton(text=f"{E.BACK} Back", callback_data=f"nav:{back_to}"))
    return builder.as_markup()


def vip_plans_kb(plans: list[Plan], t: Translate) -> InlineKeyboardMarkup:
    """Consistent VIP plans selection keyboard."""
    builder = InlineKeyboardBuilder()
    for p in plans:
        text = f"{E.VIP} {p.name} ({p.days}d) — {p.stars} ⭐"
        builder.row(InlineKeyboardButton(text=text, callback_data=CoreVipCb(action="buy", plan_id=p.id).pack()))
    builder.row(InlineKeyboardButton(text=t("btn-back"), callback_data="nav:main"))
    return builder.as_markup()
