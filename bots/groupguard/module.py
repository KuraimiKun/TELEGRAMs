"""Group Guard: a full group manager — moderation, captcha, anti-spam, notes, filters, night mode.

Viral loop: it lives in groups; every welcome carries "Protected by @bot", and admins of one group add it to
the next. Also offered by the bot factory as the "groupguard" template (a branded copy for a community).
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from aiogram import BaseMiddleware, Router

from bots.groupguard import (
    admin,
    cleanup,
    content_access,
    fed_enforcement,
    group_broadcast,
    jobs,
    operations,
    privacy,
    raids,
    reactions,
    repeats,
    verification,
)
from bots.groupguard.config import GuardEnv
from bots.groupguard.handlers import (
    antispam,
    blocklists,
    captcha,
    connections,
    content,
    data,
    fed_bans,
    federations,
    identity,
    locks,
    moderation,
    panel,
    policy,
    start,
    tools,
    topics,
    utilities,
    welcome,
)
from bots.groupguard.pipeline import GroupPipeline
from bots.groupguard.replay import ReplayMiddleware
from bots.groupguard.scope import GroupMessages
from bots.groupguard.service import GuardService
from bots.groupguard.settings import GuardSettings
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.sdk.module import AdminSection, BotModule, CommandSpec, FactoryJob, PlanSpec, ScheduledJob, StatLine


class GroupGuardBot(BotModule):
    slug = "groupguard"
    title = "Group Guard"
    table_prefix = "gg_"
    features = {Feature.ADMIN, Feature.LANG, Feature.VIP, Feature.BROADCAST, Feature.DAILY_STATS}
    child_features = {Feature.ADMIN, Feature.LANG, Feature.BROADCAST}
    factory_template = "groupguard"
    env_model = GuardEnv
    settings_model = GuardSettings
    locales_dir = Path(__file__).resolve().parent / "locales"
    default_plans = [PlanSpec(name="1 Month VIP", days=30, stars=100, sort=1)]

    async def setup(self, ctx: BotContext) -> None:
        ctx.extras["guard"] = GuardService(ctx.sm, ctx.bot_id)
        ctx.extras["guard_job_handlers"] = {"repeat_note": repeats.run, "content_delete": repeats.delete_message,
            "verification_release": verification.release_job, "verification_unban": verification.complete_unban_job,
            "verification_refund": verification.refund_job, "raid_expire": raids.expire_job,
            "bot_message_clean": cleanup.run, "group_broadcast": group_broadcast.run,
            "fed_fanout": fed_enforcement.fanout, "fed_enforce": fed_enforcement.run,"privacy_cache":privacy.run_cache}

    def update_pipeline(self, ctx: BotContext) -> BaseMiddleware:
        return ReplayMiddleware(ctx)

    def message_pipeline(self, ctx: BotContext) -> BaseMiddleware:
        return GroupPipeline(ctx)

    def required_update_types(self) -> frozenset[str]:
        return frozenset({"message", "edited_message", "message_reaction", "message_reaction_count",
                          "chat_member", "my_chat_member", "chat_join_request", "callback_query", "channel_post"})

    def priority_routers(self, ctx: BotContext) -> list[Router]:
        # Protection sees every group message first; its routers then handle commands and triggers.
        group = Router(name="gg_group")
        group.message.filter(GroupMessages())
        group.include_routers(
            operations.build_router(ctx), welcome.build_router(ctx), tools.build_router(ctx), moderation.build_router(ctx),
            policy.build_router(ctx), topics.build_router(ctx), captcha.build_router(ctx), antispam.build_router(ctx), locks.build_router(ctx), blocklists.build_router(ctx), content.build_router(ctx)
        )
        return [connections.build_router(ctx), start.build_help_router(ctx), data.build_router(ctx), fed_bans.build_router(ctx), federations.build_router(ctx), utilities.build_router(ctx), tools.log_setup_router(ctx), reactions.build_router(ctx), verification.build_router(ctx), content_access.build_router(ctx), identity.build_router(ctx), panel.build_router(ctx), group]

    def routers(self, ctx: BotContext) -> list[Router]:
        return [start.build_router(ctx)]

    async def on_child_stopping(self, ctx: BotContext, reason: str) -> str | None:
        return await jobs.stop_child(ctx, reason)

    def commands(self) -> list[CommandSpec]:
        return [CommandSpec("help", "Commands"), CommandSpec("settings", "Group settings (in a group)")]

    def admin_sections(self) -> list[AdminSection]:
        return [AdminSection(tab=admin.TAB, title="gg-btn-admin-tab", router_factory=admin.build_router)]

    def scheduled_jobs(self) -> list[ScheduledJob]:
        return [
            ScheduledJob("captchas", timedelta(seconds=30), jobs.captcha_job, timeout=timedelta(minutes=2)),
            ScheduledJob("night", timedelta(minutes=5), jobs.night_job, timeout=timedelta(minutes=5)),
        ]

    def factory_jobs(self) -> list[FactoryJob]:
        return [
            FactoryJob("captchas", timedelta(seconds=30), jobs.factory_captchas, timeout=timedelta(minutes=2)),
            FactoryJob("night", timedelta(minutes=5), jobs.factory_night, timeout=timedelta(minutes=10)),
        ]

    async def stats(self, ctx: BotContext) -> list[StatLine]:
        totals = await ctx.extras["guard"].totals()
        return [
            StatLine("Guard", "Protected groups", f"{totals['groups']:,}"),
            StatLine("Guard", "Warnings issued", f"{totals['warns']:,}"),
            StatLine("Guard", "Notes & filters", f"{totals['items']:,}"),
        ]
