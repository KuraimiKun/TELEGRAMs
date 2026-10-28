"""Actual PNG challenge generation; opaque choice indices keep callback payloads bounded."""
from __future__ import annotations

import io
import secrets
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ALPHABET = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
WORDS = ('BIRD', 'TREE', 'FISH', 'STAR', 'MOON', 'BOOK', 'LAMP', 'SHIP', 'CAKE', 'BELL', 'FROG', 'DUCK')
RNG = secrets.SystemRandom()


@dataclass(frozen=True, slots=True)
class Question:
    mode: str
    image_text: str
    choices: tuple[str, ...]
    answer: str

    def png(self, font_path: Path | None = None) -> bytes:
        return png(self.image_text, font_path)

    def to_dict(self) -> dict:
        return dict(mode=self.mode, image_text=self.image_text, choices=list(self.choices), answer=self.answer)

    @classmethod
    def from_dict(cls, raw: dict) -> Question:
        if (raw.get('mode') not in {'text', 'text2', 'math', 'button'} or
            not isinstance(raw.get('image_text'), str) or len(raw['image_text']) > 64 or
            not isinstance(raw.get('choices'), list) or not 1 <= len(raw['choices']) <= 8 or
            any(not isinstance(v, str) or not v or len(v) > 32 for v in raw['choices']) or
            not isinstance(raw.get('answer'), str) or not raw['answer'] or len(raw['answer']) > 8):
            raise ValueError('captcha_prompt_invalid')
        return cls(raw['mode'], raw['image_text'], tuple(raw['choices']), raw['answer'])


def question(mode: str) -> Question:
    if mode == 'button':
        return Question(mode, '', ('ok',), '0')
    if mode == 'math':
        a, b = RNG.randint(1, 9), RNG.randint(1, 9)
        answer = a + b
        number_choices = [answer, *RNG.sample([n for n in range(2, 19) if n != answer], 3)]
        RNG.shuffle(number_choices)
        return Question(mode, f'{a} + {b} = ?', tuple(str(n) for n in number_choices), str(number_choices.index(answer)))
    if mode == 'text':
        word_choices = RNG.sample(WORDS, 4)
        word_target = RNG.choice(word_choices)
        return Question(mode, word_target, tuple(word_choices), str(word_choices.index(word_target)))
    if mode == 'text2':
        char_target = ''.join(RNG.choice(ALPHABET) for _ in range(4))
        char_choices = list(dict.fromkeys(char_target))
        char_choices.extend(RNG.sample([c for c in ALPHABET if c not in char_choices], 8 - len(char_choices)))
        RNG.shuffle(char_choices)
        return Question(mode, char_target, tuple(char_choices), ''.join(str(char_choices.index(c)) for c in char_target))
    raise ValueError('captcha_mode_invalid')


def png(value: str, font_path: Path | None = None) -> bytes:
    if not value or len(value) > 64:
        raise ValueError('captcha_image_invalid')
    font_path = font_path or Path(__file__).resolve().parents[2] / 'core/assets/fonts/NotoSans-Bold.ttf'
    canvas = Image.new('RGB', (640, 180), (246, 249, 253))
    draw = ImageDraw.Draw(canvas)
    for _ in range(70):
        x, y = RNG.randrange(640), RNG.randrange(180)
        draw.ellipse((x, y, x + 2, y + 2), fill=(160, 176, 198))
    font = ImageFont.truetype(str(font_path), 66)
    left, top, right, bottom = draw.textbbox((0, 0), value, font=font)
    if right - left > 600:
        font = ImageFont.truetype(str(font_path), 36)
        left, top, right, bottom = draw.textbbox((0, 0), value, font=font)
    draw.text(((640 - right + left) / 2 - left, (180 - bottom + top) / 2 - top), value,
        fill=(27, 48, 77), font=font)
    output = io.BytesIO()
    canvas.save(output, format='PNG')
    return output.getvalue()
