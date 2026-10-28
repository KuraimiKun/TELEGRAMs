"""SQLAlchemy declarative base, engine and session factory."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, MetaData, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Portable types: JSONB / BIGINT on Postgres, JSON / INTEGER on SQLite (tests).
JsonType = JSON().with_variant(JSONB(), "postgresql")
BigInt = BigInteger().with_variant(BigInteger(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(UTC)


class TZDateTime(TypeDecorator[datetime]):
    """Timezone-aware datetime that always returns aware UTC values (SQLite drops tzinfo)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is not None and value.tzinfo is not None:
            value = value.astimezone(UTC)
        return value

    def process_result_value(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value


def upsert(session: AsyncSession, model: Any) -> Any:
    """Dialect-specific ``INSERT`` supporting ``on_conflict_do_*`` (Postgres in prod, SQLite in tests)."""
    bind = session.bind
    name = bind.dialect.name if bind is not None else "postgresql"
    if name == "sqlite":
        return sqlite_insert(model)
    return pg_insert(model)


def affected(result: Any) -> int:
    """Rows affected by an UPDATE/DELETE/INSERT result (typed as the generic Result by SQLAlchemy)."""
    return int(getattr(result, "rowcount", 0) or 0)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


def create_engine(url: str, echo: bool = False, pool_size: int = 5, max_overflow: int = 5) -> AsyncEngine:
    kwargs: dict = {"echo": echo, "pool_pre_ping": True}
    if url.startswith("postgresql"):
        kwargs.update(pool_size=pool_size, max_overflow=max_overflow, pool_recycle=1800)
    return create_async_engine(url, **kwargs)


def create_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
