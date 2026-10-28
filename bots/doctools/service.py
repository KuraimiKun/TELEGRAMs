"""Ten-minute file baskets, admission limits and privacy-preserving job metrics."""

from __future__ import annotations

import secrets
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Any, cast

from sqlalchemy import func, select

from bots.doctools.models import DocumentJob
from bots.doctools.operations import DocumentError
from bots.doctools.queue import Basket, DocAsset, Job, JobQueue
from bots.doctools.settings import DocToolsSettings
from core.db.base import upsert
from core.files import download_limit
from core.sdk.context import BotContext
from core.sdk.quota import DailyQuota

BASKET_TTL = 600
AI_OPERATIONS = {"summarize", "quiz", "ocr_text", "ocr_docx"}


class QuotaExceeded(DocumentError):
    def __init__(self) -> None:
        super().__init__("quota")


class QueueFull(DocumentError):
    def __init__(self) -> None:
        super().__init__("queue")


@dataclass(slots=True, frozen=True)
class Caps:
    max_bytes: int
    max_pages: int
    ai_daily_limit: int


def supported_actions(basket: Basket) -> list[str]:
    if not basket.assets:
        return []
    kinds = {asset.kind for asset in basket.assets}
    if kinds == {"pdf"}:
        actions = ["count", "ocr_text", "ocr_docx", "summarize", "quiz"]
        if len(basket.assets) > 1:
            return ["merge", *actions]
        return ["split", "extract", "compress", "rotate", "images", "numbers", "watermark", "encrypt", "decrypt", *actions]
    if kinds == {"image"}:
        return ["image_pdf", "enhance", "ocr_text", "ocr_docx", "count"]
    if kinds <= {"pdf", "image", "docx", "text"}:
        actions = ["count", "ocr_text", "ocr_docx"]
        if "image" not in kinds:
            actions.extend(["summarize", "quiz"])
        return actions
    return []


_ADD_ASSET = """
local raw = redis.call('GET', KEYS[1])
local ttl = redis.call('PTTL', KEYS[1])
local basket = raw and cjson.decode(raw) or cjson.decode(ARGV[1])
local assets = basket.assets
if not raw then assets = {} end
if #assets >= tonumber(ARGV[3]) then return -1 end
local size = 0
for _, asset in ipairs(assets) do size = size + asset.size_bytes end
local asset = cjson.decode(ARGV[2])
if size + asset.size_bytes > tonumber(ARGV[4]) then return -2 end
table.insert(assets, asset)
basket.assets = assets
basket.callback_stamp = tonumber(ARGV[6])
raw = cjson.encode(basket)
if ttl < 0 then ttl = tonumber(ARGV[5]) * 1000 end
redis.call('SET', KEYS[1], raw, 'PX', math.max(ttl, 1))
return raw
"""


class DocToolsService:
    def __init__(self, ctx: BotContext) -> None:
        self.ctx = ctx
        self.queue: JobQueue = ctx.extras.get("doctools_queue") or JobQueue(ctx.redis, ctx.keys)
        self.quota = DailyQuota(ctx.redis, ctx.keys, "dt_ai")

    def _basket_key(self, user_id: int, chat_id: int) -> str:
        return self.ctx.keys("dt", "basket", chat_id, user_id)

    async def caps(self, is_vip: bool) -> Caps:
        settings: DocToolsSettings = await self.ctx.settings.get()
        return Caps(
            download_limit(self.ctx, (settings.vip_max_mb if is_vip else settings.free_max_mb) * 1024 * 1024),
            settings.vip_max_pages if is_vip else settings.free_max_pages,
            settings.vip_ai_daily_limit if is_vip else settings.free_ai_daily_limit,
        )

    async def basket(self, user_id: int, chat_id: int) -> Basket | None:
        raw = await self.ctx.redis.get(self._basket_key(user_id, chat_id))
        return Basket.model_validate_json(raw) if raw else None

    async def add_asset(self, user_id: int, chat_id: int, asset: DocAsset) -> Basket:
        user = await self.ctx.users.get(user_id)
        caps = await self.caps(bool(user and user.is_vip()))
        settings: DocToolsSettings = await self.ctx.settings.get()
        if not asset.file_id and asset.text is None:
            raise DocumentError()
        if asset.text is not None:
            if len(asset.text) > 200_000:
                raise DocumentError("large")
            asset = asset.model_copy(update={"size_bytes": len(asset.text.encode("utf-8"))})
        if asset.size_bytes > caps.max_bytes:
            raise DocumentError("large")
        basket = Basket(user_id=user_id, chat_id=chat_id)
        raw = await cast(Awaitable[Any], self.ctx.redis.eval(
            _ADD_ASSET, 1, self._basket_key(user_id, chat_id), basket.model_dump_json(), asset.model_dump_json(),
            settings.max_basket_files, caps.max_bytes, BASKET_TTL, secrets.randbits(31),
        ))
        if isinstance(raw, int):
            raise DocumentError("large" if raw == -2 else "basket")
        return Basket.model_validate_json(raw)

    async def clear_basket(self, user_id: int, chat_id: int) -> None:
        await self.ctx.redis.delete(self._basket_key(user_id, chat_id))

    supported_actions = staticmethod(supported_actions)

    async def submit(
        self, user_id: int, chat_id: int, operation: str, *, options: dict | None = None,
        lang: str = "en", reply_to: int | None = None,
    ) -> Job:
        basket = await self.basket(user_id, chat_id)
        if basket is None or operation not in supported_actions(basket):
            raise DocumentError()
        user = await self.ctx.users.get(user_id)
        is_vip = bool(user and user.is_vip())
        caps = await self.caps(is_vip)
        if sum(asset.size_bytes for asset in basket.assets) > caps.max_bytes:
            raise DocumentError("large")
        job = Job(
            user_id=user_id, chat_id=chat_id, operation=operation, assets=basket.assets,
            options=options or {}, lang=lang, reply_to=reply_to, is_vip=is_vip,
            max_bytes=caps.max_bytes, max_pages=caps.max_pages,
        )
        if operation in {"summarize", "quiz"} and self.ctx.ai is None:
            raise DocumentError("unavailable")
        if operation in AI_OPERATIONS and self.ctx.ai is not None:
            job.quota_day = await self.quota.consume(user_id, caps.ai_daily_limit)
            if job.quota_day is None:
                raise QuotaExceeded()
        try:
            settings: DocToolsSettings = await self.ctx.settings.get()
            if await self.queue.enqueue(job, max_active=settings.max_active_jobs) < 0:
                raise QueueFull()
        except BaseException:
            await self.refund(job)
            raise
        return job

    async def refund(self, job: Job) -> None:
        if job.quota_day:
            await self.quota.refund(job.user_id, day=job.quota_day, token=job.id)

    async def record(self, job: Job, status: str, *, pages: int = 0, size_bytes: int = 0) -> None:
        async with self.ctx.sm() as session:
            await session.execute(
                upsert(session, DocumentJob).values(
                    id=job.id, bot_id=self.ctx.bot_id, user_id=job.user_id, operation=job.operation,
                    status=status, pages=pages, size_bytes=size_bytes,
                ).on_conflict_do_update(
                    index_elements=[DocumentJob.id], set_={"status": status, "pages": pages, "size_bytes": size_bytes},
                )
            )
            await session.commit()

    async def totals(self) -> dict[str, int]:
        async with self.ctx.sm() as session:
            rows = await session.execute(
                select(DocumentJob.status, func.count()).where(DocumentJob.bot_id == self.ctx.bot_id).group_by(DocumentJob.status)
            )
            counts = {status: int(count) for status, count in rows}
        return {"total": sum(counts.values()), "ok": counts.get("ok", 0), "failed": counts.get("failed", 0)}
