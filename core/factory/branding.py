"""The credit line user-created bots carry: every bot made with the factory advertises it."""

from __future__ import annotations

from core.i18n import Translate
from core.sdk.context import BotContext


def factory_link(ctx: BotContext) -> str | None:
    """Deep link into the factory that attributes the visit to this bot (``start=from_c<bot id>``)."""
    if ctx.child is None or not ctx.child.factory_username:
        return None
    return f"https://t.me/{ctx.child.factory_username}?start=from_c{ctx.bot_id}"


def credit(ctx: BotContext, t: Translate) -> str:
    """'\\n\\n🤖 Made with @factory …' for user-created bots that keep branding on; '' otherwise."""
    if ctx.child is None or not ctx.child.branding or not ctx.child.factory_username:
        return ""
    return "\n\n" + t("factory-credit", factory=ctx.child.factory_username)
