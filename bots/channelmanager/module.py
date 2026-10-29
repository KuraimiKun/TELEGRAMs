"""Channel Manager, including the full-manager factory template."""

from datetime import timedelta
from functools import partial
from pathlib import Path

from aiogram import BaseMiddleware, F, Router
from aiogram.types import ChatMemberUpdated

from bots.channelmanager import admin, handlers, interactions, outbox, publishing_ui, worker
from bots.channelmanager.automation import AutomationService
from bots.channelmanager.batches import BatchService
from bots.channelmanager.billing import BillingService
from bots.channelmanager.config import ChannelManagerEnv
from bots.channelmanager.growth import GrowthService
from bots.channelmanager.ingress import ChannelIngress
from bots.channelmanager.members import MemberService
from bots.channelmanager.posts import PostService
from bots.channelmanager.presets import PresetService
from bots.channelmanager.recurring import RecurrenceService
from bots.channelmanager.senders import SenderService, factory_sweep
from bots.channelmanager.service import ChannelService
from bots.channelmanager.settings import ChannelManagerSettings
from bots.channelmanager.team import TeamService
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.sdk.module import AdminSection, BotModule, CommandSpec, FactoryJob, ScheduledJob, StatLine


class ChannelManagerBot(BotModule):
    slug = "channelmanager"
    title = "Channel Manager"
    table_prefix = "chm_"
    durable_ingress = True
    factory_template = "channelmanager"
    features = {Feature.ADMIN, Feature.LANG, Feature.BROADCAST, Feature.DAILY_STATS}
    env_model = ChannelManagerEnv
    settings_model = ChannelManagerSettings
    locales_dir = Path(__file__).resolve().parent / "locales"

    async def setup(self, ctx: BotContext) -> None:
        ctx.extras["channelmanager"] = ChannelService(ctx)
        ctx.extras["posts"] = PostService(ctx)
        ctx.extras["presets"] = PresetService(ctx)
        ctx.extras["recurring"] = RecurrenceService(ctx)
        ctx.extras["batches"] = BatchService(ctx)
        ctx.extras["automation"] = AutomationService(ctx)
        ctx.extras["members"] = MemberService(ctx)
        ctx.extras["billing"] = BillingService(ctx)
        ctx.extras["growth"] = GrowthService(ctx)
        ctx.extras["team"] = TeamService(ctx)
        ctx.extras["senders"] = SenderService(ctx)
        ctx.broadcast.before_send = partial(outbox.wait_budget, ctx)

    def update_pipeline(self, ctx: BotContext) -> BaseMiddleware:
        return ChannelIngress(ctx)

    def required_update_types(self) -> frozenset[str]:
        return frozenset({"message", "edited_message", "callback_query", "channel_post", "edited_channel_post",
                          "my_chat_member", "chat_member", "chat_join_request", "pre_checkout_query"})

    def priority_routers(self, ctx: BotContext) -> list[Router]:
        router = Router(name=f"chm_lifecycle_{ctx.slug}")

        @router.my_chat_member(F.chat.type == "channel")
        async def lifecycle(event: ChatMemberUpdated) -> None:
            # ChannelIngress commits and queues these events before normal router dispatch.
            return None

        return [router]

    def routers(self, ctx: BotContext) -> list[Router]:
        from bots.channelmanager import advanced_ui, automation_ui, growth_ui, member_interactions, member_ui
        return [growth_ui.build_router(ctx), member_interactions.build_router(ctx), interactions.build_router(ctx), member_ui.build_router(ctx), automation_ui.build_router(ctx), advanced_ui.build_router(ctx), publishing_ui.build_router(ctx), handlers.build_router(ctx)]

    def commands(self) -> list[CommandSpec]:
        return [CommandSpec("channels", "Your channels"), CommandSpec("connect", "Connect a channel"),
                CommandSpec("newpost", "Create a post"), CommandSpec("posts", "Your posts"),
                CommandSpec("signature", "Channel signature"), CommandSpec("timezone", "Channel timezone"),
                CommandSpec("cancel", "Cancel input"),
                CommandSpec("advanced", "Advanced publishing"), CommandSpec("recurring", "Recurring posts"),
                CommandSpec("multipost", "Multipost batches"), CommandSpec("presets", "Saved sets"),
                CommandSpec("calendars", "Weekly calendars"), CommandSpec("reactions", "Default vote buttons"),
                CommandSpec("automation", "Auto-complete and forwarding"),
                CommandSpec("members", "Admission and member workflows"),
                CommandSpec("team", "Publishing team"), CommandSpec("locked", "Locked content"),
                CommandSpec("campaigns", "Subscriber campaigns"), CommandSpec("plans", "Channel plans and invoices"),
                CommandSpec("senders", "Branded senders"), CommandSpec("subscriber", "Subscriber menu"),
                CommandSpec("menus", "Configure subscriber menu and feedback"),
                CommandSpec("subscribe", "Subscribe to channel campaigns"), CommandSpec("unsubscribe", "Unsubscribe"),
                CommandSpec("forget", "Remove campaign and feedback data"),
                CommandSpec("help", "Channel Manager help")]

    def processes(self):
        return {"worker": worker.run}

    def scheduled_jobs(self) -> list[ScheduledJob]:
        return [ScheduledJob("recovery", timedelta(seconds=30), worker.sweep, timeout=timedelta(seconds=25))]

    def factory_jobs(self) -> list[FactoryJob]:
        return [FactoryJob("channelmanager", timedelta(seconds=10), factory_sweep, timeout=timedelta(seconds=55))]

    async def on_child_stopping(self, ctx: BotContext, reason: str) -> str | None:
        return await ctx.extras["senders"].stopping(reason)

    def admin_sections(self) -> list[AdminSection]:
        return [AdminSection("channelmanager", "chm-btn-admin", admin.build_router)]

    async def stats(self, ctx: BotContext) -> list[StatLine]:
        svc: ChannelService = ctx.extras["channelmanager"]
        return [StatLine("Channel Manager", key, value) for key, value in (await svc.totals()).items()]
