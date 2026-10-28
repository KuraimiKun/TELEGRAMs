"""Visitors browse the pages; the owner edits them live with /build."""

from __future__ import annotations

import io
import json

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bots.custombot.models import CbNode
from bots.custombot.render import PageCb, open_page, send_page
from bots.custombot.service import BuilderError, PageService
from bots.custombot.settings import CustomSettings
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.respond import show
from core.ui.text import esc

MEDIA = ("photo", "video", "animation", "document", "audio", "voice", "sticker", "video_note")
MAX_IMPORT_BYTES = 512 * 1024


class BuildCb(CallbackData, prefix="cbb"):
    # open | add | link | content | rename | command | nocmd | delete | delete_ok | export | import | up | preview
    action: str
    id: int = 0


class Build(StatesGroup):
    title = State()
    url = State()
    content = State()
    command = State()
    import_file = State()


def build_router(ctx: BotContext) -> Router:
    router = Router(name="custombot")
    router.message.filter(F.chat.type == "private")
    svc: PageService = ctx.extras["pages"]

    def b(text: str, action: str, node_id: int = 0) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=text, callback_data=BuildCb(action=action, id=node_id).pack())

    def is_owner(user_id: int) -> bool:
        return ctx.is_admin(user_id)

    async def builder_view(node: CbNode, t: Translate) -> tuple[str, InlineKeyboardMarkup]:
        kids = await svc.children(node.id)
        preview = (node.text or "").strip()
        lines = [
            t("cb-builder", title=esc(node.title), command=f"/{node.command}" if node.command else "—",
              buttons=str(len(kids)), pages=str(await svc.count())),
        ]
        if node.media_kind:
            lines.append(t("cb-has-media", kind=node.media_kind))
        if preview:
            lines.append(f"\n<blockquote>{esc(preview[:400])}</blockquote>")
        rows = []
        for kid in kids:
            icon = "🔗" if kid.url else "📄"
            rows.append([b(f"{icon} {kid.title}", "open", kid.id)])
        rows.append([b(t("cb-btn-add-page"), "add", node.id), b(t("cb-btn-add-link"), "link", node.id)])
        rows.append([b(t("cb-btn-content"), "content", node.id), b(t("cb-btn-command"), "command", node.id)])
        if node.parent_id is not None:
            rows.append([b(t("cb-btn-rename"), "rename", node.id), b(t("cb-btn-delete"), "delete", node.id)])
            rows.append([b(t("cb-btn-up"), "open", node.parent_id), b(t("cb-btn-preview"), "preview", node.id)])
        else:
            rows.append([b(t("cb-btn-export"), "export"), b(t("cb-btn-import"), "import")])
            rows.append([b(t("cb-btn-preview"), "preview", node.id)])
        return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)

    def link_view(node: CbNode, t: Translate) -> tuple[str, InlineKeyboardMarkup]:
        rows = [[b(t("cb-btn-rename"), "rename", node.id), b(t("cb-btn-delete"), "delete", node.id)]]
        rows.append([b(t("cb-btn-up"), "open", node.parent_id or 0)])
        return t("cb-link", title=esc(node.title), url=esc(node.url or "")), InlineKeyboardMarkup(inline_keyboard=rows)

    async def show_node(target: Message | CallbackQuery, node: CbNode, t: Translate) -> None:
        text, kb = link_view(node, t) if node.url else await builder_view(node, t)
        if isinstance(target, CallbackQuery):
            await show(target, text, kb)
        else:
            await target.answer(text, reply_markup=kb)

    # ------------------------------------------------------------------ visitors
    @router.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext, t: Translate) -> None:
        await state.clear()
        await send_page(ctx, svc, message.chat.id, await svc.root(), t)
        if message.from_user and is_owner(message.from_user.id) and not (await svc.children((await svc.root()).id)):
            await message.answer(t("cb-owner-tip"))

    @router.callback_query(PageCb.filter())
    async def cb_page(query: CallbackQuery, callback_data: PageCb, t: Translate) -> None:
        node = await svc.get(callback_data.id)
        if node is None:
            await query.answer(t("cb-page-gone"), show_alert=True)
            return
        await open_page(ctx, svc, query, node, t)

    # ------------------------------------------------------------------ builder
    @router.message(Command("build"))
    async def cmd_build(message: Message, state: FSMContext, t: Translate) -> None:
        if message.from_user is None or not is_owner(message.from_user.id):
            return
        await state.clear()
        await show_node(message, await svc.root(), t)

    @router.callback_query(BuildCb.filter())
    async def cb_build(query: CallbackQuery, callback_data: BuildCb, state: FSMContext, t: Translate) -> None:
        if not is_owner(query.from_user.id):
            await query.answer()
            return
        action = callback_data.action
        node = await svc.get(callback_data.id) if callback_data.id else await svc.root()
        if node is None:
            await query.answer(t("cb-page-gone"), show_alert=True)
            return
        if action == "open":
            await state.clear()
            await show_node(query, node, t)
        elif action in ("add", "link", "rename"):
            await state.set_state(Build.title)
            await state.update_data(mode=action, node=node.id)
            await show(query, t(f"cb-ask-title-{action}"), cancel_kb(node.id, t))
        elif action == "content":
            await state.set_state(Build.content)
            await state.update_data(node=node.id)
            await show(query, t("cb-ask-content"), cancel_kb(node.id, t))
        elif action == "command":
            await state.set_state(Build.command)
            await state.update_data(node=node.id)
            kb = InlineKeyboardMarkup(inline_keyboard=[[b(t("cb-btn-no-command"), "nocmd", node.id)],
                                                       [b(t("btn-cancel"), "open", node.id)]])
            await show(query, t("cb-ask-command"), kb)
        elif action == "nocmd":
            await state.clear()
            await svc.set_command(node.id, None if node.parent_id is not None else "start")
            await show_node(query, (await svc.get(node.id)) or node, t)
        elif action == "delete":
            kb = InlineKeyboardMarkup(inline_keyboard=[[b(t("cb-btn-delete-ok"), "delete_ok", node.id)],
                                                       [b(t("btn-cancel"), "open", node.id)]])
            await show(query, t("cb-confirm-delete", title=esc(node.title)), kb)
        elif action == "delete_ok":
            parent = node.parent_id
            await svc.delete(node.id)
            await ctx.audit.record(query.from_user.id, "custom.page_delete", node.id)
            target = await svc.get(parent) if parent else None
            await show_node(query, target or await svc.root(), t)
        elif action == "preview":
            await query.answer()
            await send_page(ctx, svc, query.from_user.id, node, t)
        elif action == "export":
            data = json.dumps(await svc.export(), ensure_ascii=False, indent=2).encode()
            await query.answer()
            await ctx.bot.send_document(query.from_user.id, BufferedInputFile(data, f"{ctx.username}-pages.json"),
                                        caption=t("cb-exported"))
        elif action == "import":
            await state.set_state(Build.import_file)
            await show(query, t("cb-ask-import"), cancel_kb(node.id, t))

    def cancel_kb(node_id: int, t: Translate) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[[b(t("btn-cancel"), "open", node_id)]])

    async def owner_state(message: Message) -> bool:
        return message.from_user is not None and is_owner(message.from_user.id)

    @router.message(Build.title, F.text)
    async def on_title(message: Message, state: FSMContext, t: Translate) -> None:
        if not await owner_state(message):
            return
        data = await state.get_data()
        node = await svc.get(int(data["node"]))
        if node is None:
            await state.clear()
            return
        title = (message.text or "").strip()
        try:
            if data["mode"] == "rename":
                if not title:
                    raise BuilderError("title")
                await svc.update(node.id, title=title[:64])
                await state.clear()
                await show_node(message, (await svc.get(node.id)) or node, t)
            elif data["mode"] == "link":
                await state.set_state(Build.url)
                await state.update_data(title=title[:64])
                await message.answer(t("cb-ask-url"), reply_markup=cancel_kb(node.id, t))
            else:
                child = await svc.add_child(node.id, title)
                await state.clear()
                await message.answer(t("cb-page-added", title=esc(child.title)))
                await show_node(message, child, t)
        except BuilderError as e:
            await message.answer(t(f"cb-err-{e.code}"))

    @router.message(Build.url, F.text)
    async def on_url(message: Message, state: FSMContext, t: Translate) -> None:
        if not await owner_state(message):
            return
        data = await state.get_data()
        try:
            await svc.add_child(int(data["node"]), str(data["title"]), url=(message.text or "").strip())
        except BuilderError as e:
            await message.answer(t(f"cb-err-{e.code}"))
            return
        await state.clear()
        parent = await svc.get(int(data["node"]))
        if parent is not None:
            await show_node(message, parent, t)

    @router.message(Build.command, F.text)
    async def on_command(message: Message, state: FSMContext, t: Translate) -> None:
        if not await owner_state(message):
            return
        data = await state.get_data()
        try:
            await svc.set_command(int(data["node"]), message.text or "")
        except BuilderError as e:
            await message.answer(t(f"cb-err-{e.code}"))
            return
        await state.clear()
        node = await svc.get(int(data["node"]))
        if node is not None:
            await show_node(message, node, t)

    @router.message(Build.content)
    async def on_content(message: Message, state: FSMContext, t: Translate) -> None:
        if not await owner_state(message):
            return
        data = await state.get_data()
        media_kind, file_id = None, None
        if message.photo:
            media_kind, file_id = "photo", message.photo[-1].file_id
        else:
            for kind in MEDIA[1:]:
                obj = getattr(message, kind, None)
                if obj is not None:
                    media_kind, file_id = kind, obj.file_id
                    break
        text = message.html_text if (message.text or message.caption) else None
        await svc.update(int(data["node"]), text=text, media_kind=media_kind, file_id=file_id)
        await state.clear()
        node = await svc.get(int(data["node"]))
        await message.answer(t("cb-content-saved"))
        if node is not None:
            await show_node(message, node, t)

    @router.message(Build.import_file, F.document)
    async def on_import(message: Message, state: FSMContext, t: Translate) -> None:
        if not await owner_state(message) or message.document is None:
            return
        if (message.document.file_size or 0) > MAX_IMPORT_BYTES:
            await message.answer(t("cb-err-import"))
            return
        buf = io.BytesIO()
        await ctx.bot.download(message.document, destination=buf)
        try:
            count = await svc.import_(json.loads(buf.getvalue().decode("utf-8")))
        except (ValueError, BuilderError, UnicodeDecodeError):
            await message.answer(t("cb-err-import"))
            return
        await state.clear()
        await ctx.audit.record(message.from_user.id if message.from_user else 0, "custom.import", count=count)
        await message.answer(t("cb-imported", count=str(count)))
        await show_node(message, await svc.root(), t)

    # ------------------------------------------------------------------ commands & fallback (must stay last)
    @router.message(F.text.startswith("/"))
    async def on_command_page(message: Message, t: Translate) -> None:
        command = (message.text or "/").split()[0][1:].split("@")[0].lower()
        node = await svc.by_command(command)
        if node is not None:
            await send_page(ctx, svc, message.chat.id, node, t)

    @router.message()
    async def fallback(message: Message, t: Translate) -> None:
        stg = await ctx.settings.get()
        assert isinstance(stg, CustomSettings)
        if stg.default_reply:
            await message.answer(stg.default_reply)
        elif stg.show_menu_on_unknown:
            await send_page(ctx, svc, message.chat.id, await svc.root(), t)

    return router
