"""Process runner for bot-defined background tasks (e.g. workers)."""

from __future__ import annotations

import asyncio

from core.log import get_logger
from core.runtime.app import run_role, wait_or_stop
from core.sdk.context import BotContext
from core.sdk.registry import discover

log = get_logger("process")


async def serve_processes(
    contexts: list[BotContext],
    stop: asyncio.Event,
    only: str | None = None,
) -> None:
    """Run bot processes (all, or the one named ``only``) until ``stop``; then let them drain."""
    tasks: list[asyncio.Task] = []
    for ctx in contexts:
        for name, fn in ctx.module.processes().items():
            if only is None or name == only:
                log.info("running_process", bot=ctx.slug, process=name)
                tasks.append(asyncio.ensure_future(fn(ctx)))
    if not tasks:
        log.error("process_not_found", process=only)
        return
    await asyncio.gather(*(wait_or_stop(t, stop) for t in tasks))


async def run_process(slug: str, process_name: str) -> None:
    module = discover([slug])[0]
    if process_name not in module.processes():
        raise SystemExit(
            f"Bot '{slug}' has no process '{process_name}'. Available: {', '.join(module.processes()) or 'none'}"
        )

    async def role(contexts: list[BotContext], stop: asyncio.Event) -> None:
        await serve_processes(contexts, stop, only=process_name)

    await run_role(role, [slug], strict=True, role_name=f"{slug}-{process_name}")
