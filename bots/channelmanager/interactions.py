"""Destination/version-bound post buttons and SQL-serialized single-choice voting."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery
from sqlalchemy import func, insert, literal, select

from bots.channelmanager import outbox
from bots.channelmanager.content import ContentError, LinkButton, PostSpec
from bots.channelmanager.models import Channel, Delivery, Post, PostVersion, Vote, VoteBoard
from core.i18n import Translate
from core.sdk.context import BotContext


def choice_button(spec: PostSpec, choice: int) -> LinkButton:
    if 40 <= choice < 40 + len(spec.reactions):
        return LinkButton(text=spec.reactions[choice - 40], kind="vote")
    row, col = divmod(choice, 4)
    if choice < 0 or row >= len(spec.buttons) or col >= len(spec.buttons[row]):
        raise ContentError("stale")
    return spec.buttons[row][col]


async def queue_markup(session, ctx: BotContext, target: Delivery, version: int, actor_id: int, revision: str) -> None:
    channel = await session.get(Channel, (ctx.bot_id, target.channel_id))
    assert channel is not None
    target.markup_status = "pending"
    target.markup_op = await outbox.enqueue(session, ctx, channel, kind="markup",
        dedupe_key=f"markup:{target.id}:{version}:{revision}", payload={"delivery_id": target.id,
            "version": version, "actor_id": actor_id, "automatic": True})


def ballot(spec: PostSpec):
    return (tuple(spec.reactions), tuple((row_index * 4 + col, button.text) for row_index, row in enumerate(spec.buttons)
        for col, button in enumerate(row) if button.kind == "vote"))


async def published(session, ctx: BotContext, target: Delivery, spec: PostSpec, actor_id: int,
                    previous_version: int | None = None) -> None:
    has_votes = bool(spec.reactions or any(b.kind == "vote" for row in spec.buttons for b in row))
    if has_votes and await session.get(VoteBoard, (ctx.bot_id, target.id, target.version)) is None:
        previous = await session.get(PostVersion, (ctx.bot_id, target.post_id, previous_version)) if previous_version else None
        old_board = await session.get(VoteBoard, (ctx.bot_id, target.id, previous_version)) if previous_version else None
        preserve = bool(previous and old_board and ballot(PostSpec.model_validate(previous.spec)) == ballot(spec))
        session.add(VoteBoard(bot_id=ctx.bot_id, delivery_id=target.id, version=target.version,
            closed=old_board.closed if preserve and old_board else False, revision=old_board.revision if preserve and old_board else 0))
        await session.flush()
        if preserve:
            await session.execute(insert(Vote).from_select(["bot_id", "delivery_id", "version", "user_id", "choice"],
                select(Vote.bot_id, Vote.delivery_id, literal(target.version), Vote.user_id, Vote.choice).where(
                    Vote.bot_id == ctx.bot_id, Vote.delivery_id == target.id, Vote.version == previous_version)))
    if (previous_version and has_votes) or any(b.kind == "share" and b.url is None for row in spec.buttons for b in row):
        await queue_markup(session, ctx, target, target.version, actor_id, "published")


async def keyboard(ctx: BotContext, target: Delivery, spec: PostSpec, version: int):
    async with ctx.sm() as session:
        board = await session.get(VoteBoard, (ctx.bot_id, target.id, version))
        counts = dict((await session.execute(select(Vote.choice, func.count()).where(Vote.bot_id == ctx.bot_id,
            Vote.delivery_id == target.id, Vote.version == version).group_by(Vote.choice))).all())
    return spec.keyboard(delivery_id=target.id, version=version, channel_id=target.channel_id,
        message_id=target.message_id, counts=counts, closed=bool(board and board.closed))


async def cast(ctx: BotContext, delivery_id: str, version: int, user_id: int, choice: int) -> bool:
    async with ctx.sm() as session:
        target = await session.get(Delivery, (ctx.bot_id, delivery_id))
        if target is None:
            raise ContentError("stale")
        post = await session.get(Post, (ctx.bot_id, target.post_id), with_for_update=True)
        target = await session.get(Delivery, (ctx.bot_id, delivery_id), with_for_update=True, populate_existing=True)
        board = await session.get(VoteBoard, (ctx.bot_id, delivery_id, version), with_for_update=True)
        channel = await session.get(Channel, (ctx.bot_id, target.channel_id)) if target else None
        if post is None or post.detached or target is None or target.state != "sent" or target.version != version or board is None:
            raise ContentError("stale")
        if channel is None or channel.status == "disconnected":
            raise ContentError("stale")
        if board.closed:
            raise ContentError("closed")
        content = await session.get(PostVersion, (ctx.bot_id, target.post_id, version))
        assert content is not None
        if choice_button(PostSpec.model_validate(content.spec), choice).kind != "vote":
            raise ContentError("buttons")
        vote = await session.get(Vote, (ctx.bot_id, delivery_id, version, user_id))
        if vote and vote.choice == choice:
            return False
        if vote is None:
            session.add(Vote(bot_id=ctx.bot_id, delivery_id=delivery_id, version=version, user_id=user_id, choice=choice))
        else:
            vote.choice = choice
        board.revision += 1
        await queue_markup(session, ctx, target, version, post.creator_id, str(board.revision))
        await session.commit()
        return True


async def close(ctx: BotContext, post_id: str, user_id: int, generation: int) -> None:
    posts = ctx.extras["posts"]
    await posts.view(post_id, user_id, "edit")
    async with ctx.sm() as session:
        post = await posts.locked(session, post_id, generation)
        for target in await posts.deliveries(session, post):
            if target.state != "sent":
                continue
            board = await session.get(VoteBoard, (ctx.bot_id, target.id, target.version), with_for_update=True)
            if board and not board.closed:
                board.closed, board.revision = True, board.revision + 1
                await queue_markup(session, ctx, target, target.version, user_id, str(board.revision))
        await session.commit()


def build_router(ctx: BotContext) -> Router:
    router = Router(name=f"chm_interactions_{ctx.slug}")

    @router.callback_query(F.data.startswith("chi:"))
    async def callback(query: CallbackQuery, t: Translate):
        try:
            if query.data == "chi:preview":
                await query.answer(t("chm-interaction-preview"), show_alert=True)
                return
            parts = (query.data or "").split(":")
            if len(parts) != 4 or len(parts[1]) != 32 or query.from_user.is_bot:
                raise ContentError("stale")
            delivery_id, version, choice = parts[1], int(parts[2]), int(parts[3])
            async with ctx.sm() as session:
                target = await session.get(Delivery, (ctx.bot_id, delivery_id))
                if target is None or target.state != "sent" or target.version != version or query.message is None or (
                    query.message.chat.id != target.channel_id or query.message.message_id != target.message_id):
                    raise ContentError("stale")
                post = await session.get(Post, (ctx.bot_id, target.post_id))
                channel = await session.get(Channel, (ctx.bot_id, target.channel_id))
                content = await session.get(PostVersion, (ctx.bot_id, target.post_id, version))
                if post is None or post.detached or content is None or channel is None or channel.status == "disconnected":
                    raise ContentError("stale")
                button = choice_button(PostSpec.model_validate(content.spec), choice)
            if button.kind == "vote":
                await cast(ctx, delivery_id, version, query.from_user.id, choice)
                await query.answer(t("chm-vote-recorded"))
            elif button.kind in {"popup", "alert", "member"}:
                value = button.value
                if button.kind == "member":
                    assert button.required_channel is not None
                    async with ctx.sm() as session:
                        required = await session.get(Channel, (ctx.bot_id, button.required_channel))
                        if required is None or required.status != "active":
                            raise ContentError("stale")
                    member = await ctx.bot.get_chat_member(button.required_channel, query.from_user.id)
                    present = member.status in {"creator", "administrator", "member"} or (member.status == "restricted" and bool(getattr(member, "is_member", False)))
                    value = button.value if present else button.otherwise or t("chm-membership-required")
                await query.answer(value, show_alert=button.kind in {"alert", "member"}, cache_time=0)
            else:
                raise ContentError("stale")
        except (ValueError, TelegramAPIError) as exc:
            await query.answer(t("chm-voting-closed") if str(exc) == "closed" else t("chm-interaction-unavailable"), show_alert=True)

    return router
