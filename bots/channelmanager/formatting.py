"""Explicit compatibility parsers; transport always receives text and UTF-16 entities."""

from __future__ import annotations

import re
from typing import Any

from aiogram.types import MessageEntity

from bots.channelmanager.content import _HTML, ContentError, TextBody, parse_html, safe_url, utf16len


class _Shorthand(_HTML):
    def handle_starttag(self, tag, attrs):
        if tag in {"br", "dot", "inv"} and not attrs:
            self.handle_data({"br": "\n", "dot": "•", "inv": "\u2063"}[tag])
        elif tag in {"m", "f"} and not attrs:
            self.stack.append((tag, tag, utf16len(self.text), {}))
        else:
            super().handle_starttag("tg-spoiler" if tag == "sp" else tag, attrs)

    def handle_startendtag(self, tag, attrs):
        if tag not in {"br", "dot", "inv"}:
            raise ContentError("html")
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "generic":
            if not self.stack:
                raise ContentError("html")
            tag = self.stack[-1][0]
        tag = "tg-spoiler" if tag == "sp" else tag
        if tag in {"m", "f"}:
            if not self.stack or self.stack[-1][0] != tag:
                raise ContentError("html")
            self.stack.pop()
        else:
            super().handle_endtag(tag)

    def handle_data(self, data):
        transforms = [tag for tag, _, _, _ in self.stack if tag in {"m", "f"}]
        for tag in transforms:
            out = []
            for char in data:
                if tag == "f":
                    char = chr(ord(char) + 0xFEE0) if "!" <= char <= "~" else "\u3000" if char == " " else char
                elif "A" <= char <= "Z":
                    char = chr(0x1D670 + ord(char) - ord("A"))
                elif "a" <= char <= "z":
                    char = chr(0x1D68A + ord(char) - ord("a"))
                elif "0" <= char <= "9":
                    char = chr(0x1D7F6 + ord(char) - ord("0"))
                out.append(char)
            data = "".join(out)
        super().handle_data(data)


def shorthand(text: str) -> TextBody:
    parser = _Shorthand()
    parser.feed(text.replace("</>", "</generic>"))
    if parser.rawdata or parser.stack:
        raise ContentError("html")
    parser.close()
    return TextBody(text=parser.text, entities=parser.entities)


def markdown(text: str, *, modern: bool = False) -> TextBody:
    """Supported Telegram legacy/V2 subset, including nesting, escapes, links and fences."""
    output = ""
    entities: list[MessageEntity] = []
    position = 0
    markers = {"*": "bold", "_": "italic", "`": "code", "```": "pre"}
    if modern:
        markers.update({"__": "underline", "~": "strikethrough", "||": "spoiler"})

    def read(until: str | None = None, *, plain=False):
        nonlocal position, output
        start_position = position
        while position < len(text):
            if text[position] == "\\":
                position += 1
                if position == len(text):
                    raise ContentError("markdown")
                output += text[position]
                position += 1
                continue
            if until and text.startswith(until, position):
                position += len(until)
                return
            if plain:
                output += text[position]
                position += 1
                continue
            marker = next((m for m in sorted(markers, key=len, reverse=True) if text.startswith(m, position)), None)
            if marker:
                position += len(marker)
                extra: dict[str, Any] = {}
                if marker == "```":
                    language = re.match(r"([A-Za-z0-9_+-]+)\n", text[position:])
                    if language:
                        extra["language"] = language[1]
                        position += len(language[0])
                offset = utf16len(output)
                read(marker, plain=marker in {"`", "```"})
                length = utf16len(output) - offset
                if not length:
                    raise ContentError("markdown")
                entities.append(MessageEntity(type=markers[marker], offset=offset, length=length, **extra))
                continue
            if text[position] == "[":
                position += 1
                offset = utf16len(output)
                read("]")
                if position >= len(text) or text[position] != "(":
                    raise ContentError("markdown")
                position += 1
                url = ""
                while position < len(text) and text[position] != ")":
                    if text[position] == "\\":
                        position += 1
                    if position == len(text):
                        raise ContentError("markdown")
                    url += text[position]
                    position += 1
                if position == len(text):
                    raise ContentError("markdown")
                position += 1
                entities.append(MessageEntity(type="text_link", offset=offset, length=utf16len(output) - offset, url=safe_url(url)))
                continue
            if modern and text[position] in "_*[]()~`>#+-=|{}.!":
                raise ContentError("markdown")
            output += text[position]
            position += 1
        if until or (position == start_position and until):
            raise ContentError("markdown")

    read()
    return TextBody(text=output, entities=entities)


def parse_format(text: str, mode: str) -> TextBody:
    if mode == "html":
        return parse_html(text)
    if mode == "shorthand":
        return shorthand(text)
    if mode in {"markdown", "markdown2"}:
        return markdown(text, modern=mode == "markdown2")
    raise ContentError("content")
