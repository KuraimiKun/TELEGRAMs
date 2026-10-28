"""One current command policy for direct, connected, alias, review and content paths."""

from __future__ import annotations

from bots.groupguard import authz, command_metadata, perms
from bots.groupguard.contracts import Actor
from core.sdk.context import BotContext


async def allowed(ctx: BotContext, name: str, chat_id: int, actor: Actor) -> bool:
    if not await authz.active_namespace(ctx) or actor.bot_id != ctx.bot_id:
        return False
    cfg = await ctx.extras["guard"].config(chat_id, fresh=True)
    canonical = command_metadata.purpose(name)
    disabled = {command_metadata.purpose(value) for value in cfg.disabled_commands}
    if canonical not in disabled or canonical in command_metadata.RECOVERY:
        return True
    if cfg.disable_admin:
        return False
    if actor.kind == "anonymous_group" and actor.source_chat_id == chat_id:
        return True
    user_id = (
        actor.human_id if actor.kind == "human" else actor.bot_sender_id if actor.kind == "bot" else None
    )
    if user_id is None:
        return False
    actual = await perms.fresh_rights(ctx, chat_id, user_id)
    return actual is not None and actual.is_admin
