"""Actual typed blocklist evidence and observed-profile checks with bounded matching."""

from __future__ import annotations

from datetime import timedelta

from aiogram.types import Chat, ChatMemberUpdated, Message, User

from bots.groupguard import actions, authz, perms
from bots.groupguard.blocklist_matcher import literal_match, match, normalize
from bots.groupguard.blocklist_types import LOOKALIKE, Entry
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.contracts import Actor, Right, StepResult
from bots.groupguard.lock_runtime import emoji_packs
from bots.groupguard.locks import detect
from core.sdk.context import BotContext
from core.ui.text import esc


def entries(cfg: ChatConfig) -> list[Entry]:
    return [Entry.model_validate(entry) for entry in cfg.blocklist_entries]


def identities(message: Message, kind: str) -> list[str]:
    return list(
        dict.fromkeys(
            value
            for item in detect(message)
            if item.kind == kind or (kind == "forward" and item.kind.startswith("forward"))
            for value in (item.value, item.identity)
            if value
        )
    )


def profile_matches(entry: Entry, user: User) -> bool:
    value = user.full_name if entry.kind == "name" else user.username or ""
    pattern = entry.pattern.lstrip("@") if entry.kind == "username" else entry.pattern
    return bool(value) and match(value, pattern, "exact")


def message_text(message: Message) -> str:
    text = message.text or message.caption or ""
    if message.rich_message:
        pending: list[object] = [message.rich_message.model_dump(mode="json", exclude_none=True)]
        strings: list[str] = []
        for _ in range(200):
            if not pending:
                break
            node = pending.pop()
            if isinstance(node, dict):
                if isinstance(node.get("text"), str):
                    strings.append(node["text"][:4096])
                pending.extend(value for value in node.values() if isinstance(value, (dict, list)))
            elif isinstance(node, list):
                pending.extend(node[:100])
        text = (text + "\n" + " ".join(strings)).strip()
    return text[:32768]


async def find(
    ctx: BotContext, message: Message, cfg: ChatConfig, *, profile: User | None = None
) -> Entry | None:
    text = message_text(message)
    packs = None
    for entry in entries(cfg):
        kind, pattern = entry.kind, entry.pattern
        matched = False
        if kind in {"name", "username"}:
            user = profile or (message.from_user if message.sender_chat is None else None)
            matched = user is not None and not user.is_bot and profile_matches(entry, user)
        elif profile is not None:
            continue
        elif kind in {"text", "prefix", "exact", "lookalike"}:
            target = normalize(text).translate(LOOKALIKE) if kind == "lookalike" else text
            expected = normalize(pattern).translate(LOOKALIKE) if kind == "lookalike" else pattern
            matcher = literal_match if entry.legacy else match
            matched = bool(target) and matcher(
                target, expected, kind if kind in {"prefix", "exact"} else "word"
            )
        elif kind == "file":
            names = [
                obj.file_name
                for obj in (message.document, message.audio, message.video, message.animation)
                if obj and obj.file_name
            ]
            matched = any(
                match(name, pattern, "exact")
                or (pattern.startswith(".") and normalize(name).endswith(normalize(pattern)))
                for name in names
            )
        elif kind in {"forward", "inline"}:
            matched = normalize(pattern.lstrip("@")) in {
                normalize(value) for value in identities(message, kind)
            }
        elif kind == "stickerpack":
            matched = (
                message.sticker is not None
                and bool(message.sticker.set_name)
                and normalize(message.sticker.set_name or "") == normalize(pattern)
            )
            if not matched:
                if packs is None:
                    packs = await emoji_packs(ctx, message)
                matched = normalize(pattern) in {normalize(value) for value in packs.values()}
        if matched:
            return entry
    return None


async def apply(
    ctx: BotContext,
    chat: Chat,
    user: User | None,
    actor: Actor,
    cfg: ChatConfig,
    entry: Entry,
    *,
    message_id: int | None = None,
) -> bool:
    if actor.kind != "human" or actor.human_id is None:
        if cfg.blocklist_delete and message_id is not None:
            await actions.delete(ctx, chat.id, message_id)
        return True
    actual = await perms.fresh_rights(ctx, chat.id, actor.human_id)
    if actual is None or actual.is_admin or await ctx.extras["guard"].approval(chat.id, actor.human_id):
        return False
    mode = entry.action or cfg.blocklist_mode
    seconds = entry.duration_seconds if entry.action is not None else cfg.blocklist_duration_seconds
    required: set[Right] = set()
    if cfg.blocklist_delete and message_id is not None:
        required.add("delete_messages")
    if mode != "nothing":
        required.add("restrict_members")
    cap = await authz.internal_authorize(ctx, chat.id, frozenset(required))
    if not cap.allowed:
        await actions.announce(ctx, cfg, chat.id, chat.title, actions.failure("blocklist", cap.code), "")
        return True
    deletion = (
        await actions.delete(ctx, chat.id, message_id)
        if cfg.blocklist_delete and message_id is not None
        else None
    )
    reason = entry.reason or cfg.blocklist_reason or actions.group_t(ctx, cfg)("gg-reason-blocklist")
    silent = (entry.silent and cfg.silent_actions_allowed and cfg.log_chat_id is not None
              and "automated" in cfg.log_categories)
    if mode == "nothing":
        return True
    if mode == "warn":
        from bots.groupguard.handlers.moderation import apply_warn

        result = await apply_warn(
            ctx,
            ctx.extras["guard"],
            cfg,
            chat,
            actor.human_id,
            user.first_name if user else "",
            reason,
            None,
            ancillary_steps=deletion.steps if deletion is not None else (),
            silent=silent,
        )
        if silent and any(step.operation == "log" and not step.completed for step in result.steps):
            await actions.notify(ctx, chat.id, actions.group_t(ctx, cfg)("gg-outcome-ancillary"))
        return True
    if mode not in {"kick", "ban", "tban", "mute", "tmute"} or (mode in {"tban", "tmute"}) != (
        seconds is not None
    ):
        result = actions.failure("blocklist", "invalid_action")
    else:
        result = await actions.punish(
            ctx,
            chat.id,
            actor.human_id,
            mode.removeprefix("t"),
            timedelta(seconds=seconds) if seconds else None,
            source="blocklist",
        )
    if deletion is not None:
        result = result.with_steps(*deletion.steps)
    if entry.silent and not silent:
        result = result.with_steps(StepResult("silence", "skipped", "creator_gate_or_log_unavailable"))
    t = actions.group_t(ctx, cfg)
    result = await actions.announce(
        ctx,
        cfg,
        chat.id,
        chat.title,
        result,
        t(
            "gg-blocklist-action",
            user=actions.mention(actor.human_id, user.first_name if user else ""),
            reason=esc(reason),
        ),
        silent=silent,
    )
    if silent and any(step.operation == "log" and not step.completed for step in result.steps):
        await actions.notify(ctx, chat.id, t("gg-outcome-ancillary"))
    return True


async def enforce(ctx: BotContext, message: Message, actor: Actor, cfg: ChatConfig) -> bool:
    if not cfg.blocklist_entries:
        return False
    entry = await find(ctx, message, cfg)
    if entry is None:
        return False
    current = await ctx.extras["guard"].config(message.chat.id, fresh=True)
    if entry.model_dump() not in current.blocklist_entries:
        return False
    return await apply(
        ctx, message.chat, message.from_user, actor, current, entry, message_id=message.message_id
    )


async def enforce_profile(ctx: BotContext, event: ChatMemberUpdated) -> bool:
    """Check actual observed joining user; no invented message or profile-change subscription."""
    user, chat = event.new_chat_member.user, event.chat
    cfg = await ctx.extras["guard"].config(chat.id, fresh=True)
    for entry in entries(cfg):
        if entry.kind not in {"name", "username"} or not profile_matches(entry, user):
            continue
        actor = Actor(ctx.bot_id, chat.id, "human", human_id=user.id)
        applied = await apply(ctx, chat, user, actor, cfg, entry)
        # Warning/mute can coexist with CAP's independently owned restriction.
        # Delete-only has no join message to delete and does not suppress verification.
        return applied and (entry.action or cfg.blocklist_mode) in {"kick", "ban", "tban"}
    return False
