"""Feedback bot tables: which owner-side message belongs to which visitor (for replies)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base, BigInt, TZDateTime, utcnow


class FeedbackThread(Base):
    __tablename__ = "fb_threads"
    __table_args__ = (Index("ix_fb_threads_user", "bot_id", "user_id"),)

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    inbox_chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=False)
    inbox_msg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    user_id: Mapped[int] = mapped_column(BigInt)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
