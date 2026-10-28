"""ffmpeg/ffprobe helpers to make files Telegram-friendly."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from bots.socialdownload.engine.ytdl import AUDIO_EXT, GIF_EXT, IMAGE_EXT, VIDEO_EXT
from core.log import get_logger

log = get_logger(__name__)

PHOTO_MAX_BYTES = 10 * 1024 * 1024


@dataclass(slots=True)
class MediaFile:
    path: Path
    kind: str  # video | audio | photo | animation | document
    size: int
    width: int | None = None
    height: int | None = None
    duration: int | None = None
    thumb: Path | None = None
    title: str | None = None
    performer: str | None = None


async def _run(*cmd: str, timeout: float = 600) -> tuple[int, bytes, bytes]:
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        return -1, b"", b"timeout"
    return proc.returncode or 0, out, err


async def probe(path: Path) -> dict:
    code, out, _ = await _run("ffprobe", "-v", "error", "-print_format", "json", "-show_format",
                              "-show_streams", str(path), timeout=60)
    if code != 0:
        return {}
    try:
        return json.loads(out)
    except ValueError:
        return {}


def _stream(info: dict, kind: str) -> dict | None:
    return next((s for s in info.get("streams", []) if s.get("codec_type") == kind), None)


async def make_thumbnail(source: Path, out: Path, at: float = 1.0) -> Path | None:
    """Telegram thumbnails: JPEG, <= 320px, < 200 KB."""
    for quality in (4, 8, 14):
        code, _, _ = await _run(
            "ffmpeg", "-y", "-loglevel", "error", "-ss", f"{max(at, 0):.2f}", "-i", str(source),
            "-frames:v", "1", "-vf", "scale='if(gt(iw,ih),320,-2)':'if(gt(iw,ih),-2,320)'",
            "-q:v", str(quality), str(out), timeout=60,
        )
        if code == 0 and out.exists() and out.stat().st_size < 200 * 1024:
            return out
    return None


async def remux_mp4(path: Path) -> Path:
    """Remux non-MP4 containers to MP4 (stream copy). Returns original on failure."""
    if path.suffix.lower() == ".mp4":
        return path
    out = path.with_suffix(".mp4")
    code, _, err = await _run("ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-c", "copy",
                              "-movflags", "+faststart", str(out), timeout=900)
    if code == 0 and out.exists() and out.stat().st_size > 0:
        path.unlink(missing_ok=True)
        return out
    out.unlink(missing_ok=True)
    log.info("remux_failed", file=path.name, err=err.decode(errors="ignore")[:200])
    return path


# Codecs every Telegram client plays inline. Anything else (VP9, AV1, Opus-in-MP4...) is transcoded.
PLAYABLE_VCODECS = {"h264", "hevc"}
PLAYABLE_ACODECS = {"aac", "mp3"}
TRANSCODE_MAX_SECONDS = 20 * 60  # longer videos are sent as-is: transcoding would hog the worker


def needs_transcode(info: dict) -> bool:
    v = _stream(info, "video")
    a = _stream(info, "audio")
    if v is None:
        return False
    if (v.get("codec_name") or "").lower() not in PLAYABLE_VCODECS:
        return True
    return a is not None and (a.get("codec_name") or "").lower() not in PLAYABLE_ACODECS


async def transcode_h264(path: Path, duration: float) -> Path:
    """Re-encode to H.264/AAC MP4. Returns the original path on failure or when the video is too long."""
    if duration and duration > TRANSCODE_MAX_SECONDS:
        return path
    out = path.with_name(f"{path.stem}_h264.mp4")
    code, _, err = await _run(
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(path),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out),
        timeout=max(300.0, (duration or 60) * 3),
    )
    if code == 0 and out.exists() and out.stat().st_size > 0:
        path.unlink(missing_ok=True)
        return out
    out.unlink(missing_ok=True)
    log.info("transcode_failed", file=path.name, err=err.decode(errors="ignore")[:200])
    return path


async def to_jpeg(path: Path) -> Path:
    out = path.with_suffix(".jpg")
    code, _, _ = await _run("ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-q:v", "2", str(out),
                            timeout=60)
    if code == 0 and out.exists():
        path.unlink(missing_ok=True)
        return out
    return path


async def prepare(files: list[Path], title: str | None = None, uploader: str | None = None) -> list[MediaFile]:
    """Turn raw downloaded files into MediaFile objects with metadata and thumbnails."""
    result: list[MediaFile] = []
    for idx, path in enumerate(files):
        ext = path.suffix.lower()
        if ext in VIDEO_EXT:
            path = await remux_mp4(path)
            info = await probe(path)
            duration = float(info.get("format", {}).get("duration") or 0)
            if path.suffix.lower() != ".mp4" or needs_transcode(info):
                transcoded = await transcode_h264(path, duration)
                if transcoded != path:
                    path = transcoded
                    info = await probe(path)
            v = _stream(info, "video") or {}
            thumb = await make_thumbnail(path, path.with_name(f"{path.stem}_thumb.jpg"),
                                         at=min(1.0, duration / 3) if duration else 0)
            kind = "video" if path.suffix.lower() == ".mp4" else "document"
            result.append(MediaFile(path=path, kind=kind, size=path.stat().st_size,
                                    width=int(v.get("width") or 0) or None,
                                    height=int(v.get("height") or 0) or None,
                                    duration=int(duration) or None, thumb=thumb,
                                    title=title))
        elif ext in AUDIO_EXT:
            info = await probe(path)
            duration = float(info.get("format", {}).get("duration") or 0)
            tags = info.get("format", {}).get("tags") or {}
            thumb = None
            if _stream(info, "video"):  # embedded cover art
                thumb = await make_thumbnail(path, path.with_name(f"{path.stem}_thumb.jpg"), at=0)
            result.append(MediaFile(path=path, kind="audio", size=path.stat().st_size,
                                    duration=int(duration) or None, thumb=thumb,
                                    title=tags.get("title") or tags.get("TITLE") or title,
                                    performer=tags.get("artist") or tags.get("ARTIST") or uploader))
        elif ext in GIF_EXT:
            result.append(MediaFile(path=path, kind="animation", size=path.stat().st_size))
        elif ext in IMAGE_EXT:
            if ext in (".webp", ".heic"):
                path = await to_jpeg(path)
            size = path.stat().st_size
            info = await probe(path)
            v = _stream(info, "video") or {}
            w, h = int(v.get("width") or 0), int(v.get("height") or 0)
            ok_photo = size <= PHOTO_MAX_BYTES and (w + h) <= 10000 and (not w or not h or max(w, h) / min(w, h) <= 20)
            result.append(MediaFile(path=path, kind="photo" if ok_photo else "document", size=size,
                                    width=w or None, height=h or None))
        else:
            result.append(MediaFile(path=path, kind="document", size=path.stat().st_size))
        log.debug("prepared", idx=idx, file=path.name, kind=result[-1].kind)
    return result
