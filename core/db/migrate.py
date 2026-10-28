"""Programmatic Alembic helpers used by ``python -m core migrate`` / ``makemigrations``."""

from __future__ import annotations

import asyncio
import re

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from core.config import get_platform_config
from core.db.base import create_engine
from core.log import get_logger
from core.sdk.registry import PROJECT_ROOT

log = get_logger(__name__)

# Revision that matches the schema produced by the pre-Alembic `create_all` bootstrap.
BASELINE_REVISION = "0001_initial"


def alembic_config(database_url: str | None = None) -> Config:
    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "core" / "db" / "migrations"))
    cfg.set_main_option("sqlalchemy.url", database_url or get_platform_config().database_url)
    cfg.attributes["configure_logger"] = False
    return cfg


async def _schema_state(database_url: str) -> tuple[bool, bool]:
    """Return (has_alembic_version_table, has_core_tables)."""
    engine = create_engine(database_url)
    try:
        async with engine.connect() as conn:
            tables = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
    finally:
        await engine.dispose()
    return "alembic_version" in tables, "bot_users" in tables


def upgrade(database_url: str | None = None, revision: str = "head") -> None:
    url = database_url or get_platform_config().database_url
    has_version, has_tables = asyncio.run(_schema_state(url))
    cfg = alembic_config(url)
    if has_tables and not has_version:
        # Database was bootstrapped with the old create_all path: adopt it at the baseline revision.
        log.warning("adopting_unversioned_database", baseline=BASELINE_REVISION)
        command.stamp(cfg, BASELINE_REVISION)
    command.upgrade(cfg, revision)
    log.info("database_migrated", revision=revision)


def make_migration(message: str, database_url: str | None = None) -> None:
    """Autogenerate the next revision with a sequential id (0003, 0004, ...)."""
    versions = PROJECT_ROOT / "core" / "db" / "migrations" / "versions"
    numbers = [int(p.name[:4]) for p in versions.glob("[0-9][0-9][0-9][0-9]_*.py")]
    slug = re.sub(r"[^a-z0-9]+", "_", message.lower()).strip("_")[:40]
    rev_id = f"{max(numbers, default=0) + 1:04d}_{slug}"
    command.revision(alembic_config(database_url), message=message, autogenerate=True, rev_id=rev_id)


def current(database_url: str | None = None) -> None:
    command.current(alembic_config(database_url), verbose=True)
