"""Only operational metadata is persisted; document contents never enter the database."""

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base, BigInt, TZDateTime, utcnow


class DocumentJob(Base):
    __tablename__ = "dt_jobs"
    __table_args__ = (Index("ix_dt_jobs_bot_created", "bot_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    operation: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(16))
    pages: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
