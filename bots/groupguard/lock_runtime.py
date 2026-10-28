"""Actual lock effects, capability unions and bounded evidence-specific pack lookups."""

from __future__ import annotations

import json
from datetime import timedelta

from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message
from redis.exceptions import RedisError

from bots.groupguard import actions, allow_refs, authz, locks, perms
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.contracts import Actor, Right, StepResult, result_of
from core.sdk.context import BotContext
from core.ui.text import esc


async def emoji_packs(ctx: BotContext, message: Message) -> dict[str, str]:
    ids = list(
        dict.fromkeys(
            e.custom_emoji_id
            for e in (message.entities or []) + (message.caption_entities or [])
            if e.type == "custom_emoji" and e.custom_emoji_id
        )
    )[:100]
    if message.rich_message:
        ids = list(dict.fromkeys([*ids,*[e.value for e in locks.detect(message) if e.kind == "emojicustom" and e.value]]))[:100]
    if not ids:
        return {}
    return await custom_packs(ctx, ids)


async def custom_packs(ctx: BotContext, ids: list[str]) -> dict[str, str]:
    ids = list(dict.fromkeys(ids))[:100]
    if not ids:
        return {}
    import hashlib

    key = ctx.keys("emoji_packs", hashlib.sha256(json.dumps(ids).encode()).hexdigest())
    try:
        cached = await ctx.redis.get(key)
        if cached is not None:
            return dict(json.loads(cached))
        actual = await ctx.bot.get_custom_emoji_stickers(ids)
        packs = {
            s.custom_emoji_id: s.set_name for s in actual or [] if s.set_name and s.custom_emoji_id in ids
        }
        await ctx.redis.set(key, json.dumps(packs, sort_keys=True), ex=3600)
        return packs
    except (TelegramAPIError, RedisError, ValueError, TypeError):
        return {}  # Lookup failure cannot fabricate a pack exception.


def selected(cfg: ChatConfig, hits: list[locks.Evidence]) -> locks.Policy:
    policies = [locks.Policy.model_validate(cfg.lock_policies.get(e.kind, {})).checked() for e in hits]
    policy = max(policies, key=lambda p: (locks.RANK[p.action], p.duration_seconds or 0))
    if cfg.lock_warns and policy.action == "delete":
        policy = policy.model_copy(update={"action": "warn"})
    return policy


async def discussion(ctx: BotContext, chat_id: int) -> bool:
    key = ctx.keys("linked_discussion", chat_id)
    try:
        cached = await ctx.redis.get(key)
        if cached is not None:
            return cached == b"1"
        chat = await ctx.bot.get_chat(chat_id)
        linked = chat is not None and chat.type == "supergroup" and bool(chat.linked_chat_id)
        await ctx.redis.set(key, "1" if linked else "0", ex=300)
        return linked
    except (TelegramAPIError, RedisError):
        return False


async def enforce(ctx: BotContext, message: Message, actor: Actor, cfg: ChatConfig) -> bool:
    if not cfg.locks:
        return False
    packs = (
        await emoji_packs(ctx, message) if any(e.get("kind") == "emojipack" for e in cfg.allowlist) else {}
    )
    cfg = await ctx.extras["guard"].config(message.chat.id, fresh=True)
    if not cfg.locks:
        return False
    if any(e.get("kind") == "emojipack" for e in cfg.allowlist) and not packs:
        packs = await emoji_packs(ctx, message)
    entries=await allow_refs.exceptions(ctx,message,cfg.allowlist)
    hits = locks.violations(message, cfg.locks, entries, emojipacks=packs)
    if (
        cfg.locked("comment")
        and message.from_user is not None
        and message.sender_chat is None
        and await discussion(ctx, message.chat.id)
    ):
        member = await perms.fresh_member(ctx, message.chat.id, message.from_user.id)
        if member is not None and (
            member.status in {"left", "kicked"}
            or (member.status == "restricted" and not getattr(member, "is_member", False))
        ):
            hits.append(locks.Evidence("comment"))
    if not hits:
        return False
    try:
        policy = selected(cfg, hits)
    except ValueError:
        policy = locks.Policy()
    action = policy.action
    targeted = actor.kind == "human" and message.from_user is not None
    sender_channel = (
        actor.kind == "channel"
        and message.sender_chat is not None
        and message.sender_chat.id != message.chat.id
    )
    required: set[Right] = {"delete_messages"}
    if action != "delete" and (targeted or (sender_channel and action == "ban")):
        required.add("restrict_members")
    cap = await authz.internal_authorize(ctx, message.chat.id, frozenset(required))
    if not cap.allowed:
        await actions.announce(
            ctx, cfg, message.chat.id, message.chat.title, actions.failure("lock", cap.code), ""
        )
        return True
    if targeted and actor.human_id is not None:
        actual = await perms.fresh_rights(ctx, message.chat.id, actor.human_id)
        if actual is None:
            return True  # Unknown attribution cannot become an invented disciplinary target.
        if actual.is_admin:
            return False
    deleted = await actions.delete(ctx, message.chat.id, message.message_id)
    silent = policy.silent and cfg.silent_actions_allowed and cfg.log_chat_id is not None and "automated" in cfg.log_categories
    if action == "delete":
        result = deleted
    elif targeted and actor.human_id is not None and message.from_user is not None:
        reason = policy.reason or actions.group_t(ctx, cfg)(
            "gg-reason-lock", types=", ".join(sorted({e.kind for e in hits}))
        )
        if action == "warn":
            from bots.groupguard.handlers.moderation import apply_warn

            result = await apply_warn(
                ctx,
                ctx.extras["guard"],
                cfg,
                message.chat,
                actor.human_id,
                message.from_user.first_name,
                reason,
                None,
                ancillary_steps=deleted.steps,
                silent=silent,
            )
            if silent and any(step.operation=="log" and not step.completed for step in result.steps):
                await actions.notify(ctx,message.chat.id,actions.group_t(ctx,cfg)("gg-outcome-ancillary"))
            return True
        duration = timedelta(seconds=policy.duration_seconds) if policy.duration_seconds else None
        result = await actions.punish(
            ctx,
            message.chat.id,
            actor.human_id,
            action.removeprefix("t"),
            duration,
            source="lock:" + hits[0].kind,
        )
        result = result.with_steps(*deleted.steps)
    elif sender_channel and action == "ban" and message.sender_chat is not None:
        sender_id = message.sender_chat.id
        result = result_of(
            await actions.perform(
                "sender_chat_ban",
                lambda: ctx.bot.ban_chat_sender_chat(message.chat.id, sender_id),
            )
        )
        result = result.with_steps(*deleted.steps)
    else:
        result = result_of(
            StepResult("lock_action", "failed", "unattributed_or_unsupported_actor_mode")
        ).with_steps(*deleted.steps)
    if action != "delete" or not result.primary_completed:
        t = actions.group_t(ctx, cfg)
        result = await actions.announce(
            ctx,
            cfg,
            message.chat.id,
            message.chat.title,
            result,
            t(
                "gg-lock-applied",
                types=esc(", ".join(sorted({e.kind for e in hits}))),
                reason=esc(policy.reason or "—"),
            ),
            silent=silent,
        )
        if silent and any(step.operation=="log" and not step.completed for step in result.steps):
            await actions.notify(ctx,message.chat.id,t("gg-outcome-ancillary"))
    return True
