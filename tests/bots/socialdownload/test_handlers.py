"""Bot handlers driven through the full dispatcher with real Updates."""

from __future__ import annotations

import pytest

from bots.socialdownload.callback_data import CancelCb, FormatCb
from bots.socialdownload.engine.ytdl import MediaInfo, SearchResult
from core.runtime.dispatcher import build_dispatcher


class FakeEngine:
    async def extract(self, url, platform, playlist=False):
        return MediaInfo(id="x", title="A <b>Title</b>", url=url, extractor="youtube", uploader="Up",
                         duration=125, heights=[1080, 720, 360])

    async def search(self, query, limit=6):
        return [SearchResult(id="abc", title="Song", url="https://www.youtube.com/watch?v=abcdefghijk",
                             duration=200, channel="c")]


@pytest.fixture(autouse=True)
def _public_dns(monkeypatch):
    # Handlers SSRF-check every URL; keep tests offline by treating names as public.
    async def ok(url):
        return None

    monkeypatch.setattr("bots.socialdownload.handlers.link.assert_public_url", ok)


@pytest.fixture
def dp(ctx):
    ctx.extras["engine"] = FakeEngine()
    return build_dispatcher(ctx)


def last_markup(api):
    edits = [m for m in api.requests if type(m).__name__ in ("EditMessageText", "SendMessage") and m.reply_markup]
    return edits[-1].reply_markup


async def test_link_is_queued_with_cancel_button(ctx, dp, api, builders):
    await dp.feed_update(ctx.bot, builders["message"]("https://x.com/user/status/123?s=20", user_id=1))
    edits = api.calls("EditMessageText")
    assert edits and edits[-1].text == ctx.translator.get("en", "dl-queued", position="1")
    button = edits[-1].reply_markup.inline_keyboard[0][0]
    assert button.callback_data.startswith("cnl:")
    assert (await ctx.extras["queue"].depth())["normal"] == 1


async def test_cancel_queued_download_refunds(ctx, dp, api, builders):
    await dp.feed_update(ctx.bot, builders["message"]("https://x.com/user/status/123", user_id=1))
    job_id = CancelCb.unpack(api.calls("EditMessageText")[-1].reply_markup.inline_keyboard[0][0].callback_data).job_id
    assert await ctx.extras["quota"].used(1) == 1
    await dp.feed_update(ctx.bot, builders["callback"](CancelCb(job_id=job_id).pack(), user_id=1))
    assert await ctx.extras["quota"].used(1) == 0
    assert (await ctx.extras["queue"].depth())["normal"] == 0


async def test_format_picker_belongs_to_its_owner(ctx, dp, api, builders):
    await dp.feed_update(ctx.bot, builders["message"]("https://youtu.be/dQw4w9WgXcQ", user_id=1))
    picker = api.calls("EditMessageText")[-1]
    assert "&lt;b&gt;Title" in picker.text  # media titles are escaped
    fmt = next(
        b.callback_data for row in picker.reply_markup.inline_keyboard for b in row
        if b.callback_data and b.callback_data.startswith("fmt:") and ":video:720" in b.callback_data
    )
    await dp.feed_update(ctx.bot, builders["callback"](fmt, user_id=2))  # someone else taps it
    assert api.calls("AnswerCallbackQuery")[-1].text == ctx.translator.get("en", "not-your-menu")
    assert (await ctx.extras["queue"].depth())["normal"] == 0

    await dp.feed_update(ctx.bot, builders["callback"](fmt, user_id=1))
    await dp.feed_update(ctx.bot, builders["callback"](fmt, user_id=1))  # double tap: no second job
    assert (await ctx.extras["queue"].depth())["normal"] == 1
    job = (await ctx.extras["queue"].queued_jobs())[0]
    assert job.max_height == 720 and job.url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


async def test_vip_only_quality_is_locked_for_free_users(ctx, dp, api, builders):
    await dp.feed_update(ctx.bot, builders["message"]("https://youtu.be/dQw4w9WgXcQ", user_id=1))
    picker = api.calls("EditMessageText")[-1]
    locked = [b.text for row in picker.reply_markup.inline_keyboard for b in row if "🔒" in b.text]
    assert locked == ["🔒 1080p (VIP)"]


async def test_free_text_becomes_search(ctx, dp, api, builders):
    await dp.feed_update(ctx.bot, builders["message"]("never gonna give", user_id=1))
    results = api.calls("EditMessageText")[-1]
    callbacks = [b.callback_data for row in results.reply_markup.inline_keyboard for b in row if b.callback_data]
    assert any(FormatCb.unpack(c).kind == "audio" for c in callbacks if c.startswith("fmt:"))


async def test_unknown_sites_ignored_in_groups(ctx, dp, api, builders):
    update = builders["message"]("look https://random-site.example/video", user_id=1, chat_type="supergroup",
                                 chat_id=-1001)
    await dp.feed_update(ctx.bot, update)
    assert api.calls("SendMessage") == [] and (await ctx.extras["queue"].depth())["normal"] == 0
