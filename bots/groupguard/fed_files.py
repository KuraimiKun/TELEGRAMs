"""Bounded federation ban files: explicit CSV/minicsv/JSON export and CSV/JSONL import."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from collections.abc import Buffer
from dataclasses import dataclass

from aiogram.types import BufferedInputFile, Message
from redis.exceptions import RedisError
from sqlalchemy import select

from bots.groupguard import fed_bans, fed_enforcement, federations
from bots.groupguard.contracts import Actor
from bots.groupguard.federations import FedError
from bots.groupguard.models import GuardFedBan
from core.db.base import utcnow
from core.sdk.context import BotContext

MAX_BYTES = 2 * 1024 * 1024
MAX_RECORDS = 1000
INTERVAL = 1800


def spreadsheet_safe(value: str) -> str:
    return "'" + value if value.startswith(("'", "=", "+", "-", "@")) else value


def csv_value(value: str | None) -> str | None:
    if value is not None and len(value) > 1 and value[0] == "'" and value[1] in "'=+-@":
        return value[1:]
    return value


class LimitedBuffer(io.BytesIO):
    def write(self, data: Buffer, /) -> int:
        if self.tell() + memoryview(data).nbytes > MAX_BYTES:
            raise FedError('file_limit')
        return super().write(data)


@dataclass(frozen=True, slots=True)
class Parsed:
    rows: tuple[fed_bans.BanInput, ...]
    duplicates: int


def parse(ctx: BotContext, body: bytes, filename: str) -> Parsed:
    if not body or len(body) > MAX_BYTES:
        raise FedError('file_limit')
    try:
        text = body.decode('utf-8-sig')
        if filename.lower().endswith('.csv'):
            reader = csv.DictReader(io.StringIO(text))
            fields = reader.fieldnames or []
            if len(fields) != len(set(fields)) or not {'id', 'reason'} <= set(fields):
                raise FedError('file_format')
            records = []
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise FedError('file_format')
                records.append({'user_id': row['id'], 'reason': csv_value(row['reason']),
                    'name': csv_value(row.get('name')), 'username': csv_value(row.get('username'))})
                if len(records) > MAX_RECORDS:
                    raise FedError('file_limit')
        elif filename.lower().endswith(('.jsonl', '.ndjson')):
            records = []
            for line in text.splitlines():
                if line.strip():
                    records.append(json.loads(line))
                if len(records) > MAX_RECORDS:
                    raise FedError('file_limit')
        elif filename.lower().endswith('.json'):
            # This is our verified JSON-array adapter; it is explicitly not JSONL.
            records = json.loads(text)
            if not isinstance(records, list):
                raise FedError('file_format')
        else:
            raise FedError('file_format')
    except (UnicodeDecodeError, json.JSONDecodeError, csv.Error, ValueError, RecursionError) as error:
        if isinstance(error, FedError):
            raise
        raise FedError('file_format') from error
    if len(records) > MAX_RECORDS:
        raise FedError('file_limit')
    unique: dict[int, fed_bans.BanInput] = {}
    duplicates = 0
    for record in records:
        if not isinstance(record, dict) or 'user_id' not in record:
            raise FedError('file_format')
        raw = record['user_id']
        if isinstance(raw, bool) or not isinstance(raw, (int, str)) or not str(raw).isdigit() or len(str(raw)) > 16:
            raise FedError('target')
        reason, name, username = record.get('reason'), record.get('name') or record.get('first_name'), record.get('username')
        if any(value is not None and not isinstance(value, str) for value in (reason, name, username)):
            raise FedError('file_format')
        item = fed_bans.validate(ctx, fed_bans.BanInput(int(raw), reason, name, username), reason_required=False)
        if item.user_id in unique:
            if unique[item.user_id] != item:
                raise FedError('file_duplicate')
            duplicates += 1
        else:
            unique[item.user_id] = item
    return Parsed(tuple(unique.values()), duplicates)


async def owner(ctx: BotContext, actor: Actor, fed_id: str, session=None):
    uid = await federations.human(ctx, actor, session)
    fed = await federations.get(ctx, fed_id, session, lock=session is not None)
    if fed is None:
        raise FedError('missing')
    if fed.owner_id != uid:
        raise FedError('authority')
    return fed


async def rate(ctx: BotContext, fed_id: str) -> None:
    try:
        if not await ctx.redis.set(ctx.keys('fed_file_interval', fed_id), 'attempted', ex=INTERVAL, nx=True):
            raise FedError('file_rate')
    except RedisError as error:
        raise FedError('file_rate') from error


async def export(ctx: BotContext, actor: Actor, fed_id: str, format: str) -> BufferedInputFile:
    if format not in {'csv', 'minicsv', 'json'}:
        raise FedError('file_format')
    fed = await owner(ctx, actor, fed_id)
    async with ctx.sm() as session:
        rows = list((await session.execute(select(GuardFedBan).where(GuardFedBan.bot_id == ctx.bot_id,
            GuardFedBan.fed_id == fed.id, GuardFedBan.active.is_(True)).order_by(
                GuardFedBan.user_id).limit(MAX_RECORDS + 1))).scalars())
    if len(rows) > MAX_RECORDS:
        raise FedError('file_limit')
    if format == 'json':
        body = json.dumps([dict(user_id=r.user_id, name=r.first_name, username=r.username, reason=r.reason,
            date=r.updated_at.isoformat()) for r in rows], ensure_ascii=False).encode()
    else:
        stream = io.StringIO(newline='')
        fields = ['id', 'reason'] if format == 'minicsv' else ['id', 'name', 'username', 'reason', 'date']
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for row in rows:
            values = dict(id=row.user_id, name=row.first_name or '', username=row.username or '',
                reason=row.reason or '', date=row.updated_at.isoformat())
            writer.writerow({key: spreadsheet_safe(value) if isinstance(value, str) else value
                for key, value in values.items() if key in fields})
        body = stream.getvalue().encode()
    if len(body) > MAX_BYTES:
        raise FedError('file_limit')
    await owner(ctx, actor, fed_id)
    await rate(ctx, fed_id)
    return BufferedInputFile(body, filename=f'federation-bans-{format}.' + ('json' if format == 'json' else 'csv'))


async def download(ctx: BotContext, message: Message) -> tuple[bytes, str]:
    doc = message.reply_to_message.document if message.reply_to_message is not None else None
    if doc is None or not doc.file_name or (doc.file_size is not None and doc.file_size > MAX_BYTES):
        raise FedError('file_limit')
    file = await ctx.bot.get_file(doc.file_id)
    if not file.file_path or (file.file_size is not None and file.file_size > MAX_BYTES):
        raise FedError('file_limit')
    buffer = LimitedBuffer()
    await ctx.bot.download_file(file.file_path, destination=buffer)
    return buffer.getvalue(), doc.file_name


async def import_rows(ctx: BotContext, actor: Actor, fed_id: str, body: bytes, filename: str) -> Parsed:
    await owner(ctx, actor, fed_id)
    parsed = parse(ctx, body, filename)
    async with ctx.extras['guard'].member_session(0, 0) as (session, _member):
        fed = await owner(ctx, actor, fed_id, session)
        values = [fed_bans.validate(ctx, row, reason_required=fed.reason_required) for row in parsed.rows]
        await rate(ctx, fed.id)
        for value in values:
            row = await session.get(GuardFedBan, (ctx.bot_id, fed.id, value.user_id), populate_existing=True)
            if row is None:
                row = GuardFedBan(bot_id=ctx.bot_id, fed_id=fed.id, user_id=value.user_id, active=True,
                    version=1, reason=value.reason, first_name=value.first_name, username=value.username,
                    by_id=actor.human_id or 0)
                session.add(row)
            else:
                row.version += 1
                row.active = True
                row.reason, row.first_name, row.username = value.reason, value.first_name, value.username
                row.by_id = actor.human_id or 0
                row.updated_at = utcnow()
            await session.flush()
            await fed_enforcement.enqueue_network(ctx, session, fed, user_id=row.user_id, version=row.version,
                by_id=actor.human_id or 0, event='ban')
        federations.audit(ctx, session, actor, 'import', fed.id, records=len(values), duplicates=parsed.duplicates,
            sha256=hashlib.sha256(body).hexdigest())
    await federations.emit(ctx, fed, actor, 'import')
    return parsed
