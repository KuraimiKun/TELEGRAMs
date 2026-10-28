"""Server-issued, bot/user/price-bound Stars invoices with atomic one-use entitlements."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bots.cvbot.models import CVInvoice, CVReviewCredit
from core.db.base import utcnow
from core.db.models import Payment
from core.sdk.context import BotContext

PREFIX = "c_cv:"


class InvalidInvoice(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProPayload:
    slug: str
    user_id: int
    stars: int
    nonce: str

    def encode(self) -> str:
        return f"{PREFIX}{self.slug}:{self.user_id}:{self.stars}:{self.nonce}"

    @classmethod
    def decode(cls, value: str) -> ProPayload | None:
        parts = value.split(":")
        if len(parts) != 5 or parts[0] != "c_cv":
            return None
        if not re.fullmatch(r"[a-z][a-z0-9_]{1,31}", parts[1]) or not re.fullmatch(r"[A-Za-z0-9_-]{22}", parts[4]):
            return None
        try:
            user_id, stars = int(parts[2]), int(parts[3])
        except ValueError:
            return None
        if user_id <= 0 or not 0 < stars <= 10000:
            return None
        return cls(parts[1], user_id, stars, parts[4])


class ProReviews:
    def __init__(self, ctx: BotContext) -> None:
        self.ctx = ctx

    async def issue(self, user_id: int, stars: int) -> ProPayload:
        payload = ProPayload(self.ctx.slug, user_id, stars, secrets.token_urlsafe(16))
        async with self.ctx.sm() as session:
            session.add(CVInvoice(
                id=payload.nonce, bot_id=self.ctx.bot_id, user_id=user_id, stars=stars,
                expires_at=utcnow() + timedelta(hours=1),
            ))
            await session.commit()
        return payload

    async def validate(self, raw: str, user_id: int, currency: str, amount: int, *, checkout: bool = True) -> ProPayload | None:
        payload = ProPayload.decode(raw)
        if payload is None or payload.slug != self.ctx.slug or payload.user_id != user_id:
            return None
        if currency != "XTR" or payload.stars != amount:
            return None
        async with self.ctx.sm() as session:
            invoice = await session.get(CVInvoice, payload.nonce)
            if invoice is None or invoice.bot_id != self.ctx.bot_id or invoice.user_id != user_id or invoice.stars != amount:
                return None
            if checkout and (invoice.paid_at is not None or invoice.expires_at <= utcnow()):
                return None
        return payload

    async def paid(self, payload: ProPayload, charge_id: str) -> bool:
        async def grant(session: AsyncSession, payment_id: int) -> None:
            invoice = (await session.execute(select(CVInvoice).where(CVInvoice.id == payload.nonce).with_for_update())).scalar_one_or_none()
            if invoice is None or invoice.paid_at is not None or invoice.bot_id != self.ctx.bot_id:
                raise InvalidInvoice("invoice has already been settled")
            if invoice.user_id != payload.user_id or invoice.stars != payload.stars:
                raise InvalidInvoice("invoice does not match purchase")
            invoice.paid_at = utcnow()
            session.add(CVReviewCredit(
                payment_id=payment_id, invoice_id=invoice.id, bot_id=self.ctx.bot_id,
                user_id=payload.user_id,
            ))

        try:
            return await self.ctx.payments.record_one_off_payment(payload.user_id, payload.stars, charge_id, grant)
        except InvalidInvoice:
            return False

    async def consume(self, user_id: int) -> int | None:
        async with self.ctx.sm() as session:
            available = select(CVReviewCredit.payment_id).join(Payment).where(
                CVReviewCredit.bot_id == self.ctx.bot_id, CVReviewCredit.user_id == user_id,
                CVReviewCredit.used_at.is_(None), Payment.status == "paid",
            ).order_by(CVReviewCredit.created_at).limit(1).scalar_subquery()
            credit = (await session.execute(update(CVReviewCredit).where(
                CVReviewCredit.payment_id == available, CVReviewCredit.used_at.is_(None),
            ).values(used_at=utcnow()).returning(CVReviewCredit.payment_id))).scalar_one_or_none()
            await session.commit()
            return credit

    async def restore(self, user_id: int, payment_id: int) -> None:
        async with self.ctx.sm() as session:
            await session.execute(update(CVReviewCredit).where(
                CVReviewCredit.bot_id == self.ctx.bot_id, CVReviewCredit.user_id == user_id,
                CVReviewCredit.payment_id == payment_id,
            ).values(used_at=None))
            await session.commit()
