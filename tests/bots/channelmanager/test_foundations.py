from datetime import timedelta

import pytest
from aiogram.types import Chat, ChatMemberLeft, Message, Update, User
from sqlalchemy import func, select

from bots.channelmanager import ingress, outbox, worker
from bots.channelmanager.handlers import ChannelCb
from bots.channelmanager.models import Channel, ChannelRole, Entitlement, Event, Inbox, Operation
from bots.channelmanager.permissions import AccessDenied
from core.db.base import utcnow
from core.db.models import BotUser
from core.runtime.dispatcher import allowed_update_types, build_dispatcher
from core.sdk.module import DurableIngressError
from core.sdk.registry import discover
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR, admin_member, membership_update
from tests.conftest import BOT_ID, callback_update, message_update


async def count(ctx, model):
    async with ctx.sm() as session:
        return await session.scalar(select(func.count()).select_from(model))


async def connect(ctx):
    return await ctx.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)


def test_module_contract_and_update_subscriptions(chm):
    mod = chm.module
    assert mod.durable_ingress and mod.factory_template == "channelmanager"
    assert {job.name for job in mod.factory_jobs()} == {"channelmanager"}
    assert "pre_checkout_query" in mod.required_update_types()
    assert set(mod.processes()) == {"worker"}
    assert "edited_channel_post" in allowed_update_types(chm, build_dispatcher(chm))
    assert discover(["groupguard"])[0].durable_ingress
    assert not discover(["notes"])[0].durable_ingress


async def test_setup_creates_scoped_roles_limits_audit_and_queued_notice(chm, dp, api):
    await dp.feed_update(chm.bot, message_update(f"/connect {CHANNEL_ID}"))
    row = await chm.extras["channelmanager"].get(CHANNEL_ID)
    assert row.status == "active" and row.connected_by == OPERATOR
    async with chm.sm() as session:
        assert await session.get(ChannelRole, (BOT_ID, CHANNEL_ID, OPERATOR))
        assert (await session.get(Entitlement, (BOT_ID, CHANNEL_ID))).tier == "free"
    assert await count(chm, Event) == 1
    assert await count(chm, Operation) == 1
    assert not any("channel status:" in (m.text or "") for m in api.calls("SendMessage"))
    await worker.tick(chm)
    assert any("&lt;channel&gt;" in (m.text or "") for m in api.calls("SendMessage"))
    async with chm.sm() as session:
        op = await session.scalar(select(Operation))
        assert op.status == "succeeded" and op.remote_message_id is not None


async def test_setup_domain_and_notice_roll_back_together(chm, monkeypatch):
    async def fail(*args, **kwargs):
        raise RuntimeError("outbox write failed")
    monkeypatch.setattr(outbox, "enqueue", fail)
    with pytest.raises(RuntimeError):
        await connect(chm)
    assert await count(chm, Channel) == await count(chm, Event) == await count(chm, Operation) == 0


@pytest.mark.parametrize("actor", [77, 999])
async def test_native_channel_permission_required_even_for_platform_admin(chm, actor):
    with pytest.raises(AccessDenied):
        await chm.extras["channelmanager"].connect(CHANNEL_ID, actor)
    assert await count(chm, Channel) == 0


async def test_non_channel_and_missing_bot_post_right_rejected(chm, api):
    api.responses["GetChat"] = Chat(id=CHANNEL_ID, type="supergroup", title="Group")
    with pytest.raises(AccessDenied):
        await connect(chm)
    api.responses["GetChat"] = Chat(id=CHANNEL_ID, type="channel", title="Channel")
    api.responses["GetChatMember"] = lambda method: admin_member(method.user_id, post=method.user_id != BOT_ID)
    with pytest.raises(AccessDenied):
        await connect(chm)


async def test_callbacks_bind_actor_and_generation_and_revalidate_rights(chm, dp, api, redis):
    row = await connect(chm)
    cb = ChannelCb(a="disconnect", c=CHANNEL_ID, g=row.generation, u=OPERATOR).pack()
    await dp.feed_update(chm.bot, callback_update(cb, user_id=77))
    assert (await chm.extras["channelmanager"].get(CHANNEL_ID)).status == "active"
    api.responses["GetChatMember"] = lambda method: admin_member(method.user_id, post=False)
    await dp.feed_update(chm.bot, callback_update(cb))
    assert (await chm.extras["channelmanager"].get(CHANNEL_ID)).status == "active"
    api.responses["GetChatMember"] = lambda method: admin_member(method.user_id)
    await redis.delete(chm.keys("throttle", "CallbackQuery", OPERATOR))
    stale = ChannelCb(a="disconnect", c=CHANNEL_ID, g=row.generation - 1, u=OPERATOR).pack()
    await dp.feed_update(chm.bot, callback_update(stale))
    assert (await chm.extras["channelmanager"].get(CHANNEL_ID)).status == "active"
    await redis.delete(chm.keys("throttle", "CallbackQuery", OPERATOR))
    await dp.feed_update(chm.bot, callback_update(cb))
    assert (await chm.extras["channelmanager"].get(CHANNEL_ID)).status == "disconnected"
    assert any(x.show_alert for x in api.calls("AnswerCallbackQuery"))


async def test_duplicate_ingress_is_durable_and_does_not_register_private_users(chm, dp, api):
    event = membership_update()
    await dp.feed_update(chm.bot, event)
    await dp.feed_update(chm.bot, event)
    assert await count(chm, Inbox) == 1
    assert await count(chm, BotUser) == 0
    assert await count(chm, Channel) == 0
    assert not api.calls("SendMessage")
    assert await ingress.process_one(chm)
    assert not await ingress.process_one(chm)
    assert await count(chm, Event) == 1
    async with chm.sm() as session:
        row = await session.scalar(select(Inbox))
        assert row.status == "completed" and row.payload == {}


async def test_failed_receipt_escapes_shared_error_handler(chm, dp, monkeypatch):
    def broken_sm():
        raise RuntimeError("database unavailable")
    monkeypatch.setattr(chm, "sm", broken_sm)
    with pytest.raises(DurableIngressError):
        await dp.feed_update(chm.bot, membership_update())


async def test_lifecycle_removal_demotion_and_stale_event_order(chm, dp):
    await connect(chm)
    now = utcnow() + timedelta(seconds=1)
    demotion = membership_update(70, member=admin_member(post=False), date=now)
    await dp.feed_update(chm.bot, demotion)
    await ingress.process_one(chm)
    assert (await chm.extras["channelmanager"].get(CHANNEL_ID)).status == "degraded"
    await dp.feed_update(chm.bot, membership_update(69, date=now - timedelta(seconds=1)))
    await ingress.process_one(chm)
    assert (await chm.extras["channelmanager"].get(CHANNEL_ID)).status == "degraded"
    removed = ChatMemberLeft(user=User(id=BOT_ID, is_bot=True, first_name="Bot"))
    await dp.feed_update(chm.bot, membership_update(71, member=removed, date=now + timedelta(seconds=1)))
    await ingress.process_one(chm)
    assert (await chm.extras["channelmanager"].get(CHANNEL_ID)).status == "removed"


async def test_anonymous_channel_posts_need_no_individual_user(chm, dp):
    post = Message(message_id=12, date=utcnow(), chat=Chat(id=CHANNEL_ID, type="channel"), text="No author")
    await dp.feed_update(chm.bot, Update(update_id=90, channel_post=post))
    await dp.feed_update(chm.bot, Update(update_id=91, edited_channel_post=post))
    assert await count(chm, Inbox) == 2 and await count(chm, BotUser) == 0
    await worker.tick(chm)


async def test_unknown_callbacks_and_foreign_channel_are_denied(chm, dp, api, redis):
    await connect(chm)
    for value in ["chm:broken", ChannelCb(a="disconnect", c=-100999, g=1, u=OPERATOR).pack()]:
        await redis.delete(chm.keys("throttle", "CallbackQuery", OPERATOR))
        await dp.feed_update(chm.bot, callback_update(value))
    assert (await chm.extras["channelmanager"].get(CHANNEL_ID)).status == "active"
    assert all(x.show_alert for x in api.calls("AnswerCallbackQuery"))


async def test_failed_inbox_processing_is_bounded_and_transactional(chm, dp, monkeypatch):
    await dp.feed_update(chm.bot, membership_update())
    svc = chm.extras["channelmanager"]

    async def fail_after_mutation(session, event, update_id):
        session.add(Channel(bot_id=BOT_ID, channel_id=CHANNEL_ID, title="rolled back"))
        await session.flush()
        raise RuntimeError("private error text")

    monkeypatch.setattr(svc, "membership", fail_after_mutation)
    for _ in range(5):
        assert await ingress.process_one(chm)
        assert await count(chm, Channel) == 0
        async with chm.sm() as session:
            row = await session.get(Inbox, (BOT_ID, 50))
            row.available_at = utcnow()
            await session.commit()
    async with chm.sm() as session:
        row = await session.get(Inbox, (BOT_ID, 50))
        assert row.status == "failed" and row.attempts == 5 and row.error_code == "RuntimeError"
    assert not await ingress.process_one(chm)


async def test_reconnect_and_refresh_track_current_bot_rights(chm, api):
    svc = chm.extras["channelmanager"]
    row = await connect(chm)
    await svc.disconnect(CHANNEL_ID, OPERATOR, row.generation)
    assert (await connect(chm)).status == "active"
    row = await svc.get(CHANNEL_ID)
    api.responses["GetChatMember"] = lambda method: admin_member(method.user_id, post=method.user_id != BOT_ID)
    assert (await svc.refresh(CHANNEL_ID, OPERATOR, row.generation)).status == "degraded"


async def test_operator_channel_limit_counts_role_memberships(chm, api):
    await chm.settings.set("max_channels_per_operator", 1)
    await connect(chm)
    api.responses["GetChat"] = Chat(id=CHANNEL_ID - 1, type="channel", title="Second")
    with pytest.raises(AccessDenied, match="limit"):
        await connect(chm)


async def test_maintenance_observes_lifecycle_while_pausing_outgoing_work(chm, dp, api):
    await connect(chm)
    await chm.settings.set("maintenance", True)
    await dp.feed_update(chm.bot, membership_update(date=utcnow() + timedelta(seconds=1)))
    await worker.tick(chm)
    assert not api.calls("SendMessage")
    async with chm.sm() as session:
        assert (await session.scalar(select(Inbox))).status == "completed"
        assert await session.scalar(select(func.count()).select_from(Operation).where(Operation.status == "pending")) == 1


def test_explicit_fixture_env_files_still_work(tmp_path):
    from core.config import PlatformConfig

    fixture = tmp_path / ".env"
    fixture.write_text("ENABLED_BOTS=channelmanager\n", encoding="utf-8")
    assert PlatformConfig(_env_file=fixture).enabled_bots == ["channelmanager"]
