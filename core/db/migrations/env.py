"""Alembic environment: one migration history for core tables and every bot's prefixed tables."""

import asyncio
from logging.config import fileConfig
from typing import Any, Literal

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import core.db.models  # noqa: F401  (registers core tables)
from core.config import get_platform_config
from core.db.base import Base, TZDateTime
from core.sdk.registry import BOTS_DIR, load_bot_models

# Register every bot's tables — including bots not enabled in this deployment — so autogenerate never
# proposes dropping another bot's tables.
for bot_dir in sorted(BOTS_DIR.iterdir()):
    if bot_dir.is_dir() and (bot_dir / "__init__.py").exists() and not bot_dir.name.startswith(("_", ".")):
        load_bot_models(bot_dir.name)

config = context.config
if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", get_platform_config().database_url)

target_metadata = Base.metadata


def render_item(type_: str, obj: Any, autogen_context: Any) -> str | Literal[False]:
    """Render app-specific column types as plain SQLAlchemy types so migrations never import app code."""
    if type_ == "type" and isinstance(obj, TZDateTime):
        return "sa.DateTime(timezone=True)"
    return False


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_item=render_item,
        render_as_batch=connection.dialect.name == "sqlite",
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        do_run_migrations(connection)
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
