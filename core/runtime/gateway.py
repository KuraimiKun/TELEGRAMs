"""Gateway process: serves webhooks or polling for all configured bots in a single event loop."""

from __future__ import annotations

import asyncio
import contextlib

from aiogram import Dispatcher
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from core.config import PlatformConfig
from core.factory.serving import ChildPoller, ChildWebhook
from core.log import get_logger
from core.runtime.app import child_registry, run_role
from core.runtime.dispatcher import allowed_update_types, build_dispatcher
from core.sdk.context import BotContext
from core.sdk.features import Feature

log = get_logger("gateway")


def command_specs(ctx: BotContext) -> list[tuple[str, str]]:
    """(command, i18n key) for every command this bot exposes, in menu order."""
    specs: list[tuple[str, str]] = [("start", "cmd-start")]
    specs += [(cs.command, f"cmd-{cs.command}") for cs in ctx.module.commands()]
    features = ctx.features
    if Feature.VIP in features:
        specs.append(("vip", "cmd-vip"))
    if Feature.REFERRAL in features:
        specs.append(("referral", "cmd-referral"))
    if Feature.LANG in features:
        specs.append(("lang", "cmd-lang"))
    specs += [("terms", "cmd-terms"), ("support", "cmd-support")]
    unique: dict[str, str] = {}
    for command, key in specs:
        unique.setdefault(command, key)
    return list(unique.items())


async def register_bot_commands(ctx: BotContext) -> None:
    """Register slash commands in every installed language (Telegram shows the user's language).

    /admin is intentionally not advertised to regular users.
    """
    specs = command_specs(ctx)
    module_desc = {cs.command: cs.description for cs in ctx.module.commands()}

    def build(lang: str) -> list[BotCommand]:
        out = []
        for command, key in specs:
            text = ctx.translator.get(lang, key)
            if text == key:  # no translation: fall back to the module's English description
                text = module_desc.get(command, command)
            out.append(BotCommand(command=command, description=text[:256]))
        return out

    already_loaded = set(ctx.translator.bundles.keys())
    try:
        await ctx.bot.set_my_commands(build(ctx.translator.default))
    except Exception as e:
        log.warning("failed_to_set_commands", bot=ctx.slug, error=str(e))
    for lang in ctx.translator.locales:
        if len(lang) != 2 or not lang.isalpha():
            continue
        try:
            await ctx.bot.set_my_commands(build(lang), language_code=lang)
        except Exception as e:
            log.warning("failed_to_set_commands", bot=ctx.slug, lang=lang, error=str(e))
        finally:
            if lang != ctx.translator.default and lang not in already_loaded:
                ctx.translator.bundles.pop(lang, None)


def _health_routes(app: web.Application, contexts: list[BotContext]) -> None:
    async def live(_request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def ready(_request: web.Request) -> web.Response:
        checks: dict[str, str] = {}
        ctx = contexts[0]
        try:
            async with ctx.sm() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {type(e).__name__}"
        try:
            await ctx.redis.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {type(e).__name__}"
        healthy = all(v == "ok" for v in checks.values())
        return web.json_response(
            {"status": "ok" if healthy else "degraded", "checks": checks, "bots": len(contexts)},
            status=200 if healthy else 503,
        )

    async def metrics(_request: web.Request) -> web.Response:
        return web.Response(body=generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})

    app.router.add_get("/metrics", metrics)
    app.router.add_get("/health", live)
    app.router.add_get("/health/live", live)
    app.router.add_get("/health/ready", ready)


async def serve_gateway(contexts: list[BotContext], stop: asyncio.Event) -> None:
    """Serve updates for every bot until ``stop`` fires. A bot that fails to configure is skipped, not fatal."""
    platform = contexts[0].platform
    app = web.Application()
    _health_routes(app, contexts)

    dispatchers: dict[str, Dispatcher] = {}
    for c in contexts:
        try:
            dispatchers[c.slug] = build_dispatcher(c)
        except Exception as e:
            log.exception("bot_dispatcher_failed", bot=c.slug, error=str(e))

    # User-created (factory) bots share this process: one dynamic route instead of one per bot.
    children = child_registry(contexts, stop)
    child_webhook: ChildWebhook | None = None
    child_poller: ChildPoller | None = None
    background: list[asyncio.Task] = []
    if children is not None:
        background.append(asyncio.create_task(children.listen(), name="factory:listen"))
        if platform.webhook_base_url:
            child_webhook = ChildWebhook(children, platform)
            child_webhook.register(app)
        else:
            child_poller = ChildPoller(children, platform.factory_dev_polling_max)

    polling: list[tuple[Dispatcher, asyncio.Task]] = []
    if platform.webhook_base_url:
        for c in contexts:
            dp = dispatchers.get(c.slug)
            if dp is None:
                continue
            path = f"/webhook/{c.slug}"
            secret = c.env.effective_webhook_secret
            SimpleRequestHandler(dispatcher=dp, bot=c.bot, secret_token=secret,
                                 handle_in_background=not c.module.durable_ingress).register(app, path=path)
            setup_application(app, dp, bot=c.bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, platform.web_host, platform.web_port)
    await site.start()
    log.info("gateway_http_started", host=platform.web_host, port=platform.web_port, webhook=bool(platform.webhook_base_url))

    if platform.webhook_base_url:
        base_url = platform.webhook_base_url.rstrip("/")
        for c in contexts:
            dp = dispatchers.get(c.slug)
            if dp is None:
                continue
            path = f"/webhook/{c.slug}"
            secret = c.env.effective_webhook_secret
            try:
                await c.bot.set_webhook(
                    url=f"{base_url}{path}",
                    secret_token=secret,
                    drop_pending_updates=False,
                    allowed_updates=allowed_update_types(c, dp),
                    max_connections=platform.webhook_max_connections,
                )
                log.info("webhook_configured", bot=c.slug, url=f"{base_url}{path}")
            except Exception as e:
                log.exception("set_webhook_failed", bot=c.slug, error=str(e))
    else:
        for c in contexts:
            dp = dispatchers.get(c.slug)
            if dp is None:
                continue
            await c.bot.delete_webhook(drop_pending_updates=False)
            task = asyncio.create_task(
                dp.start_polling(
                    c.bot,
                    handle_signals=False,
                    close_bot_session=False,
                    allowed_updates=allowed_update_types(c, dp),
                ),
                name=f"polling:{c.slug}",
            )
            polling.append((dp, task))
        log.info("gateway_polling_started", bots=[dp_task[1].get_name() for dp_task in polling])

    if child_poller is not None:
        await child_poller.start()

    async def _register_all_commands() -> None:
        for c in contexts:
            if c.slug in dispatchers:
                await register_bot_commands(c)

    background.append(asyncio.create_task(_register_all_commands(), name="commands:register"))

    await stop.wait()
    log.info("gateway_stopping")
    for dp, _task in polling:
        with contextlib.suppress(RuntimeError):
            await dp.stop_polling()
    await asyncio.gather(*(task for _dp, task in polling), return_exceptions=True)
    if child_poller is not None:
        await child_poller.close()
    await runner.cleanup()
    if child_webhook is not None:
        await child_webhook.drain()
    for task in background:
        task.cancel()
    await asyncio.gather(*background, return_exceptions=True)
    if children is not None:
        await children.close()


async def run_gateway(slugs: list[str] | None = None, platform: PlatformConfig | None = None) -> None:
    await run_role(serve_gateway, slugs, platform, role_name="gateway")
