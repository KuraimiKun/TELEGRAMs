# Channel Manager compatibility and release matrix

Recorded 29 October 2026. This matrix distinguishes repository tests from Telegram/client observations. The user explicitly skipped the live canary because no bot token exists yet. No native result below is claimed from a recorded API call.

## Environment

| Component | Evidence |
|---|---|
| Python | 3.12.4 in the local virtual environment |
| aiogram | 3.31.0; supported native structures exercised through `RecordingSession` |
| SQLAlchemy | 2.1.6 |
| PostgreSQL | 16.15, checksum-verified official source, disposable loopback instance |
| Redis | 7.4.12, checksum-verified official source, disposable loopback instance |
| Compose | 2.38.1; profile configuration validated using synthetic values and no service env-file resolution |
| Local Bot API candidate | `aiogram/telegram-bot-api:10.3`, manifest `sha256:5d568e2ff798ccda6a727feb5d1c7f8ef79d71f6ee51aae7dc6f9e748b5e703e`; registry metadata inspected, container/runtime and live verification deferred |

The PostgreSQL/Redis major versions match production, but the WSL builds are not a claim of Alpine container equivalence. Docker Desktop's engine was stopped; existing containers were not started. Compose now requires an explicit Bot API image, and the offline preflight rejects mutable image tags as release configuration.

The Telegram schema documents Bot API 10.3, including newer rich/ephemeral features. This implementation uses the conservative supported subset and private fallback below. [Telegram Bot API](https://core.telegram.org/bots/api), [image maintainer](https://github.com/aiogram/telegram-bot-api).

## Capability matrix

| Capability | Automated evidence | Supported contract / fallback | Native status |
|---|---|---|---|
| Channel connection and live roles | Native/virtual/outsider, stale callback, bot removal, grantor ceilings, two channels/children | Saved roles are hints; check current role and scoped grant at sensitive boundaries | Deferred |
| Manual channel edits | Auto-complete/manual-source fixtures, version and output ownership | Adopt only observed source messages; stricter native edit/delete authority remains | Deferred |
| Text, formatting and emoji | HTML/Markdown subsets, native entities, UTF-16 boundaries, Arabic locale fixtures | Reject unsupported markup/entities before queueing | Deferred |
| Buttons and voting | Links, copy, callbacks, membership gates, votes, generation invalidation | Structured supported button types only; no promise of every newer Telegram style | Deferred |
| Single-media post/edit | Photo/video/animation/document, caption limits, edit follow-up separation | Same sender's file IDs; changing sent media to plain text requires a new draft | Deferred |
| Albums | Source collection, ordering, partial collection, loop/edit cases | Source photo/video album handling; album composition stays outside the private composer | Deferred |
| Caption position and rich rendering | Canonical request construction/validation | Use standard supported message/media rendering; rich-only client features are not advertised | Deferred |
| Replies | Target and reply constraints | Primary channel must be the sole destination for a saved reply ID | Deferred |
| Protected forwarding/content | Protection/share shortcut/private secret request fixtures | Protection enabled where selected; recipients can still record displayed content externally | Deferred |
| Personal reveal | Separate secret/public records, signed links, ordered fresh checks, private output and no global secret edit | Signed private-chat fallback; ephemeral channel replacement is not implemented or advertised | Deferred |
| Admission and welcome | Captcha, required membership, expiry, duplicate/rejoin, temporary contact/private start, blocked recipients | Standard join requests; durable private reachability is distinct from temporary contact; no historical member enumeration | Deferred |
| New join-query/welcome permissions | Unsupported-mode fixtures and explicit hold | Newer query-only/permission modes remain unsupported; use standard join-request path | Deferred |
| Must Share | Bot-owned native link attribution, distinct first qualifying request/join, stale epochs, timeout separation | Credits are observed qualifying requests/joins, never clicks; coordinated accounts cannot be disproved | Deferred |
| Cross-sender media | Cross-bot file ID rejection | Upload to the chosen sender; no automatic file transfer/reuse | Deferred |
| Campaigns | Fixed scoped opt-in snapshot, blocked/opt-out changes, cancellation, per-recipient uncertainty | No bot-wide or cross-channel audience expansion; reviewed retries exclude sent/ambiguous results | Deferred |
| Stars and refunds | Wrong/duplicate/late charge cases, atomic grant, upgrade/downgrade, native/shared refund reconciliation | Prepaid channel entitlement, full charge refund, unused linked time reflow; personal VIP unchanged | Deferred |
| Factory lifecycle | Ownership/epoch, rotation/pause/delete, unreadable token, explicit migration, sibling isolation | Full manager in a separate namespace; explicit host migration; external poller discovery/interoperability not claimed | Deferred |
| Rollback/readiness | Staged uncached dispatch checks, cleanup/refund continuity, progress probe, bounded actions, archive restore | Keep receipt-compatible code/schema and financial records; pause new effects without schema downgrade | Offline verified |

## Behavior decisions

The [advanced publishing](ADVANCED_PUBLISHING.md), [source automation](SOURCE_AUTOMATION.md), [member workflows](MEMBER_WORKFLOWS.md), and [growth/billing](GROWTH_AND_BILLING.md) runbooks define the tested scheduling, keyword, vote, privacy and commercial contracts. Prices remain unpublished/admin-configured; campaign consent is explicit; branded bots expose the full manager; external Modular integration remains out of scope.

The [Phase 7 release runbook](RELEASE_RUNBOOK.md) defines the remaining native checks and staged advancement criteria. Offline success does not approve a production launch or validate a container that has not run.
