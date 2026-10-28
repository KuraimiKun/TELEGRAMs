"""Actual post-handler source cleanup and durable owned bot-output deletion at five minutes."""

from __future__ import annotations

import hashlib
from datetime import timedelta

from aiogram.types import Message
from sqlalchemy.exc import SQLAlchemyError

from bots.groupguard import actions, authz, command_metadata, durable, perms
from bots.groupguard.contracts import ActionResult, Actor, StepResult, result_of
from bots.groupguard.models import GuardJob
from core.db.base import utcnow
from core.log import get_logger
from core.sdk.context import BotContext

log = get_logger(__name__)
COMMAND_TYPES = frozenset({"admin", "user", "other"})
BOT_TYPES = frozenset({"action", "filter", "note"})
SERVICE_TYPES = frozenset({"join", "leave", "other", "photo", "pin", "title", "videochat"})


def service_kind(message: Message) -> str | None:
    # Payment first, including malformed mixed fixtures: its handler must run before deletion.
    if message.successful_payment:
        return "other"
    for kind, fields in [
        ("join", ("new_chat_members",)),
        ("leave", ("left_chat_member",)),
        ("photo", ("new_chat_photo", "delete_chat_photo")),
        ("pin", ("pinned_message",)),
        ("title", ("new_chat_title",)),
        (
            "videochat",
            (
                "video_chat_started",
                "video_chat_ended",
                "video_chat_scheduled",
                "video_chat_participants_invited",
            ),
        ),
        (
            "other",
            (
                "proximity_alert_triggered",
                "web_app_data",
                "message_auto_delete_timer_changed",
                "forum_topic_created",
                "forum_topic_closed",
                "forum_topic_reopened",
                "forum_topic_edited",
                "general_forum_topic_hidden",
                "general_forum_topic_unhidden",
                "giveaway_created",
                "giveaway_completed",
                "boost_added",
                "chat_background_set",
                "users_shared",
                "chat_shared",
                "write_access_allowed",
                "connected_website",
                "migrate_to_chat_id",
                "migrate_from_chat_id",
            ),
        ),
    ]:
        if any(getattr(message, field, None) for field in fields):
            return kind
    return None


async def delete_source(ctx: BotContext, message: Message) -> StepResult:
    if message.chat.id < 0:
        result = await actions.delete(ctx, message.chat.id, message.message_id)
        return result.steps[0]
    if (
        message.chat.type == "private"
        and message.from_user is not None
        and not message.from_user.is_bot
        and message.chat.id == message.from_user.id
        and await authz.active_namespace(ctx)
    ):
        return await actions.perform(
            "private_command_delete", lambda: ctx.bot.delete_message(message.chat.id, message.message_id)
        )
    return StepResult("source_delete", "failed", "wrong_scope")


async def after(
    ctx: BotContext,
    message: Message,
    chat_id: int,
    actor: Actor,
    parsed: command_metadata.ParsedCommand | None,
    *,
    other: bool = False,
    already_deleted: bool = False,
) -> None:
    if already_deleted or chat_id >= 0:
        return
    cfg = await ctx.extras["guard"].config(chat_id, fresh=True)
    kind = service_kind(message)
    selected = (
        cfg.service_clean_types
        if cfg.service_clean_types is not None
        else ["join", "leave"]
        if cfg.clean_service
        else []
    )
    if kind is not None:
        if kind in selected and message.chat.id == chat_id:
            step = await delete_source(ctx, message)
            if not step.completed:
                await actions.log_event(
                    ctx,
                    cfg,
                    message.chat.title,
                    actions.group_t(ctx, cfg)("gg-cleanup-failed"),
                    category="other",
                )
        return
    if parsed is None or not cfg.command_clean_types:
        return
    if actor.kind == "bot" and actor.bot_sender_id == ctx.bot_id:
        return
    if other or parsed.name not in command_metadata.REGISTRY:
        category = "other"
    else:
        uid = actor.human_id if actor.kind == "human" else actor.bot_sender_id
        actual = await perms.fresh_rights(ctx, chat_id, uid) if uid is not None else None
        category = (
            "admin" if actor.kind == "anonymous_group" or (actual is not None and actual.is_admin) else "user"
        )
    if category in cfg.command_clean_types:
        step = await delete_source(ctx, message)
        if not step.completed:
            await actions.log_event(
                ctx, cfg, message.chat.title, actions.group_t(ctx, cfg)("gg-cleanup-failed"), category="other"
            )


async def schedule(ctx: BotContext, chat_id: int, message: Message, category: str) -> StepResult:
    if category not in BOT_TYPES or message.chat.id != chat_id or chat_id >= 0:
        return StepResult("bot_clean_schedule", "skipped", "context")
    cfg = await ctx.extras["guard"].config(chat_id, fresh=True)
    if category not in cfg.bot_clean_types:
        return StepResult("bot_clean_schedule", "skipped")
    if message.from_user is None or message.from_user.id != ctx.bot_id or not message.from_user.is_bot:
        return StepResult("bot_clean_schedule", "failed", "missing_owned_receipt")
    identity = hashlib.sha256(f"{ctx.bot_id}:{chat_id}:{message.message_id}:{category}".encode()).hexdigest()
    try:
        await durable.enqueue(
            ctx,
            "bot_message_clean",
            chat_id,
            dedupe_key="clean:" + identity,
            payload={"message_id": message.message_id, "category": category, "bot_id": ctx.bot_id},
            run_at=utcnow() + timedelta(seconds=300),
        )
    except SQLAlchemyError:
        log.exception("gg_bot_clean_schedule_failed", bot_id=ctx.bot_id, chat_id=chat_id)
        return StepResult("bot_clean_schedule", "failed", "state_unavailable")
    return StepResult("bot_clean_schedule", "applied")


async def run(ctx: BotContext, job: GuardJob) -> ActionResult:
    category = job.payload.get("category")
    message_id = job.payload.get("message_id")
    cfg = await ctx.extras["guard"].config(job.chat_id, fresh=True)
    if (
        job.payload.get("bot_id") != ctx.bot_id
        or category not in BOT_TYPES
        or not isinstance(message_id, int)
        or message_id <= 0
        or job.chat_id >= 0
    ):
        return actions.failure("bot_clean", "invalid_receipt")
    if category not in cfg.bot_clean_types:
        return result_of(StepResult("bot_clean", "skipped", "policy_changed"))
    if not await authz.active_namespace(ctx):
        return result_of(StepResult("bot_clean", "skipped", "namespace_inactive"))
    cap = await authz.internal_authorize(ctx, job.chat_id, frozenset({"delete_messages"}))
    if not cap.allowed:
        return actions.failure("bot_clean", cap.code)
    await durable.dispatched(ctx, job)
    return await actions.delete(ctx, job.chat_id, message_id)
