# Phase 0B bounded foundation blueprint

This is a proposal for review, not implemented code. The integrated source tree is `7895f72031fd4fac13b4ff280ba04b16c8d5842c`, equal to the supplied reference. The original Phase 0 blueprint is preserved in `history/PHASE_00/ARCHITECTURE.md`.

## Evidence boundaries

**Documented contracts:** reviewer-supplied digest S09 gives precise rights, human verification for anonymous admins, optional assumed admin authority without owner authority, and attributable owner-only actions. S14 requires valid time for temporary aliases and distinguishes manual silence. S49 gates automated silence on creator enablement plus a log channel. S22 puts locks before blocklists. S40 makes connection history convenience rather than authorization. T01 describes current API capabilities and constraints; deployed server support is unobserved.

**Existing code:** `perms.sender_rights` grants creator/all rights to `sender_chat == chat.id`; `admins` caches for 300 seconds; no invalidation callers were found. `Rights` lacks promotion/topic fields. Moderation commands call `setup(right)`; panel `guard/open_panel` checks only generic administration. Temporary aliases share optional parsers and invalid values become reasons/permanent actions. `actions.punish/unmute/unban` return booleans, `delete` suppresses errors, and handlers can announce success/reset warnings on failure. `GuardService.update_config` writes cached JSON wholesale with a 30-second local cache; add/count/reset warnings are separate transactions. CAPTCHA keys lack immutable generation/message identity and expiry can act after a stale read. All ten historical diagnostic observations reproduce after import.

**Imported runtime facts:** `BotModule.throttle_exempt(event) -> bool` defaults false; throttling consults it. New CV/doc modules, AI/file/UI/payment changes and revisions `0008_cvbot -> 0009_doctools` are present. `flooding(..., message_id)` uses message IDs as Redis sorted-set members, addressing equal timestamp collisions but not establishing durable replay protection. Existing `tests/e2e` already exercises real local HTTP gateway/scheduler/workers with scripted Telegram/AI and disposable PostgreSQL/Redis. Reuse it; do not build another harness.

**Proposed hardening:** bounded server-side anonymous reviews, fresh authorization immediately before mutation, typed action outcomes, safe temporary bounds, event deduplication, immutable challenge state and retryable jobs. These choices are ours; receiving a digest does not verify them. **Open policies:** Q01–Q10, particularly threshold/exemption decisions, retention/deletion fields, source grammar defects and deployed API capabilities.

## Bounded subphases and dependencies

| Subphase | Minimum scope | Deferred owning work |
| --- | --- | --- |
| 1A | Attributable actors, exact rights, fresh caller/bot checks, strict temporary parsing, truthful results; adopt in existing commands/panel/callbacks and action callers | Full protection routing, atomic threshold generation, complete challenge lifecycle, future feature tables |
| 1B | GroupGuard-specific protection entry before consuming core handlers, message edits, sender-chat separation, explicit event subscriptions and child parity | Generic replacement dispatcher or platform-wide durable inbox |
| 1C | Atomic config patches, warning/challenge transitions, immutable issued deadlines, bounded lease/retry jobs needed by existing features | Every future federation/content/privacy schema |

Each requires a separate implementation prompt. Continue using `core.sdk.BotContext`, `ctx.bot_id`, `ctx.keys`, existing services, runtime, scheduler and factory lifecycle. Child pause/unload/delete and restart must be acceptance cases in their owning phase. No platform-wide rewrite.

## Exact proposed 1A contracts

Proposed `bots/groupguard/contracts.py` contains frozen typed values; `bots/groupguard/authz.py` contains GroupGuard-only authorization. Keep wrappers in `perms.py` only during deliberate call-site conversion.

```python
ActorKind = Literal["human", "anonymous_group", "channel", "bot", "unknown"]
Right = Literal["change_info", "delete_messages", "restrict_members",
                "pin_messages", "invite_users", "promote_members",
                "manage_topics", "creator"]

@dataclass(frozen=True)
class Actor:
    bot_id: int
    chat_id: int
    kind: ActorKind
    human_id: int | None
    sender_chat_id: int | None
    message_id: int | None
    thread_id: int | None

@dataclass(frozen=True)
class Authorization:
    allowed: bool
    code: Literal["ok", "unattributed", "caller_denied", "bot_denied",
                  "lookup_failed", "wrong_scope", "expired", "replayed"]
    human_id: int | None
    caller_rights: Rights
    bot_rights: Rights

def actor_from_message(ctx: BotContext, message: Message) -> Actor: ...
async def authorize(ctx: BotContext, actor: Actor, *, target_chat_id: int,
                    caller_right: Right, bot_rights: frozenset[Right],
                    review_token: str | None = None) -> Authorization: ...
async def fresh_rights(ctx: BotContext, chat_id: int, user_id: int) -> Rights: ...
```

`Rights` extends current fields with `promote` and `manage_topics`; map Telegram owner/admin membership explicitly. `fresh_rights` uses an uncached Telegram lookup at execution, with bot-admin guarantees respected; any uncertain/failed lookup denies. Cache remains available for display only. Call `/admincache` refresh/invalidate when that feature is implemented; membership updates should invalidate display cache in 1B. Owner-only checks require actual human creator identity. Platform admin, factory owner, another bot, channel sender and Telegram anonymous pseudo-user never imply creator. `actor_from_message` prioritizes `sender_chat`: same-group sender becomes anonymous, another channel becomes channel, never an ordinary human because `from_user` is also present.

Anonymous verification is proposed as a bounded, one-use server-side review. Token points to an immutable request snapshot keyed `ctx.keys("gg", "review", token)`; fields are bot_id, target_chat_id, original_message_id, review_message_id, thread_id, action/arguments digest, required right, issued/expires times and reviewed human ID. Proposed TTL is 120 seconds, a short interaction setting rather than data-retention policy. The button click identifies a real human; recheck their current exact rights and bot capability before atomically claiming the token with Redis GETDEL or a scope-check-and-claim Lua operation. Never claim a replayable callback ID as identity. Execute stored arguments, not callback-provided arbitrary chat/target/action. No migration/table required for this short review. Redis restart loses review and safely requires a new request. The optional `anonadmin on` product setting remains the Phase 2 owner-excluding source contract; it is not silently enabled in 1A.

| Existing adoption point | Caller requirement | Bot capability / behavior |
| --- | --- | --- |
| settings commands, panel lang/locks/config/night callbacks | change_info | Check resulting Telegram action capabilities; pure SQL settings do not need an invented Telegram bot right |
| ban/tban/kick/mute/tmute/unban/unmute/warn/remove/reset warning | restrict_members (current local warning policy retained) | restrict_members for actual sanction; no sanction success on failure |
| del/purge; delete-and-act or manual silent removal | delete_messages, plus restrict_members for sanction | Matching union; report steps independently |
| pin/unpin | pin_messages | pin_messages |
| join-request approval/CAPTCHA approval | invite_users for administrator operation; verified applicant only fulfills own challenge | invite_users; full challenge transition hardening is 1C/Phase4 |
| future promote/demote | promote_members | promote_members; grant caller/bot intersection excluding promotion |
| future topic operations | manage_topics | manage_topics |
| future clear-all/import/reset/joinfed/leavefed/automatic silent enable | attributable creator | Relevant effect capability; no assumed anonymous owner |
| current warning-remove callback | restrict_members with exact bot/chat scope | Fresh authorization; immutable per-warning target is 1C/Phase2 |

Panel callbacks must map every action to its required right and derive bot namespace from `ctx`, not callback text. Current read panel checks may permit an authorized read, but each mutation rechecks precise rights. `gg:close` remains harmless UI closure with caller scope checks. Current commands use one `authorize` path immediately before mutation. Automatic/scheduled action callers use a distinct internal origin with bot capability checks; they never borrow a fictitious human creator. Full event-origin redesign stays in 1B. Existing content, defaults, aliases, branding, night/CAS/AI and inherited private flows must remain compatible.

Proposed parser contracts in `perms.py` or a focused `duration.py`:

```python
@dataclass(frozen=True)
class DurationResult:
    kind: Literal["absent", "valid", "invalid"]
    value: timedelta | None
    reason: str | None

def parse_action_duration(token: str | None, *, required: bool,
                          minimum: timedelta, maximum: timedelta) -> DurationResult: ...
def split_action_args(args: Sequence[str], *, temporary_required: bool) \
        -> tuple[DurationResult, str]: ...
```

Keep seconds/minutes/hours/days/weeks and existing reason parsing. Temporary aliases require a token; missing, malformed, zero or out-of-bounds produces a localized error with **zero sanction API calls**. For ordinary ban/mute, a clearly time-shaped invalid token must error rather than become a reason; ordinary reason-only permanent usage remains explicit. Proposed safe temporary-action bounds are 60 seconds through 365 days, recomputing `until_date` at execution. This deliberately tightens the existing 30-second/366-day endpoints to avoid Telegram rounding/network delays converting a temporary action to permanent; it is a proposed safety deviation requiring the next prompt's review, not an implemented compatibility change or a claimed Rose bound. Module-specific bounds override: CAPTCHA kick5m..1day, flood window uses seconds independently. Test boundaries and ensure no until=None on required temporary operations.

Proposed action result contracts in existing `actions.py`:

```python
@dataclass(frozen=True)
class StepResult:
    operation: str
    status: Literal["applied", "acknowledged", "failed", "skipped"]
    error_code: str | None
    retry_after: int | None

@dataclass(frozen=True)
class ActionResult:
    status: Literal["applied", "partial", "failed", "noop"]
    steps: tuple[StepResult, ...]
    requested_message_ids: tuple[int, ...]
    confirmed_deleted_count: int | None

async def punish(ctx, chat_id, user_id, action, duration) -> ActionResult: ...
async def unmute(ctx, chat_id, user_id) -> ActionResult: ...
async def unban(ctx, chat_id, user_id) -> ActionResult: ...
async def delete(ctx, chat_id, message_id) -> ActionResult: ...
async def log_event(ctx, cfg, chat_title, text) -> StepResult: ...
```

Only successful sanction yields applied. Kick ban-success/unban-failure yields partial and explicitly states the user may still be banned. Bulk-delete acknowledgements never provide fabricated per-ID deleted counts. Manual silence suppresses group acknowledgement, preserves applicable audit attempts, and has independent deletion/sanction/log steps; automated silence gate is a later product feature. Unmute must not invent fully-open permissions after `get_chat` failure: fail truthfully; unrelated restrictive state layering is owning 1C/Phase4 work. Map expected Telegram exceptions to safe user-facing codes; do not log tokens or raw secrets. Retryable status is data for future bounded jobs, not authority to add a generic retry platform in 1A.

Convert command confirmations and `apply_warn`, protection and existing job callers from boolean/ignored results explicitly; never rely on dataclass truthiness. For 1A, warning history reset moves after successful threshold sanction, addressing false success with sequential behavior. Concurrent warning threshold ownership/generation remains 1C and must be named as a residual risk, not claimed fixed by return typing.

## Schema and compatibility boundaries

Current GroupGuard tables remain `gg_chats`, `gg_items`, `gg_warns`, tenant-scoped by bot/chat with the existing item key uniqueness. Baseline migration head is `0009_doctools` after `0008_cvbot`; disposable integration passed upgrade/downgrade/re-upgrade and metadata comparison, not a production migration. **1A requires no SQL migration**, no backfill and no retention job. Redis reviews are additive, short-lived and namespaced. Rollback loses only pending reviews and requires new verification; it does not erase group data.

1C may add a configuration revision/atomic patch and warning action generation, then challenge identity/state/deadline and lease/retry fields as concrete transitions demand. Reserve no revision number until implementation; any additive migration depends on the actual then-current head. Existing JSON fields/unknown data and legacy HTML need compatibility tests. Content media file IDs remain bot-bound; origin/import safeguards belong to owning content/portability phases. Future federation/content/export/privacy tables are designed only when required, not created in Phase1. No approved 7/30/90-day retention, global bans, admin-title operation, federation transfer or mandatory cross-bot sharing follows from this audit.

## Proposed 1A negative acceptance tests

1. Anonymous same-group sender with or without pseudo-user cannot gain creator; foreign channel/bot/unknown actor cannot impersonate a human. A verified current admin with only delete rights cannot mutate settings/restrict/pin. Owner-only actions remain denied to an admin review.
2. Demote caller/revoke bot rights after displaying panel and before callback; mutation denied despite populated300-second cache. API lookup failure denies. Private connected history, platform admin and factory owner give no extra group rights.
3. Review wrong bot/chat/message/thread/action digest/user, expired token and replay fail; one of two simultaneous claims may execute. Redis restart safely invalidates pending review.
4. Each temporary alias missing/malformed/zero/short/overlong duration produces zero ban/restrict calls; valid s/m/h/d/w, reason-only permanent form and safe boundaries remain explicit. Telegram until_date never None for temporary intent.
5. Ban failure yields no success and no warning reset. Kick second-step failure yields partial. Failed default-permission lookup blocks unmute. Bulk delete reports acknowledgements/requested IDs, no fictional deletion count. Failed log step does not erase evidence of the successful sanction.
6. Existing command/panel/callback aliases, Arabic/English text, data/defaults, namespace, child branding and optional protection settings survive. Run focused and full checks; baseline doctools failure remains separately reported unless an independent prompt authorizes its fix.


## Phase 1A cumulative addendum

Implemented Phase 1A contracts are contracts.py, authz.py, perms.py, operations.py, reviews.py, actions.py. Existing manual mutations use uncached Telegram rights sets; short-lived reviews use Redis compare-and-delete Lua; panels bind bot/target/human/message/thread. Read config(fresh=True) at protected execution paths. No table, migration, router precedence or subscription change. See reports/PHASE_01A.md for exact signatures and adoption map.
