"""Measured bounded workloads: disposable PostgreSQL/Redis and recording SDK only."""
import asyncio
import json
import os
import time
import uuid

import pytest
from sqlalchemy import select

from bots.groupguard import durable, fed_bans
from bots.groupguard.models import GuardChat, GuardFedChat, GuardFedObservation, GuardJob
from tests.bots.groupguard.conftest import no_throttle
from tests.bots.groupguard.test_groupguard import GROUP, MEMBER, gctx, group_msg
from tests.bots.groupguard.test_phase01a import env, send
from tests.bots.groupguard.test_phase10 import actual_bans, network
from tests.integration.test_groupguard_foundations import redis, sm

__all__=['env', 'gctx', 'no_throttle', 'redis', 'sm']
pytestmark=pytest.mark.skipif(not os.environ.get('TEST_GG_DATABASE_URL') or not os.environ.get('TEST_GG_REDIS_URL'),reason='Disposable PostgreSQL/Redis benchmark URLs required')


async def test_measured_real_redis_dispatcher_flood_burst(env,api):
    await env.extras['guard'].update_config(GROUP,flood_count=0,flood_consecutive_count=5,cas=False)
    before=time.perf_counter()
    await asyncio.gather(*(send(env,group_msg('measured burst '+str(n),MEMBER)) for n in range(80)))
    calls=api.calls('RestrictChatMember')
    assert len(calls)==16 and all(c.user_id==MEMBER and c.permissions.can_send_messages is False for c in calls)
    assert len(api.calls('DeleteMessage'))==16
    print('BENCHMARK '+json.dumps(dict(workload='80 parallel delivered messages',context='child' if env.child else 'standalone',bot_id=env.bot_id,
        seconds=round(time.perf_counter()-before,6),updates=80,actual_restrictions=16,actual_deletes=16,
        services='PostgreSQL16 / Redis7 disposable',telegram='stateful recording SDK',throttling='conversation fixture bypass; actual runtime guard separately tested')))


async def test_measured_federation_fanout_250_observed_groups(env,api):
    banned=actual_bans(api)
    actor,fed=await network(env)
    chats=[GROUP-n for n in range(250)]
    async with env.sm() as session:
        assert await session.get(GuardFedChat,(env.bot_id,GROUP)) is not None
        session.add(GuardFedObservation(bot_id=env.bot_id,chat_id=GROUP,user_id=30))
        for chat in chats[1:]:
            session.add(GuardChat(bot_id=env.bot_id,chat_id=chat,title='Measured fixture group',active=True,config={}))
            session.add(GuardFedChat(bot_id=env.bot_id,chat_id=chat,fed_id=fed.id,generation=uuid.uuid4().hex))
            session.add(GuardFedObservation(bot_id=env.bot_id,chat_id=chat,user_id=30))
        await session.commit()
    before=time.perf_counter()
    await fed_bans.change(env,actor,fed.id,fed_bans.BanInput(30,'Measured observed fixture'),active=True)
    maximum=0
    sweeps=0
    while time.perf_counter()-before<60:
        await durable.sweep(env,limit=100)
        sweeps+=1
        async with env.sm() as session:
            pending=list((await session.execute(select(GuardJob).where(GuardJob.bot_id==env.bot_id,
                GuardJob.kind.in_({'fed_fanout','fed_enforce'}),GuardJob.status.in_({'pending','running'})))).scalars())
        maximum=max(maximum,len(pending))
        if not pending:
            break
        await asyncio.sleep(0.05)
    assert {(chat,30) for chat in chats}<=banned
    assert len(api.calls('BanChatMember'))==250 and not pending and maximum<5000
    print('BENCHMARK '+json.dumps(dict(workload='one ban /250 observed attached fixture groups',context='child' if env.child else 'standalone',bot_id=env.bot_id,
        seconds=round(time.perf_counter()-before,6),groups=250,actual_bans=250,peak_pending=maximum,sweeps=sweeps,
        producer_batch=100,sweep_limit=100,configured_outbound_quota=20,
        services='PostgreSQL16 / Redis7 disposable',telegram='stateful recording SDK',fixture='synthetic attachments; actual service/worker/SDK effects')))
