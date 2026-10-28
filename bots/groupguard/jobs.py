"""Periodic Group Guard work: expire unsolved captchas and open/close chats for night mode.

Standalone bot: ``scheduled_jobs`` (per bot). User-created copies: ``factory_jobs`` (one sweep for all).
"""

from __future__ import annotations

import contextlib
import uuid
from datetime import timedelta

from aiogram.types import ChatPermissions
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy import and_, func, or_, select, union
from sqlalchemy.exc import SQLAlchemyError

from bots.groupguard import (
    actions,
    authz,
    challenges,
    durable,
    fair_sweeps,
    group_broadcast,
    joins,
    perms,
    reactions,
    repeats,
)
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.contracts import ActionResult, StepResult, result_of
from bots.groupguard.handlers.welcome import sweep_captchas
from bots.groupguard.models import (
    GuardBroadcast,
    GuardChallenge,
    GuardChat,
    GuardInbox,
    GuardJob,
    GuardNight,
    GuardRaid,
    GuardRepeat,
    GuardRestriction,
)
from bots.groupguard.replay import recover_inbox
from bots.groupguard.service import GuardService
from core.db.base import upsert, utcnow
from core.db.models import ChildBot
from core.factory.runtime import ChildRegistry
from core.log import get_logger
from core.sdk.context import BotContext

log = get_logger(__name__)

TEMPLATE = "groupguard"


def in_night(cfg: ChatConfig, utc_hour: int) -> bool:
    hour = (utc_hour + cfg.tz_offset) % 24
    if cfg.night_start == cfg.night_end:
        return False
    if cfg.night_start < cfg.night_end:
        return cfg.night_start <= hour < cfg.night_end
    return hour >= cfg.night_start or hour < cfg.night_end


async def persist_night(ctx: BotContext, chat_id: int, generation: str, status: str,
                        snapshot: dict, closed_permissions: dict, *, window_key: str | None = None) -> None:
    async with ctx.sm() as session:
        values = dict(generation=generation, status=status, snapshot=snapshot,
                      closed_permissions=closed_permissions, updated_at=utcnow())
        if window_key is not None:
            values["window_key"] = window_key
        await session.execute(upsert(session, GuardNight).values(bot_id=ctx.bot_id, chat_id=chat_id,
            **values).on_conflict_do_update(index_elements=["bot_id", "chat_id"], set_=values))
        await session.commit()


def night_window(cfg: ChatConfig) -> str:
    local = utcnow() + timedelta(hours=cfg.tz_offset)
    start = local.replace(hour=cfg.night_start, minute=0, second=0, microsecond=0)
    if local < start:
        start -= timedelta(days=1)
    return f"{start.date()}:{cfg.night_start}:{cfg.night_end}:{cfg.tz_offset}:v{cfg.night_policy_version}"


def permissions_match(actual: dict, expected: dict) -> bool:
    return (all(actual.get(k) == v for k, v in expected.items())
            and not any(v is True for k, v in actual.items() if k not in expected))


async def apply_night(ctx: BotContext, chat_id: int, cfg: ChatConfig, *, force_restore: bool = False) -> ActionResult:
    result = await _apply_night(ctx, chat_id, cfg, force_restore=force_restore)
    # Member restoration acquires a different serialization point, after the chat lock is released.
    await release_night_holds(ctx, chat_id)
    return result


async def _apply_night(ctx: BotContext, chat_id: int, cfg: ChatConfig, *, force_restore: bool = False) -> ActionResult:
    """Durable snapshot/dispatch evidence and restoration only when owned permissions still match."""
    svc: GuardService = ctx.extras["guard"]
    cfg = await svc.config(chat_id, fresh=True)
    night = cfg.night and in_night(cfg, utcnow().hour) and not force_restore
    window = night_window(cfg)
    t = actions.group_t(ctx, cfg)
    key = ctx.keys("night_closed", chat_id)
    async with svc.member_session(chat_id, 0) as (_session, _member):
        async with ctx.sm() as session:
            state = await session.get(GuardNight, (ctx.bot_id, chat_id))
        if state is None:
            # Import a known legacy snapshot; bounded discovery lives in night_job.
            try:
                old = await ctx.redis.get(key)
                if old is not None:
                    snapshot = ChatPermissions.model_validate_json(old).model_dump(exclude_none=True)
                    if not snapshot:
                        return actions.failure("night", "snapshot_invalid")
                    await persist_night(ctx, chat_id, uuid.uuid4().hex, "closed", snapshot,
                                        actions.MUTED.model_dump(exclude_none=True))
                    async with ctx.sm() as session:
                        state = await session.get(GuardNight, (ctx.bot_id, chat_id))
            except (RedisError, ValueError, ValidationError):
                old = None
            except SQLAlchemyError:
                return actions.failure("night", "snapshot_state_failed")
        if night and state is not None and state.status in {"dispatched", "uncertain"}:
            defaults = await actions.default_permissions(ctx, chat_id)
            if defaults.permissions is not None and permissions_match(
                    defaults.permissions.model_dump(exclude_none=True), state.closed_permissions):
                await persist_night(ctx, chat_id, state.generation, "closed", state.snapshot, state.closed_permissions)
            return result_of(StepResult("night_recovery", "skipped", "external_outcome_not_replayed"))
        starting = state is None or state.status in {"restored", "failed"} or (state.status == "superseded" and state.window_key != window)
        if night and (starting or (state is not None and state.status == "prepared")):
            defaults = await actions.default_permissions(ctx, chat_id)
            if defaults.permissions is None:
                return result_of(defaults.step)
            snapshot = defaults.permissions.model_dump(exclude_none=True)
            closed = {key: False for key in snapshot}
            closed_permissions = ChatPermissions.model_validate(closed)
            generation = uuid.uuid4().hex
            if state is not None and state.status == "prepared":
                if not permissions_match(snapshot, state.snapshot):
                    await persist_night(ctx, chat_id, state.generation, "superseded", state.snapshot,
                                        state.closed_permissions, window_key=window)
                    return result_of(StepResult("night_close", "skipped", "permissions_changed"))
                generation, snapshot, closed = state.generation, state.snapshot, state.closed_permissions
                closed_permissions = ChatPermissions.model_validate(closed)
            try:
                # Committed before any permission mutation, surviving process/Redis loss.
                await persist_night(ctx, chat_id, generation, "prepared", snapshot, closed, window_key=window)
            except SQLAlchemyError:
                return actions.failure("night", "snapshot_state_failed")
            cap = await authz.internal_authorize(ctx, chat_id, frozenset({"restrict_members"}))
            current_cfg = await svc.config(chat_id, fresh=True)
            if not cap.allowed or not current_cfg.night or not in_night(current_cfg, utcnow().hour) or night_window(current_cfg) != window:
                await persist_night(ctx, chat_id, generation, "failed", snapshot, closed)
                return actions.failure("night", cap.code if not cap.allowed else "policy_changed")
            await persist_night(ctx, chat_id, generation, "dispatched", snapshot, closed)
            result = result_of(await actions.perform("night_close", lambda: ctx.bot.set_chat_permissions(chat_id, closed_permissions)))
            uncertain = any(s.error_code in {"TelegramNetworkError", "TelegramServerError"} for s in result.steps)
            await persist_night(ctx, chat_id, generation, "closed" if result.primary_completed else "uncertain" if uncertain else "failed", snapshot, closed)
            if result.primary_completed:
                with contextlib.suppress(RedisError):
                    await ctx.redis.set(key, ChatPermissions.model_validate(snapshot).model_dump_json())
            return await actions.announce(ctx, cfg, chat_id, None, result, t("gg-night-start", end=f"{cfg.night_end:02d}:00"))
        if not night and state is not None and state.status in {"prepared", "dispatched", "closed", "uncertain"}:
            defaults = await actions.default_permissions(ctx, chat_id)
            if defaults.permissions is None:
                return result_of(defaults.step)
            actual = defaults.permissions.model_dump(exclude_none=True)
            matches = permissions_match(actual, state.closed_permissions)
            if not matches:
                # Another authorized change wins. Do not overwrite it with an old snapshot.
                await persist_night(ctx, chat_id, state.generation, "superseded", state.snapshot, state.closed_permissions,
                                    window_key=window)
                with contextlib.suppress(RedisError):
                    await ctx.redis.delete(key)
                return result_of(StepResult("night_restore", "skipped", "permissions_changed"))
            if force_restore and ctx.extras.get("owned_maintenance"):
                # Only this owned-snapshot restoration path may use a paused child's token.
                bot = await perms.fresh_rights(ctx, chat_id, ctx.bot_id)
                cap = authz.Authorization(bot is not None and bot.allows("restrict_members"), "owned_restore_denied")
            else:
                cap = await authz.internal_authorize(ctx, chat_id, frozenset({"restrict_members"}))
            if not cap.allowed:
                return actions.failure("night_restore", cap.code)
            permissions = ChatPermissions.model_validate(state.snapshot)
            result = result_of(await actions.perform("night_restore", lambda: ctx.bot.set_chat_permissions(chat_id, permissions)))
            if result.primary_completed:
                await persist_night(ctx, chat_id, state.generation, "restored", state.snapshot, state.closed_permissions)
                with contextlib.suppress(RedisError):
                    await ctx.redis.delete(key)
            return await actions.announce(ctx, cfg, chat_id, None, result, t("gg-night-end"))
        return result_of(StepResult("night", "skipped"))


async def captcha_job(ctx: BotContext) -> None:
    await group_broadcast.tick(ctx)
    await recover_inbox(ctx)
    await challenges.recover_claims(ctx)
    await joins.recover(ctx)
    await reactions.recover(ctx)
    await repeats.tick(ctx)
    await sweep_captchas(ctx)


async def night_job(ctx: BotContext) -> None:
    svc: GuardService = ctx.extras["guard"]
    candidates = union(
        select(GuardChat.chat_id).where(GuardChat.bot_id == ctx.bot_id, GuardChat.night.is_(True), GuardChat.active.is_(True)),
        select(GuardNight.chat_id).where(GuardNight.bot_id == ctx.bot_id,
            GuardNight.status.in_({"prepared", "dispatched", "closed", "uncertain"})),
        select(GuardRestriction.chat_id).where(GuardRestriction.bot_id == ctx.bot_id,
            GuardRestriction.source.startswith("night:"))).subquery()
    pending = await fair_sweeps.batch(ctx.sm, ctx.bot_id, "night_chats", 0,
                                      select(candidates.c.chat_id), candidates.c.chat_id)
    for chat_id in pending:
        await apply_night(ctx, chat_id, await svc.config(chat_id, fresh=True))
    # Legacy Redis discovery is bounded SCAN, never KEYS.
    cursor = int(ctx.extras.get("night_scan_cursor", 0))
    for _ in range(5):
        cursor, keys = await ctx.redis.scan(cursor, match=ctx.keys("night_closed", "*"), count=100)
        for raw in keys:
            try:
                chat_id = int((raw.decode() if isinstance(raw, bytes) else raw).rsplit(":", 1)[1])
                if chat_id >= 0:
                    raise ValueError("not_group")
            except (ValueError, UnicodeError, IndexError):
                log.warning("gg_legacy_night_key_invalid", bot_id=ctx.bot_id)
                continue
            await apply_night(ctx, chat_id, await svc.config(chat_id, fresh=True))
        if cursor == 0:
            break
    ctx.extras["night_scan_cursor"] = cursor


async def release_night_holds(ctx: BotContext, chat_id: int) -> None:
    from bots.groupguard.models import GuardRestriction
    async with ctx.sm() as session:
        state = await session.get(GuardNight, (ctx.bot_id, chat_id))
        if state is not None and state.status in {"prepared", "dispatched", "closed", "uncertain"}:
            return
    query = select(GuardRestriction.user_id).where(GuardRestriction.bot_id == ctx.bot_id,
        GuardRestriction.chat_id == chat_id, GuardRestriction.source.startswith("night:")).distinct()
    ids = await fair_sweeps.batch(ctx.sm, ctx.bot_id, "night_members", chat_id, query, GuardRestriction.user_id)
    if not ids:
        return
    async with ctx.sm() as session:
        rows = list((await session.execute(select(GuardRestriction).where(GuardRestriction.bot_id == ctx.bot_id,
            GuardRestriction.chat_id == chat_id, GuardRestriction.user_id.in_(ids),
            GuardRestriction.source.startswith("night:")).order_by(GuardRestriction.user_id).limit(500))).scalars())
    for row in rows:
        await actions.unmute(ctx, chat_id, row.user_id, source=row.source, generation=row.generation)


# ------------------------------------------------------------------ user-created bots (factory)
async def factory_batch(registry: ChildRegistry, kind: str, candidates) -> list[int]:
    # The lowest actual factory record owns coordination metadata only, never child authority.
    async with registry.infra.sm() as session:
        owner = (await session.execute(select(func.min(ChildBot.factory_bot_id)).where(
            ChildBot.template == TEMPLATE))).scalar_one()
    if owner is None:
        return []
    source = candidates.subquery()
    query = select(source.c.bot_id).join(ChildBot, ChildBot.bot_id == source.c.bot_id).where(
        ChildBot.template == TEMPLATE, ChildBot.status == "active").distinct()
    return await fair_sweeps.batch(registry.infra.sm, int(owner), kind, 0, query, source.c.bot_id)


async def factory_captchas(registry: ChildRegistry) -> None:
    candidates = union(
        select(GuardJob.bot_id).where(GuardJob.status.in_({"pending", "running"})),
        select(GuardInbox.bot_id).where(GuardInbox.status.in_({"received", "processing"})),
        select(GuardRepeat.bot_id).where(GuardRepeat.status == "active", GuardRepeat.next_run <= utcnow()),
        select(GuardBroadcast.bot_id).where(GuardBroadcast.status == "active"))
    for bot_id in await factory_batch(registry, "factory_captchas", candidates):
        runtime = await registry.get(bot_id)
        if runtime is not None and runtime.ctx.child is not None and runtime.ctx.child.template == TEMPLATE:
            await captcha_job(runtime.ctx)


async def factory_night(registry: ChildRegistry) -> None:
    candidates = union(
        select(GuardChat.bot_id).where(GuardChat.night.is_(True), GuardChat.active.is_(True)),
        select(GuardNight.bot_id).where(GuardNight.status.in_({"prepared", "dispatched", "closed", "uncertain"})),
        select(GuardRestriction.bot_id).where(GuardRestriction.source.startswith("night:")))
    for bot_id in await factory_batch(registry, "factory_night", candidates):
        runtime = await registry.get(bot_id)
        if runtime is not None and runtime.ctx.child is not None and runtime.ctx.child.template == TEMPLATE:
            await night_job(runtime.ctx)


async def stop_child(ctx: BotContext, reason: str) -> str | None:
    failures = []
    # Legacy snapshots may predate SQL state. Complete their discovery during explicit shutdown.
    scan_cursor = 0
    while True:
        scan_cursor, keys = await ctx.redis.scan(scan_cursor, match=ctx.keys("night_closed", "*"), count=100)
        for raw in keys:
            try:
                chat_id = int((raw.decode() if isinstance(raw, bytes) else raw).rsplit(":", 1)[1])
                if chat_id >= 0:
                    raise ValueError("not_group")
            except (ValueError, UnicodeError, IndexError):
                log.warning("gg_legacy_night_key_invalid", bot_id=ctx.bot_id)
                continue
            result = await apply_night(ctx, chat_id, await ctx.extras["guard"].config(chat_id), force_restore=True)
            if not result.primary_completed and result.status != "noop":
                failures.append("night_restore_failed")
        if scan_cursor == 0:
            break
    cursor = -(2**63)
    while True:
        async with ctx.sm() as session:
            chats = list((await session.execute(select(GuardNight.chat_id).where(GuardNight.bot_id == ctx.bot_id,
                GuardNight.chat_id > cursor, GuardNight.status.in_({"prepared", "dispatched", "closed", "uncertain"}))
                .order_by(GuardNight.chat_id).limit(100))).scalars())
        if not chats:
            break
        for chat_id in chats:
            result = await apply_night(ctx, chat_id, await ctx.extras["guard"].config(chat_id, fresh=True), force_restore=True)
            if not result.primary_completed and result.status != "noop":
                failures.append("night_restore_failed")
        cursor = chats[-1]
    # Release only this bot's transient verification mutes; never another source or a punitive ban.
    from bots.groupguard.models import GuardRestriction
    cursor_chat, cursor_user = -(2**63), -(2**63)
    while True:
        async with ctx.sm() as session:
            owned = list((await session.execute(select(GuardRestriction).where(GuardRestriction.bot_id == ctx.bot_id,
                GuardRestriction.source == "captcha", GuardRestriction.mode == "mute",
                or_(GuardRestriction.chat_id > cursor_chat, and_(GuardRestriction.chat_id == cursor_chat,
                                                               GuardRestriction.user_id > cursor_user)))
                .order_by(GuardRestriction.chat_id, GuardRestriction.user_id).limit(100))).scalars())
        if not owned:
            break
        for row in owned:
            result = await actions.unmute(ctx, row.chat_id, row.user_id, source="captcha", generation=row.generation)
            if not result.primary_completed:
                failures.append("verification_release_failed")
        cursor_chat, cursor_user = owned[-1].chat_id, owned[-1].user_id
    # Pending challenges cannot act after pause/delete; verified memory and unrelated restrictions remain.
    async with ctx.sm() as session:
        from sqlalchemy import update
        await session.execute(update(GuardChallenge).where(GuardChallenge.bot_id == ctx.bot_id,
            GuardChallenge.status.in_({"pending", "issuing"})).values(status="cancelled"))
        await session.commit()
    await durable.cancel(ctx, kind="captcha_expire")
    await durable.cancel(ctx, kind="repeat_note")
    await durable.cancel(ctx, kind="raid_expire")
    await durable.cancel(ctx, kind="bot_message_clean")
    await durable.cancel(ctx, kind="group_broadcast")
    await durable.cancel(ctx, kind="fed_fanout")
    await durable.cancel(ctx, kind="fed_enforce")
    async with ctx.sm() as session:
        await session.execute(update(GuardRaid).where(GuardRaid.bot_id == ctx.bot_id,
            GuardRaid.status == "active").values(status="inactive", updated_at=utcnow()))
        await session.execute(update(GuardBroadcast).where(GuardBroadcast.bot_id == ctx.bot_id,
            GuardBroadcast.status == "active").values(status="cancelled",updated_at=utcnow()))
        await session.commit()
    return ",".join(sorted(set(failures))) or None
