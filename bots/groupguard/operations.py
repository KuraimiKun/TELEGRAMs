"""Allowlisted immutable existing operations, shared by direct commands and human reviews."""
from __future__ import annotations

import json
from datetime import timedelta
from typing import Literal

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from pydantic import BaseModel, ConfigDict, Field, model_validator

from bots.groupguard import actions, authz, perms
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.contracts import ActionResult, Actor, Right, StepResult, result_of
from bots.groupguard.keyboards import GgCb
from bots.groupguard.service import GuardService, LimitReached
from core.sdk.context import BotContext
from core.ui.text import esc

Kind = Literal["ban", "mute", "kick", "unban", "unmute", "warn", "unwarn", "resetwarns",
               "purge", "delete", "pin", "unpin", "unpinall", "permapin", "promote", "demote",
               "approve_user", "unapprove", "unapproveall", "setlog", "unsetlog", "config", "save", "remove", "removeall", "panel",
               "lock_change", "allowlist_change", "allowlist_clear", "blocklist_change", "blocklist_clear", "raid_change", "policy_change",
               "topic_create", "topic_rename", "topic_close", "topic_reopen", "topic_delete", "echo", "fed_quiet"]
TARGETED = {"ban", "mute", "kick", "unban", "unmute", "warn", "unwarn", "resetwarns"}
PERSON_TARGETS = TARGETED | {"promote", "demote", "approve_user", "unapprove"}
CONFIRMATIONS = {"gg-language-saved","gg-rules-saved", "gg-rules-cleared", "gg-welcome-saved", "gg-welcome-reset",
                 "gg-locked", "gg-unlocked", "gg-blocklist-saved", "gg-night-on", "gg-night-off", "gg-setting-saved", "gg-anon-enabled"}


class Operation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    kind: Kind
    source_chat_id: int
    namespace_bot_id: int | None = None
    command_name: str = Field(default="", max_length=32)
    target_chat_id: int = Field(lt=0)
    message_id: int = Field(gt=0)
    thread_id: int | None = None
    chat_title: str | None = None
    target_id: int | None = None
    target_name: str = ""
    reason: str = Field(default="", max_length=256)
    duration_seconds: int | None = Field(default=None, ge=60, le=365 * 86400)
    silent: bool = False
    delete_reply: bool = False
    self_only: bool = False
    reply_id: int | None = None
    message_ids: tuple[int, ...] = ()
    patch_json: str = "{}"
    confirmation: str = ""
    values_json: str = "{}"
    item_kind: Literal["note", "filter"] = "note"
    key: str = ""
    keys: tuple[str, ...] = ()
    text: str | None = None
    content_format: Literal["html", "rose"] = "html"
    options_json: str = "{}"
    media_kind: str | None = None
    file_id: str | None = None
    log_chat_id: int | None = None
    loud: bool = False
    topic_id: int | None = Field(default=None, ge=1, le=2147483647)
    topic_name: str = Field(default="", max_length=128)

    @model_validator(mode="after")
    def validate_contract(self) -> Operation:
        if self.kind in PERSON_TARGETS and (self.target_id is None or not perms.valid_human_id(self.target_id)):
            raise ValueError("target_invalid")
        if self.silent and self.kind not in {"ban", "mute", "kick", "warn", "purge"}:
            raise ValueError("unsupported_silent")
        if self.delete_reply and (self.kind not in {"ban", "mute", "kick", "warn"} or self.reply_id is None):
            raise ValueError("reply_required")
        if self.self_only and self.kind != "kick":
            raise ValueError("self_only_kick")
        if self.kind == "config":
            patch = json.loads(self.patch_json)
            if not isinstance(patch, dict) or not patch or not set(patch) <= ChatConfig.model_fields.keys():
                raise ValueError("invalid_patch")
            ChatConfig.model_validate({**ChatConfig().model_dump(), **patch})
            from bots.groupguard.delivery import Content
            from bots.groupguard.formatting import Fillings, validate
            for name in ("welcome", "goodbye"):
                if patch.get(f"{name}_content") is not None:
                    saved = Content.from_dict(patch[f"{name}_content"])
                    validate(saved.raw, Fillings(None, self.target_chat_id), format=saved.format, kind=name)
            if "rules" in patch:
                saved = Content.from_dict(dict(raw=patch["rules"], format=patch.get("rules_format", "html")))
                validate(saved.raw, Fillings(None, self.target_chat_id), format=saved.format, kind="rules")
            if self.confirmation not in CONFIRMATIONS:
                raise ValueError("invalid_confirmation")
        if self.kind in {"save", "remove"} and not self.key:
            raise ValueError("missing_key")
        if self.kind == "save":
            from bots.groupguard.delivery import Content
            from bots.groupguard.formatting import Fillings, parse_controls, validate
            content = Content.from_dict(dict(raw=self.text or "", format=self.content_format,
                media_kind=self.media_kind, file_id=self.file_id))
            validate(content.raw, Fillings(None, self.target_chat_id), format=self.content_format, kind=self.item_kind)
            _, controls = parse_controls(content.raw, self.item_kind, format=self.content_format)
            if controls.repeat_seconds and (self.item_kind != "note" or controls.admin or controls.private):
                raise ValueError("repeat_access_invalid")
            options = json.loads(self.options_json)
            if not isinstance(options, dict) or set(options) - {"match"} or options.get("match", "word") not in {"word", "prefix", "exact"}:
                raise ValueError("options_invalid")
            keys = self.keys or (self.key,)
            if len(keys) > 30 or any(not k.strip() or len(k) > 64 for k in keys):
                raise ValueError("keys_invalid")
        if self.kind == "setlog" and (self.log_chat_id is None or self.log_chat_id >= 0):
            raise ValueError("invalid_log_destination")
        if self.kind == "lock_change":
            from bots.groupguard.lock_types import CANONICAL_LOCKS
            from bots.groupguard.locks import Policy
            if not self.keys or not set(self.keys) <= set(CANONICAL_LOCKS):
                raise ValueError("lock_types_invalid")
            Policy.model_validate_json(self.options_json).checked()
        if self.kind == "allowlist_change":
            from bots.groupguard.locks import validate_allowlist
            entries = json.loads(self.options_json)
            validate_allowlist(entries)
        if self.kind=="blocklist_change":
            from bots.groupguard.blocklist_types import Entry
            entries=json.loads(self.options_json)
            if not isinstance(entries,list) or not 1<=len(entries)<=30:
                raise ValueError("blocklist_entries_invalid")
            for entry in entries:
                Entry.model_validate(entry)
        if self.kind == "raid_change" and (self.loud != (self.duration_seconds is not None)):
            raise ValueError("raid_duration_invalid")
        if self.kind == "raid_change":
            options = json.loads(self.options_json)
            if not isinstance(options, dict) or set(options) - {"expected_generation"}:
                raise ValueError("raid_options_invalid")
            generation = options.get("expected_generation")
            if generation is not None and (not isinstance(generation, str) or len(generation) > 32):
                raise ValueError("raid_generation_invalid")
        if self.kind == 'fed_quiet':
            from bots.groupguard.federations import identifier
            identifier(self.key)
            options=json.loads(self.options_json)
            if (self.source_chat_id!=self.target_chat_id or not isinstance(options,dict)
                    or set(options)!={'expected_generation'}
                    or not isinstance(options['expected_generation'],str)
                    or len(options['expected_generation'])!=32):
                raise ValueError('federation_generation_invalid')
        if self.kind == "policy_change":
            options = json.loads(self.options_json)
            from bots.groupguard import cleanup, command_metadata
            rosters = {"disabled_commands":command_metadata.DISABLEABLE,"command_clean_types":cleanup.COMMAND_TYPES,
                       "bot_clean_types":cleanup.BOT_TYPES,"service_clean_types":cleanup.SERVICE_TYPES}
            if not isinstance(options,dict) or set(options)!={"field","values"} or options.get("field") not in rosters:
                raise ValueError("policy_options_invalid")
            if (not isinstance(options["values"],list) or any(not isinstance(value,str) for value in options["values"])
                    or not set(options["values"]) <= rosters[options["field"]]):
                raise ValueError("policy_options_invalid")
        if self.kind.startswith("topic_"):
            if self.kind in {"topic_create", "topic_rename"} and not self.topic_name:
                raise ValueError("topic_name_required")
            if self.kind != "topic_create" and self.topic_id is None:
                raise ValueError("topic_id_required")
        if self.kind == "echo":
            from bots.groupguard.content_commands import valid
            from bots.groupguard.delivery import Content
            valid(Content(self.text or "",self.content_format,self.media_kind,self.file_id),self.target_chat_id,"echo")
        if not isinstance(json.loads(self.values_json), dict):
            raise ValueError("invalid_values")
        return self

    def rights(self) -> tuple[frozenset[Right], frozenset[Right]]:
        caller: set[Right] = set()
        bot: set[Right] = set()
        if self.kind in TARGETED:
            if not self.self_only:
                caller.add("restrict_members")
            bot.add("restrict_members")
        elif self.kind in {"purge", "delete"}:
            caller.add("delete_messages")
            bot.add("delete_messages")
        elif self.kind in {"pin", "unpin", "unpinall", "permapin"}:
            caller.add("pin_messages")
            bot.add("pin_messages")
        elif self.kind in {"promote", "demote"}:
            caller.add("promote_members")
            bot.add("promote_members")
        elif self.kind in {"unapproveall", "removeall", "allowlist_clear", "blocklist_clear"} or (self.kind == "config" and "silent_actions_allowed" in json.loads(self.patch_json)):
            caller.add("creator")
        elif self.kind == "raid_change":
            caller.add("restrict_members")
            if self.loud:
                bot.add("restrict_members")
        elif self.kind.startswith("topic_") or (self.kind == "config" and "action_topic" in json.loads(self.patch_json)):
            caller.add("manage_topics")
            bot.add("manage_topics")
        else:
            caller.add("change_info")
        if (self.silent and self.kind != "purge") or self.delete_reply:
            caller.add("delete_messages")
            bot.add("delete_messages")
        return frozenset(caller), frozenset(bot)


def operation_for(message: Message, kind: Kind, **kwargs) -> Operation:
    from bots.groupguard import command_metadata, scope
    state = scope.CURRENT.get()
    target = scope.target_chat(message)
    command = command_metadata.parse(message)
    return Operation(kind=kind, source_chat_id=message.chat.id, target_chat_id=target.id,
                     namespace_bot_id=state.bot_id if state is not None and state.source is message else None,
                     command_name=command_metadata.purpose(command.name,command.args) if command else "",
                     message_id=message.message_id, thread_id=message.message_thread_id, chat_title=target.title, **kwargs)


def audit_operation(op: Operation) -> dict:
    """Audit immutable effect identifiers without duplicating saved/private content or media IDs."""
    import hashlib
    fields={'target_name','text','file_id','patch_json','options_json','values_json'}
    details=op.model_dump(mode='json',exclude=fields)
    for field in fields:
        value=getattr(op,field)
        if value:
            details[field+'_sha256']=hashlib.sha256(str(value).encode()).hexdigest()
    return details


async def operation_authorization(ctx: BotContext, actor: Actor, op: Operation) -> authz.Authorization:
    caller, bot = op.rights()
    if actor.source_chat_id != op.source_chat_id:
        return authz.Authorization(False, "wrong_scope")
    if op.namespace_bot_id is not None and op.namespace_bot_id != ctx.bot_id:
        return authz.Authorization(False, "wrong_scope")
    if op.source_chat_id > 0 and (op.kind in {"purge", "delete", "pin", "unpin"} or op.delete_reply):
        return authz.Authorization(False, "group_message_required")
    from bots.groupguard import policies
    if op.command_name and not await policies.allowed(ctx,op.command_name,op.target_chat_id,actor):
        return authz.Authorization(False, "command_disabled")
    if op.kind == "config" and json.loads(op.patch_json).get("flood_silent") is True:
        cfg = await ctx.extras["guard"].config(op.target_chat_id, fresh=True)
        if not cfg.silent_actions_allowed or cfg.log_chat_id is None or "automated" not in cfg.log_categories:
            return authz.Authorization(False, "silent_consent_required")
    if op.kind == "config" and json.loads(op.patch_json).get("silent_actions_allowed") is True:
        cfg = await ctx.extras["guard"].config(op.target_chat_id,fresh=True)
        if cfg.log_chat_id is None or "automated" not in cfg.log_categories:
            return authz.Authorization(False,"silent_consent_required")
    if op.self_only and (actor.kind != "human" or actor.human_id != op.target_id or op.source_chat_id != op.target_chat_id):
        return authz.Authorization(False, "self_only")
    if op.kind in TARGETED and op.target_id is not None:
        error = await perms.target_error(ctx, op.target_chat_id, op.target_id)
        if error:
            return authz.Authorization(False, error)
    if op.kind in {"approve_user", "unapprove"}:
        member = await perms.fresh_member(ctx, op.target_chat_id, op.target_id or 0)
        if member is None or member.user.is_bot:
            return authz.Authorization(False, "target_unknown")
    if op.kind == "setlog" and op.log_chat_id is not None:
        dest = await authz.authorize(ctx, actor, target_chat_id=op.log_chat_id,
                                     caller_rights=frozenset({"change_info"}), bot_rights=frozenset())
        if not dest.allowed:
            return dest
        try:
            chat = await ctx.bot.get_chat(op.log_chat_id)
        except TelegramAPIError:
            return authz.Authorization(False, "lookup_failed")
        if chat is None or chat.id != op.log_chat_id:
            return authz.Authorization(False, "lookup_failed")
        if chat.type == "channel":
            dest_bot = await perms.fresh_rights(ctx, op.log_chat_id, ctx.bot_id)
            if dest_bot is None or not dest_bot.allows("post_messages"):
                return authz.Authorization(False, "bot_denied")
    return await authz.authorize(ctx, actor, target_chat_id=op.target_chat_id,
                                 caller_rights=caller, bot_rights=bot, require_admin=not op.self_only)


async def submit(ctx: BotContext, message: Message, op: Operation) -> ActionResult | None:
    actor = authz.actor_from_message(ctx, message)
    cfg = await ctx.extras["guard"].config(op.target_chat_id, fresh=True)
    t = actions.group_t(ctx, cfg)
    if actor.kind == "bot" and not cfg.bot2bot_skip_review and op.kind != "panel":
        authorization = await operation_authorization(ctx,actor,op)
        if authorization.allowed:
            from bots.groupguard.reviews import create_review
            await create_review(ctx,actor,op)
        elif cfg.adminerror:
            await message.reply(denial_text(t,authorization))
        return None
    if actor.kind == "anonymous_group" and (not cfg.anonadmin or "creator" in op.rights()[0]):
        from bots.groupguard.reviews import create_review
        await create_review(ctx, actor, op)
        return None
    authorization = await operation_authorization(ctx, actor, op)
    if not authorization.allowed:
        if cfg.adminerror:
            await message.reply(denial_text(t, authorization))
        return None
    return await execute(ctx, actor, op, original_actor="bot" if actor.kind == "bot" else "human")


def denial_text(t, authorization: authz.Authorization) -> str:
    if authorization.code == "target_admin":
        return t("gg-target-admin")
    if authorization.code in {"target_invalid", "target_unknown"}:
        return t("gg-target-invalid")
    if authorization.code == "caller_denied":
        names = {"restrict_members": "restrict", "delete_messages": "delete", "pin_messages": "pin"}
        rights = ", ".join(t(f"gg-right-{names.get(r, r)}") for r in sorted(authorization.missing))
        return t("gg-need-right", right=rights or t("gg-right-admin"))
    return t("gg-auth-denied")


async def delete_operation_source(ctx: BotContext,actor: Actor,op: Operation,message_id: int) -> ActionResult:
    if op.source_chat_id < 0:
        return await actions.delete(ctx,op.source_chat_id,message_id,origin="manual")
    if actor.kind != "human" or actor.human_id != op.source_chat_id or not await authz.active_namespace(ctx):
        return actions.failure("source_delete","wrong_scope")
    return result_of(await actions.perform("private_command_delete",lambda: ctx.bot.delete_message(op.source_chat_id,message_id),acknowledged=True))


async def execute(ctx: BotContext, actor: Actor, op: Operation, *, reviewed: bool = False,
                  original_actor: Literal["human", "anonymous_group", "bot"] = "human",
                  original_bot_id: int | None = None) -> ActionResult:
    """Freshly authorize again immediately before the existing domain mutation."""
    svc: GuardService = ctx.extras["guard"]
    cfg = await svc.config(op.target_chat_id, fresh=True)
    t = actions.group_t(ctx, cfg)
    title = op.chat_title or await svc.title(op.target_chat_id)
    authorization = await operation_authorization(ctx, actor, op)
    if authorization.allowed and reviewed and original_actor == "bot":
        if original_bot_id is None:
            authorization = authz.Authorization(False,"bot_sender_invalid")
        else:
            source_bot = Actor(ctx.bot_id,op.source_chat_id,"bot",bot_sender_id=original_bot_id,
                               message_id=op.message_id,thread_id=op.thread_id)
            authorization = await operation_authorization(ctx,source_bot,op)
    if not authorization.allowed:
        result = actions.failure(op.kind, authorization.code)
        if actor.human_id is not None:
            await ctx.audit.record(actor.human_id, "gg_" + op.kind, target=op.target_chat_id, reviewed=reviewed,
                                   original_actor=original_actor, outcome=result.status, operation=audit_operation(op),
                                   primary_completed=False, denial=authorization.code)
        return result
    duration = timedelta(seconds=op.duration_seconds) if op.duration_seconds is not None else None
    who = actions.mention(op.target_id or 0, op.target_name)
    result = result_of(StepResult(op.kind, "applied"))
    text = ""
    if op.kind in {"ban", "mute", "kick"}:
        result = await actions.punish(ctx, op.target_chat_id, op.target_id or 0, op.kind, duration, origin="manual")
        key = {"ban": "gg-banned", "mute": "gg-muted", "kick": "gg-kicked"}[op.kind]
        text = t(key + "-for" if duration is not None and op.kind != "kick" else key, user=who,
                 time=perms.human(duration) if duration else "", reason=esc(op.reason or "—"))
        if op.silent or op.delete_reply:
            for mid in (op.reply_id, op.message_id if op.silent else None):
                if mid is not None:
                    result = result.with_steps(*(await delete_operation_source(ctx,actor,op,mid)).steps)
    elif op.kind in {"unban", "unmute"}:
        result = await (actions.unban if op.kind == "unban" else actions.unmute)(
            ctx, op.target_chat_id, op.target_id or 0, origin="manual")
        text = t("gg-unbanned" if op.kind == "unban" else "gg-unmuted", user=who)
    elif op.kind == "warn":
        from aiogram.types import Chat

        from bots.groupguard.handlers.moderation import apply_warn
        ancillary: list[StepResult] = []
        if op.silent or op.delete_reply:
            for mid in (op.reply_id, op.message_id if op.silent else None):
                if mid is not None:
                    ancillary.extend((await delete_operation_source(ctx,actor,op,mid)).steps)
        result = await apply_warn(ctx, svc, cfg, Chat(id=op.target_chat_id, type="supergroup", title=title),
            op.target_id or 0, op.target_name, op.reason or None, actor.human_id,
            ancillary_steps=tuple(ancillary), silent=op.silent, assumed_anonymous=actor.kind == "anonymous_group")
    elif op.kind in {"unwarn", "resetwarns"}:
        if op.kind == "unwarn":
            removed = await svc.remove_last_warn(op.target_chat_id, op.target_id or 0)
            result = result_of(StepResult("unwarn", "applied" if removed else "skipped"))
            count = await svc.count_warns(op.target_chat_id, op.target_id or 0)
            text = t("gg-unwarned", user=who, count=str(count), limit=str(cfg.warn_limit)) if removed else t("gg-item-missing")
        else:
            await svc.reset_warns(op.target_chat_id, op.target_id or 0)
            text = t("gg-warns-reset", user=who)
    elif op.kind in {"delete", "purge"}:
        result = await actions.delete_many(ctx, op.target_chat_id, op.message_ids, origin="manual", single=op.kind == "delete")
        text = t("gg-purge-ack", requested=str(len(result.requested_message_ids)),
                 acknowledged=str(len(result.acknowledged_message_ids)))
    elif op.kind in {"pin", "unpin"}:
        call = (lambda: ctx.bot.pin_chat_message(op.target_chat_id, op.reply_id or 0, disable_notification=not op.loud)) if op.kind == "pin" else (
            lambda: ctx.bot.unpin_chat_message(op.target_chat_id, message_id=op.reply_id))
        result = result_of(await actions.perform(op.kind, call))
        text = t("gg-done")
    elif op.kind == "unpinall":
        result = result_of(await actions.perform("unpinall", lambda: ctx.bot.unpin_all_chat_messages(op.target_chat_id)))
        text = t("gg-done")
    elif op.kind == "permapin":
        from bots.groupguard import delivery
        user = await perms.fresh_member(ctx, op.target_chat_id, actor.human_id) if actor.human_id else None
        f = await delivery.fillings(ctx, op.target_chat_id, user.user if user else None, raw=op.text or "")
        sent = await delivery.send(ctx, op.target_chat_id, delivery.Content(op.text or "", op.content_format,
            op.media_kind, op.file_id), f, kind="pin", thread_id=op.thread_id)
        if sent.result.primary_completed and sent.messages:
            authorization = await operation_authorization(ctx, actor, op)
            pin = await actions.perform("pin", lambda: ctx.bot.pin_chat_message(op.target_chat_id, sent.messages[0].message_id,
                disable_notification=not op.loud)) if authorization.allowed else StepResult("pin", "failed", authorization.code)
            result = result_of(pin).with_steps(*sent.result.steps)
        else:
            result = sent.result
        text = t("gg-done")
    elif op.kind in {"promote", "demote"}:
        from bots.groupguard.administration import change_admin
        result = await change_admin(ctx, actor, op)
        text = t("gg-admin-changed", user=who, action=op.kind)
    elif op.kind == "approve_user":
        await svc.approve(op.target_chat_id, op.target_id or 0, op.reason or None, actor.human_id)
        text = t("gg-approved", user=who, reason=esc(op.reason or "—"))
    elif op.kind in {"unapprove", "unapproveall"}:
        count = await svc.unapprove(op.target_chat_id, op.target_id if op.kind == "unapprove" else None)
        result = result_of(StepResult(op.kind, "applied" if count else "skipped"))
        text = t("gg-unapproved", count=str(count))
    elif op.kind == "setlog":
        step = await actions.notify(ctx, op.log_chat_id or 0, t("gg-log-connected", group=esc(title or "")))
        result = result_of(step)
        if step.completed:
            await svc.update_config(op.target_chat_id, log_chat_id=op.log_chat_id)
            text = t("gg-setlog-done")
    elif op.kind == "unsetlog":
        await svc.update_config(op.target_chat_id, log_chat_id=None)
        text = t("gg-setlog-off")
    elif op.kind == "config":
        updated = await svc.update_config(op.target_chat_id, **json.loads(op.patch_json))
        if 'lang' in json.loads(op.patch_json):
            cfg=updated
            t=actions.group_t(ctx,updated)
        if {"night", "night_start", "night_end", "tz_offset"} & json.loads(op.patch_json).keys():
            from bots.groupguard import jobs
            night_result = await jobs.apply_night(ctx, op.target_chat_id, updated)
            result = result.with_steps(*night_result.steps)
        values = json.loads(op.values_json)
        if op.confirmation == "gg-blocklist-saved":
            values["count"] = str(len(updated.blocklist))
        text = t(op.confirmation, **values)
    elif op.kind == "raid_change":
        from bots.groupguard import raids
        options = json.loads(op.options_json)
        changed = await raids.change(ctx, op.target_chat_id, op.duration_seconds if op.loud else None,
            check_generation="expected_generation" in options, expected_generation=options.get("expected_generation"))
        if changed is None:
            result = result_of(StepResult("raid_change", "skipped", "generation_changed"))
        text = t("gg-setting-saved", setting="antiraid")
    elif op.kind == "policy_change":
        options = json.loads(op.options_json)
        field, delta = options["field"], set(options["values"])
        async with svc.member_session(op.target_chat_id,0):
            current = await svc.config(op.target_chat_id,fresh=True)
            values = getattr(current,field)
            if field == "service_clean_types" and values is None:
                values = ["join","leave"] if current.clean_service else []
            selected = set(values) | delta if op.loud else set(values) - delta
            await svc.update_config(op.target_chat_id,**{field:sorted(selected)})
        text = t("gg-setting-saved",setting=field)
    elif op.kind == 'fed_quiet':
        from bots.groupguard import federations
        try:
            await federations.change_quiet(ctx,actor,op.key,
                json.loads(op.options_json)['expected_generation'],op.loud)
        except federations.FedError as error:
            result=actions.failure(op.kind,str(error))
        text=t('gg-fed-quiet',value=t('gg-on') if op.loud else t('gg-off'))
    elif op.kind.startswith("topic_"):
        from bots.groupguard import topics
        result = await topics.change(ctx,op)
        text = t("gg-topic-changed",topic=str(op.topic_id or ""),action=op.kind)
    elif op.kind == "echo":
        from bots.groupguard import cleanup, delivery
        content = delivery.Content(op.text or "",op.content_format,op.media_kind,op.file_id)
        subject = await perms.fresh_member(ctx,op.target_chat_id,actor.human_id or actor.bot_sender_id or 0)
        fillings = await delivery.fillings(ctx,op.target_chat_id,subject.user if subject else None,raw=content.raw)
        sent = await delivery.send(ctx,op.target_chat_id,content,fillings,kind="echo",
            thread_id=None if cfg.action_topic==1 else cfg.action_topic or op.thread_id)
        result = sent.result
        for message in sent.messages:
            result = result.with_steps(await cleanup.schedule(ctx,op.target_chat_id,message,"action"))
    elif op.kind == "lock_change":
        from bots.groupguard.lock_types import expand
        from bots.groupguard.locks import Policy
        selected_policy = Policy.model_validate_json(op.options_json).checked()
        if selected_policy.silent and (not cfg.silent_actions_allowed or cfg.log_chat_id is None or "automated" not in cfg.log_categories):
            return actions.failure("lock_change","silent_consent_required")
        async with svc.member_session(op.target_chat_id, 0):
            current = await svc.config(op.target_chat_id, fresh=True)
            configured = set(expand(current.locks))
            policies = dict(current.lock_policies)
            if op.loud:
                configured.update(op.keys)
                for name in op.keys:
                    policies[name] = json.loads(op.options_json)
            else:
                configured.difference_update(op.keys)
                for name in op.keys:
                    policies.pop(name,None)
            await svc.update_config(op.target_chat_id, locks=sorted(configured), lock_policies=policies, lock_schema_version=1)
        text = t("gg-locked" if op.loud else "gg-unlocked", types=", ".join(op.keys))
    elif op.kind in {"allowlist_change","allowlist_clear"}:
        async with svc.member_session(op.target_chat_id, 0):
            current = await svc.config(op.target_chat_id, fresh=True)
            entries = list(current.allowlist)
            if op.kind == "allowlist_clear":
                entries=[]
            elif op.loud:
                for entry in json.loads(op.options_json):
                    if entry not in entries:
                        entries.append(entry)
            else:
                entries=[entry for entry in entries if entry not in json.loads(op.options_json)]
            if len(entries)>500:
                result=actions.failure("allowlist_change","limit")
            else:
                await svc.update_config(op.target_chat_id, allowlist=entries)
        text=t("gg-setting-saved",setting="allowlist")
    elif op.kind in {"blocklist_change","blocklist_clear"}:
        from bots.groupguard.blocklist_types import Entry
        from bots.groupguard.settings import GuardSettings
        stg=await ctx.settings.get()
        assert isinstance(stg,GuardSettings)
        async with svc.member_session(op.target_chat_id,0):
            current=await svc.config(op.target_chat_id,fresh=True)
            records={record["key"]:record for record in current.blocklist_entries}
            if op.kind=="blocklist_clear":
                records={}
            elif op.loud:
                for record in json.loads(op.options_json):
                    parsed=Entry.model_validate(record)
                    if parsed.silent and (not current.silent_actions_allowed or current.log_chat_id is None):
                        result=actions.failure("blocklist_change","silent_consent_required")
                        break
                    records[parsed.key]=parsed.model_dump()
            else:
                for record in json.loads(op.options_json):
                    records.pop(record["key"],None)
            if len(records)>stg.max_blocklist:
                result=actions.failure("blocklist_change","limit")
            if result.primary_completed:
                await svc.update_config(op.target_chat_id,blocklist_entries=list(records.values()),
                    blocklist=[record["pattern"] for record in records.values() if record["kind"]=="text"])
        text=t("gg-blocklist-saved",count=str(len(records)))
    elif op.kind == "save":
        from dataclasses import asdict

        from bots.groupguard import repeats
        from bots.groupguard.formatting import parse_controls
        from bots.groupguard.settings import GuardSettings
        stg = await ctx.settings.get()
        assert isinstance(stg, GuardSettings)
        try:
            _, controls = parse_controls(op.text or "", op.item_kind, format=op.content_format)
            if controls.repeat_seconds and ((cfg.private_notes and not controls.noprivate) or actor.human_id is None):
                raise ValueError("repeat_access_invalid")
            async with svc.member_session(op.target_chat_id, 0) as (session, _member):
                items = await svc.save_items(op.target_chat_id, op.item_kind, list(op.keys or (op.key,)), text=op.text,
                    media_kind=op.media_kind, file_id=op.file_id, limit=stg.max_items,
                    content_format=op.content_format, options={**asdict(controls), **json.loads(op.options_json)})
                for item in items:
                    await repeats.replace(ctx, session, item, author_id=actor.human_id,
                        seconds=controls.repeat_seconds, thread_id=op.thread_id)
            text = t(f"gg-{op.item_kind}-saved", key=esc(", ".join(op.keys or (op.key,)).lower()))
        except (LimitReached, ValueError):
            result = actions.failure("save", "limit")
    elif op.kind == "remove":
        removed = await svc.delete_item(op.target_chat_id, op.item_kind, op.key)
        result = result_of(StepResult("remove", "applied" if removed else "skipped"))
        text = t("gg-item-deleted", key=esc(op.key.lower())) if removed else t("gg-item-missing")
    elif op.kind == "removeall":
        async with svc.member_session(op.target_chat_id, 0):
            items = await svc.list_items(op.target_chat_id, op.item_kind)
            for item in items:
                await svc.delete_item(op.target_chat_id, op.item_kind, item.key)
        result = result_of(StepResult("removeall", "applied" if items else "skipped"))
        text = t("gg-items-cleared", count=str(len(items)))
    elif op.kind == "panel":
        from bots.groupguard.handlers.panel import open_panel
        await svc.ensure_chat(op.target_chat_id, op.chat_title)
        opened = await open_panel(ctx, op.target_chat_id, actor.human_id or 0, t)
        result = result_of(StepResult("panel", "applied" if opened else "failed", None if opened else "state_or_send_failed"))
        if opened:
            text = t("gg-panel-sent")
        else:
            url = f"https://t.me/{ctx.username}?start=gs_{op.target_chat_id}"
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t("gg-btn-open-settings"), url=url)]])
            result = result.with_steps(await actions.notify(ctx, op.target_chat_id, t("gg-panel-start-first"), reply_markup=kb))
    if op.item_kind == "filter" and op.kind in {"save", "remove", "removeall"} and result.primary_completed:
        from bots.groupguard.filter_commands import sync
        result = result.with_steps(await sync(ctx, op.target_chat_id))
    if op.kind not in {"warn", "echo"} and not (op.kind == "panel" and not result.primary_completed):
        if text or not result.primary_completed:
            if result.status == "noop":
                result = result.with_steps(await actions.notify(ctx, op.target_chat_id, text))
            else:
                result = await actions.announce(ctx, cfg, op.target_chat_id, title, result, text,
                                                silent=op.silent or (op.kind == "delete" and result.primary_completed),
                                                category="settings" if op.kind in {"config", "setlog", "unsetlog", "save", "remove", "approve_user", "unapprove", "unapproveall", "lock_change", "allowlist_change", "allowlist_clear", "blocklist_change", "blocklist_clear", "raid_change", "fed_quiet"} else "admin",
                                                message_thread_id=op.thread_id)
        elif result.status == "partial":
            result = await actions.announce(ctx, cfg, op.target_chat_id, title, result, "")
    # Anonymous approval identity is private audit data, never the claimed original sender.
    if actor.human_id is not None or authorization.code in {"assumed_anonymous", "bot"}:
        await ctx.audit.record(actor.human_id or 0, "gg_" + op.kind, target=op.target_chat_id,
                               reviewed=reviewed, original_actor=original_actor,
                               actor_kind=actor.kind, bot_sender_id=actor.bot_sender_id, original_bot_id=original_bot_id,
                               assumed_anonymous=authorization.code == "assumed_anonymous",
                               outcome=result.status, primary_completed=result.primary_completed, operation=audit_operation(op),
                               steps=[dict(operation=s.operation, status=s.status, code=s.error_code) for s in result.steps])
    return result


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_reviews")

    @router.callback_query(GgCb.filter(F.action == "approve"))
    async def approve(query: CallbackQuery, callback_data: GgCb) -> None:
        from bots.groupguard.reviews import approve_review
        await approve_review(ctx, query, callback_data.arg, callback_chat=callback_data.chat,
                             callback_user=callback_data.user)

    return router
