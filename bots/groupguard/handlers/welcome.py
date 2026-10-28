"""Joins and leaves: CAS check, captcha (button or math), welcome/goodbye, join-request verification."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from aiogram import F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.types import (
    CallbackQuery,
    ChatJoinRequest,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    User,
)

from bots.groupguard import (
    actions,
    allow_refs,
    challenges,
    delivery,
    durable,
    greetings,
    joins,
    perms,
    restrictions,
    verification,
)
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.formatting import render
from bots.groupguard.keyboards import GgCb
from bots.groupguard.models import GuardChallenge
from bots.groupguard.protect import cas_banned, mark_newbie
from bots.groupguard.service import GuardService
from bots.groupguard.settings import GuardSettings
from core.i18n import Translate
from core.sdk.context import BotContext

MAX_TRIES = 3


def due_key(ctx: BotContext) -> str:
    """Pending captchas across the deployment: one ZSET per bot, or one per template for user-created bots."""
    if ctx.child is not None:
        return f"factory_{ctx.child.template}:captcha_due"
    return ctx.keys("captcha_due")


def due_member(ctx: BotContext, chat_id: int, user_id: int) -> str:
    return f"{ctx.bot_id}:{chat_id}:{user_id}" if ctx.child is not None else f"{chat_id}:{user_id}"


def pending_key(ctx: BotContext, chat_id: int, user_id: int) -> str:
    return ctx.keys("captcha", chat_id, user_id)


async def render_welcome(ctx: BotContext, cfg: ChatConfig, t: Translate, chat_id: int, chat_title: str | None,
                         user: User) -> tuple[str, InlineKeyboardMarkup | None]:
    saved = greetings.content(ctx, cfg, "welcome")
    f = await delivery.fillings(ctx, chat_id, user, chat_name=chat_title or "", raw=saved.raw)
    rendered = render(saved.raw, f, format=saved.format, kind="welcome")
    kb, _ = delivery.keyboard(ctx, chat_id, rendered)
    return rendered.html + greetings.suffix(ctx, cfg), kb


def captcha_markup(t: Translate, cfg: ChatConfig, chat_id: int, user_id: int) -> tuple[str, InlineKeyboardMarkup, int]:
    """(question, keyboard, correct answer)."""
    if cfg.captcha == "math":
        a, b = random.randint(1, 9), random.randint(1, 9)
        answer = a + b
        options = {answer, *random.sample([n for n in range(2, 19) if n != answer], 3)}
        buttons = [
            InlineKeyboardButton(text=str(n), callback_data=GgCb(action="cap", chat=chat_id, user=user_id, arg=str(n)).pack())
            for n in sorted(options)
        ]
        return t("gg-captcha-math", a=str(a), b=str(b)), InlineKeyboardMarkup(inline_keyboard=[buttons]), answer
    button = InlineKeyboardButton(
        text=t("gg-btn-human"), callback_data=GgCb(action="cap", chat=chat_id, user=user_id, arg="ok").pack()
    )
    return t("gg-captcha-button"), InlineKeyboardMarkup(inline_keyboard=[[button]]), 0


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_welcome")
    svc: GuardService = ctx.extras["guard"]

    async def settings() -> GuardSettings:
        stg = await ctx.settings.get()
        assert isinstance(stg, GuardSettings)
        return stg

    async def welcome(cfg: ChatConfig, chat_id: int, title: str | None, user: User) -> None:
        if not cfg.welcome:
            return
        await greetings.send(ctx, cfg, chat_id, user, title=title)

    # ------------------------------------------------------------------ joins
    @router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
    @joins.once(ctx)
    async def on_join(event: ChatMemberUpdated) -> None:
        chat, user = event.chat, event.new_chat_member.user
        if chat.type not in ("group", "supergroup"):
            return
        await svc.ensure_chat(chat.id, chat.title)
        cfg = await svc.config(chat.id, fresh=True)
        t = actions.group_t(ctx, cfg)

        if user.is_bot:
            adder = event.from_user.id if event.from_user else None
            if cfg.locked("bots") and user.id != ctx.bot_id and not await perms.is_admin(ctx, chat.id, adder):
                result = await actions.punish(ctx, chat.id, user.id, "kick", None)
                if not result.primary_completed:
                    await actions.announce(ctx, cfg, chat.id, chat.title, result, "")
            return
        if event.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR:
            return
        from bots.groupguard import fed_enforcement
        await fed_enforcement.observe(ctx, chat.id, user)
        if await fed_enforcement.passive(ctx, chat.id, user,
                event=f"join:{int(event.date.timestamp())}"):
            return
        mode, reapplied = await restrictions.on_join(ctx, chat.id, user.id)
        if mode in {"ban", "protected"} or (reapplied is not None and not reapplied.primary_completed):
            return
        name = actions.mention(user.id, user.first_name)
        await actions.log_event(ctx, cfg, chat.title, t("gg-log-join", user=name), category="user")

        banned = cfg.cas and await cas_banned(ctx, (await settings()).cas_url, user.id)
        cfg = await svc.config(chat.id, fresh=True)
        if cfg.cas and banned:
            result = await actions.punish(ctx, chat.id, user.id, "ban", None)
            await actions.announce(ctx, cfg, chat.id, chat.title, result, t("gg-cas-banned", user=name))
            return
        from bots.groupguard import raids
        if await raids.joining(ctx, event):
            return
        from bots.groupguard.blocklists import enforce_profile
        if await enforce_profile(ctx, event):
            return
        await mark_newbie(ctx, cfg, chat.id, user.id)

        verified = await ctx.redis.getdel(ctx.keys("verified", chat.id, user.id))
        approved = await svc.approval(chat.id, user.id)
        if cfg.effective_captcha() == "off" or verified is not None or approved is not None or await challenges.verified(ctx, chat.id, user.id):
            await welcome(cfg, chat.id, chat.title, user)
            return
        await verification.issue_group(ctx, cfg, chat.id, user,
            event_identity=f"join:{event.date.isoformat()}:{event.from_user.id}:{event.old_chat_member.status}:{event.new_chat_member.status}",
            before_card=lambda: welcome(cfg, chat.id, chat.title, user))

    @router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
    async def on_leave(event: ChatMemberUpdated) -> None:
        chat, user = event.chat, event.new_chat_member.user
        await ctx.redis.delete(pending_key(ctx, chat.id, user.id))
        await ctx.redis.zrem(due_key(ctx), due_member(ctx, chat.id, user.id))
        actor_admin = event.new_chat_member.status == ChatMemberStatus.KICKED and (
            event.from_user.id == ctx.bot_id or await perms.is_admin(ctx, chat.id, event.from_user.id))
        await challenges.reset(ctx, chat.id, user.id, forget=actor_admin)
        cfg = await svc.config(chat.id, fresh=True)
        if cfg.log_chat_id is not None and "user" in cfg.log_categories and not user.is_bot:
            try:
                count = await ctx.bot.get_chat_member_count(chat.id)
            except TelegramAPIError:
                count = None
            if isinstance(count, int) and count < 50:
                await actions.log_event(ctx, cfg, chat.title, actions.group_t(ctx, cfg)(
                    "gg-log-leave", user=actions.mention(user.id, user.first_name)), category="user")
        if cfg.goodbye and not user.is_bot and event.new_chat_member.status == ChatMemberStatus.LEFT:
            await greetings.send(ctx, cfg, chat.id, user, title=chat.title, kind="goodbye")

    # ------------------------------------------------------------------ captcha answers
    @router.callback_query(GgCb.filter(F.action == "cap"))
    async def on_captcha(query: CallbackQuery, callback_data: GgCb) -> None:
        cfg = await svc.config(callback_data.chat, fresh=True)
        t = actions.group_t(ctx, cfg)
        await verification.answer(ctx, query, callback_data, t)

    # ------------------------------------------------------------------ join requests
    @router.chat_join_request()
    async def on_join_request(request: ChatJoinRequest) -> None:
        from bots.groupguard import fed_enforcement
        if await fed_enforcement.request(ctx, request):
            return
        await allow_refs.remember(ctx,request)
        from bots.groupguard import raids
        if await raids.request(ctx, request):
            return
        cfg = await svc.config(request.chat.id, fresh=True)
        if cfg.effective_captcha() == "off":
            return
        issued = request.date if isinstance(request.date, datetime) else datetime.fromtimestamp(request.date, UTC)
        contact_deadline = issued + timedelta(minutes=5)
        await verification.issue_request(ctx, request, cfg, contact_deadline)

    @router.callback_query(GgCb.filter(F.action == "jr"))
    async def on_join_verified(query: CallbackQuery, callback_data: GgCb) -> None:
        cfg = await svc.config(callback_data.chat, fresh=True)
        t = actions.group_t(ctx, cfg)
        await verification.answer(ctx, query, callback_data, t)

    return router


async def sweep_captchas(ctx: BotContext, limit: int = 200) -> int:
    """SQL deadlines and generations are authoritative; Redis due mirrors cannot accelerate expiry."""
    return await durable.sweep(ctx, min(limit, 200))


async def expire_captcha(ctx: BotContext, chat_id: int, user_id: int) -> bool:
    async with ctx.sm() as session:
        state = await session.get(GuardChallenge, (ctx.bot_id, chat_id, user_id))
    if state is None:
        return False
    result = await challenges.expire(ctx, chat_id, user_id, state.generation)
    return result.primary_completed
