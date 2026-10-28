# Proposed implementation blueprint — not implemented

The source inventory is blocked. This blueprint proposes contracts for the requested modules; exact Rose syntax/defaults/exemptions remain gated by the source ledger. Extend the existing Group Guard module/template, preserve core platform contracts, and make changes only in later authorized phases. Keep the provisional phases 0–12; add small acceptance batches inside phases rather than starting new architectural subsystems without evidence.

## Minimal seams and files

Retain `module.py`, `perms.py`, `actions.py`, `service.py`, `protect.py`, `chatconfig.py`, `jobs.py`, `models.py`, existing handlers/locales and factory lifecycle. Add focused modules when needed:

- `actors.py`: immutable actor/target classifications and proof of rights. Keep `perms.py` as facade during migration.
- `commands.py`: registry and parser of explicit command spellings, typed durations, argument/mention offsets, flags, capability/permission metadata and connection eligibility. Avoid a generic plugin framework.
- `policy.py`: event normalization, exemptions and ordered protection decisions; preserve legacy protections as explicit policies.
- `content.py` (separate from handlers/content.py): versioned content representation/rendering and validated entity/button parsing. Never reinterpret saved HTML as new markup syntax.
- `services/moderation.py`, `services/content.py`, `services/onboarding.py`: transaction boundaries for existing operations. Split GuardService only when needed; retain compatibility facade.
- `services/federations.py`: own federation service and authorization, separate from Rose's inaccessible private infrastructure.
- `jobs.py` backed by durable jobs/outbox tables; reuse core scheduler as a bounded dispatcher.
- Narrow opt-in `BotModule` protection/update-requirement hook in `core/sdk/module.py`, integrated in `core/runtime/dispatcher.py` and factory subscriptions; default empty hook preserves all other bots. Do not move payment guards globally without module-specific tests.

## Public contracts

Proposed Python-level signatures, not current implementations:

```python
TenantScope(bot_id: int)  # always actual Telegram bot id; not owner id/template name
ChatScope(tenant: TenantScope, chat_id: int, thread_id: int | None)
Actor(kind: user | anonymous_group | sender_chat | bot | system,
      user_id: int | None, sender_chat_id: int | None, proof: ActorProof | None)
Target(kind: user | sender_chat, id: int, provenance: reply | mention | observed | explicit)
CommandSpec(name, aliases, parser, caller_rights, bot_rights, chat_types,
            destructive, connection_allowed, update_types, result_visibility)
ParsedCommand(spec_id, target, duration, reason, flags, source_message_id)
authorize(scope, actor, required_rights, target=None) -> AuthorizationDecision
evaluate(event: GuardEvent, snapshot: PolicySnapshot) -> ProtectionDecision
execute(ActionPlan(scope, actor, target, action, until, delete_ids,
                   notify, reason, provenance, idempotency_key)) -> ActionResult
patch_config(scope, expected_revision, field_patch, actor) -> VersionedConfig
warn(scope, user_id, actor, reason, source_update_id) -> WarningTransition
transition_challenge(scope, challenge_id, actor, event) -> ChallengeTransition
render(content: ContentV2, scope, actor, variables) -> OutgoingMessage
```

Results distinguish applied, already-applied, denied, unsupported, retryable failure, final failure, and partial action. Kick is two remote steps; never report success when unban failed. Each action is tenant/chat scoped, audited with attributable actor or explicitly unknown anonymous origin, and guarded by bot capabilities. Reject invalid temporary durations before mutation. Command alias metadata controls silence, deletion, reason and log behavior independently. No string fallback to permanent punishment. Avoid an `else => ban` primitive; unknown action is validation error.

## Actor and permission model

Telegram group rights, platform/child ownership and federation roles are separate authorities. Child ownership grants factory management only, never arbitrary group moderation. Anonymous sender_chat==group proves an anonymous group origin, not identifiable creator status or each admin right. Proposed default: read-only commands allowed; destructive/configuration actions require a short-lived action-specific confirmation by an identifiable currently authorized administrator, bound to tenant/chat/command/target/message/nonce. This intentionally removes unsupported privilege escalation; document the correction and preserve ordinary authorized admin flows. External sender-chat/channel actors get no user-admin inheritance; legitimate linked-channel automatic forwards need explicit policy, not blanket exemption. Bot identities are classified separately and any bot-to-bot feature must be checked against the current API before exclusion.

For every write, resolve current required actor rights and bot rights. Invalidate administrator cache on relevant membership/rights events; privileged operations must fail closed on unverified/revoked rights. Reads may use short revisioned cache. Targets cannot accidentally resolve anonymous pseudo-users; username mapping is bot scoped, time bounded and carries observation provenance. Honor UTF-16 Telegram entity offsets and distinguish captions/replies/channels. Promotion checks actor owner/promote authority, bot promote rights, target state and permission subset. Exact Rose admin/approval semantics await docs.

## Event precedence and exemptions

Normalize message, edited_message, sender-chat content, reaction updates, chat_member, my_chat_member, join_request and callback events before handler selection. Opt-in moderation protection must run before all core and bot command handlers, including `/terms`, `/lang`, `/admin` and FSM routes. Payment processing must remain unblocked and unrelated bots unchanged. Maintenance/platform account bans must not silently disable safety processing for group content; document a deliberate operational policy. Subscription sets derive from the same module contract for standalone/child polling/webhooks; future reactions require both reaction types explicitly.

Preserve current legacy order: joins/leaves use lifecycle processing; verified admins are exempt from content protection; flood -> locks -> blocklist -> newcomer links -> optional AI -> commands/notes/filters. Add proposed raid/federation checks with explicit precedence after source review; never assume approvals exempt every module. Store per-module exemption decisions. For edits, re-evaluate content and deduplicate by message+edit version; do not count edits as new flood messages unless sourced rules require it. Anonymous aggregate reactions lack a per-user actor; no inferred user sanctions. Sender-chat restrictions use supported sender-chat methods with documented wider effects and explicit authorization. Command disabling/cleaning happens after protection and authorization. Topics enter scope for routing/content, while chat-wide permissions remain chat-wide; do not mistakenly scope a ban to a topic.

## Persistence, schema and isolation

Additive Alembic revisions only; preserve `gg_chats`, `gg_warns`, `gg_items`, their data and unique keys. Every local table/query/index/cache/idempotency key includes bot_id; existing child slugs c<id> remain. Foreign keys to bots retain cascade lifecycle. Composite chat foreign keys should use (bot_id, chat_id) where a guarded chat row exists, with explicit data reconciliation before enforcement. Child template aggregates may index by template, but members contain immutable bot_id and never authorize cross-child reads.

Proposed staged schema:

| Table/addition | Scope, constraints and purpose |
|---|---|
| gg_chats additions | config_version, revision bigint, compatibility_profile; indexes bot_id/active/night preserved |
| gg_items additions | content_version, entities/buttons/content JSON, origin_bot_id, file_unique_id, topic policy; old text/media_kind/file_id retained |
| gg_warning_state | PK bot_id/chat_id/user_id, revision/threshold generation; lock row for add/remove/reset decisions |
| gg_warns additions | immutable warning id, source_update_id/action generation, expiry/resolution; unique tenant source identity; expiry index |
| gg_approvals | PK bot_id/chat_id/actor_kind/actor_id; module-specific flags/provenance |
| gg_challenges | challenge UUID; bot_id/chat_id/user_id, request generation/mode/prompt-chat/message, deadline, tries, state/revision; unique current pending lifecycle; due index state/deadline |
| gg_content_triggers | tenant/chat/kind/normalized key/topic; deterministic priority/action; preserve old unique identity |
| gg_rules/allowlist entries | tenant/chat/module/kind/value; canonical matching version, action and reason; migration from JSON lists |
| gg_connections | bot_id/user_id/chat_id authorization grant, nonce/expiry; do not reuse child ownership |
| gg_event_inbox | unique bot_id/update_id; payload retention bounded; lease/status/retry and persisted acknowledgement boundary |
| gg_action_outbox/jobs | tenant/action_id and source key; payload/status/deadline/attempt/lease/fencing token; indexes status/due and tenant/chat |
| gg_audit | tenant/action/provenance/actor/target/result timestamps, immutable minimal history; reuse core audit where fields suffice |
| gg_federations | explicit namespace/service_scope, UUID, owner, revision; no implicit cross-bot scope |
| gg_fed_roles/members/subscriptions | federation/user role; tenant/chat membership; directed source->subscriber edge, cycle/limits checks; unique edges |
| gg_fed_bans | federation/actor ID, issuer/reason/evidence, generation/status; immutable provenance |
| gg_fed_enforcements | bot_id/chat_id/user_id/source_fed_ban/generation, desired/applied states; dedup key and reconciliation index |
| gg_import_batches | tenant/requester/digest/schema version/preview/confirmation nonce/result; staged all-or-bounded transaction |

Warnings: acquire member state row lock, insert idempotently, count active warnings and transition threshold once; queue sanction in the same transaction. Retain history until action result known; failed actions cannot announce success or silently discard warnings. Warning removal uses immutable warning id; duplicate callbacks do not remove newly issued warnings. Concurrency tests use real PostgreSQL, not SQLite evidence.

Config: field patches under row lock or revision compare-and-swap; never whole stale JSON replacement. Enforce item/blocklist limits inside serialized transaction so concurrent saves cannot exceed limits. Revisioned caches plus transaction outbox invalidations; pubsub accelerates refresh but is not correctness. Reconnect/missed invalidation compares durable revision; no 30-second stale authorization. Cache objects are immutable snapshots. Limit/history queries remain bot scoped.

## Durable onboarding and jobs

CAPTCHA state stores issued mode/answer and challenge generation; bind callback to intended actor, tenant, group, prompt chat/message, nonce, deadline and lifecycle. Atomic pending->passed/failed/expired/cancelled transition determines a single winner. Wrong-answer increments atomic; old challenge cannot solve new join. Queue remote action after state transition and reconcile retry outcomes. Private join requests persist their Telegram contact window, approval deadline and nonce; write verified status only after confirmed approve (or record pending approval and reconcile), not before remote call. No race/replay due to current cfg.captcha changes. Retain denied/expired outcome briefly for explainable callbacks; no permanent answer storage.

Core scheduler already supplies Redis single-flight token release/timeouts/backoff, but that does not make multi-step bot jobs atomic. Durable due jobs are claimed with lease/fencing and acked after durable result; paused/unavailable child does not lose a job. Night restore state must be durable and swept independently of current night=true config, including children whose last night config is disabled. Restore recorded baseline, reconcile external permission changes, and never overwrite a later administrator change silently. Persist newcomer joined_at/expiry independently from the optional AI counter; cfg values below 24h must actually expire as promised. Recurring notes/raid actions/federation enforcement reuse bounded durable worker batches, leases/retries/backpressure and restart acceptance tests.

## Content and compatible upgrades

Set existing rows to `content_version=1`/`legacy_html`: deliver existing saved HTML/media as before; never parse them as new markdown/buttons. V2 stores source text with UTF-16 entities, explicit normalized button rows/URL/deep-link payloads and validated placeholders. Validate source length and resulting Telegram text/caption/button limits; truncation cannot bisect entities/HTML. Round-trip all eight current saved media kinds plus sourced new variants; sticker/video_note captions need explicitly defined handling. Invalid data goes to a visible repair path, not silent loss. HTML is rendered by trusted serializer with escaping; never interpolate raw untrusted names or configuration strings into markup.

Each Telegram file_id retains origin_bot_id; cannot assume a file_id works in another bot, even on local API. Store file_unique_id for identification, not sending, and optional tenant-owned recoverable media artifact under retention/quota. Cross-child imports validate ownership and require supported reupload/copy transport, deriving a fresh target file_id; otherwise preview reports unrecoverable media and requires explicit choice. No token sharing. Export secrets/remote IDs safely; content import cannot carry executable code, arbitrary URLs fetched server-side or cross-tenant authority.

Preserve all live-group legacy defaults: welcome on, goodbye off, service cleaning on, button CAPTCHA 5m, CAS on, newcomer 24h, AI off, 6/8s flood with mute60m, warn3/permanent ban, no locks/blocklist, night off23–07 UTC+0, credit on, no log, default language. Absent new fields use compatibility_profile=legacy rather than changed Rose defaults. New Rose-profile settings are explicit, reviewable opt-in; no global reset/reinterpretation. Preserve configured limits max_purge300/max_blocklist150/max_items150, UI and factory branding. Correct confirmed authorization/race bugs with documented bounded behavior changes and regression fixtures rather than treating unsafe outcomes as stable defaults.

## Federation trust and provenance

Federations are hosted by this service. Rose private data/network/subscriptions are unavailable unless separately authorized; never imply interoperability. Proposed default namespace isolates each bot's federations. If cross-child/standalone sharing is required, explicitly opt into a platform federation namespace with publisher-owner and subscriber chat-admin consent; model identities with immutable namespace+UUID, never owner id alone. Exact scope is an open decision before phase 9.

Owner/admin roles enforce each management action; owner transfer/delete/subscription/import require nonce-bound confirmation and renewed rights. Directed subscriptions reject cycles and bound fanout/depth. Publisher bans retain issuer federation, original actor/reason, source ban id/generation and subscriber path. Removing one federated source must not undo manual bans or another active source. Enforcement records source contributions; unban only when no active source remains and this service owns the corresponding restriction. Imports are staged with schema/size/ownership validation, preview/digest, dedup/provenance and rollback plan; no autoimport into live groups. Authorization is checked at enqueue and execution; revoked trust stops future actions and triggers reconciliation. Failure/deletion policies preserve provenance and do not implicitly unban all groups.

## Retention, privacy, locales and verification

Proposed defaults for review: raw event inbox payload 7 days after completion; challenge answers removed on completion and outcome metadata <=7 days; technical action retry/audit detail 30 days; moderation/federation reasons 90 days unless active sanction legally/operationally requires longer. These are design proposals, not Rose policy or changed production settings. Make retention bounded/configurable; support tenant-scoped export/delete with explicit exceptions for active safety provenance; redact tokens, unnecessary message bodies and personal data from logs. Document that username cache currently lasts 30 days and core membership/warning content can persist indefinitely; backup retention alone is not erasure. No external log destination is enabled without source and destination authorization.

Translation roster: current core selector en/ar/ru/es, Group Guard en/ar only; `LANGUAGES` registry lists more names without bundles. Rose roster unknown. Add every sourced language incrementally, with key/variable coverage, dynamic-key render tests, RTL/escaping and qualified human review; default fallback remains documented. Selector tests cannot certify language quality or feature parity.

Mocked verification: full Dispatcher feed_update fixtures for all actor/event types, recording API success/denial/partial failures, fake clock, forged/stale callback fixtures, two children and standalone, PostgreSQL concurrency/schema migrations/rollback, dedicated Redis duplicate/durable restart tests. Live verification only later with explicit test-group/bot authorization; permission degradation, reactions, topics, user-chat window, media cross-bot transport, bot-to-bot semantics and exact local API version need that boundary. Phase 12 requires cumulative regression and independent comparison against every source section; green current tests are not release parity certification.
