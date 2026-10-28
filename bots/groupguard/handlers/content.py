"""Existing group content; all writes share the allowlisted operation/authorization path."""
from __future__ import annotations

import json
import re

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bots.groupguard import actions
from bots.groupguard.chatconfig import LOCK_TYPES
from bots.groupguard.models import GuardItem
from bots.groupguard.operations import operation_for, submit
from bots.groupguard.scope import GroupMessages, target_chat
from bots.groupguard.service import GuardService
from core.sdk.context import BotContext

GROUPS = F.chat.type.in_({"group", "supergroup"})
KEY_RE = re.compile(r"^[\w-]{1,64}$")
MEDIA_KINDS = ("photo", "video", "animation", "document", "audio", "voice", "sticker", "video_note")


def media_of(message: Message) -> tuple[str | None, str | None]:
    if message.photo:
        return "photo", message.photo[-1].file_id
    for kind in MEDIA_KINDS[1:]:
        obj = getattr(message, kind, None)
        if obj is not None:
            return kind, obj.file_id
    return None, None


def html_after_args(message: Message, skip_words: int) -> str:
    parts = (message.html_text or "").split(maxsplit=skip_words + 1)
    return parts[skip_words + 1] if len(parts) > skip_words + 1 else ""


async def send_item(ctx: BotContext, message: Message, item: GuardItem) -> None:
    from bots.groupguard.content_access import display
    await display(ctx, chat_id=target_chat(message).id, destination=message.chat.id,
        user=message.from_user if not message.sender_chat else None, kind=item.kind, key=item.key,
        reply_id=message.reply_to_message.message_id if message.reply_to_message else message.message_id,
        thread_id=message.message_thread_id, sender_chat=message.sender_chat,
        subject_user=message.reply_to_message.from_user if message.reply_to_message and not message.reply_to_message.sender_chat else None,
        subject_chat=message.reply_to_message.sender_chat if message.reply_to_message else None)


async def config_operation(ctx: BotContext, message: Message, patch: dict, confirmation: str, **values) -> None:
    await submit(ctx, message, operation_for(message, "config", patch_json=json.dumps(patch, sort_keys=True),
                                            confirmation=confirmation, values_json=json.dumps(values)))


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_content")
    router.message.filter(GroupMessages())
    svc: GuardService = ctx.extras["guard"]

    from bots.groupguard.content_commands import install
    install(router, ctx)

    @router.message(Command("lock", "unlock"))
    async def cmd_lock(message: Message, command: CommandObject) -> None:
        cfg = await svc.config(target_chat(message).id, fresh=True)
        wanted = [w.lower() for w in (command.args or "").split()]
        valid = [w for w in (LOCK_TYPES if "all" in wanted else wanted) if w in LOCK_TYPES]
        if not valid:
            await message.reply(actions.group_t(ctx, cfg)("gg-lock-usage", types=", ".join(LOCK_TYPES)))
            return
        locks = set(cfg.locks) | set(valid) if command.command == "lock" else set(cfg.locks) - set(valid)
        await config_operation(ctx, message, {"locks": sorted(locks)},
                               "gg-locked" if command.command == "lock" else "gg-unlocked", types=", ".join(valid))

    @router.message(Command("locks"))
    async def cmd_locks(message: Message) -> None:
        cfg = await svc.config(target_chat(message).id)
        await message.reply("\n".join([actions.group_t(ctx, cfg)("gg-locks-title")] +
                                     [f"{'🔒' if cfg.locked(k) else '🔓'} {k}" for k in LOCK_TYPES]))

    @router.message(F.text.regexp(r"^#[\w-]{1,64}$"))
    async def hashtag_note(message: Message) -> None:
        item = await svc.get_item(target_chat(message).id, "note", (message.text or "")[1:])
        if item is not None:
            await send_item(ctx, message, item)

    @router.message(F.text | F.caption)
    async def keyword_filters(message: Message) -> None:
        from bots.groupguard import content_access
        from bots.groupguard.formatting import parse_controls
        text = (message.text or message.caption or "").lower()
        if message.from_user is not None and message.from_user.id == ctx.bot_id:
            return
        for item in await svc.filters(target_chat(message).id):
            key = item.key
            mode = item.options.get("match", "word")
            if key.startswith(("prefix:", "exact:")):
                mode, key = key.split(":", 1)
            if key.startswith("/"):
                command, _, _tail = text.partition(" ")
                command = command.split("@", 1)[0]
                matched = command == key
            elif text.startswith("/"):
                continue
            elif mode == "prefix":
                matched = text.startswith(key)
            elif mode == "exact":
                matched = text == key
            else:
                matched = re.search(rf"(?<!\w){re.escape(key)}(?!\w)", text) is not None
            if not matched:
                continue
            from bots.groupguard.delivery import Content
            content = Content.from_dict(dict(raw=item.text or "", format=item.content_format))
            _, controls = parse_controls(content.raw, "filter", format=content.format)
            if message.from_user is not None and message.from_user.is_bot and not controls.allow_bot:
                continue
            subject = message.reply_to_message if controls.replytag and message.reply_to_message else message
            sent = await content_access.display(ctx, chat_id=target_chat(message).id, destination=message.chat.id,
                user=message.from_user if not message.sender_chat else None, kind="filter", key=item.key,
                reply_id=message.message_id, thread_id=message.message_thread_id, sender_chat=message.sender_chat,
                subject_user=subject.from_user if not subject.sender_chat else None,
                subject_chat=subject.sender_chat)
            if sent is not None:
                return

    return router
