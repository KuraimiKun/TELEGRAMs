"""Network helpers: SSRF guard, short-link expansion, proxy pool with health scoring, cookie rotation."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import ipaddress
import os
import random
import re
import socket
import tempfile
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import aiohttp
from redis.asyncio import Redis

from core.log import get_logger
from core.redis import KeySpace

log = get_logger(__name__)

FAIL_WINDOW = 600  # seconds a failure counts against a proxy / cookie file
MAX_COOKIE_BYTES = 1024 * 1024
PLATFORM_NAME_RE = re.compile(r"^[a-z0-9]{2,20}$")


# ---------------------------------------------------------------------------------------- SSRF guard
class UnsafeURL(ValueError):
    """The URL points at a non-public address (loopback, private network, cloud metadata, ...)."""


def _is_public_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


async def assert_public_url(url: str) -> None:
    """Reject URLs whose host is not a public internet address.

    Stops users from making the workers fetch internal services (Redis, Postgres, the Bot API server,
    cloud metadata at 169.254.169.254, ...). Hostnames are resolved and *every* address must be public.
    """
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise UnsafeURL(f"scheme not allowed: {parts.scheme}")
    host = (parts.hostname or "").strip(".").lower()
    if not host:
        raise UnsafeURL("missing host")
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        if not _is_public_ip(literal):
            raise UnsafeURL(f"non-public address: {host}")
        return
    if "." not in host or host == "localhost" or host.endswith((".localhost", ".local", ".internal", ".lan")):
        raise UnsafeURL(f"non-public hostname: {host}")
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(host, parts.port or 443, type=socket.SOCK_STREAM)
    except OSError as e:
        raise UnsafeURL(f"cannot resolve {host}: {e}") from e
    for info in infos:
        addr = ipaddress.ip_address(info[4][0])
        if not _is_public_ip(addr):
            raise UnsafeURL(f"{host} resolves to non-public address {addr}")


async def expand_short_link(url: str, max_hops: int = 5, timeout: float = 6.0) -> str:
    """Follow redirects of short links (vm.tiktok.com, pin.it, ...) so equal media share one cache key.

    Every hop is SSRF-checked. On any failure the original URL is returned unchanged.
    """
    current = url
    try:
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=client_timeout) as session:
            for _ in range(max_hops):
                await assert_public_url(current)
                async with session.head(current, allow_redirects=False) as resp:
                    location = resp.headers.get("Location")
                    if resp.status not in (301, 302, 303, 307, 308) or not location:
                        return current
                    current = urljoin(current, location)
    except UnsafeURL:
        raise
    except Exception as e:
        log.debug("short_link_expand_failed", url=url, error=str(e))
        return url
    return current


# ---------------------------------------------------------------------------------------- proxies
def _pid(value: str) -> str:
    return hashlib.md5(value.encode(), usedforsecurity=False).hexdigest()[:10]


def mask_proxy(proxy: str) -> str:
    if "@" in proxy:
        scheme, rest = proxy.split("://", 1) if "://" in proxy else ("http", proxy)
        return f"{scheme}://***@{rest.split('@', 1)[1]}"
    return proxy


class ProxyPool:
    """Weighted-random proxy selection; proxies that recently failed get picked less.

    Proxies come from env (static) plus an optional admin-managed file (one per line).
    """

    def __init__(
        self,
        redis: Redis,
        proxies: list[str],
        file: Path | None = None,
        keys: KeySpace | None = None,
    ) -> None:
        self.redis = redis
        self._static = list(proxies)
        self._file = file
        self.keys = keys or KeySpace("socialdownload")

    def _fail_key(self, proxy: str) -> str:
        return self.keys("proxy", "fail", _pid(proxy))

    def all(self) -> list[str]:
        proxies = list(self._static)
        for line in self._file_entries():
            if line not in proxies:
                proxies.append(line)
        return proxies

    def _file_entries(self) -> list[str]:
        if not self._file or not self._file.exists():
            return []
        return [
            line.strip()
            for line in self._file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    def add(self, proxy: str) -> bool:
        if not self._file or not re.match(r"^(https?|socks5h?)://\S+$", proxy) or proxy in self.all():
            return False
        self._file.parent.mkdir(parents=True, exist_ok=True)
        with self._file.open("a", encoding="utf-8") as f:
            f.write(proxy + "\n")
        return True

    def remove(self, index: int) -> bool:
        """Remove a file-managed proxy by its index in :meth:`all` (env proxies are read-only)."""
        proxies = self.all()
        if not self._file or not (0 <= index < len(proxies)) or proxies[index] in self._static:
            return False
        target = proxies[index]
        remaining = [p for p in self._file_entries() if p != target]
        self._file.write_text("".join(p + "\n" for p in remaining), encoding="utf-8")
        return True

    async def acquire(self, exclude: set[str] | None = None) -> str | None:
        proxies = [p for p in self.all() if p not in (exclude or set())]
        if not proxies:
            return None
        fails = await self.redis.mget([self._fail_key(p) for p in proxies])
        weights = [1.0 / (1 + int(f or 0)) ** 2 for f in fails]
        return random.choices(proxies, weights=weights, k=1)[0]

    async def report(self, proxy: str | None, ok: bool) -> None:
        if not proxy:
            return
        key = self._fail_key(proxy)
        if ok:
            await self.redis.delete(key)
        else:
            async with self.redis.pipeline(transaction=False) as pipe:
                pipe.incr(key)
                pipe.expire(key, FAIL_WINDOW)
                await pipe.execute()

    async def reset(self) -> None:
        for p in self.all():
            await self.redis.delete(self._fail_key(p))

    async def health(self) -> list[tuple[str, int]]:
        proxies = self.all()
        if not proxies:
            return []
        fails = await self.redis.mget([self._fail_key(p) for p in proxies])
        return [(mask_proxy(p), int(f or 0)) for p, f in zip(proxies, fails, strict=True)]


# ---------------------------------------------------------------------------------------- cookies
def validate_cookie_file(content: bytes) -> str | None:
    """Return an error message if ``content`` is not a Netscape cookies.txt, else None."""
    if not content or len(content) > MAX_COOKIE_BYTES:
        return "file is empty or larger than 1 MB"
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return "file is not UTF-8 text"
    rows = [
        ln
        for ln in text.splitlines()
        if ln.strip() and (not ln.startswith("#") or ln.startswith("#HttpOnly_"))
    ]
    if not rows:
        return "no cookies found"
    if not all(len(ln.split("\t")) == 7 for ln in rows):
        return "not in Netscape cookies.txt format (7 tab-separated fields per line)"
    return None


class CookieJar:
    """Cookie files live in ``<cookies_dir>/<platform>_<id>.txt``; picked randomly, failures weighted down.

    yt-dlp rewrites its cookie file on exit, so every download gets a private temporary copy
    (:meth:`checkout`) — concurrent workers never write to the shared originals.
    """

    def __init__(self, directory: Path, redis: Redis | None = None, keys: KeySpace | None = None) -> None:
        self.dir = directory
        self.redis = redis
        self.keys = keys or KeySpace("socialdownload")

    def files(self, platform: str) -> list[Path]:
        if not self.dir.exists():
            return []
        return sorted(
            p
            for p in self.dir.glob("*.txt")
            if p.stem.split("_")[0] == platform and p.stat().st_size > 0
        )

    async def pick(self, platform: str) -> Path | None:
        files = self.files(platform)
        if not files:
            return None
        if self.redis is None:
            return random.choice(files)
        fails = await self.redis.mget([self.keys("cookie", "fail", p.name) for p in files])
        weights = [1.0 / (1 + int(f or 0)) ** 2 for f in fails]
        return random.choices(files, weights=weights, k=1)[0]

    def checkout(self, original: Path | None) -> str | None:
        """Copy a cookie file to a private temp file (0600). Caller must :meth:`release` it."""
        if original is None:
            return None
        fd, tmp = tempfile.mkstemp(prefix="ck_", suffix=".txt")
        with os.fdopen(fd, "wb") as f:
            f.write(original.read_bytes())
        return tmp

    @staticmethod
    def release(tmp: str | None) -> None:
        if tmp:
            with contextlib.suppress(OSError):
                os.unlink(tmp)

    async def report(self, original: Path | None, ok: bool) -> None:
        if original is None or self.redis is None:
            return
        key = self.keys("cookie", "fail", original.name)
        if ok:
            await self.redis.delete(key)
        else:
            async with self.redis.pipeline(transaction=False) as pipe:
                pipe.incr(key)
                pipe.expire(key, FAIL_WINDOW * 6)
                await pipe.execute()

    def save(self, platform: str, content: bytes) -> Path:
        if not PLATFORM_NAME_RE.match(platform):
            raise ValueError("invalid platform name")
        error = validate_cookie_file(content)
        if error:
            raise ValueError(error)
        self.dir.mkdir(parents=True, exist_ok=True)
        path = self.dir / f"{platform}_{int(time.time())}_{random.randint(100, 999)}.txt"
        tmp = path.with_suffix(".part")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        os.replace(tmp, path)
        return path

    def delete(self, name: str) -> bool:
        path = (self.dir / name).resolve()
        if path.parent != self.dir.resolve() or path.suffix != ".txt" or not path.exists():
            return False
        path.unlink()
        return True

    def clear(self, platform: str) -> int:
        files = self.files(platform)
        for f in files:
            f.unlink(missing_ok=True)
        return len(files)

    def summary(self) -> dict[str, int]:
        if not self.dir.exists():
            return {}
        out: dict[str, int] = {}
        for p in self.dir.glob("*.txt"):
            platform = p.stem.split("_")[0]
            out[platform] = out.get(platform, 0) + 1
        return out

    def listing(self) -> list[Path]:
        return sorted(self.dir.glob("*.txt")) if self.dir.exists() else []
