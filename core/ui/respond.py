"""Answer a button press by editing its message, or a typed message by replying — safely.

Callback queries on messages older than 48h carry an ``InaccessibleMessage`` that cannot be edited;
we fall back to sending a new message instead of crashing.
"""

from __future__ import annotations

import contextlib

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message


async def show(event: Message | CallbackQuery, text: str, kb: InlineKeyboardMarkup | None = None) -> None:
    if isinstance(event, CallbackQuery):
        if isinstance(event.message, Message):
            with contextlib.suppress(TelegramBadRequest):  # "message is not modified"
                await event.message.edit_text(text, reply_markup=kb)
        elif event.bot is not None:
            await event.bot.send_message(chat_id=event.from_user.id, text=text, reply_markup=kb)
        with contextlib.suppress(TelegramBadRequest):
            await event.answer()
    else:
        await event.answer(text, reply_markup=kb)
