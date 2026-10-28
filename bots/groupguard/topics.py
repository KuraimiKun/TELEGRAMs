"""Actual forum methods with precise rights and explicit general-topic semantics."""

from __future__ import annotations

from aiogram.exceptions import TelegramAPIError

from bots.groupguard import actions
from bots.groupguard.contracts import ActionResult
from core.sdk.context import BotContext


async def change(ctx: BotContext, op) -> ActionResult:
    try:
        chat = await ctx.bot.get_chat(op.target_chat_id)
    except TelegramAPIError:
        return actions.failure("topic", "lookup_failed")
    if chat is None or chat.id != op.target_chat_id or not chat.is_forum:
        return actions.failure("topic", "not_forum")
    topic_id = op.topic_id or 1
    if op.kind == "topic_delete" and topic_id == 1:
        return actions.failure("topic_delete", "general_not_deletable")

    async def rpc():
        if op.kind == "topic_create":
            return await ctx.bot.create_forum_topic(op.target_chat_id, op.topic_name)
        if op.kind == "topic_rename":
            return (
                await ctx.bot.edit_general_forum_topic(op.target_chat_id, op.topic_name)
                if topic_id == 1
                else await ctx.bot.edit_forum_topic(op.target_chat_id, topic_id, name=op.topic_name)
            )
        if op.kind == "topic_close":
            return (
                await ctx.bot.close_general_forum_topic(op.target_chat_id)
                if topic_id == 1
                else await ctx.bot.close_forum_topic(op.target_chat_id, topic_id)
            )
        if op.kind == "topic_reopen":
            return (
                await ctx.bot.reopen_general_forum_topic(op.target_chat_id)
                if topic_id == 1
                else await ctx.bot.reopen_forum_topic(op.target_chat_id, topic_id)
            )
        return await ctx.bot.delete_forum_topic(op.target_chat_id, topic_id)

    from bots.groupguard.contracts import result_of

    return result_of(await actions.perform(op.kind, rpc))
