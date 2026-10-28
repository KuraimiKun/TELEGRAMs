"""Semantic join receipts commit before effects; duplicates and unknown outcomes never replay."""
from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from functools import wraps

from aiogram.types import ChatMemberUpdated
from sqlalchemy import select, update

from bots.groupguard import allow_refs, authz
from bots.groupguard.models import GuardJoinReceipt
from core.db.base import affected, upsert, utcnow


def fingerprint(event: ChatMemberUpdated) -> str:
    payload = dict(chat_id=event.chat.id, user_id=event.new_chat_member.user.id, actor_id=event.from_user.id,
        date=int(event.date.timestamp()), old_status=event.old_chat_member.status, new_status=event.new_chat_member.status,
        old_is_member=getattr(event.old_chat_member, "is_member", None), new_is_member=getattr(event.new_chat_member, "is_member", None),
        via_request=event.via_join_request, via_folder=event.via_chat_folder_invite_link,
        invite=event.invite_link.invite_link if event.invite_link else None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def once(ctx):
    def decorate(handler):
        @wraps(handler)
        async def wrapped(event: ChatMemberUpdated):
            if not await authz.active_namespace(ctx):
                return
            identity = fingerprint(event)
            scope = dict(bot_id=ctx.bot_id, chat_id=event.chat.id, user_id=event.new_chat_member.user.id,
                fingerprint=identity)
            async with ctx.sm() as session:
                inserted = await session.execute(upsert(session, GuardJoinReceipt).values(**scope, status="processing",
                    created_at=utcnow(), updated_at=utcnow()).on_conflict_do_nothing())
                await session.commit()
                if affected(inserted) != 1:
                    return
            status = "uncertain"
            try:
                await allow_refs.remember(ctx,event)
                await handler(event)
                status = "completed"
            finally:
                async with ctx.sm() as session:
                    await session.execute(update(GuardJoinReceipt).filter_by(**scope).values(status=status, updated_at=utcnow()))
                    await session.commit()
        return wrapped
    return decorate


async def recover(ctx, limit: int = 100):
    async with ctx.sm() as session:
        stale = list((await session.execute(select(GuardJoinReceipt).where(GuardJoinReceipt.bot_id == ctx.bot_id,
            GuardJoinReceipt.status == "processing", GuardJoinReceipt.updated_at < utcnow()-timedelta(seconds=240))
            .limit(limit).with_for_update(skip_locked=True))).scalars())
        for row in stale:
            row.status = "uncertain"
            row.updated_at = utcnow()
        old = list((await session.execute(select(GuardJoinReceipt).where(GuardJoinReceipt.bot_id == ctx.bot_id,
            GuardJoinReceipt.created_at < utcnow()-timedelta(days=7)).order_by(GuardJoinReceipt.created_at)
            .limit(limit))).scalars())
        for row in old:
            await session.delete(row)
        await session.commit()
