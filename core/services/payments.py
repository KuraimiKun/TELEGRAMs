"""Telegram Stars payment and refund processing scoped to a bot."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.db.base import upsert, utcnow
from core.db.models import BotUser, Payment
from core.log import get_logger
from core.observability import PAYMENT_STARS, PAYMENTS, REFUNDS
from core.services.subscriptions import SubscriptionService

log = get_logger(__name__)


@dataclass(slots=True)
class RefundResult:
    user_id: int
    days: int
    stars: int
    vip_until: datetime | None


class PaymentService:
    def __init__(
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
        bot_id: int,
        subs: SubscriptionService,
        slug: str = "",
    ) -> None:
        self.sm = sessionmaker
        self.bot_id = bot_id
        self.subs = subs
        self.slug = slug or str(bot_id)

    async def record_one_off_payment(
        self,
        user_id: int,
        stars: int,
        charge_id: str,
        grant: Callable[[AsyncSession, int], Awaitable[None]],
    ) -> bool:
        """Record a zero-day purchase and its entitlement atomically, once per Telegram charge.

        ``grant`` validates/locks the server-issued invoice and inserts the module's entitlement in
        this same transaction. If validation or insertion fails, neither the payment nor grant survives.
        """
        async with self.sm() as session:
            result = await session.execute(
                upsert(session, Payment).values(
                    bot_id=self.bot_id, user_id=user_id, plan_id=None, stars=stars, days=0,
                    charge_id=charge_id, status="paid", created_at=utcnow(),
                ).on_conflict_do_nothing(index_elements=[Payment.charge_id]).returning(Payment.id)
            )
            payment_id = result.scalar_one_or_none()
            if payment_id is None:
                await session.rollback()
                return False
            await grant(session, payment_id)
            await session.commit()
        PAYMENTS.labels(self.slug).inc()
        PAYMENT_STARS.labels(self.slug).inc(stars)
        return True

    async def record_payment(
        self,
        user_id: int,
        plan_id: int | None,
        stars: int,
        days: int,
        charge_id: str,
    ) -> tuple[datetime, bool]:
        """Record a Stars payment and grant VIP in ONE transaction.

        Idempotent on ``charge_id``: a redelivered update returns ``(current_until, False)`` and grants nothing.
        """
        async with self.sm() as session:
            result = await session.execute(
                upsert(session, Payment)
                .values(
                    bot_id=self.bot_id,
                    user_id=user_id,
                    plan_id=plan_id,
                    stars=stars,
                    days=days,
                    charge_id=charge_id,
                    status="paid",
                    created_at=utcnow(),
                )
                .on_conflict_do_nothing(index_elements=[Payment.charge_id])
                .returning(Payment.id)
            )
            payment_id = result.scalar_one_or_none()
            if payment_id is None:
                await session.rollback()
                log.warning("duplicate_payment_received", charge_id=charge_id, user_id=user_id, bot_id=self.bot_id)
                u_stmt = select(BotUser.vip_until).where(BotUser.bot_id == self.bot_id, BotUser.user_id == user_id)
                current = (await session.execute(u_stmt)).scalar_one_or_none()
                return current or utcnow(), False

            new_until = await self.subs.extend_vip_in_session(
                session, user_id, days, source="payment", payment_id=payment_id
            )
            await session.commit()
            log.info("payment_recorded", charge_id=charge_id, user_id=user_id, stars=stars, days=days)
            PAYMENTS.labels(self.slug).inc()
            PAYMENT_STARS.labels(self.slug).inc(stars)
            return new_until, True

    async def get(self, payment_id: int) -> Payment | None:
        async with self.sm() as session:
            p = await session.get(Payment, payment_id)
            return p if p and p.bot_id == self.bot_id else None

    async def process_refund(self, charge_id: str, *, actor_id: int | None = None) -> RefundResult | None:
        """Mark a payment refunded and take back exactly the days it bought (other VIP time is kept).

        Idempotent: returns None if the payment is unknown or already refunded.
        """
        async with self.sm() as session:
            stmt = (
                select(Payment)
                .where(Payment.charge_id == charge_id, Payment.bot_id == self.bot_id)
                .with_for_update()
            )
            payment = (await session.execute(stmt)).scalar_one_or_none()
            if not payment or payment.status == "refunded":
                return None
            payment.status = "refunded"
            payment.refunded_at = utcnow()
            if payment.days:
                until = await self.subs.extend_vip_in_session(
                    session, payment.user_id, -payment.days, source="refund", payment_id=payment.id, actor_id=actor_id
                )
            else:
                # One-off entitlements check Payment.status when used; do not mutate unrelated VIP time.
                until = (await session.execute(select(BotUser.vip_until).where(
                    BotUser.bot_id == self.bot_id, BotUser.user_id == payment.user_id,
                ))).scalar_one_or_none() or utcnow()
            await session.commit()
            log.info("payment_refunded", charge_id=charge_id, user_id=payment.user_id, days=payment.days)
            REFUNDS.labels(self.slug).inc()
            return RefundResult(
                user_id=payment.user_id,
                days=payment.days,
                stars=payment.stars,
                vip_until=until if until > utcnow() else None,
            )
