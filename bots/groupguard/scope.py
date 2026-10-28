"""Logical group context while preserving the actual source message and reply destination."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass

from aiogram.filters import Filter
from aiogram.types import Chat, Message


@dataclass(frozen=True, slots=True)
class MessageScope:
    bot_id: int
    source: Message
    group: Chat


CURRENT: ContextVar[MessageScope | None] = ContextVar("guard_message_scope", default=None)


def target_chat(message: Message) -> Chat:
    state = CURRENT.get()
    return state.group if state is not None and state.source is message else message.chat


class GroupMessages(Filter):
    async def __call__(self, message: Message) -> bool:
        return target_chat(message).type in {"group", "supergroup"} and message.successful_payment is None
