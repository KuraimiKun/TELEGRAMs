from bots.socialdownload.engine.platforms import (
    detect_platform,
    extract_urls,
    is_playlist,
    normalize_url,
)


def test_extract_urls():
    text = "Check out this TikTok https://www.tiktok.com/@user/video/123456789 and this youtube youtu.be/dQw4w9WgXcQ !"
    urls = extract_urls(text)
    assert len(urls) == 2
    assert urls[0] == "https://www.tiktok.com/@user/video/123456789"
    assert urls[1] == "https://youtu.be/dQw4w9WgXcQ"


def test_platform_detection():
    assert detect_platform("https://www.tiktok.com/@user/video/123") == "tiktok"
    assert detect_platform("https://vm.tiktok.com/ZM8x/") == "tiktok"
    assert detect_platform("https://www.instagram.com/reel/C123/") == "instagram"
    assert detect_platform("https://instagram.com/p/C123/") == "instagram"
    assert detect_platform("https://youtu.be/dQw4w9WgXcQ") == "youtube"
    assert detect_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "youtube"
    assert detect_platform("https://x.com/user/status/123456") == "twitter"
    assert detect_platform("https://twitter.com/user/status/123456") == "twitter"
    assert detect_platform("https://www.facebook.com/watch/?v=123") == "facebook"
    assert detect_platform("https://www.reddit.com/r/funny/comments/123/") == "reddit"
    assert detect_platform("https://pin.it/123") == "pinterest"
    assert detect_platform("https://soundcloud.com/artist/track") == "soundcloud"
    assert detect_platform("https://vimeo.com/123456") == "vimeo"


def test_url_normalization():
    # YouTube tracking params stripped & canonicalized
    yt_url = "https://youtu.be/dQw4w9WgXcQ?si=abcdef123&utm_source=share"
    assert normalize_url(yt_url) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Instagram tracking params stripped
    ig_url = "https://www.instagram.com/reel/C12345/?igsh=abcdef12345&utm_medium=copy_link"
    assert normalize_url(ig_url) == "https://www.instagram.com/reel/C12345/"

    # Twitter to X canonical status
    tw_url = "https://twitter.com/jack/status/20?s=20&t=abcdef"
    assert normalize_url(tw_url) == "https://x.com/i/status/20"


def test_playlist_detection():
    assert is_playlist("https://www.youtube.com/playlist?list=PL123456") is True
    assert is_playlist("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is False
    assert is_playlist("https://soundcloud.com/artist/sets/album-name") is True
