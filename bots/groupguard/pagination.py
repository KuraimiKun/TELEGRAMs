"""Telegram counts visible UTF-16 units, not database rows or escaped HTML bytes."""
from __future__ import annotations

from html.parser import HTMLParser


class Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str]=[]

    def handle_data(self,data: str) -> None:
        self.parts.append(data)


def units(html: str) -> int:
    parser=Visible()
    parser.feed(html)
    parser.close()
    return len(''.join(parser.parts).encode('utf-16-le'))//2
