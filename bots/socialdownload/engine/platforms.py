"""Platform detection and URL normalization (normalized URLs make cache keys stable)."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

URL_RE = re.compile(r"https?://[^\s<>\"'`]+", re.IGNORECASE)
# Bare domains like "vm.tiktok.com/xyz" or "youtu.be/xyz" without scheme.
BARE_RE = re.compile(
    r"(?<![\w/@.])((?:www\.|m\.|vm\.|vt\.)?(?:[a-z0-9-]+\.)*"
    r"(?:tiktok\.com|instagram\.com|youtube\.com|youtu\.be|x\.com|twitter\.com|facebook\.com|fb\.watch"
    r"|reddit\.com|redd\.it|pinterest\.com|pin\.it|threads\.net|threads\.com|soundcloud\.com|vimeo\.com)"
    r"/[^\s<>\"'`]*)",
    re.IGNORECASE,
)

PLATFORM_HOSTS: dict[str, tuple[str, ...]] = {
    "tiktok": ("tiktok.com",),
    "instagram": ("instagram.com", "instagr.am"),
    "youtube": ("youtube.com", "youtu.be", "youtube-nocookie.com"),
    "twitter": ("twitter.com", "x.com", "fxtwitter.com", "vxtwitter.com"),
    "facebook": ("facebook.com", "fb.watch", "fb.com"),
    "reddit": ("reddit.com", "redd.it"),
    "pinterest": ("pinterest.com", "pin.it"),
    "threads": ("threads.net", "threads.com"),
    "snapchat": ("snapchat.com",),
    "soundcloud": ("soundcloud.com",),
    "vimeo": ("vimeo.com",),
    "twitch": ("twitch.tv",),
    "dailymotion": ("dailymotion.com", "dai.ly"),
    "likee": ("likee.video", "l.likee.video"),
    "vk": ("vk.com", "vkvideo.ru", "vk.ru"),
    "bilibili": ("bilibili.com", "b23.tv"),
    "linkedin": ("linkedin.com",),
    "tumblr": ("tumblr.com",),
    "kwai": ("kwai.com",),
    "rutube": ("rutube.ru",),
}

PLATFORM_EMOJI = {
    "tiktok": "🎵", "instagram": "📸", "youtube": "▶️", "twitter": "𝕏", "facebook": "📘",
    "reddit": "👽", "pinterest": "📌", "threads": "🧵", "snapchat": "👻", "soundcloud": "☁️",
    "vimeo": "🎬", "twitch": "🟣", "dailymotion": "🎞", "other": "🌐",
}

# Long-form platforms: show the quality picker by default.
LONG_FORM = frozenset({"youtube", "vimeo", "twitch", "dailymotion", "bilibili", "rutube", "vk"})
# Audio-first platforms.
AUDIO_FIRST = frozenset({"soundcloud"})
# Hosts using short redirecting links that should be expanded before caching.
SHORT_HOSTS = ("vm.tiktok.com", "vt.tiktok.com", "pin.it", "fb.watch", "redd.it", "b23.tv", "dai.ly",
               "on.soundcloud.com")

# Tracking parameters: either a known prefix (utm_*, share_*) or an exact name. Anchored on both ends so
# meaningful parameters that merely *start* with the same letters (season, token, type, ...) survive.
_TRACKING = re.compile(
    r"^(?:utm_\w*|share_\w*|igsh|igshid|si|feature|fbclid|gclid|dclid|msclkid|yclid|ref|ref_src|ref_url|_r"
    r"|is_from_webapp|sender_device|mibextid|rdid|context|pp|s|t|_t|xmt|sharer_id)$",
    re.IGNORECASE,
)
_YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_urls(text: str | None, limit: int = 5) -> list[str]:
    if not text:
        return []
    found: list[str] = []
    for m in URL_RE.finditer(text):
        found.append(m.group(0).rstrip(".,!?)]}»"))
    for m in BARE_RE.finditer(text):
        bare_url = "https://" + m.group(1).rstrip(".,!?)]}»")
        # Ensure we don't add bare URL if it was already part of an http(s) URL
        if not any(bare_url.split("://", 1)[1] in existing for existing in found):
            found.append(bare_url)
    out: list[str] = []
    for u in found:
        if u not in out:
            out.append(u)
    return out[:limit]


def _host(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    for prefix in ("www.", "m.", "mobile.", "music.", "web."):
        if host.startswith(prefix):
            host = host[len(prefix):]
    return host


def detect_platform(url: str) -> str:
    host = _host(url)
    for platform, hosts in PLATFORM_HOSTS.items():
        for h in hosts:
            if host == h or host.endswith("." + h):
                return platform
    return "other"


def is_short_link(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in SHORT_HOSTS or (host.endswith("tiktok.com") and urlparse(url).path.startswith("/t/"))


def is_playlist(url: str) -> bool:
    p = urlparse(url)
    if detect_platform(url) == "youtube":
        qs = parse_qs(p.query)
        return p.path.startswith("/playlist") or ("list" in qs and "v" not in qs and "/watch" not in p.path)
    if detect_platform(url) == "soundcloud":
        return "/sets/" in p.path
    return False


def _clean_query(query: str, keep: tuple[str, ...] = ()) -> str:
    qs = parse_qs(query, keep_blank_values=False)
    kept = {k: v[0] for k, v in qs.items() if (k in keep) or (not keep and not _TRACKING.match(k))}
    if keep:
        kept = {k: v for k, v in kept.items() if k in keep}
    return urlencode(sorted(kept.items()))


def normalize_url(url: str) -> str:
    """Return a canonical form of `url` (tracking params stripped, mirrors unified)."""
    url = url.strip()
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    p = urlparse(url)
    host = _host(url)
    path = re.sub(r"/{2,}", "/", p.path or "/")
    platform = detect_platform(url)

    if platform == "youtube":
        qs = parse_qs(p.query)
        vid = None
        if host == "youtu.be":
            vid = path.strip("/").split("/")[0]
        elif "v" in qs:
            vid = qs["v"][0]
        else:
            m = re.match(r"^/(?:shorts|embed|live|v|e)/([A-Za-z0-9_-]{11})", path)
            if m:
                vid = m.group(1)
        if vid and _YT_ID.match(vid):
            return f"https://www.youtube.com/watch?v={vid}"
        if "list" in qs:
            return f"https://www.youtube.com/playlist?list={qs['list'][0]}"
        return urlunparse(("https", "www.youtube.com", path.rstrip("/") or "/", "", p.query, ""))

    if platform == "twitter":
        m = re.search(r"/status(?:es)?/(\d+)", path)
        if m:
            return f"https://x.com/i/status/{m.group(1)}"
        return f"https://x.com{path.rstrip('/')}"

    if platform == "instagram":
        path = re.sub(r"^/reels/", "/reel/", path)
        # /username/p/ID and /username/reel/ID -> /p/ID and /reel/ID
        m = re.search(r"/(p|reel|tv|stories/[^/]+)/([^/?#]+)", path)
        if m:
            path = f"/{m.group(1)}/{m.group(2)}/"
        return f"https://www.instagram.com{path}"

    if platform == "tiktok":
        canonical_host = host if host in ("vm.tiktok.com", "vt.tiktok.com") else "www.tiktok.com"
        return f"https://{canonical_host}{path.rstrip('/')}"

    if platform == "facebook":
        query = _clean_query(p.query, keep=("v", "story_fbid", "id", "fbid"))
        return urlunparse(("https", "www.facebook.com" if host != "fb.watch" else host,
                           path.rstrip("/") or "/", "", query, ""))

    if platform == "reddit":
        return f"https://www.reddit.com{path.rstrip('/')}" if host != "redd.it" else f"https://redd.it{path}"

    query = _clean_query(p.query)
    netloc = p.netloc.lower()
    return urlunparse(("https", netloc, path.rstrip("/") or "/", "", query, ""))
