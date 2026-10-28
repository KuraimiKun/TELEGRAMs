"""Tables of the anonymous inbox. Every row carries ``bot_id``: user-created copies share these tables."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base, BigInt, TZDateTime, utcnow


class AnonLink(Base):
    """A user's personal inbox link ``t.me/<bot>?start=<code>``."""

    __tablename__ = "anon_links"
    __table_args__ = (UniqueConstraint("bot_id", "code", name="uq_anon_links_code"),)

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=False)
    code: Mapped[str] = mapped_column(String(16))
    # Inbox closed: the link shows "not receiving messages right now".
    paused: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # Opted in to the daily question prompt.
    daily_prompt: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class AnonMessage(Base):
    """One delivered message. ``owner_id`` is the inbox owner of the thread: whoever is not the owner stays
    anonymous, so the owner's replies show their name while the visitor's never do."""

    __tablename__ = "anon_messages"
    __table_args__ = (
        Index("ix_anon_messages_recipient", "bot_id", "recipient_id", "created_at"),
        Index("ix_anon_messages_sender", "bot_id", "sender_id", "created_at"),
        Index("ix_anon_messages_reported", "bot_id", "reported"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"))
    owner_id: Mapped[int] = mapped_column(BigInt)
    sender_id: Mapped[int] = mapped_column(BigInt)
    recipient_id: Mapped[int] = mapped_column(BigInt)
    reply_to_id: Mapped[int | None] = mapped_column(BigInteger)
    kind: Mapped[str] = mapped_column(String(16))  # text | photo | video | voice | sticker | ...
    text: Mapped[str | None] = mapped_column(Text)  # text or caption (kept for reports and hints)
    reported: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class AnonBlock(Base):
    """``owner_id`` no longer receives anything from ``sender_id`` (who is never told who blocked them)."""

    __tablename__ = "anon_blocks"

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=False)
    sender_id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=False)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
