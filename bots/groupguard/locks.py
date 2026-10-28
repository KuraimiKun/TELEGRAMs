"""Typed bounded lock evidence, independent exceptions and documented policy grammar."""

from __future__ import annotations

import posixpath
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlsplit

from aiogram.types import (
    Message,
    MessageOriginChannel,
    MessageOriginChat,
    MessageOriginUser,
    PaidMediaPhoto,
    PaidMediaVideo,
)
from pydantic import BaseModel, ConfigDict, Field

from bots.groupguard import perms
from bots.groupguard.lock_types import expand

URL = re.compile(r"(?:https?://|tg://|www\.)[^\s<>]+|(?<![\w@])(?:[\w-]+\.)+[a-z]{2,24}(?:/[^\s<>]*)?", re.I)
PHONE = re.compile(r"(?<!\w)\+?\d[\d ()-]{5,}\d(?!\w)")
EMAIL = re.compile(r"(?<![\w.-])[\w.+-]+@[\w.-]+\.[a-z]{2,24}(?!\w)", re.I)
CJK = re.compile(r"[\u2e80-\u9fff\uf900-\ufaff\U00020000-\U0003134f]")
CYRILLIC = re.compile(r"[\u0400-\u052f\u2de0-\u2dff\ua640-\ua69f]")
EMOJI = re.compile(
    r"(?:[0-9#*]\ufe0f?\u20e3|[\U0001f000-\U0001faff\u2600-\u27bf\u2300-\u23ff\u2b00-\u2bff\u00a9\u00ae\u203c\u2049\u2122\u2139])(?:[\ufe0f\u200d\U0001f3fb-\U0001f3ff\U000e0020-\U000e007f]|[\U0001f000-\U0001faff])*",
    re.U,
)
RANK = {"delete": 0, "warn": 1, "kick": 2, "tmute": 3, "mute": 4, "tban": 5, "ban": 6}


@dataclass(frozen=True, slots=True)
class Evidence:
    kind: str
    value: str = ""
    identity: str = ""


class Policy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    action: str = "delete"
    duration_seconds: int | None = Field(default=None, ge=60, le=365 * 86400)
    reason: str = Field(default="", max_length=256)
    silent: bool = False

    def checked(self) -> Policy:
        if self.action not in RANK or (self.action in {"tban", "tmute"}) != (
            self.duration_seconds is not None
        ):
            raise ValueError("lock_action_invalid")
        if self.silent and self.action == "delete":
            raise ValueError("lock_silent_invalid")
        return self


def policy_arguments(raw: str) -> tuple[list[str], Policy]:
    names, separator, detail = raw.partition("###")
    if not separator:
        marker = names.find("{")
        if marker >= 0:
            names, detail = names[:marker], names[marker:]
    types = expand(names.lower().split())
    if not types:
        raise ValueError("lock_type_missing")
    action, duration = "delete", None
    found = re.search(r"\{(delete|warn|kick|ban|mute|tban|tmute|swarn|skick|sban|smute|stban|stmute)(?:\s+([^{}\s]+))?\}\s*$", detail, re.I)
    silent = False
    if found:
        action = found[1].lower()
        if action.startswith("s"):
            action, silent = action[1:], True
        if found[2]:
            parsed = perms.parse_action_duration(found[2], required=True)
            if parsed.kind != "valid" or parsed.value is None:
                raise ValueError("lock_duration_invalid")
            duration = int(parsed.value.total_seconds())
        detail = detail[: found.start()].strip()
    elif "{" in detail or "}" in detail:
        raise ValueError("lock_action_invalid")
    if not separator:
        detail = ""
    return types, Policy(action=action, duration_seconds=duration, reason=detail, silent=silent).checked()


def entity_text(text: str, offset: int, length: int) -> str:
    return text.encode("utf-16-le")[offset * 2 : (offset + length) * 2].decode("utf-16-le", errors="replace")


def url_parts(raw: str):
    candidate = raw.strip().strip("<>\"'.,;!")
    try:
        parsed = urlsplit(candidate if "://" in candidate else "https://" + candidate)
    except ValueError:
        return None
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        return None
    try:
        host = parsed.hostname.rstrip(".").encode("idna").decode().lower()
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            return None
    except (UnicodeError, ValueError):
        return None
    path = parsed.path or "/"
    for _ in range(2):
        decoded = unquote(path)
        if decoded == path:
            break
        path = decoded
    if (
        re.search(r"%[0-9a-fA-F]{2}", path)
        or "\\" in candidate
        or "\\" in path
        or any(ord(c) < 32 for c in path)
    ):
        return None
    path = posixpath.normpath(path)
    return host, path, parsed.query


def url_identity(raw: str) -> tuple[str, str]:
    if raw.lower().startswith("tg://"):
        telegram = urlsplit(raw)
        query = parse_qs(telegram.query)
        if telegram.netloc == "join" and query.get("invite"):
            return "invitelink", raw
        if telegram.netloc == "resolve" and query.get("domain"):
            target = query["domain"][0].lower()
            return ("botlink" if target.endswith("bot") else "invitelink"), target
        return "url", ""
    parts = url_parts(raw)
    if parts is None:
        return "", ""
    host, path, _ = parts
    if host not in {"t.me", "telegram.me", "telegram.dog"}:
        return "url", ""
    target = path.strip("/").split("/", 1)[0]
    if target.startswith("+") or target.lower() == "joinchat":
        return "invitelink", raw
    if target.lower().endswith("bot") or target.lower().endswith("_bot"):
        return "botlink", target.lower()
    return "invitelink", target.lower() if target else ""


def detect(message: Message) -> list[Evidence]:
    text = (message.text or message.caption or "")[:32768]
    evidence: list[Evidence] = []

    def add(kind, value="", identity=""):
        item = Evidence(kind, str(value), str(identity))
        if item not in evidence:
            evidence.append(item)

    if message.rich_message:
        pending: list[object] = [message.rich_message.model_dump(mode="json", exclude_none=True)]
        strings = []
        for _ in range(200):
            if not pending:
                break
            node = pending.pop()
            if isinstance(node, str):
                strings.append(node[:4096])
                continue
            if isinstance(node, list):
                pending.extend(node[:100])
                continue
            if not isinstance(node, dict):
                continue
            kind = node.get("type", "")
            mapped = {
                "photo": "photo",
                "video": "video",
                "audio": "audio",
                "animation": "gif",
                "voice_note": "voice",
                "document": "document",
                "map": "location",
                "buttons": "button",
                "spoiler": "spoiler",
            }.get(kind)
            if mapped:
                add(mapped)
            if node.get("has_spoiler"):
                add("spoiler")
            if kind == "custom_emoji":
                add("emojicustom", node.get("custom_emoji_id", ""))
            elif isinstance(node.get("text"), str):
                strings.append(node["text"][:4096])
            if isinstance(node.get("url"), str):
                target, identity = url_identity(node["url"])
                add("url", node["url"], identity)
                if target in {"invitelink", "botlink"}:
                    add(target, node["url"], identity)
            pending.extend(value for value in node.values() if isinstance(value, (dict, list)))
        text = (text + "\n" + " ".join(strings)).strip()[:32768]

    urls = [match.group() for match in URL.finditer(text)]
    entities = message.entities if message.text is not None else message.caption_entities
    for entity in (entities or [])[:100]:
        value = entity_text(text, entity.offset, entity.length)
        if entity.type in {"url", "text_link"}:
            urls.append(entity.url if entity.type == "text_link" and entity.url else value)
        mapping = {
            "cashtag": "cashtag",
            "bot_command": "command",
            "email": "email",
            "phone_number": "phone",
            "spoiler": "spoiler",
            "custom_emoji": "emojicustom",
        }
        if entity.type in mapping:
            add(mapping[entity.type], entity.custom_emoji_id if entity.type == "custom_emoji" else value)
    for raw in dict.fromkeys(urls):
        kind, identity = url_identity(raw)
        add("url", raw, identity)
        if kind in {"invitelink", "botlink"}:
            add(kind, raw, identity)
    if message.reply_markup:
        for row in message.reply_markup.inline_keyboard[:100]:
            for button in row[:8]:
                if button.url:
                    kind, identity = url_identity(button.url)
                    add("button", button.url, identity)
                    add("url", button.url, identity)
                    if kind in {"invitelink", "botlink"}:
                        add(kind, button.url, identity)
                else:
                    add("button", button.text)
    if text:
        add("text")
        for match in EMAIL.finditer(text):
            add("email", match.group())
        for match in PHONE.finditer(text):
            add("phone", match.group())
        command = re.match(r"^/[a-zA-Z0-9_]{1,32}(?:@[a-zA-Z0-9_]+)?(?:\s|$)", text)
        if command:
            add("command", command.group().strip().split("@", 1)[0].lower())
        if CJK.search(text):
            add("cjk")
        if CYRILLIC.search(text):
            add("cyrillic")
        if any(unicodedata.bidirectional(c) in {"R", "AL", "RLE", "RLO", "RLI"} for c in text):
            add("rtl")
        custom_ranges = [(e.offset, e.offset + e.length) for e in entities or [] if e.type == "custom_emoji"]
        emoji = [
            match
            for match in EMOJI.finditer(text)
            if not any(
                first <= len(text[: match.start()].encode("utf-16-le")) // 2 < last
                for first, last in custom_ranges
            )
        ]
        if emoji:
            add("emoji")
        if (emoji or custom_ranges) and not EMOJI.sub("", text).strip():
            ids = [
                e.custom_emoji_id for e in entities or [] if e.type == "custom_emoji" and e.custom_emoji_id
            ]
            add("emojionly", ",".join(ids) if not emoji else "", "customonly" if ids and not emoji else "")
        run, marks, bases = 0, 0, 0
        for c in text:
            if unicodedata.category(c).startswith("M"):
                run += 1
                marks += 1
            else:
                run = 0
                bases += 1
            if run >= 4 or (marks >= 32 and marks > max(1, bases) * 3):
                add("zalgo")
                break
    fields = {
        "audio": "audio",
        "document": "document",
        "checklist": "checklist",
        "contact": "contact",
        "external_reply": "externalreply",
        "game": "game",
        "animation": "gif",
        "location": "location",
        "venue": "location",
        "photo": "photo",
        "poll": "poll",
        "video": "video",
        "video_note": "videonote",
        "voice": "voice",
        "media_group_id": "album",
    }
    for field, kind in fields.items():
        if getattr(message, field, None):
            add(kind)
    if message.live_photo:
        add("photo")
        add("video")
    if message.paid_media:
        for paid in message.paid_media.paid_media[:100]:
            if isinstance(paid, PaidMediaPhoto):
                add("photo")
            if isinstance(paid, PaidMediaVideo):
                add("video")
    if message.has_media_spoiler:
        add("spoiler")
    if message.dice:
        add("emojigame", message.dice.emoji)
    if message.sticker:
        add("sticker", message.sticker.set_name or "", "stickerpack")
        if message.sticker.is_animated or message.sticker.is_video:
            add("stickeranimated", message.sticker.set_name or "", "stickerpack")
        if message.sticker.premium_animation:
            add("stickerpremium", message.sticker.set_name or "", "stickerpack")
    if message.via_bot:
        add("inline", str(message.via_bot.id), message.via_bot.username or "")
    if message.guest_bot_caller_user or message.guest_bot_caller_chat or message.guest_query_id:
        add("guestbot")
    if message.sender_chat and message.sender_chat.type == "channel":
        add("anonchannel", str(message.sender_chat.id), message.sender_chat.username or "")
    elif message.from_user and message.from_user.is_bot:
        add("bot", str(message.from_user.id), message.from_user.username or "")
    origin = message.forward_origin
    if origin:
        if isinstance(origin, MessageOriginUser):
            add("forward", str(origin.sender_user.id), origin.sender_user.username or "")
            add(
                "forwardbot" if origin.sender_user.is_bot else "forwarduser",
                str(origin.sender_user.id),
                origin.sender_user.username or "",
            )
        elif isinstance(origin, MessageOriginChannel):
            add("forward", str(origin.chat.id), origin.chat.username or "")
            add("forwardchannel", str(origin.chat.id), origin.chat.username or "")
        elif isinstance(origin, MessageOriginChat):
            add("forward", str(origin.sender_chat.id), origin.sender_chat.username or "")
            add("forwardchannel", str(origin.sender_chat.id), origin.sender_chat.username or "")
        elif origin.type == "hidden_user":
            add("forward")
            add("forwarduser")
    if message.story:
        add("forward", str(message.story.chat.id), message.story.chat.username or "")
        add("forwardstory", str(message.story.chat.id), message.story.chat.username or "")
    return evidence


def validate_allowlist(entries: object, *, allow_empty: bool = False) -> None:
    """Validate stored entries without constructing an unrelated message action."""
    if not isinstance(entries, list) or not (0 if allow_empty else 1) <= len(entries) <= 500:
        raise ValueError("allowlist_invalid")
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("kind") not in {
                "url", "invite", "chat", "bot", "channel", "inline", "forward", "command", "stickerpack", "emojipack"}:
            raise ValueError("allowlist_invalid")
        if set(entry) - {"kind", "value", "host", "path"} or any(
                not isinstance(value, str) or len(value) > 2048 or any(ord(c) < 32 for c in value)
                for value in entry.values()):
            raise ValueError("allowlist_invalid")
        required = "host" if entry["kind"] == "url" else "value"
        if not entry.get(required):
            raise ValueError("allowlist_invalid")


def allow_entry(raw: str) -> dict:
    raw = raw.strip()
    if not raw or len(raw) > 2048 or any(ord(c) < 32 for c in raw):
        raise ValueError("allowlist_invalid")
    prefix, colon, value = raw.partition(":")
    if colon and prefix in {
        "stickerpack",
        "emojipack",
        "forward",
        "inline",
        "channel",
        "chat",
        "bot",
        "command",
    }:
        value = value.strip().lstrip("@")
        if not value or len(value) > 128:
            raise ValueError("allowlist_identity_invalid")
        return dict(kind=prefix, value=value.lower())
    kind, _identity = url_identity(raw)
    if kind == "invitelink":
        return dict(kind="invite", value=raw)
    if raw.startswith("@"):
        if not re.fullmatch(r"@[a-zA-Z0-9_]{5,32}", raw):
            raise ValueError("allowlist_identity_invalid")
        return dict(kind="chat", value=raw[1:].lower())
    parts = url_parts(raw)
    if parts is None:
        raise ValueError("allowlist_url_invalid")
    host, path, query = parts
    if query:
        raise ValueError("allowlist_query_requires_exact_invite")
    return dict(kind="url", host=host, path=path)


def allowed(
    item: Evidence,
    entries: list[dict],
    *,
    stickerpack: str | None = None,
    emojipacks: dict[str, str] | None = None,
) -> bool:
    if item.kind == "emojionly" and item.identity == "customonly" and emojipacks:
        approved = {e.get("value", "").lower() for e in entries[:500] if e.get("kind") == "emojipack"}
        return all(emojipacks.get(value, "").lower() in approved for value in item.value.split(","))
    for entry in entries[:500]:
        kind, value = entry.get("kind"), entry.get("value", "")
        if kind == "url" and item.kind in {"url", "button", "botlink"}:
            parts = url_parts(item.value)
            if parts:
                host, path, _ = parts
                base = entry.get("host", "")
                target_path = entry.get("path", "/")
                if (
                    base
                    and (host == base or host.endswith("." + base))
                    and (
                        target_path == "/"
                        or path == target_path
                        or path.startswith(target_path.rstrip("/") + "/")
                    )
                ):
                    return True
        if kind == "invite" and item.kind in {"url", "invitelink", "button"} and item.value == value:
            return True
        if kind in {"chat", "bot", "channel"} and item.kind in {
            "url",
            "botlink",
            "invitelink",
            "button",
            "anonchannel",
            "forwardchannel",
        }:
            identity = item.identity.lower()
            if (identity and identity == value) or item.value == value:
                return True
        if kind == "inline" and item.kind == "inline" and value in {item.value, item.identity.lower()}:
            return True
        if (
            kind == "forward"
            and item.kind.startswith("forward")
            and value in {item.value, item.identity.lower()}
        ):
            return True
        if (
            kind == "command"
            and item.kind == "command"
            and item.value.lstrip("/").lower() == value.lstrip("/")
        ):
            return True
        if (
            kind == "stickerpack"
            and item.kind in {"sticker", "stickeranimated", "stickerpremium"}
            and (item.value.lower() == value or (stickerpack and stickerpack.lower() == value))
        ):
            return True
        if (
            kind == "emojipack"
            and item.kind == "emojicustom"
            and emojipacks
            and emojipacks.get(item.value, "").lower() == value
        ):
            return True
    return False


def violations(message: Message, configured: list[str], entries: list[dict], **packs) -> list[Evidence]:
    kinds = set(expand(configured))
    return [item for item in detect(message) if item.kind in kinds and not allowed(item, entries, **packs)]
