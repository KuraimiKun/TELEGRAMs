"""Dispatcher factory configuring middlewares, core feature routers, and bot-specific routers."""

from __future__ import annotations

import contextlib

from aiogram import Dispatcher
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.types import ErrorEvent

from core.i18n import Translate
from core.log import get_logger
from core.middlewares import (
    BanMiddleware,
    BotContextMiddleware,
    MaintenanceMiddleware,
    ThrottlingMiddleware,
    UserMiddleware,
)
from core.middlewares._event import notify
from core.observability import HANDLER_ERRORS, capture
from core.routers import common, forcesub, groups, lang, membership, platform, referral, vip
from core.routers.admin import (
    broadcast as adm_broadcast,
)
from core.routers.admin import (
    channels as adm_channels,
)
from core.routers.admin import (
    panel as adm_panel,
)
from core.routers.admin import (
    plans as adm_plans,
)
from core.routers.admin import (
    settings as adm_settings,
)
from core.routers.admin import (
    stats as adm_stats,
)
from core.routers.admin import (
    users as adm_users,
)
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.sdk.module import DurableIngressError

log = get_logger(__name__)

FSM_TTL = 3600


def build_dispatcher(ctx: BotContext) -> Dispatcher:
    """Build a fully-configured, isolated aiogram Dispatcher for a bot context."""
    storage = RedisStorage(
        redis=ctx.redis,
        key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True, prefix=f"{ctx.slug}:fsm"),
        # Abandoned multi-step inputs (admin search, broadcast drafts...) expire instead of lingering forever.
        state_ttl=FSM_TTL,
        data_ttl=FSM_TTL,
    )
    dp = Dispatcher(storage=storage)

    # Workflow data injection
    dp["ctx"] = ctx
    dp["config"] = ctx.platform
    dp["bot_env"] = ctx.env
    dp["redis"] = ctx.redis
    dp["users"] = ctx.users
    dp["settings_service"] = ctx.settings
    dp["subs"] = ctx.subs
    dp["vip"] = ctx.subs
    dp["payments"] = ctx.payments
    dp["stats"] = ctx.stats
    dp["broadcast"] = ctx.broadcast
    dp["groups"] = ctx.groups

    for k, v in ctx.extras.items():
        dp[k] = v

    # Update-level: inject context + resolve the user for every update type.
    dp.update.outer_middleware(BotContextMiddleware(ctx))
    update_pipeline = ctx.module.update_pipeline(ctx)
    if update_pipeline is not None:
        dp.update.outer_middleware(update_pipeline)
    dp.update.outer_middleware(UserMiddleware(ctx))

    pipeline = ctx.module.message_pipeline(ctx)
    if pipeline is not None:
        dp.message.outer_middleware(pipeline)
        dp.edited_message.outer_middleware(pipeline)

    # Event-level guards (Maintenance -> Ban -> Throttling) see the concrete event, so they can reply.
    # pre_checkout_query / chat_member updates are intentionally never guarded.
    maintenance, ban, throttle = MaintenanceMiddleware(ctx), BanMiddleware(), ThrottlingMiddleware(ctx)
    for observer in (dp.message, dp.callback_query, dp.inline_query):
        observer.outer_middleware(maintenance)
        observer.outer_middleware(ban)
    # Inline queries arrive per keystroke and Telegram already rate-limits them: no throttle there.
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(throttle)

    features = ctx.features

    for router in ctx.module.priority_routers(ctx):
        dp.include_router(router)

    # 1. Admin routers
    if Feature.ADMIN in features:
        dp.include_router(adm_panel.build_router(ctx))
        dp.include_router(adm_stats.build_router(ctx))
        dp.include_router(adm_users.build_router(ctx))
        if Feature.BROADCAST in features:
            dp.include_router(adm_broadcast.build_router(ctx))
        dp.include_router(adm_settings.build_router(ctx))
        if Feature.FORCE_SUB in features:
            dp.include_router(adm_channels.build_router(ctx))
        if Feature.VIP in features:
            dp.include_router(adm_plans.build_router(ctx))

        # Dynamic admin tabs contributed by the module
        for section in ctx.module.admin_sections():
            dp.include_router(section.router_factory(ctx))

    # 2. Super-admin platform dashboard + membership tracking (blocks, groups)
    dp.include_router(platform.build_router(ctx))
    dp.include_router(membership.build_router(ctx))
    if Feature.FORCE_SUB in features:
        dp.include_router(forcesub.build_router(ctx))

    # 3. Standard user feature routers
    dp.include_router(common.build_router(ctx))
    if Feature.LANG in features:
        dp.include_router(lang.build_router(ctx))
    if Feature.VIP in features:
        dp.include_router(vip.build_router(ctx))
    if Feature.REFERRAL in features:
        dp.include_router(referral.build_router(ctx))
    if Feature.GROUPS in features:
        dp.include_router(groups.build_router(ctx))

    # 4. Bot-specific handlers
    for r in ctx.module.routers(ctx):
        dp.include_router(r)

    if update_pipeline is not None:
        ctx.extras["guard_dispatcher"] = dp
    dp.errors.register(_error_handler(ctx))
    return dp


def allowed_update_types(ctx: BotContext, dp: Dispatcher) -> list[str]:
    return sorted(set(dp.resolve_used_update_types()) | ctx.module.required_update_types())


def _error_handler(ctx: BotContext):
    """Last-resort handler: log with context and tell the user something went wrong (private chats only)."""

    async def on_error(event: ErrorEvent, t: Translate | None = None) -> bool:
        if isinstance(event.exception, DurableIngressError):
            # The default error handler must not turn a failed inbox write into HTTP 200.
            raise event.exception
        update = event.update
        log.error(
            "unhandled_update_error",
            bot=ctx.slug,
            update_id=update.update_id,
            update_type=update.event_type if update else None,
            error=repr(event.exception),
            exc_info=event.exception,
        )
        HANDLER_ERRORS.labels(ctx.metric_name).inc()
        capture(event.exception, bot=ctx.slug, update_id=update.update_id)
        text = t("error-unknown") if t else "😕 Something went wrong. Please try again later."
        with contextlib.suppress(Exception):
            await notify(update, text)
        return True

    return on_error
