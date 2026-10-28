"""Download bounds apply while streaming; share cards use real Arabic/Latin fonts."""

import io

import pytest
from PIL import Image

from core.files import FileTooLarge, _LimitedBuffer
from core.ui.cards import Card, font, render, shape


def test_streaming_download_limit_rejects_before_allocation():
    buffer = _LimitedBuffer(8)
    buffer.write(b"123456")
    with pytest.raises(FileTooLarge):
        buffer.write(b"789")
    assert buffer.getvalue() == b"123456"


def test_bundled_fonts_shape_arabic_and_render_both_sizes():
    assert "NotoSansArabic" in str(font(30, rtl=True).path)
    assert "NotoSans-Bold" in str(font(30).path)
    assert shape("أرسل لي رسالة مجهولة") != "أرسل لي رسالة مجهولة"
    card = Card(headline="حصلت سيرتي الذاتية على", big="82", big_caption="من 100",
                body="حلل سيرتك الذاتية واكتشف فرص تحسينها", footer="@test_bot", theme="ocean")
    for size, dimensions in [("story", (1080, 1920)), ("square", (1080, 1080))]:
        image = Image.open(io.BytesIO(render(card, size=size)))
        assert image.size == dimensions
