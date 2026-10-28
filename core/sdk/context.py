"""Bot execution context bundling per-bot infrastructure, models, services and state."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from aiogram import Bot
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.config import BaseBotEnv, PlatformConfig
from core.i18n import Translator
from core.redis import KeySpace

if TYPE_CHECKING:
    from core.ai.client import AIClient
    from core.sdk.features import Feature
    from core.sdk.module import BotModule
    from core.services.audit import AuditService
    from core.services.broadcast import BroadcastService
    from core.services.forcesub import ForceSubService
    from core.services.groups import GroupService
    from core.services.payments import PaymentService
    from core.services.settings import SettingsService
    from core.services.stats import StatsService
    from core.services.subscriptions import SubscriptionService
    from core.services.users import UserService


@dataclass(slots=True, frozen=True)
class ChildInfo:
    """Set on the context of a bot created through the bot factory."""

    owner_id: int
    template: str
    factory_username: str
    branding: bool = True


@dataclass(slots=True)
class BotContext:
    module: BotModule
    slug: str
    bot_id: int
    bot: Bot
    platform: PlatformConfig
    env: BaseBotEnv
    sm: async_sessionmaker[AsyncSession]
    redis: Redis
    keys: KeySpace
    translator: Translator

    # Core services (bot-scoped)
    settings: SettingsService
    users: UserService
    subs: SubscriptionService
    payments: PaymentService
    stats: StatsService
    broadcast: BroadcastService
    groups: GroupService
    audit: AuditService
    forcesub: ForceSubService

    # Bot-specific extras populated in module.setup()
    extras: dict[str, Any] = field(default_factory=dict)

    # Telegram @username of the bot (resolved once at startup via get_me)
    username: str = ""

    # Evictable cache Redis (may be the same connection as `redis`)
    cache_redis: Redis | None = None

    # Set when the process is shutting down; long-running processes/jobs should wind down when it fires.
    shutdown: asyncio.Event = field(default_factory=asyncio.Event)

    # Metered AI client (None when no provider is configured). See core/ai.
    ai: AIClient | None = None

    # User-created bot hosted by the factory (None for the platform's own bots).
    child: ChildInfo | None = None
    # Feature set in effect: the module's own, or its reduced ``child_features`` for user-created bots.
    feature_set: set[Feature] | None = None

    @property
    def features(self) -> set[Feature]:
        return self.feature_set if self.feature_set is not None else self.module.features

    @property
    def is_child(self) -> bool:
        return self.child is not None

    @property
    def metric_name(self) -> str:
        """Metrics label: thousands of user-created bots are grouped per template to keep cardinality low."""
        return f"factory_{self.child.template}" if self.child else self.slug

    def is_admin(self, user_id: int) -> bool:
        """Check if user_id has admin rights in this bot or across the entire platform."""
        return user_id in self.env.admin_ids or self.platform.is_super_admin(user_id)

    @property
    def sessionmaker(self) -> async_sessionmaker[AsyncSession]:
        return self.sm

    def is_super_admin(self, user_id: int) -> bool:
        """Check if user_id is a platform super-admin."""
        return self.platform.is_super_admin(user_id)
