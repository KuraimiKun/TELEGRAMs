"""Localized advanced publishing menus; activation and calendar plans have server-bound confirmations."""

from __future__ import annotations

import re
from datetime import datetime, time
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bots.channelmanager import interactions
from bots.channelmanager.content import ContentError, PostSpec, from_message, parse_buttons
from bots.channelmanager.models import Calendar
from bots.channelmanager.permissions import AccessDenied, publishing_access
from bots.channelmanager.posts import parse_time
from bots.channelmanager.publishing_ui import Composer, kb, owner
from bots.channelmanager.publishing_ui import btn as post_btn
from bots.channelmanager.timing import Rule
from core.db.base import utcnow
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.respond import show
from core.ui.text import esc


class AdvancedInput(StatesGroup):
    value = State()
    collect = State()


class AdvancedCb(CallbackData, prefix="cha"):
    a: str
    x: str
    g: int
    u: int


def button(text, action, resource, generation, user_id):
    from aiogram.types import InlineKeyboardButton
    return InlineKeyboardButton(text=text, callback_data=AdvancedCb(a=action, x=str(resource), g=generation, u=user_id).pack())


async def post_panel(ctx, event, post_id: str, generation: int, t: Translate):
    view = await ctx.extras["posts"].view(post_id, owner(event))
    if view.post.generation != generation:
        raise ContentError("stale")
    def b(key, action):
        return button(t(key), action, post_id, generation, owner(event))
    rows = [[b("chm3-markdown", "md"), b("chm3-markdown2", "md2"), b("chm3-shorthand", "short")],
        [b("chm3-reactions", "react"), b("chm3-apply-set", "sets")], [b("chm3-repeat", "repeat")],
        [b("chm3-close-votes", "close")], [post_btn(t("btn-back"), "view", post_id, generation, owner(event))]]
    await show(event, t("chm3-post-panel", targets=", ".join(str(c) for c in view.post.target_ids)), kb(*rows))


def parse_rule(text: str, timezone: str) -> tuple[Rule, bool]:
    """Human-readable key=value lines; IANA timezone comes from the selected channel."""
    values = {}
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if not sep or key.strip() in values:
            raise ContentError("time")
        values[key.strip()] = value.strip()
    if set(values) - {"every", "anchor", "weekdays", "monthdays", "window", "start", "end", "dst", "replace"}:
        raise ContentError("time")
    duration = values.get("every", "24h")
    if len(duration) < 2 or duration[-1] not in "mhd":
        raise ContentError("time")
    minutes = int(duration[:-1]) * {"m": 1, "h": 60, "d": 1440}[duration[-1]]
    data = {"timezone": timezone, "anchor": parse_time(values["anchor"], timezone), "every_minutes": minutes}
    if "weekdays" in values:
        weekdays = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
        data["weekdays"] = [weekdays[v.strip()] for v in values["weekdays"].split(",")]
    if "monthdays" in values:
        data["monthdays"] = [int(v) for v in values["monthdays"].split(",")]
    if "window" in values:
        start, end = values["window"].split("-")
        data.update(window_start=time.fromisoformat(start), window_end=time.fromisoformat(end))
    for field in ("start", "end"):
        if field in values:
            data[f"{field}_at"] = parse_time(values[field], timezone)
    if "dst" in values:
        data["dst"] = values["dst"]
    if values.get("replace", "no") not in {"yes", "no"}:
        raise ContentError("time")
    return Rule.model_validate(data), values.get("replace") == "yes"


def parse_calendar(text: str) -> tuple[str, list[dict]]:
    lines = text.strip().splitlines()
    if len(lines) < 2:
        raise ContentError("time")
    days = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
    slots = []
    for line in lines[1:]:
        day, clock = line.split()
        slots.append({"weekday": days[day], "at": clock})
    return lines[0].strip(), slots


def build_router(ctx: BotContext) -> Router:
    router = Router(name=f"chm_advanced_{ctx.slug}")
    router.message.filter(F.chat.type == "private")
    router.callback_query.filter(F.message.chat.type == "private")
    posts, batches, presets, recurring = (ctx.extras[k] for k in ("posts", "batches", "presets", "recurring"))

    def b(t, key, action, resource, generation, actor):
        return button(t(key), action, resource, generation, actor)

    async def error(event, t, exc):
        codes = {"stale", "busy", "limit", "time", "buttons", "targets", "access", "content"}
        advanced = {"name", "closed", "series_draft", "series_template", "batch_queued", "stale_plan"}
        code = str(exc) if isinstance(exc, ContentError) else "access" if isinstance(exc, AccessDenied) else "content"
        if code == "release_stage":
            await show(event, t("chm7-paused"))
            return
        key = f"chm3-error-{code}" if code in advanced else f"chm-error-{code}" if code in codes else "chm-error-content"
        await show(event, t(key))

    async def prompt(event, state, t, key, action, **data):
        await state.set_state(AdvancedInput.value)
        await state.set_data({"owner": owner(event), "action": action, **data})
        await show(event, t(key))

    async def hub(event, t):
        actor = owner(event)
        await show(event, t("chm3-hub"), kb(
            [b(t, "chm3-recurring", "series", "0", 0, actor), b(t, "chm3-batches", "batches", "0", 0, actor)],
            [b(t, "chm3-presets", "presets", "0", 0, actor), b(t, "chm3-calendars", "calendars", "0", 0, actor)]))

    async def choose_channel(event, t, action, offset=0):
        channels = await ctx.extras["channelmanager"].known(owner(event), offset=offset)
        rows = []
        for channel in channels:
            try:
                await publishing_access(ctx, channel.channel_id, owner(event))
            except AccessDenied:
                continue
            if channel.status == "active":
                rows.append([button(channel.title[:60], action, channel.channel_id, channel.generation, owner(event))])
        if offset:
            rows.append([button("◀️", f"pg{action}", 0, max(0, offset - 10), owner(event))])
        if len(channels) == 10:
            rows.append([button("▶️", f"pg{action}", 0, offset + 10, owner(event))])
        await show(event, t("chm-choose-channel"), kb(*rows))

    async def batch_panel(event, batch_id, t, offset=0):
        batch = await batches.get(batch_id, owner(event))
        items = await batches.items(batch_id, owner(event))
        rows = []
        states = []
        for index, item in enumerate(items):
            view = await posts.view(item.post_id, owner(event))
            states.append(t(f"chm-post-state-{view.state}"))
            if offset <= index < offset + 10:
                rows.append([post_btn(f"{item.position} · {t(f'chm-post-state-{view.state}')}", "view", item.post_id, view.post.generation, owner(event))])
        def action(key, a):
            return b(t, key, a, batch.id, batch.generation, owner(event))
        if offset:
            rows.append([action("btn-back", f"page{max(0, offset - 10)}")])
        if len(items) > offset + 10:
            rows.append([button("▶️", f"page{offset + 10}", batch.id, batch.generation, owner(event))])
        if batch.status in {"collecting", "ready"}:
            rows += [[action("chm3-add", "collect"), action("chm3-finish", "ready")],
                [action("chm3-restart", "restart"), action("chm3-remove", "remove")],
                [action("chm3-shared-buttons", "bb"), action("chm3-shared-reactions", "br")],
                [button(f"{t('chm-btn-buttons')}: {t('chm3-mode-' + batch.buttons_mode)}", "bm", batch.id, batch.generation, owner(event)),
                 button(f"{t('chm3-reactions')}: {t('chm3-mode-' + batch.reactions_mode)}", "rm", batch.id, batch.generation, owner(event))],
                [action("chm3-batch-options", "batchopts"), action("chm3-plan", "plan")]]
        if batch.status != "cancelled":
            rows.append([action("chm3-cancel-batch", "askcancel")])
        rows.append([action("chm-btn-refresh", "batch")])
        text = t("chm3-batch-panel", id=batch.id, count=str(len(items)), status=t(f"chm3-batch-{batch.status}"), progress=", ".join(states))
        await show(event, text, kb(*rows))

    async def series_panel(event, series_id, t):
        series = await recurring.get(series_id, owner(event))
        view = await posts.view(series.post_id, owner(event))
        rule = Rule.model_validate(series.rule)
        times = rule.next(utcnow())
        rendered = "\n".join(p.astimezone(ZoneInfo(rule.timezone)).isoformat() for p in times)
        text = t("chm3-series-panel", id=series.id, status=t(f"chm3-series-{series.status}"), times=rendered,
                 targets=", ".join(str(c) for c in view.post.target_ids), error=series.error_code or "—")
        rows = [[post_btn(t("chm-btn-body"), "view", view.post.id, view.post.generation, owner(event))]]
        if view.post.creator_id == owner(event):
            rows += [[b(t, "chm3-pause" if series.status == "active" else "chm3-resume", "pause" if series.status == "active" else "resume", series.id, series.generation, owner(event)),
                      b(t, "chm3-edit-rule", "rule", series.id, series.generation, owner(event))]]
        await show(event, text, kb(*rows))

    async def library(event, action, t, offset=0):
        actor = owner(event)
        if action == "presets":
            rows = [[button(p.name, "preset", p.id, p.generation, actor)] for p in await presets.list_for(actor)]
            rows += [[b(t, "chm3-new-buttons", "newbuttons", "0", 0, actor), b(t, "chm3-new-channels", "newchannels", "0", 0, actor)]]
        elif action == "batches":
            rows = [[button(batch.id, "batch", batch.id, batch.generation, actor)] for batch in await batches.list_for(actor)]
            rows += [[b(t, "chm3-new-batch", "batchchoose", "0", 0, actor)]]
        else:
            rows = [[button(series.id, "seriesview", series.id, series.generation, actor)] for series in await recurring.list_for(actor)]
        # Resource rows precede create actions. Slice only resources and retain the actions.
        tail = rows[-1:] if action in {"presets", "batches"} else []
        resources = rows[:-1] if tail else rows
        rows = resources[offset:offset + 10]
        if offset:
            rows.append([button("◀️", action, "0", max(0, offset - 10), actor)])
        if len(resources) > offset + 10:
            rows.append([button("▶️", action, "0", offset + 10, actor)])
        await show(event, t(f"chm3-{action}"), kb(*rows, *tail))

    async def planned(event, state, batch_id, t, *, start=None, calendar_id=None):
        batch = await batches.get(batch_id, owner(event))
        times = await batches.preview(batch.id, owner(event), start=start or utcnow(), calendar_id=calendar_id)
        items = await batches.items(batch.id, owner(event))
        versions = {item.post_id: (await posts.view(item.post_id, owner(event))).post.generation for item in items}
        await state.set_state(None)
        await state.set_data({"owner": owner(event), "batch": batch.id, "generation": batch.generation,
            "start": start.isoformat() if start else None, "calendar": calendar_id,
            "times": [point.isoformat() for point in times], "posts": versions})
        await show(event, t("chm3-confirm-batch", channel=str(batch.channel_id), times="\n".join(p.isoformat() for p in times)), kb(
            [b(t, "chm-btn-confirm-publish", "batchok", batch.id, batch.generation, owner(event))],
            [b(t, "btn-back", "batch", batch.id, batch.generation, owner(event))]))

    @router.message(Command("advanced", "recurring", "multipost", "presets", "calendars", "reactions"))
    async def command(message: Message, state: FSMContext, t: Translate):
        await state.clear()
        command_name = (message.text or "").split()[0].split("@")[0][1:]
        if command_name == "advanced":
            await hub(message, t)
        elif command_name == "calendars":
            await choose_channel(message, t, "channelcal")
        elif command_name == "reactions":
            await choose_channel(message, t, "defaults")
        else:
            await library(message, {"recurring": "series", "multipost": "batches", "presets": "presets"}[command_name], t)

    @router.message(AdvancedInput.collect, ~F.text.startswith("/"))
    async def collect(message: Message, state: FSMContext, t: Translate):
        data = await state.get_data()
        if data.get("owner") != owner(message):
            return
        try:
            batch = await batches.get(data["batch"], owner(message))
            spec = from_message(message, ctx.bot_id)
            post = await batches.add(batch.id, owner(message), data["generation"], spec, str(message.message_id))
            batch = await batches.get(batch.id, owner(message))
            if batch.buttons_mode == "per_item":
                await prompt(message, state, t, "chm3-buttons-prompt", "item_buttons", batch=batch.id, post=post.id, generation=post.generation)
            elif batch.reactions_mode == "per_item":
                await prompt(message, state, t, "chm3-reactions-prompt", "item_reactions", batch=batch.id, post=post.id, generation=post.generation)
            else:
                await state.clear()
                await batch_panel(message, batch.id, t)
        except (ValueError, AccessDenied, TelegramAPIError) as exc:
            await error(message, t, exc)

    @router.message(AdvancedInput.value, ~F.text.startswith("/"))
    async def value(message: Message, state: FSMContext, t: Translate):
        data = await state.get_data()
        if data.get("owner") != owner(message):
            return
        try:
            action, text = data["action"], message.text or ""
            if action == "rule":
                view = await posts.view(data["post"], owner(message), "edit")
                channel = await ctx.extras["channelmanager"].get(view.post.channel_id)
                rule, replace = parse_rule(text, channel.timezone)
                times = rule.next(utcnow())
                if not times:
                    raise ContentError("time")
                await state.set_state(None)
                await state.set_data({**data, "rule": rule.model_dump(mode="json"), "replace": replace})
                await show(message, t("chm3-confirm-series", targets=", ".join(str(c) for c in view.post.target_ids),
                    times="\n".join(p.astimezone(ZoneInfo(rule.timezone)).isoformat() for p in times), replace=t("chm3-yes") if replace else t("chm3-no")), kb(
                        [b(t, "chm-btn-confirm", "seriesok", view.post.id, data["generation"], owner(message))]))
                return
            if action == "batch_start":
                batch = await batches.get(data["batch"], owner(message))
                channel = await ctx.extras["channelmanager"].get(batch.channel_id)
                start = parse_time(text, channel.timezone)
                if start <= utcnow():
                    raise ContentError("time")
                await planned(message, state, batch.id, t, start=start, calendar_id=data.get("calendar"))
                return
            if action == "calendar":
                name, slots = parse_calendar(text)
                channel = await ctx.extras["channelmanager"].get(data["channel"])
                calendar = await batches.save_calendar(channel.channel_id, owner(message), name, channel.timezone, slots,
                    calendar_id=data.get("calendar"), generation=data.get("generation"))
                await state.clear()
                await calendar_panel(message, calendar, t)
                return
            if action in {"preset_buttons", "preset_channels"}:
                name, separator, body = text.partition("\n")
                if not separator:
                    raise ContentError("content")
                kind = "buttons" if action == "preset_buttons" else "channels"
                payload = {"buttons": [[v.model_dump(mode="json") for v in row] for row in parse_buttons(body)]} if kind == "buttons" else {
                    "channels": [int(v.strip()) for v in body.split(",")]}
                await presets.save(owner(message), name, kind, payload, preset_id=data.get("preset"), generation=data.get("generation"))
                await state.clear()
                await library(message, "presets", t)
                return
            if action == "defaults":
                await presets.set_reactions(data["channel"], owner(message), [] if text.strip() == "-" else [v.strip() for v in text.split("|")])
                await state.clear()
                await show(message, t("chm-settings-saved"))
                return
            if action == "remove":
                await batches.remove(data["batch"], owner(message), data["generation"], int(text))
            elif action == "batch_ttl":
                match = re.fullmatch(r"(\d+)\s*([mhd])", text.strip())
                if text.strip() != "-" and not match:
                    raise ContentError("time")
                seconds = int(match[1]) * {"m": 60, "h": 3600, "d": 86400}[match[2]] if match else None
                await batches.configure(data["batch"], owner(message), data["generation"], defaults={"delete_after_seconds": seconds})
            elif action in {"batch_buttons", "batch_reactions"}:
                key = "buttons" if action == "batch_buttons" else "reactions"
                parsed = [[v.model_dump(mode="json") for v in row] for row in parse_buttons(text)] if key == "buttons" else [] if text.strip() == "-" else [v.strip() for v in text.split("|")]
                await batches.configure(data["batch"], owner(message), data["generation"], defaults={key: parsed})
            elif action in {"post_reactions", "item_buttons", "item_reactions"}:
                view = await posts.view(data["post"], owner(message), "edit")
                values = view.spec.model_dump(mode="json")
                key = "buttons" if action == "item_buttons" else "reactions"
                values[key] = [[v.model_dump(mode="json") for v in row] for row in parse_buttons(text)] if key == "buttons" else [] if text.strip() == "-" else [v.strip() for v in text.split("|")]
                post = await posts.edit(view.post.id, owner(message), data["generation"], PostSpec.model_validate(values))
                if action == "post_reactions":
                    await state.clear()
                    await post_panel(ctx, message, post.id, post.generation, t)
                    return
                batch = await batches.get(data["batch"], owner(message))
                if action == "item_buttons" and batch.reactions_mode == "per_item":
                    await prompt(message, state, t, "chm3-reactions-prompt", "item_reactions", batch=batch.id, post=post.id, generation=post.generation)
                    return
            else:
                raise ContentError("content")
            await state.clear()
            await batch_panel(message, data["batch"], t)
        except (ValueError, KeyError, AccessDenied, TelegramAPIError) as exc:
            await error(message, t, exc)

    async def calendar_panel(event, calendar, t):
        days = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
        slots = "\n".join(f"{days[s['weekday']]} {s['at']}" for s in calendar.slots)
        await show(event, t("chm3-calendar-panel", name=esc(calendar.name), timezone=calendar.timezone, slots=slots), kb(
            [b(t, "chm3-edit-calendar", "editcal", calendar.id, calendar.generation, owner(event))]))

    @router.callback_query(AdvancedCb.filter())
    async def callback(query: CallbackQuery, callback_data: AdvancedCb, state: FSMContext, t: Translate):
        cb = callback_data
        if cb.u != owner(query):
            await query.answer(t("chm-denied"), show_alert=True)
            return
        try:
            if cb.a not in {"apply", "seriesok", "batchok", "pickcal", "calnow"}:
                await state.clear()
            if cb.a in {"series", "batches", "presets"}:
                if not 0 <= cb.g <= 100:
                    raise ContentError("stale")
                await state.clear()
                await library(query, cb.a, t, cb.g)
            elif cb.a in {"batchchoose", "calendars"}:
                await state.clear()
                await choose_channel(query, t, "newbatch" if cb.a == "batchchoose" else "channelcal")
            elif cb.a.startswith("pg"):
                if cb.a[2:] not in {"newbatch", "channelcal", "defaults"} or not 0 <= cb.g <= 10000:
                    raise ContentError("stale")
                await choose_channel(query, t, cb.a[2:], cb.g)
            elif cb.a in {"newbatch", "channelcal", "defaults"}:
                channel = await ctx.extras["channelmanager"].get(int(cb.x))
                await publishing_access(ctx, int(cb.x), cb.u)
                if channel is None or channel.generation != cb.g or channel.status != "active":
                    raise ContentError("stale")
                if cb.a == "newbatch":
                    batch = await batches.create(channel.channel_id, cb.u)
                    await batch_panel(query, batch.id, t)
                elif cb.a == "defaults":
                    await prompt(query, state, t, "chm3-reactions-prompt", "defaults", channel=channel.channel_id)
                else:
                    calendars = await batches.calendars(channel.channel_id, cb.u)
                    rows = [[button(c.name, "calendar", c.id, c.generation, cb.u)] for c in calendars]
                    rows.append([b(t, "chm3-new-calendar", "newcal", cb.x, channel.generation, cb.u)])
                    await show(query, t("chm3-calendars"), kb(*rows))
            elif cb.a in {"newcal", "editcal", "calendar"}:
                if cb.a == "newcal":
                    await prompt(query, state, t, "chm3-calendar-prompt", "calendar", channel=int(cb.x))
                else:
                    async with ctx.sm() as session:
                        calendar = await session.get(Calendar, (ctx.bot_id, cb.x))
                    if calendar is None or calendar.generation != cb.g:
                        raise ContentError("stale")
                    await publishing_access(ctx, calendar.channel_id, cb.u)
                    if cb.a == "calendar":
                        await calendar_panel(query, calendar, t)
                    else:
                        await prompt(query, state, t, "chm3-calendar-prompt", "calendar", channel=calendar.channel_id, calendar=calendar.id, generation=cb.g)
            elif cb.a in {"newbuttons", "newchannels", "preset", "presetedit", "presetdel"}:
                if cb.a.startswith("new"):
                    await prompt(query, state, t, "chm3-preset-prompt", "preset_buttons" if cb.a == "newbuttons" else "preset_channels")
                else:
                    preset = await presets.get(cb.x, cb.u)
                    if preset.generation != cb.g:
                        raise ContentError("stale")
                    if cb.a == "presetdel":
                        await presets.delete(preset.id, cb.u, cb.g)
                        await library(query, "presets", t)
                    elif cb.a == "presetedit":
                        await prompt(query, state, t, "chm3-preset-prompt", f"preset_{preset.kind}", preset=preset.id, generation=cb.g)
                    else:
                        await show(query, t("chm3-preset-panel", name=esc(preset.name)), kb(
                            [b(t, "chm-btn-body", "presetedit", cb.x, cb.g, cb.u), b(t, "chm3-delete-set", "presetdel", cb.x, cb.g, cb.u)]))
            elif cb.a in {"md", "md2", "short", "react", "sets", "repeat", "post", "close"}:
                view = await posts.view(cb.x, cb.u, "edit")
                if view.post.generation != cb.g:
                    raise ContentError("stale")
                if cb.a in {"md", "md2", "short"}:
                    await state.set_state(Composer.content)
                    await state.set_data({"owner": cb.u, "post": cb.x, "generation": cb.g, "channel": view.post.channel_id,
                        "format": {"md": "markdown", "md2": "markdown2", "short": "shorthand"}[cb.a]})
                    await show(query, t("chm3-format-prompt"))
                elif cb.a == "react":
                    await prompt(query, state, t, "chm3-reactions-prompt", "post_reactions", post=cb.x, generation=cb.g)
                elif cb.a == "sets":
                    await state.set_state(None)
                    await state.set_data({"owner": cb.u, "post": cb.x, "generation": cb.g})
                    rows = [[button(p.name, "apply", p.id, p.generation, cb.u)] for p in await presets.list_for(cb.u)]
                    await show(query, t("chm3-presets"), kb(*rows))
                elif cb.a == "repeat":
                    await prompt(query, state, t, "chm3-rule-prompt", "rule", post=cb.x, generation=cb.g)
                elif cb.a == "close":
                    await interactions.close(ctx, cb.x, cb.u, cb.g)
                    await post_panel(ctx, query, cb.x, cb.g, t)
                else:
                    await post_panel(ctx, query, cb.x, cb.g, t)
            elif cb.a == "apply":
                data = await state.get_data()
                preset = await presets.get(cb.x, cb.u)
                if data.get("owner") != cb.u or not data.get("post") or preset.generation != cb.g:
                    raise ContentError("stale")
                post = await presets.apply(cb.x, data["post"], cb.u, data["generation"])
                await state.clear()
                await post_panel(ctx, query, post.id, post.generation, t)
            elif cb.a == "seriesok":
                data = await state.get_data()
                if data.get("owner") != cb.u or data.get("post") != cb.x or data.get("generation") != cb.g or "rule" not in data:
                    raise ContentError("stale")
                series = await recurring.configure(cb.x, cb.u, cb.g, Rule.model_validate(data["rule"]), replace_previous=data["replace"])
                await state.clear()
                await series_panel(query, series.id, t)
            elif cb.a in {"seriesview", "pause", "resume", "rule"}:
                series = await recurring.get(cb.x, cb.u)
                if series.generation != cb.g:
                    raise ContentError("stale")
                if cb.a == "rule":
                    view = await posts.view(series.post_id, cb.u, "edit")
                    await prompt(query, state, t, "chm3-rule-prompt", "rule", post=view.post.id, generation=view.post.generation)
                else:
                    if cb.a in {"pause", "resume"}:
                        await recurring.toggle(cb.x, cb.u, cb.g, active=cb.a == "resume")
                    await state.clear()
                    await series_panel(query, cb.x, t)
            elif cb.a == "batchok":
                data = await state.get_data()
                if data.get("owner") != cb.u or data.get("batch") != cb.x or data.get("generation") != cb.g or "times" not in data:
                    raise ContentError("stale")
                batch = await batches.schedule(cb.x, cb.u, cb.g, start=datetime.fromisoformat(data["start"]) if data["start"] else None,
                    calendar_id=data["calendar"], expected=[datetime.fromisoformat(v) for v in data["times"]], expected_posts=data["posts"])
                await state.clear()
                await batch_panel(query, batch.id, t)
            elif cb.a in {"pickcal", "calnow"}:
                data = await state.get_data()
                if data.get("owner") != cb.u or not data.get("batch"):
                    raise ContentError("stale")
                async with ctx.sm() as session:
                    calendar = await session.get(Calendar, (ctx.bot_id, cb.x))
                if calendar is None or calendar.generation != cb.g:
                    raise ContentError("stale")
                if cb.a == "calnow":
                    await planned(query, state, data["batch"], t, start=utcnow(), calendar_id=cb.x)
                else:
                    await prompt(query, state, t, "chm3-start-prompt", "batch_start", batch=data["batch"], calendar=cb.x)
                    await show(query, t("chm3-start-prompt"), kb([b(t, "chm-now", "calnow", cb.x, cb.g, cb.u)]))
            else:
                batch = await batches.get(cb.x, cb.u)
                if batch.generation != cb.g:
                    raise ContentError("stale")
                if cb.a.startswith("page") and cb.a[4:].isdigit() and 0 <= int(cb.a[4:]) <= 100:
                    await batch_panel(query, cb.x, t, int(cb.a[4:]))
                elif cb.a in {"collect", "restart"}:
                    if cb.a == "restart":
                        await batches.remove(cb.x, cb.u, cb.g)
                        batch = await batches.get(cb.x, cb.u)
                    if batch.status not in {"collecting", "ready"}:
                        raise ContentError("batch_queued")
                    await state.set_state(AdvancedInput.collect)
                    await state.set_data({"owner": cb.u, "batch": batch.id, "generation": batch.generation})
                    await show(query, t("chm3-collect-prompt"))
                elif cb.a in {"bb", "br", "remove"}:
                    key = "chm3-buttons-prompt" if cb.a == "bb" else "chm3-reactions-prompt" if cb.a == "br" else "chm3-remove-prompt"
                    await prompt(query, state, t, key, {"bb": "batch_buttons", "br": "batch_reactions", "remove": "remove"}[cb.a], batch=batch.id, generation=cb.g)
                elif cb.a in {"bm", "rm"}:
                    field = "buttons_mode" if cb.a == "bm" else "reactions_mode"
                    modes = ["shared", "per_item", "none"]
                    await batches.configure(cb.x, cb.u, cb.g, **{field: modes[(modes.index(getattr(batch, field)) + 1) % 3]})
                    await batch_panel(query, cb.x, t)
                elif cb.a == "batchopts":
                    flags = [("notifications", "chm-opt-notifications"), ("link_preview", "chm-opt-preview"),
                        ("protected", "chm-opt-protected"), ("pin", "chm-opt-pin"), ("include_signature", "chm-opt-signature")]
                    defaults = PostSpec.model_validate({"body": {"text": "validation"}, **batch.defaults})
                    rows = [[button(f"{'✅' if getattr(defaults, key) else '❌'} {t(label)}", f"bf{i}", cb.x, cb.g, cb.u)] for i, (key, label) in enumerate(flags)]
                    rows += [[b(t, "chm-btn-delete-after", "bttl", cb.x, cb.g, cb.u)], [b(t, "btn-back", "batch", cb.x, cb.g, cb.u)]]
                    await show(query, t("chm3-batch-options"), kb(*rows))
                elif re.fullmatch(r"bf[0-4]", cb.a):
                    key = ["notifications", "link_preview", "protected", "pin", "include_signature"][int(cb.a[2:])]
                    defaults = PostSpec.model_validate({"body": {"text": "validation"}, **batch.defaults})
                    await batches.configure(cb.x, cb.u, cb.g, defaults={key: not getattr(defaults, key)})
                    await batch_panel(query, cb.x, t)
                elif cb.a == "bttl":
                    await prompt(query, state, t, "chm-delete-after-prompt", "batch_ttl", batch=cb.x, generation=cb.g)
                elif cb.a == "ready":
                    await batches.ready(cb.x, cb.u, cb.g)
                    await state.clear()
                    await batch_panel(query, cb.x, t)
                elif cb.a == "plan":
                    await state.clear()
                    await show(query, t("chm3-plan"), kb(
                        [b(t, "chm-btn-publish", "batchnow", cb.x, cb.g, cb.u), b(t, "chm-btn-schedule", "batchlater", cb.x, cb.g, cb.u)],
                        [b(t, "chm3-use-calendar", "batchcal", cb.x, cb.g, cb.u)]))
                elif cb.a == "batchnow":
                    await planned(query, state, cb.x, t)
                elif cb.a == "batchlater":
                    await prompt(query, state, t, "chm3-start-prompt", "batch_start", batch=cb.x)
                elif cb.a == "batchcal":
                    await state.set_data({"owner": cb.u, "batch": cb.x})
                    await state.set_state(None)
                    calendars = await batches.calendars(batch.channel_id, cb.u)
                    await show(query, t("chm3-calendars"), kb(*[[button(c.name, "pickcal", c.id, c.generation, cb.u)] for c in calendars]))
                elif cb.a == "askcancel":
                    await state.clear()
                    await show(query, t("chm3-confirm-cancel"), kb([b(t, "chm-btn-confirm", "cancelbatch", cb.x, cb.g, cb.u)]))
                elif cb.a == "cancelbatch":
                    await batches.cancel(cb.x, cb.u, cb.g)
                    await state.clear()
                    await batch_panel(query, cb.x, t)
                elif cb.a == "batch":
                    await state.clear()
                    await batch_panel(query, cb.x, t)
                else:
                    raise ContentError("stale")
        except (ValueError, KeyError, AccessDenied, TelegramAPIError) as exc:
            await error(query, t, exc)

    @router.callback_query(F.data.startswith("cha:"))
    async def malformed(query: CallbackQuery, t: Translate):
        await query.answer(t("chm-denied"), show_alert=True)

    return router
