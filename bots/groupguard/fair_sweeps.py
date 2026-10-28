"""Durable tenant-owned keyset sweep cursors with bounded batches and replica serialization."""

from __future__ import annotations

from sqlalchemy import select

from bots.groupguard.models import GuardSweep
from core.db.base import upsert, utcnow

START = -(2**63)


async def batch(sm, bot_id: int, kind: str, scope_id: int, query, column, *, limit: int = 100) -> list[int]:
    if not 1 <= limit <= 500:
        raise ValueError("sweep_limit_invalid")
    async with sm() as session:
        await session.execute(
            upsert(session, GuardSweep)
            .values(bot_id=bot_id, kind=kind, scope_id=scope_id, last_id=START, updated_at=utcnow())
            .on_conflict_do_nothing()
        )
        cursor = (
            await session.execute(
                select(GuardSweep)
                .where(GuardSweep.bot_id == bot_id, GuardSweep.kind == kind, GuardSweep.scope_id == scope_id)
                .with_for_update()
            )
        ).scalar_one()
        ids = list(
            (
                await session.execute(query.where(column > cursor.last_id).order_by(column).limit(limit))
            ).scalars()
        )
        if not ids and cursor.last_id != START:
            ids = list(
                (await session.execute(query.where(column > START).order_by(column).limit(limit))).scalars()
            )
        cursor.last_id = int(ids[-1]) if ids else START
        cursor.updated_at = utcnow()
        await session.commit()
        return [int(value) for value in ids]
