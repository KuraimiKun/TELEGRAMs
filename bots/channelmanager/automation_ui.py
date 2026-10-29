"""Localized automation editors, activation previews and per-source reports."""

from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message

from bots.channelmanager.auto_content import MediaReference, RouteSpec, RuleSpec, from_source, transform
from bots.channelmanager.automation import source_rights
from bots.channelmanager.content import ContentError, PostSpec, TextBody, parse_buttons, validation_code
from bots.channelmanager.permissions import AccessDenied
from bots.channelmanager.publishing_ui import kb, owner
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.respond import show
from core.ui.text import esc


class AutoInput(StatesGroup):
    value = State()


class AutoCb(CallbackData, prefix="cha4"):
    a: str
    x: str
    g: int
    u: int


def button(text, action, resource, generation, actor):
    return InlineKeyboardButton(text=text, callback_data=AutoCb(a=action, x=str(resource), g=generation, u=actor).pack())


def build_router(ctx: BotContext) -> Router:
    router = Router(name=f"chm_automation_{ctx.slug}")
    router.message.filter(F.chat.type == "private")
    router.callback_query.filter(F.message.chat.type == "private")
    svc = ctx.extras["automation"]

    def b(t, key, action, resource, generation, actor):
        return button(t(key), action, resource, generation, actor)

    async def error(event, t, exc):
        if isinstance(exc, AccessDenied):
            await show(event, t("chm-error-access"))
            return
        code = validation_code(exc)
        if code == "release_stage":
            await show(event, t("chm7-paused"))
            return
        known = {"keywords", "keyword_budget", "filters", "replacement", "forward_edits", "route_cycle", "no_safe_retry", "unsupported_media"}
        if code in known:
            await show(event, t(f"chm4-error-{code}"))
        else:
            await show(event, t(f"chm-error-{code}" if code in {"content", "stale", "length", "media", "buttons", "limit", "time"} else "chm-error-content"))

    async def choose(event, t, offset=0):
        rows = []
        channels = await ctx.extras["channelmanager"].known(owner(event), offset=offset)
        for channel in channels:
            try:
                await source_rights(ctx, channel.channel_id, owner(event))
            except AccessDenied:
                continue
            rows.append([button(channel.title[:60], "chan", channel.channel_id, channel.generation, owner(event))])
        if offset:
            rows.append([button("◀️", "choose", "0", max(0, offset - 10), owner(event))])
        if len(channels) == 10:
            rows.append([button("▶️", "choose", "0", offset + 10, owner(event))])
        await show(event, t("chm4-choose"), kb(*rows))

    async def channel_panel(event, channel_id, t):
        await source_rights(ctx, channel_id, owner(event))
        channel = await ctx.extras["channelmanager"].get(channel_id)
        await show(event, t("chm4-channel", title=esc(channel.title), id=str(channel_id)), kb(
            [b(t, "chm4-sets", "sets", channel_id, 0, owner(event)), b(t, "chm4-routes", "routes", channel_id, 0, owner(event))],
            [b(t, "chm4-reports", "reports", channel_id, 0, owner(event))]))

    async def listing(event, channel_id, kind, t, offset=0):
        entries = await (svc.rules(channel_id, owner(event)) if kind == "rule" else svc.routes(channel_id, owner(event)))
        rows = [[button(f"{'●' if entry.active else '○'} {entry.name[:40]}", kind, entry.id, entry.generation, owner(event))]
            for entry in entries[offset:offset + 10]]
        action = "sets" if kind == "rule" else "routes"
        if offset:
            rows.append([button("◀️", action, channel_id, max(0, offset - 10), owner(event))])
        if len(entries) > offset + 10:
            rows.append([button("▶️", action, channel_id, offset + 10, owner(event))])
        rows += [[b(t, "chm4-new-set" if kind == "rule" else "chm4-new-route", "newrule" if kind == "rule" else "newroute", channel_id, 0, owner(event))],
            [b(t, "btn-back", "chan", channel_id, 0, owner(event))]]
        await show(event, t("chm4-sets" if kind == "rule" else "chm4-routes"), kb(*rows))

    async def panel(event, row, kind, t):
        actor = owner(event)
        def action(key, name):
            return b(t, key, name, row.id, row.generation, actor)
        spec = RuleSpec.model_validate(row.spec) if kind == "rule" else RouteSpec.model_validate(row.spec)
        text = t("chm4-config", name=esc(row.name), status=t("chm4-enabled" if row.active else "chm4-disabled"),
            triggers=str(len(spec.filters.triggers)), excludes=str(len(spec.filters.excludes)), media=", ".join(spec.filters.media))
        if isinstance(spec, RuleSpec):
            text += "\n" + t("chm4-priority-value", value=str(row.priority))
            rows = [[action("chm4-header", "header"), action("chm4-signature", "signature")],
                [action("chm-btn-buttons", "buttons"), action("chm3-reactions", "votes")],
                [action("chm4-attachment", "attach"), action("chm4-separator", "sticker")],
                [action("chm4-replace", "replace"), action("chm-btn-delete-after", "timer")],
                [action("chm4-command", "command"), action("chm4-priority", "priority")],
                [button(f"{t('chm4-on-edits')}: {t('chm4-yes') if spec.on_edits else t('chm4-no')}", "editmode", row.id, row.generation, actor)],
                [button(f"{t('chm4-remove-command')}: {t('chm4-yes') if spec.remove_command else t('chm4-no')}", "remove", row.id, row.generation, actor)],
                [action("chm4-test", "test")]]
        else:
            assert isinstance(spec, RouteSpec)
            text += "\n" + t("chm4-route-details", destination=str(row.destination_id), mode=t(f"chm4-mode-{spec.mode}"),
                content=t(f"chm4-content-{spec.content}"), edits=t("chm4-yes") if spec.propagate_edits else t("chm4-no"))
            rows = [[action("chm4-destination", "dest"), action("chm4-mode", "mode")],
                [action("chm4-content", "content"), action("chm4-propagate", "propagate")]]
        # The resource kind is stored in callback state for prompts/toggles below.
        rows += [[action("chm4-trigger", "filterin"), action("chm4-exclude", "filterout")],
            [action("chm4-media", "media"), button(f"{t('chm4-case')}: {t('chm4-yes') if spec.filters.case_sensitive else t('chm4-no')}",
                "case", row.id, row.generation, actor)],
            [action("chm4-rename", "rename")],
            [action("chm4-disable" if row.active else "chm4-enable", "stop" if row.active else "enable")],
            [b(t, "btn-back", "sets" if kind == "rule" else "routes", row.channel_id, 0, actor)]]
        await show(event, text, kb(*rows))

    async def locate(resource_id, actor):
        try:
            return "rule", await svc.get("rule", resource_id, actor)
        except ContentError:
            return "route", await svc.get("route", resource_id, actor)

    async def prompt(event, state, t, key, action, **values):
        await state.set_state(AutoInput.value)
        await state.set_data({"owner": owner(event), "action": action, **values})
        await show(event, t(key))

    async def save(row, kind, actor, values, *, name=None, priority=None, destination=None, active=None):
        if kind == "rule":
            return await svc.save_rule(row.channel_id, actor, name or row.name, RuleSpec.model_validate(values),
                priority=row.priority if priority is None else priority, active=row.active if active is None else active,
                resource_id=row.id, generation=row.generation)
        return await svc.save_route(row.channel_id, actor, name or row.name, row.destination_id if destination is None else destination,
            RouteSpec.model_validate(values), active=row.active if active is None else active, resource_id=row.id, generation=row.generation)

    @router.message(Command("automation"))
    async def command(message: Message, state: FSMContext, t: Translate):
        await state.clear()
        await choose(message, t)

    command_filter = ~F.text.regexp(r"^/(?:cancel|start|help|channels|connect|posts|newpost|advanced|recurring|multipost|presets|calendars|reactions|signature|timezone)(?:\s|@|$)")

    @router.message(AutoInput.value, command_filter)
    async def value(message: Message, state: FSMContext, t: Translate):
        data = await state.get_data()
        if data.get("owner") != owner(message):
            return
        try:
            action, text = data["action"], message.text or ""
            if action in {"newrule", "newroute"}:
                if not 1 <= len(text.strip()) <= 64:
                    raise ContentError("name")
                if action == "newroute":
                    await prompt(message, state, t, "chm4-destination-prompt", "createdest", channel=data["channel"], name=text.strip())
                    return
                row = await svc.save_rule(data["channel"], owner(message), text.strip(), RuleSpec())
                kind = "rule"
            elif action == "createdest":
                row = await svc.save_route(data["channel"], owner(message), data["name"], int(text.strip()), RouteSpec())
                kind = "route"
            else:
                kind, row = await locate(data["resource"], owner(message))
                if row.generation != data["generation"]:
                    raise ContentError("stale")
                values = dict(row.spec)
                if action == "test":
                    spec = RuleSpec.model_validate(values)
                    item = from_source(message)
                    if not spec.filters.matches([item]):
                        await show(message, t("chm4-no-match"))
                        return
                    items, _, warnings = transform([item], spec, ctx.bot_id)
                    preview = PostSpec.model_validate({**items[0].spec(ctx.bot_id).model_dump(mode="json"), "reactions": spec.reactions})
                    await ctx.bot(preview.send_method(owner(message), preview=True))
                    await state.clear()
                    await show(message, t("chm4-preview-result", warnings=", ".join(warnings) or "—"))
                    return
                if action in {"header", "signature"}:
                    values[action] = TextBody().model_dump(mode="json") if text.strip() == "-" else TextBody(text=text,
                        entities=message.entities or []).model_dump(mode="json")
                elif action in {"buttons", "votes"}:
                    values["buttons" if action == "buttons" else "reactions"] = [[b.model_dump(mode="json") for b in row] for row in parse_buttons(text)] if action == "buttons" else [] if text.strip() == "-" else [v.strip() for v in text.split("|")]
                elif action in {"filterin", "filterout", "media", "command"}:
                    filters = dict(values.get("filters", {}))
                    field = {"filterin": "triggers", "filterout": "excludes", "media": "media", "command": "command"}[action]
                    filters[field] = None if action == "command" and text.strip() == "-" else text.strip() if action == "command" else (
                        sorted({"text", "photo", "video", "animation", "document", "album"}) if action == "media" and text.strip() == "all" else
                        [v.strip() for v in text.split(",") if v.strip()] if action == "media" else [] if text.strip() == "-" else [v.strip() for v in text.splitlines() if v.strip()])
                    values["filters"] = filters
                elif action in {"attach", "sticker"}:
                    field = "attachment" if action == "attach" else "separator"
                    if text.strip() == "-":
                        values[field] = None
                    elif action == "sticker" and message.sticker:
                        values[field] = MediaReference(kind="sticker", file_id=message.sticker.file_id,
                            unique_id=message.sticker.file_unique_id, bot_id=ctx.bot_id).model_dump(mode="json")
                    else:
                        item = from_source(message)
                        values[field] = MediaReference.model_validate({"kind": item.kind, "file_id": item.file_id,
                            "unique_id": item.unique_id, "bot_id": ctx.bot_id}).model_dump(mode="json")
                elif action == "timer":
                    match = re.fullmatch(r"(\d+)\s*([mhd])", text.strip())
                    if text.strip() != "-" and not match:
                        raise ContentError("time")
                    values["delete_after_seconds"] = int(match[1]) * {"m": 60, "h": 3600, "d": 86400}[match[2]] if match else None
                elif action == "replace":
                    pairs = []
                    if text.strip() != "-":
                        for line in text.splitlines():
                            old, sep, new = line.partition(" => ")
                            if not sep:
                                raise ContentError("replacement")
                            pairs.append({"old": old, "new": new})
                    values["replacements"] = pairs
                elif action not in {"rename", "priority", "dest"}:
                    raise ContentError("content")
                row = await save(row, kind, owner(message), values, name=text.strip() if action == "rename" else None,
                    priority=int(text) if action == "priority" else None, destination=int(text) if action == "dest" else None)
            await state.clear()
            await panel(message, row, kind, t)
        except (ValueError, AccessDenied, TelegramAPIError) as exc:
            await error(message, t, exc)

    @router.callback_query(AutoCb.filter())
    async def callback(query: CallbackQuery, callback_data: AutoCb, state: FSMContext, t: Translate):
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
            elif cb.a == "chan":
                await channel_panel(query, int(cb.x), t)
            elif cb.a in {"sets", "routes"}:
                if not 0 <= cb.g <= 100:
                    raise ContentError("stale")
                await listing(query, int(cb.x), "rule" if cb.a == "sets" else "route", t, cb.g)
            elif cb.a in {"newrule", "newroute"}:
                await source_rights(ctx, int(cb.x), cb.u)
                await prompt(query, state, t, "chm4-name-prompt", cb.a, channel=int(cb.x))
            elif cb.a == "reports":
                if not 0 <= cb.g <= 10000:
                    raise ContentError("stale")
                sources = await svc.reports(int(cb.x), cb.u, cb.g)
                rows = [[button(f"{s.id} · {t('chm4-source-' + s.status)}", "report", s.id, s.generation, cb.u)] for s in sources]
                if cb.g:
                    rows.append([button("◀️", "reports", cb.x, max(0, cb.g - 10), cb.u)])
                if len(sources) == 10:
                    rows.append([button("▶️", "reports", cb.x, cb.g + 10, cb.u)])
                await show(query, t("chm4-reports"), kb(*rows))
            elif cb.a in {"report", "r"}:
                if cb.a == "r":
                    await svc.retry(cb.x, cb.u)
                    async with ctx.sm() as session:
                        from bots.channelmanager.models import AutoAction
                        action = await session.get(AutoAction, (ctx.bot_id, cb.x))
                    if action is None:
                        raise ContentError("stale")
                    source_id = action.source_id
                else:
                    source_id = cb.x
                source, snapshot, actions = await svc.report(source_id, cb.u)
                text = t("chm4-source-report", id=source.id, version=str(source.generation), status=t(f"chm4-source-{source.status}"),
                    code=esc(source.error_code or "—"), warnings=esc(", ".join(snapshot.warnings) if snapshot and snapshot.warnings else "—"))
                rows = []
                for action in actions:
                    display_kind = "reminder" if action.error_code == "manual_reminder" else action.kind
                    text += "\n" + t("chm4-action-report", version=str(action.version), kind=t(f"chm4-action-{display_kind}"),
                        destination=str(action.destination_id), status=t(f"chm4-state-{action.status}"), code=esc(action.error_code or "—"), ids=", ".join(str(i) for i in action.remote_ids) or "—")
                    if action.status == "failed":
                        rows.append([button(t("chm4-retry", id=action.id[:8]), "r", action.id, 0, cb.u)])
                rows.append([button(t("chm-btn-refresh"), "report", source.id, source.generation, cb.u)])
                # Telegram limits a single message; older actions remain in the SQL ledger.
                await show(query, text[:3900], kb(*rows[:20]))
            else:
                kind, row = await locate(cb.x, cb.u)
                if row.generation != cb.g:
                    raise ContentError("stale")
                if cb.a in {"rule", "route"}:
                    await panel(query, row, kind, t)
                elif cb.a == "stop":
                    await svc.stop(kind, cb.x, cb.u, cb.g)
                    await panel(query, await svc.get(kind, cb.x, cb.u), kind, t)
                elif cb.a == "enable":
                    await state.set_state(None)
                    await state.set_data({"owner": cb.u, "resource": cb.x, "generation": cb.g})
                    await show(query, t("chm4-enable-confirm", name=esc(row.name)), kb([b(t, "chm-btn-confirm", "on", cb.x, cb.g, cb.u)]))
                elif cb.a == "on":
                    data = await state.get_data()
                    if data.get("owner") != cb.u or data.get("resource") != cb.x or data.get("generation") != cb.g:
                        raise ContentError("stale")
                    updated = await save(row, kind, cb.u, dict(row.spec), active=True)
                    await state.clear()
                    await panel(query, updated, kind, t)
                elif cb.a in {"mode", "content", "propagate", "case", "editmode", "remove"}:
                    values = dict(row.spec)
                    if cb.a == "case":
                        filters = dict(values.get("filters", {}))
                        filters["case_sensitive"] = not filters.get("case_sensitive", False)
                        values["filters"] = filters
                    elif cb.a == "mode":
                        values["mode"] = "forward" if values.get("mode", "copy") == "copy" else "copy"
                    elif cb.a == "content":
                        values["content"] = "transformed" if values.get("content", "original") == "original" else "original"
                    else:
                        field = {"propagate": "propagate_edits", "editmode": "on_edits", "remove": "remove_command"}[cb.a]
                        values[field] = not values.get(field, field != "propagate_edits")
                    await panel(query, await save(row, kind, cb.u, values), kind, t)
                else:
                    prompts = {"header": "chm4-text-prompt", "signature": "chm4-text-prompt", "buttons": "chm3-buttons-prompt",
                        "votes": "chm3-reactions-prompt", "attach": "chm4-attach-prompt", "sticker": "chm4-sticker-prompt",
                        "timer": "chm-delete-after-prompt", "replace": "chm4-replacement-prompt", "filterin": "chm4-keywords-prompt",
                        "filterout": "chm4-keywords-prompt", "media": "chm4-media-prompt", "command": "chm4-command-prompt",
                        "priority": "chm4-priority-prompt", "rename": "chm4-name-prompt", "dest": "chm4-destination-prompt", "test": "chm4-test-prompt"}
                    if cb.a not in prompts:
                        raise ContentError("stale")
                    await prompt(query, state, t, prompts[cb.a], cb.a, resource=row.id, generation=cb.g)
        except (ValueError, AccessDenied, TelegramAPIError) as exc:
            await error(query, t, exc)

    @router.callback_query(F.data.startswith("cha4:"))
    async def malformed(query: CallbackQuery, t: Translate):
        await query.answer(t("chm-denied"), show_alert=True)

    return router
