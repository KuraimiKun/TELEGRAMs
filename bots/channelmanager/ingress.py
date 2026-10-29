"""Commit channel events before acknowledgement; process only SQL work in inbox transactions."""

from __future__ import annotations

import json
import uuid
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlalchemy import select

from bots.channelmanager.models import Inbox
from bots.channelmanager.service import ChannelService
from core.db.base import upsert, utcnow
from core.sdk.context import BotContext
from core.sdk.module import DurableIngressError

MAX_UPDATE_BYTES = 131072


def is_channel_event(event: Update) -> bool:
    inner = event.my_chat_member or event.chat_member or event.chat_join_request or event.channel_post or event.edited_channel_post
    return inner is not None and inner.chat.type == "channel"


class ChannelIngress(BaseMiddleware):
    def __init__(self, ctx: BotContext) -> None:
        self.ctx = ctx

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        financial = isinstance(event, Update) and event.message and event.message.chat.type == "private" and (event.message.successful_payment or event.message.refunded_payment)
        if not isinstance(event, Update) or (not financial and not is_channel_event(event)):
            return await handler(event, data)
        kind = ("billing_paid" if event.message and event.message.successful_payment else "billing_refund") if financial else event.event_type
        try:
            payload = event.model_dump(mode="json", exclude_none=True)
            if len(json.dumps(payload).encode()) > MAX_UPDATE_BYTES:
                raise ValueError("channel_update_too_large")
            async with self.ctx.sm() as session:
                await session.execute(upsert(session, Inbox).values(bot_id=self.ctx.bot_id, update_id=event.update_id,
                    event_type=kind,
                    payload=payload).on_conflict_do_nothing())
                await session.commit()
        except Exception:
            # SQL driver exceptions can include the private update payload in their parameters.
            raise DurableIngressError("channelmanager_inbox_unavailable") from None
        # Do not register channel members as private bot users or perform Telegram side effects here.
        return None


async def process_one(ctx: BotContext) -> bool:
    update_id = None
    try:
        settings = await ctx.settings.get()
        async with ctx.sm() as session:
            row = (await session.execute(select(Inbox).where(Inbox.bot_id == ctx.bot_id,
                Inbox.status == "pending", Inbox.event_type.not_in({"billing_paid", "billing_refund"}), Inbox.available_at <= utcnow()).order_by(Inbox.update_id)
                .limit(1).with_for_update(skip_locked=True))).scalar_one_or_none()
            if row is None:
                return False
            update_id = row.update_id
            # No external calls: receipt, channel changes, events and notices commit together.
            event = Update.model_validate(row.payload)
            svc: ChannelService = ctx.extras["channelmanager"]
            if event.my_chat_member:
                await svc.membership(session, event.my_chat_member, row.update_id)
            from bots.channelmanager import members
            if event.chat_join_request:
                await members.observe_request(session, ctx, event.chat_join_request, row.update_id, row.created_at)
            if event.chat_member:
                await members.observe_member(session, ctx, event.chat_member, row.update_id)
            if event.channel_post or event.edited_channel_post:
                from bots.channelmanager.automation import ingest
                source_message = event.channel_post or event.edited_channel_post
                assert source_message is not None
                await members.observe_service(session, ctx, source_message)
                await ingest(session, ctx, source_message, row.update_id,
                    edited=event.edited_channel_post is not None, received_at=row.created_at, collection_seconds=settings.album_collection_seconds)
            row.status, row.payload, row.error_code = "completed", {}, None
            await session.commit()
            return True
    except Exception as exc:
        if update_id is None:
            raise
        async with ctx.sm() as session:
            row = await session.get(Inbox, (ctx.bot_id, update_id), with_for_update=True)
            if row is not None and row.status == "pending":
                row.attempts += 1
                row.status = "failed" if row.attempts >= 5 else "pending"
                row.available_at = utcnow() + timedelta(seconds=min(2 ** row.attempts, 60))
                row.error_code = type(exc).__name__[:64]
                await session.commit()
        return True


async def process_payment(ctx: BotContext) -> bool:
    """Lease receipts without holding a database transaction across native authorization calls."""
    owner = uuid.uuid4().hex
    async with ctx.sm() as session:
        row = await session.scalar(select(Inbox).where(Inbox.bot_id == ctx.bot_id, Inbox.status == "pending",
            Inbox.event_type.in_({"billing_paid", "billing_refund"}), Inbox.available_at <= utcnow())
            .order_by(Inbox.update_id).limit(1).with_for_update(skip_locked=True))
        if row is None:
            return False
        row.lease_owner, row.lease_until = owner, utcnow() + timedelta(seconds=90)
        row.available_at = row.lease_until
        update_id, payload = row.update_id, row.payload
        await session.commit()
    code = None
    try:
        event = Update.model_validate(payload)
        message = event.message
        if message is None or message.from_user is None:
            raise ValueError("payment_actor")
        if message.successful_payment:
            await ctx.extras["billing"].fulfill(message.from_user, message.successful_payment, receipt=(update_id, owner))
        elif message.refunded_payment:
            await ctx.extras["billing"].apply_refund(message.refunded_payment.telegram_payment_charge_id)
        else:
            raise ValueError("payment_receipt")
    except Exception as exc:
        code = type(exc).__name__[:64]
    async with ctx.sm() as session:
        row = await session.get(Inbox, (ctx.bot_id, update_id), with_for_update=True)
        if row is None or row.lease_owner != owner:
            return True
        row.lease_owner, row.lease_until = None, None
        if code:
            row.attempts += 1
            row.status = "failed" if row.attempts >= 5 else "pending"
            row.available_at, row.error_code = utcnow() + timedelta(seconds=min(2 ** row.attempts, 60)), code
        else:
            row.status, row.payload, row.error_code = "completed", {}, None
        await session.commit()
    return True
