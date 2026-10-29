from datetime import UTC, datetime, time, timedelta

import pytest
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import Chat, Message
from sqlalchemy import func, select, update

from bots.channelmanager import delivery, interactions, outbox, posts, recurring
from bots.channelmanager.content import ContentError, PostSpec, TextBody, parse_buttons
from bots.channelmanager.formatting import markdown, shorthand
from bots.channelmanager.models import (
    CalendarReservation,
    Delivery,
    Entitlement,
    Occurrence,
    Operation,
    Recurrence,
    Vote,
    VoteBoard,
)
from bots.channelmanager.permissions import AccessDenied
from bots.channelmanager.timing import Rule, calendar_times
from core.db.base import utcnow
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR, admin_member
from tests.bots.channelmanager.test_publishing import channel_sends, drain, setup_post
from tests.conftest import BOT_ID


@pytest.fixture(autouse=True)
def instant_budgets(monkeypatch):
    async def immediate(*args):
        return 0
    monkeypatch.setattr(outbox, "reserve_budget", immediate)


def test_markdown_modes_unicode_nesting_links_and_escapes():
    old = markdown("*👋 _مرحبا_* [site](https://example.com) `a*b`")
    assert old.text == "👋 مرحبا site a*b"
    assert {e.type for e in old.entities} == {"bold", "italic", "text_link", "code"}
    assert next(e for e in old.entities if e.type == "bold").length == 8
    modern = markdown("__a__ ~b~ ||c|| \\. ```py\nx = 1\n```", modern=True)
    assert modern.text == "a b c . x = 1\n"
    assert modern.entities[-1].language == "py"


@pytest.mark.parametrize("text", ["*open", "[x](javascript:foo)", "__open", "text!", "`x", "a\\"])
def test_invalid_markdown_fails_before_transport(text):
    with pytest.raises(ValueError):
        markdown(text, modern=True)


def test_shorthand_transforms_before_utf16_entity_offsets():
    body = shorthand("<b><m>Ab1</><br><sp>سر</><dot><f>X</><inv></>")
    assert body.text == "𝙰𝚋𝟷\nسر•Ｘ\u2063"
    assert next(e for e in body.entities if e.type == "bold").length == 12
    assert next(e for e in body.entities if e.type == "spoiler").offset == 7
    assert "<" not in body.text


@pytest.mark.parametrize("text", ["<m>x</f>", "</>", "<bad>x</>", "<b>open", "<br bad='x'>"])
def test_shorthand_rejects_invalid_markup(text):
    with pytest.raises(ValueError):
        shorthand(text)


def test_rule_month_edges_and_weekday_constraints_are_combined():
    rule = Rule(anchor=datetime(2027, 1, 31, 9, tzinfo=UTC), every_minutes=1440, monthdays=[31])
    times = rule.next(datetime(2027, 2, 1, tzinfo=UTC), 3)
    assert [(p.month, p.day) for p in times] == [(3, 31), (5, 31), (7, 31)]
    filtered = rule.model_copy(update={"weekdays": [2]})
    assert all(p.weekday() == 2 and p.day == 31 for p in filtered.next(datetime(2027, 1, 1, tzinfo=UTC)))


def test_overnight_windows_and_local_wall_clock_anchor():
    rule = Rule(anchor=datetime(2027, 1, 1, tzinfo=UTC), every_minutes=60, window_start=time(22), window_end=time(2))
    assert [p.hour for p in rule.next(datetime(2027, 1, 1, 20, tzinfo=UTC))] == [22, 23, 0, 1, 22]
    assert all(p.date().day <= 2 for p in rule.next(datetime(2027, 1, 1, 20, tzinfo=UTC), 4))


def test_dst_skips_nonexistent_and_ambiguous_times_or_uses_selected_fold():
    spring = Rule(timezone="America/New_York", anchor=datetime(2027, 3, 13, 7, 30, tzinfo=UTC), every_minutes=1440)
    assert spring.next(datetime(2027, 3, 13, 8, tzinfo=UTC), 1)[0] == datetime(2027, 3, 15, 6, 30, tzinfo=UTC)
    fall = Rule(timezone="America/New_York", anchor=datetime(2027, 11, 6, 5, 30, tzinfo=UTC), every_minutes=1440)
    after = datetime(2027, 11, 6, 8, tzinfo=UTC)
    assert fall.next(after, 1)[0].day == 8
    assert fall.model_copy(update={"dst": "earlier"}).next(after, 1)[0].hour == 5
    assert fall.model_copy(update={"dst": "later"}).next(after, 1)[0].hour == 6


def test_rule_start_end_and_calendar_dst_reservations():
    rule = Rule(anchor=datetime(2027, 1, 1, tzinfo=UTC), every_minutes=1440,
        start_at=datetime(2027, 1, 3, tzinfo=UTC), end_at=datetime(2027, 1, 5, tzinfo=UTC))
    assert [p.day for p in rule.next(datetime(2027, 1, 1, tzinfo=UTC))] == [3, 4]
    times = calendar_times([{"weekday": 6, "at": "02:30"}], "America/New_York", datetime(2027, 3, 13, tzinfo=UTC), 2)
    assert [p.day for p in times] == [21, 28]
    assert calendar_times([{"weekday": 6, "at": "02:30"}], "America/New_York", datetime(2027, 3, 13, tzinfo=UTC), 1, {times[0]}) == [times[1]]


async def test_vote_idempotency_change_closure_and_version_scope(chm, api):
    spec = PostSpec(body=TextBody(text="Vote"), reactions=["👍", "👎"])
    post = await setup_post(chm, api, spec)
    svc = chm.extras["posts"]
    post = await svc.publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    target = (await svc.view(post.id, OPERATOR)).deliveries[0]
    assert await interactions.cast(chm, target.id, 1, 77, 40)
    assert not await interactions.cast(chm, target.id, 1, 77, 40)
    assert await interactions.cast(chm, target.id, 1, 77, 41)
    await drain(chm)
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(Vote)) == 1
        assert (await session.scalar(select(Vote))).choice == 41
    assert "1" in api.calls("EditMessageReplyMarkup")[-1].reply_markup.inline_keyboard[0][1].text
    await interactions.close(chm, post.id, OPERATOR, post.generation)
    with pytest.raises(ContentError, match="closed"):
        await interactions.cast(chm, target.id, 1, 88, 40)
    await drain(chm)
    post = await svc.edit(post.id, OPERATOR, post.generation, spec.model_copy(update={"reactions": ["A", "B"]}))
    await drain(chm)
    with pytest.raises(ContentError, match="stale"):
        await interactions.cast(chm, target.id, 1, 88, 40)
    assert await interactions.cast(chm, target.id, 2, 88, 40)


async def test_structured_buttons_share_hydration_and_protected_fallback(chm, api):
    buttons = parse_buttons("Info | popup | مرحبا && Copy | copy | hello\nDiscuss | comments | https://t.me/example/1\nShare | share && Like | vote")
    post = await setup_post(chm, api, PostSpec(body=TextBody(text="Buttons"), buttons=buttons))
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    sent = channel_sends(api)[0].reply_markup
    assert sent.inline_keyboard[0][0].callback_data.startswith("chi:")
    assert sent.inline_keyboard[0][1].copy_text.text == "hello"
    assert "t.me%2Fc%2F" in api.calls("EditMessageReplyMarkup")[-1].reply_markup.inline_keyboard[-1][0].url
    with pytest.raises(ValueError):
        PostSpec(body=TextBody(text="Protected"), buttons=buttons, protected=True)
    with pytest.raises(ValueError):
        parse_buttons("Style | danger | red")


async def test_presets_are_personal_and_applied_values_are_snapshots(chm, api):
    post = await setup_post(chm, api)
    svc = chm.extras["presets"]
    first = await svc.save(OPERATOR, "Links", "buttons", {"buttons": [[{"text": "Old", "url": "https://example.com"}]]})
    with pytest.raises(AccessDenied):
        await svc.get(first.id, 77)
    await svc.apply(first.id, post.id, OPERATOR, post.generation)
    await svc.save(OPERATOR, "Links", "buttons", {"buttons": [[{"text": "New", "url": "https://example.com"}]]}, preset_id=first.id, generation=first.generation)
    assert (await chm.extras["posts"].view(post.id, OPERATOR)).spec.buttons[0][0].text == "Old"
    with pytest.raises(ContentError, match="stale"):
        await svc.delete(first.id, OPERATOR, first.generation)


async def make_series(chm, api, monkeypatch, *, replace=False):
    post = await setup_post(chm, api)
    point = utcnow().replace(second=0, microsecond=0) + timedelta(minutes=1)
    rule = Rule(anchor=point, every_minutes=60)
    series = await chm.extras["recurring"].configure(post.id, OPERATOR, post.generation, rule, replace_previous=replace)
    clock = [point]
    for module in (outbox, posts, delivery, recurring):
        monkeypatch.setattr(module, "utcnow", lambda: clock[0])
    api.responses["SendMessage"] = lambda method: Message(message_id=1000 + len(api.calls("SendMessage")), date=clock[0],
        chat=Chat(id=int(method.chat_id), type="channel" if int(method.chat_id) < 0 else "private"))
    return post, series, clock


async def test_duplicate_sweeps_and_restart_keep_independent_occurrences(chm, api, monkeypatch):
    root, _series, clock = await make_series(chm, api, monkeypatch)
    svc = chm.extras["recurring"]
    assert await svc.sweep() == 1 and await svc.sweep() == 0
    await drain(chm)
    clock[0] += timedelta(hours=1)
    assert await recurring.RecurrenceService(chm).sweep() == 1
    await drain(chm)
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(Occurrence)) == 2
        assert await session.scalar(select(func.count()).select_from(Delivery)) == 2
    assert len(channel_sends(api)) == 2
    current = await chm.extras["posts"].view(root.id, OPERATOR)
    with pytest.raises(ContentError, match="series_template"):
        await chm.extras["posts"].publish(root.id, OPERATOR, current.post.generation)


async def test_replacement_only_deletes_after_success_and_retains_old_on_failure(chm, api, monkeypatch):
    _, _series, clock = await make_series(chm, api, monkeypatch, replace=True)
    svc = chm.extras["recurring"]
    await svc.sweep()
    await drain(chm)
    clock[0] += timedelta(hours=1)
    api.responses["SendMessage"] = lambda method: TelegramForbiddenError(method=method, message="failed replacement")
    await svc.sweep()
    await drain(chm)
    assert not api.calls("DeleteMessage")
    api.responses.pop("SendMessage")
    clock[0] += timedelta(hours=1)
    await svc.sweep()
    await drain(chm)
    assert len(api.calls("DeleteMessage")) == 1


async def test_recurrence_downtime_pause_and_shared_target_permissions(chm, api, monkeypatch):
    root, series, clock = await make_series(chm, api, monkeypatch)
    clock[0] += timedelta(days=3)
    assert await chm.extras["recurring"].sweep() == 0
    async with chm.sm() as session:
        row = await session.get(Recurrence, (BOT_ID, series.id))
        assert row.last_skipped_at and row.next_at >= clock[0]
    root = (await chm.extras["posts"].view(root.id, OPERATOR)).post
    api.responses["GetChatMember"] = lambda method: admin_member(method.user_id)
    with pytest.raises(AccessDenied, match="series_creator"):
        await chm.extras["posts"].targets(root.id, 77, root.generation, [CHANNEL_ID])
    paused = await chm.extras["recurring"].toggle(series.id, OPERATOR, series.generation, active=False)
    assert paused.status == "paused" and await chm.extras["recurring"].sweep() == 0


async def test_shared_template_edits_only_affect_future_occurrences(chm, api, monkeypatch):
    root, _series, clock = await make_series(chm, api, monkeypatch)
    await chm.extras["recurring"].sweep()
    await drain(chm)
    root = (await chm.extras["posts"].view(root.id, OPERATOR)).post
    await chm.extras["posts"].edit(root.id, OPERATOR, root.generation, PostSpec(body=TextBody(text="New shared version")))
    clock[0] += timedelta(hours=1)
    await chm.extras["recurring"].sweep()
    await drain(chm)
    assert [m.text for m in channel_sends(api)] == ["Hello", "New shared version"]
    async with chm.sm() as session:
        assert [o.root_version for o in (await session.scalars(select(Occurrence).order_by(Occurrence.scheduled_at))).all()] == [1, 2]


async def make_batch(chm, api, count=2):
    await chm.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
    svc = chm.extras["batches"]
    batch = await svc.create(CHANNEL_ID, OPERATOR)
    for index in range(count):
        await svc.add(batch.id, OPERATOR, batch.generation, PostSpec(body=TextBody(text=f"Item {index}")), str(index))
        batch = await svc.get(batch.id, OPERATOR)
    return batch


async def test_batch_defaults_remove_restart_and_atomic_quota_rollback(chm, api):
    batch = await make_batch(chm, api)
    svc = chm.extras["batches"]
    await svc.remove(batch.id, OPERATOR, batch.generation)
    batch = await svc.get(batch.id, OPERATOR)
    assert len(await svc.items(batch.id, OPERATOR)) == 1
    await svc.add(batch.id, OPERATOR, batch.generation, PostSpec(body=TextBody(text="Replacement")), "new-input")
    batch = await svc.get(batch.id, OPERATOR)
    async with chm.sm() as session:
        await session.execute(update(Entitlement).values(max_schedules=1))
        await session.commit()
    with pytest.raises(ContentError, match="limit"):
        await svc.schedule(batch.id, OPERATOR, batch.generation, start=utcnow() + timedelta(hours=1))
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(Delivery)) == 0
    assert (await svc.get(batch.id, OPERATOR)).status == "collecting"


async def test_calendar_reservations_stale_preview_and_cancel_release(chm, api):
    first = await make_batch(chm, api)
    second = await make_batch(chm, api)
    svc = chm.extras["batches"]
    calendar = await svc.save_calendar(CHANNEL_ID, OPERATOR, "Daily", "UTC", [{"weekday": day, "at": "09:00"} for day in range(7)])
    start = utcnow() + timedelta(hours=1)
    times = await svc.preview(first.id, OPERATOR, start=start, calendar_id=calendar.id)
    first = await svc.schedule(first.id, OPERATOR, first.generation, start=start, calendar_id=calendar.id, expected=times)
    with pytest.raises(ContentError, match="stale_plan"):
        await svc.schedule(second.id, OPERATOR, second.generation, start=start, calendar_id=calendar.id, expected=times)
    more = await svc.preview(second.id, OPERATOR, start=start, calendar_id=calendar.id)
    assert set(times).isdisjoint(more)
    await svc.cancel(first.id, OPERATOR, first.generation)
    assert await svc.preview(second.id, OPERATOR, start=start, calendar_id=calendar.id) == times
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(CalendarReservation)) == 0


async def test_batch_confirmation_detects_content_changes(chm, api):
    batch = await make_batch(chm, api, 1)
    svc = chm.extras["batches"]
    item = (await svc.items(batch.id, OPERATOR))[0]
    view = await chm.extras["posts"].view(item.post_id, OPERATOR)
    expected = {item.post_id: view.post.generation}
    await chm.extras["posts"].edit(item.post_id, OPERATOR, view.post.generation, PostSpec(body=TextBody(text="Changed")))
    with pytest.raises(ContentError, match="stale_plan"):
        await svc.schedule(batch.id, OPERATOR, batch.generation, expected_posts=expected)


async def test_individual_post_cancel_releases_its_future_calendar_slot(chm, api):
    batch = await make_batch(chm, api, 1)
    svc = chm.extras["batches"]
    calendar = await svc.save_calendar(CHANNEL_ID, OPERATOR, "Daily", "UTC", [{"weekday": d, "at": "09:00"} for d in range(7)])
    start = utcnow() + timedelta(hours=1)
    times = await svc.preview(batch.id, OPERATOR, start=start, calendar_id=calendar.id)
    await svc.schedule(batch.id, OPERATOR, batch.generation, start=start, calendar_id=calendar.id, expected=times)
    item = (await svc.items(batch.id, OPERATOR))[0]
    view = await chm.extras["posts"].view(item.post_id, OPERATOR)
    await chm.extras["posts"].cancel(item.post_id, OPERATOR, view.post.generation)
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(CalendarReservation)) == 0


async def test_template_pause_cancels_unsent_occurrence_and_resume_skips_backlog(chm, api, monkeypatch):
    root, series, clock = await make_series(chm, api, monkeypatch)
    await chm.extras["recurring"].sweep()
    paused = await chm.extras["recurring"].toggle(series.id, OPERATOR, series.generation, active=False)
    await drain(chm)
    assert not channel_sends(api)
    clock[0] += timedelta(days=2)
    resumed = await chm.extras["recurring"].toggle(series.id, OPERATOR, paused.generation, active=True)
    assert resumed.next_at > clock[0]
    view = await chm.extras["posts"].view(root.id, OPERATOR)
    await chm.extras["posts"].cancel(root.id, OPERATOR, view.post.generation, detach=True)
    assert (await chm.extras["recurring"].get(series.id, OPERATOR)).status == "paused"


async def test_recurrence_lost_rights_pauses_without_creating_work(chm, api, monkeypatch):
    _, series, _clock = await make_series(chm, api, monkeypatch)
    api.responses["GetChatMember"] = lambda method: admin_member(method.user_id, post=False)
    assert await chm.extras["recurring"].sweep() == 0
    async with chm.sm() as session:
        row = await session.get(Recurrence, (BOT_ID, series.id))
        assert row.status == "paused" and row.error_code == "rights_lost"
        assert await session.scalar(select(func.count()).select_from(Occurrence)) == 0


async def test_each_occurrence_has_its_own_delete_timer(chm, api, monkeypatch):
    root, _series, clock = await make_series(chm, api, monkeypatch)
    view = await chm.extras["posts"].view(root.id, OPERATOR)
    await chm.extras["posts"].edit(root.id, OPERATOR, view.post.generation,
        PostSpec(body=TextBody(text="Timed recurrence"), delete_after_seconds=600))
    await chm.extras["recurring"].sweep()
    await drain(chm)
    clock[0] += timedelta(hours=1)
    await chm.extras["recurring"].sweep()
    await drain(chm)
    async with chm.sm() as session:
        targets = (await session.scalars(select(Delivery).order_by(Delivery.sent_at))).all()
        assert len(targets) == 2
        for target in targets:
            job = await session.get(Operation, (BOT_ID, target.delete_op))
            # Completed cleanup changes run_at; only pending timers retain their due instant.
            if job.status == "pending":
                assert job.run_at == target.sent_at + timedelta(seconds=600)


async def test_delivery_followups_are_serialized_before_remote_dispatch(chm, api):
    spec = PostSpec(body=TextBody(text="Two followups"), pin=True, buttons=parse_buttons("Share | share"))
    post = await setup_post(chm, api, spec)
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    while True:
        op = await outbox.claim(chm)
        await outbox.execute(chm, op)
        if op.kind == "publish":
            break
    first, second = await outbox.claim(chm), await outbox.claim(chm)
    assert {first.kind, second.kind} == {"pin", "markup"}
    assert await outbox.mark_dispatched(chm, first)
    first.dispatched = True
    await outbox.execute(chm, second)
    async with chm.sm() as session:
        held = await session.get(Operation, (BOT_ID, second.id))
        assert held.status == "pending" and not held.dispatched and held.error_code == "delivery_busy"
    await delivery.complete(chm, first, outbox.PostJob.model_validate(first.payload), "succeeded", result=True)
    async with chm.sm() as session:
        await session.execute(update(Operation).where(Operation.id == second.id).values(run_at=utcnow()))
        await session.commit()
    await drain(chm)


async def test_recurring_shared_edit_cannot_cross_missing_target_permission(chm, api):
    root = await setup_post(chm, api, second=True)
    other = CHANNEL_ID - 1
    root = await chm.extras["posts"].targets(root.id, OPERATOR, root.generation, [CHANNEL_ID, other])
    await chm.extras["recurring"].configure(root.id, OPERATOR, root.generation,
        Rule(anchor=(utcnow() + timedelta(hours=1)).replace(second=0, microsecond=0)))
    api.responses["GetChatMember"] = lambda method: admin_member(method.user_id, post=method.chat_id != other or method.user_id != 77)
    root = (await chm.extras["posts"].view(root.id, OPERATOR)).post
    with pytest.raises(AccessDenied):
        await chm.extras["posts"].edit(root.id, 77, root.generation, PostSpec(body=TextBody(text="Forbidden extension")))


async def test_replacement_obligation_survives_interrupted_cleanup_planning(chm, api, monkeypatch):
    _root, _series, clock = await make_series(chm, api, monkeypatch, replace=True)
    await chm.extras["recurring"].sweep()
    await drain(chm)
    original = recurring.settle_replacements
    async def interrupted(*args, **kwargs):
        return None
    monkeypatch.setattr(recurring, "settle_replacements", interrupted)
    clock[0] += timedelta(hours=1)
    await chm.extras["recurring"].sweep()
    await drain(chm)
    assert not api.calls("DeleteMessage")
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(Delivery).where(Delivery.replace_pending.is_(True))) == 1
    monkeypatch.setattr(recurring, "settle_replacements", original)
    await original(chm)
    await original(chm)
    await drain(chm)
    assert len(api.calls("DeleteMessage")) == 1


async def test_body_edit_preserves_votes_and_does_not_reopen_closed_ballot(chm, api):
    spec = PostSpec(body=TextBody(text="Before"), reactions=["A", "B"])
    post = await setup_post(chm, api, spec)
    post = await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    target = (await chm.extras["posts"].view(post.id, OPERATOR)).deliveries[0]
    await interactions.cast(chm, target.id, 1, 77, 40)
    await interactions.close(chm, post.id, OPERATOR, post.generation)
    await drain(chm)
    await chm.extras["posts"].edit(post.id, OPERATOR, post.generation, spec.model_copy(update={"body": TextBody(text="After")}))
    await drain(chm)
    async with chm.sm() as session:
        assert (await session.get(VoteBoard, (BOT_ID, target.id, 2))).closed
        assert (await session.get(Vote, (BOT_ID, target.id, 2, 77))).choice == 40
    with pytest.raises(ContentError, match="closed"):
        await interactions.cast(chm, target.id, 2, 88, 41)


async def test_shared_template_edit_cancels_obsolete_unsent_occurrence(chm, api, monkeypatch):
    root, _series, clock = await make_series(chm, api, monkeypatch)
    await chm.extras["recurring"].sweep()
    root = (await chm.extras["posts"].view(root.id, OPERATOR)).post
    await chm.extras["posts"].edit(root.id, OPERATOR, root.generation, PostSpec(body=TextBody(text="Current template")))
    await drain(chm)
    assert not channel_sends(api)
    clock[0] += timedelta(hours=1)
    await chm.extras["recurring"].sweep()
    await drain(chm)
    assert [m.text for m in channel_sends(api)] == ["Current template"]
