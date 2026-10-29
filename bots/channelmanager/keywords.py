"""Bounded Unicode token matching without user-supplied regular expressions."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from bots.channelmanager.content import ContentError


def normalized(text: str, case_sensitive=False) -> str:
    value = unicodedata.normalize("NFC", text)
    return value if case_sensitive else value.casefold()


def tokens(text: str):
    for match in re.finditer(r"\S+", text):
        start, end = match.span()
        while start < end and unicodedata.category(text[start]).startswith("P"):
            start += 1
        while end > start and unicodedata.category(text[end - 1]).startswith("P"):
            end -= 1
        if end > start:
            yield start, end, text[start:end]


@dataclass(frozen=True)
class Term:
    atoms: tuple[str, ...]

    def matches(self, value: str, budget: list[int]) -> bool:
        if len(value) > 512:
            return False
        if not any(a in {"(*)", "(+)", "(?)"} for a in self.atoms):
            return "".join(self.atoms) == value
        reachable = {0}
        for atom in self.atoms:
            budget[0] -= max(1, len(reachable))
            if budget[0] < 0:
                raise ContentError("keyword_budget")
            if not reachable:
                return False
            if atom == "(*)":
                reachable = set(range(min(reachable), len(value) + 1))
            elif atom == "(+)":
                reachable = set(range(min(reachable) + 1, len(value) + 1))
            elif atom == "(?)":
                reachable |= {p + 1 for p in reachable if p < len(value)}
            else:
                reachable = {p + 1 for p in reachable if p < len(value) and value[p] == atom}
        return len(value) in reachable


def compile_term(value: str) -> Term:
    if not 1 <= len(value) <= 64 or any(c.isspace() for c in value):
        raise ContentError("keywords")
    atoms = []
    position = 0
    while position < len(value):
        marker = value[position:position + 3]
        if marker in {"(*)", "(+)", "(?)"}:
            atoms.append(marker)
            position += 3
        else:
            if value[position] in '()"&[]{}\\|^$*+?':
                raise ContentError("keywords")
            atoms.append(value[position])
            position += 1
    if sum(a in {"(*)", "(+)", "(?)"} for a in atoms) > 4:
        raise ContentError("keywords")
    return Term(tuple(atoms))


@dataclass(frozen=True)
class Expression:
    exact: str | None
    terms: tuple[Term, ...]
    case_sensitive: bool = False

    @classmethod
    def parse(cls, text: str, case_sensitive=False):
        text = normalized(text.strip(), case_sensitive)
        if not 1 <= len(text) <= 512:
            raise ContentError("keywords")
        if text.startswith('"'):
            if len(text) < 3 or not text.endswith('"') or '"' in text[1:-1]:
                raise ContentError("keywords")
            return cls(text[1:-1], (), case_sensitive)
        parts = text.split("&&")
        if not 1 <= len(parts) <= 8:
            raise ContentError("keywords")
        return cls(None, tuple(compile_term(p.strip()) for p in parts), case_sensitive)

    def matches(self, text: str, budget: list[int] | None = None) -> bool:
        if len(text) > 16384:
            raise ContentError("keyword_budget")
        if self.exact is not None:
            return self.exact == normalized(text.strip(), self.case_sensitive)
        values = [normalized(word, self.case_sensitive) for _, _, word in tokens(text)]
        counter = budget if budget is not None else [200000]
        return all(any(term.matches(value, counter) for value in values) for term in self.terms)


def any_match(expressions: list[str], text: str, case_sensitive=False) -> bool:
    budget = [200000]
    return any(Expression.parse(expr, case_sensitive).matches(text, budget) for expr in expressions)
