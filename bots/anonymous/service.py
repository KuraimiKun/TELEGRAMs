"""Anonymous inbox storage: links, messages, blocks, reports."""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bots.anonymous.models import AnonBlock, AnonLink, AnonMessage
from core.db.base import affected, utcnow

CODE_ALPHABET = string.ascii_lowercase + string.digits
CODE_LEN = 8
MAX_TEXT = 3500


def new_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LEN))


def valid_code(code: str) -> bool:
    return len(code) == CODE_LEN and all(c in CODE_ALPHABET for c in code)


@dataclass(slots=True)
class InboxStats:
    received: int
    sent: int
    replied: int
    week: int


class AnonService:
    def __init__(self, sm: async_sessionmaker[AsyncSession], bot_id: int) -> None:
        self.sm = sm
        self.bot_id = bot_id

    # ------------------------------------------------------------------ links
    async def link_for(self, user_id: int) -> AnonLink:
        """The user's link, created on first use (retrying on the rare code collision)."""
        async with self.sm() as s:
            link = await s.get(AnonLink, (self.bot_id, user_id))
            if link is not None:
                return link
        for _ in range(5):
            try:
                async with self.sm() as s:
                    link = AnonLink(bot_id=self.bot_id, user_id=user_id, code=new_code())
                    s.add(link)
                    await s.commit()
                    return link
            except IntegrityError:
                async with self.sm() as s:  # a concurrent request may have created it
                    existing = await s.get(AnonLink, (self.bot_id, user_id))
                    if existing is not None:
                        return existing
        raise RuntimeError("could not allocate a link code")

    async def by_code(self, code: str) -> AnonLink | None:
        if not valid_code(code):
            return None
        async with self.sm() as s:
            stmt = select(AnonLink).where(AnonLink.bot_id == self.bot_id, AnonLink.code == code)
            return (await s.execute(stmt)).scalar_one_or_none()

    async def get_link(self, user_id: int) -> AnonLink | None:
        async with self.sm() as s:
            return await s.get(AnonLink, (self.bot_id, user_id))

    async def reset_code(self, user_id: int) -> AnonLink:
        await self.link_for(user_id)
        for _ in range(5):
            try:
                async with self.sm() as s:
                    await s.execute(
                        update(AnonLink)
                        .where(AnonLink.bot_id == self.bot_id, AnonLink.user_id == user_id)
                        .values(code=new_code())
                    )
                    await s.commit()
                    break
            except IntegrityError:
                continue
        return await self.link_for(user_id)

    async def set_flag(self, user_id: int, **flags: bool) -> AnonLink:
        await self.link_for(user_id)
        async with self.sm() as s:
            await s.execute(
                update(AnonLink).where(AnonLink.bot_id == self.bot_id, AnonLink.user_id == user_id).values(**flags)
            )
            await s.commit()
        return await self.link_for(user_id)

    async def daily_prompt_users(self, after_user: int, limit: int = 500) -> list[int]:
        async with self.sm() as s:
            stmt = (
                select(AnonLink.user_id)
                .where(AnonLink.bot_id == self.bot_id, AnonLink.daily_prompt.is_(True), AnonLink.user_id > after_user)
                .order_by(AnonLink.user_id)
                .limit(limit)
            )
            return [int(x) for x in (await s.execute(stmt)).scalars()]

    # ------------------------------------------------------------------ messages
    async def record(
        self,
        *,
        owner_id: int,
        sender_id: int,
        recipient_id: int,
        kind: str,
        text: str | None,
        reply_to_id: int | None = None,
    ) -> AnonMessage:
        async with self.sm() as s:
            msg = AnonMessage(
                bot_id=self.bot_id,
                owner_id=owner_id,
                sender_id=sender_id,
                recipient_id=recipient_id,
                kind=kind,
                text=(text or "")[:MAX_TEXT] or None,
                reply_to_id=reply_to_id,
            )
            s.add(msg)
            await s.commit()
            return msg

    async def get(self, message_id: int) -> AnonMessage | None:
        async with self.sm() as s:
            msg = await s.get(AnonMessage, message_id)
            return msg if msg is not None and msg.bot_id == self.bot_id else None

    async def mark_reported(self, message_id: int) -> bool:
        async with self.sm() as s:
            res = await s.execute(
                update(AnonMessage)
                .where(AnonMessage.id == message_id, AnonMessage.bot_id == self.bot_id, AnonMessage.reported.is_(False))
                .values(reported=True)
            )
            await s.commit()
            return affected(res) > 0

    async def reported(self, limit: int = 10) -> list[AnonMessage]:
        async with self.sm() as s:
            stmt = (
                select(AnonMessage)
                .where(AnonMessage.bot_id == self.bot_id, AnonMessage.reported.is_(True))
                .order_by(AnonMessage.id.desc())
                .limit(limit)
            )
            return list((await s.execute(stmt)).scalars())

    async def stats(self, user_id: int) -> InboxStats:
        week_ago = utcnow() - timedelta(days=7)
        base = (AnonMessage.bot_id == self.bot_id,)
        async with self.sm() as s:

            async def count(*cond) -> int:
                return int((await s.execute(select(func.count()).select_from(AnonMessage).where(*base, *cond))).scalar_one())

            return InboxStats(
                received=await count(AnonMessage.recipient_id == user_id, AnonMessage.owner_id == user_id),
                sent=await count(AnonMessage.sender_id == user_id, AnonMessage.owner_id != user_id),
                replied=await count(AnonMessage.sender_id == user_id, AnonMessage.owner_id == user_id),
                week=await count(
                    AnonMessage.recipient_id == user_id,
                    AnonMessage.owner_id == user_id,
                    AnonMessage.created_at >= week_ago,
                ),
            )

    async def totals(self) -> dict[str, int]:
        day_ago = utcnow() - timedelta(days=1)
        async with self.sm() as s:

            async def count(*cond) -> int:
                stmt = select(func.count()).select_from(AnonMessage).where(AnonMessage.bot_id == self.bot_id, *cond)
                return int((await s.execute(stmt)).scalar_one())

            links = int(
                (await s.execute(select(func.count()).select_from(AnonLink).where(AnonLink.bot_id == self.bot_id))).scalar_one()
            )
            return {
                "links": links,
                "messages": await count(),
                "today": await count(AnonMessage.created_at >= day_ago),
                "reports": await count(AnonMessage.reported.is_(True)),
            }

    # ------------------------------------------------------------------ blocks
    async def block(self, owner_id: int, sender_id: int) -> None:
        async with self.sm() as s:
            if await s.get(AnonBlock, (self.bot_id, owner_id, sender_id)) is None:
                s.add(AnonBlock(bot_id=self.bot_id, owner_id=owner_id, sender_id=sender_id))
                await s.commit()

    async def is_blocked(self, owner_id: int, sender_id: int) -> bool:
        async with self.sm() as s:
            return await s.get(AnonBlock, (self.bot_id, owner_id, sender_id)) is not None

    async def unblock_all(self, owner_id: int) -> int:
        async with self.sm() as s:
            res = await s.execute(delete(AnonBlock).where(AnonBlock.bot_id == self.bot_id, AnonBlock.owner_id == owner_id))
            await s.commit()
            return affected(res)
