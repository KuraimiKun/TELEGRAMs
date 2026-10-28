"""yt-dlp / gallery-dl powered extraction and download engine."""

from __future__ import annotations

import asyncio
import contextlib
import shutil
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yt_dlp
from yt_dlp.utils import DownloadCancelled, DownloadError, ExtractorError

from bots.socialdownload.engine.errors import RETRYABLE, Cancelled, DownloadFailed, classify_error
from bots.socialdownload.engine.network import CookieJar, ProxyPool
from core.log import get_logger

log = get_logger(__name__)

VIDEO_EXT = {".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi", ".flv", ".ts", ".3gp"}
AUDIO_EXT = {".mp3", ".m4a", ".aac", ".opus", ".ogg", ".oga", ".flac", ".wav"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
GIF_EXT = {".gif"}
GALLERY_FALLBACK_PLATFORMS = {"instagram", "twitter", "tiktok", "pinterest", "reddit", "threads", "tumblr",
                              "facebook", "other"}


@dataclass(slots=True)
class MediaInfo:
    id: str
    title: str
    url: str
    extractor: str
    uploader: str | None = None
    duration: int | None = None
    thumbnail: str | None = None
    heights: list[int] = field(default_factory=list)
    sizes: dict[int, int] = field(default_factory=dict)
    audio_size: int | None = None
    is_live: bool = False
    is_playlist: bool = False
    entries_count: int = 0


@dataclass(slots=True)
class SearchResult:
    id: str
    title: str
    url: str
    duration: int | None
    channel: str | None


@dataclass(slots=True)
class Progress:
    """Mutable progress state shared between the download thread and the progress reporter."""

    stage: str = "download"
    downloaded: int = 0
    total: int = 0
    speed: float = 0.0
    eta: int | None = None
    item: int = 1
    updated: float = field(default_factory=time.monotonic)


@dataclass(slots=True)
class DownloadOutput:
    files: list[Path]
    title: str = ""
    uploader: str | None = None
    webpage_url: str = ""
    duration: int | None = None


def _format_selector(kind: str, max_height: int, audio_format: str) -> str:
    if kind == "audio":
        return "bestaudio[ext=m4a]/bestaudio/best" if audio_format == "m4a" else "bestaudio/best"
    # Resolution is capped through format_sort (`res:<h>` uses the *smaller* dimension, so vertical
    # 1080x1920 counts as 1080p). Height filters would mis-handle vertical videos.
    return "bv*+ba/b"


def _format_sort(kind: str, max_height: int) -> list[str]:
    if kind == "audio":
        return ["acodec:aac", "abr"]
    return [f"res:{max_height}", "vcodec:h264", "acodec:aac", "ext:mp4:m4a"]


# Keep this much free space beyond the expected download (merging needs ~2x the size).
DISK_HEADROOM = 512 * 1024 * 1024


def _estimate_size(info: dict) -> int:
    size = info.get("filesize") or info.get("filesize_approx")
    if size:
        return int(size)
    total = 0
    for f in info.get("requested_formats") or []:
        total += int(f.get("filesize") or f.get("filesize_approx") or 0)
    return total


class DownloadEngine:
    def __init__(
        self,
        proxies: ProxyPool,
        cookies: CookieJar,
        pot_provider_url: str | None = None,
        max_threads: int = 16,
        **kwargs: Any,
    ) -> None:
        self.proxies = proxies
        self.cookies = cookies
        self.pot_url = pot_provider_url or kwargs.get("pot_url")
        self._sem = asyncio.Semaphore(max_threads)

    # ------------------------------------------------------------------ options
    def _base_opts(self, platform: str, proxy: str | None, cookiefile: str | None) -> dict[str, Any]:
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "noplaylist": True,
            "socket_timeout": 20,
            "retries": 3,
            "fragment_retries": 5,
            "extractor_retries": 2,
            "concurrent_fragment_downloads": 4,
            "geo_bypass": True,
            "restrictfilenames": True,
            "windowsfilenames": True,
            "trim_file_name": 60,
            "overwrites": True,
            "cachedir": False,
            "logger": _QuietLogger(),
        }
        if proxy:
            opts["proxy"] = proxy
        if cookiefile:
            opts["cookiefile"] = cookiefile
        extractor_args: dict[str, dict[str, list[str]]] = {}
        if self.pot_url and platform == "youtube":
            extractor_args["youtubepot-bgutilhttp"] = {"base_url": [self.pot_url]}
        if extractor_args:
            opts["extractor_args"] = extractor_args
        return opts

    async def _run(self, fn, *args):
        async with self._sem:
            return await asyncio.to_thread(fn, *args)

    async def _with_retries(self, platform: str, attempt_fn, attempts: int = 3):
        """Run attempt_fn(proxy, cookiefile) rotating proxies/cookies on retryable errors."""
        tried: set[str] = set()
        last: DownloadFailed | None = None
        for attempt in range(attempts):
            proxy = await self.proxies.acquire(exclude=tried)
            cookie_src = await self.cookies.pick(platform)
            cookiefile = self.cookies.checkout(cookie_src)
            try:
                result = await attempt_fn(proxy, cookiefile)
                await self.proxies.report(proxy, ok=True)
                await self.cookies.report(cookie_src, ok=True)
                return result
            except DownloadFailed as e:
                last = e
                log.warning("download_attempt_failed", platform=platform, attempt=attempt + 1, code=e.code,
                            detail=e.detail[:300])
                if e.code == "login":
                    await self.cookies.report(cookie_src, ok=False)
                if e.code not in RETRYABLE:
                    raise
                await self.proxies.report(proxy, ok=False)
                if proxy:
                    tried.add(proxy)
                elif e.code not in ("timeout", "rate_limited") and not (
                    e.code == "login" and len(self.cookies.files(platform)) > 1
                ):
                    break  # nothing left to rotate and not transient
                await asyncio.sleep(1.5 * (attempt + 1))
            finally:
                self.cookies.release(cookiefile)
        assert last is not None
        raise last

    # ------------------------------------------------------------------ extract
    async def extract(self, url: str, platform: str, playlist: bool = False) -> MediaInfo:
        async def attempt(proxy, cookiefile):
            opts = self._base_opts(platform, proxy, cookiefile)
            if playlist:
                opts.update(noplaylist=False, extract_flat="in_playlist", playlistend=500)
            return await self._run(_extract_sync, url, opts)

        info = await self._with_retries(platform, attempt)
        return _to_media_info(info, url)

    async def search(self, query: str, limit: int = 6) -> list[SearchResult]:
        async def attempt(proxy, cookiefile):
            opts = self._base_opts("youtube", proxy, cookiefile)
            opts.update(extract_flat=True, noplaylist=False)
            return await self._run(_extract_sync, f"ytsearch{limit}:{query}", opts)

        info = await self._with_retries("youtube", attempt, attempts=2)
        results = []
        for e in info.get("entries") or []:
            if not e or not e.get("id"):
                continue
            results.append(SearchResult(
                id=e["id"], title=e.get("title") or e["id"],
                url=f"https://www.youtube.com/watch?v={e['id']}",
                duration=int(e["duration"]) if e.get("duration") else None,
                channel=e.get("channel") or e.get("uploader"),
            ))
        return results

    # ------------------------------------------------------------------ download
    async def download(self, *, url: str, platform: str, workdir: Path, kind: str, max_height: int,
                       max_bytes: int, max_duration_s: int, playlist_items: str | None,
                       audio_format: str, progress: Progress, cancel: threading.Event,
                       max_items: int = 10) -> DownloadOutput:
        workdir.mkdir(parents=True, exist_ok=True)
        free = shutil.disk_usage(workdir).free
        if free < min(max_bytes, 4 * 1024**3) * 2 + DISK_HEADROOM:
            log.error("disk_space_low", free_mb=free // (1024 * 1024), needed_mb=max_bytes // (1024 * 1024))
            raise DownloadFailed("busy", f"free={free}")

        async def attempt(proxy, cookiefile):
            _clear_dir(workdir)
            opts = self._base_opts(platform, proxy, cookiefile)
            opts.update(self._download_opts(workdir, kind, max_height, max_bytes, audio_format))
            opts["progress_hooks"] = [_make_hook(progress, cancel)]
            opts["postprocessor_hooks"] = [_make_pp_hook(progress, cancel)]
            if playlist_items:
                opts.update(noplaylist=False, playlist_items=playlist_items, ignoreerrors=True,
                            match_filter=_duration_filter(max_duration_s))
                return await self._run(_download_playlist_sync, url, opts)
            return await self._run(_download_single_sync, url, opts, max_bytes, max_duration_s, max_items)

        try:
            output = await self._with_retries(platform, attempt)
        except DownloadFailed as e:
            fallback = e.code in ("no_media", "unsupported", "unknown") or (
                platform == "instagram" and e.code == "login")
            if not (fallback and platform in GALLERY_FALLBACK_PLATFORMS and kind == "video"):
                raise
            log.info("gallery_dl_fallback", platform=platform, code=e.code)
            output = await self._gallery_dl(url, platform, workdir, playlist_items or f"1-{max_items}",
                                            max_bytes, cancel, progress)

        output.files = collect_media(workdir, kind)
        if not output.files:
            raise DownloadFailed("no_media")
        if not playlist_items and sum(f.stat().st_size for f in output.files) > max_bytes:
            raise DownloadFailed("too_large", "total size of all items")
        return output

    def _download_opts(self, workdir: Path, kind: str, max_height: int, max_bytes: int,
                       audio_format: str) -> dict[str, Any]:
        tmpl = str(workdir / "%(autonumber)03d_%(id).40s.%(ext)s")
        opts: dict[str, Any] = {
            "format": _format_selector(kind, max_height, audio_format),
            "format_sort": _format_sort(kind, max_height),
            "outtmpl": {"default": tmpl},
            "paths": {"home": str(workdir), "temp": str(workdir)},
            "max_filesize": max_bytes,
        }
        if kind == "audio":
            codec = "m4a" if audio_format == "m4a" else "mp3"
            opts.update(
                writethumbnail=True,
                postprocessors=[
                    {"key": "FFmpegExtractAudio", "preferredcodec": codec, "preferredquality": "192"},
                    {"key": "FFmpegThumbnailsConvertor", "format": "jpg", "when": "before_dl"},
                    {"key": "FFmpegMetadata", "add_metadata": True},
                    {"key": "EmbedThumbnail"},
                ],
            )
        else:
            opts.update(
                merge_output_format="mp4",
                postprocessor_args={"merger+ffmpeg_o": ["-movflags", "+faststart"]},
            )
        return opts

    async def _gallery_dl(self, url: str, platform: str, workdir: Path, items: str, max_bytes: int,
                          cancel: threading.Event, progress: Progress) -> DownloadOutput:
        _clear_dir(workdir)
        cmd = [sys.executable, "-m", "gallery_dl", "-q", "--no-mtime", "-D", str(workdir),
               "--range", items, "--filesize-max", f"{max(1, max_bytes // (1024 * 1024))}M"]
        proxy = await self.proxies.acquire()
        if proxy:
            cmd += ["--proxy", proxy]
        cookie_src = await self.cookies.pick(platform)
        cookiefile = self.cookies.checkout(cookie_src)
        if cookiefile:
            cmd += ["--cookies", cookiefile]
        cmd.append(url)
        # stderr goes to a file (not a pipe) so a chatty process can never block on a full pipe buffer.
        with tempfile.TemporaryFile() as errfile:
            async with self._sem:
                proc = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=errfile
                )
                try:
                    deadline = time.monotonic() + 300
                    while proc.returncode is None:
                        if cancel.is_set():
                            raise Cancelled()
                        if time.monotonic() > deadline:
                            raise DownloadFailed("timeout", "gallery-dl timeout")
                        progress.downloaded = sum(p.stat().st_size for p in workdir.rglob("*") if p.is_file())
                        progress.updated = time.monotonic()
                        with contextlib.suppress(TimeoutError):
                            await asyncio.wait_for(proc.wait(), timeout=1)
                finally:
                    if proc.returncode is None:
                        proc.kill()
                        await proc.wait()
                    self.cookies.release(cookiefile)
            errfile.seek(0)
            stderr = errfile.read(4000).decode(errors="ignore")
        if not any(workdir.iterdir()):
            raise DownloadFailed(classify_error(stderr) if stderr else "no_media", stderr[:500])
        return DownloadOutput(files=[], title="", webpage_url=url)


# ---------------------------------------------------------------------- sync helpers (threads)
class _QuietLogger:
    def debug(self, msg: str) -> None:
        pass

    def info(self, msg: str) -> None:
        pass

    def warning(self, msg: str) -> None:
        pass

    def error(self, msg: str) -> None:
        log.debug("ytdlp_error", msg=msg[:500])


def _wrap_errors(fn):
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except DownloadCancelled as e:
            raise Cancelled() from e
        except (DownloadError, ExtractorError) as e:
            msg = str(e)
            raise DownloadFailed(classify_error(msg), msg[:1000]) from e
    return inner


@_wrap_errors
def _extract_sync(url: str, opts: dict) -> dict:
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info is None:
            raise DownloadFailed("no_media")
        return ydl.sanitize_info(info)


@_wrap_errors
def _download_single_sync(url: str, opts: dict, max_bytes: int, max_duration_s: int,
                          max_items: int = 10) -> DownloadOutput:
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info is None:
            raise DownloadFailed("no_media")
        if info.get("_type") == "playlist":
            entries = [e for e in (info.get("entries") or []) if e]
            if not entries:
                raise DownloadFailed("no_media")
            if len(entries) > 1:
                # Multi-item post (carousel / thread) — or a channel/profile URL. Never download more than
                # the plan's item cap, and enforce duration/size limits across *all* items.
                entries = entries[:max_items]
                for e in entries:
                    _check_entry(e, max_duration_s)
                total = sum(_estimate_size(e) for e in entries)
                if total > max_bytes:
                    raise DownloadFailed("too_large", str(total))
                info = {**info, "entries": entries}
                ydl.params["noplaylist"] = False
                ydl.process_ie_result(info, download=True)
                return DownloadOutput(
                    files=[], title=info.get("title") or "", uploader=info.get("uploader") or info.get("channel"),
                    webpage_url=info.get("webpage_url") or url,
                )
            info = entries[0]
        _check_entry(info, max_duration_s)
        duration = info.get("duration")
        size = _estimate_size(info)
        if size and size > max_bytes:
            raise DownloadFailed("too_large", str(size))
        ydl.process_ie_result(info, download=True)
        return DownloadOutput(
            files=[], title=info.get("title") or "", uploader=info.get("uploader") or info.get("channel"),
            webpage_url=info.get("webpage_url") or url,
            duration=int(duration) if duration else None,
        )


def _check_entry(info: dict, max_duration_s: int) -> None:
    if info.get("live_status") in ("is_live", "is_upcoming") or info.get("is_live"):
        raise DownloadFailed("live")
    duration = info.get("duration")
    if duration and max_duration_s and duration > max_duration_s:
        raise DownloadFailed("too_long", str(duration))


@_wrap_errors
def _download_playlist_sync(url: str, opts: dict) -> DownloadOutput:
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            raise DownloadFailed("no_media")
        return DownloadOutput(files=[], title=info.get("title") or "", uploader=info.get("uploader"),
                              webpage_url=info.get("webpage_url") or url)


def _duration_filter(max_duration_s: int):
    def match(info: dict, *, incomplete: bool = False) -> str | None:
        duration = info.get("duration")
        if duration and max_duration_s and duration > max_duration_s:
            return "too long"
        if info.get("live_status") in ("is_live", "is_upcoming"):
            return "live"
        return None
    return match


def _make_hook(progress: Progress, cancel: threading.Event):
    seen: set[str] = set()

    def hook(d: dict) -> None:
        if cancel.is_set():
            raise DownloadCancelled("cancelled by user")
        filename = d.get("filename") or ""
        if d.get("status") == "downloading":
            if filename and filename not in seen:
                seen.add(filename)
                progress.item = max(1, len([s for s in seen if not s.endswith((".part", ".ytdl"))]) or 1)
            progress.stage = "download"
            progress.downloaded = int(d.get("downloaded_bytes") or 0)
            progress.total = int(d.get("total_bytes") or d.get("total_bytes_estimate") or 0)
            progress.speed = float(d.get("speed") or 0)
            progress.eta = int(d["eta"]) if d.get("eta") is not None else None
            progress.updated = time.monotonic()
    return hook


def _make_pp_hook(progress: Progress, cancel: threading.Event):
    def hook(d: dict) -> None:
        if cancel.is_set():
            raise DownloadCancelled("cancelled by user")
        if d.get("status") == "started":
            progress.stage = "process"
            progress.updated = time.monotonic()
    return hook


def _to_media_info(info: dict, url: str) -> MediaInfo:
    is_playlist = info.get("_type") == "playlist"
    heights: set[int] = set()
    sizes: dict[int, int] = {}
    audio_size = None
    formats = info.get("formats") or []
    best_audio = 0
    for f in formats:
        if f.get("vcodec") == "none" and f.get("acodec") not in (None, "none"):
            best_audio = max(best_audio, int(f.get("filesize") or f.get("filesize_approx") or 0))
    for f in formats:
        h = f.get("height")
        if not h or f.get("vcodec") in (None, "none"):
            continue
        h = int(h)
        # Normalize odd heights (e.g. 1012 for vertical, 1080 for 1920x1080).
        std = next((s for s in (2160, 1440, 1080, 720, 480, 360, 240, 144) if h >= s * 0.9), None)
        if std is None:
            continue
        heights.add(std)
        fs = int(f.get("filesize") or f.get("filesize_approx") or 0)
        if fs:
            extra = best_audio if f.get("acodec") in (None, "none") else 0
            sizes[std] = max(sizes.get(std, 0), fs + extra)
    if best_audio:
        audio_size = best_audio
    entries = info.get("entries") or []
    return MediaInfo(
        id=str(info.get("id") or ""),
        title=info.get("title") or info.get("fulltitle") or "",
        url=info.get("webpage_url") or url,
        extractor=info.get("extractor_key") or info.get("extractor") or "",
        uploader=info.get("uploader") or info.get("channel"),
        duration=int(info["duration"]) if info.get("duration") else None,
        thumbnail=info.get("thumbnail"),
        heights=sorted(heights, reverse=True),
        sizes=sizes,
        audio_size=audio_size,
        is_live=info.get("live_status") in ("is_live", "is_upcoming") or bool(info.get("is_live")),
        is_playlist=is_playlist,
        entries_count=info.get("playlist_count") or len(entries),
    )


def _clear_dir(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        return
    for p in path.iterdir():
        if p.is_file():
            p.unlink(missing_ok=True)


def collect_media(workdir: Path, kind: str) -> list[Path]:
    """Return final media files in download order, skipping partials/thumbnails."""
    allowed = AUDIO_EXT if kind == "audio" else VIDEO_EXT | AUDIO_EXT | IMAGE_EXT | GIF_EXT
    files = [p for p in workdir.rglob("*") if p.is_file() and p.suffix.lower() in allowed
             and not p.name.endswith((".part", ".ytdl", ".temp")) and p.stat().st_size > 0]
    if kind == "video":
        # If a video exists with the same stem, drop sidecar images (thumbnails).
        video_stems = {p.stem for p in files if p.suffix.lower() in VIDEO_EXT}
        files = [p for p in files if not (p.suffix.lower() in IMAGE_EXT and p.stem in video_stems)]
    return sorted(files, key=lambda p: (p.name, p.stat().st_mtime))
