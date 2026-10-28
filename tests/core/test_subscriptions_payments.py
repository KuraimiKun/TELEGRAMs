from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.db.base import Base
from core.db.models import Bot, BotUser, User
from core.sdk.module import PlanSpec
from core.services.payments import PaymentService
from core.services.subscriptions import SubscriptionService


@pytest.mark.asyncio
async def test_vip_and_payment_service():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sm = async_sessionmaker(engine, expire_on_commit=False)

    bot_id = 1
    user_id = 12345

    # Seed Bot, User, and BotUser
    async with sm() as session:
        b = Bot(id=bot_id, slug="socialdownload", title="Social Download", active=True)
        session.add(b)
        u = User(id=user_id)
        session.add(u)
        bu = BotUser(bot_id=bot_id, user_id=user_id)
        session.add(bu)
        await session.commit()

    subs = SubscriptionService(sessionmaker=sm, bot_id=bot_id)
    payments = PaymentService(sessionmaker=sm, bot_id=bot_id, subs=subs)

    # 1. Ensure plans
    specs = [
        PlanSpec(name="1 Month VIP", days=30, stars=150, sort=1),
        PlanSpec(name="1 Year VIP", days=365, stars=1000, sort=2),
    ]
    await subs.ensure_plans(specs)
    plans = await subs.list_active_plans()
    assert len(plans) == 2
    assert plans[0].days == 30

    # 2. Grant VIP 7 days
    until_1 = await subs.grant_vip(user_id, days=7)
    assert until_1 > datetime.now(UTC)

    # 3. Grant another 30 days -> stacks on top of until_1
    until_2 = await subs.grant_vip(user_id, days=30)
    diff = (until_2 - until_1).total_seconds()
    assert abs(diff - (30 * 86400)) < 5

    # 4. Record payment via PaymentService
    until_3, created = await payments.record_payment(
        user_id=user_id,
        plan_id=plans[0].id,
        stars=150,
        days=30,
        charge_id="tg_charge_123",
    )
    assert created is True
    diff_pay = (until_3 - until_2).total_seconds()
    assert abs(diff_pay - (30 * 86400)) < 5

    # 4b. Telegram redelivers the same update -> idempotent, no second grant
    until_dup, created_dup = await payments.record_payment(
        user_id=user_id,
        plan_id=plans[0].id,
        stars=150,
        days=30,
        charge_id="tg_charge_123",
    )
    assert created_dup is False
    assert abs((until_dup - until_3).total_seconds()) < 1

    # 5. Process refund -> deducts 30 days
    refund_res = await payments.process_refund("tg_charge_123")
    assert refund_res is not None and (refund_res.user_id, refund_res.days) == (user_id, 30)
    assert await payments.process_refund("tg_charge_123") is None  # idempotent

    # The ledger explains every change: 2 admin grants, 1 payment, 1 refund.
    sources = [g.source for g in reversed(await subs.ledger(user_id))]
    assert sources == ["admin", "admin", "payment", "refund"]

    async with sm() as session:
        bu = await session.get(BotUser, (bot_id, user_id))
        vu = bu.vip_until if bu.vip_until.tzinfo else bu.vip_until.replace(tzinfo=UTC)
        diff_ref = (until_2 - vu).total_seconds()
        assert abs(diff_ref) < 5

    await engine.dispose()
