"""End-to-end worker tests: real queue/quota/cache/DB, fake downloader, recording Bot API."""

from __future__ import annotations

import asyncio
import shutil
import threading
from pathlib import Path

import pytest
from sqlalchemy import select

from bots.socialdownload.engine.errors import Cancelled, DownloadFailed
from bots.socialdownload.engine.ytdl import DownloadOutput
from bots.socialdownload.models import Download
from bots.socialdownload.services.requests import Outcome
from bots.socialdownload.worker import DownloadWorker
from tests.bots.socialdownload.conftest import needs_ffmpeg

pytestmark = needs_ffmpeg

URL = "https://x.com/i/status/42"


class FakeEngine:
    def __init__(self, sample: Path) -> None:
        self.sample = sample
        self.calls = 0
        self.fail: DownloadFailed | None = None
        self.block: asyncio.Event | None = None  # when set, download waits until cancelled or released
        self.started = asyncio.Event()

    async def download(self, *, workdir: Path, cancel: threading.Event, **_kw) -> DownloadOutput:
        self.calls += 1
        self.started.set()
        workdir.mkdir(parents=True, exist_ok=True)
        if self.block is not None:
            while not self.block.is_set():
                if cancel.is_set():
                    raise Cancelled()
                await asyncio.sleep(0.05)
        if self.fail:
            raise self.fail
        shutil.copy(self.sample, workdir / "001_clip.mp4")
        return DownloadOutput(files=[workdir / "001_clip.mp4"], title="Tom & Jerry <3")


@pytest.fixture
def engine(sample_mp4) -> FakeEngine:
    return FakeEngine(sample_mp4)


@pytest.fixture
def worker(ctx, engine, media_api) -> DownloadWorker:
    ctx.extras["engine"] = engine
    return DownloadWorker(
        bot=ctx.bot,
        queue=ctx.extras["queue"],
        cache=ctx.extras["cache"],
        lock=ctx.extras["download_lock"],
        engine=engine,  # type: ignore[arg-type]
        uploader=ctx.extras["uploader"],
        service=ctx.extras["downloads"],
        translator=ctx.translator,
        env=ctx.env,  # type: ignore[arg-type]
        username="test_bot",
    )


async def submit(ctx, user_id: int = 7, **kw):
    user, _ = await ctx.users.get_or_create(user_id, language_code="en")
    return await ctx.extras["downloads"].submit(
        user=user, chat_id=user_id, chat_type="private", url=URL, platform="twitter", kind="video",
        status_msg_id=77, **kw,
    )


async def run_next(worker) -> None:
    job = await worker.queue.pop()
    assert job is not None
    await worker.run_job(job)


async def test_successful_download_delivers_caches_and_counts(ctx, worker, media_api):
    res = await submit(ctx)
    assert res.outcome is Outcome.QUEUED
    await run_next(worker)

    videos = media_api.calls("SendVideo")
    assert len(videos) == 1
    assert "Tom &amp; Jerry &lt;3" in videos[0].caption  # HTML-escaped title
    assert await ctx.extras["quota"].used(7) == 1
    assert await worker.queue.depth() == {"high": 0, "normal": 0, "inflight": 0, "dead": 0}
    user = await ctx.users.get(7)
    assert user.actions_count == 1
    async with ctx.sm() as s:
        rows = (await s.execute(select(Download))).scalars().all()
    assert [r.status for r in rows] == ["ok"]

    # Same request again: instant delivery from the file_id cache, no download, no queue.
    again = await submit(ctx)
    assert again.outcome is Outcome.DELIVERED
    assert worker.engine.calls == 1
    assert len(media_api.calls("SendVideo")) == 2


async def test_failed_download_refunds_and_reports(ctx, worker, engine, media_api):
    engine.fail = DownloadFailed("private")
    await submit(ctx)
    await run_next(worker)
    assert await ctx.extras["quota"].used(7) == 0
    edits = [m.text for m in media_api.calls("EditMessageText")]
    assert ctx.translator.get("en", "error-private") in edits
    async with ctx.sm() as s:
        rows = (await s.execute(select(Download))).scalars().all()
    assert [(r.status, r.error_code) for r in rows] == [("failed", "private")]


async def test_cancel_while_running_refunds_exactly_once(ctx, worker, engine, media_api):
    engine.block = asyncio.Event()
    res = await submit(ctx)
    task = asyncio.create_task(run_next(worker))
    await asyncio.wait_for(engine.started.wait(), 2)

    first, _ = await worker.queue.cancel(res.job.id, 7)
    assert first.found and not first.removed_from_queue  # running: the worker owns the refund
    await asyncio.wait_for(task, 5)

    assert await ctx.extras["quota"].used(7) == 0
    # A second refund attempt for the same job (e.g. a duplicate cancel) is a no-op.
    await ctx.extras["downloads"].refund(res.job)
    assert await ctx.extras["quota"].used(7) == 0
    assert media_api.calls("SendVideo") == []


async def test_identical_concurrent_requests_download_once(ctx, worker, engine, media_api):
    engine.block = asyncio.Event()
    await submit(ctx, user_id=1)
    await submit(ctx, user_id=2)
    leader = asyncio.create_task(run_next(worker))
    await asyncio.wait_for(engine.started.wait(), 2)

    await run_next(worker)  # follower: lock is held -> parks without occupying the worker
    assert (await worker.queue.depth())["inflight"] == 2

    engine.block.set()
    await asyncio.wait_for(leader, 5)
    await run_next(worker)  # woken follower is served from cache
    assert engine.calls == 1
    assert sorted(m.chat_id for m in media_api.calls("SendVideo")) == [1, 2]
    assert await worker.queue.depth() == {"high": 0, "normal": 0, "inflight": 0, "dead": 0}


async def test_shutdown_requeues_running_job(ctx, worker, engine):
    engine.block = asyncio.Event()
    res = await submit(ctx)
    task = asyncio.create_task(run_next(worker))
    await asyncio.wait_for(engine.started.wait(), 2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    depth = await worker.queue.depth()
    assert depth["normal"] == 1 and depth["inflight"] == 0
    assert (await worker.queue.get(res.job.id)) is not None
    assert await ctx.extras["quota"].used(7) == 1  # still owed a download, not refunded


async def test_dead_lettered_job_is_refunded(ctx, worker, media_api):
    import time

    await submit(ctx)
    job = await worker.queue.pop()
    job.attempts = 2
    await worker.queue.save(job)
    await worker.queue.redis.zadd(worker.queue.inflight, {job.id: time.time() - 1})
    await worker.reap_once()
    assert (await worker.queue.depth())["dead"] == 1
    assert await ctx.extras["quota"].used(7) == 0


async def test_limits_and_concurrency(ctx, worker):
    stg = await ctx.settings.get()
    await ctx.settings.set("free_concurrent", 1)
    first = await submit(ctx, user_id=9)
    second = await submit(ctx, user_id=9)
    assert first.outcome is Outcome.QUEUED and second.outcome is Outcome.BUSY
    assert await ctx.extras["quota"].used(9) == 1  # busy requests are not charged

    await ctx.settings.set("free_daily_limit", 1)
    await ctx.settings.set("free_concurrent", 5)
    third = await submit(ctx, user_id=9)
    assert third.outcome is Outcome.LIMIT
    locked = await submit(ctx, user_id=9, height=stg.vip_max_height)
    assert locked.outcome is Outcome.LOCKED


async def test_waiting_users_see_their_position_move(ctx, worker, media_api):
    for uid in (21, 22, 23):
        await submit(ctx, user_id=uid)
    await worker.queue.pop()  # first job starts running
    edits = await worker.update_positions()
    assert edits == 2  # users 22 and 23 moved from 2,3 to 1,2
    texts = [m.text for m in media_api.calls("EditMessageText")]
    assert ctx.translator.get("en", "dl-queued", position="1") in texts
    await ctx.redis.delete(worker.queue.keys("positions_lock"))
    assert await worker.update_positions() == 0  # nothing changed since


async def test_inline_mode_cache_hit_and_queued_delivery(ctx, worker, media_api):
    from aiogram.types import ChosenInlineResult, InlineQuery, Update, User

    from bots.socialdownload.engine.cache import CachedItem, CachedMedia, request_key
    from core.runtime.dispatcher import build_dispatcher

    dp = build_dispatcher(ctx)
    await ctx.users.get_or_create(7, language_code="en")
    who = User(id=7, is_bot=False, first_name="A", language_code="en")

    # Miss: a "download" article is offered.
    await dp.feed_update(ctx.bot, Update(update_id=1, inline_query=InlineQuery(id="q1", from_user=who, query=URL, offset="")))
    [article] = media_api.calls("AnswerInlineQuery")[-1].results
    assert article.id.startswith("dl:")

    # The user picks it: the job is queued for their private chat, tied to the inline message.
    chosen = ChosenInlineResult(result_id=article.id, from_user=who, query=URL, inline_message_id="IMSG")
    await dp.feed_update(ctx.bot, Update(update_id=2, chosen_inline_result=chosen))
    await run_next(worker)
    assert media_api.calls("SendVideo")[-1].chat_id == 7
    inline_edits = [m for m in media_api.calls("EditMessageText") if m.inline_message_id == "IMSG"]
    assert inline_edits and inline_edits[-1].text == ctx.translator.get("en", "inline-sent", bot="test_bot")

    # Hit: now the media itself is offered instantly.
    stg = await ctx.settings.get()
    key = request_key(URL, "video", stg.free_max_height, "mp3")
    await ctx.extras["cache"].set(key, CachedMedia(items=[CachedItem("video", "FILE1")], title="T"))
    await dp.feed_update(ctx.bot, Update(update_id=3, inline_query=InlineQuery(id="q2", from_user=who, query=URL, offset="")))
    results = media_api.calls("AnswerInlineQuery")[-1].results
    assert results[0].video_file_id == "FILE1"
