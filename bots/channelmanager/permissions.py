"""Live Telegram checks. Stored roles are discovery hints, never proof of authority."""

from __future__ import annotations

from typing import Any

from aiogram.exceptions import TelegramAPIError
from aiogram.types import ChatMemberUnion
from sqlalchemy import select

from bots.channelmanager.models import Channel, VirtualGrant
from core.sdk.context import BotContext

RIGHTS = ("can_post_messages", "can_edit_messages", "can_delete_messages", "can_invite_users", "can_restrict_members")


class AccessDenied(Exception):
    pass


def rights_of(member: ChatMemberUnion) -> dict[str, bool]:
    return {name: member.status == "creator" or bool(getattr(member, name, False)) for name in RIGHTS}


async def operator_rights(ctx: BotContext, channel_id: int, user_id: int) -> dict[str, bool]:
    try:
        member = await ctx.bot.get_chat_member(channel_id, user_id)
    except TelegramAPIError as exc:
        raise AccessDenied("membership_unavailable") from exc
    if member.status not in {"creator", "administrator"}:
        raise AccessDenied("not_channel_admin")
    rights = rights_of(member)
    if not rights["can_post_messages"]:
        raise AccessDenied("cannot_post")
    return rights


async def publishing_access(ctx: BotContext, channel_id: int, user_id: int, *, action="view") -> dict[str, Any]:
    try:
        rights: dict[str, Any] = dict(await operator_rights(ctx, channel_id, user_id))
        if action == "settings" and not rights["can_edit_messages"]:
            raise AccessDenied("settings_right")
        return {**rights, "_virtual": False, "_grant_generation": None}
    except AccessDenied:
        pass
    async with ctx.sm() as session:
        grant = await session.get(VirtualGrant, (ctx.bot_id, channel_id, user_id))
        if grant is None or not grant.active:
            raise AccessDenied("delegation_unavailable")
        from bots.channelmanager.growth_specs import DelegateSpec
        spec = DelegateSpec.model_validate(grant.permissions)
        # Paid quota changes pause excess delegates without deleting grants.
        from bots.channelmanager.billing import limits_for
        limits = await limits_for(ctx, channel_id, session=session)
        allowed = list((await session.scalars(select(VirtualGrant.user_id).where(VirtualGrant.bot_id == ctx.bot_id,
            VirtualGrant.channel_id == channel_id, VirtualGrant.active.is_(True)).order_by(VirtualGrant.created_at, VirtualGrant.user_id)
            .limit(limits.delegates))).all()) if limits.delegates else []
        if user_id not in allowed:
            raise AccessDenied("plan_limit")
    from bots.channelmanager.team import delegated_rights, grantor_rights
    delegated_rights(await grantor_rights(ctx, channel_id, grant.grantor_id), spec)
    if (action in {"create", "publish"} and not spec.create) or (action == "schedule" and not spec.schedules) or (action == "settings" and not spec.settings):
        raise AccessDenied("delegation_permission")
    return {"can_post_messages": spec.create, "can_edit_messages": spec.edit_all, "can_delete_messages": spec.delete_all,
        "can_invite_users": False, "can_restrict_members": False, "_virtual": True, "_grant_generation": grant.generation,
        "_permissions": spec.model_dump()}


async def post_rights(ctx: BotContext, channel_id: int, user_id: int, creator_id: int, action: str) -> dict[str, Any]:
    rights = await publishing_access(ctx, channel_id, user_id, action=action if action in {"publish", "create", "schedule", "settings"} else "view")
    if rights["_virtual"]:
        spec = rights["_permissions"]
        own = user_id == creator_id
        if action == "view":
            allowed = own or spec["edit_all"] or spec["delete_all"]
        elif action == "delete":
            allowed = spec["delete_all"] or (own and spec["delete_own"])
        elif action in {"publish", "create"}:
            allowed = spec["create"] and (own or spec["edit_all"])
        else:
            allowed = spec["edit_all"] or (own and spec["edit_own"])
        if not allowed:
            raise AccessDenied("delegation_permission")
        return rights
    if user_id != creator_id:
        required = "can_delete_messages" if action == "delete" else "can_edit_messages"
        if action == "view":
            if not (rights["can_edit_messages"] or rights["can_delete_messages"]):
                raise AccessDenied("other_post")
        elif not rights[required]:
            raise AccessDenied("other_post")
    return rights


async def bot_post_rights(ctx: BotContext, channel_id: int, action: str) -> None:
    async with ctx.sm() as session:
        channel = await session.get(Channel, (ctx.bot_id, channel_id))
        if channel is None or channel.status == "disconnected" or (action != "delete" and channel.status != "active"):
            raise AccessDenied("channel_inactive")
    try:
        member = await ctx.bot.get_chat_member(channel_id, ctx.bot_id)
    except TelegramAPIError as exc:
        raise AccessDenied("bot_unavailable") from exc
    rights = rights_of(member)
    if member.status != "administrator":
        raise AccessDenied("bot_not_admin")
    required = "can_edit_messages" if action in {"edit", "pin", "markup"} else "can_post_messages"
    if action == "delete":
        if not (rights["can_delete_messages"] or rights["can_post_messages"]):
            raise AccessDenied("bot_cannot_delete")
    elif not rights[required]:
        raise AccessDenied("bot_missing_right")
