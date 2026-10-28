"""Tables owned by the Notes & Reminders bot. Every table name starts with "notes_"."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base, BigInt, TZDateTime, utcnow


class Note(Base):
    __tablename__ = "notes_notes"
    __table_args__ = (Index("ix_notes_notes_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class Reminder(Base):
    __tablename__ = "notes_reminders"
    __table_args__ = (
        Index("ix_notes_reminders_due", "sent_at", "due_at"),
        Index("ix_notes_reminders_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt)
    chat_id: Mapped[int] = mapped_column(BigInt)
    text: Mapped[str] = mapped_column(String(1000))
    lang: Mapped[str] = mapped_column(String(8), default="en")
    due_at: Mapped[datetime] = mapped_column(TZDateTime())
    sent_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
