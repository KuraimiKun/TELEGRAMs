"""Scoped forum management and replay-protected destructive confirmation."""

from __future__ import annotations

import json
import secrets

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from redis.exceptions import RedisError

from bots.groupguard import actions, authz
from bots.groupguard.handlers.content import config_operation
from bots.groupguard.keyboards import GgCb
from bots.groupguard.operations import (
    Kind,
    Operation,
    execute,
    operation_authorization,
    operation_for,
    submit,
)
from bots.groupguard.reviews import CLAIM
from bots.groupguard.scope import GroupMessages, target_chat
from core.sdk.context import BotContext


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_topics")
    router.message.filter(GroupMessages())
    svc = ctx.extras["guard"]

    @router.message(
        Command(
            "setactiontopic",
            "actiontopic",
            "newtopic",
            "renametopic",
            "closetopic",
            "reopentopic",
            "deletetopic",
        )
    )
    async def command(message: Message, command: CommandObject):
        chat = target_chat(message)
        cfg = await svc.config(chat.id, fresh=True)
        t = actions.group_t(ctx, cfg)
        name, args = command.command, (command.args or "").strip()
        if name == "actiontopic":
            await message.reply(t("gg-action-topic", topic=str(cfg.action_topic or 1)))
            return
        if name == "setactiontopic":
            try:
                actual = await ctx.bot.get_chat(chat.id)
            except TelegramAPIError:
                actual = None
            if actual is None or actual.id != chat.id or not actual.is_forum:
                await message.reply(t("gg-topic-unavailable"))
                return
            topic = message.message_thread_id or 1
            await config_operation(
                ctx,
                message,
                {"action_topic": None if topic == 1 else topic},
                "gg-setting-saved",
                setting=name,
            )
            return
        topic_id = message.message_thread_id or 1
        if message.chat.type == "private" and name != "newtopic":
            first, _, rest = args.partition(" ")
            if not first.isdigit() or not 1 <= int(first) <= 2147483647:
                await message.reply(t("gg-topic-id-required"))
                return
            topic_id, args = int(first), rest.strip()
        kinds: dict[str,Kind] = {
            "newtopic": "topic_create",
            "renametopic": "topic_rename",
            "closetopic": "topic_close",
            "reopentopic": "topic_reopen",
            "deletetopic": "topic_delete",
        }
        kind = kinds[name]
        if (name in {"newtopic", "renametopic"} and not 1 <= len(args) <= 128) or (
            name not in {"newtopic", "renametopic"} and args
        ):
            await message.reply(t("gg-setting-invalid"))
            return
        op = operation_for(message, kind, topic_id=topic_id, topic_name=args)
        if name != "deletetopic":
            await submit(ctx, message, op)
            return
        actor = authz.actor_from_message(ctx, message)
        if topic_id == 1:
            await message.reply(t("gg-topic-general-delete"))
            return
        if actor.kind in {"bot","anonymous_group"}:
            from bots.groupguard.reviews import create_review
            await create_review(ctx,actor,op)
            return
        if actor.kind != "human" or actor.human_id is None:
            await message.reply(t("gg-human-required"))
            return
        permitted = await operation_authorization(ctx, actor, op)
        if not permitted.allowed:
            await message.reply(t("gg-auth-denied"))
            return
        nonce = secrets.token_urlsafe(16)
        state = dict(bot_id=ctx.bot_id, user_id=actor.human_id, operation=op.model_dump_json())
        try:
            await ctx.redis.set(ctx.keys("topic_confirm", nonce), json.dumps(state), ex=120, nx=True)
            sent = await message.reply(
                t("gg-topic-delete-confirm", topic=str(topic_id)),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=t("gg-btn-confirm-delete"),
                                callback_data=GgCb(action="td", chat=chat.id, arg=nonce).pack(),
                            )
                        ]
                    ]
                ),
            )
            await authz.bind_message(
                ctx,
                sent,
                target_chat_id=chat.id,
                owner_id=actor.human_id,
                kind="topic_delete",
                data=nonce,
                slot="topic",
            )
        except RedisError:
            await message.reply(t("gg-outcome-failed"))

    @router.callback_query(GgCb.filter(F.action == "td"))
    async def delete(query: CallbackQuery, callback_data: GgCb, t):
        if not isinstance(query.message, Message) or not await authz.bound_message(
            ctx,
            query,
            target_chat_id=callback_data.chat,
            kind="topic_delete",
            data=callback_data.arg,
            slot="topic",
        ):
            await query.answer(t("gg-auth-denied"), show_alert=True)
            return
        key = ctx.keys("topic_confirm", callback_data.arg)
        try:
            raw = await ctx.redis.get(key)
            state = json.loads(raw) if raw else {}
            op = Operation.model_validate_json(state["operation"])
            valid = (
                state.get("bot_id") == ctx.bot_id
                and state.get("user_id") == query.from_user.id
                and op.target_chat_id == callback_data.chat
                and op.kind == "topic_delete"
            )
            actor = authz.actor_from_callback(ctx, query)
            # The confirmation message is separate from the original actual command source.
            actor = authz.Actor(
                ctx.bot_id,
                op.source_chat_id,
                "human",
                query.from_user.id,
                message_id=query.message.message_id,
                thread_id=query.message.message_thread_id,
            )
            if not valid or not (await operation_authorization(ctx, actor, op)).allowed:
                raise ValueError("wrong_scope")
            if await ctx.redis.eval(CLAIM, 1, key, raw) != 1:  # type: ignore[misc]
                raise ValueError("claimed")
        except (RedisError, ValueError, TypeError, KeyError):
            await query.answer(t("gg-auth-denied"), show_alert=True)
            return
        result = await execute(ctx, actor, op)
        await query.answer(
            t("gg-done") if result.primary_completed else t("gg-outcome-failed"),
            show_alert=not result.primary_completed,
        )

    return router
