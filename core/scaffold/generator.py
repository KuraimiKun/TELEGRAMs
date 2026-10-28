"""Scaffold a new bot module: ``python -m core new-bot <slug> [--title "My Bot"]``.

The skeleton is a complete, working bot that follows every platform contract (prefixed tables,
localized handlers, core action bookkeeping, a smoke test). Replace the example handler with your own.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from core.sdk.registry import BOTS_DIR, PROJECT_ROOT, RESERVED_SLUGS

SLUG_RE = re.compile(r"^[a-z][a-z0-9_]{1,31}$")

TEMPLATES: dict[str, str] = {
    "__init__.py": """\"\"\"{title} package.\"\"\"

from bots.{slug}.module import {cls}Bot

module = {cls}Bot()

__all__ = ["{cls}Bot", "module"]
""",
    "config.py": """\"\"\"Environment for {title}: variables prefixed with {SLUG}_ (e.g. {SLUG}_TOKEN).\"\"\"

from __future__ import annotations

from core.config import BaseBotEnv


class {cls}Env(BaseBotEnv):
    pass
""",
    "settings.py": """\"\"\"Runtime settings for {title}, editable in /admin -> Settings.\"\"\"

from __future__ import annotations

from core.sdk.module import BaseBotSettings


class {cls}Settings(BaseBotSettings):
    free_daily_limit: int = 20
    vip_daily_limit: int = 500

    @classmethod
    def setting_groups(cls) -> dict[str, list[str]]:
        groups = super().setting_groups()
        groups["limits"] = ["free_daily_limit", "vip_daily_limit"]
        return groups
""",
    "models.py": """\"\"\"Tables owned by {title}. Every table name starts with "{prefix}".\"\"\"

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base, BigInt, TZDateTime, utcnow


class {cls}Event(Base):
    __tablename__ = "{prefix}events"
    __table_args__ = (Index("ix_{prefix}events_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt)
    action: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
""",
    "handlers/__init__.py": "",
    "handlers/main.py": """\"\"\"Example handlers for {title}.\"\"\"

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bots.{slug}.models import {cls}Event
from core.db.models import BotUser
from core.i18n import Translate
from core.sdk.actions import record_user_action
from core.sdk.context import BotContext
from core.ui.text import esc


def build_router(ctx: BotContext) -> Router:
    router = Router(name="{slug}_main")

    @router.message(CommandStart())
    async def cmd_start(message: Message, user: BotUser, t: Translate) -> None:
        name = (message.from_user.first_name if message.from_user else None) or "there"
        await message.answer(t("{slug}-start", name=esc(name)))

    @router.message(Command("help"))
    async def cmd_help(message: Message, t: Translate) -> None:
        await message.answer(t("{slug}-help"))

    @router.message(Command("ping"))
    async def cmd_ping(message: Message, user: BotUser, t: Translate) -> None:
        # The bot's "core action": store it, then let the platform count it (referral rewards etc.).
        async with ctx.sm() as session:
            session.add({cls}Event(user_id=user.user_id, action="ping"))
            await session.commit()
        await record_user_action(ctx, user.user_id)
        await message.answer(t("{slug}-pong"))

    return router
""",
    "locales/en/messages.ftl": """## {title} — English. Shared keys (buttons, VIP, admin...) come from core/locales.
{slug}-start = 👋 Hello, <b>{{ $name }}</b>! Welcome to {title_html}.
{slug}-help = ℹ️ Send /ping to try the example command.
{slug}-pong = 🏓 Pong!
cmd-ping = Example command
""",
    "module.py": """\"\"\"Module definition for {title}.\"\"\"

from __future__ import annotations

from pathlib import Path

from aiogram import Router

from bots.{slug}.config import {cls}Env
from bots.{slug}.handlers import main
from bots.{slug}.settings import {cls}Settings
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.sdk.module import BotModule, CommandSpec, PlanSpec


class {cls}Bot(BotModule):
    slug = "{slug}"
    title = {title_repr}
    table_prefix = "{prefix}"
    features = {{Feature.ADMIN, Feature.LANG, Feature.VIP, Feature.REFERRAL, Feature.BROADCAST, Feature.DAILY_STATS}}
    env_model = {cls}Env
    settings_model = {cls}Settings
    locales_dir = Path(__file__).resolve().parent / "locales"
    default_plans = [PlanSpec(name="1 Month VIP", days=30, stars=100, sort=1)]

    def routers(self, ctx: BotContext) -> list[Router]:
        return [main.build_router(ctx)]

    def commands(self) -> list[CommandSpec]:
        return [CommandSpec("help", "How to use the bot"), CommandSpec("ping", "Example command")]
""",
}

TEST_TEMPLATE = """from core.sdk.registry import discover


def test_{slug}_module_contract():
    [module] = discover(["{slug}"])
    assert module.table_prefix == "{prefix}"
    assert {{c.command for c in module.commands()}} >= {{"help"}}
"""


def create_bot_skeleton(slug: str, title: str | None = None, *, bots_dir: Path = BOTS_DIR) -> Path:
    slug = slug.strip().lower()
    if not SLUG_RE.match(slug):
        raise ValueError(f"Invalid slug '{slug}': 2-32 chars, lowercase letters, digits and '_', starting with a letter.")
    if slug in RESERVED_SLUGS:
        raise ValueError(f"Slug '{slug}' is reserved by the platform.")
    bot_dir = bots_dir / slug
    if bot_dir.exists():
        raise FileExistsError(f"'{bot_dir}' already exists.")

    title = title or slug.replace("_", " ").title()
    values = {
        "slug": slug,
        "SLUG": slug.upper(),
        "title": title.replace('"', "'"),
        "title_repr": repr(title),
        "title_html": html.escape(title, quote=False),
        "cls": "".join(part.capitalize() for part in slug.split("_")),
        "prefix": f"{slug}_",  # unique because slugs are unique
    }
    for rel, template in TEMPLATES.items():
        path = bot_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(template.format(**values), encoding="utf-8")

    tests_root = bots_dir.parent / "tests"
    tests_dir = tests_root / "bots" / slug
    if tests_root.exists() and not tests_dir.exists():
        tests_dir.mkdir(parents=True)
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")
        (tests_dir / f"test_{slug}.py").write_text(TEST_TEMPLATE.format(**values), encoding="utf-8")

    shown = bot_dir.relative_to(PROJECT_ROOT) if bot_dir.is_relative_to(PROJECT_ROOT) else bot_dir
    print(f"\nCreated bot '{slug}' in {shown}. Next steps:")
    print(f"  1. Add {slug.upper()}_TOKEN=<token from @BotFather> to .env (and '{slug}' to ENABLED_BOTS if set).")
    print(f'  2. Create its tables:  python -m core makemigrations -m "add {slug} tables" && python -m core migrate')
    print("  3. Validate:           python -m core bots")
    print("  4. Run locally:        python -m core dev\n")
    return bot_dir
