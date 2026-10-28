import asyncio
import io
import os
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pymupdf as fitz
import pytest
from aiogram import Bot
from PIL import Image

from bots.doctools.config import DocToolsEnv
from bots.doctools.queue import DocAsset, Job, JobQueue
from bots.doctools.worker import DocumentWorker
from core.ai.base import AIResult
from core.config import PlatformConfig
from core.redis import KeySpace
from tests.conftest import TOKEN


def pdf_bytes(text):
    with fitz.open() as doc:
        page = doc.new_page()
        page.insert_text((30, 40), text)
        return doc.tobytes()


@pytest.fixture
def worker(redis, api, tmp_path, monkeypatch):
    monkeypatch.setattr("bots.doctools.worker.record_user_action", AsyncMock())
    queue = JobQueue(redis, KeySpace("doctools"))
    service = SimpleNamespace(refund=AsyncMock(), record=AsyncMock())
    ctx = SimpleNamespace(
        extras={"doctools_queue": queue, "doctools": service},
        env=DocToolsEnv(token=TOKEN), bot=Bot(token=TOKEN, session=api),
        translator=SimpleNamespace(get=lambda lang, key, **kwargs: f"{key} {kwargs}"),
        platform=PlatformConfig(data_dir=tmp_path), slug="doctools", metric_name="doctools", ai=None,
    )
    return DocumentWorker(ctx)


async def enqueue(worker, operation="merge", **kwargs):
    job = Job(
        user_id=42, chat_id=42, operation=operation,
        assets=[DocAsset(file_id="first"), DocAsset(file_id="second")], **kwargs,
    )
    assert await worker.queue.enqueue(job) > 0
    return await worker.queue.pop()


async def test_worker_merges_delivers_and_removes_private_files(worker, api, monkeypatch):
    contents = {"first": pdf_bytes("first page"), "second": pdf_bytes("second page")}
    monkeypatch.setattr("bots.doctools.worker.fetch_bytes", AsyncMock(side_effect=lambda ctx, id, size, limit: contents[id]))
    delivered = []
    original_send = worker.ctx.bot.send_document

    async def inspect_delivery(**kwargs):
        path = Path(kwargs["document"].path)
        with fitz.open(path) as doc:
            delivered.extend(page.get_text().strip() for page in doc)
        return await original_send(**kwargs)

    monkeypatch.setattr(worker.ctx.bot, "send_document", inspect_delivery)
    job = await enqueue(worker)
    await worker.run_job(job)
    assert delivered == ["first page", "second page"]
    assert len(api.calls("SendDocument")) == 1
    assert await worker.queue.get(job.id) is None
    assert list((worker.ctx.platform.bot_data_dir("doctools") / "tmp").iterdir()) == []
    worker.service.record.assert_awaited_once_with(job, "ok", pages=2, size_bytes=worker.service.record.await_args.kwargs["size_bytes"])


async def test_oversized_job_refunds_once_and_keeps_queue_responsive(worker, api, monkeypatch):
    monkeypatch.setattr("bots.doctools.worker.fetch_bytes", AsyncMock(return_value=b"too large"))
    job = await enqueue(worker, max_bytes=1, quota_day="20261009")
    await worker.run_job(job)
    worker.service.refund.assert_awaited_once_with(job)
    assert "dt-error-large" in api.calls("SendMessage")[0].text
    assert not api.calls("SendDocument")
    assert await worker.queue.get(job.id) is None


async def test_group_count_replies_to_request(worker, api, monkeypatch):
    monkeypatch.setattr("bots.doctools.worker.fetch_bytes", AsyncMock(return_value=pdf_bytes("Hello world")))
    job = await enqueue(worker, operation="count", reply_to=777)
    await worker.run_job(job)
    reply = api.calls("SendMessage")[0].reply_parameters
    assert reply.message_id == 777 and reply.allow_sending_without_reply


async def test_quiz_delivers_ten_native_polls_and_retains_arabic(worker, api, monkeypatch):
    monkeypatch.setattr("bots.doctools.worker.fetch_bytes", AsyncMock(return_value=pdf_bytes("Study facts")))
    questions = [{"question": f"سؤال {i + 1}", "options": ["أ", "ب", "ج", "د"], "correct": i % 4, "explanation": "تفسير"} for i in range(10)]
    worker.ctx.ai = SimpleNamespace(ask=AsyncMock(return_value=AIResult(text="", model="fake", data={"questions": questions})))
    job = await enqueue(worker, operation="quiz", lang="ar", quota_day="20261009")
    await worker.run_job(job)
    polls = api.calls("SendPoll")
    assert len(polls) == 10
    assert all(poll.type == "quiz" and poll.is_anonymous for poll in polls)
    assert [poll.correct_option_ids for poll in polls] == [[i % 4] for i in range(10)]
    assert polls[0].question == "سؤال 1"
    worker.service.refund.assert_not_awaited()
    assert await worker.queue.get(job.id) is None


async def test_ocr_on_digital_pdf_exports_docx_without_ai(worker, api, monkeypatch):
    monkeypatch.setattr("bots.doctools.worker.fetch_bytes", AsyncMock(return_value=pdf_bytes("Hello world")))
    job = await enqueue(worker, operation="ocr_docx")
    await worker.run_job(job)
    documents = api.calls("SendDocument")
    assert len(documents) == 1
    assert documents[0].document.filename == "recognized.docx"
    assert await worker.queue.get(job.id) is None


async def test_shutdown_requeues_inflight_job_without_refund(worker, monkeypatch):
    started = asyncio.Event()

    async def block(*args, **kwargs):
        started.set()
        await asyncio.Event().wait()

    monkeypatch.setattr("bots.doctools.worker.fetch_bytes", block)
    job = await enqueue(worker, quota_day="20261009")
    task = asyncio.create_task(worker.run_job(job))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    replacement = await worker.queue.pop()
    assert replacement and replacement.id == job.id
    assert replacement.attempts == 0
    worker.service.refund.assert_not_awaited()


async def test_vision_ocr_uses_image_and_returns_text_file(worker, api, monkeypatch):
    data = io.BytesIO()
    Image.new("RGB", (100, 50), "white").save(data, "PNG")
    monkeypatch.setattr("bots.doctools.worker.fetch_bytes", AsyncMock(return_value=data.getvalue()))
    worker.ctx.ai = SimpleNamespace(ask=AsyncMock(return_value=AIResult(text="مرحبا بالعالم", model="fake")))
    job = Job(user_id=42, chat_id=42, operation="ocr_text", assets=[DocAsset(kind="image", file_id="scan")], quota_day="20261009")
    await worker.queue.enqueue(job)
    leased = await worker.queue.pop()
    await worker.run_job(leased)
    assert len(api.calls("SendDocument")) == 1
    assert api.calls("SendDocument")[0].document.filename == "recognized.txt"
    attachments = worker.ctx.ai.ask.await_args.kwargs["attachments"]
    assert len(attachments) == 1 and attachments[0].media_type == "image/png"
    worker.service.refund.assert_not_awaited()


async def test_resumed_quiz_does_not_repeat_delivered_polls_or_refund_ai(worker, api, monkeypatch):
    monkeypatch.setattr("bots.doctools.worker.fetch_bytes", AsyncMock(return_value=pdf_bytes("Study facts")))
    questions = [{"question": f"Question {i}", "options": ["A", "B", "C", "D"], "correct": 0, "explanation": "Reason"} for i in range(10)]
    worker.ctx.ai = SimpleNamespace(ask=AsyncMock())
    job = await enqueue(worker, operation="quiz", quota_day="20261009", ai_used=True,
                        delivered_items=4, options={"quiz_questions": questions, "result_pages": 2})
    await worker.run_job(job)
    assert len(api.calls("SendPoll")) == 6
    assert api.calls("SendPoll")[0].question == "Question 4"
    worker.ctx.ai.ask.assert_not_awaited()
    worker.service.refund.assert_not_awaited()


async def test_reaper_removes_only_abandoned_document_scratch(worker):
    root = worker.ctx.platform.bot_data_dir("doctools") / "tmp"
    stale = root / "document-old"
    active = root / "document-active"
    unrelated = root / "other-old"
    for path in [stale, active, unrelated]:
        path.mkdir(parents=True)
        (path / "private.pdf").write_bytes(b"private")
    old = time.time() - 3600
    os.utime(stale, (old, old))
    os.utime(unrelated, (old, old))
    await worker.reap_once()
    assert not stale.exists()
    assert active.exists() and unrelated.exists()
