"""Layered Fluent-based i18n: core translations + optional per-bot bundle overrides."""

from __future__ import annotations

import functools
import uuid
from pathlib import Path
from typing import Any, Protocol

from fluent.runtime import FluentBundle, FluentResource
from fluent.syntax import ast

from core.log import get_logger

log = get_logger(__name__)

LANGUAGES: dict[str, str] = {
    "en": "🇬🇧 English",
    "ar": "🇸🇦 العربية",
    "ru": "🇷🇺 Русский",
    "es": "🇪🇸 Español",
    "tr": "🇹🇷 Türkçe",
    "fa": "🇮🇷 فارسی",
    "hi": "🇮🇳 हिन्दी",
    "id": "🇮🇩 Indonesia",
    "pt": "🇧🇷 Português",
    "fr": "🇫🇷 Français",
    "de": "🇩🇪 Deutsch",
    "uz": "🇺🇿 Oʻzbek",
    "az": "🇦🇿 Azərbaycanca",
    "be": "🇧🇾 Беларуская",
    "bg": "🇧🇬 Български",
    "ckb": "کوردیی ناوەندی",
    "en-gb": "🇬🇧 British English",
    "en-pt": "🏴‍☠️ Pirate English",
    "es-ar": "🇦🇷 Español argentino",
    "fil": "🇵🇭 Filipino",
    "he": "🇮🇱 עברית",
    "it": "🇮🇹 Italiano",
    "ml-in": "🇮🇳 മലയാളം",
    "ms": "🇲🇾 Bahasa Melayu",
    "nl": "🇳🇱 Nederlands",
    "pl": "🇵🇱 Polski",
    "pt-br": "🇧🇷 Português brasileiro",
    "sh": "Srpskohrvatski",
    "ta": "🇮🇳 தமிழ்",
    "uk": "🇺🇦 Українська",
    "vi": "🇻🇳 Tiếng Việt",
    "zh-cn": "🇨🇳 简体中文",
    "zh-tw": "🇹🇼 繁體中文",
}
ALIASES = {"pt-br": "pt", "zh-hans": "zh-cn", "zh-hant": "zh-tw", "ml": "ml-in", "tl": "fil",
    "uk": "ru", "be": "ru", "kk": "ru", "ur": "hi", "ms": "id"}

class Translate(Protocol):
    """Signature of the per-request ``t(key, **vars)`` helper injected by UserMiddleware."""

    def __call__(self, key: str, /, **kwargs: Any) -> str: ...


CORE_LOCALES_DIR = Path(__file__).resolve().parent / "locales"


@functools.lru_cache(maxsize=256)
def _resource(path: Path, modified: int, size: int) -> ast.Resource:
    # Fluent bundles compile their own resolvers from the parsed resource.
    # Sharing source ASTs avoids parsing every locale again for each child;
    # request arguments and compiled-message state stay in each bundle.
    return FluentResource(path.read_text(encoding="utf-8"))


def _load(bundle: FluentBundle, path: Path) -> None:
    """Add a .ftl file to a bundle, logging syntax errors (Fluent silently skips broken entries)."""
    stamp = path.stat()
    resource = _resource(path.resolve(), stamp.st_mtime_ns, stamp.st_size)
    for entry in getattr(resource, "body", []):
        if isinstance(entry, ast.Junk):
            log.error("fluent_parse_error", file=str(path), snippet=(entry.content or "")[:120])
    bundle.add_resource(resource, allow_overrides=True)


def _number_variables(node: ast.SyntaxNode) -> set[str]:
    """Numeric selectors/NUMBER arguments need numbers; ordinary IDs remain text."""
    found: set[str] = set()
    if isinstance(node, ast.SelectExpression) and isinstance(node.selector, ast.VariableReference):
        found.add(node.selector.id.name)
    if isinstance(node, ast.FunctionReference) and node.id.name == 'NUMBER':
        found.update(arg.id.name for arg in node.arguments.positional if isinstance(arg, ast.VariableReference))
    for value in vars(node).values():
        for child in value if isinstance(value, list) else [value]:
            if isinstance(child, ast.SyntaxNode):
                found.update(_number_variables(child))
    return found


class _LazyBundles(dict[str, FluentBundle]):
    """Dictionary of FluentBundles that parses each locale on first use instead of all at startup."""

    def __init__(self, codes: set[str], bot_locales_dir: Path | None) -> None:
        super().__init__()
        self._codes = set(codes)
        self._bot_locales_dir = bot_locales_dir

    def __contains__(self, key: object) -> bool:
        return key in self._codes or super().__contains__(key)

    def _build(self, code: str) -> FluentBundle:
        plural_locale = {"en-pt": "en", "sh": "sr-Latn", "ml-in": "ml"}.get(code, code)
        bundle = FluentBundle([plural_locale], use_isolating=False)

        # 1. Base core translations
        core_file = CORE_LOCALES_DIR / code / "core.ftl"
        if not core_file.exists():
            core_file = CORE_LOCALES_DIR / code.split("-")[0] / "core.ftl"
        if core_file.exists():
            _load(bundle, core_file)

        # 2. Bot specific overrides/additions
        if self._bot_locales_dir:
            for candidate in ("messages.ftl", f"{code}.ftl"):
                bot_file = self._bot_locales_dir / code / candidate
                if bot_file.exists():
                    _load(bundle, bot_file)
                    break
            platform_file = self._bot_locales_dir / code / "platform.ftl"
            if platform_file.exists():
                _load(bundle, platform_file)

        super().__setitem__(code, bundle)
        return bundle

    def __getitem__(self, key: str) -> FluentBundle:
        if not super().__contains__(key) and key in self._codes:
            return self._build(key)
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        if not super().__contains__(key) and key in self._codes:
            return self._build(key)
        return super().get(key, default)


class Translator:
    """Translation manager supporting core platform bundles layered with bot-specific overrides."""

    def __init__(self, bot_locales_dir: Path | None = None, default: str = "en") -> None:
        self.default = default

        # Collect all language codes present in core or bot directories
        codes: set[str] = set()
        if CORE_LOCALES_DIR.exists():
            codes.update(d.name for d in CORE_LOCALES_DIR.iterdir() if d.is_dir())
        if bot_locales_dir and bot_locales_dir.exists():
            codes.update(d.name for d in bot_locales_dir.iterdir() if d.is_dir())

        self.bundles: dict[str, FluentBundle] = _LazyBundles(codes, bot_locales_dir)

        if default not in self.bundles:
            log.warning("default_locale_missing", default=default)
        else:
            # Eagerly load only the default language at startup; other locales load on first request.
            self.bundles.get(default)

    @property
    def locales(self) -> list[str]:
        return [code for code in LANGUAGES if code in self.bundles]

    def resolve(self, language_code: str | None) -> str:
        if not language_code:
            return self.default
        code = language_code.lower().replace('_','-')
        # Prefer installed regional content, then the longest available script or
        # legacy alias. Telegram can supply tags such as zh-Hant-TW or tl-PH.
        while code:
            if code in self.bundles:
                return code
            alias = ALIASES.get(code)
            if alias in self.bundles:
                return alias
            code = code.rpartition('-')[0]
        return self.default

    def get(self, lang: str | None, key: str, /, **kwargs: Any) -> str:
        for code in (lang or self.default, self.default):
            bundle = self.bundles.get(code)
            if bundle is None or not bundle.has_message(key):
                continue
            message = bundle.get_message(key)
            if message.value is None:
                continue
            # Ordinary numbers are text to preserve IDs/resolutions. Actual Fluent
            # numeric selectors and NUMBER calls retain numbers for CLDR branches.
            numeric = _number_variables(message.value)
            args = {k: str(v) if isinstance(v, int | float) and not isinstance(v, bool) and k not in numeric else v
                for k, v in kwargs.items()}
            # Fluent's 2500-character placeable limit protects expression expansion. Long
            # external text is already data, never Fluent source. Substitute bounded opaque
            # markers during resolution and restore it afterwards, preserving those guards.
            replacements: dict[str,str]={}
            for name,value in args.items():
                if isinstance(value,str) and len(value)>2000:
                    if len(value)>65536:
                        raise ValueError('translation_argument_too_long')
                    marker='\ue000'+uuid.uuid4().hex+'\ue001'
                    while marker in value or marker in replacements:
                        marker='\ue000'+uuid.uuid4().hex+'\ue001'
                    replacements[marker]=value
                    args[name]=marker
            text, errors = bundle.format_pattern(message.value, args)
            if errors:
                log.warning("fluent_format_error", key=key, lang=code, errors=[str(e) for e in errors])
            result=str(text)
            projected=len(result)+sum(result.count(marker)*(len(value)-len(marker))
                for marker,value in replacements.items())
            if projected>131072:
                raise ValueError('translation_result_too_long')
            for marker,value in replacements.items():
                result=result.replace(marker,value)
            return result
        return key

    def __call__(self, lang: str | None, key: str, **kwargs: Any) -> str:
        return self.get(lang, key, **kwargs)

    def bind(self, lang: str | None) -> Translate:
        """A ``t(key, **vars)`` callable for one language (e.g. to write to someone other than the sender)."""
        resolved = self.resolve(lang)
        return functools.partial(self.get, resolved)
