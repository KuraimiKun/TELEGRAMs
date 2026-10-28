"""CV report summaries and payment entitlements. Original CVs are never persisted here."""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base, BigInt, JsonType, TZDateTime, utcnow


class CVReport(Base):
    __tablename__ = "cv_reports"
    __table_args__ = (Index("ix_cv_reports_user_created", "bot_id", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(BigInt)
    score: Mapped[int] = mapped_column(Integer)
    summary: Mapped[dict[str, Any]] = mapped_column(JsonType)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class CVInvoice(Base):
    __tablename__ = "cv_invoices"
    __table_args__ = (Index("ix_cv_invoices_user", "bot_id", "user_id"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(BigInt)
    stars: Mapped[int] = mapped_column(Integer)
    paid_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    expires_at: Mapped[datetime] = mapped_column(TZDateTime())
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class CVReviewCredit(Base):
    __tablename__ = "cv_review_credits"
    __table_args__ = (Index("ix_cv_review_credits_user", "bot_id", "user_id", "used_at"),)

    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("cv_invoices.id"), unique=True)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(BigInt)
    used_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
