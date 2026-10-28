"""Fetching user files from Telegram safely (size caps) and scratch directories that always get cleaned up."""

from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
from collections.abc import AsyncIterator, Buffer
from pathlib import Path

from core.sdk.context import BotContext

MB = 1024 * 1024
# The cloud Bot API refuses getFile above 20 MB; a local Bot API server serves up to 2 GB.
CLOUD_DOWNLOAD_LIMIT = 20 * MB


class FileTooLarge(ValueError):
    def __init__(self, size: int, limit: int) -> None:
        super().__init__(f"file is {size} bytes, limit is {limit}")
        self.size = size
        self.limit = limit


class _LimitedBuffer(io.BytesIO):
    def __init__(self, limit: int) -> None:
        super().__init__()
        self.limit = limit

    def write(self, data: Buffer, /) -> int:
        size = self.tell() + memoryview(data).nbytes
        if size > self.limit:
            raise FileTooLarge(size, self.limit)
        return super().write(data)


def download_limit(ctx: BotContext, wanted: int) -> int:
    """The effective cap: what the bot allows, bounded by what the Bot API can hand out."""
    return wanted if ctx.platform.uses_local_api else min(wanted, CLOUD_DOWNLOAD_LIMIT)


async def fetch_bytes(ctx: BotContext, file_id: str, size: int | None, max_bytes: int) -> bytes:
    """Download a Telegram file into memory, refusing anything above ``max_bytes`` (checked before and after)."""
    limit = download_limit(ctx, max_bytes)
    if size is not None and size > limit:
        raise FileTooLarge(size, limit)
    buf = _LimitedBuffer(limit)
    await ctx.bot.download(file_id, destination=buf)
    data = buf.getvalue()
    if len(data) > limit:
        raise FileTooLarge(len(data), limit)
    return data


@contextlib.asynccontextmanager
async def scratch_dir(ctx: BotContext, prefix: str = "job") -> AsyncIterator[Path]:
    """A private temporary directory under the bot's data dir, removed on exit whatever happens."""
    root = ctx.platform.bot_data_dir(ctx.slug) / "tmp"
    root.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(prefix=f"{prefix}-", dir=root))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
