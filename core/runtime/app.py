"""Process lifecycle: build shared infra + bot contexts once, run a role, shut down gracefully on SIGTERM."""

from __future__ import annotations

import asyncio
import contextlib
import os
import signal
import socket
import time
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from pathlib import Path
from typing import TYPE_CHECKING

from redis.asyncio import from_url as redis_from_url

from core.config import PlatformConfig, get_platform_config
from core.log import get_logger
from core.observability import init_sentry, start_metrics_server
from core.redis import PLATFORM
from core.sdk.context import BotContext
from core.sdk.registry import SharedInfra, build_context, discover

if TYPE_CHECKING:
    from core.factory.runtime import ChildRegistry

log = get_logger("runtime")

# Shared infrastructure of the running process (set by run_role), for roles that build more contexts later.
CURRENT_INFRA: ContextVar[SharedInfra | None] = ContextVar("current_infra", default=None)


def child_registry(contexts: list[BotContext], stop: asyncio.Event) -> ChildRegistry | None:
    """Runtime registry of user-created bots, when the factory is configured in this process."""
    infra = CURRENT_INFRA.get()
    if infra is None or not contexts or contexts[0].platform.factory_secret_key is None:
        return None
    from core.factory.runtime import ChildRegistry

    registry = ChildRegistry(contexts[0].platform, infra, stop)
    return registry if registry.enabled else None

Role = Callable[[list[BotContext], asyncio.Event], Awaitable[None]]


async def build_contexts(
    infra: SharedInfra,
    platform: PlatformConfig,
    slugs: list[str] | None = None,
    *,
    strict: bool = False,
) -> list[BotContext]:
    """Build a context per bot. One bot's bad token or DB conflict must not take every other bot down,
    so failures are logged and skipped unless ``strict`` (single-bot processes) is set."""
    contexts: list[BotContext] = []
    for module in discover(slugs, platform):
        try:
            contexts.append(await build_context(module, platform, infra))
        except Exception as e:
            if strict:
                raise
            log.exception("bot_context_failed", bot=module.slug, error=str(e))
    return contexts


def install_signal_handlers(stop: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError, RuntimeError):  # Windows / non-main thread
            loop.add_signal_handler(sig, stop.set)


async def close_contexts(contexts: list[BotContext], infra: SharedInfra) -> None:
    for ctx in contexts:
        with contextlib.suppress(Exception):
            if ctx.bot.session is not infra.session:
                await ctx.bot.session.close()
    await infra.close()


HEARTBEAT_EVERY = 15
HEARTBEAT_TTL = 60


def instance_id() -> str:
    return os.environ.get("HOSTNAME") or socket.gethostname()


def heartbeat_key(role_name: str, instance: str | None = None) -> str:
    return PLATFORM("hb", role_name, instance or instance_id())


def heartbeat_file(role_name: str) -> Path:
    return Path(f"/tmp/hb-{role_name}")


async def _heartbeat(infra: SharedInfra, role_name: str, stop: asyncio.Event) -> None:
    key = heartbeat_key(role_name)
    hb_path = heartbeat_file(role_name)
    while not stop.is_set():
        now = str(time.time())
        with contextlib.suppress(Exception):
            hb_path.write_text(now, encoding="utf-8")
        with contextlib.suppress(Exception):
            await infra.redis.set(key, now, ex=HEARTBEAT_TTL)
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=HEARTBEAT_EVERY)
    with contextlib.suppress(Exception):
        hb_path.unlink(missing_ok=True)
    with contextlib.suppress(Exception):
        await infra.redis.delete(key)


async def check_heartbeat(role_name: str, max_age: float = HEARTBEAT_TTL) -> bool:
    """Used by container healthchecks: is this instance's role loop alive?"""
    hb_path = heartbeat_file(role_name)
    with contextlib.suppress(Exception):
        if hb_path.exists():
            return time.time() - float(hb_path.read_text(encoding="utf-8").strip()) < max_age
    platform = get_platform_config()
    redis = redis_from_url(platform.redis_url)
    try:
        raw = await redis.get(heartbeat_key(role_name))
        return raw is not None and time.time() - float(raw) < max_age
    finally:
        await redis.aclose()


async def run_role(
    role: Role,
    slugs: list[str] | None = None,
    platform: PlatformConfig | None = None,
    *,
    strict: bool = False,
    role_name: str = "app",
) -> None:
    """Common entrypoint: infra -> contexts -> role(contexts, stop) -> graceful cleanup."""
    platform = platform or get_platform_config()
    init_sentry(platform, role_name)
    if role_name != "gateway":
        start_metrics_server(platform.metrics_port)
    infra = await SharedInfra.create(platform)
    CURRENT_INFRA.set(infra)
    stop = asyncio.Event()
    install_signal_handlers(stop)
    contexts: list[BotContext] = []
    hb = asyncio.create_task(_heartbeat(infra, role_name, stop))
    try:
        contexts = await build_contexts(infra, platform, slugs, strict=strict)
        if not contexts:
            log.error("no_bots_available")
            return
        for ctx in contexts:
            ctx.shutdown = stop
        await role(contexts, stop)
    finally:
        stop.set()
        await hb
        await close_contexts(contexts, infra)
        log.info("process_stopped", role=role_name)


async def wait_or_stop(task: asyncio.Task, stop: asyncio.Event, grace: float = 25.0) -> None:
    """Run ``task`` until it finishes or ``stop`` is set; then give it ``grace`` seconds to wind down."""
    stopper = asyncio.create_task(stop.wait())
    done, _ = await asyncio.wait({task, stopper}, return_when=asyncio.FIRST_COMPLETED)
    stopper.cancel()
    if task in done:
        task.result()
        return
    try:
        await asyncio.wait_for(asyncio.shield(task), timeout=grace)
    except TimeoutError:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await task
