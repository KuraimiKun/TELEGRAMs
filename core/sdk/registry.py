"""Bot module discovery, contract validation, and context creation."""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass
from pathlib import Path

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.session.base import BaseSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from redis.asyncio import Redis
from redis.asyncio import from_url as redis_from_url
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from core.ai.client import AIClient
from core.ai.registry import build_ai
from core.config import BaseBotEnv, PlatformConfig, get_platform_config, load_bot_env
from core.db.base import create_engine, create_sessionmaker, upsert
from core.db.models import Bot as BotRecord
from core.i18n import Translator
from core.log import get_logger
from core.redis import KeySpace
from core.sdk.context import BotContext, ChildInfo
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

log = get_logger(__name__)


class BotIdentityMismatch(RuntimeError):
    """API/token or SQL slug identity would cross a bot namespace."""

SLUG_RE = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
# Slugs that would collide with platform-level Redis namespaces or URL routes.
RESERVED_SLUGS = frozenset({"platform", "core", "health", "metrics", "webhook", "dl"})
# User-created (factory) bots use the slug ``c<telegram bot id>``.
CHILD_SLUG_RE = re.compile(r"^c\d{3,}$")


def child_slug(bot_id: int) -> str:
    return f"c{bot_id}"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BOTS_DIR = PROJECT_ROOT / "bots"


@dataclass(slots=True)
class SharedInfra:
    """Shared infrastructure pool: database engine, redis connection, and bot API session."""

    engine: AsyncEngine
    sm: async_sessionmaker[AsyncSession]
    redis: Redis
    cache_redis: Redis
    session: BaseSession | None = None
    ai: AIClient | None = None

    @classmethod
    async def create(cls, config: PlatformConfig) -> SharedInfra:
        engine = create_engine(
            config.database_url, pool_size=config.db_pool_size, max_overflow=config.db_max_overflow
        )
        sm = create_sessionmaker(engine)
        redis = redis_from_url(config.redis_url)
        cache_redis = redis_from_url(config.redis_cache_url) if config.redis_cache_url else redis

        session = None
        if config.telegram_api_url:
            server = TelegramAPIServer.from_base(config.telegram_api_url, is_local=config.telegram_api_local_files)
            session = AiohttpSession(api=server)

        return cls(
            engine=engine, sm=sm, redis=redis, cache_redis=cache_redis, session=session, ai=build_ai(config, redis)
        )

    async def close(self) -> None:
        if self.ai is not None:
            await self.ai.close()
        if self.cache_redis is not self.redis:
            await self.cache_redis.aclose()
        await self.redis.aclose()
        await self.engine.dispose()
        if self.session:
            await self.session.close()


def load_bot_models(slug: str) -> None:
    """Import ``bots.<slug>.models`` (if present) so its tables are registered on ``Base.metadata``.

    A missing models module is fine; any *other* import error inside it is a real bug and propagates.
    """
    name = f"bots.{slug}.models"
    try:
        importlib.import_module(name)
    except ModuleNotFoundError as e:
        if e.name != name:
            raise


def bot_packages() -> list[str]:
    """Every bot package under ``bots/`` (directories with an ``__init__.py``), sorted."""
    if not BOTS_DIR.exists():
        return []
    return sorted(
        d.name
        for d in BOTS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith((".", "_")) and (d / "__init__.py").exists()
    )


def discover(
    slugs: list[str] | None = None, platform: PlatformConfig | None = None, *, include_templates: bool = False
) -> list[BotModule]:
    """Discover and validate BotModule instances.

    Factory-only templates (``standalone = False``) have no token of their own, so they are left out of the
    bots a process runs unless ``include_templates`` is set (contract validation, migrations, the factory).
    """
    platform = platform or get_platform_config()
    target_slugs = slugs if slugs is not None else platform.enabled_bots
    if not target_slugs:
        target_slugs = bot_packages()

    modules: list[BotModule] = []
    seen_slugs: set[str] = set()
    seen_prefixes: dict[str, str] = {}
    seen_templates: dict[str, str] = {}

    for slug in target_slugs:
        slug = slug.strip()
        if not slug:
            continue

        if not SLUG_RE.match(slug):
            raise ValueError(f"Invalid bot slug '{slug}'. Must be 2-32 chars, lowercase alphanumeric + underscore.")
        if slug in RESERVED_SLUGS or CHILD_SLUG_RE.match(slug):
            raise ValueError(f"Bot slug '{slug}' is reserved by the platform.")
        if slug in seen_slugs:
            raise ValueError(f"Duplicate bot slug '{slug}' discovered.")

        module_path = f"bots.{slug}"
        try:
            pkg = importlib.import_module(module_path)
        except ImportError as e:
            raise ImportError(f"Failed to import bot package '{module_path}': {e}") from e
        load_bot_models(slug)

        mod = getattr(pkg, "module", None)
        if not mod or not isinstance(mod, BotModule):
            raise TypeError(f"Package '{module_path}' must export a 'module' attribute which is an instance of BotModule.")

        if mod.slug != slug:
            raise ValueError(f"Bot module slug mismatch: directory is '{slug}' but module.slug is '{mod.slug}'.")

        if not mod.table_prefix or not mod.table_prefix.endswith("_"):
            raise ValueError(f"Bot '{slug}' table_prefix must be non-empty and end with an underscore (e.g. '{slug[:3]}_').")

        other = seen_prefixes.get(mod.table_prefix)
        if other:
            raise ValueError(f"Bots '{other}' and '{slug}' share table_prefix '{mod.table_prefix}'.")
        seen_prefixes[mod.table_prefix] = slug

        if mod.factory_template:
            if mod.factory_template in seen_templates:
                raise ValueError(
                    f"Bots '{seen_templates[mod.factory_template]}' and '{slug}' both declare factory_template "
                    f"'{mod.factory_template}'."
                )
            seen_templates[mod.factory_template] = slug
        elif not mod.standalone:
            raise ValueError(f"Bot '{slug}' is not standalone, so it must declare a factory_template.")

        seen_slugs.add(slug)
        if mod.standalone or include_templates:
            modules.append(mod)

    return modules


def factory_templates() -> dict[str, BotModule]:
    """Template key -> module for every bot package that can run as a user-created bot."""
    return {
        m.factory_template: m
        for m in discover(bot_packages(), include_templates=True)
        if m.factory_template
    }


async def build_context(module: BotModule, platform: PlatformConfig, infra: SharedInfra) -> BotContext:
    """Instantiate a standalone bot from its ``<SLUG>_*`` environment."""
    env = load_bot_env(module.env_model, module.slug)
    return await init_context(module, platform, infra, env)


async def init_context(
    module: BotModule,
    platform: PlatformConfig,
    infra: SharedInfra,
    env: BaseBotEnv,
    *,
    child: ChildInfo | None = None,
    session: BaseSession | None = None,
) -> BotContext:
    """Create the Bot, sync its identity with the database and wire bot-scoped services.

    With ``child`` the bot is a user-created (factory) bot: its slug becomes ``c<bot id>``, its owner is
    its only admin (via ``env.admin_ids``) and it runs with the module's ``child_features``.
    """
    shared = session or infra.session
    bot = Bot(
        token=env.token.get_secret_value(),
        session=shared,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        return await _init_context(module, platform, infra, env, bot, child)
    except BaseException:
        if shared is None:
            await bot.session.close()
        raise


async def _init_context(
    module: BotModule,
    platform: PlatformConfig,
    infra: SharedInfra,
    env: BaseBotEnv,
    bot: Bot,
    child: ChildInfo | None,
) -> BotContext:
    me = await bot.get_me()
    if me.id != bot.id:
        raise BotIdentityMismatch("Bot API identity does not match the configured token namespace")
    bot_id = me.id
    is_child = child is not None
    slug = child_slug(bot_id) if is_child else module.slug
    title = f"{module.title} · @{me.username}" if is_child else module.title

    # Sync bot record in database (idempotent: every process of the deployment runs this on start)
    async with infra.sm() as session:
        bound = (await session.execute(select(BotRecord).where(BotRecord.slug == slug))).scalar_one_or_none()
        if bound is not None and bound.id != bot_id:
            raise BotIdentityMismatch(
                f"Bot slug '{slug}' is bound to Telegram bot id {bound.id} in the database, but the configured "
                f"token belongs to bot id {bot_id} (@{me.username}). Refusing to start to avoid mixing two bots' "
                "users, payments and settings. Restore the original token, or migrate the data explicitly."
            )
        await session.execute(
            upsert(session, BotRecord)
            .values(id=bot_id, slug=slug, title=title, username=me.username, active=True)
            .on_conflict_do_update(
                index_elements=[BotRecord.id],
                set_={"slug": slug, "title": title, "username": me.username, "active": True},
            )
        )
        await session.commit()

    keys = KeySpace(slug)
    translator = Translator(module.locales_dir, default=platform.default_lang)

    # Core bot-scoped services
    settings = SettingsService(infra.sm, bot_id=bot_id, model=module.settings_model)
    users = UserService(infra.sm, bot_id=bot_id)
    subs = SubscriptionService(infra.sm, bot_id=bot_id)
    payments = PaymentService(infra.sm, bot_id=bot_id, subs=subs, slug=slug)
    stats = StatsService(infra.sm, bot_id=bot_id)
    broadcast = BroadcastService(
        infra.sm, bot_id=bot_id, redis=infra.redis, keys=keys, metric=f"factory_{child.template}" if child else None
    )
    groups = GroupService(infra.sm, bot_id=bot_id)
    audit = AuditService(infra.sm, bot_id=bot_id)
    forcesub = ForceSubService(bot, groups, infra.redis, keys)

    ctx = BotContext(
        module=module,
        slug=slug,
        bot_id=bot_id,
        bot=bot,
        platform=platform,
        env=env,
        sm=infra.sm,
        redis=infra.redis,
        keys=keys,
        translator=translator,
        settings=settings,
        users=users,
        subs=subs,
        payments=payments,
        stats=stats,
        broadcast=broadcast,
        groups=groups,
        audit=audit,
        forcesub=forcesub,
        username=me.username or "",
        cache_redis=infra.cache_redis,
        ai=infra.ai,
        child=child,
        feature_set=set(module.child_features) if is_child else None,
    )

    # Allow bot module to initialize its own custom services
    await module.setup(ctx)

    # Ensure default VIP plans exist (standalone bots only: user-created bots don't sell VIP)
    if module.default_plans and not is_child:
        await subs.ensure_plans(module.default_plans)

    return ctx
