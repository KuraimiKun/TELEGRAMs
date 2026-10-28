"""Versioned selected group modules; transient identity/trust/issued work is never portable."""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any, Literal

from aiogram.exceptions import TelegramAPIError
from aiogram.types import File
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select, update

from bots.groupguard import authz, delivery, filter_commands, jobs, perms, repeats
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.content_commands import valid
from bots.groupguard.contracts import Actor
from bots.groupguard.models import (
    GuardChallenge,
    GuardChat,
    GuardItem,
    GuardJob,
    GuardRaid,
    GuardRepeat,
    GuardRestriction,
)
from core.db.base import utcnow
from core.db.models import AdminAuditLog
from core.sdk.context import BotContext

MAX_BYTES = 2 * 1024 * 1024
MAX_ITEMS = 1000
SCHEMA = 'groupguard.modules'
VERSION = 1
MODULES: dict[str, tuple[str, ...]] = {
    'moderation': ('warn_limit','warn_action','warn_duration_seconds','warn_legacy_duration','warn_time_seconds',
        'adminerror','anonadmin','reports','antichannelpin','cleanlinked'),
    'protections': ('cas','newbie_hours','ai_spam','action_minutes'),
    'captcha': ('captcha','captcha_enabled','captcha_minutes','captcha_text','captcha_rules','captcha_kick',
        'captcha_kick_seconds','captcha_mute_seconds'),
    'flood': ('flood_count','flood_seconds','flood_action','flood_consecutive_count','flood_duration_seconds',
        'flood_legacy_duration','flood_silent','clear_flood'),
    'raid': ('raid_seconds','raid_ban_seconds','auto_raid_count'),
    'night': ('night','night_start','night_end','tz_offset'),
    'locks': ('locks','lock_schema_version','lock_policies','lock_warns','allowlist'),
    'blocklists': ('blocklist','blocklist_warn','blocklist_entries','blocklist_mode','blocklist_duration_seconds',
        'blocklist_delete','blocklist_reason'),
    'rules': ('rules','rules_format','private_rules','rules_button'),
    'notes': ('private_notes',),
    'filters': (),
    'greetings': ('welcome','welcome_text','welcome_content','goodbye','goodbye_content','clean_welcome'),
    'policy': ('disabled_commands','disabled_delete','disable_admin','command_clean_types','bot_clean_types',
        'service_clean_types','clean_service','bot2bot_mode','bot2bot_skip_review','silent_actions_allowed'),
    'language': ('lang',),
    'destinations': ('action_topic','log_chat_id','log_categories'),
    'extensions': (),
}
NONPORTABLE = {'credit','welcome_messages','night_policy_version'}


class PortableError(ValueError):
    pass


class Item(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True,strict=True)
    kind: str
    key: str = Field(min_length=1, max_length=64)
    text: str | None = Field(default=None, max_length=32768)
    media_kind: str | None = None
    file_id: str | None = Field(default=None, max_length=256)
    format: Literal['html', 'rose'] = 'html'
    options: dict[str, Any] = Field(default_factory=dict)


class Envelope(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True,strict=True)
    schema_name: str = Field(alias='schema')
    version: int
    source_bot_id: int = Field(gt=0)
    source_chat_id: int = Field(lt=0)
    modules: dict[str, dict[str, Any]]
    items: list[Item] = Field(default_factory=list, max_length=MAX_ITEMS)


def selected(value: str) -> frozenset[str]:
    names = frozenset(value.lower().replace(',', ' ').split())
    if not names or names == {'all'}:
        return frozenset(MODULES)
    if not names <= MODULES.keys():
        raise PortableError('module')
    return names


async def authorize(ctx: BotContext, actor: Actor, chat_id: int, *, creator: bool, session=None) -> None:
    if (actor.kind != 'human' or actor.human_id is None or actor.bot_id != ctx.bot_id
            or not await authz.active_namespace(ctx, session)):
        raise PortableError('authority')
    actual = await authz.authorize(ctx, actor, target_chat_id=chat_id,
        caller_rights=frozenset({'creator'} if creator else set()), bot_rights=frozenset(),session=session)
    if not actual.allowed:
        raise PortableError('authority')


async def export(ctx: BotContext, actor: Actor, chat_id: int, modules: frozenset[str]) -> bytes:
    await authorize(ctx, actor, chat_id, creator=False)
    cfg = await ctx.extras['guard'].config(chat_id, fresh=True)
    current = cfg.model_dump()
    entries = {name: {key: current[key] for key in MODULES[name]} for name in modules if name != 'extensions'}
    if 'extensions' in modules:
        entries['extensions'] = dict(cfg.model_extra or {})
    async with ctx.sm() as session:
        kinds = [kind for kind, family in [('note','notes'),('filter','filters')] if family in modules]
        rows = list((await session.execute(select(GuardItem).where(GuardItem.bot_id == ctx.bot_id,
            GuardItem.chat_id == chat_id, GuardItem.kind.in_(kinds)).order_by(GuardItem.kind, GuardItem.key)
            .limit(MAX_ITEMS + 1))).scalars()) if kinds else []
        if len(rows) > MAX_ITEMS:
            raise PortableError('limit')
    items = [dict(kind=row.kind,key=row.key,text=row.text,media_kind=row.media_kind,file_id=row.file_id,
        format=row.content_format,options=row.options) for row in rows]
    body = json.dumps(dict(schema=SCHEMA,version=VERSION,source_bot_id=ctx.bot_id,source_chat_id=chat_id,
        modules=entries,items=items),ensure_ascii=False).encode()
    if len(body) > MAX_BYTES:
        raise PortableError('limit')
    return body


def parse(body: bytes, modules: frozenset[str]) -> Envelope:
    if not body or len(body) > MAX_BYTES:
        raise PortableError('limit')
    try:
        document = Envelope.model_validate_json(body)
    except (ValueError, RecursionError) as error:
        raise PortableError('format') from error
    if document.schema_name != SCHEMA or document.version != VERSION:
        raise PortableError('version')
    if not set(document.modules) <= MODULES.keys() or not modules <= document.modules.keys():
        raise PortableError('module')
    for name, fields in document.modules.items():
        if name != 'extensions' and set(fields) != set(MODULES[name]):
            raise PortableError('field')
        if name == 'extensions' and (set(fields) & (set(ChatConfig.model_fields) | NONPORTABLE)):
            raise PortableError('field')
    seen: set[tuple[str,str]] = set()
    for item in document.items:
        if item.kind not in {'note','filter'} or ('notes' if item.kind == 'note' else 'filters') not in document.modules:
            raise PortableError('item')
        identity = (item.kind,item.key.lower())
        if identity in seen:
            raise PortableError('item')
        seen.add(identity)
        if item.format not in {'html','rose'}:
            raise PortableError('item')
        valid(delivery.Content(item.text or '',item.format,item.media_kind,item.file_id),
            document.source_chat_id,item.kind)
        validate_options(item)
    return document


def validate_options(item: Item) -> None:
    from dataclasses import fields

    from bots.groupguard.formatting import Controls
    allowed = {field.name for field in fields(Controls)} | {'match'}
    if not set(item.options) <= allowed:
        raise PortableError('item')
    for key,value in item.options.items():
        if key in {'match','command_description'}:
            if not isinstance(value,str) or len(value)>256:
                raise PortableError('item')
        elif key == 'repeat_seconds':
            if value is not None and (type(value) is not int or not 60<=value<=30*86400):
                raise PortableError('item')
        elif type(value) is not bool:
            raise PortableError('item')
    if item.options.get('match','word') not in {'word','contains','prefix','exact'}:
        raise PortableError('item')
    if ((item.options.get('admin') and item.options.get('user')) or
            (item.options.get('private') and item.options.get('noprivate')) or
            (item.options.get('repeat_seconds') and (item.kind != 'note' or item.options.get('private') or item.options.get('admin')))):
        raise PortableError('item')
    if bool(item.media_kind) != bool(item.file_id) or item.media_kind not in {
            None,'photo','video','animation','document','audio','voice','sticker','video_note'}:
        raise PortableError('media')


async def destinations(ctx: BotContext, actor: Actor, chat_id: int, cfg: ChatConfig, document: Envelope | None) -> None:
    if cfg.lang is not None and cfg.lang not in ctx.translator.locales:
        raise PortableError('language')
    if cfg.action_topic is not None:
        # Telegram has no GetForumTopic method. Only same-group identifiers are portable.
        if document is not None and document.source_chat_id != chat_id:
            raise PortableError('destination')
        chat = await ctx.bot.get_chat(chat_id)
        bot = await perms.fresh_rights(ctx,chat_id,ctx.bot_id)
        if not chat.is_forum or bot is None or not bot.allows('manage_topics'):
            raise PortableError('destination')
    if cfg.log_chat_id is not None:
        from bots.groupguard.federations import destination
        if not await destination(ctx,actor.human_id or 0,cfg.log_chat_id):
            raise PortableError('destination')
    if cfg.silent_actions_allowed and (cfg.log_chat_id is None or 'automated' not in cfg.log_categories):
        raise PortableError('destination')


async def restore_selected(ctx: BotContext, chat_id: int, modules: frozenset[str]) -> None:
    if 'night' in modules:
        result = await jobs.apply_night(ctx,chat_id,await ctx.extras['guard'].config(chat_id,fresh=True),force_restore=True)
        if not result.primary_completed and result.status != 'noop':
            raise PortableError('restore')
    if 'captcha' in modules:
        cursor = 0
        while True:
            async with ctx.sm() as session:
                rows = list((await session.execute(select(GuardRestriction).where(
                    GuardRestriction.bot_id==ctx.bot_id,GuardRestriction.chat_id==chat_id,
                    GuardRestriction.user_id>cursor,GuardRestriction.source=='captcha',GuardRestriction.mode=='mute')
                    .order_by(GuardRestriction.user_id).limit(100))).scalars())
            if not rows:
                break
            for row in rows:
                from bots.groupguard import actions
                result = await actions.unmute(ctx,chat_id,row.user_id,source='captcha',generation=row.generation)
                if not result.primary_completed:
                    raise PortableError('restore')
            cursor=rows[-1].user_id


async def media(ctx: BotContext, document: Envelope, modules: frozenset[str]) -> None:
    files = {item.file_id for item in document.items if item.file_id and
        ('notes' if item.kind == 'note' else 'filters') in modules}
    for family in ('greetings',):
        if family in modules:
            for field in ('welcome_content','goodbye_content'):
                value = document.modules[family].get(field)
                if isinstance(value,dict) and value.get('file_id'):
                    files.add(value['file_id'])
    if files and document.source_bot_id != ctx.bot_id:
        raise PortableError('media')
    for file_id in files:
        try:
            found = await ctx.bot.get_file(file_id)
        except TelegramAPIError as error:
            raise PortableError('media') from error
        if not isinstance(found,File) or not found.file_path:
            raise PortableError('media')


@dataclass(frozen=True, slots=True)
class Intent:
    chat_id: int
    modules: frozenset[str]
    body: bytes | None
    expected_revision: int
    reset: bool = False

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.body or b'reset').hexdigest()


async def prepared(ctx: BotContext, actor: Actor, intent: Intent, document: Envelope | None, stored: dict) -> ChatConfig:
    old = ChatConfig.from_storage(stored)
    defaults = ChatConfig().model_dump()
    values = dict(stored)
    for name in intent.modules:
        if name == 'extensions':
            if document is not None:
                values.update(document.modules[name])
            else:
                values = {key:value for key,value in values.items() if key in ChatConfig.model_fields}
            continue
        fields = document.modules[name] if document is not None else {key:defaults[key] for key in MODULES[name]}
        values.update(fields)
    if 'night' in intent.modules:
        values['night_policy_version'] = old.night_policy_version + 1
    try:
        cfg = ChatConfig.model_validate(ChatConfig.normalized_storage(values),strict=True)
        from bots.groupguard.formatting import Fillings, validate
        from bots.groupguard.handlers.tools import LOG_CATEGORIES
        from bots.groupguard.lock_types import CANONICAL_LOCKS, expand
        from bots.groupguard.locks import Policy, validate_allowlist
        expand(cfg.locks)
        if not set(cfg.lock_policies)<=set(CANONICAL_LOCKS) or not set(cfg.log_categories)<=set(LOG_CATEGORIES):
            raise ValueError('policy')
        for policy in cfg.lock_policies.values():
            Policy.model_validate(policy,strict=True).checked()
        validate_allowlist(cfg.allowlist,allow_empty=True)
        validate(cfg.rules,Fillings(None,intent.chat_id),format=cfg.rules_format,kind='rules')
        for family in ('welcome','goodbye'):
            value=getattr(cfg,family+'_content')
            if value is not None:
                content=delivery.Content.from_dict(value)
                if content.format not in {'html','rose'} or content.media_kind not in {
                        None,'photo','video','animation','document','audio','voice','sticker','video_note'}:
                    raise ValueError('media')
                if bool(content.media_kind)!=bool(content.file_id) or (content.file_id and len(content.file_id)>256):
                    raise ValueError('media')
                validate(content.raw,Fillings(None,intent.chat_id),format=content.format,kind=family)
    except ValueError as error:
        raise PortableError('field') from error
    if intent.modules & {'language','policy','destinations'}:
        await destinations(ctx,actor,intent.chat_id,cfg,document)
    settings = await ctx.settings.get()
    if len(cfg.blocklist_entries)>settings.max_blocklist:
        raise PortableError('limit')
    return cfg


async def apply(ctx: BotContext, actor: Actor, intent: Intent) -> None:
    if not intent.modules or not intent.modules<=MODULES.keys():
        raise PortableError('module')
    await authorize(ctx,actor,intent.chat_id,creator=True)
    document = parse(intent.body or b'',intent.modules) if not intent.reset else None
    if document is not None:
        await media(ctx,document,intent.modules)
    svc = ctx.extras['guard']
    original = await svc.config(intent.chat_id,fresh=True)
    if original._revision != intent.expected_revision:
        raise PortableError('stale')
    await prepared(ctx,actor,intent,document,original.model_dump())
    async with svc.member_session(intent.chat_id,0) as (session,_member):
        row = (await session.execute(select(GuardChat).where(GuardChat.bot_id==ctx.bot_id,
            GuardChat.chat_id==intent.chat_id).with_for_update())).scalar_one_or_none()
        if row is None or row.revision != intent.expected_revision:
            raise PortableError('stale')
        await authorize(ctx,actor,intent.chat_id,creator=True,session=session)
        cfg=await prepared(ctx,actor,intent,document,row.config or {})
        settings=await ctx.settings.get()
        kinds = [kind for kind,family in [('note','notes'),('filter','filters')] if family in intent.modules]
        if kinds:
            from sqlalchemy import func
            kept = (await session.execute(select(func.count()).select_from(GuardItem).where(
                GuardItem.bot_id==ctx.bot_id,GuardItem.chat_id==intent.chat_id,GuardItem.kind.not_in(kinds)))).scalar_one()
            incoming = [item for item in document.items if item.kind in kinds] if document is not None else []
            if kept+len(incoming)>settings.max_items:
                raise PortableError('limit')
            for item in incoming:
                if item.options.get('repeat_seconds') and cfg.private_notes and not item.options.get('noprivate'):
                    raise PortableError('item')
            await restore_selected(ctx,intent.chat_id,intent.modules)
            await authorize(ctx,actor,intent.chat_id,creator=True,session=session)
            selected_ids = select(GuardItem.id).where(GuardItem.bot_id==ctx.bot_id,
                GuardItem.chat_id==intent.chat_id,GuardItem.kind.in_(kinds))
            await session.execute(update(GuardJob).where(GuardJob.bot_id==ctx.bot_id,
                GuardJob.chat_id==intent.chat_id,GuardJob.kind=='repeat_note',
                GuardJob.payload['item_id'].as_integer().in_(selected_ids),
                GuardJob.status.in_({'pending','running'}),GuardJob.dispatched.is_(False)).values(status='cancelled'))
            await session.execute(delete(GuardRepeat).where(GuardRepeat.bot_id==ctx.bot_id,
                GuardRepeat.chat_id==intent.chat_id,GuardRepeat.item_id.in_(selected_ids)))
            await session.execute(delete(GuardItem).where(GuardItem.bot_id==ctx.bot_id,
                GuardItem.chat_id==intent.chat_id,GuardItem.kind.in_(kinds)))
            if document is not None:
                for item in document.items:
                    if item.kind not in kinds:
                        continue
                    saved = GuardItem(bot_id=ctx.bot_id,chat_id=intent.chat_id,kind=item.kind,key=item.key.lower(),
                        text=item.text,content_format=item.format,media_kind=item.media_kind,file_id=item.file_id,
                        options=item.options)
                    session.add(saved)
                    await session.flush()
                    if item.kind == 'note':
                        interval = item.options.get('repeat_seconds')
                        if interval is not None:
                            await repeats.replace(ctx,session,saved,author_id=actor.human_id,
                                seconds=int(interval),thread_id=None)
        if not kinds:
            await restore_selected(ctx,intent.chat_id,intent.modules)
            await authorize(ctx,actor,intent.chat_id,creator=True,session=session)
        row.config = cfg.model_dump()
        row.night = cfg.night
        row.revision += 1
        row.updated_at = utcnow()
        session.add(AdminAuditLog(bot_id=ctx.bot_id,admin_id=actor.human_id or 0,
            action='gg_reset' if intent.reset else 'gg_import',target=str(intent.chat_id),
            details=dict(modules=sorted(intent.modules),sha256=intent.digest)))
        if 'captcha' in intent.modules:
            await session.execute(update(GuardChallenge).where(GuardChallenge.bot_id==ctx.bot_id,
                GuardChallenge.chat_id==intent.chat_id,GuardChallenge.status.in_({'pending','issuing'})).values(status='cancelled'))
            await session.execute(update(GuardJob).where(GuardJob.bot_id==ctx.bot_id,GuardJob.chat_id==intent.chat_id,
                GuardJob.kind=='captcha_expire',GuardJob.dispatched.is_(False),GuardJob.status.in_({'pending','running'}))
                .values(status='cancelled'))
        if 'raid' in intent.modules:
            # A selected replacement retires the old transient activation and
            # its deadline. Existing punitive restrictions remain untouched.
            await session.execute(update(GuardRaid).where(GuardRaid.bot_id==ctx.bot_id,
                GuardRaid.chat_id==intent.chat_id).values(status='inactive',generation=uuid.uuid4().hex,
                    deadline=utcnow(),updated_at=utcnow()))
            await session.execute(update(GuardJob).where(GuardJob.bot_id==ctx.bot_id,
                GuardJob.chat_id==intent.chat_id,GuardJob.kind=='raid_expire',
                GuardJob.dispatched.is_(False),GuardJob.status.in_({'pending','running'}))
                .values(status='cancelled',updated_at=utcnow()))
    if intent.modules & {'filters','language'}:
        step=await filter_commands.sync(ctx,intent.chat_id)
        if not step.completed:
            raise PortableError('saved_delivery')
