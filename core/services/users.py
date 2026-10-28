"""User repository and referral management scoped to a bot."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.db.base import affected, upsert, utcnow
from core.db.models import BotUser, User


class UserService:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession], bot_id: int) -> None:
        self.sm = sessionmaker
        self.bot_id = bot_id

    async def get_or_create(
        self,
        user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        language_code: str | None = None,
        referred_by: int | None = None,
        *,
        unblock: bool = True,
    ) -> tuple[BotUser, bool]:
        """Upsert the global User + bot-scoped BotUser. Safe under concurrent updates from one user."""
        now = utcnow()
        async with self.sm() as session:
            # 1. Upsert global profile (only overwrite names when Telegram sent them).
            profile_set: dict[str, Any] = {"last_seen": now}
            if username:
                profile_set["username"] = username
            if first_name:
                profile_set["first_name"] = first_name
            await session.execute(
                upsert(session, User)
                .values(
                    id=user_id,
                    username=username,
                    first_name=first_name,
                    language_code=language_code,
                    created_at=now,
                    last_seen=now,
                )
                .on_conflict_do_update(index_elements=[User.id], set_=profile_set)
            )

            # 2. Referrer must be a member of *this* bot, otherwise the credit would be lost.
            ref_parent: int | None = None
            if referred_by and referred_by != user_id:
                exists = await session.execute(
                    select(BotUser.user_id).where(BotUser.bot_id == self.bot_id, BotUser.user_id == referred_by)
                )
                if exists.scalar_one_or_none() is not None:
                    ref_parent = referred_by

            # 3. Insert membership if missing; rowcount tells us whether this is a new member.
            result = await session.execute(
                upsert(session, BotUser)
                .values(
                    bot_id=self.bot_id,
                    user_id=user_id,
                    lang=language_code,
                    referred_by=ref_parent,
                    prefs={},
                    started_at=now,
                    last_seen=now,
                )
                .on_conflict_do_nothing(index_elements=[BotUser.bot_id, BotUser.user_id])
            )
            is_new = bool(affected(result))

            if not is_new:
                values: dict[str, Any] = {"last_seen": now}
                if unblock:
                    values["blocked_bot"] = False
                await session.execute(
                    update(BotUser)
                    .where(BotUser.bot_id == self.bot_id, BotUser.user_id == user_id)
                    .values(**values)
                )
            await session.commit()

            stmt = (
                select(BotUser)
                .where(BotUser.bot_id == self.bot_id, BotUser.user_id == user_id)
                .execution_options(populate_existing=True)
            )
            bot_user = (await session.execute(stmt)).scalar_one()
            return bot_user, is_new

    async def get(self, user_id: int) -> BotUser | None:
        async with self.sm() as session:
            stmt = select(BotUser).where(BotUser.bot_id == self.bot_id, BotUser.user_id == user_id)
            return (await session.execute(stmt)).scalar_one_or_none()

    async def set_lang(self, user_id: int, lang: str) -> None:
        async with self.sm() as session:
            stmt = (
                update(BotUser)
                .where(BotUser.bot_id == self.bot_id, BotUser.user_id == user_id)
                .values(lang=lang)
            )
            await session.execute(stmt)
            await session.commit()

    async def update_pref(self, user_id: int, key: str, value: Any) -> None:
        async with self.sm() as session:
            stmt = select(BotUser).where(BotUser.bot_id == self.bot_id, BotUser.user_id == user_id)
            bot_user = (await session.execute(stmt)).scalar_one_or_none()
            if bot_user:
                prefs = dict(bot_user.prefs or {})
                prefs[key] = value
                bot_user.prefs = prefs
                await session.commit()

    async def mark_blocked(self, user_id: int) -> None:
        async with self.sm() as session:
            stmt = (
                update(BotUser)
                .where(BotUser.bot_id == self.bot_id, BotUser.user_id == user_id)
                .values(blocked_bot=True)
            )
            await session.execute(stmt)
            await session.commit()

    async def set_banned(self, user_id: int, banned: bool, reason: str | None = None) -> bool:
        async with self.sm() as session:
            stmt = select(BotUser).where(BotUser.bot_id == self.bot_id, BotUser.user_id == user_id)
            bot_user = (await session.execute(stmt)).scalar_one_or_none()
            if not bot_user:
                return False
            bot_user.is_banned = banned
            bot_user.ban_reason = reason if banned else None
            await session.commit()
            return True

    async def record_action(
        self,
        user_id: int,
        referral_required: int = 5,
        referral_enabled: bool = True,
    ) -> int | None:
        """Atomically increment the action counter and qualify the user's referral on first action.

        Returns the referrer's user_id if they just reached a reward milestone.
        """
        async with self.sm() as session:
            me = BotUser.bot_id == self.bot_id, BotUser.user_id == user_id
            await session.execute(update(BotUser).where(*me).values(actions_count=BotUser.actions_count + 1))

            # Conditional update = exactly-once qualification even with concurrent actions.
            qualified = await session.execute(
                update(BotUser)
                .where(*me, BotUser.referral_qualified.is_(False), BotUser.referred_by.is_not(None))
                .values(referral_qualified=True)
                .returning(BotUser.referred_by)
            )
            parent_id = qualified.scalar_one_or_none()

            reward_recipient: int | None = None
            if parent_id is not None:
                bumped = await session.execute(
                    update(BotUser)
                    .where(BotUser.bot_id == self.bot_id, BotUser.user_id == parent_id)
                    .values(referral_count=BotUser.referral_count + 1)
                    .returning(BotUser.referral_count)
                )
                count = bumped.scalar_one_or_none()
                if count and referral_enabled and referral_required > 0 and count % referral_required == 0:
                    reward_recipient = parent_id

            await session.commit()
            return reward_recipient

    async def count_users(self) -> int:
        async with self.sm() as session:
            stmt = select(func.count(BotUser.user_id)).where(BotUser.bot_id == self.bot_id)
            return int((await session.execute(stmt)).scalar_one() or 0)

    # ------------------------------------------------------------------ admin queries
    async def list_page(self, kind: str, page: int, per_page: int = 10) -> tuple[list[BotUser], int]:
        """Users for the admin list: kind = new | vip | banned | active. Returns (page_items, total)."""
        conds = [BotUser.bot_id == self.bot_id]
        order: Any = BotUser.started_at.desc()
        now = utcnow()
        if kind == "vip":
            conds.append(BotUser.vip_until > now)
            order = BotUser.vip_until.desc()
        elif kind == "banned":
            conds.append(BotUser.is_banned.is_(True))
        elif kind == "active":
            order = BotUser.last_seen.desc()
        async with self.sm() as session:
            total = int((await session.execute(select(func.count()).select_from(BotUser).where(*conds))).scalar_one())
            stmt = select(BotUser).where(*conds).order_by(order).offset(max(0, page - 1) * per_page).limit(per_page)
            return list((await session.execute(stmt)).scalars().all()), total

    async def search(self, query: str, limit: int = 10) -> list[BotUser]:
        """Find members by numeric id, exact @username, or name/username substring (LIKE-escaped)."""
        q = query.strip().lstrip("@")
        if not q:
            return []
        if q.isdigit():
            u = await self.get(int(q))
            return [u] if u else []
        pattern = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        async with self.sm() as session:
            stmt = (
                select(BotUser)
                .join(User, User.id == BotUser.user_id)
                .where(
                    BotUser.bot_id == self.bot_id,
                    User.username.ilike(pattern, escape="\\") | User.first_name.ilike(pattern, escape="\\"),
                )
                .order_by(BotUser.last_seen.desc())
                .limit(limit)
            )
            return list((await session.execute(stmt)).scalars().all())

    async def set_blocked(self, user_id: int, blocked: bool) -> None:
        async with self.sm() as session:
            await session.execute(
                update(BotUser)
                .where(BotUser.bot_id == self.bot_id, BotUser.user_id == user_id)
                .values(blocked_bot=blocked)
            )
            await session.commit()
