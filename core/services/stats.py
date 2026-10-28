"""Stats service for bot-level and cross-bot analytics (aggregate queries, no N+1)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.db.base import utcnow
from core.db.models import Bot, BotUser, Payment, User


class StatsService:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession], bot_id: int) -> None:
        self.sm = sessionmaker
        self.bot_id = bot_id

    async def get_overview(self) -> dict[str, Any]:
        """Aggregate analytics for this bot: two queries total."""
        now = utcnow()
        paid = Payment.status == "paid"
        async with self.sm() as session:
            users = (
                await session.execute(
                    select(
                        func.count(),
                        func.count().filter(BotUser.last_seen >= now - timedelta(days=1)),
                        func.count().filter(BotUser.last_seen >= now - timedelta(days=7)),
                        func.count().filter(BotUser.vip_until > now),
                        func.coalesce(func.sum(BotUser.actions_count), 0),
                    ).where(BotUser.bot_id == self.bot_id)
                )
            ).one()
            revenue = (
                await session.execute(
                    select(
                        func.coalesce(func.sum(Payment.stars).filter(paid), 0),
                        func.coalesce(func.sum(Payment.stars).filter(paid, Payment.created_at >= now - timedelta(days=30)), 0),
                    ).where(Payment.bot_id == self.bot_id)
                )
            ).one()
        total, active_24h, active_7d, vip, actions = (int(v or 0) for v in users)
        return {
            "total_users": total,
            "active_24h": active_24h,
            "active_7d": active_7d,
            "vip_users": vip,
            "total_actions": actions,
            "revenue_total": int(revenue[0] or 0),
            "revenue_30d": int(revenue[1] or 0),
        }

    async def get_platform_overview(self) -> dict[str, Any]:
        """Cross-bot analytics for the super-admin dashboard (grouped queries)."""
        async with self.sm() as session:
            total_global_users = int((await session.execute(select(func.count(User.id)))).scalar_one() or 0)
            bots = list((await session.execute(select(Bot).where(Bot.active.is_(True)).order_by(Bot.slug))).scalars())
            users_by_bot = dict(
                (await session.execute(select(BotUser.bot_id, func.count()).group_by(BotUser.bot_id))).tuples().all()
            )
            revenue_by_bot = dict(
                (
                    await session.execute(
                        select(Payment.bot_id, func.sum(Payment.stars))
                        .where(Payment.status == "paid")
                        .group_by(Payment.bot_id)
                    )
                ).tuples().all()
            )
        summaries = [
            {
                "id": b.id,
                "slug": b.slug,
                "title": b.title,
                "username": b.username,
                "users": int(users_by_bot.get(b.id, 0)),
                "revenue": int(revenue_by_bot.get(b.id) or 0),
            }
            for b in bots
        ]
        return {
            "total_global_users": total_global_users,
            "total_bots": len(bots),
            "total_revenue": sum(s["revenue"] for s in summaries),
            "bots": summaries,
        }
