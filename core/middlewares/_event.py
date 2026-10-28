"""Helpers for middlewares that may receive either an ``Update`` or an inner event object."""

from __future__ import annotations

from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, InlineQuery, Message, PreCheckoutQuery, TelegramObject, Update


def unwrap(event: TelegramObject) -> TelegramObject:
    """Return the concrete inner event of an ``Update`` (or the event itself)."""
    if isinstance(event, Update):
        try:
            inner = event.event
        except Exception:  # UpdateTypeLookupError for update types aiogram does not know
            return event
        return inner if inner is not None else event
    return event


def is_private(event: TelegramObject) -> bool:
    event = unwrap(event)
    if isinstance(event, Message):
        return event.chat.type == ChatType.PRIVATE
    if isinstance(event, CallbackQuery):
        msg = event.message
        return msg is None or msg.chat.type == ChatType.PRIVATE
    return isinstance(event, InlineQuery)


def is_payment_event(event: TelegramObject) -> bool:
    """Payment-related events must never be dropped by throttling/maintenance guards."""
    event = unwrap(event)
    if isinstance(event, Message):
        return bool(event.successful_payment or event.refunded_payment)
    return isinstance(event, PreCheckoutQuery)


async def notify(event: TelegramObject, text: str, *, alert: bool = True) -> None:
    """Tell the user why their event was rejected — in private chats and callbacks only.

    Replying in groups would spam every member, so group messages are dropped silently.
    """
    event = unwrap(event)
    if isinstance(event, CallbackQuery):
        await event.answer(text, show_alert=alert)
    elif isinstance(event, Message) and event.chat.type == ChatType.PRIVATE:
        await event.answer(text)
    elif isinstance(event, InlineQuery):
        await event.answer([], cache_time=5, is_personal=True)
