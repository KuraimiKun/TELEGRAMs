"""Bot-specific ORM models for SocialDownload (table prefix: sd_)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base, TZDateTime, utcnow


class Download(Base):
    __tablename__ = "sd_downloads"
    __table_args__ = (Index("ix_sd_downloads_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    url: Mapped[str] = mapped_column(Text)
    quality: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), index=True)  # ok | failed
    error_code: Mapped[str | None] = mapped_column(String(32))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    from_cache: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow, index=True)
