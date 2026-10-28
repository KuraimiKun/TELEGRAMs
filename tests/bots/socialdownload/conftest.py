from __future__ import annotations

import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from aiogram.types import Audio, Chat, Message, PhotoSize, Video

HAS_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
needs_ffmpeg = pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg not installed")


def make_video(path: Path, *, codec: str = "libx264", size: str = "64x64", seconds: int = 1) -> Path:
    args = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc=duration={seconds}:size={size}:rate=5"]
    if codec == "libx264":
        args += ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
    else:
        args += ["-c:v", codec]
    subprocess.run([*args, str(path)], check=True)
    return path


@pytest.fixture(scope="session")
def sample_mp4(tmp_path_factory) -> Path:
    if not HAS_FFMPEG:
        pytest.skip("ffmpeg not installed")
    return make_video(tmp_path_factory.mktemp("media") / "sample.mp4")


def _msg(chat_id: int, **media) -> Message:
    return Message(message_id=500, date=datetime.now(UTC), chat=Chat(id=chat_id, type="private"), **media)


@pytest.fixture
def media_api(api):
    """Make the recording Bot API return media messages carrying file_ids, like Telegram does."""
    counter = iter(range(1, 10_000))

    def video(m):
        return _msg(m.chat_id, video=Video(file_id=f"vid{next(counter)}", file_unique_id="u", width=64, height=64,
                                           duration=1))

    def photo(m):
        return _msg(m.chat_id, photo=[PhotoSize(file_id=f"ph{next(counter)}", file_unique_id="u", width=1, height=1)])

    def audio(m):
        return _msg(m.chat_id, audio=Audio(file_id=f"au{next(counter)}", file_unique_id="u", duration=1))

    def group(m):
        out = []
        for item in m.media:
            fn = {"video": video, "photo": photo, "audio": audio}.get(item.type, video)
            out.append(fn(m))
        return out

    api.responses.update(SendVideo=video, SendPhoto=photo, SendAudio=audio, SendMediaGroup=group)
    return api
