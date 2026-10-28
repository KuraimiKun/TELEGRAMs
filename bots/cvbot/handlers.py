"""Private CV workflows, score sharing, five-turn mock interviews and Stars purchases."""

from __future__ import annotations

import asyncio
import contextlib
import secrets
from collections.abc import Awaitable
from typing import cast

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from bots.cvbot.extraction import Extracted, ExtractionError, extract
from bots.cvbot.payments import PREFIX, ProReviews
from bots.cvbot.pdf import render_pdf
from bots.cvbot.schemas import Analysis
from bots.cvbot.service import CVService, CVSession
from bots.cvbot.settings import CVSettings
from core.ai.base import AIError, AIUnavailable
from core.db.models import BotUser
from core.files import FileTooLarge, fetch_bytes
from core.i18n import Translate
from core.routers.forcesub import require_subscription
from core.sdk.actions import record_user_action
from core.sdk.context import BotContext
from core.sdk.quota import DailyQuota
from core.ui.cards import Card, render
from core.ui.text import esc


class CVFlow(StatesGroup):
    job = State()
    cover_job = State()
    role = State()
    answer = State()


def analysis_blocks(report: Analysis, t: Translate) -> list[str]:
    """Small complete HTML blocks, so chunking never cuts a Telegram entity or tag."""
    blocks = [t("cv-report-score", score=report.score), t("cv-report-subscores", **report.subscores.model_dump())]
    for title, entries in [
        (t("cv-strengths"), [f"• {esc(x)}" for x in report.strengths]),
        (t("cv-issues"), [f"• <b>{esc(x.issue)}</b>\n{esc(x.fix)}" for x in report.issues]),
        (t("cv-bullets"), [f"• {esc(x.original)}\n→ {esc(x.improved)}" for x in report.rewritten_bullets]),
        (t("cv-missing"), [f"• {esc(x)}" for x in report.missing_sections]),
        (t("cv-roles"), [f"• {esc(x)}" for x in report.suggested_roles]),
    ]:
        if entries:
            blocks.extend([f"<b>{title}</b>", *entries])
    blocks.append(t("cv-source-language", language=esc(report.language)))
    return blocks


async def send_blocks(message: Message, blocks: list[str], markup: InlineKeyboardMarkup | None = None) -> None:
    chunks: list[str] = []
    current = ""
    for block in blocks:
        # Telegram measures text in UTF-16 code units. Counting encoded HTML conservatively also
        # leaves room for markup; the bounded individual blocks fit after entity decoding.
        if current and len((current + "\n\n" + block).encode("utf-16-le")) // 2 > 3800:
            chunks.append(current)
            current = ""
        current += ("\n\n" if current else "") + block
    if current:
        chunks.append(current)
    for index, chunk in enumerate(chunks):
        await message.answer(chunk, reply_markup=markup if index == len(chunks) - 1 else None)


def build_router(ctx: BotContext) -> Router:
    router = Router(name="cvbot_main")
    router.message.filter(F.chat.type == ChatType.PRIVATE)
    service: CVService = ctx.extras["cv"]
    quota: DailyQuota = ctx.extras["cv_quota"]
    pro: ProReviews = ctx.extras["cv_pro"]

    def actions(t: Translate) -> InlineKeyboardMarkup:
        rows = []
        if ctx.ai is not None:
            rows = [
                [InlineKeyboardButton(text=t("cv-btn-match"), callback_data="cv:match"),
                 InlineKeyboardButton(text=t("cv-btn-cover"), callback_data="cv:coverletter")],
                [InlineKeyboardButton(text=t("cv-btn-linkedin"), callback_data="cv:linkedin"),
                 InlineKeyboardButton(text=t("cv-btn-interview"), callback_data="cv:interview")],
                [InlineKeyboardButton(text=t("cv-btn-export"), callback_data="cv:export")],
            ]
        rows.append([InlineKeyboardButton(text=t("cv-btn-share"), callback_data="cv:share")])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    def upgrades(t: Translate) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=t("btn-vip"), callback_data="c_vip:info:0"),
            InlineKeyboardButton(text=t("cv-btn-pro"), callback_data="cv:pro"),
        ]])

    async def privacy(message: Message, user: BotUser, t: Translate) -> None:
        if not (user.prefs or {}).get("cv_privacy_seen"):
            await message.answer(t("cv-privacy"))
            await ctx.users.update_pref(user.user_id, "cv_privacy_seen", True)

    async def source(message: Message, user: BotUser, t: Translate) -> CVSession | None:
        session = await service.current_session(user.user_id)
        if session is None:
            await message.answer(t("cv-session-expired"))
        return session

    async def ai_error(message: Message, error: AIError, t: Translate) -> None:
        await message.answer(t("ai-unavailable") if isinstance(error, AIUnavailable) else t("cv-ai-error"))

    @router.message(CommandStart())
    async def start(message: Message, user: BotUser, state: FSMContext, t: Translate) -> None:
        await state.clear()
        await privacy(message, user, t)
        await message.answer(t("cv-start"))
        if ctx.ai is None:
            await message.answer(t("ai-unavailable"))

    @router.callback_query(F.data == "nav:main")
    async def main(query: CallbackQuery, t: Translate) -> None:
        await query.answer()
        if isinstance(query.message, Message):
            await query.message.answer(t("cv-start"))

    @router.message(Command("help"))
    async def help_message(message: Message, t: Translate) -> None:
        await message.answer(t("cv-help") + "\n\n" + t("cv-privacy"))

    @router.message(Command("analyze"))
    async def request_cv(message: Message, state: FSMContext, user: BotUser, t: Translate) -> None:
        await state.clear()
        await privacy(message, user, t)
        await message.answer(t("cv-start") if ctx.ai is not None else t("ai-unavailable"))

    @router.message(Command("cancel"))
    async def cancel(message: Message, state: FSMContext, t: Translate) -> None:
        await state.clear()
        await message.answer(t("cv-cancelled"))

    @router.message(Command("forget"))
    async def forget(message: Message, state: FSMContext, user: BotUser, t: Translate) -> None:
        await state.clear()
        await service.forget(user.user_id)
        await message.answer(t("cv-forgotten"))

    async def buy_review(message: Message, user: BotUser, t: Translate) -> None:
        if ctx.ai is None or not await ctx.ai.available():
            await message.answer(t("ai-unavailable"))
            return
        settings: CVSettings = await ctx.settings.get()
        payload = await pro.issue(user.user_id, settings.pro_review_stars)
        await message.answer_invoice(
            title=t("cv-invoice-title"), description=t("cv-invoice-desc"), payload=payload.encode(),
            currency="XTR", prices=[LabeledPrice(label=t("cv-invoice-title"), amount=payload.stars)],
        )

    @router.message(Command("pro"))
    async def pro_command(message: Message, user: BotUser, t: Translate) -> None:
        await buy_review(message, user, t)

    @router.pre_checkout_query(F.invoice_payload.startswith(PREFIX))
    async def checkout(query: PreCheckoutQuery) -> None:
        payload = await pro.validate(query.invoice_payload, query.from_user.id, query.currency, query.total_amount)
        await query.answer(ok=payload is not None, error_message=None if payload else "Invalid or expired Pro review invoice")

    @router.message(F.successful_payment.invoice_payload.startswith(PREFIX))
    async def paid(message: Message, t: Translate) -> None:
        payment = message.successful_payment
        if payment is None or message.from_user is None:
            return
        payload = await pro.validate(
            payment.invoice_payload, message.from_user.id, payment.currency, payment.total_amount, checkout=False,
        )
        if payload is not None and await pro.paid(payload, payment.telegram_payment_charge_id):
            await message.answer(t("cv-pro-paid"))

    @router.message(F.refunded_payment.invoice_payload.startswith(PREFIX))
    async def refunded(message: Message, t: Translate) -> None:
        if message.refunded_payment and await ctx.payments.process_refund(message.refunded_payment.telegram_payment_charge_id):
            await message.answer(t("cv-pro-refunded"))

    async def share(message: Message, user: BotUser, t: Translate) -> None:
        report = await service.latest(user.user_id)
        if report is None:
            await message.answer(t("cv-no-report"))
            return
        link = f"https://t.me/{ctx.username}"
        png = await asyncio.to_thread(render, Card(
            headline=t("cv-card-title"), body=t("cv-card-body"), big=str(report.score),
            big_caption=t("cv-card-score"), footer=f"@{ctx.username}", theme="ocean",
        ), "square")
        await message.answer_photo(
            BufferedInputFile(png, filename="cv-score.png"), caption=t("cv-share-caption", score=report.score, link=link),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=t("cv-btn-try"), url=link),
                InlineKeyboardButton(text=t("cv-btn-forward"), switch_inline_query=""),
            ]]),
        )

    @router.message(Command("share"))
    async def share_command(message: Message, user: BotUser, t: Translate) -> None:
        await share(message, user, t)

    @router.inline_query()
    async def inline_share(query: InlineQuery, user: BotUser, t: Translate) -> None:
        report = await service.latest(user.user_id)
        if report is None:
            await query.answer([], cache_time=0, is_personal=True)
            return
        link = f"https://t.me/{ctx.username}"
        await query.answer([InlineQueryResultArticle(
            id="cv-score", title=t("cv-report-score", score=report.score).replace("<b>", "").replace("</b>", ""),
            input_message_content=InputTextMessageContent(message_text=t("cv-share-caption", score=report.score, link=link)),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t("cv-btn-try"), url=link)]]),
        )], cache_time=0, is_personal=True)

    async def action(message: Message, name: str, state: FSMContext, user: BotUser, lang: str, t: Translate) -> None:
        if name == "share":
            await share(message, user, t)
            return
        if name == "pro":
            await buy_review(message, user, t)
            return
        if ctx.ai is None:
            await message.answer(t("ai-unavailable"))
            return
        session = await source(message, user, t)
        if session is None:
            return
        if name == "match":
            await state.set_state(CVFlow.job)
            await message.answer(t("cv-ask-job"))
        elif name == "coverletter":
            await state.set_state(CVFlow.cover_job)
            await message.answer(t("cv-ask-cover-job"))
        elif name == "interview":
            await state.set_state(CVFlow.role)
            await message.answer(t("cv-ask-role"))
        elif name == "linkedin":
            try:
                profile = await service.linkedin(session.source, user.user_id, lang)
                await send_blocks(message, [f"<b>{esc(profile.headline)}</b>", esc(profile.summary)])
            except AIError as exc:
                await ai_error(message, exc, t)
        elif name == "export":
            if not user.is_vip():
                await message.answer(t("cv-export-vip"), reply_markup=upgrades(t))
                return
            await message.answer(t("cv-select-template"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=t("cv-template-classic"), callback_data="cv:pdf:classic"),
                InlineKeyboardButton(text=t("cv-template-modern"), callback_data="cv:pdf:modern"),
            ]]))

    @router.message(Command("match", "coverletter", "linkedin", "interview", "export"))
    async def action_command(message: Message, state: FSMContext, user: BotUser, lang: str, t: Translate) -> None:
        name = (message.text or "").split()[0][1:].split("@")[0].lower()
        await action(message, name, state, user, lang, t)

    @router.callback_query(F.data.startswith("cv:"))
    async def action_callback(query: CallbackQuery, state: FSMContext, user: BotUser, lang: str, t: Translate) -> None:
        await query.answer()
        # Send results privately even if someone forwards the score/report's buttons to a group.
        if not isinstance(query.message, Message) or query.message.chat.id != user.user_id:
            return
        name = (query.data or "")[3:]
        if name.startswith("pdf:"):
            if not user.is_vip():
                await query.message.answer(t("cv-export-vip"), reply_markup=upgrades(t))
                return
            session = await source(query.message, user, t)
            if session is None:
                return
            template = name[4:]
            if template not in {"classic", "modern"}:
                return
            try:
                improved = await service.improve(session.source, user.user_id, lang)
                pdf = await asyncio.to_thread(render_pdf, improved, template)
                await query.message.answer_document(BufferedInputFile(pdf, filename=f"cv-{template}.pdf"))
            except AIError as exc:
                await ai_error(query.message, exc, t)
            except (ValueError, RuntimeError):
                await query.message.answer(t("cv-export-error"))
        else:
            await action(query.message, name, state, user, lang, t)

    @router.message(StateFilter(CVFlow.job, CVFlow.cover_job), F.text, ~F.text.startswith("/"))
    async def job_input(message: Message, state: FSMContext, user: BotUser, lang: str, t: Translate) -> None:
        session = await source(message, user, t)
        if session is None:
            await state.clear()
            return
        job = (message.text or "").strip()
        if len(job) > 15000:
            await message.answer(t("cv-text-limit", max=15000))
            return
        try:
            if await state.get_state() == CVFlow.job.state:
                match = await service.match(session.source, job, user.user_id, lang)
                await send_blocks(message, [t("cv-job-score", score=match.score), t("cv-keywords"),
                    *[f"• {esc(k)}" for k in match.missing_keywords], t("cv-tailored"),
                    *[f"• {esc(b)}" for b in match.tailored_bullets]])
            else:
                letter = await service.cover_letter(session.source, job, user.user_id, lang)
                # Free text has no markup: split before escaping to keep entities complete.
                await send_blocks(message, [esc(letter[i:i + 1500]) for i in range(0, len(letter), 1500)])
            await state.clear()
        except AIError as exc:
            await ai_error(message, exc, t)

    @router.message(CVFlow.role, F.text, ~F.text.startswith("/"))
    async def interview_role(message: Message, state: FSMContext, user: BotUser, lang: str, t: Translate) -> None:
        session = await source(message, user, t)
        if session is None:
            await state.clear()
            return
        try:
            questions = await service.interview(session.source, (message.text or "")[:200], user.user_id, lang)
            session.questions = questions.questions
            await state.set_data({"question": 0})  # No original CV or answer text goes into Redis FSM data.
            await state.set_state(CVFlow.answer)
            await message.answer(t("cv-question", number=1, question=esc(session.questions[0])))
        except AIError as exc:
            await ai_error(message, exc, t)

    @router.message(CVFlow.answer, F.text, ~F.text.startswith("/"))
    async def interview_answer(message: Message, state: FSMContext, user: BotUser, lang: str, t: Translate) -> None:
        session = await source(message, user, t)
        index = (await state.get_data()).get("question", 0)
        if session is None or not session.questions or not isinstance(index, int) or not 0 <= index < 5:
            await state.clear()
            return
        try:
            feedback = await service.feedback(session.questions[index], (message.text or "")[:4000], user.user_id, lang)
            await send_blocks(message, [t("cv-answer-score", score=feedback.score), esc(feedback.feedback)])
            index += 1
            if index == 5:
                await state.clear()
                session.questions.clear()
                await message.answer(t("cv-interview-done"))
            else:
                await state.update_data(question=index)
                await message.answer(t("cv-question", number=index + 1, question=esc(session.questions[index])))
        except AIError as exc:
            await ai_error(message, exc, t)

    @router.message(F.document | F.photo | (F.text & ~F.text.startswith("/")))
    async def analyze_input(message: Message, user: BotUser, state: FSMContext, lang: str, t: Translate) -> None:
        await privacy(message, user, t)
        if ctx.ai is None:
            await message.answer(t("ai-unavailable"))
            return
        if not await require_subscription(ctx, user, message.chat.id, t, payload={"action": "cv"}):
            return
        lock = ctx.keys("cv_busy", user.user_id)
        token = secrets.token_hex(16)
        if not await ctx.redis.set(lock, token, nx=True, ex=900):
            await message.answer(t("cv-busy"))
            return
        day: str | None = None
        credit: int | None = None
        completed = False
        try:
            settings: CVSettings = await ctx.settings.get()
            epoch = await service.epoch(user.user_id)
            extracted: Extracted | None = None
            if message.text:
                text = message.text.strip()
                if len(text) > settings.max_text_chars:
                    await message.answer(t("cv-text-limit", max=settings.max_text_chars))
                    return
            else:
                asset = message.document or (message.photo[-1] if message.photo else None)
                if asset is None:
                    return
                filename = message.document.file_name or "file" if message.document else "cv.jpg"
                data = await fetch_bytes(ctx, asset.file_id, asset.file_size, settings.max_file_mb * 1024 * 1024)
                extracted = await asyncio.to_thread(extract, data, filename,
                    max_pages=settings.max_pages, max_chars=settings.max_text_chars)
                del data
                text = extracted.text
            if message.text and len(text.strip()) < 40:
                await message.answer(t("cv-too-short"))
                return
            if not user.is_vip():
                credit = await pro.consume(user.user_id)
                if credit is None:
                    day = await quota.consume(user.user_id, settings.free_analyses_per_day)
                    if day is None:
                        await message.answer(t("cv-quota", max=settings.free_analyses_per_day), reply_markup=upgrades(t))
                        return
            if extracted is not None:
                # Reserve allowance before any paid vision transcription, including exhausted free users.
                text = await service.read_scans(extracted, user.user_id, settings.max_text_chars)
                del extracted
            if len(text.strip()) < 40:
                await message.answer(t("cv-too-short"))
                return
            await message.answer(t("cv-analyzing"))
            report = await service.analyze(text, user.user_id, lang, pro=credit is not None)
            if await service.save(user.user_id, report, epoch) is None:
                return  # /forget happened while AI was processing; refund and discard this result.
            service.remember(user.user_id, text, report, epoch)
            completed = True
            await state.clear()
            await send_blocks(message, analysis_blocks(report, t), actions(t))
            await record_user_action(ctx, user.user_id)
        except FileTooLarge:
            await message.answer(t("cv-file-limit"))
        except ExtractionError:
            await message.answer(t("cv-extract-error"))
        except AIError as exc:
            await ai_error(message, exc, t)
        finally:
            if not completed:
                if day is not None:
                    await quota.refund(user.user_id, day=day, token=token)
                if credit is not None:
                    await pro.restore(user.user_id, credit)
            with contextlib.suppress(Exception):
                await cast(Awaitable[object], ctx.redis.eval(
                    "if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) end return 0",
                    1, lock, token,
                ))

    return router
