"""Anonymous inbox: personal links, sending, anonymous replies, blocking, reports, hints, share cards."""

from __future__ import annotations

import hashlib

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from bots.anonymous.delivery import deliver, display_name, hint_for, is_allowed, kind_of, quote
from bots.anonymous.keyboards import AnonCb, back_kb, btn, home_kb, incoming_kb, sent_kb, share_url
from bots.anonymous.service import AnonService
from bots.anonymous.settings import AnonSettings
from core.callback_data import CoreVipCb
from core.db.models import BotUser
from core.factory.branding import credit, factory_link
from core.i18n import Translate
from core.sdk.actions import record_user_action
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.sdk.quota import DailyQuota
from core.ui.cards import Card, render
from core.ui.respond import show

CARD_TTL = 30 * 86400
HINTS_PER_DAY = 30


class Writing(StatesGroup):
    message = State()


def build_router(ctx: BotContext) -> Router:
    router = Router(name="anonymous")
    router.message.filter(F.chat.type == ChatType.PRIVATE)
    svc: AnonService = ctx.extras["anon"]
    sent_quota = DailyQuota(ctx.redis, ctx.keys, "sent")
    hint_quota = DailyQuota(ctx.redis, ctx.keys, "hints")
    child = ctx.child

    # ------------------------------------------------------------------ helpers
    async def link_of(user_id: int) -> str:
        if child is not None:  # a user-created bot is one inbox: its own t.me link
            return f"https://t.me/{ctx.username}"
        link = await svc.link_for(user_id)
        return f"https://t.me/{ctx.username}?start={link.code}"

    def is_owner(user_id: int) -> bool:
        return child is None or user_id == child.owner_id

    async def settings() -> AnonSettings:
        stg = await ctx.settings.get()
        assert isinstance(stg, AnonSettings)
        return stg

    def own_link_button(t: Translate) -> InlineKeyboardButton | None:
        if child is not None:
            url = factory_link(ctx)
            return InlineKeyboardButton(text=t("anon-btn-own-bot"), url=url) if url else None
        return InlineKeyboardButton(text=t("anon-btn-own-link"), callback_data=AnonCb(action="home").pack())

    async def home_text(user: BotUser, name: str, t: Translate) -> tuple[str, InlineKeyboardMarkup]:
        link = await link_of(user.user_id)
        stats = await svc.stats(user.user_id)
        key = "anon-owner-home" if child is not None else "anon-home"
        text = t(key, name=name, link=link, received=str(stats.received), week=str(stats.week))
        kb = home_kb(t, link, vip=Feature.VIP in ctx.features, lang=Feature.LANG in ctx.features)
        return text, kb

    async def start_writing(
        message: Message, state: FSMContext, t: Translate, *, to: int, owner: int, reply_to: int | None
    ) -> None:
        await state.set_state(Writing.message)
        await state.update_data(to=to, owner=owner, reply_to=reply_to)
        if reply_to is None:
            name = await display_name(ctx, to)
            text = t("anon-write-prompt", name=name) + credit(ctx, t)
        else:
            text = t("anon-reply-prompt")
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[btn(t("btn-cancel"), "cancel")]]))

    # ------------------------------------------------------------------ entry points
    @router.message(CommandStart())
    async def cmd_start(
        message: Message, command: CommandObject, state: FSMContext, user: BotUser, t: Translate
    ) -> None:
        await state.clear()
        uid = user.user_id
        name = message.from_user.first_name if message.from_user else ""
        if child is not None:
            if is_owner(uid):
                text, kb = await home_text(user, name, t)
                await message.answer(text, reply_markup=kb)
                return
            await open_inbox(message, state, t, uid, child.owner_id)
            return

        code = (command.args or "").strip()
        if code:
            link = await svc.by_code(code)
            if link is None:
                await message.answer(t("anon-link-invalid"))
            elif link.user_id == uid:
                await message.answer(t("anon-own-link"))
            else:
                await open_inbox(message, state, t, uid, link.user_id)
                return
        text, kb = await home_text(user, name, t)
        await message.answer(text, reply_markup=kb)

    async def open_inbox(message: Message, state: FSMContext, t: Translate, uid: int, owner: int) -> None:
        link = await svc.get_link(owner)
        if link is not None and link.paused:
            await message.answer(t("anon-inbox-paused") + credit(ctx, t))
            return
        if await svc.is_blocked(owner, uid):
            await message.answer(t("anon-cant-send"))
            return
        await start_writing(message, state, t, to=owner, owner=owner, reply_to=None)

    @router.message(Command("link"))
    async def cmd_link(message: Message, user: BotUser, t: Translate) -> None:
        await send_card(message, user, t)

    @router.message(Command("stats"))
    async def cmd_stats(message: Message, user: BotUser, t: Translate) -> None:
        await message.answer(await stats_text(user.user_id, t), reply_markup=back_kb(t))

    @router.message(Command("help"))
    async def cmd_help(message: Message, t: Translate) -> None:
        await message.answer(t("anon-help") + credit(ctx, t))

    async def stats_text(user_id: int, t: Translate) -> str:
        s = await svc.stats(user_id)
        return t("anon-stats", received=str(s.received), week=str(s.week), sent=str(s.sent), replied=str(s.replied))

    async def send_card(message: Message, user: BotUser, t: Translate) -> None:
        link = await link_of(user.user_id)
        lang = user.lang or ctx.translator.default
        cache_key = ctx.keys("card", lang)
        cache = ctx.cache_redis or ctx.redis
        caption = t("anon-card-caption", link=link)
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=t("anon-btn-share"), url=share_url(link, t("anon-share-text")))]]
        )
        cached = await cache.get(cache_key)
        if cached:
            await message.answer_photo(cached.decode(), caption=caption, reply_markup=kb)
            return
        png = render(
            Card(
                headline=t("anon-card-headline"),
                body=t("anon-card-body"),
                placeholder=t("anon-card-placeholder"),
                footer=f"@{ctx.username}",
                theme="violet",
            )
        )
        sent = await message.answer_photo(BufferedInputFile(png, "story.png"), caption=caption, reply_markup=kb)
        if sent.photo:
            await cache.set(cache_key, sent.photo[-1].file_id, ex=CARD_TTL)

    # ------------------------------------------------------------------ menu callbacks
    @router.callback_query(F.data == "nav:main")
    @router.callback_query(AnonCb.filter(F.action == "home"))
    async def cb_home(query: CallbackQuery, state: FSMContext, user: BotUser, t: Translate) -> None:
        await state.clear()
        text, kb = await home_text(user, query.from_user.first_name, t)
        await show(query, text, kb)

    @router.callback_query(AnonCb.filter(F.action == "cancel"))
    async def cb_cancel(query: CallbackQuery, state: FSMContext, t: Translate) -> None:
        await state.clear()
        await show(query, t("anon-cancelled"), None)

    @router.callback_query(AnonCb.filter(F.action == "card"))
    async def cb_card(query: CallbackQuery, user: BotUser, t: Translate) -> None:
        await query.answer()
        if isinstance(query.message, Message):
            await send_card(query.message, user, t)

    @router.callback_query(AnonCb.filter(F.action == "stats"))
    async def cb_stats(query: CallbackQuery, user: BotUser, t: Translate) -> None:
        await show(query, await stats_text(user.user_id, t), back_kb(t))

    async def settings_view(user_id: int, t: Translate) -> tuple[str, InlineKeyboardMarkup]:
        link = await svc.link_for(user_id)
        stg = await settings()
        on, off = t("anon-on"), t("anon-off")
        rows = [[btn(t("anon-btn-pause", state=on if not link.paused else off), "pause")]]
        if child is None and stg.daily_prompt_enabled:
            rows.append([btn(t("anon-btn-prompt", state=on if link.daily_prompt else off), "prompt")])
        if child is None:
            rows.append([btn(t("anon-btn-reset"), "reset")])
        rows.append([btn(t("anon-btn-unblock"), "unblock")])
        rows.append([btn(t("btn-back"), "home")])
        return t("anon-settings"), InlineKeyboardMarkup(inline_keyboard=rows)

    @router.callback_query(AnonCb.filter(F.action == "settings"))
    async def cb_settings(query: CallbackQuery, t: Translate) -> None:
        text, kb = await settings_view(query.from_user.id, t)
        await show(query, text, kb)

    @router.callback_query(AnonCb.filter(F.action.in_({"pause", "prompt", "reset", "unblock"})))
    async def cb_setting_change(query: CallbackQuery, callback_data: AnonCb, t: Translate) -> None:
        uid = query.from_user.id
        if not is_owner(uid):
            await query.answer()
            return
        link = await svc.link_for(uid)
        if callback_data.action == "pause":
            await svc.set_flag(uid, paused=not link.paused)
        elif callback_data.action == "prompt":
            await svc.set_flag(uid, daily_prompt=not link.daily_prompt)
        elif callback_data.action == "reset":
            await svc.reset_code(uid)
            await query.answer(t("anon-link-reset"), show_alert=True)
        else:
            n = await svc.unblock_all(uid)
            await query.answer(t("anon-unblocked", count=str(n)), show_alert=True)
        text, kb = await settings_view(uid, t)
        await show(query, text, kb)

    # ------------------------------------------------------------------ inline sharing
    @router.inline_query()
    async def inline(query: InlineQuery, t: Translate) -> None:
        if not is_owner(query.from_user.id):
            await query.answer([], cache_time=60, is_personal=True)
            return
        link = await link_of(query.from_user.id)
        result = InlineQueryResultArticle(
            id=hashlib.sha1(link.encode()).hexdigest()[:32],
            title=t("anon-inline-title"),
            description=t("anon-inline-desc"),
            input_message_content=InputTextMessageContent(message_text=t("anon-inline-text", link=link)),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t("anon-btn-send-me"), url=link)]]),
        )
        await query.answer([result], cache_time=300, is_personal=True)

    # ------------------------------------------------------------------ message actions
    @router.callback_query(AnonCb.filter(F.action == "reply"))
    async def cb_reply(query: CallbackQuery, callback_data: AnonCb, state: FSMContext, t: Translate) -> None:
        msg = await svc.get(callback_data.id)
        uid = query.from_user.id
        if msg is None or msg.recipient_id != uid:
            await query.answer(t("anon-not-yours"), show_alert=True)
            return
        if await svc.is_blocked(msg.sender_id, uid):
            await query.answer(t("anon-cant-send"), show_alert=True)
            return
        await query.answer()
        if isinstance(query.message, Message):
            await start_writing(query.message, state, t, to=msg.sender_id, owner=msg.owner_id, reply_to=msg.id)

    @router.callback_query(AnonCb.filter(F.action == "again"))
    async def cb_again(query: CallbackQuery, callback_data: AnonCb, state: FSMContext, t: Translate) -> None:
        msg = await svc.get(callback_data.id)
        if msg is None or msg.sender_id != query.from_user.id:
            await query.answer(t("anon-not-yours"), show_alert=True)
            return
        await query.answer()
        if isinstance(query.message, Message):
            await start_writing(
                query.message, state, t, to=msg.recipient_id, owner=msg.owner_id, reply_to=msg.reply_to_id
            )

    @router.callback_query(AnonCb.filter(F.action == "block"))
    async def cb_block(query: CallbackQuery, callback_data: AnonCb, t: Translate) -> None:
        msg = await svc.get(callback_data.id)
        uid = query.from_user.id
        if msg is None or msg.recipient_id != uid or msg.owner_id != uid:
            await query.answer(t("anon-not-yours"), show_alert=True)
            return
        await svc.block(uid, msg.sender_id)
        await query.answer(t("anon-blocked"), show_alert=True)

    @router.callback_query(AnonCb.filter(F.action == "report"))
    async def cb_report(query: CallbackQuery, callback_data: AnonCb, t: Translate) -> None:
        msg = await svc.get(callback_data.id)
        uid = query.from_user.id
        if msg is None or msg.recipient_id != uid:
            await query.answer(t("anon-not-yours"), show_alert=True)
            return
        if await svc.mark_reported(msg.id):
            await svc.block(uid, msg.sender_id)
            if child is None:  # a user-created bot's owner moderates it themselves: reporting = blocking
                await notify_report(msg.id, msg.sender_id, msg.text, msg.kind)
        await query.answer(t("anon-reported"), show_alert=True)

    async def notify_report(message_id: int, sender_id: int, text: str | None, kind: str) -> None:
        """Tell moderators (log channel, else the bot's admins) — with the sender's internal id only."""
        report = (
            f"⚠️ <b>Report</b> #{message_id} · {kind}\nSender id: <code>{sender_id}</code>{quote(text, 800)}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[[btn("🚫 Ban sender", "ban", message_id)]])
        if ctx.env.log_channel_id:
            targets = [ctx.env.log_channel_id]
        else:
            targets = list(dict.fromkeys([*ctx.env.admin_ids, *ctx.platform.super_admin_ids]))
        for chat_id in targets:
            try:
                await ctx.bot.send_message(chat_id, report, reply_markup=kb)
            except Exception:
                continue

    @router.callback_query(AnonCb.filter(F.action == "ban"))
    async def cb_ban(query: CallbackQuery, callback_data: AnonCb) -> None:
        if not ctx.is_admin(query.from_user.id):
            await query.answer()
            return
        msg = await svc.get(callback_data.id)
        if msg is None:
            await query.answer("Not found", show_alert=True)
            return
        await ctx.users.set_banned(msg.sender_id, True, reason=f"anonymous report #{msg.id}")
        await ctx.audit.record(query.from_user.id, "anon.ban", msg.sender_id, message=msg.id)
        await query.answer(f"Banned {msg.sender_id}", show_alert=True)

    @router.callback_query(AnonCb.filter(F.action == "hint"))
    async def cb_hint(query: CallbackQuery, callback_data: AnonCb, user: BotUser, t: Translate, lang: str) -> None:
        msg = await svc.get(callback_data.id)
        uid = query.from_user.id
        if msg is None or msg.recipient_id != uid or msg.owner_id != uid or msg.sender_id == uid:
            await query.answer(t("anon-not-yours"), show_alert=True)
            return
        if Feature.VIP in ctx.features and not user.is_vip():
            await query.answer(t("anon-hint-vip"), show_alert=True)
            if isinstance(query.message, Message):
                await query.message.answer(
                    t("anon-hint-upsell"),
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[[InlineKeyboardButton(text=t("btn-vip"), callback_data=CoreVipCb(action="info").pack())]]
                    ),
                )
            return
        if await hint_quota.consume(uid, HINTS_PER_DAY) is None:
            await query.answer(t("anon-hint-limit"), show_alert=True)
            return
        await query.answer()
        when, kind, emojis, vibe = await hint_for(ctx, msg, lang, uid)
        text = t("anon-hint", when=t(f"anon-time-{when}"), kind=t(f"anon-kind-{kind}"), emojis=str(emojis))
        if vibe:
            text += "\n\n🔮 " + vibe
        if isinstance(query.message, Message):
            await query.message.answer(text)

    # ------------------------------------------------------------------ writing (must stay last)
    async def recipient_t(user_id: int) -> Translate:
        """Headers and buttons are read by the recipient, so they use the recipient's language."""
        member = await ctx.users.get(user_id)
        return ctx.translator.bind(member.lang if member else None)

    @router.message(Writing.message, ~F.text.startswith("/"))
    async def on_message(message: Message, state: FSMContext, user: BotUser, t: Translate) -> None:
        data = await state.get_data()
        to, owner = int(data["to"]), int(data["owner"])
        reply_to = int(data["reply_to"]) if data.get("reply_to") else None
        uid = user.user_id
        stg = await settings()
        kind = kind_of(message)
        if kind is None or (kind != "text" and not stg.allow_media):
            await message.answer(t("anon-unsupported"))
            return
        # The inbox owner blocks anonymous senders; a visitor blocked by the owner can't reply either.
        if await svc.is_blocked(owner, uid if uid != owner else to):
            await state.clear()
            await message.answer(t("anon-cant-send"))
            return
        if stg.ai_filter and not await is_allowed(ctx, message.text or message.caption or "", uid):
            await message.answer(t("anon-filtered"))
            return
        limit = stg.vip_daily_messages if user.is_vip() else stg.free_daily_messages
        day = await sent_quota.consume(uid, limit)
        if day is None:
            await message.answer(t("anon-limit", limit=str(limit)))
            return

        record = await svc.record(
            owner_id=owner, sender_id=uid, recipient_id=to, kind=kind,
            text=message.text or message.caption, reply_to_id=reply_to,
        )
        from_anonymous = uid != owner
        original = await svc.get(reply_to) if reply_to else None
        rt = await recipient_t(to)
        if original is None:
            header = rt("anon-new")
        elif from_anonymous:
            header = rt("anon-reply-anonymous") + quote(original.text)
        else:
            header = rt("anon-reply-from-owner", name=await display_name(ctx, owner)) + quote(original.text)
        kb = incoming_kb(rt, record.id, from_anonymous=from_anonymous, hints=stg.hints_enabled)
        result = await deliver(ctx, message, to, header, kb)
        await state.clear()
        if not result.ok:
            await sent_quota.refund(uid, day=day, token=f"msg{record.id}")
            await message.answer(t("anon-not-delivered"))
            return
        await record_user_action(ctx, uid)
        await message.answer(
            t("anon-sent") + credit(ctx, t),
            reply_markup=sent_kb(t, record.id, own_link_button(t) if from_anonymous else None),
        )

    return router
