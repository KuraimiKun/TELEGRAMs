"""Promotion rights are bounded by the current caller/bot intersection."""
from __future__ import annotations

from aiogram.methods import PromoteChatMember
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner

from bots.groupguard import actions, perms
from bots.groupguard.contracts import ActionResult, Actor, result_of
from bots.groupguard.operations import Operation
from core.sdk.context import BotContext


async def change_admin(ctx: BotContext, actor: Actor, op: Operation) -> ActionResult:
    target = await perms.fresh_member(ctx, op.target_chat_id, op.target_id or 0)
    if target is None:
        return actions.failure(op.kind, "target_lookup_failed")
    if target.user.is_bot or isinstance(target, ChatMemberOwner):
        return actions.failure(op.kind, "target_protected")
    if isinstance(target, ChatMemberAdministrator) and not target.can_be_edited:
        return actions.failure(op.kind, "target_not_editable")
    if op.kind == "demote" and not isinstance(target, ChatMemberAdministrator):
        return actions.failure(op.kind, "target_not_admin")
    bot = await perms.fresh_member(ctx, op.target_chat_id, ctx.bot_id)
    caller = await perms.fresh_member(ctx, op.target_chat_id, actor.human_id) if actor.human_id else bot
    if bot is None or caller is None or not perms.member_rights(bot).allows("promote_members") or not perms.member_rights(caller).allows("promote_members"):
        return actions.failure(op.kind, "promotion_revoked")
    values = {}
    for field in PromoteChatMember.model_fields:
        if not field.startswith("can_"):
            continue
        values[field] = (op.kind == "promote" and field != "can_promote_members"
            and (isinstance(caller, ChatMemberOwner) or getattr(caller, field, False) is True)
            and (isinstance(bot, ChatMemberOwner) or getattr(bot, field, False) is True))
    values["is_anonymous"] = False
    result = result_of(await actions.perform(op.kind, lambda: ctx.bot.promote_chat_member(
        op.target_chat_id, op.target_id or 0, **values)))
    if result.primary_completed:
        await perms.forget_admins(ctx, op.target_chat_id)
    return result


async def public_admins(ctx: BotContext, chat_id: int):
    from aiogram.exceptions import TelegramAPIError
    try:
        members = await ctx.bot.get_chat_administrators(chat_id)
    except TelegramAPIError:
        return None
    return [member for member in members if isinstance(member, (ChatMemberOwner, ChatMemberAdministrator))
            and not member.is_anonymous and not member.user.is_bot
            and perms.valid_human_id(member.user.id)]
