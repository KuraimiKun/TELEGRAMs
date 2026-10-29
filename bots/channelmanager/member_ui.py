"""Private, actor-bound configuration and admission-queue menus."""

from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, CopyTextButton, InlineKeyboardButton, Message

from bots.channelmanager.content import ContentError, from_message, parse_buttons
from bots.channelmanager.member_specs import CLEAN_SERVICES, EVENTS, MemberSpec
from bots.channelmanager.members import rights, start_token
from bots.channelmanager.permissions import AccessDenied as AccessError
from bots.channelmanager.publishing_ui import kb, owner
from core.i18n import Translate
from core.ui.respond import show
from core.ui.text import esc


class MemberInput(StatesGroup):
    value = State()


class MemberCb(CallbackData, prefix="ch5"):
    a: str
    x: str
    g: int
    u: int


def button(text, action, resource, generation, actor):
    return InlineKeyboardButton(text=text, callback_data=MemberCb(a=action, x=str(resource), g=generation, u=actor).pack())


def duration(value):
    match = re.fullmatch(r"(\d+)\s*([smhd])", value.strip())
    if not match:
        raise ContentError("time")
    return int(match[1]) * {"s": 1, "m": 60, "h": 3600, "d": 86400}[match[2]]


def build_router(ctx):
    router = Router(name=f"chm_members_{ctx.slug}")
    router.message.filter(F.chat.type == "private")
    router.callback_query.filter(F.message.chat.type == "private")
    svc = ctx.extras["members"]

    async def choose(event, t, offset=0):
        channels = await ctx.extras["channelmanager"].known(owner(event), offset=offset)
        rows = []
        for channel in channels:
            try:
                await rights(ctx, channel.channel_id, owner(event))
            except (AccessError, TelegramAPIError):
                continue
            rows.append([button(channel.title[:60], "chan", channel.channel_id, 0, owner(event))])
        if offset:
            rows.append([button("◀️", "choose", "0", max(0, offset - 10), owner(event))])
        if len(channels) == 10:
            rows.append([button("▶️", "choose", "0", offset + 10, owner(event))])
        await show(event, t("chm5-choose"), kb(*rows))

    async def panel(event, channel_id, t, section="main"):
        row = await svc.config(channel_id, owner(event))
        spec, generation = MemberSpec.model_validate(row.spec) if row else MemberSpec(), row.generation if row else 0
        def b(key, action):
            return button(t(key), action, channel_id, generation, owner(event))
        text = t("chm5-policy", channel=str(channel_id), state=t("chm4-yes" if spec.enabled else "chm4-no"),
            mode=t(f"chm5-mode-{spec.mode}"), captcha=t("chm4-yes" if spec.captcha else "chm4-no"), required=str(len(spec.required)))
        if section == "main":
            rows = [[button(t("chm5-queue"), "queue", channel_id, 0, owner(event)), b("chm5-bulk", "bulk")],
                [b("chm5-mode", "mode"), b("chm5-delay", "delay")],
                [b("chm5-expiry", "expiry"), b("chm5-captcha", "captcha")],
                [b("chm5-attempts", "attempts"), b("chm5-required", "required")],
                [b("chm5-content", "content"), b("chm5-filters", "filters")],
                [b("chm5-departure", "departure"), b("chm5-events", "events")],
                [b("chm5-results", "results")], [b("chm5-disable" if spec.enabled else "chm5-enable", "off" if spec.enabled else "ask")]]
            rows.insert(4, [b("chm6-invitations", "invites")])
        elif section == "invites":
            text += "\n" + t("chm6-invite-policy", count=str(spec.invite_threshold), seconds=str(spec.invite_timeout_seconds), bypass=t("chm4-yes" if spec.invite_timeout_bypass else "chm4-no"))
            rows = [[b("chm6-invite-threshold", "threshold"), b("chm6-invite-timeout", "invtime")], [b("chm6-invite-bypass", "bypass")]]
        elif section == "content":
            rows = [[b(f"chm5-{field}", field), b("chm-btn-buttons", field + "btn"), b("chm-btn-preview", field + "pre")]
                for field in ("intro", "welcome", "goodbye")]
        elif section == "filters":
            text += "\n" + t("chm5-filter-summary", block=t("chm4-yes" if spec.profile.total_block else "chm4-no"),
                rate=str(spec.profile.max_per_ten_seconds or "—"), outcome=t(f"chm5-outcome-{spec.profile.outcome}"))
            rows = [[b("chm5-total-block", "block"), b("chm5-rate", "rate")], [b("chm5-outcome", "outcome")],
                [b("chm5-names", "names"), b("chm5-usernames", "usernames")],
                [b("chm5-alphabet", "alphabet"), b("chm5-languages", "languages")],
                [b("chm5-unknown-language", "unknown")]]
        elif section == "departure":
            text += "\n" + t("chm5-departure-summary", ban=t("chm4-yes" if spec.departure_ban else "chm4-no"),
                duration=str(spec.ban_seconds) if spec.ban_seconds else t("chm5-permanent"), group=str(spec.linked_group or "—"))
            rows = [[b("chm5-ban", "ban"), b("chm5-ban-duration", "banduration")], [b("chm5-linked", "linked")]]
        else:
            text += "\n" + t("chm5-event-summary", log=str(spec.log_channel or "—"), language=spec.log_language,
                events=", ".join(spec.log_events), cleanup=", ".join(spec.cleanup) or "—")
            rows = [[b("chm5-log-channel", "log"), b("chm5-log-language", "loglang")],
                [b("chm5-log-events", "logevents"), b("chm5-cleanup", "cleanup")]]
        if section != "main":
            rows.append([b("btn-back", "chan")])
        await show(event, text, kb(*rows))

    async def request_panel(event, request_id, t):
        row, actions = await svc.request(request_id, owner(event))
        text = t("chm5-request", user=str(row.user_id), generation=str(row.generation), status=t(f"chm5-status-{row.status}"),
            code=esc(row.error_code or row.filter_code or "—"), attempts=str(row.captcha_attempts),
            solved=t("chm4-yes" if row.captcha_solved else "chm4-no"), required=str(row.required_index), expiry=row.expires_at.isoformat())
        rows = []
        for action in actions:
            text += "\n" + t("chm5-action", kind=t(f"chm5-kind-{action.kind}"), state=t(f"chm4-state-{action.status}"), code=esc(action.error_code or "—"))
            if action.status == "failed":
                rows.append([button(t("chm4-retry", id=action.id[:8]), "r", action.id, 0, owner(event))])
        if row.status in {"pending", "held"}:
            rows.append([button(t("chm5-release"), "release", row.id, row.generation, owner(event)),
                button(t("chm5-decline"), "decline", row.id, row.generation, owner(event))])
            if row.status == "held":
                rows.append([button(t("chm5-adopt"), "adopt", row.id, row.generation, owner(event))])
            username = ctx.username or (await ctx.bot.get_me()).username
            if username:
                rows.append([InlineKeyboardButton(text=t("chm5-copy-start"), copy_text=CopyTextButton(
                    text=f"https://t.me/{username}?start={start_token(ctx, row)}"))])
        rows.append([button(t("chm-btn-refresh"), "request", row.id, row.generation, owner(event))])
        await show(event, text[:3900], kb(*rows[:20]))

    async def error(event, t, exc):
        await show(event, t("chm-error-access" if isinstance(exc, AccessError) else "chm5-invalid"))

    @router.message(Command("members"))
    async def command(message: Message, state: FSMContext, t: Translate):
        await state.clear()
        await choose(message, t)

    known_commands = ~F.text.regexp(r"^/(?:cancel|start|help|channels|connect|posts|newpost|advanced|automation|recurring|multipost|presets|calendars|reactions|signature|timezone)(?:\s|@|$)")

    @router.message(MemberInput.value, known_commands)
    async def value(message: Message, state: FSMContext, t: Translate):
        data = await state.get_data()
        if data.get("owner") != owner(message):
            return
        try:
            channel_id, field = data["channel"], data["field"]
            row = await svc.config(channel_id, owner(message))
            if (row.generation if row else 0) != data["generation"]:
                raise ContentError("stale")
            spec = MemberSpec.model_validate(row.spec) if row else MemberSpec()
            values = spec.model_dump(mode="json")
            text = (message.text or "").strip()
            section = "main"
            if field in {"intro", "welcome", "goodbye"}:
                target = "introduction" if field == "intro" else field
                values[target] = None if text == "-" else from_message(message, ctx.bot_id).model_dump(mode="json")
                section = "content"
            elif field.endswith("btn"):
                target = "introduction" if field == "introbtn" else field[:-3]
                if values[target] is None:
                    raise ContentError("member_content")
                content = dict(values[target])
                content["buttons"] = [[b.model_dump(mode="json") for b in r] for r in parse_buttons(text)]
                values[target], section = content, "content"
            elif field in {"delay", "expiry", "banduration"}:
                values[{"delay": "delay_seconds", "expiry": "expires_seconds", "banduration": "ban_seconds"}[field]] = None if field == "banduration" and text == "permanent" else duration(text)
                section = "departure" if field == "banduration" else "main"
            elif field == "attempts":
                values["captcha_attempts"] = int(text)
            elif field in {"threshold", "invtime"}:
                values["invite_threshold" if field == "threshold" else "invite_timeout_seconds"] = int(text) if field == "threshold" else duration(text)
                if field == "threshold" and int(text) == 0:
                    values["invite_timeout_bypass"] = False
                section = "invites"
            elif field == "required":
                values["required"] = [] if text == "-" else [{"chat_id": int(line.split(maxsplit=1)[0]), "url": line.split(maxsplit=1)[1]} for line in text.splitlines()]
            elif field in {"rate", "names", "usernames", "alphabet", "languages"}:
                policy = dict(values["profile"])
                if field == "rate":
                    policy["max_per_ten_seconds"] = None if text == "-" else int(text)
                elif field in {"names", "usernames"}:
                    policy["blocked_names" if field == "names" else "blocked_usernames"] = [] if text == "-" else text.splitlines()
                else:
                    mode, _, rest = text.partition(" ")
                    if mode not in ({"allow", "block", "any"} if field == "languages" else {"allow", "block"}):
                        raise ContentError("profile_filter")
                    policy["language_mode" if field == "languages" else "script_mode"] = mode
                    policy["languages" if field == "languages" else "scripts"] = [v.strip().lower() if field == "languages" else v.strip().upper() for v in rest.split(",") if v.strip()]
                values["profile"], section = policy, "filters"
            elif field in {"linked", "log"}:
                values["linked_group" if field == "linked" else "log_channel"] = None if text == "-" else int(text)
                section = "departure" if field == "linked" else "events"
            elif field in {"logevents", "cleanup"}:
                values["log_events" if field == "logevents" else "cleanup"] = sorted(EVENTS if field == "logevents" else CLEAN_SERVICES) if text == "all" else [] if text == "-" else [v.strip() for v in text.split(",")]
                section = "events"
            elif field == "bulk":
                batch = await svc.prepare_bulk(channel_id, owner(message), 5000 if text == "all" else int(text))
                await state.clear()
                await show(message, t("chm5-bulk-confirm", count=str(len(batch.request_ids))), kb(
                    [button(t("chm-btn-confirm"), "bulkdo", batch.id, batch.config_generation, owner(message))]))
                return
            else:
                raise ContentError("member_policy")
            await svc.save(channel_id, owner(message), MemberSpec.model_validate(values), data["generation"])
            await state.clear()
            await panel(message, channel_id, t, section)
        except (ValueError, AccessError, TelegramAPIError, IndexError) as exc:
            await error(message, t, exc)

    @router.callback_query(MemberCb.filter())
    async def callback(query: CallbackQuery, callback_data: MemberCb, state: FSMContext, t: Translate):
        cb = callback_data
        if cb.u != owner(query):
            await query.answer(t("chm-denied"), show_alert=True)
            return
        try:
            if cb.a != "on":
                await state.clear()
            if cb.a == "choose":
                if not 0 <= cb.g <= 10000:
                    raise ContentError("stale")
                await choose(query, t, cb.g)
            elif cb.a in {"release", "decline", "adopt"}:
                current, _ = await svc.request(cb.x, cb.u)
                if current.generation != cb.g:
                    raise ContentError("stale")
                await svc.decide(cb.x, cb.u, cb.a)
                await request_panel(query, cb.x, t)
            elif cb.a == "request":
                await request_panel(query, cb.x, t)
            elif cb.a == "r":
                await svc.retry(cb.x, cb.u)
                await show(query, t("chm5-retry-queued"))
            elif cb.a == "bulkdo":
                batch = await svc.confirm_bulk(cb.x, cb.u)
                await show(query, t("chm5-bulk-result", **{k: str(v) for k, v in batch.result.items()}))
            else:
                channel_id = int(cb.x)
                row = await svc.config(channel_id, cb.u)
                spec, generation = MemberSpec.model_validate(row.spec) if row else MemberSpec(), row.generation if row else 0
                if cb.a not in {"chan", "queue", "results", "content", "filters", "departure", "events", "invites"} and generation != cb.g:
                    raise ContentError("stale")
                if cb.a in {"chan", "content", "filters", "departure", "events", "invites"}:
                    await panel(query, channel_id, t, "main" if cb.a == "chan" else cb.a)
                elif cb.a == "queue":
                    if not 0 <= cb.g <= 10000:
                        raise ContentError("stale")
                    entries = await svc.requests(channel_id, cb.u, cb.g)
                    rows = [[button(f"{r.user_id} · {t('chm5-status-' + r.status)}", "request", r.id, r.generation, cb.u)] for r in entries]
                    if cb.g:
                        rows.append([button("◀️", "queue", channel_id, max(0, cb.g - 10), cb.u)])
                    if len(entries) == 10:
                        rows.append([button("▶️", "queue", channel_id, cb.g + 10, cb.u)])
                    await show(query, t("chm5-queue"), kb(*rows))
                elif cb.a == "results":
                    rows, text = [], t("chm5-results")
                    for action in await svc.actions(channel_id, cb.u):
                        text += "\n" + t("chm5-action", kind=t(f"chm5-kind-{action.kind}"), state=t(f"chm4-state-{action.status}"), code=esc(action.error_code or "—"))
                        if action.status == "failed":
                            rows.append([button(t("chm4-retry", id=action.id[:8]), "r", action.id, 0, cb.u)])
                    await show(query, text[:3900], kb(*rows[:20]))
                elif cb.a == "ask":
                    await state.set_data({"owner": cb.u, "channel": channel_id, "generation": cb.g})
                    await show(query, t("chm5-enable-confirm"), kb([button(t("chm-btn-confirm"), "on", channel_id, cb.g, cb.u)]))
                elif cb.a in {"on", "off", "mode", "captcha", "block", "outcome", "unknown", "ban", "loglang", "bypass"}:
                    if cb.a == "on" and await state.get_data() != {"owner": cb.u, "channel": channel_id, "generation": cb.g}:
                        raise ContentError("stale")
                    values = spec.model_dump(mode="json")
                    section = "main"
                    if cb.a in {"on", "off"}:
                        values["enabled"] = cb.a == "on"
                    elif cb.a == "mode":
                        modes = ["manual", "immediate", "timed"]
                        values["mode"] = modes[(modes.index(spec.mode) + 1) % 3]
                    elif cb.a in {"block", "unknown", "outcome"}:
                        policy = dict(values["profile"])
                        field = {"block": "total_block", "unknown": "reject_unknown_language", "outcome": "outcome"}[cb.a]
                        policy[field] = ("ban" if policy[field] == "decline" else "decline") if cb.a == "outcome" else not policy[field]
                        values["profile"], section = policy, "filters"
                    elif cb.a == "loglang":
                        values["log_language"], section = "ar" if spec.log_language == "en" else "en", "events"
                    elif cb.a == "bypass":
                        values["invite_timeout_bypass"], section = not spec.invite_timeout_bypass, "invites"
                    else:
                        field = "captcha" if cb.a == "captcha" else "departure_ban"
                        values[field] = not values[field]
                        if field == "departure_ban" and not values[field]:
                            values["linked_group"] = None
                        section = "main" if field == "captcha" else "departure"
                    await svc.save(channel_id, cb.u, MemberSpec.model_validate(values), generation)
                    await state.clear()
                    await panel(query, channel_id, t, section)
                elif cb.a.endswith("pre"):
                    content = getattr(spec, "introduction" if cb.a == "intropre" else cb.a[:-3], None)
                    if content is None:
                        raise ContentError("member_content")
                    await ctx.bot(content.send_method(cb.u, preview=True))
                else:
                    keys = {"intro": "content", "welcome": "content", "goodbye": "content", "introbtn": "buttons", "welcomebtn": "buttons", "goodbyebtn": "buttons",
                        "delay": "duration", "expiry": "duration", "banduration": "ban-duration", "attempts": "attempts", "required": "required", "rate": "rate",
                        "names": "keywords", "usernames": "keywords", "alphabet": "alphabet", "languages": "languages", "linked": "linked", "log": "log", "logevents": "logevents", "cleanup": "cleanup", "bulk": "bulk", "threshold": "threshold", "invtime": "duration"}
                    if cb.a not in keys:
                        raise ContentError("stale")
                    await state.set_state(MemberInput.value)
                    await state.set_data({"owner": cb.u, "channel": channel_id, "generation": generation, "field": cb.a})
                    await show(query, t("chm6-prompt-threshold") if cb.a == "threshold" else t(f"chm5-prompt-{keys[cb.a]}"))
        except (ValueError, AccessError, TelegramAPIError) as exc:
            await error(query, t, exc)

    @router.callback_query(F.data.startswith("ch5:"))
    async def malformed(query: CallbackQuery, t: Translate):
        await query.answer(t("chm-denied"), show_alert=True)

    return router
