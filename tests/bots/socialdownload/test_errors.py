from bots.socialdownload.engine.errors import classify_error


def test_classify_error():
    assert classify_error("This account is private and cannot be downloaded") == "private"
    assert classify_error("Sign in to confirm you're not a bot") == "login"
    assert classify_error("Video unavailable in your country") == "geo"
    assert classify_error("HTTP Error 429: Too Many Requests") == "rate_limited"
    assert classify_error("Video deleted or removed by user") == "removed"
    assert classify_error("No video formats found") == "no_media"
    assert classify_error("Connection timed out") == "timeout"
    assert classify_error("Unrecognized stream failure") == "unknown"


def test_network_failures_are_transient():
    from bots.socialdownload.engine.errors import RETRYABLE, classify_error

    for msg in (
        "Unable to download JSON metadata: ('Unable to connect to proxy', OSError('Tunnel connection failed: 403'))",
        "[Errno -2] Name or service not known",
        "Failed to resolve 'api.x.com'",
    ):
        code = classify_error(msg)
        assert code == "timeout" and code in RETRYABLE, msg
