"""Shared greeting envelopes and owned five-minute old-welcome cleanup."""
from __future__ import annotations

from bots.groupguard import actions, delivery, repeats
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.delivery import Content, Delivered
from bots.groupguard.formatting import render
from core.factory.branding import credit
from core.sdk.context import BotContext


def content(ctx: BotContext, cfg: ChatConfig, kind: str) -> Content:
    t = actions.group_t(ctx, cfg)
    saved = cfg.welcome_content if kind == "welcome" else cfg.goodbye_content
    if saved is not None:
        return Content.from_dict(saved)
    return Content(cfg.welcome_text or t("gg-welcome-default") if kind == "welcome" else t("gg-goodbye", user="{mention}"))


def suffix(ctx: BotContext, cfg: ChatConfig) -> str:
    t = actions.group_t(ctx, cfg)
    return credit(ctx, t) if ctx.child is not None else "\n\n" + t("gg-credit", bot=ctx.username) if cfg.credit else ""


async def remember(ctx: BotContext, chat_id: int, ids: list[int]) -> None:
    if not ids:
        return
    svc = ctx.extras["guard"]
    async with svc.member_session(chat_id, 0) as (session, _member):
        cfg = await svc.config(chat_id, fresh=True)
        if cfg.clean_welcome:
            await repeats.schedule_delete(ctx, chat_id, cfg.welcome_messages, session=session)
        await svc.update_config(chat_id, welcome_messages=list(dict.fromkeys(ids)))


async def send(ctx: BotContext, cfg: ChatConfig, chat_id: int, user, *, title="", kind="welcome",
               thread_id: int | None = None) -> Delivered:
    saved = content(ctx, cfg, kind)
    f = await delivery.fillings(ctx, chat_id, user, chat_name=title or "", raw=saved.raw)
    kb = None
    if kind == "welcome" and cfg.rules and not render(saved.raw, f, format=saved.format, kind=kind).controls.rules:
        kb = await delivery.private_button(ctx, chat_id, kind="rules", label=f.rules_label)
    sent = await delivery.send(ctx, chat_id, saved, f, kind=kind, extra_keyboard=kb,
        suffix=suffix(ctx, cfg) if kind == "welcome" else "",
        thread_id=None if cfg.action_topic in {None, 1} else cfg.action_topic)
    if kind == "welcome" and sent.messages:
        await remember(ctx, chat_id, [msg.message_id for msg in sent.messages])
    return sent
