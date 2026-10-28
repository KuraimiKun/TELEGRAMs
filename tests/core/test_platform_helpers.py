from PIL import Image

from core.config import PlatformConfig
from core.factory.crypto import decrypt_token, encrypt_token, verify_webhook, webhook_secret
from core.redis import KeySpace
from core.sdk.quota import DailyQuota
from core.ui.cards import Card, is_rtl, render, shape


def test_token_encryption_round_trip():
    p = PlatformConfig(factory_secret_key="k1")
    blob = encrypt_token(p, "123:abc")
    assert "123:abc" not in blob and decrypt_token(p, blob) == "123:abc"
    assert decrypt_token(PlatformConfig(factory_secret_key="other"), blob) is None
    assert decrypt_token(p, "") is None


def test_webhook_secret_is_per_bot_and_telegram_safe():
    p = PlatformConfig(factory_secret_key="k1")
    s1, s2 = webhook_secret(p, 1), webhook_secret(p, 2)
    assert s1 != s2 and s1.isalnum() and len(s1) == 48
    assert verify_webhook(p, 1, s1) and not verify_webhook(p, 2, s1) and not verify_webhook(p, 1, "")


async def test_daily_quota(redis):
    q = DailyQuota(redis, KeySpace("cv"), "analyses")
    assert await q.consume(1, limit=2) and await q.consume(1, limit=2)
    assert await q.consume(1, limit=2) is None
    assert await q.remaining(1, 2) == 0
    assert await q.refund(1, token="job1") and not await q.refund(1, token="job1")
    assert await q.remaining(1, 2) == 1
    assert await redis.exists("cv:analyses:1:" + __import__("core.sdk.quota", fromlist=["today"]).today())


def test_cards_render_rtl_and_ltr(tmp_path):
    assert is_rtl("مرحبا") and not is_rtl("hello")
    assert shape("hello") == "hello" and shape("مرحبا") != "مرحبا"
    for size in ("story", "square"):
        png = render(Card(headline="أرسل لي رسالة 👀", body="test", big="82", placeholder="…", footer="@bot"), size)
        path = tmp_path / f"{size}.png"
        path.write_bytes(png)
        with Image.open(path) as img:
            assert img.size == ((1080, 1920) if size == "story" else (1080, 1080))
