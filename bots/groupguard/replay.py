"""Bounded durable update claims and content versions, before user/core side effects."""
from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, Update
from sqlalchemy import select, update

from bots.groupguard.authz import active_namespace
from bots.groupguard.models import GuardInbox, GuardMessage
from bots.groupguard.protect import EventIdentity
from core.db.base import affected, upsert, utcnow
from core.sdk.context import BotContext

INBOX_LEASE_SECONDS = 240
MAX_UPDATE_BYTES = 131072


class ReplayMiddleware(BaseMiddleware):
    def __init__(self, ctx: BotContext) -> None:
        self.ctx = ctx

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        if not isinstance(event, Update):
            return await handler(event, data)
        ctx = self.ctx
        if not await active_namespace(ctx):
            return None
        payload = event.model_dump(mode="json", exclude_none=True)
        if len(json.dumps(payload).encode()) > MAX_UPDATE_BYTES:
            raise ValueError("groupguard_update_too_large")
        async with ctx.sm() as session:
            await session.execute(upsert(session, GuardInbox).values(bot_id=ctx.bot_id,
                update_id=event.update_id, event_type=event.event_type, payload=payload,
                status="received", created_at=utcnow()).on_conflict_do_nothing())
            claimed = await session.execute(update(GuardInbox).where(GuardInbox.bot_id == ctx.bot_id,
                GuardInbox.update_id == event.update_id, GuardInbox.status == "received").values(
                    status="processing", lease_until=utcnow() + timedelta(seconds=INBOX_LEASE_SECONDS)))
            await session.commit()
        if affected(claimed) != 1:
            return None
        msg = event.message or event.edited_message
        if isinstance(msg, Message) and msg.chat.type in {"group", "supergroup"}:
            identity = EventIdentity.of(ctx, msg, {"event_update": event})
            async with ctx.sm() as session:
                inserted = await session.execute(upsert(session, GuardMessage).values(bot_id=ctx.bot_id,
                    chat_id=msg.chat.id, message_id=msg.message_id, user_id=msg.from_user.id if msg.from_user and msg.sender_chat is None else None,
                    content_version=identity.content_version, counted=not identity.edited,
                    created_at=utcnow()).on_conflict_do_nothing())
                first = affected(inserted) == 1
                if not first:
                    if not identity.edited:
                        await self._completed(event.update_id, session=session)
                        await session.commit()
                        return None
                    changed = await session.execute(update(GuardMessage).where(GuardMessage.bot_id == ctx.bot_id,
                        GuardMessage.chat_id == msg.chat.id, GuardMessage.message_id == msg.message_id,
                        GuardMessage.content_version != identity.content_version).values(content_version=identity.content_version))
                    if affected(changed) != 1:
                        await self._completed(event.update_id, session=session)
                        await session.commit()
                        return None
                await session.commit()
            data["guard_message_new"] = first and not identity.edited
        try:
            result = await handler(event, data)
        except BaseException:
            async with ctx.sm() as session:
                await session.execute(update(GuardInbox).where(GuardInbox.bot_id == ctx.bot_id,
                    GuardInbox.update_id == event.update_id).values(status="uncertain", error_code="interrupted_processing", lease_until=None))
                await session.commit()
            raise
        await self._completed(event.update_id)
        return result

    async def _completed(self, update_id: int, *, session=None) -> None:
        if session is None:
            async with self.ctx.sm() as owned:
                await self._completed(update_id, session=owned)
                await owned.commit()
                return
        await session.execute(update(GuardInbox).where(GuardInbox.bot_id == self.ctx.bot_id,
            GuardInbox.update_id == update_id).values(status="completed", lease_until=None,payload={}))


async def recover_inbox(ctx: BotContext, limit: int = 100) -> int:
    async with ctx.sm() as session:
        stale = list((await session.execute(select(GuardInbox).where(GuardInbox.bot_id == ctx.bot_id,
            GuardInbox.status == "processing", GuardInbox.lease_until < utcnow()).order_by(GuardInbox.lease_until)
            .limit(limit).with_for_update(skip_locked=True))).scalars())
        for row in stale:
            row.status, row.error_code, row.lease_until = "uncertain", "interrupted_processing", None
        ready = list((await session.execute(select(GuardInbox).where(GuardInbox.bot_id == ctx.bot_id,
            GuardInbox.status == "received").order_by(GuardInbox.created_at).limit(limit))).scalars())
        await session.commit()
    dp = ctx.extras.get("guard_dispatcher")
    if dp is None:
        return 0
    count = 0
    for row in ready:
        await dp.feed_update(ctx.bot, Update.model_validate(row.payload, context={"bot": ctx.bot}))
        count += 1
    return count
