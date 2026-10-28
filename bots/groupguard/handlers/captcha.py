"""CAPTCHA settings through the common fresh authorization and review contract."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bots.groupguard import actions, perms
from bots.groupguard.handlers.content import config_operation
from bots.groupguard.handlers.tools import boolean
from bots.groupguard.scope import GroupMessages, target_chat
from core.sdk.context import BotContext


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_captcha_settings")
    router.message.filter(GroupMessages())
    svc = ctx.extras["guard"]

    @router.message(Command("captcha", "captchamode", "setcaptchatext", "resetcaptchatext", "captchakick",
        "captchakicktime", "captcharules", "captchamutetime"))
    async def settings(message: Message, command: CommandObject):
        cfg = await svc.config(target_chat(message).id, fresh=True)
        t = actions.group_t(ctx, cfg)
        args = (command.args or "").strip()
        name = command.command
        patch: dict = {}
        if not args and name != "resetcaptchatext":
            await message.reply(t("gg-captcha-settings", mode=t(f"gg-val-{cfg.captcha}"), enabled=t("gg-on") if cfg.effective_captcha() != "off" else t("gg-off"),
                kick=t("gg-on") if cfg.captcha_kick else t("gg-off"), seconds=str(cfg.verification_seconds()),
                release=str(cfg.captcha_mute_seconds) if cfg.captcha_mute_seconds else t("gg-off")))
            return
        if name in {"captcha", "captchakick", "captcharules"}:
            value = boolean(args.lower())
            if value is not None:
                key = {"captcha": "captcha_enabled", "captchakick": "captcha_kick", "captcharules": "captcha_rules"}[name]
                if (name == "captcha" and value and not cfg.welcome) or (name == "captcharules" and value and not cfg.rules):
                    await message.reply(t("gg-captcha-dependency"))
                    return
                patch = {key: value}
                if name == "captcha" and value and cfg.captcha == "off":
                    patch["captcha"] = "button"
        elif name == "captchamode" and args.lower() in {"button", "text", "math", "text2"}:
            patch = {"captcha": args.lower()}
        elif name == "resetcaptchatext":
            patch = {"captcha_text": ""}
        elif name == "setcaptchatext" and 0 < len(args.encode("utf-16-le")) // 2 <= 128 and not any(ord(c) < 32 for c in args):
            patch = {"captcha_text": args}
        elif name in {"captchakicktime", "captchamutetime"}:
            duration = perms.parse_duration(args.lower())
            low = 300 if name == "captchakicktime" else 60
            if name == "captchamutetime" and args.lower() in {"off", "no", "false"}:
                patch = {"captcha_mute_seconds": None}
            elif duration is not None and low <= duration.total_seconds() <= 86400:
                patch = {"captcha_kick_seconds" if name == "captchakicktime" else "captcha_mute_seconds": int(duration.total_seconds())}
        if not patch:
            await message.reply(t("gg-setting-invalid"))
            return
        await config_operation(ctx, message, patch, "gg-setting-saved", setting=name)

    return router
