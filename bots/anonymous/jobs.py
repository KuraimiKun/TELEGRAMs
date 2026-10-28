"""Daily question: opted-in users get a fun prompt to share, which brings new anonymous messages."""

from __future__ import annotations

import asyncio

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bots.anonymous.keyboards import share_url
from bots.anonymous.service import AnonService
from bots.anonymous.settings import AnonSettings
from core.db.base import utcnow
from core.log import get_logger
from core.sdk.context import BotContext

log = get_logger(__name__)

PROMPTS = 12  # anon-prompt-1 … anon-prompt-12 in every locale
SEND_RATE = 20  # messages per second


async def daily_prompt(ctx: BotContext) -> None:
    stg = await ctx.settings.get()
    assert isinstance(stg, AnonSettings)
    now = utcnow()
    if not stg.daily_prompt_enabled or now.hour != stg.daily_prompt_hour_utc % 24:
        return
    done_key = ctx.keys("daily_prompt", f"{now:%Y%m%d}")
    if not await ctx.redis.set(done_key, "1", nx=True, ex=2 * 86400):
        return  # already sent today
    svc: AnonService = ctx.extras["anon"]
    question_key = f"anon-prompt-{now.timetuple().tm_yday % PROMPTS + 1}"
    after, sent = 0, 0
    while True:
        batch = await svc.daily_prompt_users(after)
        if not batch:
            break
        for user_id in batch:
            after = user_id
            member = await ctx.users.get(user_id)
            if member is None or member.blocked_bot or member.is_banned:
                continue
            lang = ctx.translator.resolve(member.lang)
            link = await svc.link_for(user_id)
            url = f"https://t.me/{ctx.username}?start={link.code}"
            question = ctx.translator.get(lang, question_key)
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=ctx.translator.get(lang, "anon-btn-share"),
                                                       url=share_url(url, question))]]
            )
            text = ctx.translator.get(lang, "anon-daily-prompt", question=question, link=url)
            try:
                await ctx.bot.send_message(user_id, text, reply_markup=kb)
                sent += 1
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except TelegramForbiddenError:
                await ctx.users.mark_blocked(user_id)
            except Exception as e:
                log.warning("anon_prompt_failed", user=user_id, error=str(e))
            await asyncio.sleep(1 / SEND_RATE)
    log.info("anon_daily_prompt_sent", bot=ctx.slug, sent=sent)
