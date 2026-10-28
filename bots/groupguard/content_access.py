"""Fresh read authority for content commands, bound menus and opaque private links."""
from __future__ import annotations

import json
import re

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message, User
from redis.exceptions import RedisError

from bots.groupguard import actions, authz, delivery, perms, policies
from bots.groupguard.contracts import ActorKind, result_of
from bots.groupguard.delivery import Content, Delivered
from bots.groupguard.formatting import ContentError, parse_controls
from bots.groupguard.keyboards import GgCb
from core.sdk.context import BotContext


async def display(ctx: BotContext, *, chat_id: int, destination: int, user: User | None, kind: str,
                  key: str = "", reply_id: int | None = None, thread_id: int | None = None,
                  sender_chat=None, noformat: bool = False, subject_user: User | None = None,
                  subject_chat=None) -> Delivered | None:
    svc = ctx.extras["guard"]
    cfg = await svc.config(chat_id, fresh=True)
    t = actions.group_t(ctx, cfg)
    if kind == "rules":
        actor_kind: ActorKind = "human" if user is not None and not user.is_bot else "bot" if user is not None else "anonymous_group" if sender_chat is not None and sender_chat.id == chat_id else "channel"
        actor = authz.Actor(ctx.bot_id,destination,actor_kind,human_id=user.id if user is not None and not user.is_bot else None,
            sender_chat_id=sender_chat.id if sender_chat is not None else None,
            bot_sender_id=user.id if user is not None and user.is_bot else None)
        if not await policies.allowed(ctx,"rules",chat_id,actor):
            return None
    if chat_id >= 0 or not (await authz.internal_authorize(ctx, chat_id, frozenset())).allowed:
        return None
    if user is not None and not user.is_bot and not await delivery.current_member(ctx, chat_id, user.id):
        return None
    if kind == "rules":
        if not cfg.rules:
            return Delivered(actions.failure("content", "missing_rules"))
        content = Content(cfg.rules, cfg.rules_format)
    else:
        item = await svc.get_item(chat_id, kind, key)
        if item is None:
            return None
        content = Content.from_dict(dict(raw=item.text or "", format=item.content_format,
            media_kind=item.media_kind, file_id=item.file_id))
    try:
        _, controls = parse_controls(content.raw, kind, format=content.format)
    except ContentError:
        return None
    admin = False
    if user is not None:
        rights = await perms.fresh_rights(ctx, chat_id, user.id)
        admin = rights is not None and rights.is_admin
    if (controls.admin and not admin) or (controls.user and admin):
        return None
    if user is not None and user.is_bot and (kind != "filter" or not controls.allow_bot):
        return None
    private = (kind == "rules" and cfg.private_rules) or (kind == "note" and (controls.private or cfg.private_notes) and not controls.noprivate)
    if destination > 0 and (user is None or user.is_bot or destination != user.id):
        return None
    if (private or destination > 0) and (user is None or user.is_bot):
        return None
    if private and destination < 0:
        kb = await delivery.private_button(ctx, chat_id, kind=kind, key=key,
            label=cfg.rules_button or t("gg-btn-rules") if kind == "rules" else t("gg-btn-private-note"),
            user_id=user.id if user else None, noformat=noformat)
        if kb is None:
            return Delivered(actions.failure("content", "state_failed"))
        return Delivered(result_of(await actions.notify(ctx, destination, t("gg-open-private"), reply_markup=kb,
            reply_to_message_id=reply_id, message_thread_id=thread_id)))
    if noformat:
        # Copyable source, with HTML escaping rather than rendering Rose syntax.
        from core.ui.text import esc
        content = Content("<pre>" + esc(content.raw) + "</pre>", "html", content.media_kind, content.file_id)
    f = await delivery.fillings(ctx, chat_id, None if subject_chat else subject_user or user,
        sender_chat=subject_chat or sender_chat, raw=content.raw)
    return await delivery.send(ctx, destination, content, f, kind=kind, reply_id=reply_id,
        thread_id=thread_id, owner_id=user.id if user is not None and destination > 0 else None)


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_content_access")

    @router.message(F.chat.type == "private", CommandStart(deep_link=True), F.text.regexp(r"^/start(?:@\w+)? ggo_[A-Za-z0-9_-]{20,32}$"))
    async def private_open(message: Message, command: CommandObject, t) -> None:
        user = message.from_user
        if user is None or user.is_bot or message.chat.id != user.id:
            return
        try:
            raw = await ctx.redis.get(ctx.keys("content_open", (command.args or "")[4:]))
            state = json.loads(raw) if raw else {}
            valid = (state.get("bot_id") == ctx.bot_id and isinstance(state.get("chat_id"), int)
                and state["chat_id"] < 0 and state.get("owner_id") in (None, user.id)
                and state.get("kind") in {"note", "rules"} and isinstance(state.get("key", ""), str))
        except (RedisError, TypeError, ValueError):
            valid = False
        sent = await display(ctx, chat_id=state["chat_id"], destination=user.id, user=user,
            kind=state["kind"], key=state.get("key", ""), noformat=state.get("noformat") is True) if valid else None
        if sent is None or not sent.result.primary_completed:
            await message.answer(t("gg-content-unavailable"))

    @router.callback_query(GgCb.filter(F.action == "menu"))
    async def menu(query: CallbackQuery, callback_data: GgCb, t) -> None:
        msg = query.message
        if not isinstance(msg, Message) or query.from_user.is_bot or not re.fullmatch(r"[A-Za-z0-9_-]{12}", callback_data.arg):
            await query.answer(t("gg-content-unavailable"), show_alert=True)
            return
        try:
            raw = await ctx.redis.get(authz.binding_key(ctx, msg, slot="content"))
            state = json.loads(raw) if raw else {}
            data = state.get("data", "{}")
            targets = json.loads(data)
            target = targets.get(callback_data.arg)
            valid = isinstance(target, dict) and target.get("kind") in {"note", "rules"} and await authz.bound_message(
                ctx, query, target_chat_id=callback_data.chat, kind="content", data=data, slot="content")
        except (RedisError, ValueError, TypeError, AttributeError):
            valid = False
        sent = await display(ctx, chat_id=callback_data.chat, destination=msg.chat.id, user=query.from_user,
            kind=target["kind"], key=target.get("key", ""), reply_id=msg.message_id if msg.chat.id < 0 else None,
            thread_id=msg.message_thread_id) if valid else None
        await query.answer("" if sent is not None and sent.result.primary_completed else t("gg-content-unavailable"),
            show_alert=sent is None or not sent.result.primary_completed)

    return router
