from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from bots.notes.service import deliver_due_reminders, parse_when
from core.runtime.dispatcher import build_dispatcher
from core.sdk.registry import discover
from tests.conftest import build_test_ctx


def test_notes_module_contract():
    [module] = discover(["notes"])
    assert module.table_prefix == "notes_"
    assert {c.command for c in module.commands()} >= {"help", "notes", "remind"}


@pytest.fixture
async def nctx(sm, redis, api, tmp_path):
    return await build_test_ctx(discover(["notes"])[0], sm, redis, api, tmp_path)


async def _unthrottle(ctx):
    keys = await ctx.redis.keys(ctx.keys("throttle*"))
    if keys:
        await ctx.redis.delete(*keys)


def test_parse_when():
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    assert parse_when("10m", now) == now + timedelta(minutes=10)
    assert parse_when("2h", now) == now + timedelta(hours=2)
    assert parse_when("18:30", now) == now.replace(hour=18, minute=30)
    assert parse_when("09:00", now) == (now + timedelta(days=1)).replace(hour=9, minute=0)
    assert parse_when("0m", now) is None and parse_when("999d", now) is None and parse_when("soon", now) is None


async def test_text_becomes_note_with_limits_and_referral_credit(nctx, api, builders):
    dp = build_dispatcher(nctx)
    await nctx.settings.set("free_max_notes", 2)
    for i in range(3):
        await _unthrottle(nctx)
        await dp.feed_update(nctx.bot, builders["message"](f"buy <milk> {i}", user_id=5))
    texts = [m.text for m in api.calls("SendMessage")]
    assert texts[-1] == nctx.translator.get("en", "notes-limit-notes", max=2)
    notes, total = await nctx.extras["notes"].page(5, 1)
    assert total == 2 and notes[0].text == "buy <milk> 1"
    assert (await nctx.users.get(5)).actions_count == 2

    await _unthrottle(nctx)
    await dp.feed_update(nctx.bot, builders["message"]("/notes", user_id=5))
    assert "buy &lt;milk&gt;" in api.calls("SendMessage")[-1].text  # notes are escaped


async def test_reminders_fire_exactly_once_in_users_language(nctx, api, builders):
    dp = build_dispatcher(nctx)
    await dp.feed_update(nctx.bot, builders["message"]("/remind 10m stretch", user_id=6))
    [r] = await nctx.extras["notes"].pending_reminders(6)
    assert r.text == "stretch"

    # Not due yet.
    assert await deliver_due_reminders(nctx) == 0
    async with nctx.sm() as s:
        db_r = await s.get(type(r), r.id)
        db_r.due_at = datetime.now(UTC) - timedelta(seconds=1)
        await s.commit()
    assert await deliver_due_reminders(nctx) == 1
    assert await deliver_due_reminders(nctx) == 0  # never twice
    fired = api.calls("SendMessage")[-1]
    assert fired.chat_id == 6 and "stretch" in fired.text


async def test_arabic_users_get_arabic_texts(nctx, api, builders):
    dp = build_dispatcher(nctx)
    await dp.feed_update(nctx.bot, builders["message"]("/help", user_id=7, lang="ar"))
    assert api.calls("SendMessage")[-1].text == nctx.translator.get("ar", "notes-help")
