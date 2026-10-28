"""Download worker: leases jobs from the crash-safe queue, downloads, post-processes and delivers.

Lifecycle of one job::

    pop (lease) -> [cancelled? expired?] -> cache hit? -> dedupe lock (or park as follower)
        -> download -> prepare -> upload -> cache -> finish
                     \\-> failure: refund once, record, tell the user -> finish

Every running job heartbeats its lease; a worker crash makes the lease expire and the reaper (running in
every worker process) re-queues the job or dead-letters it after ``MAX_ATTEMPTS``.
"""

from __future__ import annotations

import asyncio
import contextlib
import shutil
import threading
import time

import structlog
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bots.socialdownload.callback_data import CancelCb
from bots.socialdownload.config import SocialDownloadEnv
from bots.socialdownload.engine.cache import CachedMedia, DownloadLock, MediaCache
from bots.socialdownload.engine.errors import Cancelled, DownloadFailed
from bots.socialdownload.engine.media import prepare
from bots.socialdownload.engine.queue import JOB_ID_RE, Job, JobQueue
from bots.socialdownload.engine.ytdl import DownloadEngine, Progress
from bots.socialdownload.services.requests import DownloadService
from bots.socialdownload.uploader import TelegramUploader
from core.i18n import Translate, Translator
from core.log import get_logger
from core.observability import BYTES_DELIVERED, JOB_SECONDS, JOBS, QUEUE_DEPTH, capture
from core.sdk.context import BotContext
from core.ui.text import human_size, human_speed, progress_bar

log = get_logger(__name__)

HEARTBEAT_EVERY = 20
CANCEL_POLL = 1.0
REAP_EVERY = 30
IDLE_SLEEP = 0.5


class DownloadWorker:
    def __init__(
        self,
        bot: Bot,
        queue: JobQueue,
        cache: MediaCache,
        lock: DownloadLock,
        engine: DownloadEngine,
        uploader: TelegramUploader,
        service: DownloadService,
        translator: Translator,
        env: SocialDownloadEnv,
        username: str = "bot",
    ) -> None:
        self.bot = bot
        self.queue = queue
        self.cache = cache
        self.lock = lock
        self.engine = engine
        self.uploader = uploader
        self.service = service
        self.translator = translator
        self.env = env
        self.username = username
        self._stop_event = asyncio.Event()

    # ------------------------------------------------------------------ lifecycle
    async def run(self, concurrency: int = 4, drain_timeout: float = 20.0) -> None:
        log.info("worker_started", concurrency=concurrency)
        tasks = [asyncio.create_task(self._worker_loop(i)) for i in range(concurrency)]
        reaper = asyncio.create_task(self._reaper_loop())
        await self._stop_event.wait()
        # Stop taking new jobs; let in-flight jobs finish, then interrupt (they get re-queued).
        _done, pending = await asyncio.wait(tasks, timeout=drain_timeout)
        for t in pending:
            t.cancel()
        reaper.cancel()
        await asyncio.gather(*tasks, reaper, return_exceptions=True)
        log.info("worker_stopped", interrupted=len(pending))

    def stop(self) -> None:
        self._stop_event.set()

    async def _idle(self, seconds: float) -> None:
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(self._stop_event.wait(), timeout=seconds)

    async def _worker_loop(self, worker_id: int) -> None:
        while not self._stop_event.is_set():
            try:
                job = await self.queue.pop()
            except Exception as e:
                log.exception("queue_pop_failed", worker_id=worker_id, error=str(e))
                await self._idle(2)
                continue
            if job is None:
                await self._idle(IDLE_SLEEP)
                continue
            await self.run_job(job)

    async def _reaper_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.reap_once()
                await self.update_positions()
            except Exception as e:
                log.exception("reaper_failed", error=str(e))
            await self._idle(REAP_EVERY)

    async def update_positions(self, max_edits: int = 30) -> int:
        """Refresh "position in queue" for waiting users (one replica at a time, bounded edits)."""
        lock_key = self.queue.keys("positions_lock")
        if not await self.queue.redis.set(lock_key, "1", nx=True, ex=REAP_EVERY - 5):
            return 0
        edits = 0
        for position, job in enumerate(await self.queue.queued_jobs(limit=100), start=1):
            if edits >= max_edits:
                break
            if job.shown_position == position or not job.status_msg_id:
                continue
            t = self._t(job)
            await self._edit_status(job, t("dl-queued", position=str(position)), self._cancel_kb(job, t))
            job.shown_position = position
            await self.queue.save(job)
            edits += 1
        return edits

    async def reap_once(self) -> None:
        depth = await self.queue.depth()
        for state, value in depth.items():
            QUEUE_DEPTH.labels(self.queue.keys.slug, state).set(value)
        requeued, exhausted = await self.queue.reap()
        for job in requeued:
            log.warning("job_requeued_after_lease_expiry", job_id=job.id, attempts=job.attempts)
        for job in exhausted:
            log.error("job_dead_lettered", job_id=job.id, attempts=job.attempts + 1)
            await self.service.refund(job)
            await self.service.record_failure(job, "unknown")
            await self._edit_status(job, self._t(job)("error-unknown"))
            await self.queue.dead_letter(job, "lease expired too many times")

    # ------------------------------------------------------------------ helpers
    def _t(self, job: Job) -> Translate:
        def t(key: str, /, **kwargs: object) -> str:
            return self.translator.get(job.lang, key, **kwargs)

        return t

    async def _edit_status(self, job: Job, text: str, markup: InlineKeyboardMarkup | None = None) -> None:
        with contextlib.suppress(TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter):
            if job.inline_message_id:  # request made through inline mode
                await self.bot.edit_message_text(inline_message_id=job.inline_message_id, text=text)
            elif job.status_msg_id and job.chat_id:
                await self.bot.edit_message_text(
                    chat_id=job.chat_id, message_id=job.status_msg_id, text=text, reply_markup=markup
                )

    async def _delete_status(self, job: Job) -> None:
        """Called after delivery: remove the progress message (or update the inline message)."""
        if job.inline_message_id:
            await self._edit_status(job, self._t(job)("inline-sent", bot=self.username))
        elif job.status_msg_id and job.chat_id:
            with contextlib.suppress(Exception):
                await self.bot.delete_message(chat_id=job.chat_id, message_id=job.status_msg_id)

    async def _try_cached(self, job: Job) -> bool:
        cached = await self.cache.get(job.cache_key)
        if not cached or not job.chat_id:
            return False
        return await self.uploader.deliver_cached(
            job.chat_id, cached, job, self.username, reply_to=job.reply_to, cache_key=job.cache_key
        )

    # ------------------------------------------------------------------ job execution
    async def run_job(self, job: Job) -> None:
        """Run one leased job with a heartbeat and a cancel watcher. On shutdown the job is re-queued."""
        if not JOB_ID_RE.match(job.id):  # job ids become directory names
            log.error("invalid_job_id", job_id=job.id)
            await self.queue.finish(job)
            return

        structlog.contextvars.bind_contextvars(bot=self.queue.keys.slug, job_id=job.id, user_id=job.user_id)
        started = time.monotonic()
        cancel_event = threading.Event()
        side_tasks = [
            asyncio.create_task(self._heartbeat(job)),
            asyncio.create_task(self._watch_cancel(job, cancel_event)),
        ]
        finished = True
        try:
            finished = await self._process(job, cancel_event)
        except asyncio.CancelledError:
            # Interrupted by shutdown: hand the job back so another worker picks it up.
            finished = False
            cancel_event.set()
            with contextlib.suppress(Exception):
                await self.queue.requeue(job, count_attempt=False)
            log.info("job_requeued_on_shutdown", job_id=job.id)
            raise
        finally:
            for t in side_tasks:
                t.cancel()
            if finished:
                JOB_SECONDS.labels(self.queue.keys.slug, job.platform).observe(time.monotonic() - started)
            structlog.contextvars.unbind_contextvars("bot", "job_id", "user_id")
            if finished:
                with contextlib.suppress(Exception):
                    await self.queue.finish(job)
            workdir = self.env.downloads_dir / job.id
            if workdir.exists():
                await asyncio.to_thread(shutil.rmtree, workdir, True)

    async def _heartbeat(self, job: Job) -> None:
        while True:
            await asyncio.sleep(HEARTBEAT_EVERY)
            with contextlib.suppress(Exception):
                await self.queue.heartbeat(job.id)

    async def _watch_cancel(self, job: Job, cancel_event: threading.Event) -> None:
        while not cancel_event.is_set():
            await asyncio.sleep(CANCEL_POLL)
            with contextlib.suppress(Exception):
                if await self.queue.is_cancelled(job.id):
                    cancel_event.set()

    async def _process(self, job: Job, cancel_event: threading.Event) -> bool:
        """Returns False when the job was parked (it is not finished yet)."""
        t = self._t(job)
        stg = await self.service.settings()
        started = time.monotonic()

        try:
            if await self.queue.is_cancelled(job.id):
                raise Cancelled()
            if not job.attempts and not job.parked and time.time() - job.created_at > stg.queue_max_wait_min * 60:
                raise DownloadFailed("queue_expired")

            if await self._try_cached(job):
                await self._delete_status(job)
                await self.service.record_success(job, from_cache=True)
                JOBS.labels(self.queue.keys.slug, job.platform, "cached").inc()
                return True

            token = await self.lock.acquire(job.cache_key)
            if token is None:
                # Someone is downloading exactly this media: wait for them without holding a worker.
                await self.queue.park(job, job.cache_key)
                if not await self.lock.held(job.cache_key):  # leader finished in between: wake ourselves
                    await self.queue.wake(job.cache_key)
                return False

            try:
                await self._download_and_deliver(job, t, cancel_event, token, started)
            finally:
                with contextlib.suppress(Exception):
                    await self.lock.release(job.cache_key, token)
                with contextlib.suppress(Exception):
                    await self.queue.wake(job.cache_key)
            return True

        except Cancelled:
            log.info("job_cancelled", job_id=job.id, user_id=job.user_id)
            JOBS.labels(self.queue.keys.slug, job.platform, "cancelled").inc()
            await self.service.refund(job)
            await self._edit_status(job, t("dl-cancelled"))
        except DownloadFailed as e:
            log.warning("job_download_failed", job_id=job.id, code=e.code, detail=e.detail[:300])
            JOBS.labels(self.queue.keys.slug, job.platform, f"failed_{e.code}").inc()
            await self.service.refund(job)
            await self.service.record_failure(job, e.code)
            await self._edit_status(job, t(f"error-{e.code}"))
        except Exception as e:
            log.exception("job_unexpected_error", job_id=job.id, error=str(e))
            JOBS.labels(self.queue.keys.slug, job.platform, "failed_unknown").inc()
            capture(e, bot=self.queue.keys.slug, job_id=job.id, platform=job.platform)
            await self.service.refund(job)
            await self.service.record_failure(job, "unknown")
            await self._edit_status(job, t("error-unknown"))
        return True

    async def _download_and_deliver(
        self, job: Job, t: Translate, cancel_event: threading.Event, token: str, started: float
    ) -> None:
        progress = Progress()
        extender = asyncio.create_task(self._extend_lock(job, token))
        reporter = asyncio.create_task(self._report_progress(job, progress, t))
        try:
            output = await self.engine.download(
                url=job.url,
                platform=job.platform,
                workdir=self.env.downloads_dir / job.id,
                kind=job.kind,
                max_height=job.max_height,
                max_bytes=job.max_bytes,
                max_duration_s=job.max_duration_s,
                playlist_items=job.playlist_items,
                audio_format=job.audio_format,
                progress=progress,
                cancel=cancel_event,
                max_items=job.max_items,
            )
            progress.stage = "process"
            media_files = await prepare(output.files, title=output.title, uploader=output.uploader)
            if cancel_event.is_set():
                raise Cancelled()

            progress.stage = "upload"
            if not job.chat_id:
                raise DownloadFailed("unknown", "job without chat")

            async def should_cancel() -> bool:
                return cancel_event.is_set()

            result = await self.uploader.upload(
                chat_id=job.chat_id,
                files=media_files,
                job=job,
                bot_username=self.username,
                t=t,
                reply_to=job.reply_to,
                should_cancel=should_cancel,
            )
        finally:
            extender.cancel()
            reporter.cancel()

        # Delivered. Nothing below may turn this into a failure.
        if result.items and result.complete:
            try:
                await self.cache.set(
                    job.cache_key, CachedMedia(items=result.items, title=output.title or "", url=job.url)
                )
            except Exception as e:
                log.warning("cache_set_failed", job_id=job.id, error=str(e))
        await self._delete_status(job)
        delivered_bytes = sum(f.size for f in media_files)
        JOBS.labels(self.queue.keys.slug, job.platform, "ok").inc()
        BYTES_DELIVERED.labels(self.queue.keys.slug).inc(delivered_bytes)
        await self.service.record_success(
            job,
            from_cache=False,
            size_bytes=delivered_bytes,
            duration_ms=int((time.monotonic() - started) * 1000),
        )

    async def _extend_lock(self, job: Job, token: str) -> None:
        while True:
            await asyncio.sleep(DownloadLock.LEASE / 3)
            with contextlib.suppress(Exception):
                if not await self.lock.extend(job.cache_key, token):
                    log.warning("download_lock_lost", job_id=job.id)

    # ------------------------------------------------------------------ progress
    def _cancel_kb(self, job: Job, t: Translate) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=t("btn-cancel"), callback_data=CancelCb(job_id=job.id).pack())]]
        )

    def render_progress(self, job: Job, progress: Progress, t: Translate) -> str:
        prefix = f"[{progress.item}/{job.playlist_items.split('-')[-1]}] " if job.playlist_items else ""
        if progress.stage == "process":
            return prefix + t("dl-processing")
        if progress.stage == "upload":
            return t("dl-uploading")
        if progress.total > 0:
            percent = min(100, int(progress.downloaded * 100 / progress.total))
            return prefix + t(
                "dl-downloading",
                percent=percent,
                bar=progress_bar(percent),
                done=human_size(progress.downloaded),
                total=human_size(progress.total),
                speed=human_speed(progress.speed),
                eta=f"{progress.eta}s" if progress.eta else "--",
            )
        if progress.downloaded > 0:
            return prefix + t(
                "dl-downloading-simple", done=human_size(progress.downloaded), speed=human_speed(progress.speed)
            )
        return prefix + t("dl-starting")

    async def _report_progress(self, job: Job, progress: Progress, t: Translate) -> None:
        """Edit the status message as the job advances. Telegram errors never kill the job."""
        if not (job.chat_id and job.status_msg_id):
            return
        interval = 3.0 if job.chat_type == "private" else 6.0
        markup = self._cancel_kb(job, t)
        last_text = ""
        while True:
            await asyncio.sleep(interval)
            text = self.render_progress(job, progress, t)
            if text == last_text:
                continue
            try:
                await self.bot.edit_message_text(
                    chat_id=job.chat_id, message_id=job.status_msg_id, text=text, reply_markup=markup
                )
                last_text = text
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except (TelegramBadRequest, TelegramForbiddenError):
                last_text = text
            except Exception as e:
                log.debug("progress_edit_failed", job_id=job.id, error=str(e))


async def run_worker(ctx: BotContext) -> None:
    """Entry point when run via `python -m core run socialdownload worker`."""
    env: SocialDownloadEnv = ctx.env  # type: ignore[assignment]
    worker = DownloadWorker(
        bot=ctx.bot,
        queue=ctx.extras["queue"],
        cache=ctx.extras["cache"],
        lock=ctx.extras["download_lock"],
        engine=ctx.extras["engine"],
        uploader=ctx.extras["uploader"],
        service=ctx.extras["downloads"],
        translator=ctx.translator,
        env=env,
        username=ctx.username or "bot",
    )

    async def _stop_on_shutdown() -> None:
        await ctx.shutdown.wait()
        worker.stop()

    watcher = asyncio.create_task(_stop_on_shutdown())
    log.info("socialdownload_worker_starting", concurrency=env.worker_concurrency)
    try:
        await worker.run(concurrency=env.worker_concurrency)
    finally:
        watcher.cancel()
