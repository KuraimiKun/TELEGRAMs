"""Every translation key used in code exists, and every language defines the same keys and variables."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fluent.syntax import FluentParser, ast

ROOT = Path(__file__).resolve().parents[1]
KEY_CALL = re.compile(r"""\bt\(\s*"([a-z][a-z0-9-]+)"|\.get\(\s*[\w.]+\s*,\s*"([a-z][a-z0-9-]+)\"""")


def variables(node: ast.SyntaxNode) -> set[str]:
    found: set[str] = set()
    if isinstance(node, ast.VariableReference):
        found.add(node.id.name)
    for value in vars(node).values():
        for child in value if isinstance(value, list) else [value]:
            if isinstance(child, ast.SyntaxNode):
                found |= variables(child)
    return found


def ftl_messages(path: Path) -> dict[str, set[str]]:
    """message id -> set of variable names it uses."""
    resource = FluentParser().parse(path.read_text(encoding="utf-8"))
    out: dict[str, set[str]] = {}
    for entry in resource.body:
        if isinstance(entry, ast.Junk):
            raise AssertionError(f"{path}: unparsable entry: {entry.content[:80]!r}")
        if isinstance(entry, ast.Message):
            out[entry.id.name] = variables(entry)
    return out


def locale_sets(base: Path, filename: str) -> dict[str, dict[str, set[str]]]:
    return {d.name: ftl_messages(d / filename) for d in sorted(base.iterdir()) if (d / filename).exists()}


CORE = locale_sets(ROOT / "core" / "locales", "core.ftl")
BOTS = {
    d.name: locale_sets(d / "locales", "messages.ftl")
    for d in sorted((ROOT / "bots").iterdir())
    if (d / "locales").is_dir()
}


@pytest.mark.parametrize("name,sets", [("core", CORE), *BOTS.items()])
def test_languages_define_identical_keys_and_variables(name, sets):
    reference = sets["en"]
    for lang, messages in sets.items():
        assert set(messages) == set(reference), f"{name}/{lang}: key mismatch {set(messages) ^ set(reference)}"
        for key, variables in reference.items():
            assert messages[key] == variables, f"{name}/{lang}/{key}: variables {messages[key]} != {variables}"


def used_keys(paths: list[Path]) -> set[str]:
    keys: set[str] = set()
    for path in paths:
        for match in KEY_CALL.finditer(path.read_text(encoding="utf-8")):
            keys.add(match.group(1) or match.group(2))
    return keys


def test_core_code_only_uses_core_keys():
    code = [p for p in (ROOT / "core").rglob("*.py") if "scaffold" not in p.parts]  # templates for new bots
    missing = used_keys(code) - set(CORE["en"])
    assert not missing, f"core code uses keys missing from core.ftl: {sorted(missing)}"


@pytest.mark.parametrize("bot", sorted(BOTS))
def test_bot_code_keys_exist(bot):
    available = set(CORE["en"]) | set(BOTS[bot]["en"])
    missing = used_keys(list((ROOT / "bots" / bot).rglob("*.py"))) - available
    assert not missing, f"{bot} uses undefined keys: {sorted(missing)}"
