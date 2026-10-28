from __future__ import annotations

import os

import fakeredis.aioredis
import pytest

from bots.socialdownload.engine.network import (
    CookieJar,
    ProxyPool,
    UnsafeURL,
    assert_public_url,
    validate_cookie_file,
)
from bots.socialdownload.engine.platforms import normalize_url
from core.redis import KeySpace

GOOD_COOKIES = b"# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tSID\tabc\n"


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:6379/",
        "http://[::1]/",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5/x",
        "http://192.168.1.1/",
        "http://redis:6379/",
        "http://localhost/",
        "http://telegram-bot-api:8081/",
        "ftp://example.com/file",
        "http://[::ffff:127.0.0.1]/",
    ],
)
async def test_ssrf_guard_blocks_internal_targets(url):
    with pytest.raises(UnsafeURL):
        await assert_public_url(url)


async def test_ssrf_guard_allows_public_ip_literals():
    await assert_public_url("https://1.1.1.1/video.mp4")


def test_tracking_params_are_stripped_but_real_params_survive():
    url = "https://example.com/watch?season=2&token=abc&type=clip&utm_source=x&fbclid=y&s=1&t=2"
    assert normalize_url(url) == "https://example.com/watch?season=2&token=abc&type=clip"


def test_cookie_validation():
    assert validate_cookie_file(GOOD_COOKIES) is None
    assert validate_cookie_file(b"not a cookie file") is not None
    assert validate_cookie_file(b"") is not None
    assert validate_cookie_file(b"x" * (2 * 1024 * 1024)) is not None


async def test_cookie_jar_save_checkout_and_delete(tmp_path):
    jar = CookieJar(tmp_path, redis=fakeredis.aioredis.FakeRedis())
    path = jar.save("youtube", GOOD_COOKIES)
    if os.name == "posix":  # Windows reports synthetic mode bits; access is controlled by NTFS ACLs.
        assert oct(path.stat().st_mode)[-3:] == "600"
    with pytest.raises(ValueError):
        jar.save("../../etc", GOOD_COOKIES)
    with pytest.raises(ValueError):
        jar.save("youtube", b"garbage")

    picked = await jar.pick("youtube")
    tmp = jar.checkout(picked)
    assert tmp and tmp != str(picked)  # yt-dlp writes to a private copy, never the shared original
    jar.release(tmp)

    assert jar.delete("../etc/passwd") is False
    assert jar.delete(path.name) is True
    assert jar.files("youtube") == []


async def test_proxy_keys_are_namespaced_and_failures_weighted():
    redis = fakeredis.aioredis.FakeRedis()
    pool = ProxyPool(redis, ["http://a:1", "http://b:2"], keys=KeySpace("botx"))
    await pool.report("http://a:1", ok=False)
    keys = [k.decode() for k in await redis.keys("*")]
    assert keys and all(k.startswith("botx:") for k in keys)
    health = dict(await pool.health())
    assert health["http://a:1"] == 1 and health["http://b:2"] == 0
