"""One bounded renderer for Rose markup, Telegram HTML, fillings, controls and buttons."""
from __future__ import annotations

import html
import random
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Literal
from urllib.parse import urlsplit

from aiogram.types import Chat, Message, MessageEntity, User
from aiogram.utils.text_decorations import html_decoration

from bots.groupguard import perms

Format = Literal["html", "rose"]
MAX_SOURCE = 32768
_BUTTON = re.compile(r"\[([^\]\n]{1,256})\]\(buttonurl://([^\n)]{1,2048})\)")
_TOKEN = re.compile(r"<(/?)(pre|code)\b[^>]*>|`[^`]*`|\\.|\{([^{}\n]{1,256})\}", re.I)
_FILL = re.compile(r"\{(first|last|fullname|username|mention|id|chatname|group|count)\}", re.I)


class ContentError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Controls:
    preview: bool = False
    nonotif: bool = False
    protect: bool = False
    mediaspoiler: bool = False
    admin: bool = False
    user: bool = False
    private: bool = False
    noprivate: bool = False
    allow_bot: bool = False
    replytag: bool = False
    rules: bool = False
    repeat_seconds: int | None = None
    command: bool = False
    command_description: str = ""


@dataclass(frozen=True, slots=True)
class Button:
    label: str
    kind: Literal["url", "note", "rules"]
    target: str
    same_row: bool = False


@dataclass(frozen=True, slots=True)
class Fillings:
    user: User | None
    chat_id: int
    chat_name: str = ""
    sender_chat: Chat | None = None
    count: int | None = None
    rules_label: str = "Rules"

    def plain(self, name: str) -> str:
        user = self.user
        if name in {"chatname", "group"}:
            return self.chat_name or str(self.chat_id)
        if name == "count":
            return str(self.count) if self.count is not None else "—"
        if user is None:
            return (self.sender_chat.title or "—") if self.sender_chat and name in {"first", "fullname", "mention", "username"} else "—"
        return {"first": user.first_name, "last": user.last_name or "", "fullname": user.full_name,
            "username": "@" + user.username if user.username else user.full_name,
            "mention": user.full_name, "id": str(user.id)}.get(name, "")

    def atom(self, name: str) -> str:
        if self.user is not None and (name == "mention" or (name == "username" and not self.user.username)):
            return f'<a href="tg://user?id={self.user.id}">{html.escape(self.user.full_name, quote=False)}</a>'
        return html.escape(self.plain(name), quote=False)


@dataclass(frozen=True, slots=True)
class Rendered:
    html: str
    buttons: tuple[Button, ...]
    controls: Controls
    utf16_length: int


def utf16_size(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def html_size(value: str) -> int:
    class Plain(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts: list[str] = []
        def handle_data(self, data):
            self.parts.append(data)
    parser = Plain()
    parser.feed(value)
    parser.close()
    return utf16_size("".join(parser.parts))


def valid_url(value: str) -> str:
    value = html.unescape(value)
    if len(value) > 2048 or any(c.isspace() or ord(c) < 32 for c in value):
        raise ContentError("url_invalid")
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() in {"http", "https"} and parsed.hostname and not parsed.username and not parsed.password:
            _ = parsed.port
            return value
        if parsed.scheme.lower() == "tg" and parsed.netloc in {"user", "resolve", "join"}:
            return value
    except ValueError:
        pass
    raise ContentError("url_invalid")


def parse_controls(raw: str, kind: str = "note", *, format: Format = "rose") -> tuple[str, Controls]:
    if len(raw) > MAX_SOURCE:
        raise ContentError("content_long")
    values: dict = {}
    common = {"preview", "nonotif", "protect", "mediaspoiler", "rules"}
    allowed = common | ({"admin", "private", "noprivate", "repeat", "repeated"} if kind == "note" else
        {"admin", "user", "allow_bot", "replytag", "command"} if kind == "filter" else set())
    code_depth = 0

    def token(match):
        nonlocal code_depth
        if match.group(2):
            if format == "html":
                code_depth = max(0, code_depth + (-1 if match.group(1) else 1))
            return match.group()
        if match.group(3) is None or code_depth:
            return match.group()
        parts = match.group(3).strip().split(maxsplit=1)
        name = parts[0].lower() if parts else ""
        if name not in allowed:
            return match.group()
        arg = parts[1] if len(parts) > 1 else ""
        if name in {"repeat", "repeated"}:
            duration = perms.parse_duration(arg)
            if duration is None or not 60 <= duration.total_seconds() <= 30 * 86400:
                raise ContentError("repeat_invalid")
            seconds = int(duration.total_seconds())
            if values.get("repeat_seconds", seconds) != seconds:
                raise ContentError("repeat_conflict")
            values["repeat_seconds"] = seconds
        elif name == "command":
            if len(arg) > 256:
                raise ContentError("command_description_long")
            values.update(command=True, command_description=arg)
        elif arg:
            raise ContentError("modifier_invalid")
        else:
            values[name] = True
        return ""

    body = _TOKEN.sub(token, raw)
    if (values.get("admin") and values.get("user")) or (values.get("private") and values.get("noprivate")):
        raise ContentError("modifier_conflict")
    return body, Controls(**values)


def _escaped(value: str, position: int) -> bool:
    count = 0
    while position > 0 and value[position - 1] == "\\":
        count, position = count + 1, position - 1
    return count % 2 == 1


def _code_ranges(raw: str, format: Format) -> list[tuple[int, int]]:
    pattern = r"<(code|pre)\b[^>]*>.*?</\1>" if format == "html" else r"`[^`]*`"
    return [(match.start(), match.end()) for match in re.finditer(pattern, raw, re.I | re.S) if not _escaped(raw, match.start())]


def _buttons(raw: str, format: Format) -> tuple[str, list[Button]]:
    output, buttons, start = [], [], 0
    ranges = _code_ranges(raw, format)
    for match in _BUTTON.finditer(raw):
        if _escaped(raw, match.start()) or any(first <= match.start() < last for first, last in ranges):
            continue
        output.append(raw[start:match.start()])
        label, target = match.groups()
        same = target.endswith(":same")
        target = target[:-5] if same else target
        if target.startswith("#"):
            key = html.unescape(target[1:]).strip()
            if not key or len(key) > 64 or any(ord(c) < 32 for c in key):
                raise ContentError("note_button_invalid")
            button = Button(label, "note", key, same)
        else:
            button = Button(label, "url", valid_url(target), same)
        buttons.append(button)
        start = match.end()
    output.append(raw[start:])
    if len(buttons) > 100:
        raise ContentError("buttons_many")
    return "".join(output), buttons


def _inline(raw: str, depth: int = 0) -> str:
    if depth > 8:
        return html.escape(raw)
    tags = [("__", "u"), ("||", 'span class="tg-spoiler"'), ("*", "b"), ("_", "i"), ("~", "s")]
    output, i = [], 0
    while i < len(raw):
        if raw[i] == "\\" and i + 1 < len(raw):
            output.append("<gg-literal>" + html.escape(raw[i + 1]) + "</gg-literal>")
            i += 2
            continue
        if raw[i] == "`":
            end = raw.find("`", i + 1)
            if end >= 0:
                output.append("<code>" + html.escape(raw[i + 1:end]) + "</code>")
                i = end + 1
                continue
        if raw[i] == "[":
            match = re.match(r"\[([^\]\n]+)\]\(([^)\n]+)\)", raw[i:])
            if match:
                url = valid_url(match[2])
                output.append(f'<a href="{html.escape(url, quote=True)}">{_inline(match[1], depth + 1)}</a>')
                i += match.end()
                continue
        styled = False
        for marker, tag in tags:
            if raw.startswith(marker, i):
                end = i + len(marker)
                while True:
                    end = raw.find(marker, end)
                    if end < 0 or not _escaped(raw, end):
                        break
                    end += len(marker)
                if end > i + len(marker):
                    output.append(f"<{tag}>" + _inline(raw[i + len(marker):end], depth + 1) + f"</{tag.split()[0]}>")
                    i, styled = end + len(marker), True
                    break
        if not styled:
            output.append(html.escape(raw[i]))
            i += 1
    return "".join(output)


def _rose(raw: str) -> str:
    output: list[str] = []
    quote: list[str] = []
    def flush():
        if quote:
            expandable = quote[-1].endswith("||")
            if expandable:
                quote[-1] = quote[-1][:-2]
            output.append("<blockquote" + (" expandable" if expandable else "") + ">" + _inline("\n".join(quote)) + "</blockquote>")
            quote.clear()
    for line in raw.split("\n"):
        if line.startswith(">"):
            quote.append(line[1:].removeprefix(" "))
        else:
            flush()
            output.append(_inline(line))
    flush()
    return "\n".join(output)


class _SafeHTML(HTMLParser):
    def __init__(self, fillings: Fillings, *, allow_literal: bool = False):
        super().__init__(convert_charrefs=True)
        self.fillings = fillings
        self.allow_literal = allow_literal
        self.parts: list[str] = []
        self.plain: list[str] = []
        self.stack: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        alias = {"strong": "b", "em": "i", "del": "s", "strike": "s", "ins": "u", "tg-spoiler": "span"}
        target = alias.get(tag, tag)
        values = dict(attrs)
        suffix = ""
        if target == "gg-literal" and self.allow_literal:
            self.stack.append((tag, ""))
            return
        if target == "br":
            self.handle_data("\n")
            return
        if target not in {"b", "i", "u", "s", "a", "code", "pre", "span", "blockquote", "tg-emoji"} or len(self.stack) >= 16:
            return
        if target == "a":
            suffix = f' href="{html.escape(valid_url(values.get("href") or ""), quote=True)}"'
        elif target == "span":
            if tag != "tg-spoiler" and values.get("class") != "tg-spoiler":
                return
            suffix = ' class="tg-spoiler"'
        elif target == "blockquote" and "expandable" in values:
            suffix = " expandable"
        elif target == "tg-emoji":
            emoji_id = values.get("emoji-id") or ""
            if not emoji_id.isdigit() or len(emoji_id) > 20:
                return
            suffix = f' emoji-id="{emoji_id}"'
        elif target == "code" and re.fullmatch(r"language-[a-zA-Z0-9_-]{1,32}", values.get("class") or ""):
            suffix = f' class="{values["class"]}"'
        self.parts.append(f"<{target}{suffix}>")
        self.stack.append((tag, target))

    def handle_endtag(self, tag):
        match = next((i for i in range(len(self.stack) - 1, -1, -1) if self.stack[i][0] == tag), None)
        if match is not None:
            while len(self.stack) > match:
                target = self.stack.pop()[1]
                if target:
                    self.parts.append(f"</{target}>")

    def handle_data(self, data):
        if any(target in {"code", "pre", ""} for _, target in self.stack):
            self.parts.append(html.escape(data, quote=False))
            self.plain.append(data)
            return
        start = 0
        for match in _FILL.finditer(data):
            if _escaped(data, match.start()):
                self.parts.append(html.escape(data[start:match.start() - 1] + match.group(), quote=False))
                self.plain.append(data[start:match.start() - 1] + match.group())
                start = match.end()
                continue
            self.parts.append(html.escape(data[start:match.start()], quote=False))
            self.plain.append(data[start:match.start()])
            name = match[1].lower()
            self.parts.append(self.fillings.atom(name))
            self.plain.append(self.fillings.plain(name))
            start = match.end()
        self.parts.append(html.escape(data[start:], quote=False))
        self.plain.append(data[start:])

    def finish(self) -> tuple[str, str]:
        self.close()
        while self.stack:
            target = self.stack.pop()[1]
            if target:
                self.parts.append(f"</{target}>")
        return "".join(self.parts), "".join(self.plain)


def alternatives(body: str, format: Format) -> list[str]:
    ranges = _code_ranges(body, format)
    choices, start = [], 0
    for separator in re.finditer("%%%", body):
        if _escaped(body, separator.start()) or any(first <= separator.start() < last for first, last in ranges):
            continue
        choices.append(body[start:separator.start()])
        start = separator.end()
    choices.append(body[start:])
    if len(choices) > 50:
        raise ContentError("alternative_limit")
    return choices


def validate(raw: str, fillings: Fillings, *, format: Format = "rose", kind: str = "note") -> None:
    body, _ = parse_controls(raw, kind, format=format)
    for index in range(len(alternatives(body, format))):
        render(raw, fillings, format=format, kind=kind, alternative=index)


def render(raw: str, fillings: Fillings, *, format: Format = "rose", kind: str = "note",
           alternative: int | None = None) -> Rendered:
    body, controls = parse_controls(raw, kind, format=format)
    choices = alternatives(body, format)
    if alternative is not None and not 0 <= alternative < len(choices):
        raise ContentError("alternative_invalid")
    body = choices[alternative] if alternative is not None else random.choice(choices)
    body, buttons = _buttons(body, format)
    parser = _SafeHTML(fillings, allow_literal=format == "rose")
    parser.feed(_rose(body) if format == "rose" else body)
    content, plain = parser.finish()
    if utf16_size(plain) > 4096:
        raise ContentError("content_long")
    filled = []
    for button in buttons:
        label = button.label
        if format == "html":
            label_parser = _SafeHTML(fillings)
            label_parser.feed(label)
            _, label = label_parser.finish()
        else:
            label = _FILL.sub(lambda m: fillings.plain(m[1].lower()), html.unescape(label))
        if not label.strip() or utf16_size(label) > 128:
            raise ContentError("button_label_invalid")
        filled.append(Button(label, button.kind, button.target, button.same_row))
    if controls.rules:
        filled.append(Button(fillings.rules_label, "rules", ""))
    if len(filled) > 100:
        raise ContentError("button_limit")
    return Rendered(content, tuple(filled), controls, utf16_size(plain))


def message_source(message: Message, start: int = 0) -> tuple[str, Format]:
    text = message.text or message.caption or ""
    entities = message.entities if message.text is not None else message.caption_entities
    begin = utf16_size(text[:start])
    end = utf16_size(text)
    sliced: list[MessageEntity] = []
    for entity in entities or []:
        first, last = max(entity.offset, begin), min(entity.offset + entity.length, end)
        if last > first and entity.type != "bot_command":
            sliced.append(entity.model_copy(update={"offset": first - begin, "length": last - first}))
    body = text[start:]
    if sliced:
        return html_decoration.unparse(body, sliced), "html"
    return body, "rose"
