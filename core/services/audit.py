"""Append-only audit trail of admin actions."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.db.base import utcnow
from core.db.models import AdminAuditLog
from core.log import get_logger

log = get_logger(__name__)


class AuditService:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession], bot_id: int) -> None:
        self.sm = sessionmaker
        self.bot_id = bot_id

    async def record(self, admin_id: int, action: str, target: str | int | None = None, **details: Any) -> None:
        """Never raises: auditing must not break the admin action itself (but failures are logged)."""
        try:
            async with self.sm() as session:
                session.add(
                    AdminAuditLog(
                        bot_id=self.bot_id,
                        admin_id=admin_id,
                        action=action,
                        target=str(target)[:128] if target is not None else None,
                        details={k: v for k, v in details.items() if v is not None},
                        created_at=utcnow(),
                    )
                )
                await session.commit()
            log.info("admin_action", bot_id=self.bot_id, admin_id=admin_id, action=action, target=target)
        except Exception as e:
            log.exception("audit_write_failed", action=action, error=str(e))

    async def recent(self, limit: int = 15) -> list[AdminAuditLog]:
        async with self.sm() as session:
            stmt = (
                select(AdminAuditLog)
                .where(AdminAuditLog.bot_id == self.bot_id)
                .order_by(AdminAuditLog.id.desc())
                .limit(limit)
            )
            return list((await session.execute(stmt)).scalars().all())
