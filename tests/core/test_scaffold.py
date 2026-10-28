"""`python -m core new-bot` produces a bot that passes the platform contract and builds a dispatcher."""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys

import pytest

from core.db.base import Base
from core.runtime.dispatcher import build_dispatcher
from core.scaffold.generator import create_bot_skeleton
from core.sdk.registry import BOTS_DIR, PROJECT_ROOT, discover
from tests.conftest import build_test_ctx

SLUG = "zz_scaffold_probe"


@pytest.fixture
def generated():
    bot_dir = create_bot_skeleton(SLUG, 'Probe "Bot" & Co')
    yield bot_dir
    shutil.rmtree(bot_dir, ignore_errors=True)
    shutil.rmtree(PROJECT_ROOT / "tests" / "bots" / SLUG, ignore_errors=True)
    for name in [m for m in sys.modules if m.startswith(f"bots.{SLUG}")]:
        del sys.modules[name]
    table = Base.metadata.tables.get(f"{SLUG}_events")
    if table is not None:
        Base.metadata.remove(table)


async def test_generated_bot_is_valid(generated, sm, redis, api, tmp_path):
    assert generated == BOTS_DIR / SLUG
    lint = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-m", "ruff", "check", "--no-cache", str(generated)],
        capture_output=True,
        text=True,
    )
    assert lint.returncode == 0, lint.stdout

    [module] = discover([SLUG])
    assert module.table_prefix == f"{SLUG}_" and module.title == 'Probe "Bot" & Co'
    async with sm() as s:  # auto-discovery registered its table and create_all built it
        tables = await s.run_sync(lambda sync: sync.connection().dialect.get_table_names(sync.connection()))
    assert f"{SLUG}_events" in tables

    ctx = await build_test_ctx(module, sm, redis, api, tmp_path)
    assert build_dispatcher(ctx) is not None
    assert ctx.translator.get("en", f"{SLUG}-start", name="A").endswith("Probe \"Bot\" &amp; Co.")


def test_rejects_bad_and_reserved_slugs():
    for bad in ("bad-slug", "1x", "platform", "a"):
        with pytest.raises(ValueError):
            create_bot_skeleton(bad)
