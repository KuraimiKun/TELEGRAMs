"""Bot Factory: create a bot from a template in one minute, then manage it from here."""

from __future__ import annotations

import contextlib
import math
import time

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bots.factory.settings import FactorySettings
from core.callback_data import CoreVipCb
from core.db.models import BotUser, ChildBot
from core.factory.children import ChildError, ChildService
from core.factory.crypto import decrypt_token, encrypt_token
from core.i18n import Translate
from core.sdk.actions import record_user_action
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.ui.respond import show
from core.ui.text import esc

PER_PAGE = 6
TEMPLATE_EMOJI = {"anonymous": "📩", "feedback": "💬", "groupguard": "🛡", "custom": "🧩"}
STATUS_EMOJI = {"active": "🟢", "paused": "⏸", "error": "🔴", "revoked": "⛔"}


class FacCb(CallbackData, prefix="fac"):
    # home | new | tpl | list | bot | pause | resume | token | public | brand | del | del_ok | gallery
    action: str
    id: int = 0
    page: int = 1
    arg: str = ""


class Making(StatesGroup):
    token = State()
    rotate = State()


def cb(action: str, id: int = 0, page: int = 1, arg: str = "") -> str:
    return FacCb(action=action, id=id, page=page, arg=arg).pack()


def build_router(ctx: BotContext) -> Router:
    router = Router(name="factory")
    router.message.filter(F.chat.type == "private")
    children: ChildService = ctx.extras["children"]
    templates: list[str] = sorted(children.templates)

    def btn(text: str, action: str, **kw) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=text, callback_data=cb(action, **kw))

    def tpl_name(t: Translate, key: str) -> str:
        return f"{TEMPLATE_EMOJI.get(key, '🤖')} {t(f'fac-tpl-{key}')}"

    async def settings() -> FactorySettings:
        stg = await ctx.settings.get()
        assert isinstance(stg, FactorySettings)
        return stg

    async def limit_for(user: BotUser) -> int:
        stg = await settings()
        if user.is_vip():
            return stg.vip_bots
        bonus = user.referral_count // stg.referrals_per_slot if stg.referrals_per_slot > 0 else 0
        return stg.free_bots + bonus

    async def home(user: BotUser, name: str, t: Translate) -> tuple[str, InlineKeyboardMarkup]:
        count = await children.count_for_owner(user.user_id)
        rows = [
            [btn(t("fac-btn-new"), "new")],
            [btn(t("fac-btn-mine", count=str(count)), "list")],
        ]
        if (await settings()).gallery_enabled:
            rows.append([btn(t("fac-btn-gallery"), "gallery")])
        extra = []
        if Feature.VIP in ctx.features:
            extra.append(InlineKeyboardButton(text=t("btn-vip"), callback_data=CoreVipCb(action="info").pack()))
        if Feature.REFERRAL in ctx.features:
            extra.append(InlineKeyboardButton(text=t("btn-referral"), callback_data="nav:referral"))
        if extra:
            rows.append(extra)
        text = t("fac-home", name=esc(name), count=str(count), limit=str(await limit_for(user)))
        return text, InlineKeyboardMarkup(inline_keyboard=rows)

    # ------------------------------------------------------------------ entry
    @router.message(CommandStart())
    async def cmd_start(message: Message, command: CommandObject, state: FSMContext, user: BotUser,
                        t: Translate) -> None:
        await state.clear()
        payload = (command.args or "").strip()
        if payload.startswith("from_c") and payload[6:].isdigit():
            await ctx.redis.incr(ctx.keys("attribution", payload[6:]))
        text, kb = await home(user, message.from_user.first_name if message.from_user else "", t)
        await message.answer(text, reply_markup=kb)

    @router.callback_query(F.data == "nav:main")
    @router.callback_query(FacCb.filter(F.action == "home"))
    async def cb_home(query: CallbackQuery, state: FSMContext, user: BotUser, t: Translate) -> None:
        await state.clear()
        text, kb = await home(user, query.from_user.first_name, t)
        await show(query, text, kb)

    # ------------------------------------------------------------------ create
    async def choose_template(user: BotUser, t: Translate) -> tuple[str, InlineKeyboardMarkup]:
        if ctx.platform.factory_secret_key is None:
            return t("fac-disabled"), InlineKeyboardMarkup(inline_keyboard=[[btn(t("btn-back"), "home")]])
        limit = await limit_for(user)
        if await children.count_for_owner(user.user_id) >= limit:
            rows = [[btn(t("btn-back"), "home")]]
            if Feature.VIP in ctx.features:
                rows.insert(0, [InlineKeyboardButton(text=t("btn-vip"), callback_data=CoreVipCb(action="info").pack())])
            return t("fac-err-limit", limit=str(limit)), InlineKeyboardMarkup(inline_keyboard=rows)
        lines = [t("fac-choose")]
        lines += [f"\n<b>{tpl_name(t, k)}</b>\n{t(f'fac-tpl-{k}-desc')}" for k in templates]
        rows = [[btn(tpl_name(t, k), "tpl", arg=k)] for k in templates]
        rows.append([btn(t("btn-back"), "home")])
        return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)

    @router.message(Command("newbot"))
    async def cmd_newbot(message: Message, user: BotUser, t: Translate) -> None:
        text, kb = await choose_template(user, t)
        await message.answer(text, reply_markup=kb)

    @router.callback_query(FacCb.filter(F.action == "new"))
    async def cb_new(query: CallbackQuery, user: BotUser, t: Translate) -> None:
        text, kb = await choose_template(user, t)
        await show(query, text, kb)

    @router.callback_query(FacCb.filter(F.action == "tpl"))
    async def cb_template(query: CallbackQuery, callback_data: FacCb, state: FSMContext, t: Translate) -> None:
        if callback_data.arg not in templates:
            await query.answer()
            return
        await state.set_state(Making.token)
        await state.update_data(template=callback_data.arg)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("fac-btn-botfather"), url="https://t.me/BotFather")],
            [btn(t("btn-cancel"), "home")],
        ])
        await show(query, t("fac-steps", template=tpl_name(t, callback_data.arg)), kb)

    async def read_token(message: Message) -> str:
        """The token is a secret: take it and delete the user's message right away."""
        token = (message.text or "").strip()
        with contextlib.suppress(TelegramAPIError):
            await message.delete()
        return token

    @router.message(Making.token, F.text)
    async def on_token(message: Message, state: FSMContext, user: BotUser, t: Translate) -> None:
        data = await state.get_data()
        token = await read_token(message)
        progress = await message.answer(t("fac-creating"))
        try:
            child = await children.create(user.user_id, token, str(data["template"]), limit=await limit_for(user))
        except ChildError as e:
            if e.code == "migration_required":
                await state.set_data({"template": data["template"], "pending_token": encrypt_token(ctx.platform, token),
                    "migration_owner": user.user_id, "migration_until": time.time() + 300})
                await progress.edit_text(t("fac-migration-confirm"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [btn(t("fac-btn-migrate"), "migrate")], [btn(t("btn-cancel"), "home")]]))
                return
            await progress.edit_text(t(f"fac-err-{e.code}", limit=str(await limit_for(user))))
            if e.code not in ("token_format", "token_invalid", "telegram"):
                await state.clear()
            return
        await state.clear()
        await record_user_action(ctx, user.user_id)
        await ctx.audit.record(user.user_id, "factory.create", child.bot_id, template=child.template)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("fac-btn-open", username=child.username), url=f"https://t.me/{child.username}")],
            [btn(t("fac-btn-manage"), "bot", id=child.bot_id)],
        ])
        await progress.edit_text(
            t("fac-created", username=child.username, template=tpl_name(t, child.template),
              guide=t(f"fac-tpl-{child.template}-guide")),
            reply_markup=kb,
        )

    @router.callback_query(FacCb.filter(F.action == "migrate"))
    async def cb_migrate(query: CallbackQuery, state: FSMContext, user: BotUser, t: Translate) -> None:
        data = await state.get_data()
        if data.get("migration_owner") != user.user_id or data.get("migration_until", 0) <= time.time():
            await state.clear()
            await query.answer(t("fac-not-found"), show_alert=True)
            return
        if data.get("migration_action") == "resume":
            child = await children.get_owned(user.user_id, data["migration_bot"])
            await state.clear()
            if child is None or child.status == "revoked":
                await show(query, t("fac-not-found"))
                return
            try:
                await children.resume(child, migrate_existing=True)
            except ChildError as exc:
                await show(query, t(f"fac-err-{exc.code}", limit=""))
                return
            await ctx.audit.record(user.user_id, "factory.migrate", child.bot_id, template=child.template)
            refreshed = await children.get(child.bot_id)
            if refreshed is not None:
                text, keyboard = await manage_view(refreshed, t)
                await show(query, text, keyboard)
            return
        token = decrypt_token(ctx.platform, data["pending_token"])
        await state.clear()
        if not token:
            await show(query, t("fac-err-token_invalid"))
            return
        try:
            child = await children.create(user.user_id, token, data["template"], limit=await limit_for(user), migrate_existing=True)
        except ChildError as exc:
            await show(query, t(f"fac-err-{exc.code}", limit=str(await limit_for(user))))
            return
        await ctx.audit.record(user.user_id, "factory.migrate", child.bot_id, template=child.template)
        await show(query, t("fac-created", username=child.username, template=tpl_name(t, child.template),
            guide=t(f"fac-tpl-{child.template}-guide")), InlineKeyboardMarkup(inline_keyboard=[
                [btn(t("fac-btn-manage"), "bot", id=child.bot_id)]]))

    # ------------------------------------------------------------------ my bots
    async def list_view(user_id: int, page: int, t: Translate) -> tuple[str, InlineKeyboardMarkup]:
        total = await children.count_for_owner(user_id)
        pages = max(1, math.ceil(total / PER_PAGE))
        page = min(max(1, page), pages)
        bots = await children.list_for_owner(user_id, offset=(page - 1) * PER_PAGE, limit=PER_PAGE)
        rows = [[btn(f"{STATUS_EMOJI.get(c.status, '•')} @{c.username} · {tpl_name(t, c.template)}", "bot",
                     id=c.bot_id)] for c in bots]
        nav = []
        if page > 1:
            nav.append(btn("◀️", "list", page=page - 1))
        if page < pages:
            nav.append(btn("▶️", "list", page=page + 1))
        if nav:
            rows.append(nav)
        rows.append([btn(t("fac-btn-new"), "new"), btn(t("btn-back"), "home")])
        text = t("fac-mine", count=str(total)) if bots else t("fac-mine-empty")
        return text, InlineKeyboardMarkup(inline_keyboard=rows)

    @router.message(Command("mybots"))
    async def cmd_mybots(message: Message, user: BotUser, t: Translate) -> None:
        text, kb = await list_view(user.user_id, 1, t)
        await message.answer(text, reply_markup=kb)

    @router.callback_query(FacCb.filter(F.action == "list"))
    async def cb_list(query: CallbackQuery, callback_data: FacCb, state: FSMContext, user: BotUser,
                      t: Translate) -> None:
        await state.clear()
        text, kb = await list_view(user.user_id, callback_data.page, t)
        await show(query, text, kb)

    async def manage_view(child: ChildBot, t: Translate) -> tuple[str, InlineKeyboardMarkup]:
        users = await children.member_count(child.bot_id)
        visits = int(await ctx.redis.get(ctx.keys("attribution", child.bot_id)) or 0)
        on, off = "✅", "❌"
        text = t(
            "fac-manage", username=child.username, template=tpl_name(t, child.template),
            status=f"{STATUS_EMOJI.get(child.status, '')} {t(f'fac-status-{child.status}')}", users=str(users),
            visits=str(visits), created=f"{child.created_at:%Y-%m-%d}",
        )
        if child.last_error and child.status == "error":
            text += "\n\n" + t("fac-last-error", error=esc(child.last_error))
        toggle = btn(t("fac-btn-pause"), "pause", id=child.bot_id) if child.status == "active" else \
            btn(t("fac-btn-resume"), "resume", id=child.bot_id)
        rows = [
            [InlineKeyboardButton(text=t("fac-btn-open", username=child.username), url=f"https://t.me/{child.username}")],
            [toggle, btn(t("fac-btn-token"), "token", id=child.bot_id)],
            [btn(t("fac-btn-public", state=on if child.public else off), "public", id=child.bot_id),
             btn(t("fac-btn-brand", state=on if child.branding else off), "brand", id=child.bot_id)],
            [btn(t("fac-btn-refresh"), "bot", id=child.bot_id), btn(t("fac-btn-delete"), "del", id=child.bot_id)],
            [btn(t("btn-back"), "list")],
        ]
        return text, InlineKeyboardMarkup(inline_keyboard=rows)

    async def owned(query: CallbackQuery, bot_id: int, t: Translate) -> ChildBot | None:
        child = await children.get_owned(query.from_user.id, bot_id)
        if child is None or child.status == "revoked":
            await query.answer(t("fac-not-found"), show_alert=True)
            return None
        return child

    @router.callback_query(FacCb.filter(F.action == "bot"))
    async def cb_bot(query: CallbackQuery, callback_data: FacCb, state: FSMContext, t: Translate) -> None:
        await state.clear()
        if (child := await owned(query, callback_data.id, t)) is None:
            return
        text, kb = await manage_view(child, t)
        await show(query, text, kb)

    @router.callback_query(FacCb.filter(F.action.in_({"pause", "resume", "public", "brand"})))
    async def cb_toggle(query: CallbackQuery, callback_data: FacCb, state: FSMContext, user: BotUser, t: Translate) -> None:
        if (child := await owned(query, callback_data.id, t)) is None:
            return
        try:
            if callback_data.action == "pause":
                await children.pause(child)
            elif callback_data.action == "resume":
                await children.resume(child)
            elif callback_data.action == "public":
                await children.set_flags(child, public=not child.public)
            else:
                if child.branding and not user.is_vip():
                    await query.answer(t("fac-brand-vip"), show_alert=True)
                    return
                await children.set_flags(child, branding=not child.branding)
        except ChildError as e:
            if e.code == "migration_required":
                await state.set_data({"migration_action": "resume", "migration_bot": child.bot_id,
                    "migration_owner": user.user_id, "migration_until": time.time() + 300})
                await show(query, t("fac-migration-confirm"), InlineKeyboardMarkup(inline_keyboard=[
                    [btn(t("fac-btn-migrate"), "migrate")], [btn(t("btn-cancel"), "home")]]))
                return
            await query.answer(t(f"fac-err-{e.code}", limit=""), show_alert=True)
        await ctx.audit.record(user.user_id, f"factory.{callback_data.action}", child.bot_id)
        refreshed = await children.get(child.bot_id)
        if refreshed is not None:
            text, kb = await manage_view(refreshed, t)
            await show(query, text, kb)

    @router.callback_query(FacCb.filter(F.action == "token"))
    async def cb_token(query: CallbackQuery, callback_data: FacCb, state: FSMContext, t: Translate) -> None:
        if (child := await owned(query, callback_data.id, t)) is None:
            return
        await state.set_state(Making.rotate)
        await state.update_data(bot_id=child.bot_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[[btn(t("btn-cancel"), "bot", id=child.bot_id)]])
        await show(query, t("fac-rotate", username=child.username), kb)

    @router.message(Making.rotate, F.text)
    async def on_rotate(message: Message, state: FSMContext, user: BotUser, t: Translate) -> None:
        data = await state.get_data()
        token = await read_token(message)
        child = await children.get_owned(user.user_id, int(data["bot_id"]))
        if child is None:
            await state.clear()
            return
        try:
            await children.rotate_token(child, token)
        except ChildError as e:
            if e.code == "migration_required":
                await state.set_state(None)
                await state.set_data({"migration_action": "resume", "migration_bot": child.bot_id,
                    "migration_owner": user.user_id, "migration_until": time.time() + 300})
                await message.answer(t("fac-migration-confirm"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [btn(t("fac-btn-migrate"), "migrate")], [btn(t("btn-cancel"), "home")]]))
                return
            await message.answer(t(f"fac-err-{e.code}", limit=""))
            return
        await state.clear()
        refreshed = await children.get(child.bot_id)
        if refreshed is not None:
            text, kb = await manage_view(refreshed, t)
            await message.answer(t("fac-rotated") + "\n\n" + text, reply_markup=kb)

    @router.callback_query(FacCb.filter(F.action == "del"))
    async def cb_delete(query: CallbackQuery, callback_data: FacCb, t: Translate) -> None:
        if (child := await owned(query, callback_data.id, t)) is None:
            return
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [btn(t("fac-btn-delete-ok"), "del_ok", id=child.bot_id)],
            [btn(t("btn-cancel"), "bot", id=child.bot_id)],
        ])
        await show(query, t("fac-confirm-delete", username=child.username), kb)

    @router.callback_query(FacCb.filter(F.action == "del_ok"))
    async def cb_delete_ok(query: CallbackQuery, callback_data: FacCb, user: BotUser, t: Translate) -> None:
        if (child := await owned(query, callback_data.id, t)) is None:
            return
        await children.delete(child)
        await ctx.audit.record(user.user_id, "factory.delete", child.bot_id)
        text, kb = await list_view(user.user_id, 1, t)
        await show(query, t("fac-deleted", username=child.username) + "\n\n" + text, kb)

    # ------------------------------------------------------------------ gallery
    @router.message(Command("top"))
    async def cmd_top(message: Message, t: Translate) -> None:
        text, kb = await gallery_view(t)
        await message.answer(text, reply_markup=kb)

    @router.callback_query(FacCb.filter(F.action == "gallery"))
    async def cb_gallery(query: CallbackQuery, t: Translate) -> None:
        text, kb = await gallery_view(t)
        await show(query, text, kb)

    async def gallery_view(t: Translate) -> tuple[str, InlineKeyboardMarkup]:
        entries = await children.gallery(limit=10)
        lines = [t("fac-gallery")]
        rows = []
        for i, e in enumerate(entries, 1):
            lines.append(f"{i}. @{esc(e.bot.username)} · {tpl_name(t, e.bot.template)} · 👥 {e.users:,}")
            rows.append([InlineKeyboardButton(text=f"{i}. @{e.bot.username}", url=f"https://t.me/{e.bot.username}")])
        if not entries:
            lines.append(t("fac-gallery-empty"))
        rows.append([btn(t("fac-btn-new"), "new"), btn(t("btn-back"), "home")])
        return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)

    return router
