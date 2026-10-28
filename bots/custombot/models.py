"""No-code bot content: a tree of pages. Each page has content and its children become its buttons."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base, BigInt, TZDateTime, utcnow


class CbNode(Base):
    __tablename__ = "cb_nodes"
    __table_args__ = (
        Index("ix_cb_nodes_parent", "bot_id", "parent_id", "position"),
        Index("ix_cb_nodes_command", "bot_id", "command"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"))
    parent_id: Mapped[int | None] = mapped_column(BigInteger)  # None = the root (/start) page
    position: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(64))  # button label
    command: Mapped[str | None] = mapped_column(String(32))  # optional /command opening this page
    text: Mapped[str | None] = mapped_column(Text)  # HTML
    media_kind: Mapped[str | None] = mapped_column(String(16))
    file_id: Mapped[str | None] = mapped_column(String(256))
    url: Mapped[str | None] = mapped_column(String(512))  # set = a link button, not a page
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
