"""Validated canonical content and one renderer for private previews and channel publication."""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Any, Literal
from urllib.parse import quote, urlparse

from aiogram.methods import (
    EditMessageMedia,
    EditMessageText,
    SendAnimation,
    SendDocument,
    SendMessage,
    SendPhoto,
    SendVideo,
)
from aiogram.types import (
    CopyTextButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaAnimation,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    LinkPreviewOptions,
    Message,
    MessageEntity,
    ReplyParameters,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class ContentError(ValueError):
    pass


def validation_code(exc: Exception, default="content") -> str:
    if isinstance(exc, ContentError):
        return str(exc)
    if isinstance(exc, ValidationError):
        for issue in exc.errors():
            cause = issue.get("ctx", {}).get("error")
            if isinstance(cause, ContentError):
                return str(cause)
    return default


def utf16len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def safe_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https", "tg"} or not parsed.netloc or any(ord(c) < 32 for c in value):
        raise ContentError("url")
    return value


class TextBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = ""
    entities: list[MessageEntity] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def check_entities(self):
        boundaries = {0}
        offset = 0
        for char in self.text:
            offset += utf16len(char)
            boundaries.add(offset)
        for entity in self.entities:
            if entity.offset not in boundaries or entity.offset + entity.length not in boundaries or entity.length <= 0:
                raise ContentError("entities")
            if entity.url:
                safe_url(entity.url)
        for index, first in enumerate(self.entities):
            for second in self.entities[index + 1:]:
                a, b = sorted((first, second), key=lambda e: (e.offset, -e.length))
                if a.offset < b.offset < a.offset + a.length < b.offset + b.length:
                    raise ContentError("entities")
                overlap = max(a.offset, b.offset) < min(a.offset + a.length, b.offset + b.length)
                if overlap and (a.type in {"code", "pre"} or b.type in {"code", "pre"}):
                    raise ContentError("entities")
        return self


class LinkButton(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=64)
    url: str | None = Field(default=None, min_length=1, max_length=2048)
    kind: Literal["link", "popup", "alert", "member", "copy", "comments", "share", "vote"] = "link"
    value: str = Field(default="", max_length=256)
    required_channel: int | None = Field(default=None, lt=0)
    otherwise: str = Field(default="", max_length=200)

    @model_validator(mode="after")
    def check_url(self):
        if self.url:
            safe_url(self.url)
        if self.kind in {"link", "comments"} and not self.url:
            raise ContentError("buttons")
        if self.kind == "comments" and urlparse(self.url or "").hostname not in {"t.me", "telegram.me"}:
            raise ContentError("buttons")
        if self.kind in {"popup", "alert", "member"} and not 1 <= len(self.value) <= 200:
            raise ContentError("buttons")
        if self.kind == "copy" and not self.value:
            raise ContentError("buttons")
        if self.kind == "member" and self.required_channel is None:
            raise ContentError("buttons")
        return self


class PostSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["text", "photo", "video", "animation", "document"] = "text"
    body: TextBody
    file_id: str | None = Field(default=None, max_length=1024)
    media_bot_id: int | None = None
    buttons: list[list[LinkButton]] = Field(default_factory=list, max_length=10)
    reactions: list[str] = Field(default_factory=list, max_length=6)
    signature: TextBody = Field(default_factory=TextBody)
    include_signature: bool = True
    notifications: bool = True
    link_preview: bool = True
    protected: bool = False
    pin: bool = False
    caption_above: bool = False
    reply_message_id: int | None = Field(default=None, gt=0)
    delete_after_seconds: int | None = Field(default=None, gt=0, le=31536000)

    @model_validator(mode="after")
    def validate_content(self):
        if self.kind != "text" and (not self.file_id or not self.media_bot_id or "://" in self.file_id):
            raise ContentError("media")
        if self.kind == "text" and self.file_id is not None:
            raise ContentError("media")
        if any(not row or len(row) > 4 for row in self.buttons):
            raise ContentError("buttons")
        if any(not r.strip() or len(r) > 32 for r in self.reactions) or len(set(self.reactions)) != len(self.reactions):
            raise ContentError("buttons")
        if self.protected and any(b.kind in {"copy", "share"} for row in self.buttons for b in row):
            raise ContentError("buttons")
        text, _ = self.render()
        if (self.kind == "text" and not text) or utf16len(text) > (4096 if self.kind == "text" else 1024):
            raise ContentError("length")
        if self.caption_above and self.kind not in {"photo", "video", "animation"}:
            raise ContentError("caption")
        if utf16len(self.signature.text) > 250:
            raise ContentError("length")
        return self

    def render(self) -> tuple[str, list[MessageEntity]]:
        text, entities = self.body.text, list(self.body.entities)
        if self.include_signature and self.signature.text:
            gap = "\n\n" if text else ""
            shift = utf16len(text + gap)
            text += gap + self.signature.text
            entities += [e.model_copy(update={"offset": e.offset + shift}) for e in self.signature.entities]
        return text, entities

    def keyboard(self, *, delivery_id: str | None = None, version: int = 1, channel_id: int | None = None,
                 message_id: int | None = None, counts: dict[int, int] | None = None, closed: bool = False) -> InlineKeyboardMarkup | None:
        counts = counts or {}
        rows = []
        def render(button: LinkButton, choice: int):
            text = button.text
            if button.kind == "vote":
                text = f"{text[:48]} · {counts.get(choice, 0)}{' 🔒' if closed else ''}"
            if button.kind in {"link", "comments"}:
                return InlineKeyboardButton(text=text, url=button.url)
            if button.kind == "copy":
                return InlineKeyboardButton(text=text, copy_text=CopyTextButton(text=button.value))
            if button.kind == "share":
                url = button.url
                if not url and channel_id and message_id and str(channel_id).startswith("-100"):
                    url = f"https://t.me/c/{str(channel_id)[4:]}/{message_id}"
                if not url:
                    return None
                return InlineKeyboardButton(text=text, url="https://t.me/share/url?url=" + quote(url, safe=""))
            data = f"chi:{delivery_id}:{version}:{choice}" if delivery_id else "chi:preview"
            return InlineKeyboardButton(text=text, callback_data=data)
        for row_index, row in enumerate(self.buttons):
            rendered = [render(b, row_index * 4 + index) for index, b in enumerate(row)]
            if items := [b for b in rendered if b is not None]:
                rows.append(items)
        for start in range(0, len(self.reactions), 3):
            rows.append([render(LinkButton(text=text, kind="vote"), 40 + i)
                         for i, text in enumerate(self.reactions[start:start + 3], start)])
        return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None

    def send_method(self, chat_id: int, *, preview: bool = False, markup: InlineKeyboardMarkup | None = None):
        text, entities = self.render()
        common: dict[str, Any] = {"chat_id": chat_id, "parse_mode": None, "reply_markup": markup or self.keyboard(),
            "disable_notification": not self.notifications, "protect_content": self.protected}
        if self.reply_message_id and not preview:
            common["reply_parameters"] = ReplyParameters(message_id=self.reply_message_id)
        if self.kind == "text":
            return SendMessage(text=text, entities=entities, link_preview_options=LinkPreviewOptions(is_disabled=not self.link_preview), **common)
        assert self.file_id is not None
        common.update(caption=text or None, caption_entities=entities or None)
        if self.kind in {"photo", "video", "animation"}:
            common["show_caption_above_media"] = self.caption_above
        if self.kind == "photo":
            return SendPhoto(photo=self.file_id, **common)
        if self.kind == "video":
            return SendVideo(video=self.file_id, **common)
        if self.kind == "animation":
            return SendAnimation(animation=self.file_id, **common)
        return SendDocument(document=self.file_id, **common)

    def edit_method(self, chat_id: int, message_id: int, *, markup: InlineKeyboardMarkup | None = None):
        text, entities = self.render()
        if self.kind == "text":
            return EditMessageText(chat_id=chat_id, message_id=message_id, text=text, entities=entities,
                parse_mode=None, reply_markup=markup or self.keyboard(), link_preview_options=LinkPreviewOptions(is_disabled=not self.link_preview))
        common: dict[str, Any] = {"media": self.file_id, "caption": text or None, "caption_entities": entities or None, "parse_mode": None}
        classes = {"photo": InputMediaPhoto, "video": InputMediaVideo, "animation": InputMediaAnimation, "document": InputMediaDocument}
        if self.kind != "document":
            common["show_caption_above_media"] = self.caption_above
        return EditMessageMedia(chat_id=chat_id, message_id=message_id, media=classes[self.kind](**common), reply_markup=markup or self.keyboard())


def from_message(message: Message, bot_id: int, *, html: bool = False, signature: TextBody | None = None,
                 format_mode: str | None = None) -> PostSpec:
    if message.media_group_id:
        raise ContentError("album")
    from bots.channelmanager.formatting import parse_format
    body = parse_format(message.text or message.caption or "", format_mode or "html") if html or format_mode else TextBody(
        text=message.text or message.caption or "", entities=message.entities or message.caption_entities or [])
    media = next(((kind, getattr(message, kind)) for kind in ("photo", "video", "animation", "document") if getattr(message, kind)), None)
    if media:
        kind, value = media
        file_id = value[-1].file_id if kind == "photo" else value.file_id
        return PostSpec(kind=kind, body=body, file_id=file_id, media_bot_id=bot_id, signature=signature or TextBody())
    if not message.text:
        raise ContentError("media")
    return PostSpec(body=body, signature=signature or TextBody())


def parse_buttons(text: str) -> list[list[LinkButton]]:
    if text.strip() == "-":
        return []
    rows = []
    for line in text.strip().splitlines():
        row = []
        for item in line.split("&&"):
            if " | " in item:
                parts = [p.strip() for p in item.split(" | ")]
                if len(parts) < 2:
                    raise ContentError("buttons")
                label, kind, *values = parts
                options: dict[str, Any] = {"text": label, "kind": kind}
                if kind == "member" and 2 <= len(values) <= 3:
                    options.update(required_channel=int(values[0]), value=values[1], otherwise=values[2] if len(values) == 3 else "")
                elif kind in {"link", "comments", "share"} and len(values) <= 1:
                    options["url"] = values[0] if values else None
                elif kind in {"copy", "popup", "alert"} and len(values) == 1:
                    options["value"] = values[0]
                elif kind != "vote" or values:
                    raise ContentError("buttons")
                row.append(LinkButton.model_validate(options))
                continue
            label, sep, url = item.strip().partition(" - ")
            if not sep:
                raise ContentError("buttons")
            row.append(LinkButton(text=label.strip(), url=url.strip()))
        rows.append(row)
    return rows


class _HTML(HTMLParser):
    tags = {"b": "bold", "strong": "bold", "i": "italic", "em": "italic", "u": "underline", "ins": "underline",
            "s": "strikethrough", "strike": "strikethrough", "del": "strikethrough", "code": "code", "pre": "pre",
            "blockquote": "blockquote", "tg-spoiler": "spoiler", "a": "text_link"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = ""
        self.entities: list[MessageEntity] = []
        self.stack: list[tuple[str, str, int, dict[str, Any]]] = []

    def handle_starttag(self, tag, attrs):
        options = dict(attrs)
        if tag not in self.tags or (options and not (tag == "a" and set(options) == {"href"})):
            raise ContentError("html")
        extra = {"url": safe_url(options["href"])} if tag == "a" and options.get("href") else {}
        if tag == "a" and not extra:
            raise ContentError("html")
        self.stack.append((tag, self.tags[tag], utf16len(self.text), extra))

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1][0] != tag:
            raise ContentError("html")
        _, kind, offset, extra = self.stack.pop()
        length = utf16len(self.text) - offset
        if length:
            self.entities.append(MessageEntity(type=kind, offset=offset, length=length, **extra))

    def handle_data(self, data):
        self.text += data

    def handle_comment(self, data):
        raise ContentError("html")

    def handle_decl(self, decl):
        raise ContentError("html")


def parse_html(text: str) -> TextBody:
    parser = _HTML()
    parser.feed(text)
    if parser.rawdata:
        raise ContentError("html")
    parser.close()
    if parser.stack or parser.rawdata:
        raise ContentError("html")
    return TextBody(text=parser.text, entities=parser.entities)
