# PHASE 0 REPORT — repository audit complete; source inventory blocked

Audit date: **2026-10-12 (Asia/Jakarta)**. No future feature implementation, production refactor/configuration change, live Telegram action, merge or deployment.

## 1. Identity, scope and completeness

Repository: kunkura/TELEGRAMBOTS, `/workspace/TELEGRAMBOTS`; branch `work`; HEAD `e474c59784c47f4055cdc0eab7a74d111a1ff66b`. Initial working tree clean. The supplied reference `d55fc44fe1a63ba5788125c1325d2a855944d5e0` is absent and a read-only fetch failed `upload-pack: not our ref` (exit128). Exact differences cannot be reported; no reset/switch/push was used. Current history includes Group Guard `17b71dc` and factory `44ff18f`, without establishing their relation to the absent reference.

No AGENTS.md or supplied planning/report files were found. Read README and BOT_SDK, DESIGN_SYSTEM, OPERATIONS. Reconstructed equivalent planning/report templates. Inspected all Group Guard modules/handlers/locales/tests, middleware/SDK/routing/subscriptions, factory lifecycle/webhooks/jobs, tenant storage/migrations and test harnesses. No production files were changed; all changed paths are additions under `docs/groupguard-rose/`: FEATURE_MATRIX.csv/.md, BASELINE.md, ARCHITECTURE.md, DECISIONS.md, SOURCE_COVERAGE.md, PLAN.md, REPORT_TEMPLATE.md, reports/PHASE_00.md, evidence/{bots,ruff,mypy,targeted,all,integration,probes}.log, evidence/probes.py.txt, evidence/dependencies.txt, evidence/reference-fetch.log and MANIFEST.sha256. No commit was made. Manifest identifies artifact bytes; reports are planning evidence, not independent certification.

**Source coverage is incomplete.** Both https://missrose.org/docs/ and https://core.telegram.org/bots/api were denied by the environment proxy with CONNECT403, including retry. Zero Rose pages were retrieved. Its page/section denominator, nested/explanation-only sections, indirect commands, aliases/defaults/permissions/private flows/languages/custom clone annotations and relevant functional links are unknown. The block occurred before website responses; do not interpret it as Rose being down. This was not an automatic approval rejection. No network configuration was changed or proxy bypassed.

Official tdlib local Bot API README was read via raw.githubusercontent.com, and installed aiogram schemas/docstrings were inspected. Current official API website and deployed local API capabilities remain unverified. This report cannot establish exhaustive Rose inventory or parity. Every matrix row says Rose source unretrieved; requested-scope rows remain visible.

## 2. Compact full local inventory and requested coverage

Matrix: **201 stable rows**, 20 columns. Local evidence statuses: **6 implemented-and-tested**, **78 existing-but-unverified**, **61 partial**, **56 externally dependent**. No verified Rose behavior is labeled missing because Rose behavior could not be retrieved. Tested means the stated local subset only; every row's Rose verification is unknown. All Group Guard operations apply to standalone/children unless noted; existing factory tests mainly use other templates and do not establish Group Guard child parity.

IDs `GG-CMD-<spelling>` cover all **44 explicit Group Guard slash spellings**, individually:

| Module / phase | Commands, variants, modifiers and current evidence |
|---|---|
| Restriction / P2 | `/ban [target] [duration] [reason]`, `/tban`, `/sban`, `/unban`, `/kick`, `/mute [target] [duration] [reason]`, `/tmute`, `/unmute`. Ban/mute basic rights+duration tested. tban/tmute use the same permissive parser and can become permanent; sban deletes command but skips log/response; kick/unban/unmute semantics otherwise unverified and failure results can be lost. |
| Warnings / P2 | `/warn [target] [reason]`, `/unwarn`, `/rmwarn`, `/resetwarns`, `/warns [target]`, remove-warning button. Sequential threshold ban tested, but failed sanction loses warnings, threshold/add/remove races unprotected and callback targets latest warning rather than warning ID. |
| Message/admin/report/log / P2 | `/purge` reply range (max_purge300, inclusive may301), `/del` reply+command, `/pin [loud\|notify]` default silent, `/unpin` reply or latest, `/report`, `/admin`, `/admins` all reply-report aliases, `/id`, `/setlog <numeric destination>`, `/unsetlog`. Handler presence only; no focused tests. `/admin` also collides with earlier core admin path. |
| Rules/greetings / P3 | `/rules`, `/setrules <text>` or reply (empty clears,3500), `/setwelcome <text>` or reply (3000,enables), `/resetwelcome`. Stored HTML and text-only greeting modes; no complete markup/button/media grammar. Private `/start rules_<chat_id>` exposes stored rules without membership check. |
| Notes / P3 | `/save <name> <text>` or replied media, `/get <name>`, `#name`, `/notes`, `/clear <name>`. Basic save/hashtag retrieval/member refusal tested; other modes/unbounded listing/unverified media incomplete. Names 1–64 Unicode word/hyphen, lowercased; shared note+filter limit150. |
| Filters / P3 | `/filter <word> <text>` or reply, `/filters`, `/stop <word>`. Literal Unicode word boundary matching, first alphabetical match, captions included, slash input ignored. Simple auto-reply tested; phrase/multi-trigger/mode/modifier parity unresolved. |
| Locks / P5 | `/lock <types...\|all>`, `/unlock`, `/locks`; nine kinds: links, invites, forwards, media, stickers, gifs, voice, polls, bots. Default no locks; admins exempt. Links tested. Media=photo/video/document/audio; voice includes video_note; hidden invite links/edits/sender-chat/reactions insufficient. Joining bots only kicked when added by nonadmin. |
| Blocklist / P6 | `/addblock`, `/blocklist` (list without args/add with args), `/rmblock`, `/unblocklist`; comma/newline lowercase literal phrases, first50 inputs, sorted truncation150. Case/boundary deletion/admin exemption tested; advanced grammar/actions/exemptions not sourced. Optional blocklist_warn flag defaultfalse. |
| Settings/night/help / P11/P7 | `/settings` opens private cycling panel; `/start gs_<chat_id>` fallback is shadowed. `/night <start> <end> [offset]` or `off`, fixed UTC offset; night-window calculation tested, restoration unverified/defective. `/help` private, `/start` home and gg_help callback; add-to-group rights and branding. |

Target syntax for moderation: reply first, text mention, observed @username (30-day bot cache), then signed numeric ID. Targets protect bot/admin users in ban/mute/kick/warn. Duration grammar: 1–4 digits plus s/m/h/d/w, 30s–366d; invalid tokens are not errors and become reason/permanent action. Exact Rose target priority, aliases, temporary/silent/delete behavior remain unknown.

`GG-CFG-<field>` covers all **26 group configuration fields/defaults**:

- `lang=None`; `welcome=True`, `welcome_text=""`, `goodbye=False`, `clean_service=True`, `rules=""`, `credit=True`.
- `captcha="button"`, `captcha_minutes=5` (1–60); `cas=True`, `newbie_hours=24` (0–168), `ai_spam=False`.
- `flood_count=6` (0–50,0 disables), `flood_seconds=8` (2–120), `flood_action="mute"`, `action_minutes=60` (1–43200).
- `warn_limit=3` (1–20), `warn_action="ban"`; `locks=[]`, `blocklist=[]`, `blocklist_warn=False`.
- `night=False`, `night_start=23`, `night_end=7` (0–23), `tz_offset=0` (-12..14); `log_chat_id=None`.

`GG-LIMIT-{cas_url,max_purge,max_blocklist,max_items}` preserves bot-wide CAS https://api.cas.chat/check,300,150,150; no explicit range validation. Panel cycles: welcome/clean/goodbye/CAS/AI/night/credit toggles; CAPTCHA button/math/off; minutes5/10/2; flood6/10/4/off; flood action mute/kick/ban; warn3/5/2; warn action ban/mute/kick; auto minutes60/1440/10080/10; newcomer24/72/off; language and individual locks. Panel checks is_admin, not field-specific rights. AI toggle appears only with configured provider; standalone credit hiding requires VIP; child branding follows factory flags.

Other complete **local inventory sets**:

- `GG-LOCK-{links,invites,forwards,media,stickers,gifs,voice,polls,bots}`: nine independently testable detection/exemption rows; only links locally tested.
- `GG-MEDIA-{photo,video,animation,document,audio,voice,sticker,video_note}`: eight saved media transports, all unverified. Store bot-specific file_id; sticker/video_note captions discarded. Cross-bot transfer not implemented or validated.
- `GG-FMT-{first,mention,username,group,id,count}`: six welcome substitutions, escaping except numeric id/count; get_chat_member_count fallback `?`; unverified escaping/HTML-boundary fixtures. Existing HTML may be truncated through tags and must remain compatible during upgrades.
- `GG-EVT-{hashtag,filter}` plus `{join,leave,service,captcha-button,captcha-math,captcha-expiry,join-request,join-request-answer,cas,newbie,ai-spam,flood,night,warning-remove-button,panel,close,group-registration}`: button solve/wrong-user/timeout and flood mute tested; math/request/lifecycle/action failure/concurrency/restart behaviors partial or unverified. CAS and AI live integration externally dependent. Math1..9+1..9/four choices/three attempts; CAPTCHA issued state lives Redis timeout+600; private request verified marker600; newcomer first3 AI checks; flood 7th message within8s triggers mute60m.
- `GG-FOUND-{anonymous,edited,core-precedence,reaction-subscription,config-race,warnings-race,admin-cache,target-resolution,durations,webhook-durability}`: ten foundation rows, partial; concrete evidence below.
- `GG-FACTORY-{namespace,lifecycle,branding,jobs,night-off,features}`: bot_id tables and c<bot_id> Redis namespace, encrypted token lifecycle, factory branding, shared-template jobs/due membership includes bot_id. Generic lifecycle tests exist, Group Guard child enforcement not covered. Standalone admin/lang/vip/broadcast/daily_stats; children admin/lang/broadcast, no VIP. Night/CAPTCHA child recovery defects remain.
- `GG-LANG-{en,ar,ru,es}`: selector en/ar/ru/es, Group Guard translated keys only en/ar; ru/es fall back for Group Guard strings. Existing locale tests verify present bundle keys/variables, not Rose roster/completeness/translation quality. Larger core name registry is not installed language coverage.
- `GG-CORE-{terms,support,lang,admin,cancel,platform,vip}`: inherited core flows. Terms/support/personal language are early routers; admin/cancel are bot/platform admin flows, platform is superadmin, VIP standalone only. Core broadcast/FSM are inherited platform mechanisms rather than verified Rose group echo-broadcast parity.
- `SRC-{rose,api,reference,local-api}`: explicit coverage/reference/current-server verification gates. Local API README retrieved; other requested source verification blocked.

`REQ-P<phase>-<area>` contains **51 unresolved user-request areas**, preserving phase order. Exact commands/modifiers/defaults/permissions cannot be invented. Areas must be decomposed after source access:

| Phase | Source-dependent areas |
|---:|---|
| 2 | admin-listing; promote-demote-title; approvals; warning-modes-and-expiry; report-settings; pin-management; purge-variants; moderation-aliases; logging-types |
| 3 | shared-formatting-entities; button-layout-menus; rules-modes; note-modes; filter-modes; greeting-media-and-goodbye; recurring-notes |
| 4 | captcha-mode-roster; newcomer-persistence-and-joinrequests |
| 5 | full-lock-roster; lock-actions; allowlists; reaction-enforcement |
| 6 | advanced-blocklist-parser; blocklist-action-modes; blocklist-exemptions |
| 7 | flood-modes; raid-detection; raid-policies |
| 8 | connections; disabling; cleaning; topics; echo-broadcast; bot-to-bot-capability-review |
| 9 | federation-create-delete-transfer; federation-roles; federation-chat-membership; federation-discovery-and-notices |
| 10 | federation-bans-and-reasons; federation-subscriptions; federation-enforcement-and-provenance; federation-imports |
| 11 | settings-import-export; reset-authorization; privacy-retention; rose-language-roster; complete-localized-ui; clone-specific-annotations |
| 12 | cumulative-regression; independent-source-review; live-release-checks |

P0 remains the audit/source gate. P1 owns foundations. No table represents a sourced Rose command roster or exhaustive page coverage.

## 3. Reproducible baseline

Actual versions: Python3.12.14, aiogram3.31.0, pytest9.1.1, pytest-asyncio1.4.0, Ruff0.17.0, mypy2.4.0, SQLAlchemy2.1.4, asyncpg0.32.0, redis-py7.4.1, fakeredis2.39.0, Alembic1.20.0; PostgreSQL16.15, Redis7.4.11. Existing `.venv` from repository `pip install -e '.[dev]'`; dependency freeze saved because no lockfile exists.

Working directory `/workspace/TELEGRAMBOTS`:

| Actual command | Exit | Current-run result |
|---|---:|---|
| `.venv/bin/python -m core bots` | 0 | 7 valid bot contracts |
| `.venv/bin/ruff check .` | 0 | Passed |
| `.venv/bin/mypy` | 0 | Passed,210 source files |
| `.venv/bin/pytest -q tests/bots/groupguard tests/bots/factory tests/test_locales.py` | 0 | 32 passed,4.80s |
| `.venv/bin/pytest -q` | 0 | 158 passed,2 skipped,38.01s |
| `TEST_DATABASE_URL=postgresql+asyncpg://bot@127.0.0.1:5432/gg_phase0_audit .venv/bin/pytest -q tests/integration` | 0 | 2 passed,2.97s |
| `PYTHONPATH=/workspace/TELEGRAMBOTS .venv/bin/python /tmp/groupguard-audit/probes.py` | 0 | 10 diagnostics,not pytest tests |
| `pytest -q tests/e2e` | unrun | Directory absent |

Two skips are PostgreSQL integration cases without TEST_DATABASE_URL; both passed when explicitly enabled. Live tests excluded by repository default `-m 'not live'`. No failing/expected-failure baseline tests. Created new disposable `gg_phase0_audit` DB in existing loopback onboarding PostgreSQL container; destructive schema checks ran only there. Used fakeredis/SQLite for ordinary tests/probes; no real Redis flush. Integration migration up/down/model/concurrency checks validate core paths, not Group Guard warning/config races. No live behavior established.

## 4. Findings, severity and evidence

Severity rates potential impact in real groups, not arbitrary forged Telegram identities. R=reproduced with RecordingSession/SQLite/fakeredis; S=static code evidence needing a later targeted regression.

| ID | Severity / evidence | Finding and consequence |
|---|---|---|
| F01 | High,R P01; perms.py90 | Anonymous group sender gets creator/all rights. An anonymous admin lacking a specific right can pass its guard; identity cannot be attributed. This does not mean any member can forge Telegram sender_chat. |
| F02 | High,R P02/P03; module.py45, dispatcher.py81–132 | Edited content unprotected; earlier core command/FSM routing can consume ordinary message before protection. Maintenance/account-ban guards can drop group events before safety policy. Sender-chat user-based early returns/target logic incomplete. |
| F03 | High,S; core/factory/webhooks.py11 + P09 | Reactions omitted from child fixed subscriptions; standalone no observers/subscriptions; child edited subscription exists but no protection handler. SDK supports both reaction types, so no API-impossibility excuse. |
| F04 | High,R P05; service.py54–69 | Cached whole-JSON config writes lose other edits;30s replica staleness. Warnings add/count/reset and remove-last transactions race; thresholds may punish/reset multiple times or lose warnings. |
| F05 | High,R P06; moderation.py32–39 | Warning threshold resets before action; failed ban still announces success and leaves zero warnings. Unban/unmute likewise ignore success; purge count reports submitted IDs, not successful deletions. |
| F06 | High,R P07/P08; welcome.py196–218,283 | CAPTCHA success/expiry can both act on stale reads; expired old callback solves new same-user challenge because no challenge/message/nonce binding. Wrong attempts race; issued mode is read from current config. |
| F07 | High,S; welcome.py232–266, jobs.py75–85 | Join-request buttons have no pending request identity/deadline; verified marker stored before approval and survives error. Child due member removed before runtime lookup; paused/unavailable child loses expiry work. |
| F08 | High,S; perms.py53–88 | Admin cache TTL300; forget_admins unused, membership updates do not invalidate. Revoked privileges can remain usable until cache expiry. Panel only checks is_admin, weaker than command field-specific guards. |
| F09 | High,S; moderation.py76/86/130; P10 | tban/tmute missing/invalid duration can cause permanent action. Current sban omits log as well as response; exact Rose aliases still source-unverified. |
| F10 | Medium,R P04; start.py/group router order | Private gs_ settings fallback is shadowed by earlier generic /start, so user without an existing DM can fail to reach intended panel. |
| F11 | Medium,S; jobs.py39–57/88 | Night restore snapshot expires after24h; stored after closing; child disabled-last-night chat excluded from sweep; permission errors/intervening admin changes can strand or overwrite state. |
| F12 | Medium,S; protect.py97–101 | Newcomer TTL max(config_hours,24), while policy uses only marker existence: configured1h remains restricted24h; optional AI shares lifecycle counter. |
| F13 | Medium,S; service.py136–168/content.py | Item limits count-before-insert race; sorted/truncated blocklist additions may drop prior words; HTML truncation/UTF-16 parsing/content versions untested; long warning reasons exceed PostgreSQL256 varchar while SQLite won't expose it. |
| F14 | Medium,S; factory/serving.py29–47 | Child webhook acknowledges then feeds background task; no durable inbox/idempotent processing boundary. Crash after ACK loses update. Core scheduler's single-flight lock does not repair these multi-step state races. |
| F15 | Compatibility constraint,S; models.py/content.py | Existing HTML and file_ids are stored without version/origin metadata. Bot-scoped rows currently protect local use; planned exports/imports must not assume cross-bot media portability or reinterpret HTML as new formatting. |
| F16 | Coverage gap,S; locales/core i18n/tests | Four-language selector versus two translated Group Guard bundles; no Group Guard child isolation/race/reaction/edit/media/restore coverage. Passing locale keys and generic factory tests cannot certify parity. |

No findings were fixed in this phase.

## 5. Concrete implementation blueprint

**Files/services:** retain existing module/perms/actions/GuardService/handlers/config/jobs/models as integration points. Add actors.py, commands.py, policy.py, a separate content representation module and focused moderation/content/onboarding/federation services as needed. Introduce an opt-in BotModule pre-routing policy/update-requirements hook, empty by default for other bots; share subscriptions across gateway/factory polling/webhooks. Reuse core scheduler to dispatch durable bot jobs rather than inventing a new unbounded runner.

**Contracts:** TenantScope(actual bot_id), ChatScope(tenant,chat_id,optional thread), Actor(kind user/anonymous_group/sender_chat/bot/system, attributable identity/proof), Target(kind,id,provenance), CommandSpec(name,aliases,typed parser,actor/bot rights,chat types,destructive flag,connection/update requirements,response/log/delete policy), ParsedCommand, ProtectionDecision, ActionPlan and ActionResult. Results distinguish applied/already applied/denied/unsupported/retryable/final/partial. Strict temporary parser rejects missing/out-of-bounds duration before mutation; unknown action never defaults to ban.

**Authority:** child owner manages factory only; actual current group rights authorize moderation; federation roles are another scope. Anonymous group actor gets no invented creator powers; proposed privileged flow uses identifiable current-right confirmation bound to tenant/chat/action/target/nonce/message/expiry. This UX proposal requires later review. Cache invalidation is event-driven and privileged authorization fails closed; sender-chat targets use correct method/capability, with current wider effects verified. UTF-16 entities and observed username provenance prevent mistaken target selection.

**Precedence:** normalize messages/edits/sender chats/reactions/membership/requests/callbacks. Opt-in protection precedes core and module handlers, preserving payment correctness/unrelated bots. Keep legacy order flood→locks→blocklist→newcomer→AI, joins handled as lifecycle and verified admin exemptions per policy. Decide sourced approvals/raid/federation exemptions explicitly. Edits re-evaluate content without accidental flood recounting; aggregate reactions do not invent user identity. Topic routing does not turn group-wide bans into topic-only actions.

**Schema/indexes/tenants:** additive Alembic migration; preserve existing gg_chats(bot_id,chat_id), gg_items unique(bot_id,chat_id,kind,key), gg_warns and bot cascade. Add config/content versions and durable revision; warning_state PK(bot_id,chat_id,user_id), warning source-update/generation/expiry, approvals, challenges with unique pending lifecycle/deadline index, content triggers/allowlist entries, connections grants, unique(bot_id,update_id) inbox, action outbox/jobs due/status/lease/fencing, scoped audit/import batches, federation roles/membership/subscriptions/bans/enforcement provenance tables. Composite tenant/chat FKs after reconciliation; indexes lead with tenant for local queries. Shared template due index contains actual bot_id; never use template/owner alone as tenant.

**Atomicity/cache/jobs:** config field patches under row lock/revision-CAS, immutable cache snapshots, durable revision/outbox invalidation (pubsub acceleration only). Serialize warnings per member, dedup source action, sanction generation exactly once, preserve history on failure and remove immutable warning IDs. Serialize item quotas. CAPTCHA atomic pending→passed/failed/expired/cancelled; issued mode/answer/tries/deadline/nonce/prompt/message bound to actor+lifecycle. Persist join request contact window and approval result before verified status. Durable leased jobs ack only after recorded result, paused child retained; night restore swept independently of enabled config, survives restart and records baseline permissions. Separate newcomer expiry from AI count.

**Compatibility/content:** existing rows marked legacy profile/content-v1 HTML; never reinterpret as new markup. Add V2 entity/button/placeholder AST; validate rendered lengths and escaping, preserving every current media kind. Store origin_bot_id/file_unique_id and optional recoverable artifact; cross-bot import needs target reupload/transport or visible unrecoverable-media choice, never token/file_id sharing. Keep all26 current defaults, configured limits300/150/150, UI/night/CAS/optional AI/newcomer/branding; new Rose defaults explicit opt-in. Existing authorization/race failures are documented corrections, not defaults to preserve.

**Federations:** own service, proposed default bot-scoped namespace; any platform cross-bot sharing requires explicit publisher/subscriber group consent before P9. Owner/admin/transfer/delete authorization, directed subscription graph with cycle/fanout limits, immutable issuer/source-ban/generation/reason/path provenance. Applied enforcement contributions prevent unfederating/unbanning one source from undoing manual/other-source bans. Check authority on enqueue and execution; staged imports with preview+digest+nonce+schema/ownership/size validation and reconciliation. No Rose private-network/data entitlement.

**Privacy/locales/authorization:** proposed reviewable retention: completed raw inbox7d, challenge answer deleted on completion/outcome<=7d, technical action detail30d, moderation reason90d unless active provenance needs longer. These are not sourced Rose rules or applied settings. Tenant-scoped export/delete handles active sanctions/backups; redact credentials/unnecessary bodies. Destructive reset/clear/import/federation transfer/delete needs current scoped rights and expiring confirmation bound to preview/digest; log destination consent is explicit. Current en/ar coverage vs en/ar/ru/es selection remains visible; add actual sourced roster with dynamic-key/RTL/escaping checks and human translation review.

**API verification:** aiogram3.31 supports reaction types and permissions including can_react_to_messages, sender-chat ban/unban, promote/title, bulk delete/unpin-all/topic APIs and independent permission flags. Installed docs note explicit reaction subscriptions/admin, restriction30s–366d boundaries, delete <=100 IDs/48h, join-contact5m and invite rights. Official tdlib README establishes local2000MB uploads/unlimited downloads/local paths/webhooks, not deployed server or bot-to-bot semantics. Never declare reactions/topics/bot-to-bot/media transport impossible from older assumptions.

**Verification boundary:** RecordingSession fixtures validate decisions/API calls, not real delivery. Later PostgreSQL row-race/migration data tests and disposable Redis duplicates/restarts must supplement them. Actual reaction identities, bot-to-bot delivery, topic rights, request contact window, cross-bot media and pinned local server need later explicitly authorized test bots/groups; no such actions here. P12 requires cumulative regressions and independent every-section source review.

## 6. Outstanding gates and precise next prompt

Every incomplete item remains open: (1) entire Rose crawl/section/alias/default/private/indirect/language/clone coverage; (2) current official API website; (3) supplied reference diff; (4) actual local server version; (5) exact temporary/silent/exemption semantics; (6) anonymous privileged confirmation UX; (7) federation scope/trust; (8) legacy HTML/media import recovery; (9) destructive authorization/retention/log consent; (10) Rose language roster/human translation; (11) absent e2e and Group Guard child/concurrency/restart/event/media coverage; (12) all F01–F16 defects/constraints and51 roadmap source areas.

To finish Phase 0's source gate, provide readable public destinations missrose.org/core.telegram.org or complete dated snapshots, plus accessible reference commit/patch. No additional Telegram secret is needed for source/mock work. Do not represent inaccessible coverage as completed.

Recommended next instruction after evidence review: **Phase1 only**, in small actor/parser, routing/subscriptions, atomic/compatibility batches. If source inventory remains blocked, explicitly authorize only bounded local foundations; do not infer Rose alias/UI semantics. Acceptance must include:

1. User/admin/owner/bot/anonymous/external sender-chat identities; child owner cannot substitute for group rights; demotion/current bot-right failures deny mutation; entity/target correctness.
2. Temporary commands never become permanent for absent/invalid/10s/out-of-range duration; explicit silence/delete/log modes and @bot/whitespace/reason variants.
3. Protection before `/terms`, `/lang`, group/platform `/admin`, FSM and bot paths; text/media/edits/sender_chat; agreed standalone-child polling/webhook event sets. Preserve payments/unrelated modules; actual reaction feature P5.
4. PostgreSQL concurrent config patches preserve both values; stale cache/revision/missed pubsub tests; warning threshold/duplicate/remove/reset/failure generations cannot lose history or falsely announce success.
5. Atomic challenge foundation prevents simultaneous success/expiry, lost wrong attempts, old-message/new-join replay and mode-change bypass; unavailable child due work preserved. New CAPTCHA mode roster P4.
6. Two children + standalone same-group isolation; existing defaults/limits/HTML/media/UI/branding preserved by additive migration fixtures and up/down checks.
7. All original baseline checks plus meaningful new phase regressions; inline evidence and open gates. No merge/deploy/live Telegram implied.

Stopped after Phase 0. Awaiting the reviewer's next prompt.
