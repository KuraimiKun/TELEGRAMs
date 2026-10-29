"""Abstract contract for pluggable bot modules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from aiogram import BaseMiddleware, Router
from aiogram.types import TelegramObject
from pydantic import BaseModel

from core.config import BaseBotEnv
from core.db.models import BotUser
from core.sdk.features import Feature

if TYPE_CHECKING:
    from core.factory.runtime import ChildRegistry
    from core.sdk.context import BotContext


class DurableIngressError(RuntimeError):
    """An update was not committed; webhook delivery must fail instead of acknowledging it."""


@dataclass(slots=True)
class PlanSpec:
    name: str
    days: int
    stars: int
    sort: int = 0


@dataclass(slots=True)
class CommandSpec:
    command: str
    description: str


@dataclass(slots=True)
class AdminSection:
    tab: str
    title: str
    router_factory: Callable[[BotContext], Router]


@dataclass(slots=True)
class ScheduledJob:
    name: str
    interval: timedelta
    handler: Callable[[BotContext], Awaitable[None]]
    # Hard limit for one run (defaults to the interval).
    timeout: timedelta | None = None


@dataclass(slots=True)
class FactoryJob:
    """Periodic work for *all* user-created bots of a template, run once per deployment (not once per bot).

    The handler receives the :class:`~core.factory.runtime.ChildRegistry` to load the bots it needs.
    """

    name: str
    interval: timedelta
    handler: Callable[[ChildRegistry], Awaitable[None]]
    timeout: timedelta | None = None


@dataclass(slots=True)
class StatLine:
    section: str
    label: str
    value: str | int


class BaseBotSettings(BaseModel):
    """Base runtime settings configurable via admin panel."""

    maintenance: bool = False
    force_sub_enabled: bool = True
    sponsor_enabled: bool = False
    sponsor_text: str = ""
    referral_enabled: bool = True
    referral_required: int = 5
    referral_reward_days: int = 3
    groups_enabled: bool = True

    @classmethod
    def setting_groups(cls) -> dict[str, list[str]]:
        return {
            "growth": [
                "force_sub_enabled",
                "sponsor_enabled",
                "sponsor_text",
                "referral_enabled",
                "referral_required",
                "referral_reward_days",
            ],
            "features": ["maintenance", "groups_enabled"],
        }


class BotModule(ABC):
    """Contract that every bot in `bots/<slug>` must implement."""

    slug: ClassVar[str]
    title: ClassVar[str]
    table_prefix: ClassVar[str]
    features: ClassVar[set[Feature]] = {Feature.ADMIN, Feature.LANG, Feature.BROADCAST}
    env_model: ClassVar[type[BaseBotEnv]] = BaseBotEnv
    settings_model: ClassVar[type[BaseBotSettings]] = BaseBotSettings
    default_plans: ClassVar[list[PlanSpec]] = []
    locales_dir: ClassVar[Path | None] = None

    # False for factory-only templates: they never run with their own token, only as user-created bots.
    standalone: ClassVar[bool] = True
    # Do not acknowledge a webhook until the module's update pipeline has committed its inbox.
    durable_ingress: ClassVar[bool] = False
    # Key under which the bot factory offers this module as a template (None = not a template).
    factory_template: ClassVar[str | None] = None
    # Features when running as a user-created bot. Payments/VIP and referrals stay off there: Stars paid
    # to a user's bot belong to its owner, not to the platform.
    child_features: ClassVar[set[Feature]] = {Feature.ADMIN, Feature.LANG, Feature.BROADCAST}

    async def setup(self, ctx: BotContext) -> None:  # noqa: B027
        """Initialize bot-specific services and attach them to ctx.extras."""
        pass

    def update_pipeline(self, ctx: BotContext) -> BaseMiddleware | None:
        """Optional durable delivery/dedup before user and handler side effects."""
        return None

    def message_pipeline(self, ctx: BotContext) -> BaseMiddleware | None:
        """Optional group protection before core guards/routers, for messages and edits."""
        return None

    def priority_routers(self, ctx: BotContext) -> list[Router]:
        """Narrow context-specific routes that must precede generic core routes."""
        return []

    def required_update_types(self) -> frozenset[str]:
        """Explicit subscriptions for events whose delivery cannot be inferred from handlers."""
        return frozenset()

    @abstractmethod
    def routers(self, ctx: BotContext) -> list[Router]:
        """Return fresh Router instances for this bot's specific handlers."""
        ...

    async def on_child_stopping(self, ctx: BotContext, reason: str) -> str | None:
        """Scoped owned-state cleanup before pause/delete; return a sanitized residual code."""
        return None

    def commands(self) -> list[CommandSpec]:
        """List of standard bot commands registered in Telegram Bot API."""
        return []

    def admin_sections(self) -> list[AdminSection]:
        """Extra tabs and routers to display in the bot's /admin panel."""
        return []

    def processes(self) -> dict[str, Callable[[BotContext], Awaitable[None]]]:
        """Named background processes (e.g. workers)."""
        return {}

    def scheduled_jobs(self) -> list[ScheduledJob]:
        """Periodic background tasks managed by the central scheduler."""
        return []

    def factory_jobs(self) -> list[FactoryJob]:
        """Periodic tasks covering every user-created bot of this template (see :class:`FactoryJob`)."""
        return []

    async def stats(self, ctx: BotContext) -> list[StatLine]:
        """Bot-specific metrics to include in /admin stats and daily reports."""
        return []

    def throttle_rate(self, user: BotUser) -> float:
        """Per-request throttle window in seconds (default: 0.4s for VIP, 1.0s for free)."""
        return 0.4 if user.is_vip() else 1.0

    def throttle_exempt(self, event: TelegramObject) -> bool:
        """Allow bounded collection workflows to accept individual items sent in a burst."""
        return False

    async def reset_user_limits(self, ctx: BotContext, user_id: int) -> bool:
        """Admin "reset limits" button: clear the user's bot-specific quotas. Return False if unsupported."""
        return False

    async def on_force_sub_passed(self, ctx: BotContext, user: BotUser, payload: dict[str, Any], chat_id: int) -> None:
        """Called after a user joined the required channels; ``payload`` is what the bot saved when it showed
        the join prompt (see ``core.routers.forcesub.require_subscription``). Use it to finish the request."""
        return None

    async def vip_info(self, ctx: BotContext) -> dict[str, Any]:
        """Variables for the VIP screen's ``vip-perks`` / ``vip-status-none`` messages (real plan limits)."""
        return {}
