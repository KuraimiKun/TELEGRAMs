import fakeredis.aioredis
import pytest

from bots.socialdownload.engine.cache import CachedItem, CachedMedia, MediaCache, media_key


@pytest.mark.asyncio
async def test_media_cache():
    fake_redis = fakeredis.aioredis.FakeRedis()
    cache = MediaCache(redis=fake_redis, ttl_days=1)

    key = media_key("https://www.youtube.com/watch?v=123", "video", 720)
    assert len(key) == 40  # SHA1 hash hex

    # Initially empty
    assert await cache.get(key) is None

    # Store items
    media = CachedMedia(
        items=[CachedItem(kind="video", file_id="AgACAgIAAxkBAAI...")],
        title="Test Video",
        url="https://www.youtube.com/watch?v=123",
    )
    await cache.set(key, media)

    # Retrieve items
    loaded = await cache.get(key)
    assert loaded is not None
    assert loaded.title == "Test Video"
    assert len(loaded.items) == 1
    assert loaded.items[0].kind == "video"
    assert loaded.items[0].file_id == "AgACAgIAAxkBAAI..."
