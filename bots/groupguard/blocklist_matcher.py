"""Bounded normalized wildcard matching; no backtracking regular expressions."""

from __future__ import annotations

import unicodedata

MAX_PATTERN = 1024  # 256 raw codepoints may expand under Unicode normalization.
MAX_TEXT = 32768


def normalize(text: str) -> str:
    base = unicodedata.normalize("NFKD", text).casefold()
    if base.isascii():
        return " ".join(base.split())
    chars = []
    optional_marks = False
    for char in base:
        if unicodedata.category(char).startswith("M"):
            # Indic vowel/virama and Japanese voicing marks are essential script characters.
            if not optional_marks:
                chars.append(char)
        else:
            optional_marks = any(
                script in unicodedata.name(char, "")
                for script in ("LATIN", "GREEK", "CYRILLIC", "ARABIC", "HEBREW")
            )
            chars.append(char)
    return " ".join(unicodedata.normalize("NFC", "".join(chars)).split())


def tokens(pattern: str):
    if not pattern or len(pattern) > MAX_PATTERN:
        raise ValueError("blocklist_pattern_invalid")
    out = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "\\" and i + 1 < len(pattern):
            out.append(("literal", pattern[i + 1]))
            i += 2
            continue
        if c == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                out.append(("all", ""))
                i += 2
            else:
                out.append(("word", ""))
                i += 1
        elif c == "?":
            out.append(("one", ""))
            i += 1
        else:
            out.append(("literal", c))
            i += 1
    if sum(kind != "literal" for kind, _ in out) > 32:
        raise ValueError("blocklist_wildcard_limit")
    return out


def word(c):
    return c.isalnum() or c == "_" or unicodedata.category(c).startswith("M") or c in {"\u200c", "\u200d"}


def literal_match(text: str, pattern: str, mode="word") -> bool:
    text, literal = normalize(text[:MAX_TEXT])[:MAX_TEXT], normalize(pattern)
    if not literal:
        return False
    if mode == "exact":
        return text == literal
    if mode == "prefix":
        return text.startswith(literal)
    start = 0
    while True:
        position = text.find(literal, start)
        if position < 0:
            return False
        end = position + len(literal)
        if (position == 0 or not word(text[position - 1])) and (end == len(text) or not word(text[end])):
            return True
        start = position + 1


def match(text: str, pattern: str, mode="word") -> bool:
    text = normalize(text[:MAX_TEXT])[:MAX_TEXT]
    pattern = normalize(pattern)
    seq = tokens(pattern)
    size = len(seq)
    if all(kind == "literal" for kind, _ in seq):
        literal = "".join(value for _, value in seq)
        if mode == "exact":
            return text == literal
        if mode == "prefix":
            return text.startswith(literal)
        start = 0
        while True:
            position = text.find(literal, start)
            if position < 0:
                return False
            end = position + len(literal)
            if (position == 0 or not word(text[position - 1])) and (end == len(text) or not word(text[end])):
                return True
            start = position + 1

    # Every literal atom is mandatory, even between optional wildcards.
    # Reject impossible inputs before running the per-character NFA.
    required = {value for kind, value in seq if kind == "literal"}
    if not required.issubset(text):
        return False

    literals: dict[str, int] = {}
    one = looping = skipping = any_loop = 0
    for position, (kind, value) in enumerate(seq):
        bit = 1 << position
        if kind == "literal":
            literals[value] = literals.get(value, 0) | bit
        elif kind == "one":
            one |= bit
        else:
            skipping |= bit
            if kind == "all":
                any_loop |= bit
            else:
                looping |= bit

    def closure(states: int) -> int:
        # Bitset NFA: only forward epsilon edges, at most 32 wildcard hops.
        while True:
            expanded = states | ((states & skipping) << 1)
            if expanded == states:
                return states
            states = expanded

    initial = closure(1)
    final = 1 << size
    active = 0
    for index, c in enumerate(text):
        start = index == 0 if mode in {"exact", "prefix"} else index == 0 or not word(text[index - 1])
        if start:
            active |= initial
        advancing = literals.get(c, 0) | (one if not c.isspace() else 0)
        loops = any_loop | (looping if not c.isspace() else 0)
        active = closure(((active & advancing) << 1) | (active & loops))
        if active & final:
            end = index + 1 == len(text)
            if mode == "exact" and end:
                return True
            if mode == "prefix":
                return True
            if mode == "word" and (end or not word(text[index + 1])):
                return True
    return False
