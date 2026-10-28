from bots.socialdownload.engine.limits import policy_for
from bots.socialdownload.settings import SocialDownloadSettings as BotSettings
from core.config import MB


def test_tier_policy_limits():
    settings = BotSettings(
        free_daily_limit=10,
        free_max_height=720,
        free_max_mb=500,
        vip_daily_limit=500,
        vip_max_height=2160,
        vip_max_mb=4096,
        sponsor_enabled=True,
        sponsor_text="Join @OurChannel for more!",
        force_sub_enabled=True,
    )

    free_policy = policy_for(is_vip=False, s=settings)
    assert free_policy.daily_limit == 10
    assert free_policy.max_height == 720
    assert free_policy.max_bytes == 500 * MB
    assert free_policy.priority == "normal"
    assert free_policy.allows_height(720) is True
    assert free_policy.allows_height(1080) is False
    assert free_policy.show_sponsor is True
    assert free_policy.force_sub is True

    vip_policy = policy_for(is_vip=True, s=settings)
    assert vip_policy.daily_limit == 500
    assert vip_policy.max_height == 2160
    assert vip_policy.max_bytes == 4096 * MB
    assert vip_policy.priority == "high"
    assert vip_policy.allows_height(2160) is True
    assert vip_policy.show_sponsor is False
    assert vip_policy.force_sub is False
