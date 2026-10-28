"""Settings panel: /settings in a group opens an inline panel in the admin's private chat."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from pydantic import ValidationError

from bots.groupguard import actions, authz
from bots.groupguard.chatconfig import LOCK_TYPES, ChatConfig
from bots.groupguard.handlers.content import config_operation
from bots.groupguard.keyboards import GgCb
from bots.groupguard.lock_types import CANONICAL_LOCKS, expand
from bots.groupguard.operations import operation_for, submit
from bots.groupguard.scope import GroupMessages, target_chat
from bots.groupguard.service import GuardService
from core.db.models import BotUser
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.text import esc

# Short panel code -> (config field, values to cycle through)
CYCLES: dict[str, tuple[str, list]] = {
    "wel": ("welcome", [True, False]),
    "cln": ("clean_service", [True, False]),
    "bye": ("goodbye", [False, True]),
    "cap": ("captcha", ["button", "math", "text", "text2", "off"]),
    "cpm": ("captcha_minutes", [5, 10, 2]),
    "fld": ("flood_count", [6, 10, 4, 0]),
    "fla": ("flood_action", ["mute", "kick", "ban"]),
    "wrn": ("warn_limit", [3, 5, 2]),
    "wra": ("warn_action", ["ban", "mute", "kick"]),
    "act": ("action_minutes", [60, 1440, 10080, 10]),
    "cas": ("cas", [True, False]),
    "nwb": ("newbie_hours", [24, 72, 0]),
    "ais": ("ai_spam", [False, True]),
    "ngt": ("night", [False, True]),
    "crd": ("credit", [True, False]),
}


def _next(values: list, current: object) -> object:
    try:
        return values[(values.index(current) + 1) % len(values)]
    except ValueError:
        return values[0]


def fmt(t: Translate, value: object) -> str:
    if isinstance(value, bool):
        return "✅" if value else "❌"
    return t(f"gg-val-{value}") if isinstance(value, str) else str(value)

def b(text: str, action: str, chat: int, arg: str = "") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=GgCb(action=action, chat=chat, arg=arg).pack())

def panel(ctx: BotContext, t: Translate, chat_id: int, title: str, cfg: ChatConfig) -> tuple[str, InlineKeyboardMarkup]:
    t=actions.group_t(ctx,cfg)
    def opt(code: str) -> InlineKeyboardButton:
        field = CYCLES[code][0]
        return b(t(f"gg-opt-{code}", value=fmt(t, getattr(cfg, field))), "set", chat_id, code)

    rows = [
        [opt("wel"), opt("cln")],
        [opt("bye"), opt("cas")],
        [opt("cap"), opt("cpm")],
        [opt("fld"), opt("fla")],
        [opt("wrn"), opt("wra")],
        [opt("act"), opt("nwb")],
        [b(t("gg-btn-locks", count=str(len(cfg.locks))), "locks", chat_id), opt("ngt")],
    ]
    extra = [b(t("gg-opt-lang", value=cfg.lang or ctx.translator.default), "lang", chat_id)]
    if ctx.ai is not None:
        extra.insert(0, opt("ais"))
    rows.append(extra)
    if ctx.child is None:
        rows.append([opt("crd")])
    rows.append([b(t("btn-close"), "close", chat_id)])
    text = t("gg-panel", group=esc(title), night=f"{cfg.night_start:02d}:00–{cfg.night_end:02d}:00 (UTC{cfg.tz_offset:+d})")
    return text, InlineKeyboardMarkup(inline_keyboard=rows)

def locks_panel(t: Translate, chat_id: int, cfg: ChatConfig) -> tuple[str, InlineKeyboardMarkup]:
    rows, row = [], []
    for kind in CANONICAL_LOCKS:
        row.append(b(f"{'🔒' if cfg.locked(kind) else '🔓'} {t(f'gg-lock-{kind}')}", "lock", chat_id, kind))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([b(t("btn-back"), "panel", chat_id)])
    return t("gg-locks-panel"), InlineKeyboardMarkup(inline_keyboard=rows)


async def open_panel(ctx: BotContext, chat_id: int, user_id: int, t: Translate) -> bool:
    svc: GuardService = ctx.extras["guard"]
    cfg = await svc.config(chat_id, fresh=True)
    text, kb = panel(ctx, t, chat_id, await svc.title(chat_id) or str(chat_id), cfg)
    authorization = await authz.authorize(ctx, authz.Actor(ctx.bot_id, chat_id, "human", user_id),
        target_chat_id=chat_id, caller_rights=frozenset({"change_info"}), bot_rights=frozenset())
    if not authorization.allowed:
        return False
    try:
        sent = await ctx.bot.send_message(user_id, text, reply_markup=kb)
    except TelegramAPIError:
        return False
    return await authz.bind_message(ctx, sent, target_chat_id=chat_id, owner_id=user_id, kind="settings")


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_panel")
    svc: GuardService = ctx.extras["guard"]

    async def guard(query: CallbackQuery, chat_id: int, t: Translate) -> ChatConfig | None:
        if not await authz.bound_message(ctx, query, target_chat_id=chat_id, kind="settings"):
            await query.answer(t("gg-auth-denied"), show_alert=True)
            return None
        from bots.groupguard import policies
        action = GgCb.unpack(query.data or "").action
        if action == "locks" and (not await policies.allowed(ctx,"locks",chat_id,authz.actor_from_callback(ctx,query))
                or not await policies.allowed(ctx,"locktypes",chat_id,authz.actor_from_callback(ctx,query))):
            await query.answer(t("gg-auth-denied"),show_alert=True)
            return None
        cfg = await svc.config(chat_id, fresh=True)
        authorized = await authz.authorize(ctx, authz.actor_from_callback(ctx, query), target_chat_id=chat_id,
                                           caller_rights=frozenset({"change_info"}), bot_rights=frozenset())
        if not authorized.allowed:
            await query.answer(t("gg-auth-denied"), show_alert=True)
            return None
        return cfg

    async def show_panel(query: CallbackQuery, text: str, kb: InlineKeyboardMarkup, *, mutated: bool = False,
                         chat_id: int) -> None:
        if not isinstance(query.message, Message):
            return
        msg = query.message
        notice = await actions.perform("panel_notice", lambda: msg.edit_text(text, reply_markup=kb))
        if mutated:
            await ctx.audit.record(query.from_user.id, "gg_panel_config", target=chat_id,
                                   outcome="applied" if notice.completed else "partial", primary_completed=True,
                                   notification=notice.status, error_code=notice.error_code)
        await query.answer("" if notice.completed else ctx.translator.bind(query.from_user.language_code)(
            "gg-outcome-ancillary" if mutated else "gg-outcome-failed"))

    @router.message(GroupMessages(), Command("settings"))
    async def cmd_settings(message: Message, t: Translate) -> None:
        await submit(ctx, message, operation_for(message, "panel"))

    @router.message(CommandStart(deep_link=True), F.chat.type == "private", F.text.regexp(r"^/start gs_-?\d+$"))
    async def start_settings(message: Message, command: CommandObject, t: Translate) -> None:
        chat_id = int((command.args or "")[3:])
        authorized = await authz.authorize(ctx, authz.actor_from_message(ctx, message), target_chat_id=chat_id,
                                           caller_rights=frozenset({"change_info"}), bot_rights=frozenset())
        if not authorized.allowed or message.from_user is None:
            await message.answer(t("gg-auth-denied"))
            return
        await open_panel(ctx, chat_id, message.from_user.id, t)

    @router.callback_query(GgCb.filter(F.action == "set"))
    async def cb_set(query: CallbackQuery, callback_data: GgCb, t: Translate, user: BotUser | None = None) -> None:
        if (cfg := await guard(query, callback_data.chat, t)) is None or callback_data.arg not in CYCLES:
            return
        field, values = CYCLES[callback_data.arg]
        if field == "credit" and ctx.child is not None:
            await query.answer(t("gg-auth-denied"), show_alert=True)
            return
        if field == "credit" and cfg.credit and not (user is not None and user.is_vip()):
            await query.answer(t("gg-credit-vip"), show_alert=True)
            return
        patch = {field: _next(values, getattr(cfg, field))}
        if field == "captcha":
            patch["captcha_enabled"] = patch[field] != "off"
        cfg = await svc.update_config(callback_data.chat, **patch)
        text, kb = panel(ctx, t, callback_data.chat, await svc.title(callback_data.chat) or "", cfg)
        await show_panel(query, text, kb, mutated=True, chat_id=callback_data.chat)

    @router.callback_query(GgCb.filter(F.action == "lang"))
    async def cb_lang(query: CallbackQuery, callback_data: GgCb, t: Translate) -> None:
        if (cfg := await guard(query, callback_data.chat, t)) is None:
            return
        cfg = await svc.update_config(callback_data.chat, lang=_next(ctx.translator.locales, cfg.lang or ctx.translator.default))
        text, kb = panel(ctx, t, callback_data.chat, await svc.title(callback_data.chat) or "", cfg)
        await show_panel(query, text, kb, mutated=True, chat_id=callback_data.chat)

    @router.callback_query(GgCb.filter(F.action.in_({"locks", "lock", "panel"})))
    async def cb_locks(query: CallbackQuery, callback_data: GgCb, t: Translate) -> None:
        if (cfg := await guard(query, callback_data.chat, t)) is None:
            return
        t=actions.group_t(ctx,cfg)
        if callback_data.action == "panel":
            text, kb = panel(ctx, t, callback_data.chat, await svc.title(callback_data.chat) or "", cfg)
            await show_panel(query, text, kb, chat_id=callback_data.chat)
            return
        if callback_data.action == "lock" and callback_data.arg in LOCK_TYPES:
            configured=set(expand(cfg.locks))
            wanted=set(expand([callback_data.arg]))
            configured=configured-wanted if wanted<=configured else configured|wanted
            cfg = await svc.update_config(callback_data.chat, locks=sorted(configured),lock_schema_version=1)
        text, kb = locks_panel(t, callback_data.chat, cfg)
        await show_panel(query, text, kb, mutated=callback_data.action == "lock" and callback_data.arg in LOCK_TYPES,
                         chat_id=callback_data.chat)

    @router.callback_query(GgCb.filter(F.action == "close"))
    async def cb_close(query: CallbackQuery, callback_data: GgCb, t: Translate) -> None:
        if (await guard(query, callback_data.chat, t)) is None or not isinstance(query.message, Message):
            return
        msg = query.message
        result = await actions.perform("close_panel", lambda: msg.delete())
        if result.completed:
            await ctx.redis.delete(authz.binding_key(ctx, msg))
        await query.answer("" if result.completed else t("gg-outcome-failed"))

    @router.message(GroupMessages(), Command("setlang"))
    async def cmd_setlang(message: Message, command: CommandObject) -> None:
        cfg = await svc.config(target_chat(message).id,fresh=True)
        t = actions.group_t(ctx,cfg)
        code=(command.args or '').lower().replace('_','-')
        if code not in ctx.translator.locales:
            await message.reply(t('gg-language-usage',codes=' '.join(ctx.translator.locales)))
            return
        await config_operation(ctx,message,{'lang':code},'gg-language-saved')

    @router.message(GroupMessages(), Command("night"))
    async def cmd_night(message: Message, command: CommandObject) -> None:
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        args = (command.args or "").split()
        if args == ["off"]:
            await config_operation(ctx, message, {"night": False}, "gg-night-off")
            return
        try:
            if len(args) not in (2, 3):
                raise ValueError("syntax")
            start, end = int(args[0]), int(args[1])
            offset = int(args[2]) if len(args) == 3 else cfg.tz_offset
            await config_operation(ctx, message, dict(night=True, night_start=start, night_end=end, tz_offset=offset),
                                   "gg-night-on", start=f"{start:02d}:00", end=f"{end:02d}:00", tz=f"UTC{offset:+d}")
        except (ValueError, ValidationError):
            await message.reply(t("gg-night-usage"))

    return router
