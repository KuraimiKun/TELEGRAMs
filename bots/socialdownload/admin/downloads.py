"""SocialDownload admin tab: queue health, dead letters, proxies and cookie files."""

from __future__ import annotations

import io
import json
import re

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bots.socialdownload.engine.network import MAX_COOKIE_BYTES, CookieJar, ProxyPool, mask_proxy
from bots.socialdownload.engine.queue import JobQueue
from core.callback_data import AdminNavCb
from core.i18n import Translate
from core.routers.admin.common import actor, admin_router, back_row, btn, markup, nav, show
from core.sdk.context import BotContext
from core.ui.text import esc

TAB = "downloads"
COOKIE_PLATFORMS = ("instagram", "youtube", "tiktok", "facebook", "twitter", "reddit", "pinterest", "threads", "vk")


class DlAdminCb(CallbackData, prefix="sd_adm"):
    action: str  # queue | purge | proxies | proxy_add | proxy_del | proxy_reset | cookies | cookie_del
    arg: int = 0


class DlAdminStates(StatesGroup):
    proxy = State()


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "sd_downloads")
    queue: JobQueue = ctx.extras["queue"]
    proxies: ProxyPool = ctx.extras["proxies"]
    cookies: CookieJar = ctx.extras["cookies"]

    def cb(action: str, arg: int = 0) -> str:
        return DlAdminCb(action=action, arg=arg).pack()

    @router.callback_query(AdminNavCb.filter(F.tab == TAB))
    async def home(query: CallbackQuery, t: Translate) -> None:
        d = await queue.depth()
        text = t(
            "sd-adm-home",
            high=d["high"],
            normal=d["normal"],
            running=d["inflight"],
            dead=d["dead"],
            proxies=len(proxies.all()),
            cookies=sum(cookies.summary().values()),
        )
        await show(
            query,
            text,
            markup(
                [btn(t("sd-btn-dead"), cb("queue")), btn(t("sd-btn-proxies"), cb("proxies"))],
                [btn(t("sd-btn-cookies"), cb("cookies")), nav(TAB, t("btn-adm-refresh"))],
                back_row(t),
            ),
        )

    # ------------------------------------------------------------------ dead letters
    @router.callback_query(DlAdminCb.filter(F.action == "queue"))
    async def dead_letters(query: CallbackQuery, t: Translate) -> None:
        lines = []
        for raw in await queue.dead_jobs(10):
            try:
                entry = json.loads(raw)
                job = entry.get("job", {})
                lines.append(f"• <code>{esc(job.get('id'))}</code> {esc(job.get('platform'))} — {esc(entry.get('reason'))}")
            except ValueError:
                continue
        text = t("sd-adm-dead") + "\n\n" + ("\n".join(lines) if lines else t("adm-list-empty"))
        await show(query, text, markup([btn(t("sd-btn-purge"), cb("purge"))], back_row(t, TAB)))

    @router.callback_query(DlAdminCb.filter(F.action == "purge"))
    async def purge(query: CallbackQuery, t: Translate) -> None:
        n = await queue.purge_dead()
        await ctx.audit.record(actor(query), "downloads.purge_dead", count=n)
        await dead_letters(query, t)

    # ------------------------------------------------------------------ proxies
    @router.callback_query(DlAdminCb.filter(F.action == "proxies"))
    async def proxies_view(query: CallbackQuery, t: Translate) -> None:
        health = await proxies.health()
        rows = [
            [btn(f"🗑 {masked[:40]} · ⚠️{fails}", cb("proxy_del", i))]
            for i, (masked, fails) in enumerate(health)
        ]
        await show(
            query,
            t("sd-adm-proxies", count=len(health)),
            markup(
                *rows,
                [btn(t("sd-btn-proxy-add"), cb("proxy_add")), btn(t("sd-btn-proxy-reset"), cb("proxy_reset"))],
                back_row(t, TAB),
            ),
        )

    @router.callback_query(DlAdminCb.filter(F.action == "proxy_add"))
    async def proxy_prompt(query: CallbackQuery, state: FSMContext, t: Translate) -> None:
        await state.set_state(DlAdminStates.proxy)
        await show(query, t("sd-adm-proxy-prompt"), markup(back_row(t, TAB)))

    @router.message(DlAdminStates.proxy, F.text)
    async def proxy_add(message: Message, state: FSMContext, t: Translate) -> None:
        value = (message.text or "").strip()
        if not proxies.add(value):
            await message.answer(t("sd-adm-proxy-invalid"), reply_markup=markup(back_row(t, TAB)))
            return
        await state.clear()
        await ctx.audit.record(actor(message), "downloads.proxy_add", mask_proxy(value))
        with_creds = re.sub(r"//[^@/]+@", "//***@", value)
        await message.answer(t("adm-setting-saved", key="proxy", value=esc(with_creds)), reply_markup=markup(back_row(t, TAB)))

    @router.callback_query(DlAdminCb.filter(F.action.in_({"proxy_del", "proxy_reset"})))
    async def proxy_change(query: CallbackQuery, callback_data: DlAdminCb, t: Translate) -> None:
        if callback_data.action == "proxy_reset":
            await proxies.reset()
            await ctx.audit.record(actor(query), "downloads.proxy_reset")
        elif proxies.remove(callback_data.arg):
            await ctx.audit.record(actor(query), "downloads.proxy_remove", callback_data.arg)
        else:
            await query.answer(t("sd-adm-proxy-readonly"), show_alert=True)
        await proxies_view(query, t)

    # ------------------------------------------------------------------ cookies
    @router.callback_query(DlAdminCb.filter(F.action == "cookies"))
    async def cookies_view(query: CallbackQuery, t: Translate) -> None:
        files = cookies.listing()
        rows = [[btn(f"🗑 {f.name[:48]}", cb("cookie_del", i))] for i, f in enumerate(files) if f.suffix == ".txt"]
        await show(
            query,
            t("sd-adm-cookies", count=len(rows), platforms=", ".join(COOKIE_PLATFORMS)),
            markup(*rows, back_row(t, TAB)),
        )

    @router.callback_query(DlAdminCb.filter(F.action == "cookie_del"))
    async def cookie_delete(query: CallbackQuery, callback_data: DlAdminCb, t: Translate) -> None:
        files = cookies.listing()
        if 0 <= callback_data.arg < len(files) and cookies.delete(files[callback_data.arg].name):
            await ctx.audit.record(actor(query), "downloads.cookie_delete", files[callback_data.arg].name)
        await cookies_view(query, t)

    @router.message(F.document, F.caption.lower().strip().in_(COOKIE_PLATFORMS))
    async def cookie_upload(message: Message, t: Translate) -> None:
        platform = (message.caption or "").strip().lower()
        doc = message.document
        if not doc or (doc.file_size or 0) > MAX_COOKIE_BYTES:
            await message.answer(t("sd-adm-cookie-invalid", error="max 1 MB"))
            return
        buf = io.BytesIO()
        await ctx.bot.download(doc, destination=buf)
        try:
            saved = cookies.save(platform, buf.getvalue())
        except ValueError as e:
            await message.answer(t("sd-adm-cookie-invalid", error=esc(e)))
            return
        await ctx.audit.record(actor(message), "downloads.cookie_upload", saved.name)
        await message.answer(t("sd-adm-cookie-saved", platform=esc(platform), name=esc(saved.name)))

    return router
