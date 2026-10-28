# Phase 0 decisions and unresolved work

No production decisions are applied. This records proposed implementation choices and their gates.

## Decided for the audit

1. Phase 0 only; documentation and audit evidence are the only checkout changes. No new feature implementation, production refactor/configuration, live Telegram action, merge or deploy.
2. Keep the actual checkout/HEAD. Missing reference cannot justify a reset. Source access failure cannot justify invented source URLs/defaults or exhaustive coverage claims.
3. Matrix repository evidence is separate from Rose verification; every Rose status is unretrieved. User-request scope rows must later be decomposed into individually sourced behaviors. Keep stable semantic IDs as the inventory expands.
4. Preserve standalone and factory behavior/data/UI/limits, night/CAS/AI/newcomer protections and branding. New profile defaults are opt-in; fix security/reliability defects explicitly, not by changing all live-group defaults.
5. Use actual bot_id for local tenant scope. Child owner, group authority and federation role are distinct. Federations are our service, not Rose network access.
6. Current SDK supports reactions, sender-chat bans and topic APIs; do not call them impossible. Official current semantics and deployed local server remain unverified.
7. Keep phases 0–12. Phase 1 can be delivered as three reviewable batches: actor/parser; routing/subscription; atomic state/compatibility foundations. These are recommendations only.

## Provisional phase ownership

| Phase | Scope and dependencies |
|---:|---|
| 0 | Exhaustive source inventory, local audit, baseline, blueprint; source/reference blockers still open |
| 1 | Permissions/actor/target model, parser, event precedence/update subscriptions, atomic state/idempotency, legacy profile/tenant foundations |
| 2 | Manual moderation/admins/approvals/warnings/reports/pins/purges/logging; action and actor contracts |
| 3 | Shared formatting/rules/notes/filters/greetings/buttons/recurring notes; V1/V2 content and durable jobs |
| 4 | CAPTCHA/newcomer and private request lifecycle; atomic challenge/jobs and legacy protections |
| 5 | Full sourced locks/allowlists/reactions; normalized event coverage and capability checks |
| 6 | Advanced blocklists; shared matching/action/exemption contracts |
| 7 | Flood/raids; durable policy counters and restored night/newbie legacy behavior |
| 8 | Connections/disabling/cleaning/topics/echo-broadcast/bot-to-bot review; current API verification |
| 9 | Federation management, namespace/ownership/roles/chat trust; explicit scope decision |
| 10 | Federation bans/subscriptions/enforcement/imports; provenance/contribution model |
| 11 | Settings import/export/reset/privacy/locales/complete UI; review/retention and source roster |
| 12 | Cumulative release candidate, independent source review, authorized live checks; every earlier phase gate |

## Required open questions / dependencies

- **Q01 Source access:** missrose.org root and official core.telegram.org reference denied by proxy. Need readable public destinations or complete dated source snapshots including nested functional pages, explanation-only sections, tables/variants/aliases/defaults, indirect commands, private flows, languages and custom-clone annotations. Page denominator remains unknown.
- **Q02 Reference:** supplied d55fc44… cannot be read or fetched. Need available commit/patch; exact before/after comparison remains unperformed.
- **Q03 API deployment:** actual local Bot API image/version unknown and no local server run. Latest Compose image is not a pinned/version-tested deployment. No impossibility claim for reaction permissions, bot-to-bot operations, sender chats or topics before current official review.
- **Q04 Semantics:** exact Rose temporary/silent/delete aliases, default sanction durations, invalid input behavior, report/admin listing distinctions, exemptions/approvals, content modes/modifiers and defaults are unknown. Current local syntax is evidence only.
- **Q05 Anonymous authority:** recommend identifiable right-bearing confirmation for privileged anonymous commands; exact Rose private confirmation mechanism unknown. Reviewer must approve product behavior before changing authorized command UX.
- **Q06 Federation scope:** default per-bot namespace proposed; optional cross-bot platform namespace needs explicit publishing/subscribing trust and consent. Rose public docs cannot grant private network/data access.
- **Q07 Content migration/media:** define supported export transport, unrecoverable media choices and legacy HTML preservation; file_ids treated as bot-bound pending official sending-files review. No silent data loss/reinterpretation.
- **Q08 Destructive UX:** reset/all-clear/import/owner transfer/federation delete require explicit scope+digest preview, current rights and expiring nonce; independent review cannot certify unseen implementation.
- **Q09 Retention/privacy:** exact policies are proposals; define erasure versus active moderation provenance, consent for log destinations and backup handling. Avoid storing complete message content by default.
- **Q10 Locales:** Rose language roster unknown; en/ar Group Guard versus en/ar/ru/es selector distinction explicit. Key parity does not provide translation review.
- **Q11 Verification:** no e2e suite exists. Generic factory tests do not test Group Guard child behavior. Add meaningful phase-specific tests later, including real PostgreSQL races and disposable Redis restarts; live API checks require separate explicit authorization.
- **Q12 Existing defects:** warning/config/CAPTCHA races, old-button replay, earlier-router bypass, stale admin cache, private gs_ shadow, night restore and newcomer duration defects need prioritized regression coverage. No fixes in this phase.

## Recommended Phase 1 acceptance gates

Do not start Phase 1 in this task. Next prompt should first unblock source/reference evidence or explicitly accept a bounded foundations task while source inventory remains incomplete.

1. Identifiable member/admin/owner/bot/anonymous-group/external sender-chat matrix: no invented creator privilege; owner != group admin; revoked rights stop privileged mutation. Targets include replies, text mentions with UTF-16 offsets, usernames, IDs and sender chats; no negative ID as user by accident.
2. Strict parser metadata for temporary/silent aliases. Absent/invalid/10s/oversized durations must never trigger permanent punishment in a temporary-only command. Test command @bot suffix, captions, whitespace/reasons and action log/delete/notify modes; exact Rose spellings deferred to sources.
3. All group content traverses protection before core/bot handlers and FSM inputs; verify `/terms`, `/lang`, both platform and group `/admin`, normal text/media, sender_chat and edited_message. Payments and unrelated bots remain functional. Reaction update subscription sets agree for standalone/children polling/webhooks; no feature reaction enforcement until phase 5.
4. Tenant/row locking and config field patches: two simultaneous edits survive across two service instances; stale revisions conflict/retry explicitly; cache invalidation survives missed pubsub. Warning add/remove/reset threshold generation is idempotent under concurrent PostgreSQL transactions, error results cannot announce success; remove-button targets one immutable warning.
5. Atomic challenge transition foundation: wrong tries, success/expiry/leaving/rejoining/mode changes/duplicate callbacks cannot both release and kick or reuse prior challenge; paused child jobs persist. Full new CAPTCHA variants belong to phase 4.
6. Versioned legacy fixtures prove unchanged gg_chats defaults, notes HTML/media, indexes/tenant isolation and existing limits/UI/branding; additive migration with downgrade/upgrade data evidence, no unrelated source/config churn. Use two child bot IDs and standalone in the same group for every state test.
7. Run all baseline commands plus new phase-specific negative/concurrency tests. Report exact outcomes and any inaccessible source/live check; independent reviewer sees inline report. No deployment/merge/live Telegram without later instruction.
