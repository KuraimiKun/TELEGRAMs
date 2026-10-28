"""Group chat settings and forced-subscription channels scoped to a bot."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.db.base import upsert
from core.db.models import ForceSubChannel, Group


class GroupService:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession], bot_id: int) -> None:
        self.sm = sessionmaker
        self.bot_id = bot_id

    async def get_or_create(self, chat_id: int, title: str | None = None) -> Group:
        async with self.sm() as session:
            await session.execute(
                upsert(session, Group)
                .values(bot_id=self.bot_id, chat_id=chat_id, title=title, active=True, auto_download=True, prefs={})
                .on_conflict_do_nothing(index_elements=[Group.bot_id, Group.chat_id])
            )
            stmt = select(Group).where(Group.bot_id == self.bot_id, Group.chat_id == chat_id)
            grp = (await session.execute(stmt)).scalar_one()
            if title and grp.title != title:
                grp.title = title
            await session.commit()
            return grp

    async def toggle_auto_download(self, chat_id: int) -> bool:
        async with self.sm() as session:
            stmt = select(Group).where(Group.bot_id == self.bot_id, Group.chat_id == chat_id)
            grp = (await session.execute(stmt)).scalar_one_or_none()
            if not grp:
                grp = Group(bot_id=self.bot_id, chat_id=chat_id, auto_download=False)
                session.add(grp)
                state = False
            else:
                grp.auto_download = not grp.auto_download
                state = grp.auto_download
            await session.commit()
            return state

    async def set_active(self, chat_id: int, active: bool, title: str | None = None) -> None:
        """Track the bot being added to / removed from a group."""
        async with self.sm() as session:
            await session.execute(
                upsert(session, Group)
                .values(bot_id=self.bot_id, chat_id=chat_id, title=title, active=active, auto_download=True, prefs={})
                .on_conflict_do_update(
                    index_elements=[Group.bot_id, Group.chat_id],
                    set_={"active": active, **({"title": title} if title else {})},
                )
            )
            await session.commit()

    async def count_active(self) -> int:
        async with self.sm() as session:
            stmt = select(func.count()).where(Group.bot_id == self.bot_id, Group.active.is_(True))
            return int((await session.execute(stmt)).scalar_one() or 0)

    async def list_channels(self, include_inactive: bool = False) -> list[ForceSubChannel]:
        async with self.sm() as session:
            stmt = select(ForceSubChannel).where(ForceSubChannel.bot_id == self.bot_id)
            if not include_inactive:
                stmt = stmt.where(ForceSubChannel.active.is_(True))
            return list((await session.execute(stmt.order_by(ForceSubChannel.title))).scalars().all())

    async def add_channel(self, chat_id: int, title: str, invite_link: str) -> ForceSubChannel:
        async with self.sm() as session:
            await session.execute(
                upsert(session, ForceSubChannel)
                .values(bot_id=self.bot_id, chat_id=chat_id, title=title, invite_link=invite_link, active=True)
                .on_conflict_do_update(
                    index_elements=[ForceSubChannel.bot_id, ForceSubChannel.chat_id],
                    set_={"title": title, "invite_link": invite_link, "active": True},
                )
            )
            await session.commit()
            return ForceSubChannel(bot_id=self.bot_id, chat_id=chat_id, title=title, invite_link=invite_link, active=True)

    async def toggle_channel(self, chat_id: int) -> bool | None:
        async with self.sm() as session:
            ch = await session.get(ForceSubChannel, (self.bot_id, chat_id))
            if ch is None:
                return None
            ch.active = not ch.active
            await session.commit()
            return ch.active

    async def delete_channel(self, chat_id: int) -> None:
        async with self.sm() as session:
            stmt = delete(ForceSubChannel).where(ForceSubChannel.bot_id == self.bot_id, ForceSubChannel.chat_id == chat_id)
            await session.execute(stmt)
            await session.commit()
