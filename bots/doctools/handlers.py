"""File baskets, contextual actions, group counters and inline citations."""

from __future__ import annotations

import contextlib
import hashlib
from pathlib import PurePath
from typing import Literal

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultsButton,
    InputTextMessageContent,
    Message,
)
from aiogram.types.inline_query_result_union import InlineQueryResultUnion

from bots.doctools.citations import (
    CitationError,
    CitationService,
    bounded_citation,
    format_citations,
    plain_citation,
)
from bots.doctools.operations import DocumentError
from bots.doctools.queue import Basket, DocAsset
from bots.doctools.service import DocToolsService, supported_actions
from core.db.models import BotUser
from core.i18n import Translate
from core.routers.forcesub import require_subscription
from core.sdk.actions import record_user_action
from core.sdk.context import BotContext
from core.ui.text import esc

PARAMETERS = {
    "split": "ranges", "extract": "ranges", "rotate": "angle", "watermark": "watermark",
    "encrypt": "password", "decrypt": "password",
}


class DtCb(CallbackData, prefix="dt"):
    action: str
    owner: int
    stamp: int


class Options(StatesGroup):
    value = State()


def asset_from_message(message: Message) -> DocAsset | None:
    if message.photo:
        photo = message.photo[-1]
        return DocAsset(message_id=message.message_id, file_id=photo.file_id, file_name="photo.jpg", kind="image", size_bytes=photo.file_size or 0)
    if message.document:
        doc = message.document
        filename = PurePath(doc.file_name or "document").name
        suffix = PurePath(filename).suffix.lower()
        kind: Literal["pdf", "image", "docx", "text"] | None = None
        if suffix == ".pdf" or doc.mime_type == "application/pdf":
            kind = "pdf"
        elif suffix == ".docx":
            kind = "docx"
        elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}:
            kind = "image"
        elif suffix == ".txt" or doc.mime_type == "text/plain":
            kind = "text"
        if kind:
            return DocAsset(message_id=message.message_id, file_id=doc.file_id, file_name=filename, kind=kind, size_bytes=doc.file_size or 0)
    if message.text and not message.text.startswith("/"):
        return DocAsset(message_id=message.message_id, kind="text", file_name="assignment.txt", text=message.text)
    return None


def action_keyboard(ctx: BotContext, basket: Basket, t: Translate) -> InlineKeyboardMarkup:
    actions = supported_actions(basket)
    if ctx.ai is None:
        actions = [action for action in actions if action not in {"summarize", "quiz"}]
    buttons = [InlineKeyboardButton(text=t(f"dt-action-{action}"),
                                   callback_data=DtCb(action=action, owner=basket.user_id,
                                                      stamp=basket.callback_stamp).pack()) for action in actions]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton(text=t("dt-clear"),
                                     callback_data=DtCb(action="clear", owner=basket.user_id,
                                                        stamp=basket.callback_stamp).pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def enqueue_action(ctx: BotContext, user: BotUser, chat_id: int, operation: str, *,
                         options: dict | None = None, reply_to: int | None = None, gate: bool = True) -> bool:
    t = ctx.translator.bind(user.lang)
    if gate and not await require_subscription(ctx, user, chat_id, t,
                                               payload={"operation": operation, "options": options or {},
                                                        "reply_to": reply_to}, reply_to=reply_to):
        return False
    service: DocToolsService = ctx.extras["doctools"]
    try:
        await service.submit(user.user_id, chat_id, operation, options=options, lang=user.lang or "en",
                             reply_to=reply_to)
    except DocumentError as e:
        await ctx.bot.send_message(chat_id, t(f"dt-error-{e.code}"))
        return False
    await ctx.bot.send_message(chat_id, t("dt-queued"))
    return True


def build_router(ctx: BotContext) -> Router:
    router = Router(name=f"doctools_{ctx.slug}")
    service: DocToolsService = ctx.extras["doctools"]
    citations: CitationService = ctx.extras["citations"]

    async def show_basket(message: Message, basket: Basket, t: Translate) -> None:
        names = "\n".join(f"{i}. {bounded_citation(esc(asset.file_name[:80]), 150)}" for i, asset in enumerate(basket.assets[:12], 1))
        if len(basket.assets) > 12:
            names += f"\n… +{len(basket.assets) - 12}"
        await message.answer(t("dt-basket", count=len(basket.assets), files=names),
                             reply_markup=action_keyboard(ctx, basket, t))

    @router.message(CommandStart())
    @router.message(Command("help"))
    async def start(message: Message, state: FSMContext, t: Translate) -> None:
        await state.clear()
        await message.answer(t("dt-help", bot=esc(ctx.username)))

    @router.message(Command("tools", "basket"), F.chat.type == "private")
    async def tools(message: Message, user: BotUser, state: FSMContext, t: Translate) -> None:
        await state.clear()
        basket = await service.basket(user.user_id, message.chat.id)
        if basket:
            await show_basket(message, basket, t)
        else:
            await message.answer(t("dt-empty"))

    @router.message(Command("clear", "cancel"), F.chat.type == "private")
    async def clear(message: Message, user: BotUser, state: FSMContext, t: Translate) -> None:
        await state.clear()
        await service.clear_basket(user.user_id, message.chat.id)
        await message.answer(t("dt-cleared"))

    @router.message(Command("cite"))
    async def cite(message: Message, command: CommandObject, user: BotUser, t: Translate) -> None:
        if message.chat.type != "private" and not (await ctx.settings.get()).groups_enabled:
            return
        if not command.args:
            await message.reply(t("dt-cite-help"))
            return
        try:
            ref = await citations.lookup(command.args)
        except CitationError:
            await message.reply(t("dt-cite-error"))
            return
        await message.reply(t("dt-cite-title", title=esc(ref.title[:150])))
        for style, text in format_citations(ref).items():
            if len(text) > 3900:
                await message.answer_document(BufferedInputFile(plain_citation(text).encode("utf-8"),
                                               filename=f"citation-{style.lower()}.txt"), caption=style)
            else:
                await message.reply(f"<b>{style}</b>\n{text}", parse_mode="HTML")
        await record_user_action(ctx, user.user_id)

    @router.inline_query()
    async def inline(query: InlineQuery, t: Translate) -> None:
        value = query.query.strip()
        if value.lower().startswith("cite "):
            value = value[5:].strip()
        try:
            ref = await citations.lookup(value)
        except CitationError:
            await query.answer([], is_personal=True, cache_time=5,
                               button=InlineQueryResultsButton(text=t("dt-cite-help")[:64], start_parameter="cite"))
            return
        articles: list[InlineQueryResultUnion] = [InlineQueryResultArticle(
            id=hashlib.sha256(f"{value}:{style}".encode()).hexdigest()[:24],
            title=f"{style} · {ref.title}"[:150], description=text.replace("<i>", "").replace("</i>", "")[:200],
            input_message_content=InputTextMessageContent(message_text=f"<b>{style}</b>\n{bounded_citation(text)}", parse_mode="HTML"),
        ) for style, text in format_citations(ref).items()]
        await query.answer(articles, cache_time=3600, is_personal=True)

    @router.message(Command("count"))
    async def count(message: Message, command: CommandObject, user: BotUser, t: Translate) -> None:
        if message.chat.type != "private" and not (await ctx.settings.get()).groups_enabled:
            return
        source = message.reply_to_message
        asset = (DocAsset(kind="text", file_name="assignment.txt", text=command.args) if command.args
                 else asset_from_message(source) if source else None)
        if asset:
            await service.clear_basket(user.user_id, message.chat.id)
            try:
                await service.add_asset(user.user_id, message.chat.id, asset)
            except DocumentError as e:
                await message.reply(t(f"dt-error-{e.code}"))
                return
        elif not await service.basket(user.user_id, message.chat.id):
            await message.reply(t("dt-count-help"))
            return
        await enqueue_action(ctx, user, message.chat.id, "count", reply_to=message.message_id,
                             gate=message.chat.type == "private")

    @router.callback_query(DtCb.filter())
    async def action(query: CallbackQuery, callback_data: DtCb, user: BotUser, state: FSMContext,
                     t: Translate) -> None:
        if callback_data.owner != user.user_id or not isinstance(query.message, Message):
            await query.answer(t("dt-owner-only"), show_alert=True)
            return
        basket = await service.basket(user.user_id, query.message.chat.id)
        if not basket or basket.callback_stamp != callback_data.stamp:
            await query.answer(t("dt-empty"), show_alert=True)
            return
        operation = callback_data.action
        image_format = {"images_zip": "zip", "images_album": "album"}.get(operation)
        if image_format:
            operation = "images"
        if operation == "clear":
            await state.clear()
            await service.clear_basket(user.user_id, query.message.chat.id)
            await query.answer(t("dt-cleared"))
            with contextlib.suppress(TelegramBadRequest):
                await query.message.edit_text(t("dt-cleared"))
            return
        if operation not in supported_actions(basket):
            await query.answer(t("dt-error-invalid"), show_alert=True)
            return
        if operation == "images" and image_format is None:
            await query.answer()
            await query.message.answer(t("dt-images-format"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=t("dt-images-zip"), callback_data=DtCb(action="images_zip", owner=user.user_id,
                                    stamp=basket.callback_stamp).pack()),
                InlineKeyboardButton(text=t("dt-images-album"), callback_data=DtCb(action="images_album", owner=user.user_id,
                                    stamp=basket.callback_stamp).pack()),
            ]]))
            return
        if operation in PARAMETERS:
            await state.set_state(Options.value)
            await state.set_data({"operation": operation, "stamp": callback_data.stamp})
            await query.answer()
            await query.message.answer(t(f"dt-ask-{operation}"))
            return
        await state.clear()
        await query.answer()
        await enqueue_action(ctx, user, query.message.chat.id, operation,
                             options={"format": image_format} if image_format else None)

    @router.message(Options.value, F.chat.type == "private", F.text)
    async def option(message: Message, user: BotUser, state: FSMContext, t: Translate) -> None:
        data = await state.get_data()
        basket = await service.basket(user.user_id, message.chat.id)
        if not basket or basket.callback_stamp != data.get("stamp"):
            await state.clear()
            await message.answer(t("dt-empty"))
            return
        operation = str(data.get("operation", ""))
        value = (message.text or "").strip()
        if operation not in PARAMETERS:
            await state.clear()
            return
        if not value or len(value) > 200:
            await message.answer(t("dt-error-invalid"))
            return
        parsed: str | int = value
        if operation == "rotate":
            if value not in {"90", "180", "270"}:
                await message.answer(t("dt-ask-rotate"))
                return
            parsed = int(value)
        elif operation in {"encrypt", "decrypt"} and len(value.encode("utf-8")) > 127:
            await message.answer(t("dt-error-password"))
            return
        await state.clear()
        await enqueue_action(ctx, user, message.chat.id, operation, options={PARAMETERS[operation]: parsed})

    @router.message(F.chat.type == "private", F.document | F.photo | F.text)
    async def collect(message: Message, user: BotUser, t: Translate) -> None:
        if message.text and message.text.startswith("/"):
            return
        asset = asset_from_message(message)
        if asset is None:
            await message.answer(t("dt-error-invalid"))
            return
        try:
            basket = await service.add_asset(user.user_id, message.chat.id, asset)
        except DocumentError as e:
            await message.answer(t(f"dt-error-{e.code}"))
            return
        await show_basket(message, basket, t)

    return router
