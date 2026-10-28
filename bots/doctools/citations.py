"""Bibliographic metadata and four citation styles, with bounded public-only URL fetching."""

from __future__ import annotations

import asyncio
import hashlib
import html
import ipaddress
import json
import re
import socket
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import quote, urljoin, urlsplit

import aiohttp
from aiohttp.abc import ResolveResult
from aiohttp.resolver import ThreadedResolver

from core.sdk.context import BotContext
from core.ui.text import esc

MAX_RESPONSE = 2 * 1024 * 1024
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)
STYLES = ("APA", "MLA", "Harvard", "Chicago")


class CitationError(ValueError):
    """Metadata is unavailable or the input cannot be safely retrieved."""


def _public(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


def check_url(url: str) -> None:
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").rstrip(".").lower()
    except ValueError as e:
        raise CitationError("invalid URL") from e
    if parts.scheme not in {"http", "https"} or not host or parts.username or parts.password:
        raise CitationError("invalid URL")
    try:
        port = parts.port
    except ValueError as e:
        raise CitationError("invalid port") from e
    if port not in {None, 80, 443}:
        raise CitationError("non-web port")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if "." not in host or host.endswith((".localhost", ".local", ".internal", ".lan")):
            raise CitationError("non-public host") from None
    else:
        if not _public(host):
            raise CitationError("non-public address")


class PublicResolver(ThreadedResolver):
    """Validate the addresses actually used by the connector, including every redirect."""

    async def resolve(self, host: str, port: int = 0,
                      family: socket.AddressFamily = socket.AddressFamily.AF_INET) -> list[ResolveResult]:
        results = await super().resolve(host, port, family)
        if not results or any(not _public(result["host"]) for result in results):
            raise CitationError("host resolves to a non-public address")
        return results


async def fetch_public(url: str) -> bytes:
    connector = aiohttp.TCPConnector(resolver=PublicResolver(), use_dns_cache=False)
    timeout = aiohttp.ClientTimeout(total=12)
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout, trust_env=False,
                                         headers={"User-Agent": "TelegramDocumentTools/2.0 (citation metadata)"}) as client:
            current = url
            for _ in range(5):
                check_url(current)
                async with client.get(current, allow_redirects=False) as response:
                    if response.status in {301, 302, 303, 307, 308}:
                        location = response.headers.get("Location")
                        if not location:
                            raise CitationError("redirect has no location")
                        current = urljoin(current, location)
                        continue
                    if response.status != 200:
                        raise CitationError("metadata not found")
                    if response.content_length and response.content_length > MAX_RESPONSE:
                        raise CitationError("response too large")
                    data = bytearray()
                    async for chunk in response.content.iter_chunked(64 * 1024):
                        data.extend(chunk)
                        if len(data) > MAX_RESPONSE:
                            raise CitationError("response too large")
                    return bytes(data)
            raise CitationError("too many redirects")
    except (aiohttp.ClientError, TimeoutError, OSError) as e:
        raise CitationError("metadata service unavailable") from e


@dataclass(slots=True)
class Author:
    family: str
    given: str = ""

    def initials(self) -> str:
        return " ".join(f"{part[0]}." for part in self.given.replace("-", " ").split() if part)

    def inverted(self, short: bool = False) -> str:
        given = self.initials() if short else self.given
        return f"{self.family}, {given}" if given else self.family

    def full(self) -> str:
        return f"{self.given} {self.family}".strip()


@dataclass(slots=True)
class Reference:
    title: str
    authors: list[Author] = field(default_factory=list)
    year: str = "n.d."
    container: str = ""
    publisher: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    url: str = ""
    kind: str = "article"


def _clean(value: Any) -> str:
    if not isinstance(value, str | int | float):
        return ""
    return re.sub(r"\s+", " ", str(value or "")).strip()[:1000]


def _records(value: Any) -> list[dict[str, Any]]:
    return [item for item in value[:100] if isinstance(item, dict)] if isinstance(value, list) else []


def _first(value: Any) -> str:
    return _clean(value[0]) if isinstance(value, list) and value else _clean(value)


def crossref_reference(data: dict[str, Any]) -> Reference:
    if not isinstance(data, dict):
        raise CitationError("invalid Crossref response")
    item = data.get("message", data)
    if not isinstance(item, dict):
        raise CitationError("invalid Crossref response")
    title = _first(item.get("title"))
    if not title:
        raise CitationError("missing title")
    year = "n.d."
    for key in ("published-print", "published-online", "published", "issued"):
        date = item.get(key)
        parts = date.get("date-parts") if isinstance(date, dict) else None
        if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0] and re.fullmatch(r"\d{4}", str(parts[0][0])):
            year = str(parts[0][0])
            break
    authors = [Author(_clean(a.get("family") or a.get("name")), _clean(a.get("given")))
               for a in _records(item.get("author")) if _clean(a.get("family") or a.get("name"))]
    doi = _clean(item.get("DOI"))
    return Reference(title=title, authors=authors, year=year,
                     container=_first(item.get("container-title")),
                     publisher=_clean(item.get("publisher")), volume=_clean(item.get("volume")),
                     issue=_clean(item.get("issue")), pages=_clean(item.get("page")),
                     url=f"https://doi.org/{doi}" if doi else _clean(item.get("URL")),
                     kind="book" if item.get("type") in {"book", "monograph", "edited-book"} else "article")


def _person(name: str) -> Author:
    if "," in name:
        family, given = name.split(",", 1)
        return Author(family.strip(), given.strip())
    parts = name.split()
    return Author(parts[-1] if parts else "", " ".join(parts[:-1]))


def openlibrary_reference(data: dict[str, Any], isbn: str) -> Reference:
    if not isinstance(data, dict):
        raise CitationError("invalid OpenLibrary response")
    item = data.get(f"ISBN:{isbn}")
    if not isinstance(item, dict) or not _clean(item.get("title")):
        raise CitationError("ISBN not found")
    year_match = re.search(r"\b(?:1[0-9]{3}|20[0-9]{2})\b", str(item.get("publish_date", "")))
    return Reference(title=_clean(item["title"]),
                     authors=[_person(_clean(a.get("name"))) for a in _records(item.get("authors")) if _clean(a.get("name"))],
                     year=year_match.group() if year_match else "n.d.",
                     publisher=", ".join(_clean(p.get("name")) for p in _records(item.get("publishers")) if _clean(p.get("name"))),
                     url=_clean(item.get("url")), kind="book")


class PageMetadata(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, list[str]] = {}
        self.title: list[str] = []
        self.in_title = False

    def unknown_decl(self, data: str) -> None:
        # HTMLParser silently ignores arbitrary marked declarations on some Python versions.
        # Keep legacy conditional comments readable, but reject unsupported declaration syntax.
        value = data.strip().casefold()
        if value.startswith("if ") or value == "endif":
            return
        raise ValueError("unsupported page declaration")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() == "meta":
            name = (attributes.get("name") or attributes.get("property") or "").lower()
            content = attributes.get("content")
            if name and content:
                self.meta.setdefault(name, []).append(content)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title.append(data)

    def first(self, *names: str) -> str:
        return next((_clean(self.meta[name][0]) for name in names if self.meta.get(name)), "")


def page_reference(data: bytes, url: str) -> Reference:
    parser = PageMetadata()
    try:
        parser.feed(data.decode("utf-8", errors="replace"))
        parser.close()
    except (ValueError, AssertionError) as e:
        raise CitationError("invalid page metadata") from e
    title = parser.first("citation_title", "og:title", "dc.title") or _clean("".join(parser.title))
    if not title:
        raise CitationError("page has no title")
    authors = parser.meta.get("citation_author") or parser.meta.get("author") or parser.meta.get("dc.creator") or []
    date = parser.first("citation_publication_date", "article:published_time", "date", "dc.date")
    year = re.search(r"\b(?:1[0-9]{3}|20[0-9]{2})\b", date)
    return Reference(title, [_person(_clean(a)) for a in authors], year.group() if year else "n.d.",
                     container=parser.first("citation_journal_title", "og:site_name") or urlsplit(url).hostname or "",
                     publisher=parser.first("citation_publisher"), url=url, kind="web")


def _join_authors(values: list[str], conjunction: str = "and") -> str:
    if len(values) < 2:
        return values[0] if values else ""
    if len(values) == 2:
        return f"{values[0]} {conjunction} {values[1]}"
    return ", ".join(values[:-1]) + f", {conjunction} {values[-1]}"


def format_citations(ref: Reference, *, accessed: datetime | None = None) -> dict[str, str]:
    """Format available fields without inventing authors, dates, pages, or publishers."""
    title, container, publisher = esc(ref.title[:300]), esc(ref.container[:120]), esc(ref.publisher[:120])
    authors = [Author(a.family[:50], a.given[:40]) for a in ref.authors[:20]]
    apa_author = _join_authors([esc(a.inverted(True)) for a in authors], "&amp;")
    harvard_author = _join_authors([esc(a.inverted(True)) for a in authors])
    if len(authors) > 2:
        mla_author = f"{esc(authors[0].inverted())}, et al."
    elif len(authors) == 2:
        mla_author = f"{esc(authors[0].inverted())}, and {esc(authors[1].full())}"
    else:
        mla_author = esc(authors[0].inverted()) if authors else ""
    chicago_author = _join_authors([esc(a.inverted()) if i == 0 else esc(a.full())
                                   for i, a in enumerate(authors)])
    location = esc(ref.url[:600])
    year = esc(ref.year[:16])
    volume, issue, pages = esc(ref.volume[:30]), esc(ref.issue[:30]), esc(ref.pages[:80].replace("-", "–"))
    apa_tail = f"<i>{container}{', ' + volume if volume else ''}</i>" if container else ""
    if issue:
        apa_tail += f"({issue})"
    if pages:
        apa_tail += f", {pages}"
    mla_tail = ", ".join(part for part in [f"<i>{container}</i>" if container else "",
                                          f"vol. {volume}" if volume else "",
                                          f"no. {issue}" if issue else "", year,
                                          f"pp. {pages}" if pages else ""] if part)
    chicago_tail = f"<i>{container}</i>" if container else ""
    if volume:
        chicago_tail += f" {volume}"
    if issue:
        chicago_tail += f", no. {issue}"
    chicago_tail += f" ({year})"
    if pages:
        chicago_tail += f": {pages}"
    if ref.kind == "book":
        apa = (f"{apa_author}. ({year}). <i>{title}</i>. {publisher}." if apa_author
               else f"<i>{title}</i>. ({year}). {publisher}.")
        mla = f"{mla_author + '. ' if mla_author else ''}<i>{title}</i>. {publisher + ', ' if publisher else ''}{year}."
        harvard = (f"{harvard_author} ({year}) <i>{title}</i>. {publisher}." if harvard_author
                   else f"<i>{title}</i> ({year}). {publisher}.")
        chicago = f"{chicago_author + '. ' if chicago_author else ''}<i>{title}</i>. {publisher + ', ' if publisher else ''}{year}."
    elif ref.kind == "web":
        apa = (f"{apa_author}. ({year}). <i>{title}</i>. {container}." if apa_author
               else f"<i>{title}</i>. ({year}). {container}.")
        mla = f'{mla_author + ". " if mla_author else ""}“{title}.” <i>{container}</i>, {year}.'
        harvard = (f"{harvard_author} ({year}) <i>{title}</i>. {container}." if harvard_author
                   else f"<i>{title}</i> ({year}). {container}.")
        chicago = f'{chicago_author + ". " if chicago_author else ""}“{title}.” {container}. {year}.'
    else:
        apa = (f"{apa_author}. ({year}). {title}. {apa_tail}." if apa_author
               else f"{title}. ({year}). {apa_tail}.")
        mla = f'{mla_author + ". " if mla_author else ""}“{title}.” {mla_tail}.'
        harvard = (f"{harvard_author} ({year}) ‘{title}’, {apa_tail}." if harvard_author
                   else f"‘{title}’ ({year}), {apa_tail}.")
        chicago = f'{chicago_author + ". " if chicago_author else ""}“{title}.” {chicago_tail}.'
    citations = dict(zip(STYLES, [apa, mla, harvard, chicago], strict=True))
    access_date = (accessed or datetime.now(UTC)).strftime("%d %B %Y")
    for style in STYLES:
        if location:
            citations[style] += f" {location}."
        if ref.kind == "web" and style in {"Harvard", "Chicago"}:
            citations[style] += f" (Accessed: {access_date})."
        citations[style] = citations[style].replace(". .", ".").replace(".. ", ". ").strip()
    return citations


class _PlainCitation(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def plain_citation(value: str) -> str:
    parser = _PlainCitation()
    parser.feed(value)
    return "".join(parser.parts)


def bounded_citation(value: str, limit: int = 3800) -> str:
    """Bound HTML without cutting an entity or leaving an italic tag open."""
    if len(value) <= limit:
        return value
    plain = plain_citation(value)
    parts: list[str] = []
    size = 0
    for character in plain:
        escaped = html.escape(character)
        if size + len(escaped) > limit - 1:
            return "".join(parts) + "…"
        parts.append(escaped)
        size += len(escaped)
    return "".join(parts)


def classify(value: str) -> tuple[str, str]:
    value = value.strip()[:2048]
    doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value, flags=re.I)
    if DOI_RE.fullmatch(doi):
        return "doi", doi
    isbn = re.sub(r"[\s-]", "", re.sub(r"^isbn(?:-1[03])?\s*:?\s*", "", value, flags=re.I)).upper()
    if re.fullmatch(r"\d{9}[\dX]", isbn):
        if sum((10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(isbn)) % 11 == 0:
            return "isbn", isbn
    elif (re.fullmatch(r"\d{13}", isbn)
          and sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(isbn)) % 10 == 0):
        return "isbn", isbn
    if value.startswith(("http://", "https://")):
        check_url(value)
        return "url", value
    raise CitationError("send a DOI, ISBN, or public URL")


class CitationService:
    def __init__(self, ctx: BotContext, fetch: Callable[[str], Awaitable[bytes]] = fetch_public) -> None:
        self.ctx = ctx
        self.fetch = fetch

    async def lookup(self, value: str) -> Reference:
        kind, value = classify(value)
        key = self.ctx.keys("dt", "citation", hashlib.sha256(f"{kind}:{value}".encode()).hexdigest())
        cached = await self.ctx.redis.get(key)
        if cached:
            try:
                item = json.loads(cached)
                if not isinstance(item, dict) or not isinstance(item.get("authors"), list):
                    raise CitationError("invalid cached reference")
                item["authors"] = [Author(**author) for author in item["authors"]]
                ref = Reference(**item)
                if (not all(isinstance(getattr(ref, name), str) for name in ("title", "year", "container", "publisher", "volume", "issue", "pages", "url", "kind"))
                        or not all(isinstance(author.family, str) and isinstance(author.given, str) for author in ref.authors)):
                    raise CitationError("invalid cached fields")
                return ref
            except (ValueError, KeyError, TypeError, AttributeError):
                await self.ctx.redis.delete(key)
        try:
            async with asyncio.timeout(15):
                if kind == "doi":
                    # Crossref's documented /works/{doi} endpoint.
                    raw = await self.fetch(f"https://api.crossref.org/works/{quote(value, safe='')}")
                    ref = crossref_reference(json.loads(raw))
                elif kind == "isbn":
                    raw = await self.fetch(f"https://openlibrary.org/api/books?bibkeys=ISBN:{value}&format=json&jscmd=data")
                    ref = openlibrary_reference(json.loads(raw), value)
                else:
                    ref = page_reference(await self.fetch(value), value)
        except (ValueError, KeyError, TypeError, AttributeError, IndexError, TimeoutError) as e:
            raise CitationError("metadata not available") from e
        await self.ctx.redis.set(key, json.dumps(asdict(ref)), ex=86400)
        return ref
