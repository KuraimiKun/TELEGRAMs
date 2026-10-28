"""VIP subscription and plan management scoped to a bot.

Every change of ``vip_until`` is written to the ``vip_grants`` ledger (source: payment, referral, admin,
refund, revoke), so refunds remove only the time that was paid for and admins can audit any account.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.db.base import utcnow
from core.db.models import Bot, BotUser, Payment, Plan, VipGrant
from core.log import get_logger
from core.sdk.module import PlanSpec

log = get_logger(__name__)


class PlanError(ValueError):
    pass


def validate_plan(name: str, days: int, stars: int) -> None:
    if not name.strip() or len(name) > 64:
        raise PlanError("name must be 1-64 characters")
    if days <= 0 or days > 3650:
        raise PlanError("days must be between 1 and 3650")
    if stars < 1 or stars > 100_000:
        raise PlanError("stars must be between 1 and 100000")


class SubscriptionService:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession], bot_id: int) -> None:
        self.sm = sessionmaker
        self.bot_id = bot_id

    # ------------------------------------------------------------------ plans
    async def ensure_plans(self, specs: list[PlanSpec]) -> None:
        """Seed default plans the first time a bot starts (never re-adds plans an admin removed)."""
        if not specs:
            return
        async with self.sm() as session:
            # Lock the bot row so concurrently starting processes don't both seed.
            await session.execute(select(Bot.id).where(Bot.id == self.bot_id).with_for_update())
            stmt = select(Plan.id).where(Plan.bot_id == self.bot_id).limit(1)
            if (await session.execute(stmt)).first() is None:
                for spec in specs:
                    session.add(
                        Plan(
                            bot_id=self.bot_id,
                            name=spec.name,
                            days=spec.days,
                            stars=spec.stars,
                            active=True,
                            sort=spec.sort,
                        )
                    )
            await session.commit()

    async def list_active_plans(self) -> list[Plan]:
        async with self.sm() as session:
            stmt = (
                select(Plan)
                .where((Plan.bot_id == self.bot_id) | (Plan.bot_id.is_(None)), Plan.active.is_(True))
                .order_by(Plan.sort, Plan.stars)
            )
            return list((await session.execute(stmt)).scalars().all())

    async def list_plans(self) -> list[Plan]:
        """All plans visible to this bot's admins (own + global), active or not."""
        async with self.sm() as session:
            stmt = (
                select(Plan)
                .where((Plan.bot_id == self.bot_id) | (Plan.bot_id.is_(None)))
                .order_by(Plan.sort, Plan.stars)
            )
            return list((await session.execute(stmt)).scalars().all())

    async def get_plan(self, plan_id: int) -> Plan | None:
        async with self.sm() as session:
            plan = await session.get(Plan, plan_id)
            if plan and plan.bot_id not in (self.bot_id, None):
                return None
            return plan

    async def add_or_update_plan(
        self,
        plan_id: int | None,
        name: str,
        days: int,
        stars: int,
        active: bool = True,
        sort: int = 0,
        *,
        allow_global: bool = False,
    ) -> Plan:
        """Create or edit a plan. Global plans (shared by all bots) need ``allow_global`` (super-admins)."""
        validate_plan(name, days, stars)
        async with self.sm() as session:
            if plan_id:
                plan = await session.get(Plan, plan_id)
                if plan is None or plan.bot_id not in (self.bot_id, None):
                    raise PlanError("plan not found")
                if plan.bot_id is None and not allow_global:
                    raise PlanError("global plans can only be edited by a super-admin")
                plan.name, plan.days, plan.stars, plan.active, plan.sort = name.strip(), days, stars, active, sort
            else:
                plan = Plan(bot_id=self.bot_id, name=name.strip(), days=days, stars=stars, active=active, sort=sort)
                session.add(plan)
            await session.commit()
            return plan

    async def set_plan_active(self, plan_id: int, active: bool, *, allow_global: bool = False) -> Plan:
        plan = await self.get_plan(plan_id)
        if plan is None:
            raise PlanError("plan not found")
        return await self.add_or_update_plan(
            plan.id, plan.name, plan.days, plan.stars, active, plan.sort, allow_global=allow_global
        )

    async def delete_plan(self, plan_id: int, *, allow_global: bool = False) -> None:
        plan = await self.get_plan(plan_id)
        if plan is None:
            raise PlanError("plan not found")
        if plan.bot_id is None and not allow_global:
            raise PlanError("global plans can only be deleted by a super-admin")
        async with self.sm() as session:
            await session.execute(delete(Plan).where(Plan.id == plan_id))
            await session.commit()

    # ------------------------------------------------------------------ VIP time
    async def extend_vip_in_session(
        self,
        session: AsyncSession,
        user_id: int,
        days: int,
        *,
        source: str = "admin",
        payment_id: int | None = None,
        actor_id: int | None = None,
    ) -> datetime:
        """Change VIP by ``days`` (may be negative) inside the caller's transaction, under a row lock."""
        stmt = (
            select(BotUser)
            .where(BotUser.bot_id == self.bot_id, BotUser.user_id == user_id)
            .with_for_update(of=BotUser)
        )
        user = (await session.execute(stmt)).scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not registered in bot {self.bot_id}")

        now = utcnow()
        current = user.vip_until if (user.vip_until and user.vip_until > now) else now
        new_until = max(now, current + timedelta(days=days))
        user.vip_until = new_until if new_until > now else None
        session.add(
            VipGrant(
                bot_id=self.bot_id,
                user_id=user_id,
                days=days,
                source=source,
                payment_id=payment_id,
                actor_id=actor_id,
                created_at=now,
            )
        )
        return new_until

    async def grant_vip(self, user_id: int, days: int, *, source: str = "admin", actor_id: int | None = None) -> datetime:
        """Extend or activate VIP by N days for the user in this bot."""
        async with self.sm() as session:
            new_until = await self.extend_vip_in_session(session, user_id, days, source=source, actor_id=actor_id)
            await session.commit()
            return new_until

    async def revoke_vip(self, user_id: int, *, actor_id: int | None = None) -> None:
        async with self.sm() as session:
            stmt = (
                select(BotUser)
                .where(BotUser.bot_id == self.bot_id, BotUser.user_id == user_id)
                .with_for_update(of=BotUser)
            )
            user = (await session.execute(stmt)).scalar_one_or_none()
            if not user:
                return
            now = utcnow()
            remaining = max(0, round((user.vip_until - now).total_seconds() / 86400)) if user.vip_until else 0
            user.vip_until = None
            session.add(
                VipGrant(bot_id=self.bot_id, user_id=user_id, days=-remaining, source="revoke", actor_id=actor_id)
            )
            await session.commit()

    async def ledger(self, user_id: int, limit: int = 10) -> list[VipGrant]:
        async with self.sm() as session:
            stmt = (
                select(VipGrant)
                .where(VipGrant.bot_id == self.bot_id, VipGrant.user_id == user_id)
                .order_by(VipGrant.id.desc())
                .limit(limit)
            )
            return list((await session.execute(stmt)).scalars().all())

    async def payments_of(self, user_id: int, limit: int = 10) -> list[Payment]:
        async with self.sm() as session:
            stmt = (
                select(Payment)
                .where(Payment.bot_id == self.bot_id, Payment.user_id == user_id)
                .order_by(Payment.id.desc())
                .limit(limit)
            )
            return list((await session.execute(stmt)).scalars().all())

    async def count_vip(self) -> int:
        async with self.sm() as session:
            stmt = select(func.count()).where(BotUser.bot_id == self.bot_id, BotUser.vip_until > utcnow())
            return int((await session.execute(stmt)).scalar_one() or 0)
