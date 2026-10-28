import pytest

from core.sdk.registry import discover


def test_registry_discover_socialdownload():
    modules = discover(["socialdownload"])
    assert len(modules) == 1
    m = modules[0]
    assert m.slug == "socialdownload"
    assert m.table_prefix == "sd_"
    assert len(m.commands()) > 0
    assert len(m.default_plans) == 3


def test_registry_invalid_slug():
    with pytest.raises(ValueError, match="Invalid bot slug"):
        discover(["123invalid"])

    with pytest.raises(ValueError, match="Invalid bot slug"):
        discover(["CAPS_NOT_ALLOWED"])


def test_registry_nonexistent_bot():
    with pytest.raises(ImportError, match="Failed to import bot package"):
        discover(["non_existent_bot_12345"])
