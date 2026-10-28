"""Platform-level bookkeeping every bot should call when a user completes a "core action"."""

from __future__ import annotations

import contextlib

from core.log import get_logger
from core.sdk.context import BotContext

log = get_logger(__name__)


async def record_user_action(ctx: BotContext, user_id: int) -> None:
    """Count the action, qualify the user's referral and reward the referrer when a milestone is reached.

    Never raises: bookkeeping must not turn a successfully served request into a failure.
    """
    try:
        s = await ctx.settings.get()
        reward_id = await ctx.users.record_action(
            user_id,
            referral_required=s.referral_required,
            referral_enabled=s.referral_enabled,
        )
        if not reward_id:
            return

        until = await ctx.subs.grant_vip(reward_id, s.referral_reward_days, source="referral")
        log.info("referral_reward_granted", bot=ctx.slug, user_id=reward_id, days=s.referral_reward_days)

        parent = await ctx.users.get(reward_id)
        lang = ctx.translator.resolve(parent.lang if parent else None)
        text = ctx.translator.get(
            lang,
            "referral-reward",
            required=s.referral_required,
            days=s.referral_reward_days,
            until=until.strftime("%Y-%m-%d"),
        )
        with contextlib.suppress(Exception):
            await ctx.bot.send_message(chat_id=reward_id, text=text)
    except Exception as e:
        log.exception("record_user_action_failed", bot=ctx.slug, user_id=user_id, error=str(e))
