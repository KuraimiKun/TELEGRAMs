"""Callback data of Group Guard."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class GgCb(CallbackData, prefix="gg"):
    # cap (captcha answer) | jr (join request) | unwarn | set (panel option) | locks | lock | close | panel
    action: str
    chat: int = 0
    user: int = 0
    arg: str = ""
