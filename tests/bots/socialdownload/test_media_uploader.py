from __future__ import annotations

from bots.socialdownload.engine.media import prepare, probe
from bots.socialdownload.uploader import Sendable, plan_batches
from tests.bots.socialdownload.conftest import make_video, needs_ffmpeg


def kinds(batches):
    return [[i.kind for i in b] for b in batches]


def items(*ks):
    return [Sendable(kind=k, media=f"id{n}") for n, k in enumerate(ks)]


def test_batches_never_produce_single_item_groups_or_mixed_types():
    eleven = plan_batches(items(*["photo"] * 11))
    assert [len(b) for b in eleven] == [10, 1]  # the trailing single item is sent on its own

    mixed = plan_batches(items("photo", "video", "audio", "audio", "document", "photo"))
    assert kinds(mixed) == [["photo", "video"], ["audio", "audio"], ["document"], ["photo"]]


def test_animations_are_never_grouped():
    assert kinds(plan_batches(items("photo", "animation", "photo", "photo"))) == [
        ["photo"],
        ["animation"],
        ["photo", "photo"],
    ]


@needs_ffmpeg
async def test_vp9_video_is_transcoded_to_h264_mp4(tmp_path):
    src = make_video(tmp_path / "clip.webm", codec="libvpx-vp9")
    [mf] = await prepare([src], title="t")
    assert mf.kind == "video" and mf.path.suffix == ".mp4"
    info = await probe(mf.path)
    assert next(s for s in info["streams"] if s["codec_type"] == "video")["codec_name"] == "h264"
    assert mf.thumb is not None and mf.thumb.exists()


@needs_ffmpeg
async def test_vertical_video_metadata(tmp_path):
    src = make_video(tmp_path / "v.mp4", size="72x128")
    [mf] = await prepare([src])
    assert (mf.width, mf.height) == (72, 128)
