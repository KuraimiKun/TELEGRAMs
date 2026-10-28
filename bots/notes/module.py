"""Notes & Reminders: a small second bot proving the multi-bot SDK end to end.

It exercises: prefixed tables, localized handlers (en + ar), runtime settings, VIP limits and plans,
a scheduled job, an admin tab, bot stats, and the core action bookkeeping (referral rewards).
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from aiogram import Router

from bots.notes import admin
from bots.notes.config import NotesEnv
from bots.notes.handlers import main
from bots.notes.service import NotesService, deliver_due_reminders
from bots.notes.settings import NotesSettings
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.sdk.module import AdminSection, BotModule, CommandSpec, PlanSpec, ScheduledJob, StatLine


class NotesBot(BotModule):
    slug = "notes"
    title = "Notes & Reminders"
    table_prefix = "notes_"
    features = {Feature.ADMIN, Feature.LANG, Feature.VIP, Feature.REFERRAL, Feature.BROADCAST, Feature.DAILY_STATS}
    env_model = NotesEnv
    settings_model = NotesSettings
    locales_dir = Path(__file__).resolve().parent / "locales"
    default_plans = [
        PlanSpec(name="1 Month VIP", days=30, stars=50, sort=1),
        PlanSpec(name="1 Year VIP", days=365, stars=400, sort=2),
    ]

    async def setup(self, ctx: BotContext) -> None:
        ctx.extras["notes"] = NotesService(ctx.sm)

    def routers(self, ctx: BotContext) -> list[Router]:
        return [main.build_router(ctx)]

    def commands(self) -> list[CommandSpec]:
        return [
            CommandSpec("notes", "Your notes"),
            CommandSpec("remind", "Set a reminder"),
            CommandSpec("reminders", "Upcoming reminders"),
            CommandSpec("help", "How to use the bot"),
        ]

    def admin_sections(self) -> list[AdminSection]:
        return [AdminSection(tab="notes", title="notes-btn-admin-tab", router_factory=admin.build_router)]

    def scheduled_jobs(self) -> list[ScheduledJob]:
        return [
            ScheduledJob(name="reminders", interval=timedelta(seconds=30), handler=_deliver, timeout=timedelta(minutes=5))
        ]

    async def stats(self, ctx: BotContext) -> list[StatLine]:
        totals = await ctx.extras["notes"].totals()
        return [
            StatLine("Notes", "Stored notes", f"{totals['notes']:,}"),
            StatLine("Notes", "Pending reminders", f"{totals['pending']:,}"),
            StatLine("Notes", "Delivered reminders", f"{totals['sent']:,}"),
        ]

    async def vip_info(self, ctx: BotContext) -> dict:
        stg: NotesSettings = await ctx.settings.get()
        return {"notes": stg.vip_max_notes, "reminders": stg.vip_max_reminders,
                "free_notes": stg.free_max_notes, "free_reminders": stg.free_max_reminders}


async def _deliver(ctx: BotContext) -> None:
    await deliver_due_reminders(ctx)
