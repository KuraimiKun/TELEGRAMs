"""Actual scoped reaction removal with semantic replay and explicit attribution limits."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta

from aiogram import Router
from aiogram.types import MessageReactionCountUpdated, MessageReactionUpdated, ReactionTypeCustomEmoji
from sqlalchemy import select, update

from bots.groupguard import actions, authz, locks, perms
from bots.groupguard.contracts import Right, result_of
from bots.groupguard.lock_types import expand
from bots.groupguard.models import GuardEventReceipt
from core.db.base import affected, upsert, utcnow
from core.sdk.context import BotContext
from core.ui.text import esc


def identity(event) -> str:
    raw = event.model_dump(mode="json", exclude_none=True)
    # Display names are not a new reaction intent.
    if "user" in raw:
        raw["user"] = {"id": raw["user"]["id"]}
    if "actor_chat" in raw:
        raw["actor_chat"] = {"id": raw["actor_chat"]["id"]}
    return hashlib.sha256(json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


async def begin(ctx, event, kind):
    scope = dict(bot_id=ctx.bot_id, kind=kind, chat_id=event.chat.id, fingerprint=identity(event))
    async with ctx.sm() as session:
        inserted = await session.execute(
            upsert(session, GuardEventReceipt)
            .values(
                **scope,
                status="processing",
                user_id=event.user.id if isinstance(event, MessageReactionUpdated) and event.user else None,
                actor_chat_id=event.actor_chat.id
                if isinstance(event, MessageReactionUpdated) and event.actor_chat
                else None,
                created_at=utcnow(),
                updated_at=utcnow(),
            )
            .on_conflict_do_nothing()
        )
        await session.commit()
    return scope if affected(inserted) == 1 else None


async def finish(ctx, scope, status, code=None):
    async with ctx.sm() as session:
        await session.execute(
            update(GuardEventReceipt)
            .filter_by(**scope)
            .values(status=status, error_code=code, updated_at=utcnow())
        )
        await session.commit()


async def recover(ctx, limit=100):
    async with ctx.sm() as session:
        stale = list(
            (
                await session.execute(
                    select(GuardEventReceipt)
                    .where(
                        GuardEventReceipt.bot_id == ctx.bot_id,
                        GuardEventReceipt.status == "processing",
                        GuardEventReceipt.updated_at < utcnow() - timedelta(seconds=240),
                    )
                    .limit(limit)
                    .with_for_update(skip_locked=True)
                )
            ).scalars()
        )
        for row in stale:
            row.status = "uncertain"
            row.error_code = "interrupted_processing"
        old = list(
            (
                await session.execute(
                    select(GuardEventReceipt)
                    .where(
                        GuardEventReceipt.bot_id == ctx.bot_id,
                        GuardEventReceipt.created_at < utcnow() - timedelta(days=7),
                    )
                    .order_by(GuardEventReceipt.created_at)
                    .limit(limit)
                )
            ).scalars()
        )
        for row in old:
            await session.delete(row)
        await session.commit()


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_reactions")
    svc = ctx.extras["guard"]

    @router.message_reaction()
    async def changed(event: MessageReactionUpdated):
        if (
            event.chat.type not in {"group", "supergroup"}
            or not event.new_reaction
            or not await authz.active_namespace(ctx)
        ):
            return
        cfg = await svc.config(event.chat.id, fresh=True)
        enabled = set(expand(cfg.locks))
        relevant = enabled & {"reaction", "outsidereaction", "emoji", "emojicustom", "emojigame"}
        if not relevant:
            return
        scope = await begin(ctx, event, "reaction")
        if scope is None:
            return
        result = None
        try:
            user = event.user
            if (user is None) == (event.actor_chat is None):
                await finish(ctx, scope, "failed", "actor_ambiguous_or_unavailable")
                return
            if user and user.id == ctx.bot_id:
                await finish(ctx, scope, "completed", "own_bot_exempt")
                return
            member = await perms.fresh_member(ctx, event.chat.id, user.id) if user else None
            if user and member is None:
                await finish(ctx, scope, "failed", "actor_lookup_failed")
                return
            if (member and perms.member_rights(member).is_admin) or (
                user and await svc.approval(event.chat.id, user.id)
            ):
                await finish(ctx, scope, "completed", "administrator_or_approved")
                return
            outsider = member is not None and (
                member.status in {"left", "kicked"}
                or (member.status == "restricted" and not getattr(member, "is_member", False))
            )
            kinds = set()
            if "reaction" in relevant:
                kinds.add("reaction")
            from bots.groupguard.lock_runtime import discussion

            if "outsidereaction" in relevant and outsider and await discussion(ctx, event.chat.id):
                kinds.add("outsidereaction")
            if "emoji" in relevant and any(r.type == "emoji" for r in event.new_reaction):
                kinds.add("emoji")
            if "emojicustom" in relevant and any(r.type == "custom_emoji" for r in event.new_reaction):
                kinds.add("emojicustom")
            if not kinds:
                await finish(ctx, scope, "completed", "no_violation")
                return
            cfg = await svc.config(event.chat.id, fresh=True)
            if not kinds & set(expand(cfg.locks)):
                await finish(ctx, scope, "completed", "policy_changed")
                return
            from bots.groupguard.lock_runtime import selected

            if event.actor_chat and locks.allowed(
                locks.Evidence("anonchannel", str(event.actor_chat.id), event.actor_chat.username or ""),
                cfg.allowlist,
            ):
                await finish(ctx, scope, "completed", "channel_exception")
                return
            if kinds == {"emojicustom"}:
                from bots.groupguard.lock_runtime import custom_packs

                ids = [
                    r.custom_emoji_id for r in event.new_reaction if isinstance(r, ReactionTypeCustomEmoji)
                ]
                packs = await custom_packs(ctx, ids)
                if ids and all(
                    locks.allowed(locks.Evidence("emojicustom", key), cfg.allowlist, emojipacks=packs)
                    for key in ids
                ):
                    await finish(ctx, scope, "completed", "emoji_pack_exception")
                    return
            policy = selected(cfg, [locks.Evidence(k) for k in sorted(kinds)])
            required: set[Right] = {"delete_messages"}
            if policy.action != "delete":
                required.add("restrict_members")
            cap = await authz.internal_authorize(ctx, event.chat.id, frozenset(required))
            if not cap.allowed:
                await finish(ctx, scope, "failed", cap.code)
                return
            if user is None and event.actor_chat is None:
                await finish(ctx, scope, "failed", "actor_unavailable")
                return
            result = result_of(
                await actions.perform(
                    "reaction_remove",
                    lambda: ctx.bot.delete_message_reaction(
                        event.chat.id,
                        event.message_id,
                        user_id=user.id if user else None,
                        actor_chat_id=event.actor_chat.id if event.actor_chat else None,
                    ),
                )
            )
            if policy.action == "warn" and user and not user.is_bot:
                from bots.groupguard.handlers.moderation import apply_warn

                result = await apply_warn(
                    ctx,
                    svc,
                    cfg,
                    event.chat,
                    user.id,
                    user.first_name,
                    policy.reason or "reaction",
                    None,
                    ancillary_steps=result.steps,
                )
            elif policy.action not in {"delete", "warn"} and user and not user.is_bot:
                punishment = await actions.punish(
                    ctx,
                    event.chat.id,
                    user.id,
                    policy.action.removeprefix("t"),
                    timedelta(seconds=policy.duration_seconds) if policy.duration_seconds else None,
                    source="lock:reaction",
                )
                result = punishment.with_steps(*result.steps)
            status = (
                "completed"
                if result.primary_completed
                else "uncertain"
                if any(s.error_code in {"TelegramNetworkError", "TelegramServerError"} for s in result.steps)
                else "failed"
            )
            code = next((s.error_code for s in result.steps if s.status == "failed"), None)
            await finish(ctx, scope, status, code)
            if not result.primary_completed:
                await actions.log_event(
                    ctx,
                    cfg,
                    event.chat.title,
                    actions.group_t(ctx, cfg)("gg-reaction-failed", code=esc(code or "unknown")),
                    category="automated",
                )
        except BaseException:
            await finish(ctx, scope, "uncertain", "interrupted_processing")
            raise

    @router.message_reaction_count()
    async def anonymous(event: MessageReactionCountUpdated):
        if event.chat.type not in {"group", "supergroup"} or not await authz.active_namespace(ctx):
            return
        cfg = await svc.config(event.chat.id, fresh=True)
        if not (cfg.locked("reaction") or cfg.locked("outsidereaction")):
            return
        scope = await begin(ctx, event, "reaction_count")
        if scope is None:
            return
        # The aggregate update contains no reacting user/chat ID required by the real removal API.
        await finish(ctx, scope, "failed", "anonymous_actor_unavailable")
        await actions.log_event(
            ctx,
            cfg,
            event.chat.title,
            actions.group_t(ctx, cfg)("gg-reaction-anonymous"),
            category="automated",
        )

    return router
