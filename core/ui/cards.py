"""Shareable image cards (stories, score cards, invite cards) rendered with Pillow.

Cards are how users show a bot to their friends (Instagram/Telegram stories, chats), so every viral bot uses
them. Arabic and other RTL text is shaped and reordered before drawing.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw, ImageFont

Size = Literal["story", "square"]
SIZES: dict[str, tuple[int, int]] = {"story": (1080, 1920), "square": (1080, 1080)}

THEMES: dict[str, tuple[tuple[int, int, int], tuple[int, int, int]]] = {
    "violet": ((88, 28, 135), (236, 72, 153)),
    "ocean": ((12, 74, 110), (34, 211, 238)),
    "sunset": ((194, 65, 12), (250, 204, 21)),
    "forest": ((20, 83, 45), (132, 204, 22)),
    "night": ((15, 23, 42), (71, 85, 105)),
}

# Bundled OFL fonts work on Windows, packaged wheels and Docker alike.
_FONTS = Path(__file__).resolve().parents[1] / "assets" / "fonts"
FONT_CANDIDATES = (
    str(_FONTS / "NotoSansArabic-Bold.ttf"),
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
)
LATIN_CANDIDATES = (
    str(_FONTS / "NotoSans-Bold.ttf"),
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
)
_RTL = re.compile(r"[֐-ࣿיִ-﷿ﹰ-﻿]")
# Pillow's basic layout cannot draw colour emoji; strip them (cards use drawn shapes instead).
_EMOJI = re.compile("[\U0001f000-\U0001faff☀-➿️‍]")


@dataclass(slots=True)
class Card:
    headline: str
    body: str = ""
    big: str = ""  # a large number or short word, e.g. a score "82"
    big_caption: str = ""
    # NGL-style fake input field under the text ("Send me a message…") — makes the card look tappable.
    placeholder: str = ""
    footer: str = ""  # usually the bot's @username
    theme: str = "violet"


def is_rtl(text: str) -> bool:
    return bool(_RTL.search(text))


def shape(text: str) -> str:
    """Arabic letter shaping + bidi reordering so a non-shaping renderer draws RTL text correctly."""
    # Noto Sans Arabic lacks U+2026; use its covered punctuation rather than a missing-glyph box.
    text = text.replace("…", "...")
    if not is_rtl(text):
        return text
    import arabic_reshaper
    from bidi.algorithm import get_display

    return str(get_display(arabic_reshaper.reshape(text)))


@lru_cache(maxsize=8)
def _font_path(rtl: bool) -> str | None:
    for candidate in FONT_CANDIDATES if rtl else LATIN_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


@lru_cache(maxsize=64)
def font(size: int, rtl: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = _font_path(rtl) or _font_path(not rtl)
    if path is None:
        return ImageFont.load_default(size)
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.BASIC)


def _wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            trial = f"{line} {word}".strip()
            if draw.textlength(shape(trial), font=fnt) <= max_width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def _gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    base = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        base.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return base.resize((w, h))


def _draw_centered(draw: ImageDraw.ImageDraw, lines: list[str], fnt, y: int, width: int, fill, line_h: int) -> int:
    for line in lines:
        shaped = shape(line)
        w = draw.textlength(shaped, font=fnt)
        draw.text(((width - w) / 2, y), shaped, font=fnt, fill=fill)
        y += line_h
    return y


def render(card: Card, size: Size = "story") -> bytes:
    """Render ``card`` to PNG bytes: gradient background, a white panel sized to its content, footer pill."""
    width, height = SIZES[size]
    story = size == "story"
    top, bottom = THEMES.get(card.theme, THEMES["violet"])
    canvas = _gradient((width, height), top, bottom).convert("RGBA")
    measure = ImageDraw.Draw(canvas)

    margin, pad = 80, 90
    inner = width - 2 * margin - 2 * pad
    headline = _EMOJI.sub("", card.headline).strip()
    body = _EMOJI.sub("", card.body).strip()
    rtl = is_rtl(headline + body + card.big_caption + card.placeholder)

    # Fit the whole panel before drawing. Score cards and Arabic text often wrap onto more lines.
    scale = 1.0
    footer_space = 180 if card.footer else 0
    max_panel = height - 2 * margin - footer_space
    while True:
        blocks = []
        if card.big:
            size_big = int((300 if story else 220) * scale)
            blocks.append(([card.big], font(size_big), top, int(size_big * 1.08), 0))
            if card.big_caption:
                fnt = font(int(48 * scale), rtl)
                blocks.append((_wrap(measure, card.big_caption, fnt, inner), fnt, (82, 82, 91),
                               int(66 * scale), int(50 * scale)))
        head_size = int((84 if story else 70) * scale)
        hf = font(head_size, rtl)
        blocks.append((_wrap(measure, headline, hf, inner), hf, (24, 24, 27), int(head_size * 1.3), int(36 * scale)))
        if body:
            body_size = int((50 if story else 42) * scale)
            bf = font(body_size, rtl)
            blocks.append((_wrap(measure, body, bf, inner)[:8], bf, (82, 82, 91), int(body_size * 1.45), 0))
        box_h = int(130 * scale) if card.placeholder else 0
        box_gap = int(60 * scale)
        content_h = sum(len(lines) * lh + gap for lines, _, _, lh, gap in blocks) + (box_h + box_gap if box_h else 0)
        if content_h + 2 * pad <= max_panel or scale <= 0.3:
            break
        scale *= 0.9

    panel_h = content_h + 2 * pad
    panel_top = max(margin, int(height * (0.44 if story else 0.46)) - panel_h // 2)
    panel = (margin, panel_top, width - margin, panel_top + panel_h)

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle((panel[0] + 8, panel[1] + 18, panel[2] + 8, panel[3] + 18), radius=64, fill=(0, 0, 0, 50))
    od.rounded_rectangle(panel, radius=64, fill=(255, 255, 255, 242))
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)

    y = panel[1] + pad
    for lines, fnt, colour, lh, gap in blocks:
        y = _draw_centered(draw, lines, fnt, y, width, colour, lh) + gap
    if card.placeholder:
        y += box_gap
        box = (panel[0] + pad - 20, y, panel[2] - pad + 20, y + box_h)
        draw.rounded_rectangle(box, radius=box_h // 2, fill=(244, 244, 245), outline=(212, 212, 216), width=3)
        pf = font(int(46 * scale), rtl)
        shaped = shape(_EMOJI.sub("", card.placeholder).strip())
        tw = draw.textlength(shaped, font=pf)
        draw.text(((width - tw) / 2, y + (box_h - int(56 * scale)) / 2), shaped, font=pf, fill=(113, 113, 122))

    if card.footer:
        ff = font(52, rtl=is_rtl(card.footer))
        shaped = shape(card.footer)
        fw = draw.textlength(shaped, font=ff)
        free_top = panel[3] + 18
        fy = free_top + (height - free_top) // 2 - 50
        pill = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle(
            ((width - fw) / 2 - 48, fy - 22, (width + fw) / 2 + 48, fy + 84), radius=53, fill=(0, 0, 0, 70)
        )
        canvas = Image.alpha_composite(canvas, pill)
        ImageDraw.Draw(canvas).text(((width - fw) / 2, fy), shaped, font=ff, fill=(255, 255, 255))

    out = io.BytesIO()
    canvas.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()
