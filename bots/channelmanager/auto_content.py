"""Typed source content, rule filters and repeat-safe canonical transformations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Literal

from aiogram.types import Message
from pydantic import BaseModel, ConfigDict, Field, model_validator

from bots.channelmanager.content import ContentError, LinkButton, PostSpec, TextBody, utf16len
from bots.channelmanager.keywords import Expression, any_match, normalized, tokens

KINDS = {"text", "photo", "video", "animation", "document", "album"}


class Filters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    triggers: list[str] = Field(default_factory=list, max_length=20)
    excludes: list[str] = Field(default_factory=list, max_length=20)
    media: list[str] = Field(default_factory=lambda: sorted(KINDS), min_length=1, max_length=6)
    command: str | None = Field(default=None, min_length=1, max_length=64)
    case_sensitive: bool = False

    @model_validator(mode="after")
    def valid(self):
        if not set(self.media) <= KINDS or (self.command and any(c.isspace() for c in self.command)):
            raise ContentError("filters")
        for expression in self.triggers + self.excludes:
            Expression.parse(expression, self.case_sensitive)
        return self

    def matches(self, items: list[SourceItem], *, album=False) -> bool:
        kind = "album" if album else items[0].kind
        text = "\n".join(item.body.text for item in items)
        if kind not in self.media:
            return False
        if self.command and normalized(text.split(maxsplit=1)[0] if text.split() else "", self.case_sensitive) != normalized(self.command, self.case_sensitive):
            return False
        return (not self.triggers or any_match(self.triggers, text, self.case_sensitive)) and not any_match(self.excludes, text, self.case_sensitive)


class MediaReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["photo", "video", "animation", "sticker"]
    file_id: str = Field(min_length=1, max_length=1024)
    unique_id: str = Field(min_length=1, max_length=256)
    bot_id: int = Field(gt=0)

    @model_validator(mode="after")
    def valid(self):
        if "://" in self.file_id:
            raise ContentError("media")
        return self


class Replacement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    old: str = Field(min_length=1, max_length=64)
    new: str = Field(max_length=500)

    @model_validator(mode="after")
    def valid(self):
        parts = list(tokens(self.old))
        if len(parts) != 1 or parts[0][2] != self.old:
            raise ContentError("replacement")
        return self


class RuleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filters: Filters = Field(default_factory=Filters)
    header: TextBody = Field(default_factory=TextBody)
    signature: TextBody = Field(default_factory=TextBody)
    buttons: list[list[LinkButton]] = Field(default_factory=list, max_length=10)
    reactions: list[str] = Field(default_factory=list, max_length=6)
    attachment: MediaReference | None = None
    separator: MediaReference | None = None
    replacements: list[Replacement] = Field(default_factory=list, max_length=50)
    remove_command: bool = True
    on_edits: bool = True
    delete_after_seconds: int | None = Field(default=None, gt=0, le=31536000)

    @model_validator(mode="after")
    def valid(self):
        if utf16len(self.header.text) > 500 or utf16len(self.signature.text) > 250:
            raise ContentError("length")
        if (self.attachment and self.attachment.kind == "sticker") or (self.separator and self.separator.kind != "sticker"):
            raise ContentError("media")
        keys = [normalized(r.old, self.filters.case_sensitive) for r in self.replacements]
        if len(set(keys)) != len(keys):
            raise ContentError("replacement")
        PostSpec(body=TextBody(text="validation"), buttons=self.buttons, reactions=self.reactions)
        return self


class RouteSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filters: Filters = Field(default_factory=Filters)
    mode: Literal["copy", "forward"] = "copy"
    content: Literal["original", "transformed"] = "original"
    propagate_edits: bool = False
    max_hops: int = Field(default=4, ge=1, le=8)

    @model_validator(mode="after")
    def valid(self):
        if self.mode == "forward" and self.propagate_edits:
            raise ContentError("forward_edits")
        return self


class SourceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message_id: int = Field(gt=0)
    kind: Literal["text", "photo", "video", "animation", "document", "unsupported"]
    body: TextBody = Field(default_factory=TextBody)
    file_id: str | None = None
    unique_id: str | None = None
    buttons: list[list[LinkButton]] = Field(default_factory=list)
    protected: bool = False
    sent_at: datetime

    def spec(self, bot_id: int) -> PostSpec:
        if self.kind == "unsupported":
            raise ContentError("unsupported_media")
        buttons = [[b for b in row if not self.protected or b.kind not in {"copy", "share"}] for row in self.buttons]
        return PostSpec(kind=self.kind, body=self.body, file_id=self.file_id,
            media_bot_id=bot_id if self.file_id else None, include_signature=False, protected=self.protected,
            buttons=[row for row in buttons if row])

    def fingerprint(self, *, media=True, privacy=True) -> str:
        formatting = []
        for entity in self.body.entities:
            if entity.type in {"url", "email", "mention", "hashtag", "cashtag", "bot_command", "phone_number"}:
                continue
            data = entity.model_dump(mode="json", exclude_none=True)
            if entity.user:
                data["user"] = {"id": entity.user.id}
            formatting.append(data)
        value: dict[str, Any] = {"kind": self.kind, "text": self.body.text,
            "entities": sorted(formatting, key=lambda e: (e["offset"], e["length"], e["type"]))}
        if media:
            value["media"] = self.unique_id or self.file_id
        if privacy:
            value["protected"] = self.protected
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def from_source(message: Message) -> SourceItem:
    kind, file_id, unique_id = "text" if message.text is not None else "unsupported", None, None
    for name in ("photo", "video", "animation", "document"):
        value = getattr(message, name)
        if value:
            value = value[-1] if name == "photo" else value
            kind, file_id, unique_id = name, value.file_id, value.file_unique_id
            break
    buttons = []
    if message.reply_markup:
        for row in message.reply_markup.inline_keyboard:
            safe = []
            for button in row[:4]:
                if button.url:
                    try:
                        safe.append(LinkButton(text=button.text, url=button.url))
                    except ValueError:
                        continue
            if safe:
                buttons.append(safe)
    return SourceItem(message_id=message.message_id, kind=kind, body=TextBody(text=message.text or message.caption or "",
        entities=message.entities or message.caption_entities or []), file_id=file_id, unique_id=unique_id,
        protected=bool(message.has_protected_content), sent_at=message.date, buttons=buttons[:10])


def splice(body: TextBody, start: int, end: int, replacement: str) -> TextBody:
    """Replace Python-character ranges, preserving UTF-16 formatting outside/around them."""
    left, right = utf16len(body.text[:start]), utf16len(body.text[:end])
    delta = utf16len(replacement) - (right - left)
    entities = []
    for entity in body.entities:
        a, b = entity.offset, entity.offset + entity.length
        if b <= left:
            entities.append(entity)
        elif a >= right:
            entities.append(entity.model_copy(update={"offset": a + delta}))
        elif a <= left and b >= right and entity.type != "custom_emoji":
            if b - a + delta > 0:
                entities.append(entity.model_copy(update={"length": b - a + delta}))
        else:
            if a < left:
                entities.append(entity.model_copy(update={"length": left - a}))
            if b > right:
                entities.append(entity.model_copy(update={"offset": left + utf16len(replacement), "length": b - right}))
    return TextBody(text=body.text[:start] + replacement + body.text[end:], entities=entities)


def affix(body: TextBody, header: TextBody, signature: TextBody) -> tuple[TextBody, dict[str, str]]:
    prefix = header.text + ("\n\n" if header.text and body.text else "")
    suffix = ("\n\n" if signature.text and (body.text or prefix) else "") + signature.text
    offset = utf16len(prefix)
    entities = list(header.entities) + [e.model_copy(update={"offset": e.offset + offset}) for e in body.entities]
    signature_offset = utf16len(prefix + body.text + suffix[:-len(signature.text)] if signature.text else prefix + body.text)
    entities += [e.model_copy(update={"offset": e.offset + signature_offset}) for e in signature.entities]
    return TextBody(text=prefix + body.text + suffix, entities=entities), {"prefix": prefix, "suffix": suffix}


def strip_affixes(item: SourceItem, saved: dict[str, str]) -> SourceItem:
    body = item.body
    prefix, suffix = saved.get("prefix", ""), saved.get("suffix", "")
    if prefix and body.text.startswith(prefix):
        body = splice(body, 0, len(prefix), "")
    if suffix and body.text.endswith(suffix):
        body = splice(body, len(body.text) - len(suffix), len(body.text), "")
    return item.model_copy(update={"body": body})


def transform(items: list[SourceItem], rule: RuleSpec, bot_id: int, *, album=False):
    result = [item.model_copy(deep=True) for item in items]
    warnings: list[str] = []
    metadata: dict[int, dict[str, str]] = {}
    if album:
        # Albums receive one signature on the caption-bearing/first item only.
        index = next((i for i, item in enumerate(result) if item.body.text), 0)
        result[index].body, metadata[result[index].message_id] = affix(result[index].body, TextBody(), rule.signature)
        if any((rule.header.text, rule.buttons, rule.reactions, rule.attachment, rule.separator, rule.replacements, rule.filters.command)):
            warnings.append("album_signature_only")
    else:
        item = result[0]
        body = item.body
        if rule.filters.command and rule.remove_command:
            parts = body.text.split(maxsplit=1)
            if parts and normalized(parts[0], rule.filters.case_sensitive) == normalized(rule.filters.command, rule.filters.case_sensitive):
                stop = body.text.find(parts[0]) + len(parts[0])
                while stop < len(body.text) and body.text[stop].isspace():
                    stop += 1
                body = splice(body, 0, stop, "")
        mapping = {normalized(r.old, rule.filters.case_sensitive): r.new for r in rule.replacements}
        changes = [(a, b, mapping[normalized(word, rule.filters.case_sensitive)]) for a, b, word in tokens(body.text)
            if normalized(word, rule.filters.case_sensitive) in mapping]
        for start, end, value in reversed(changes):
            body = splice(body, start, end, value)
        item.body, metadata[item.message_id] = affix(body, rule.header, rule.signature)
        item.buttons = rule.buttons or item.buttons
        if rule.attachment:
            if rule.attachment.bot_id != bot_id:
                raise ContentError("media")
            if item.kind == "text":
                if rule.attachment.kind == "sticker":
                    raise ContentError("media")
                item.kind, item.file_id, item.unique_id = rule.attachment.kind, rule.attachment.file_id, rule.attachment.unique_id
            else:
                warnings.append("existing_media_retained")
    for item in result:
        spec = item.spec(bot_id)
        if not album:
            PostSpec.model_validate({**spec.model_dump(mode="json"), "reactions": rule.reactions})
    return result, metadata, warnings


def routed_spec(item: SourceItem, bot_id: int) -> PostSpec:
    # Source-bound callbacks, reactions and comments must not be copied to another chat.
    safe = [[b for b in row if b.kind in {"link", "copy"} or (b.kind == "share" and b.url)] for row in item.buttons]
    return item.model_copy(update={"buttons": [row for row in safe if row]}).spec(bot_id)
