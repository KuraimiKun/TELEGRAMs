"""Formatted echo and isolated operator group broadcast, preserving core private dashboards."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bots.groupguard import actions, group_broadcast
from bots.groupguard.content_commands import argument_start, replied_content, valid
from bots.groupguard.operations import operation_for, submit
from bots.groupguard.scope import GroupMessages, target_chat
from core.sdk.context import BotContext


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_utilities")

    @router.message(GroupMessages(), Command("echo", "say"))
    async def echo(message: Message):
        t = actions.group_t(ctx, await ctx.extras["guard"].config(target_chat(message).id))
        try:
            content = replied_content(message, argument_start(message))
            valid(content, target_chat(message).id, "echo")
        except ValueError:
            await message.reply(t("gg-content-invalid"))
            return
        await submit(
            ctx,
            message,
            operation_for(
                message,
                "echo",
                text=content.raw,
                content_format=content.format,
                media_kind=content.media_kind,
                file_id=content.file_id,
            ),
        )

    @router.message(F.chat.type.in_({"private", "group", "supergroup"}), Command("broadcast"))
    async def broadcast(message: Message, command: CommandObject, t):
        user = message.from_user
        if (
            user is None
            or user.is_bot
            or message.sender_chat is not None
            or not await group_broadcast.owner(ctx, user.id)
        ):
            await message.reply(t("gg-broadcast-owner"))
            return
        if not command.args and message.reply_to_message is None:
            state = await group_broadcast.latest_status(ctx, user.id)
            if state is None:
                await message.reply(t("gg-broadcast-empty"))
            else:
                campaign, counts = state
                await message.reply(t("gg-broadcast-status", id=str(campaign.id), status=campaign.status,
                    queued=str(counts.get("pending", 0) + counts.get("running", 0)),
                    sent=str(counts.get("succeeded", 0)), failed=str(counts.get("failed", 0)),
                    uncertain=str(counts.get("uncertain", 0)), cancelled=str(counts.get("cancelled", 0))))
            return
        try:
            content = replied_content(message, argument_start(message))
            valid(content, -1, "broadcast")
        except ValueError:
            await message.reply(t("gg-content-invalid"))
            return
        created = await group_broadcast.create(ctx, user, content)
        await message.reply(
            t("gg-broadcast-queued", id=str(created.id)) if created else t("gg-broadcast-busy")
        )

    return router
