"""Source-aware content grammar and group command handlers."""
from __future__ import annotations

import json
import re
import shlex

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, Message

from bots.groupguard import actions, content_access, delivery, perms
from bots.groupguard.delivery import Content
from bots.groupguard.formatting import (
    ContentError,
    Fillings,
    alternatives,
    message_source,
    parse_controls,
    render,
    validate,
)
from bots.groupguard.operations import operation_for, submit
from bots.groupguard.scope import target_chat
from core.sdk.context import BotContext
from core.ui.text import esc

NOTE = re.compile(r"^[\w-]{1,64}$")


def media_of(message: Message) -> tuple[str | None, str | None]:
    if message.photo:
        return "photo", message.photo[-1].file_id
    for kind in ("video", "animation", "document", "audio", "voice", "sticker", "video_note"):
        obj = getattr(message, kind, None)
        if obj is not None:
            return kind, obj.file_id
    return None, None


def argument_start(message: Message) -> int:
    match = re.match(r"\S+\s*", message.text or message.caption or "")
    return match.end() if match else 0


def content_of(message: Message, start: int = 0) -> Content:
    raw, format = message_source(message, start)
    media, file = media_of(message)
    return Content(raw, format, media, file)


def replied_content(message: Message, start: int) -> Content:
    inline = content_of(message, start)
    if message.reply_to_message is None:
        return inline
    replied = content_of(message.reply_to_message)
    return Content(inline.raw, inline.format, replied.media_kind, replied.file_id) if inline.raw.strip() else replied


def triggers(raw: str, *, note: bool,max_key:int=64,preserve_escapes:bool=False) -> tuple[list[str], int]:
    """Return keys and character offset; commas inside quoted phrases remain literal."""
    pos = 0
    while pos < len(raw) and raw[pos].isspace():
        pos += 1
    grouped = not note and pos < len(raw) and raw[pos] == "("
    if grouped:
        pos += 1
    keys = []
    while pos < len(raw):
        while pos < len(raw) and raw[pos].isspace():
            pos += 1
        if pos == len(raw):
            raise ContentError("trigger_missing")
        quote = raw[pos] if raw[pos] in {"\"", "'"} else None
        if quote:
            pos += 1
            chars = []
            while pos < len(raw) and raw[pos] != quote:
                if raw[pos] == "\\" and pos + 1 < len(raw):
                    if preserve_escapes and raw[pos+1] not in {quote,"\\"}:
                        chars.append("\\")
                    pos += 1
                chars.append(raw[pos])
                pos += 1
            if pos == len(raw):
                raise ContentError("trigger_quote_unclosed")
            key = "".join(chars)
            pos += 1
        else:
            begin = pos
            while pos < len(raw) and not raw[pos].isspace() and (not grouped or raw[pos] not in {",", ")"}):
                pos += 1
            key = raw[begin:pos]
        key = key.lstrip("#") if note else key
        key = key.strip().lower()
        if not key or len(key) > max_key or (note and not NOTE.fullmatch(key)):
            raise ContentError("trigger_invalid")
        keys.append(key)
        if len(keys) > 30:
            raise ContentError("trigger_limit")
        if not grouped:
            if pos < len(raw) and not raw[pos].isspace():
                raise ContentError("trigger_separator_invalid")
            break
        while pos < len(raw) and raw[pos].isspace():
            pos += 1
        if pos < len(raw) and raw[pos] == ")":
            pos += 1
            if pos < len(raw) and not raw[pos].isspace():
                raise ContentError("trigger_separator_invalid")
            break
        if pos >= len(raw) or raw[pos] != ",":
            raise ContentError("trigger_group_unclosed")
        pos += 1
    else:
        raise ContentError("trigger_missing")
    while pos < len(raw) and raw[pos].isspace():
        pos += 1
    return list(dict.fromkeys(keys)), pos


def valid(content: Content, chat_id: int, kind: str) -> None:
    validate(content.raw, Fillings(None, chat_id), format=content.format, kind=kind)
    body, controls = parse_controls(content.raw, kind, format=content.format)
    if not content.file_id:
        for index in range(len(alternatives(body, content.format))):
            value = render(content.raw, Fillings(None, chat_id), format=content.format, kind=kind, alternative=index)
            if not value.html.strip() and not value.buttons:
                raise ContentError("content_empty")
    if controls.mediaspoiler and content.media_kind not in {"photo", "video", "animation"}:
        raise ContentError("media_spoiler_unsupported")


def install(router: Router, ctx: BotContext) -> None:
    svc = ctx.extras["guard"]

    async def patch(message: Message, changes: dict, confirmation="gg-setting-saved"):
        await submit(ctx, message, operation_for(message, "config", patch_json=json.dumps(changes),
            confirmation=confirmation, values_json=json.dumps(dict(setting=(message.text or "").split()[0]))))

    @router.message(Command("rules", "welcome", "goodbye"))
    async def show_or_toggle(message: Message, command: CommandObject):
        from bots.groupguard.handlers.tools import boolean
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        args = (command.args or "").strip().lower()
        kind = command.command
        if kind == "rules":
            sent = await content_access.display(ctx, chat_id=target_chat(message).id, destination=message.chat.id,
                user=message.from_user if message.sender_chat is None else None, kind="rules", reply_id=message.message_id,
                thread_id=message.message_thread_id, sender_chat=message.sender_chat, noformat=args == "noformat")
            if sent is None or not sent.result.primary_completed:
                await message.reply(t("gg-no-rules"))
            return
        value = boolean(args) if args else None
        if value is not None:
            await patch(message, {kind: value})
        elif args and args != "noformat":
            await message.reply(t("gg-setting-invalid"))
        else:
            content = Content.from_dict(getattr(cfg, f"{kind}_content")) if getattr(cfg, f"{kind}_content") else Content(
                cfg.welcome_text or t("gg-welcome-default") if kind == "welcome" else t("gg-goodbye", user="{mention}"))
            if args == "noformat":
                content = Content("<pre>" + esc(content.raw) + "</pre>", "html", content.media_kind, content.file_id)
            f = await delivery.fillings(ctx, target_chat(message).id, message.from_user if message.sender_chat is None else None,
                sender_chat=message.sender_chat, raw=content.raw)
            await delivery.send(ctx, message.chat.id, content, f, kind=kind, reply_id=message.message_id,
                thread_id=message.message_thread_id)

    @router.message(Command("setrules", "setwelcome", "setgoodbye"))
    async def set_content(message: Message, command: CommandObject):
        kind = command.command[3:]
        content = replied_content(message, argument_start(message))
        t = actions.group_t(ctx, await svc.config(target_chat(message).id))
        try:
            valid(content, target_chat(message).id, kind)
            if kind == "rules" and content.file_id:
                raise ContentError("rules_media_invalid")
        except ContentError:
            await message.reply(t("gg-content-invalid"))
            return
        changes = dict(rules=content.raw, rules_format=content.format) if kind == "rules" else {
            f"{kind}_content": content.to_dict(), kind: True}
        await patch(message, changes, "gg-rules-saved" if kind == "rules" else "gg-welcome-saved" if kind == "welcome" else "gg-setting-saved")

    @router.message(Command("resetrules", "resetwelcome", "resetgoodbye"))
    async def reset_content(message: Message, command: CommandObject):
        kind = command.command[5:]
        changes: dict = dict(rules="", rules_format="html") if kind == "rules" else {f"{kind}_content": None}
        if kind == "welcome":
            changes["welcome_text"] = ""
        await patch(message, changes, "gg-rules-cleared" if kind == "rules" else "gg-welcome-reset" if kind == "welcome" else "gg-setting-saved")

    @router.message(Command("privaterules", "privatenotes", "cleanwelcome", "setrulesbutton", "rulesbutton", "resetrulesbutton"))
    async def content_settings(message: Message, command: CommandObject):
        from bots.groupguard.handlers.tools import boolean
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        args = (command.args or "").strip()
        key = {"privaterules": "private_rules", "privatenotes": "private_notes", "cleanwelcome": "clean_welcome"}.get(command.command, "rules_button")
        if not args and command.command != "resetrulesbutton":
            await message.reply(t("gg-setting-value", setting=command.command, value=str(getattr(cfg, key))))
            return
        value = "" if command.command == "resetrulesbutton" else args if key == "rules_button" else boolean(args.lower())
        if value is None or (isinstance(value, str) and (len(value.encode("utf-16-le")) // 2 > 128 or any(ord(c) < 32 for c in value))):
            await message.reply(t("gg-setting-invalid"))
            return
        await patch(message, {key: value})

    @router.message(Command("save", "filter", "filterprefix", "filterexact"))
    async def save(message: Message, command: CommandObject):
        kind = "note" if command.command == "save" else "filter"
        t = actions.group_t(ctx, await svc.config(target_chat(message).id))
        start = argument_start(message)
        try:
            keys, consumed = triggers((message.text or message.caption or "")[start:], note=kind == "note")
            content = replied_content(message, start + consumed)
            valid(content, target_chat(message).id, kind)
            _, controls = parse_controls(content.raw, kind, format=content.format)
            if controls.command:
                from bots.groupguard.command_metadata import REGISTRY
                from bots.groupguard.filter_commands import COMMAND
                from core.runtime.gateway import command_specs
                reserved = {key for key, _ in command_specs(ctx)} | set(REGISTRY)
                if any(not key.startswith("/") or not COMMAND.fullmatch(key[1:]) or key[1:] in reserved for key in keys):
                    raise ContentError("command_invalid")
            op = operation_for(message, "save", item_kind=kind, key=keys[0], keys=tuple(keys),
                text=content.raw, content_format=content.format, media_kind=content.media_kind, file_id=content.file_id,
                options_json=json.dumps(dict(match={"filterprefix": "prefix", "filterexact": "exact"}.get(command.command) or "word")))
        except ValueError:
            await message.reply(t("gg-content-invalid"))
            return
        await submit(ctx, message, op)

    @router.message(Command("clear", "stop", "clearall", "stopall"))
    async def remove(message: Message, command: CommandObject):
        kind = "note" if command.command.startswith("clear") else "filter"
        args = (command.args or "").strip().lstrip("#")
        if command.command.endswith("all"):
            if args != "confirm":
                await message.reply(actions.group_t(ctx, await svc.config(target_chat(message).id))("gg-clearall-confirm", command=command.command))
                return
            await submit(ctx, message, operation_for(message, "removeall", item_kind=kind))
        elif args:
            try:
                keys, consumed = triggers(args, note=False)
                if len(keys) != 1 or consumed != len(args):
                    raise ContentError("trigger_invalid")
            except ContentError:
                await message.reply(actions.group_t(ctx, await svc.config(target_chat(message).id))("gg-content-invalid"))
                return
            await submit(ctx, message, operation_for(message, "remove", item_kind=kind, key=keys[0]))

    @router.message(Command("notes", "filters"))
    async def lists(message: Message, command: CommandObject):
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        kind = "note" if command.command == "notes" else "filter"
        items = await svc.list_items(target_chat(message).id, kind)
        rights = await perms.fresh_rights(ctx, target_chat(message).id, message.from_user.id) if message.from_user and not message.sender_chat else None
        visible = [i for i in items if not i.options.get("admin") or (rights is not None and rights.is_admin)]
        text = "\n".join(("#" if kind == "note" else "") + i.key for i in visible)
        if not visible:
            await message.reply(t(f"gg-{kind}s-empty"))
        elif len(text) > 3000:
            await message.reply_document(BufferedInputFile(text.encode(), filename=f"{kind}s.txt"), caption=t(f"gg-{kind}s-list"))
        else:
            await message.reply(t(f"gg-{kind}s-list") + "\n<pre>" + esc(text) + "</pre>")

    @router.message(Command("get"))
    async def get(message: Message, command: CommandObject):
        args = (command.args or "").strip()
        noformat = args.endswith(" noformat")
        key = args.removesuffix(" noformat") if noformat else args
        await content_access.display(ctx, chat_id=target_chat(message).id, destination=message.chat.id,
            user=message.from_user if not message.sender_chat else None, kind="note", key=key.lstrip("#"),
            reply_id=message.reply_to_message.message_id if message.reply_to_message else message.message_id,
            thread_id=message.message_thread_id, sender_chat=message.sender_chat, noformat=noformat,
            subject_user=message.reply_to_message.from_user if message.reply_to_message and not message.reply_to_message.sender_chat else None,
            subject_chat=message.reply_to_message.sender_chat if message.reply_to_message else None)

    @router.message(Command("button"))
    async def button(message: Message, command: CommandObject):
        args = (command.args or "").strip()
        try:
            from bots.groupguard.formatting import valid_url
            lines = []
            for line in args.splitlines():
                parts = shlex.split(line)
                if len(parts) not in {2, 3} or (len(parts) == 3 and parts[2] != "same"):
                    raise ContentError("button_invalid")
                label, target = parts[:2]
                if any(c in label for c in "[]"):
                    raise ContentError("button_label_invalid")
                if target.startswith("#"):
                    if not NOTE.fullmatch(target[1:]):
                        raise ContentError("note_target_invalid")
                else:
                    valid_url(target)
                    target = target.replace("(", "%28").replace(")", "%29")
                lines.append(f"[{label}](buttonurl://{target}{':same' if len(parts) == 3 else ''})")
            if not lines:
                raise ContentError("button_empty")
            content = Content("\n".join(lines), "rose")
            valid(content, target_chat(message).id, "note")
        except ValueError:
            await message.reply(actions.group_t(ctx, await svc.config(target_chat(message).id))("gg-button-usage"))
            return
        await message.reply("<code>" + esc(content.raw) + "</code>")
        f = await delivery.fillings(ctx, target_chat(message).id, message.from_user)
        await delivery.send(ctx, message.chat.id, content, f, reply_id=message.message_id)
