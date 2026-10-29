import pytest

from bots.channelmanager.member_interactions import GateCb
from bots.channelmanager.member_specs import MemberSpec
from bots.channelmanager.member_ui import MemberCb
from bots.channelmanager.models import MemberConfig, MemberLead
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR
from tests.bots.channelmanager.test_members import PERSON, ingest, join_event, latest, setup_members
from tests.bots.channelmanager.test_publishing_ui import feed
from tests.conftest import callback_update, message_update


async def click(ctx, dp, action, resource=CHANNEL_ID, generation=None, actor=OPERATOR):
    if generation is None:
        row = await ctx.extras["members"].config(CHANNEL_ID, OPERATOR)
        generation = row.generation if row else 0
    await feed(ctx, dp, callback_update(MemberCb(a=action, x=str(resource), g=generation, u=OPERATOR).pack(), user_id=actor))


async def config(ctx):
    async with ctx.sm() as session:
        return await session.get(MemberConfig, (ctx.bot_id, CHANNEL_ID))


async def test_enable_is_owned_generation_bound_and_reviewed(chm, dp, api):
    await setup_members(chm, api, MemberSpec())
    await feed(chm, dp, message_update("/members"))
    await click(chm, dp, "chan")
    await click(chm, dp, "ask")
    await click(chm, dp, "on", actor=PERSON)
    assert not (await config(chm)).spec["enabled"]
    await click(chm, dp, "on")
    assert (await config(chm)).spec["enabled"]


async def test_stale_confirmation_cannot_enable_changed_policy(chm, dp, api):
    await setup_members(chm, api, MemberSpec())
    row = await config(chm)
    await click(chm, dp, "ask")
    await chm.extras["members"].save(CHANNEL_ID, OPERATOR, MemberSpec(captcha=True), row.generation)
    await click(chm, dp, "on", generation=row.generation)
    assert not (await config(chm)).spec["enabled"]


async def test_profile_and_required_chat_inputs_use_validated_plain_fields(chm, dp, api):
    await setup_members(chm, api, MemberSpec())
    for action, value in [("names", "spam\nbot && ad"), ("languages", "allow en,ar"), ("alphabet", "allow LATIN,ARABIC"),
        ("required", "-100999 https://t.me/required"), ("rate", "25")]:
        await click(chm, dp, action)
        await feed(chm, dp, message_update(value))
    spec = MemberSpec.model_validate((await config(chm)).spec)
    assert spec.profile.blocked_names == ["spam", "bot && ad"]
    assert spec.profile.languages == ["en", "ar"] and spec.profile.scripts == ["LATIN", "ARABIC"]
    assert spec.required[0].chat_id == -100999 and spec.profile.max_per_ten_seconds == 25


async def test_shared_content_buttons_preview_and_cancel(chm, dp, api):
    await setup_members(chm, api, MemberSpec())
    await click(chm, dp, "welcome")
    await feed(chm, dp, message_update("Welcome here"))
    await click(chm, dp, "welcomebtn")
    await feed(chm, dp, message_update("Website - https://example.com"))
    await click(chm, dp, "welcomepre")
    assert any(m.text == "Welcome here" and m.chat_id == OPERATOR for m in api.calls("SendMessage"))
    before = (await config(chm)).generation
    await click(chm, dp, "goodbye")
    await feed(chm, dp, message_update("/cancel"))
    await feed(chm, dp, message_update("Unrelated"))
    assert (await config(chm)).generation == before


async def test_bulk_confirmation_releases_recorded_condition_without_approval(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True, captcha=True))
    await ingest(chm, dp, join_event())
    await click(chm, dp, "bulk")
    await feed(chm, dp, message_update("all"))
    markup = api.calls("SendMessage")[-1].reply_markup
    data = MemberCb.unpack(markup.inline_keyboard[0][0].callback_data)
    await click(chm, dp, "bulkdo", data.x, data.g)
    assert (await latest(chm)).manual_release
    assert not api.calls("ApproveChatJoinRequest")


async def test_signed_start_enters_private_gate_router(chm, dp, api):
    from bots.channelmanager.members import start_token
    await setup_members(chm, api, MemberSpec(enabled=True, captcha=True))
    await ingest(chm, dp, join_event())
    row = await latest(chm)
    await feed(chm, dp, message_update(f"/start {start_token(chm, row)}", user_id=PERSON))
    async with chm.sm() as session:
        lead = await session.get(MemberLead, (chm.bot_id, CHANNEL_ID, PERSON))
        assert lead.reachable and lead.private_interacted_at
    assert any(m.chat_id == PERSON and m.reply_markup for m in api.calls("SendMessage"))


@pytest.mark.parametrize("callback", [MemberCb(a="r", x="a" * 32, g=0, u=999999999999999999),
    GateCb(r="a" * 16, g=99999999, a=-1, u=999999999999999999)])
def test_membership_callbacks_fit_telegram_limit(callback):
    assert len(callback.pack().encode()) <= 64
