"""Notes and reminders storage + the reminder delivery job."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bots.notes.models import Note, Reminder
from core.db.base import affected, utcnow
from core.log import get_logger
from core.sdk.context import BotContext
from core.ui.text import esc

log = get_logger(__name__)

MAX_NOTE_CHARS = 3500
MAX_DELAY = timedelta(days=365)
_DURATION = re.compile(r"^(\d{1,4})\s*([mhd])$", re.IGNORECASE)
_CLOCK = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


class LimitReached(Exception):
    pass


def parse_when(token: str, now: datetime) -> datetime | None:
    """'10m' / '2h' / '3d' -> now + delta;  'HH:MM' -> next occurrence (UTC). None if not understood."""
    if m := _DURATION.match(token):
        value, unit = int(m.group(1)), m.group(2).lower()
        delta = {"m": timedelta(minutes=value), "h": timedelta(hours=value), "d": timedelta(days=value)}[unit]
        return now + delta if timedelta(0) < delta <= MAX_DELAY else None
    if m := _CLOCK.match(token):
        due = now.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
        return due if due > now else due + timedelta(days=1)
    return None


class NotesService:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.sm = sessionmaker

    async def count_notes(self, user_id: int) -> int:
        async with self.sm() as s:
            return int((await s.execute(select(func.count()).where(Note.user_id == user_id))).scalar_one())

    async def add_note(self, user_id: int, text: str, limit: int) -> Note:
        if await self.count_notes(user_id) >= limit:
            raise LimitReached
        async with self.sm() as s:
            note = Note(user_id=user_id, text=text[:MAX_NOTE_CHARS])
            s.add(note)
            await s.commit()
            return note

    async def page(self, user_id: int, page: int, per_page: int = 5) -> tuple[list[Note], int]:
        async with self.sm() as s:
            total = int((await s.execute(select(func.count()).where(Note.user_id == user_id))).scalar_one())
            stmt = (
                select(Note)
                .where(Note.user_id == user_id)
                .order_by(Note.id.desc())
                .offset(max(0, page - 1) * per_page)
                .limit(per_page)
            )
            return list((await s.execute(stmt)).scalars()), total

    async def delete_note(self, user_id: int, note_id: int) -> bool:
        async with self.sm() as s:
            res = await s.execute(delete(Note).where(Note.id == note_id, Note.user_id == user_id))
            await s.commit()
            return bool(affected(res))

    async def pending_reminders(self, user_id: int) -> list[Reminder]:
        async with self.sm() as s:
            stmt = (
                select(Reminder)
                .where(Reminder.user_id == user_id, Reminder.sent_at.is_(None))
                .order_by(Reminder.due_at)
            )
            return list((await s.execute(stmt)).scalars())

    async def add_reminder(
        self, user_id: int, chat_id: int, text: str, due_at: datetime, lang: str, limit: int
    ) -> Reminder:
        if len(await self.pending_reminders(user_id)) >= limit:
            raise LimitReached
        async with self.sm() as s:
            r = Reminder(user_id=user_id, chat_id=chat_id, text=text[:1000], due_at=due_at, lang=lang)
            s.add(r)
            await s.commit()
            return r

    async def cancel_reminder(self, user_id: int, reminder_id: int) -> bool:
        async with self.sm() as s:
            res = await s.execute(
                delete(Reminder).where(
                    Reminder.id == reminder_id, Reminder.user_id == user_id, Reminder.sent_at.is_(None)
                )
            )
            await s.commit()
            return bool(affected(res))

    async def totals(self) -> dict[str, int]:
        async with self.sm() as s:
            notes = int((await s.execute(select(func.count()).select_from(Note))).scalar_one())
            pending = int(
                (await s.execute(select(func.count()).where(Reminder.sent_at.is_(None)))).scalar_one()
            )
            sent = int((await s.execute(select(func.count()).where(Reminder.sent_at.is_not(None)))).scalar_one())
        return {"notes": notes, "pending": pending, "sent": sent}


async def deliver_due_reminders(ctx: BotContext) -> int:
    """Scheduled job: send every due reminder exactly once (claimed with a conditional UPDATE)."""
    now = utcnow()
    async with ctx.sm() as s:
        due = list(
            (
                await s.execute(
                    select(Reminder).where(Reminder.sent_at.is_(None), Reminder.due_at <= now).order_by(Reminder.due_at).limit(500)
                )
            ).scalars()
        )
    delivered = 0
    for r in due:
        async with ctx.sm() as s:
            claimed = await s.execute(
                update(Reminder).where(Reminder.id == r.id, Reminder.sent_at.is_(None)).values(sent_at=utcnow())
            )
            await s.commit()
        if not affected(claimed):
            continue  # another scheduler replica took it
        text = ctx.translator.get(r.lang, "notes-reminder-fire", text=esc(r.text))
        try:
            await ctx.bot.send_message(chat_id=r.chat_id, text=text)
            delivered += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            await ctx.bot.send_message(chat_id=r.chat_id, text=text)
            delivered += 1
        except TelegramForbiddenError:
            await ctx.users.set_blocked(r.user_id, True)
        except Exception as e:
            log.warning("reminder_send_failed", reminder_id=r.id, error=str(e))
        await asyncio.sleep(0.05)
    return delivered

