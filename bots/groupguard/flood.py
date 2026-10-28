"""Atomic bounded consecutive/window observations; edits/replays never enter this counter."""

from __future__ import annotations

import json
import time
from datetime import timedelta

from aiogram.types import Message
from redis.exceptions import RedisError

from bots.groupguard import actions, authz, perms
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.contracts import Actor, Right
from core.sdk.context import BotContext

# Two keys share the group hash tag for Redis cluster support. Different timer users remain scoped.
OBSERVE = r"""
local policy = ARGV[1]
local eligible = ARGV[2] == '1'
local who, mid = ARGV[3], ARGV[4]
local now, window = tonumber(ARGV[5]), tonumber(ARGV[6])
local consecutive, timer = tonumber(ARGV[7]), tonumber(ARGV[8])
local hit, ids = false, {}
if consecutive > 0 then
    local raw = redis.call('GET', KEYS[1])
    local state = raw and cjson.decode(raw) or {who='', ids={}, policy=policy}
    if state.policy ~= policy or state.who ~= who or not eligible then state.ids = {} end
    state.who, state.policy = who, policy
    if eligible then
        table.insert(state.ids, tonumber(mid))
        if #state.ids >= consecutive then
            hit, ids, state.ids = true, state.ids, {}
        end
    end
    redis.call('SET', KEYS[1], cjson.encode(state), 'EX', 86400)
else
    redis.call('DEL', KEYS[1])
end
if eligible and timer > 0 then
    redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', now-window)
    redis.call('ZADD', KEYS[2], now, mid)
    redis.call('EXPIRE', KEYS[2], math.ceil(window)+5)
    if redis.call('ZCARD', KEYS[2]) > timer then
        local timed = redis.call('ZRANGE', KEYS[2], 0, -1)
        for _, v in ipairs(timed) do table.insert(ids, tonumber(v)) end
        redis.call('DEL', KEYS[2])
        hit = true
    end
end
if hit then return cjson.encode(ids) end
return ''
"""


def policy(cfg: ChatConfig) -> str:
    return json.dumps(
        [
            cfg.flood_consecutive_count,
            cfg.flood_count,
            cfg.flood_seconds,
            cfg.flood_action,
            cfg.flood_duration_seconds,
            cfg.flood_legacy_duration,
            cfg.action_minutes if cfg.flood_legacy_duration else None,
            cfg.flood_silent,
            cfg.clear_flood,
        ],
        separators=(",", ":"),
    )


def duration(cfg: ChatConfig) -> timedelta | None:
    if cfg.flood_action == "kick":
        return None
    seconds = cfg.flood_duration_seconds
    if seconds is None and cfg.flood_legacy_duration:
        seconds = cfg.action_minutes * 60
    return timedelta(seconds=seconds) if seconds is not None else None


async def observe(
    ctx: BotContext, message: Message, actor: Actor, cfg: ChatConfig, *, eligible: bool
) -> tuple[int, ...] | None:
    if cfg.flood_consecutive_count == 0 and (cfg.flood_count == 0 or not eligible):
        return None
    owner = f"{actor.kind}:{actor.human_id if actor.human_id is not None else actor.sender_chat_id}"
    tag = "{" + str(message.chat.id) + "}"
    stamp = policy(cfg)
    # Changing the timer count/window creates independent new state, unrelated setting changes do not.
    key = ctx.keys("flood_window", tag, actor.human_id or 0, cfg.flood_count, cfg.flood_seconds)
    raw = await ctx.redis.eval(
        OBSERVE,
        2,
        ctx.keys("flood_consecutive", tag),
        key,
        stamp,
        "1" if eligible else "0",
        owner,
        str(message.message_id),
        str(time.time()),
        str(cfg.flood_seconds),
        str(cfg.flood_consecutive_count),
        str(cfg.flood_count),
    )  # type: ignore[misc]
    return tuple(sorted(set(json.loads(raw)))) if raw else None


async def enforce(
    ctx: BotContext, message: Message, actor: Actor, cfg: ChatConfig, *, eligible: bool, edited: bool
) -> bool:
    if edited:
        return False
    try:
        ids = await observe(ctx, message, actor, cfg, eligible=eligible)
    except (RedisError, ValueError, TypeError):
        if eligible:
            await actions.announce(
                ctx,
                cfg,
                message.chat.id,
                message.chat.title,
                actions.failure("flood", "counter_unavailable"),
                "",
            )
        return False
    if ids is None or actor.human_id is None or actor.kind != "human":
        return False
    current = await ctx.extras["guard"].config(message.chat.id, fresh=True)
    if policy(current) != policy(cfg):
        return False

    async def current_target() -> bool:
        latest = await ctx.extras["guard"].config(message.chat.id, fresh=True)
        actual = await perms.fresh_rights(ctx, message.chat.id, actor.human_id or 0)
        return (
            policy(latest) == policy(current)
            and actual is not None
            and not actual.is_admin
            and await ctx.extras["guard"].approval(message.chat.id, actor.human_id or 0) is None
        )

    if not await current_target():
        return False
    required: frozenset[Right] = frozenset({"delete_messages", "restrict_members"})
    cap = await authz.internal_authorize(ctx, message.chat.id, required)
    if not cap.allowed:
        await actions.announce(
            ctx, current, message.chat.id, message.chat.title, actions.failure("flood", cap.code), ""
        )
        return True
    deleting = ids if current.clear_flood else (message.message_id,)
    deleted = (
        await actions.delete_many(ctx, message.chat.id, list(deleting), origin="internal")
        if current.clear_flood
        else await actions.delete(ctx, message.chat.id, message.message_id)
    )
    result = await actions.punish(
        ctx,
        message.chat.id,
        actor.human_id,
        current.flood_action,
        duration(current),
        source="flood",
        dispatch_guard=current_target,
    )
    result = result.with_steps(*deleted.steps)
    silent = (
        current.flood_silent
        and current.silent_actions_allowed
        and current.log_chat_id is not None
        and "automated" in current.log_categories
    )
    t = actions.group_t(ctx, current)
    result = await actions.announce(
        ctx,
        current,
        message.chat.id,
        message.chat.title,
        result,
        t(
            f"gg-flood-{current.flood_action}",
            user=actions.mention(actor.human_id, message.from_user.first_name if message.from_user else ""),
        ),
        silent=silent,
    )
    if silent and any(s.operation == "log" and not s.completed for s in result.steps):
        await actions.notify(ctx, message.chat.id, t("gg-outcome-ancillary"))
    return True
