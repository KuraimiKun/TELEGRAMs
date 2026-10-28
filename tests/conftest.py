"""Shared fixtures: in-memory DB, fake Redis, a recording Bot API session and a full BotContext."""

from __future__ import annotations

import itertools
from collections.abc import AsyncGenerator, AsyncIterator, Callable
from datetime import UTC, datetime
from typing import Any

import fakeredis.aioredis
import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import TelegramMethod
from aiogram.types import (
    CallbackQuery,
    Chat,
    Message,
    PreCheckoutQuery,
    SuccessfulPayment,
    TelegramObject,
    Update,
    User,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.ai.client import AIClient
from core.config import PlatformConfig
from core.db.base import Base
from core.db.models import Bot as BotRecord
from core.i18n import Translator
from core.redis import KeySpace
from core.sdk.context import BotContext, ChildInfo
from core.sdk.module import BotModule
from core.sdk.registry import discover
from core.services.audit import AuditService
from core.services.broadcast import BroadcastService
from core.services.forcesub import ForceSubService
from core.services.groups import GroupService
from core.services.payments import PaymentService
from core.services.settings import SettingsService
from core.services.stats import StatsService
from core.services.subscriptions import SubscriptionService
from core.services.users import UserService

TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
BOT_ID = 123456


def _bind(result: Any, bot: Bot) -> Any:
    """Mount returned objects on the bot, like aiogram's real session does (so `msg.edit_text()` works)."""
    if isinstance(result, TelegramObject):
        return result.as_(bot)
    if isinstance(result, list):
        return [_bind(r, bot) for r in result]
    return result


class RecordingSession(BaseSession):
    """Bot API session that records every call and returns plausible defaults instead of hitting Telegram."""

    def __init__(self) -> None:
        super().__init__()
        self.requests: list[TelegramMethod[Any]] = []
        self.responses: dict[str, Any] = {}
        self._ids = itertools.count(100)
        self.messages: list[Message] = []

    async def make_request(self, bot: Bot, method: TelegramMethod[Any], timeout: int | None = None) -> Any:
        result = await self._respond(method)
        if isinstance(result, Message):
            result = result.model_copy(update={"from_user": User(id=bot.id, is_bot=True, first_name="Bot"),
                                               "message_thread_id": getattr(method, "message_thread_id", None)})
            self.messages.append(result)
        return _bind(result, bot)

    async def _respond(self, method: TelegramMethod[Any]) -> Any:
        self.requests.append(method)
        override = self.responses.get(type(method).__name__)
        if override is not None:
            result = override(method) if callable(override) else override
            if isinstance(result, BaseException):
                raise result
            return result
        if type(method).__name__ in {"EditMessageText", "EditMessageCaption", "EditMessageReplyMarkup"}:
            return True  # Bot API permits Message or True for edits.
        returning = getattr(method, "__returning__", None)
        if returning is bool:
            return True
        if returning is Message:
            chat_id = getattr(method, "chat_id", 1) or 1
            return Message(
                message_id=next(self._ids),
                date=datetime.now(UTC),
                chat=Chat(id=int(chat_id), type="supergroup" if int(chat_id) < 0 else "private"),
                text=getattr(method, "text", None),
            )
        if returning is User:
            return User(id=BOT_ID, is_bot=True, first_name="Test", username="test_bot")
        return None

    async def stream_content(self, *args: Any, **kwargs: Any) -> AsyncGenerator[bytes, None]:
        yield b""

    async def close(self) -> None:
        return None

    def calls(self, name: str) -> list[Any]:
        return [m for m in self.requests if type(m).__name__ == name]


@pytest.fixture
async def sm() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    discover()  # import every bot's models so their tables exist too
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        session.add(BotRecord(id=BOT_ID, slug="socialdownload", title="Social Download", active=True))
        await session.commit()
    yield maker
    await engine.dispose()


@pytest.fixture
async def redis() -> AsyncIterator[fakeredis.aioredis.FakeRedis]:
    r = fakeredis.aioredis.FakeRedis()
    yield r
    await r.aclose()


@pytest.fixture
def module() -> BotModule:
    return discover(["socialdownload"])[0]


@pytest.fixture
def api() -> RecordingSession:
    return RecordingSession()


async def build_test_ctx(
    module: BotModule, sm, redis, api, tmp_path, *, ai: AIClient | None = None, child: ChildInfo | None = None
) -> BotContext:
    """A fully wired BotContext for ``module`` backed by SQLite, fakeredis and the recording Bot API.

    ``child`` builds it as a user-created (factory) bot owned by ``child.owner_id``.
    """
    platform = PlatformConfig(_env_file=None, super_admin_ids=[999], factory_secret_key="test-factory-secret")
    bot = Bot(token=TOKEN, session=api)
    slug = f"c{BOT_ID}" if child else module.slug
    keys = KeySpace(slug)
    subs = SubscriptionService(sm, bot_id=BOT_ID)
    groups = GroupService(sm, bot_id=BOT_ID)
    env_kwargs: dict[str, Any] = {"token": TOKEN}
    if child:
        env_kwargs["admin_ids"] = [child.owner_id]
    if "data_dir" in module.env_model.model_fields:
        env_kwargs["data_dir"] = tmp_path / "data"
    c = BotContext(
        module=module,
        slug=slug,
        bot_id=BOT_ID,
        bot=bot,
        platform=platform,
        env=module.env_model(_env_file=None, **env_kwargs),
        sm=sm,
        redis=redis,
        keys=keys,
        translator=Translator(module.locales_dir),
        settings=SettingsService(sm, bot_id=BOT_ID, model=module.settings_model),
        users=UserService(sm, bot_id=BOT_ID),
        subs=subs,
        payments=PaymentService(sm, bot_id=BOT_ID, subs=subs),
        stats=StatsService(sm, bot_id=BOT_ID),
        broadcast=BroadcastService(sm, BOT_ID, redis, keys=keys),
        groups=groups,
        audit=AuditService(sm, bot_id=BOT_ID),
        forcesub=ForceSubService(bot, groups, redis, keys),
        username="test_bot",
        ai=ai,
        child=child,
        feature_set=set(module.child_features) if child else None,
    )
    await module.setup(c)
    return c


@pytest.fixture
async def ctx(sm, redis, module, api, tmp_path) -> BotContext:
    return await build_test_ctx(module, sm, redis, api, tmp_path)


# --- Update builders -------------------------------------------------------------------------------

_update_ids = itertools.count(1)


def tg_user(user_id: int = 42, lang: str = "en") -> User:
    return User(id=user_id, is_bot=False, first_name="Alice", username="alice", language_code=lang)


def message_update(
    text: str, user_id: int = 42, chat_type: str = "private", chat_id: int | None = None, lang: str = "en"
) -> Update:
    chat = Chat(id=chat_id if chat_id is not None else user_id, type=chat_type)
    msg = Message(
        message_id=next(_update_ids),
        date=datetime.now(UTC),
        chat=chat,
        from_user=tg_user(user_id, lang),
        text=text,
    )
    return Update(update_id=next(_update_ids), message=msg)


def callback_update(data: str, user_id: int = 42) -> Update:
    msg = Message(message_id=1, date=datetime.now(UTC), chat=Chat(id=user_id, type="private"), text="x")
    cq = CallbackQuery(id=str(next(_update_ids)), from_user=tg_user(user_id), chat_instance="ci", data=data, message=msg)
    return Update(update_id=next(_update_ids), callback_query=cq)


def pre_checkout_update(payload: str, amount: int, user_id: int = 42, currency: str = "XTR") -> Update:
    pcq = PreCheckoutQuery(
        id=str(next(_update_ids)),
        from_user=tg_user(user_id),
        currency=currency,
        total_amount=amount,
        invoice_payload=payload,
    )
    return Update(update_id=next(_update_ids), pre_checkout_query=pcq)


def payment_update(payload: str, amount: int, charge_id: str, user_id: int = 42) -> Update:
    sp = SuccessfulPayment(
        currency="XTR",
        total_amount=amount,
        invoice_payload=payload,
        telegram_payment_charge_id=charge_id,
        provider_payment_charge_id="",
    )
    msg = Message(
        message_id=next(_update_ids),
        date=datetime.now(UTC),
        chat=Chat(id=user_id, type="private"),
        from_user=tg_user(user_id),
        successful_payment=sp,
    )
    return Update(update_id=next(_update_ids), message=msg)


@pytest.fixture
def builders() -> dict[str, Callable[..., Update]]:
    return {
        "message": message_update,
        "callback": callback_update,
        "pre_checkout": pre_checkout_update,
        "payment": payment_update,
    }
