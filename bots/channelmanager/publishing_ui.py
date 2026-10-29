"""Localized private composer and post library; publishing always has an explicit summary/confirm step."""

from __future__ import annotations

import re
from datetime import UTC
from urllib.parse import quote

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select

from bots.channelmanager.content import ContentError, PostSpec, TextBody, from_message, parse_buttons
from bots.channelmanager.models import Recurrence
from bots.channelmanager.permissions import AccessDenied, publishing_access
from bots.channelmanager.posts import PostService, PostView, parse_time
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.respond import show
from core.ui.text import esc


class Composer(StatesGroup):
    content = State()
    buttons = State()
    targets = State()
    schedule = State()
    delete_after = State()
    reply = State()
    signature = State()


class PostCb(CallbackData, prefix="chp"):
    a: str
    p: str
    g: int
    u: int


def btn(text: str, action: str, post_id: str, generation: int, user_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=PostCb(a=action, p=post_id, g=generation, u=user_id).pack())


def kb(*rows: list[InlineKeyboardButton]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=list(rows))


def owner(event: Message | CallbackQuery) -> int:
    if event.from_user is None:
        raise AccessDenied("no_actor")
    return event.from_user.id


def post_link(channel_id: int, username: str | None, message_id: int) -> str | None:
    if username:
        return f"https://t.me/{username}/{message_id}"
    value = str(channel_id)
    return f"https://t.me/c/{value[4:]}/{message_id}" if value.startswith("-100") else None


def build_router(ctx: BotContext) -> Router:
    router = Router(name=f"chm_publishing_{ctx.slug}")
    router.message.filter(F.chat.type == "private")
    router.callback_query.filter(F.message.chat.type == "private")
    svc: PostService = ctx.extras["posts"]

    async def error(event: Message | CallbackQuery, t: Translate, exc: Exception) -> None:
        code = str(exc) if isinstance(exc, ContentError) else "access" if isinstance(exc, AccessDenied) else "content"
        if code == "release_stage":
            await show(event, t("chm7-paused"))
            return
        known = {"length", "media", "album", "html", "buttons", "url", "entities", "caption", "time", "reply", "targets",
                 "stale", "busy", "limit", "conversion", "published_settings", "already_sent", "access", "content", "markdown"}
        if code in {"series_template", "series_draft"}:
            await show(event, t(f"chm3-error-{code}"))
            return
        key = f"chm-error-{code}" if code in known else "chm-error-content"
        await show(event, t(key))

    async def panel(event: Message | CallbackQuery, view: PostView, t: Translate) -> None:
        post = view.post
        actor = owner(event)
        target_titles = []
        links = []
        for channel_id in post.target_ids:
            channel = await ctx.extras["channelmanager"].get(channel_id)
            target_titles.append(esc(channel.title if channel else str(channel_id)))
        summary = t("chm-post", id=post.id, status=t(f"chm-post-state-{view.state}"), targets=", ".join(target_titles))
        async with ctx.sm() as session:
            series = await session.scalar(select(Recurrence).where(Recurrence.bot_id == ctx.bot_id, Recurrence.post_id == post.id))
        if series:
            summary += "\n" + t("chm3-recurring-template")
        for delivery in view.deliveries:
            summary += "\n" + t("chm-delivery", channel=str(delivery.channel_id), version=str(delivery.version), status=t(f"chm-post-state-{delivery.state}"),
                edit=t(f"chm-job-{delivery.edit_status}"), pin=t(f"chm-job-{delivery.pin_status}"), deletion=t(f"chm-job-{delivery.delete_status}"))
            summary += "\n" + t("chm3-markup-status", status=t(f"chm-job-{delivery.markup_status}"))
            if delivery.message_id:
                channel = await ctx.extras["channelmanager"].get(delivery.channel_id)
                url = post_link(delivery.channel_id, channel.username if channel else None, delivery.message_id)
                if url:
                    link_row = [InlineKeyboardButton(text=t("chm-btn-open", channel=str(delivery.channel_id)), url=url)]
                    if not view.spec.protected:
                        link_row.append(InlineKeyboardButton(text=t("chm-btn-share"), url="https://t.me/share/url?url=" + quote(url, safe="")))
                    links.append(link_row)
        if view.schedule and view.schedule.status == "pending":
            summary += "\n" + t("chm-send-at", when=view.schedule.run_at.astimezone(UTC).isoformat())
        if view.spec.delete_after_seconds:
            summary += "\n" + t("chm-delete-after-value", seconds=str(view.spec.delete_after_seconds))
            if view.spec.delete_after_seconds >= 172800:
                summary += "\n" + t("chm-reminder-only")
        def actions(label, action):
            return btn(t(label), action, post.id, post.generation, actor)
        rows = [[actions("chm-btn-preview", "prev"), actions("chm-btn-body", "body")],
                [actions("chm-btn-buttons", "btns"), actions("chm-btn-clone", "clone")]]
        if not series and view.state in {"draft", "queued", "held", "failed", "cancelled", "partial", "uncertain"}:
            rows += [[actions("chm-btn-publish", "send"), actions("chm-btn-schedule", "when")]]
        if view.state in {"draft", "queued", "held", "failed", "cancelled"}:
            rows += [[actions("chm-btn-targets", "tgt"), actions("chm-btn-options", "opts")]]
        if view.state == "draft":
            rows += [[actions("chm-btn-save", "save")]]
        elif view.state in {"queued", "held", "failed", "partial", "uncertain"}:
            rows += [[actions("chm-btn-cancel-post", "askcancel")]]
        if any("failed" in {d.edit_status, d.pin_status, d.delete_status, d.markup_status} for d in view.deliveries):
            rows += [[actions("chm-btn-retry-followups", "retry")]]
        rows += [[actions("chm3-advanced", "advanced")]]
        if series:
            from bots.channelmanager.advanced_ui import button
            rows += [[button(t("chm3-recurring"), "seriesview", series.id, series.generation, actor)]]
        rows += [[actions("chm-btn-delete-post", "askdel"), actions("chm-btn-detach", "askdet")],
                 [actions("chm-btn-refresh", "view"), btn(t("chm-btn-posts"), "list", "mine", 0, actor)]]
        await show(event, summary, kb(*rows, *links))

    async def library(event: Message | CallbackQuery, actor: int, t: Translate, channel: str = "mine", offset: int = 0, action: str = "list") -> None:
        rows = []
        category = {"list": "all", "ld": "draft", "lq": "scheduled", "ls": "sent"}[action]
        posts = await svc.list_posts(actor, None if channel == "mine" else int(channel), offset, category)
        for post in posts:
            try:
                view = await svc.view(post.id, actor)
            except AccessDenied:
                continue
            rows.append([btn(f"{post.id} · {t(f'chm-post-state-{view.state}')}", "view", post.id, post.generation, actor)])
        nav = []
        if offset:
            nav.append(btn("◀️", action, channel, max(0, offset - 10), actor))
        if len(posts) == 10:
            nav.append(btn("▶️", action, channel, offset + 10, actor))
        if nav:
            rows.append(nav)
        rows.append([btn(t("chm-filter-all"), "list", channel, 0, actor), btn(t("chm-filter-drafts"), "ld", channel, 0, actor)])
        rows.append([btn(t("chm-filter-scheduled"), "lq", channel, 0, actor), btn(t("chm-filter-published"), "ls", channel, 0, actor)])
        rows.append([btn(t("chm-btn-new-post"), "choose", "0", 0, actor)])
        await show(event, t("chm-library"), kb(*rows))

    async def choose(event: Message | CallbackQuery, actor: int, t: Translate, offset: int = 0) -> None:
        channels = await ctx.extras["channelmanager"].known(actor, offset=offset)
        rows = []
        for channel in channels:
            if channel.status != "active":
                continue
            try:
                await publishing_access(ctx, channel.channel_id, actor)
            except AccessDenied:
                continue
            rows.append([btn(channel.title[:60], "new", str(channel.channel_id), channel.generation, actor)])
        navigation = []
        if offset:
            navigation.append(btn("◀️", "choose", "0", max(0, offset - 10), actor))
        if len(channels) == 10:
            navigation.append(btn("▶️", "choose", "0", offset + 10, actor))
        if navigation:
            rows.append(navigation)
        await show(event, t("chm-choose-channel"), kb(*rows))

    async def prompt_content(event, state: FSMContext, t: Translate, *, channel_id: int, post_id="", generation=0, html=False):
        await state.set_state(Composer.content)
        await state.set_data({"owner": owner(event), "channel": channel_id, "post": post_id, "generation": generation, "html": html})
        await show(event, t("chm-content-html") if html else t("chm-content-prompt"))

    async def confirmation(event: Message | CallbackQuery, view: PostView, t: Translate, state: FSMContext, when=None) -> None:
        await state.set_state(None)
        await state.set_data({"owner": owner(event), "post": view.post.id, "generation": view.post.generation,
                              "send_at": when.isoformat() if when else None})
        titles = []
        from zoneinfo import ZoneInfo
        for channel_id in view.post.target_ids:
            channel = await ctx.extras["channelmanager"].get(channel_id)
            title = esc(channel.title if channel else str(channel_id))
            at = when.astimezone(ZoneInfo(channel.timezone)).isoformat() if when and channel else t("chm-now")
            titles.append(f"{title} · {at}")
        text = t("chm-publish-confirm", targets="\n".join(titles))
        if view.spec.delete_after_seconds and view.spec.delete_after_seconds >= 172800:
            text += "\n" + t("chm-reminder-only")
        await show(event, text, kb(
            [btn(t("chm-btn-confirm-publish"), "ok", view.post.id, view.post.generation, owner(event))],
            [btn(t("btn-back"), "view", view.post.id, view.post.generation, owner(event))]))

    @router.message(Command("newpost"))
    async def new(message: Message, state: FSMContext, t: Translate):
        await state.clear()
        await choose(message, owner(message), t)

    @router.message(Command("posts"))
    async def posts(message: Message, state: FSMContext, t: Translate):
        await state.clear()
        await library(message, owner(message), t)

    @router.message(Command("cancel"))
    async def cancel(message: Message, state: FSMContext, t: Translate):
        await state.clear()
        await show(message, t("chm-input-cancelled"))

    @router.message(Command("signature"))
    async def signature(message: Message, state: FSMContext, t: Translate):
        parts = (message.text or "").split()
        if len(parts) != 2 or not re.fullmatch(r"-\d+", parts[1]):
            await show(message, t("chm-signature-usage"))
            return
        await state.set_state(Composer.signature)
        await state.set_data({"owner": owner(message), "channel": int(parts[1])})
        await show(message, t("chm-signature-prompt"))

    @router.message(Command("timezone"))
    async def timezone(message: Message, t: Translate):
        try:
            parts = (message.text or "").split()
            if len(parts) != 3 or not re.fullmatch(r"-\d+", parts[1]):
                raise ContentError("time")
            await svc.configure(int(parts[1]), owner(message), timezone=parts[2])
            await show(message, t("chm-settings-saved"))
        except (ValueError, AccessDenied, TelegramAPIError) as exc:
            await error(message, t, exc)

    @router.message(Composer.content, ~F.text.startswith("/"))
    async def content(message: Message, state: FSMContext, t: Translate):
        data = await state.get_data()
        if data.get("owner") != owner(message):
            return
        try:
            if data.get("post"):
                view = await svc.view(data["post"], owner(message), "edit")
                spec = from_message(message, ctx.bot_id, html=data.get("html", False), signature=view.spec.signature, format_mode=data.get("format"))
                values = view.spec.model_dump(mode="json")
                values.update(spec.model_dump(mode="json", include={"kind", "body", "file_id", "media_bot_id"}))
                spec = PostSpec.model_validate(values)
                async with ctx.sm() as session:
                    series = await session.scalar(select(Recurrence.id).where(Recurrence.bot_id == ctx.bot_id, Recurrence.post_id == view.post.id))
                if series:
                    await state.set_state(None)
                    await state.set_data({"owner": owner(message), "post": view.post.id, "generation": data["generation"], "candidate": spec.model_dump(mode="json")})
                    await ctx.bot(spec.send_method(owner(message), preview=True))
                    await show(message, t("chm3-confirm-shared-edit", targets=", ".join(str(c) for c in view.post.target_ids)), kb(
                        [btn(t("chm-btn-confirm"), "apply", view.post.id, data["generation"], owner(message))]))
                    return
                post = await svc.edit(view.post.id, owner(message), data["generation"], spec)
            else:
                spec = from_message(message, ctx.bot_id, html=data.get("html", False), signature=await svc.signature(data["channel"]))
                values = spec.model_dump(mode="json")
                values["reactions"] = await ctx.extras["presets"].reactions(data["channel"])
                spec = PostSpec.model_validate(values)
                post = await svc.create(data["channel"], owner(message), spec,
                    source_key=f"input:{message.chat.id}:{message.message_id}")
            await state.clear()
            await panel(message, await svc.view(post.id, owner(message)), t)
        except (ValueError, AccessDenied, TelegramAPIError) as exc:
            await error(message, t, exc)

    @router.message(Composer.buttons, ~F.text.startswith("/"))
    @router.message(Composer.targets, ~F.text.startswith("/"))
    @router.message(Composer.schedule, ~F.text.startswith("/"))
    @router.message(Composer.delete_after, ~F.text.startswith("/"))
    @router.message(Composer.reply, ~F.text.startswith("/"))
    @router.message(Composer.signature, ~F.text.startswith("/"))
    async def input_value(message: Message, state: FSMContext, t: Translate):
        data = await state.get_data()
        if data.get("owner") != owner(message):
            return
        try:
            current = await state.get_state()
            text = message.text or ""
            if current == Composer.signature.state:
                await svc.configure(data["channel"], owner(message), signature=TextBody() if text == "-" else TextBody(
                    text=text, entities=message.entities or []))
                await state.clear()
                await show(message, t("chm-settings-saved"))
                return
            view = await svc.view(data["post"], owner(message), "edit")
            if view.post.generation != data["generation"]:
                raise ContentError("stale")
            if current == Composer.schedule.state:
                channel = await ctx.extras["channelmanager"].get(view.post.channel_id)
                when = parse_time(text, channel.timezone)
                from core.db.base import utcnow
                if when <= utcnow():
                    raise ContentError("time")
                await confirmation(message, view, t, state, when)
                return
            if current == Composer.targets.state:
                target_values = [int(v.strip()) for v in text.split(",")]
                post = await svc.targets(view.post.id, owner(message), view.post.generation, target_values)
            else:
                values = view.spec.model_dump(mode="json")
                if current == Composer.buttons.state:
                    values["buttons"] = [[b.model_dump() for b in row] for row in parse_buttons(text)]
                elif current == Composer.reply.state:
                    values["reply_message_id"] = None if text == "-" else int(text)
                else:
                    if text == "-":
                        values["delete_after_seconds"] = None
                    else:
                        match = re.fullmatch(r"(\d+)\s*([mhd])", text)
                        if not match:
                            raise ContentError("time")
                        values["delete_after_seconds"] = int(match[1]) * {"m": 60, "h": 3600, "d": 86400}[match[2]]
                post = await svc.edit(view.post.id, owner(message), view.post.generation, PostSpec.model_validate(values))
            await state.clear()
            await panel(message, await svc.view(post.id, owner(message)), t)
        except (ValueError, AccessDenied, TelegramAPIError) as exc:
            await error(message, t, exc)

    @router.callback_query(PostCb.filter())
    async def callback(query: CallbackQuery, callback_data: PostCb, state: FSMContext, t: Translate):
        cb = callback_data
        if cb.u != query.from_user.id:
            await query.answer(t("chm-denied"), show_alert=True)
            return
        try:
            if cb.a not in {"ok", "apply"}:
                await state.clear()
            if cb.a in {"choose", "list", "ld", "lq", "ls", "new"}:
                await state.clear()
                if cb.a == "choose":
                    if not 0 <= cb.g <= 10000:
                        raise ContentError("stale")
                    await choose(query, cb.u, t, cb.g)
                elif cb.a in {"list", "ld", "lq", "ls"} and 0 <= cb.g <= 10000 and (cb.p == "mine" or re.fullmatch(r"-\d+", cb.p)):
                    await library(query, cb.u, t, cb.p, cb.g, cb.a)
                elif cb.a == "new":
                    channel_id = int(cb.p)
                    await publishing_access(ctx, channel_id, cb.u)
                    channel = await ctx.extras["channelmanager"].get(channel_id)
                    if not channel or channel.generation != cb.g or channel.status != "active":
                        raise ContentError("stale")
                    await prompt_content(query, state, t, channel_id=channel_id)
                else:
                    raise ContentError("stale")
                return
            view = await svc.view(cb.p, cb.u)
            if view.post.generation != cb.g:
                raise ContentError("stale")
            if cb.a == "view":
                await state.clear()
                await panel(query, view, t)
            elif cb.a == "advanced":
                from bots.channelmanager.advanced_ui import post_panel
                await post_panel(ctx, query, cb.p, cb.g, t)
            elif cb.a == "apply":
                data = await state.get_data()
                if data.get("owner") != cb.u or data.get("post") != cb.p or data.get("generation") != cb.g or "candidate" not in data:
                    raise ContentError("stale")
                post = await svc.edit(cb.p, cb.u, cb.g, PostSpec.model_validate(data["candidate"]))
                await state.clear()
                await panel(query, await svc.view(post.id, cb.u), t)
            elif cb.a == "prev":
                await ctx.bot(view.spec.send_method(cb.u, preview=True))
                await query.answer()
            elif cb.a in {"body", "html"}:
                await prompt_content(query, state, t, channel_id=view.post.channel_id, post_id=cb.p, generation=cb.g, html=cb.a == "html")
            elif cb.a in {"btns", "tgt", "when", "ttl", "reply"}:
                states = {"btns": Composer.buttons, "tgt": Composer.targets, "when": Composer.schedule,
                          "ttl": Composer.delete_after, "reply": Composer.reply}
                prompts = {"btns": "chm-buttons-prompt", "tgt": "chm-targets-prompt", "when": "chm-schedule-prompt",
                           "ttl": "chm-delete-after-prompt", "reply": "chm-reply-prompt"}
                await state.set_state(states[cb.a])
                await state.set_data({"owner": cb.u, "post": cb.p, "generation": cb.g})
                channel = await ctx.extras["channelmanager"].get(view.post.channel_id)
                await show(query, t(prompts[cb.a], timezone=channel.timezone))
            elif cb.a == "send":
                await confirmation(query, view, t, state)
            elif cb.a == "ok":
                data = await state.get_data()
                if data.get("owner") != cb.u or data.get("post") != cb.p or data.get("generation") != cb.g:
                    raise ContentError("stale")
                when = parse_time(data["send_at"], "UTC") if data.get("send_at") else None
                post = await svc.publish(cb.p, cb.u, cb.g, run_at=when)
                await state.clear()
                await panel(query, await svc.view(post.id, cb.u), t)
            elif cb.a == "save":
                if view.state != "draft":
                    raise ContentError("published_settings")
                await state.clear()
                await show(query, t("chm-draft-saved"), kb([btn(t("chm-btn-posts"), "list", "mine", 0, cb.u)]))
            elif cb.a == "opts":
                flags = [("notifications", "chm-opt-notifications"), ("link_preview", "chm-opt-preview"),
                         ("protected", "chm-opt-protected"), ("pin", "chm-opt-pin"),
                         ("include_signature", "chm-opt-signature"), ("caption_above", "chm-opt-caption")]
                rows = [[btn(f"{'✅' if getattr(view.spec, key) else '❌'} {t(label)}", f"f{index}", cb.p, cb.g, cb.u)]
                        for index, (key, label) in enumerate(flags) if key != "caption_above" or view.spec.kind in {"photo", "video", "animation"}]
                rows += [[btn(t("chm-btn-html"), "html", cb.p, cb.g, cb.u)],
                         [btn(t("chm-btn-delete-after"), "ttl", cb.p, cb.g, cb.u), btn(t("chm-btn-reply"), "reply", cb.p, cb.g, cb.u)],
                         [btn(t("btn-back"), "view", cb.p, cb.g, cb.u)]]
                await show(query, t("chm-options"), kb(*rows))
            elif re.fullmatch(r"f[0-5]", cb.a):
                keys = ["notifications", "link_preview", "protected", "pin", "include_signature", "caption_above"]
                values = view.spec.model_dump(mode="json")
                key = keys[int(cb.a[1])]
                values[key] = not values[key]
                post = await svc.edit(cb.p, cb.u, cb.g, PostSpec.model_validate(values))
                await panel(query, await svc.view(post.id, cb.u), t)
            elif cb.a == "clone":
                post = await svc.create(view.post.channel_id, cb.u, view.spec, source_key=f"clone:{query.id}")
                await state.clear()
                await panel(query, await svc.view(post.id, cb.u), t)
            elif cb.a == "retry":
                await svc.retry_followups(cb.p, cb.u, cb.g)
                await panel(query, await svc.view(cb.p, cb.u), t)
            elif cb.a in {"askdel", "askdet", "askcancel"}:
                action = {"askdel": "del", "askdet": "det", "askcancel": "cancel"}[cb.a]
                key = {"askdel": "chm-confirm-delete", "askdet": "chm-confirm-detach", "askcancel": "chm-confirm-cancel"}[cb.a]
                await show(query, t(key), kb([btn(t("chm-btn-confirm"), action, cb.p, cb.g, cb.u)],
                                            [btn(t("btn-back"), "view", cb.p, cb.g, cb.u)]))
            elif cb.a in {"del", "det", "cancel"}:
                if cb.a == "del":
                    await svc.delete(cb.p, cb.u, cb.g)
                else:
                    await svc.cancel(cb.p, cb.u, cb.g, detach=cb.a == "det")
                await state.clear()
                if cb.a == "det":
                    await show(query, t("chm-detached"))
                else:
                    await panel(query, await svc.view(cb.p, cb.u), t)
            else:
                raise ContentError("stale")
        except (ValueError, AccessDenied, TelegramAPIError) as exc:
            await error(query, t, exc)

    @router.callback_query(F.data.startswith("chp:"))
    async def malformed(query: CallbackQuery, t: Translate):
        await query.answer(t("chm-denied"), show_alert=True)

    return router
