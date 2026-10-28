"""Short-lived cross-worker human approval of an immutable existing operation."""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import time
from typing import Any, Literal

from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from pydantic import ValidationError
from redis.exceptions import RedisError

from bots.groupguard import actions, authz
from bots.groupguard.contracts import ActionResult, Actor
from bots.groupguard.keyboards import GgCb
from bots.groupguard.operations import Operation, denial_text, execute, operation_authorization
from core.sdk.context import BotContext
from core.ui.text import esc

REVIEW_TTL = 120
CLAIM = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
  redis.call('DEL', KEYS[1])
  return 1
end
return 0
"""


def review_key(ctx: BotContext, nonce: str) -> str:
    return ctx.keys("gg", "review", nonce)


async def create_review(ctx: BotContext, actor: Actor, op: Operation) -> str | None:
    cfg = await ctx.extras["guard"].config(op.target_chat_id, fresh=True)
    t = actions.group_t(ctx, cfg)
    if actor.bot_id != ctx.bot_id or actor.source_chat_id != op.source_chat_id or op.source_chat_id != op.target_chat_id:
        return None
    if actor.kind not in {"human", "anonymous_group", "bot"}:
        return None
    if actor.kind == "bot" and not (await operation_authorization(ctx,actor,op)).allowed:
        return None
    caller, bot = op.rights()
    cap = await authz.internal_authorize(ctx, op.target_chat_id, bot)
    if not cap.allowed:
        await actions.notify(ctx, op.target_chat_id, t("gg-auth-denied"))
        return None
    nonce = secrets.token_urlsafe(16)
    payload = op.model_dump_json()
    created = time.time()
    detail = op.reason
    if op.kind == "config":
        detail = op.patch_json
    elif op.kind == "save":
        detail = f"{op.item_kind}: {op.key}\n{op.text or ''}\n{op.media_kind or ''} {op.file_id or ''}"
    elif op.kind in {"pin", "unpin", "purge", "delete"}:
        detail = f"message IDs: {op.message_ids or (op.reply_id,)}; loud={op.loud}"
    elif op.kind == "setlog":
        detail = f"destination: {op.log_chat_id}"
    if op.silent:
        detail += f"; silent; delete messages: {op.reply_id}, {op.message_id}"
    if op.kind not in {"ban","mute","kick","unban","unmute","warn","unwarn","resetwarns","purge","delete","pin","unpin","setlog","config","save"}:
        detail = op.model_dump_json(exclude_defaults=True)
    if op.kind=='fed_quiet':
        detail=t('gg-fed-quiet',value=t('gg-on') if op.loud else t('gg-off'))+'\n'+op.key
    operation_title=t('gg-op-policy_change') if op.kind=='fed_quiet' else t(f'gg-op-{op.kind}')
    summary = t("gg-review-request", operation=operation_title,
                target=esc(str(op.target_id or op.key or op.target_chat_id)),
                details=esc(detail or "—"),
                duration=str(op.duration_seconds) if op.duration_seconds is not None else t("gg-duration-permanent"))
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
        text=t("gg-review-approve"), callback_data=GgCb(action="approve", chat=op.target_chat_id, arg=nonce).pack())]])
    try:
        if len(summary) > 3800:
            # The complete normalized effect is shown in preceding, escaped chunks in the same thread.
            full_detail = detail or "—"
            for start in range(0, len(full_detail), 900):
                notice = await actions.notify(ctx, op.target_chat_id, esc(full_detail[start:start + 900]),
                                              message_thread_id=op.thread_id)
                if not notice.completed:
                    return None
            summary = t("gg-review-request", operation=operation_title,
                        target=esc(str(op.target_id or op.key or op.target_chat_id)),
                        details=t("gg-review-details-above"),
                        duration=str(op.duration_seconds) if op.duration_seconds is not None else t("gg-duration-permanent"))
        sent = await ctx.bot.send_message(op.target_chat_id, summary, reply_markup=kb, message_thread_id=op.thread_id)
        state: dict[str, Any] = dict(version=1, bot_id=ctx.bot_id, source_chat_id=op.source_chat_id, target_chat_id=op.target_chat_id,
                     original_message_id=op.message_id, review_message_id=sent.message_id, thread_id=op.thread_id,
                     owner_id=actor.human_id, original_actor=actor.kind, bot_sender_id=actor.bot_sender_id,
                     created=created, expires=created + REVIEW_TTL,
                     operation=payload, digest=hashlib.sha256(payload.encode()).hexdigest(),
                     caller_rights=sorted(caller), bot_rights=sorted(bot))
        ttl = max(1, int(state["expires"] - time.time()))
        stored = await ctx.redis.set(review_key(ctx, nonce), json.dumps(state, sort_keys=True), ex=ttl, nx=True)
        if not stored:
            await actions.notify(ctx, op.target_chat_id, t("gg-review-unavailable"))
            return None
    except RedisError:
        await actions.notify(ctx, op.target_chat_id, t("gg-review-unavailable"))
        return None
    except Exception as e:
        from aiogram.exceptions import TelegramAPIError
        if isinstance(e, TelegramAPIError):
            return None
        raise
    return nonce


async def approve_review(ctx: BotContext, query: CallbackQuery, nonce: str, *, callback_chat: int | None = None,
                         callback_user: int = 0) -> ActionResult | None:
    t = ctx.translator.bind(query.from_user.language_code)
    msg = query.message
    if (not re.fullmatch(r"[A-Za-z0-9_-]{22}", nonce) or not isinstance(msg, Message)
            or msg.from_user is None or msg.from_user.id != ctx.bot_id or query.from_user.is_bot):
        await query.answer(t("gg-review-expired"), show_alert=True)
        return None
    key = review_key(ctx, nonce)
    try:
        raw = await ctx.redis.get(key)
        state = json.loads(raw) if raw else {}
        if not isinstance(state, dict):
            raise ValueError("state_invalid")
        op = Operation.model_validate_json(state["operation"])
        caller, bot = op.rights()
        if not (state.get("version") == 1 and state["bot_id"] == ctx.bot_id
                and state["source_chat_id"] == op.source_chat_id == msg.chat.id == op.target_chat_id
                and state["target_chat_id"] == op.target_chat_id
                and state["review_message_id"] == msg.message_id
                and state["original_message_id"] == op.message_id
                and state["thread_id"] == msg.message_thread_id == op.thread_id
                and state["owner_id"] in (None, query.from_user.id)
                and state["expires"] > time.time() and state["created"] <= time.time()
                and state["expires"] - state["created"] <= REVIEW_TTL
                and state["digest"] == hashlib.sha256(state["operation"].encode()).hexdigest()
                and state["caller_rights"] == sorted(caller) and state["bot_rights"] == sorted(bot)
                and callback_chat in (None, op.target_chat_id) and callback_user == 0):
            raise ValueError("wrong_scope")
        actor = authz.actor_from_callback(ctx, query)
        authorization = await operation_authorization(ctx, actor, op)
        if not authorization.allowed:
            await query.answer(denial_text(t, authorization), show_alert=True)
            return None
        if state.get("original_actor") == "bot":
            sender_id = state.get("bot_sender_id")
            if not isinstance(sender_id,int):
                raise ValueError("bot_sender_invalid")
            original = Actor(ctx.bot_id,op.source_chat_id,"bot",bot_sender_id=sender_id,
                             message_id=op.message_id,thread_id=op.thread_id)
            if not (await operation_authorization(ctx,original,op)).allowed:
                await query.answer(t("gg-auth-denied"),show_alert=True)
                return None
        claimed = await ctx.redis.execute_command("EVAL", CLAIM, 1, key, raw)
        if claimed != 1:
            await query.answer(t("gg-review-expired"), show_alert=True)
            return None
    except (RedisError, ValueError, TypeError, KeyError, ValidationError):
        await query.answer(t("gg-review-expired"), show_alert=True)
        return None
    # Claim is consumed even if the final fresh check or execution fails.
    source_actor: Literal["human", "anonymous_group", "bot"] = "bot" if state.get("original_actor") == "bot" else "anonymous_group" if state["owner_id"] is None else "human"
    result = await execute(ctx, actor, op, reviewed=True, original_actor=source_actor,
                           original_bot_id=state.get("bot_sender_id"))
    notice = await actions.perform("review_notice", lambda: msg.edit_text(t("gg-review-consumed"), reply_markup=None))
    result = result.with_steps(notice)
    if not notice.completed:
        await ctx.audit.record(query.from_user.id, "gg_review_notice", target=op.target_chat_id, reviewed=True,
                               original_actor="anonymous_group" if state["owner_id"] is None else "human",
                               outcome=result.status, primary_completed=result.primary_completed,
                               error_code=notice.error_code)
    await query.answer(t("gg-review-consumed"))
    return result
