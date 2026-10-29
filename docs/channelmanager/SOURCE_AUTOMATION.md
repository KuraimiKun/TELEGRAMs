# Source automation

Phase 4 adds auto-complete rules and filtered routes for manually published channel posts. Open **Source automation** from `/start` or channel details, or send `/automation`. The existing gateway, worker, and recovery scheduler execute these workflows; no separate process is required.

Apply migration `0022_chm_automation` before starting this code. See [setup and recovery](OPERATIONS.md) and [verification](PHASE_04_VERIFICATION.md). This implementation has automated verification with mocked Telegram responses; Phase 0 live compatibility and production canary checks remain outstanding.

## Auto-complete rules

1. Connect the source through `/connect`, then select it under `/automation`.
2. Open **Auto-complete sets**, create a named set, and configure its filters and transformations. A new set starts disabled.
3. Set a priority: lower numbers win. Ties use the stable rule ID. Only the first matching active set applies to a source version.
4. Use **Test a sample** to send a private text/media example and inspect the transformed preview. This does not create a source automation job or enable the rule.
5. Enable the set, review the activation summary, and confirm. The confirmation is bound to the operator and configuration generation.
6. Publish a new manual source post and inspect **Source reports**. Genuine manual edits are evaluated again when **Apply to source edits** is enabled.

Filters inspect the canonical input before this version's transformations. Saved header/signature affixes are removed from a manually edited enriched message before matching. An edit still needs to satisfy the filters; for example, a command-qualified rule requires its leading command again. Updating or activating configuration affects receipts committed after that change, including later genuine edits; it does not sweep old posts or replay already queued work. A configuration change invalidates stale, undispatched automation in that source channel.

Supported fields:

| Field | Behavior |
|---|---|
| Trigger / excluded expressions | Newline-separated alternatives; any exclude wins |
| Media | Text, photo, video, animation, document, or album |
| Leading command | Exact first whitespace-separated word, with optional removal |
| Header / signature | Formatted text/entities, separated from content by a blank line |
| Buttons / votes | Phase 3 structured buttons and version-scoped single-choice voting |
| Attachment | Photo, video, or animation uploaded to this bot; converts text into media; existing source media is retained with a warning |
| Separator | One uploaded sticker after successful enrichment; not resent on ordinary later edits |
| Replacements | Whole-token `old => new` pairs; evaluated simultaneously against the input |
| Deletion timer | Deletes the source message and separator independently; retains the source's original send timestamp |

Use `-` to clear optional text, keyword lists, buttons, replacements, media references, or timers in their input prompt. Media selectors accept comma-separated names or `all`. Durations accept `30m`, `2h`, or `3d`, up to one year. Headers allow 500 UTF-16 units, signatures 250, and resulting text/captions use the shared 4,096/1,024 limits. Overlong content fails visibly instead of truncating it. The default quota is 25 named sets and 25 routes per source, configurable up to 100 each; disabling a saved configuration preserves its history and quota usage.

Source operators must currently have native posting and editing rights. A source deletion timer additionally requires the operator and bot to have deletion rights when saved. The bot needs the native editing right to enrich another administrator's messages. Private previews and stored app roles do not confer Telegram rights.

Single-message enrichment creates an internal managed post linked to the existing source message, without publishing another source message. Its votes and follow-up reports reuse the publishing system. Managing this adopted manual message still requires native edit-all/delete-all rights, even for the operator who created its rule. General adoption of arbitrary historical message IDs is not exposed.

## Keyword contract

The guide describes token wildcards, quoted exact messages, and conjunctions. This implementation fixes the following deterministic subset; it does not accept arbitrary regular expressions. [Guide keyword syntax](https://botguide.me/s/en-keywords).

| Expression | Matches |
|---|---|
| `help` | A complete whitespace-delimited token, after trimming surrounding Unicode punctuation |
| `c(*)bot` | `cbot`, `chbot`, or `chelpbot`; never across whitespace |
| `c(+)bot` | At least one character between `c` and `bot` |
| `c(?)bot` | Zero or one character between them |
| `"exact message"` | The whole message after trimming outer whitespace |
| `bot && help` | Both terms anywhere in the message, in either order |
| Separate lines | OR alternatives |

NFC normalization and Unicode case folding apply by default; **Case sensitive** disables folding. Arabic diacritics, emoji, and symbols are retained. The matcher does not stem words or transliterate scripts. Conjunctions are explicitly unordered; quoted text retains its internal spacing. Limits are 20 alternatives per trigger/exclude list, 512 characters per expression, eight conjunction terms, 64 characters per token term, and four wildcard markers per term. Input length and wildcard work are bounded; an exhausted budget produces a visible failure.

Replacements use the same token boundaries and case setting. Each old value must be one plain token, with no duplicate normalized keys. Replacement text does not trigger another replacement in the same pass. Formatting spans are shifted or clipped in UTF-16 units, including around Arabic text and emoji.

## Routing

Create a named route, supply a destination ID, choose its filters, mode, content selection, and source-edit policy, then enable it after review. Destinations are connected managed channels or native groups/supergroups in which both operator and bot are administrators. Private users and branded/factory senders are outside this phase. Each route records its own result; a failed group does not prevent another channel from succeeding.

| Choice | Result |
|---|---|
| Copy + original | Sends the saved canonical input without this version's enrichment |
| Copy + transformed | Sends the computed enriched snapshot independently of the source edit RPC |
| Forward + original | Uses Telegram attribution; ordered before this version's enrichment |
| Forward + transformed | Uses Telegram attribution after successful required source edits |
| Copy + propagate edits | Edits known destination message IDs on genuine later source edits |
| Propagation off (default) | Leaves the first known destination publication intact; repeated edits never create replacement copies |

Attributed forwarding operates on the live Telegram source. It cannot forward an immutable historical snapshot or undo an earlier manual/enrichment change. Use copy mode when the saved snapshot is required. Telegram may reject unsupported/removed live messages, and that route reports the rejection. Native forwarded-message edit propagation is rejected in configuration. Automatic source-deletion propagation is disabled.

Copied destinations keep safe link/native-copy buttons and explicit share URLs. Source-bound callbacks, membership actions, comments, and votes are omitted. A copied album has no per-item keyboards. This avoids transporting callbacks bound to another delivery/version. Telegram forwarding has its native server-defined behavior. [Forwarding APIs](https://core.telegram.org/bots/api#forwardmessages).

Changing a route destination never reuses message IDs from another chat. Switching an existing attributed publication to editable copy mode holds that source's propagation for review rather than editing the forwarded message. A new logical source post uses the current route normally. Changing filters or disabling a route leaves existing remote messages intact.

Protection is checked in the receipt and again against the source chat immediately before every copy/forward request, including propagated edits. Protected input is never reuploaded as an alternative to a rejected forward. Destination and source authorization are rechecked before dispatch. These checks cannot make external permission changes and network requests atomic.

## Albums and loop prevention

New albums collect durably with a configurable two-second quiet period, capped at 30 seconds from initial source observation. Only complete photo/video albums of 2–10 items are routed. A lone item at the deadline, unsupported album media, or a post-publication change in album membership is held with a reason.

Album enrichment appends one signature to the caption-bearing/first item. Header, command removal, replacement, attachment, separator, and callback/vote options are omitted and reported as `album_signature_only`. Per-item deletion obligations remain supported. Caption overflow fails validation. Album copy propagation edits each known destination item separately, preserving the original album layout. Partial native forward results retain all returned IDs and become uncertain; missing items are not automatically resent.

Bot-generated edits and publications are recognized through persisted source fingerprints, managed deliveries, output message IDs, and in-flight effects. The worker does not recursively automate its own routed output in another managed channel. Routing cycles are rejected under a bot-wide configuration lock, and actions retain path/hop limits as an additional fence. Identical manual content that is indistinguishable from an in-flight effect is conservatively suppressed. General cross-bot loop detection is outside this phase.

## Reports and recovery

Open `/automation` → source → **Source reports**. Each source version has immutable original/transformed snapshots, transformation warnings, and independent edit, route, separator, and cleanup outcomes. Reports show sanitized codes and known IDs. Platform `/admin` diagnostics and `channelmanager_work` metrics include collecting/held source counts and failed/uncertain automation counts.

| Outcome | Meaning and next step |
|---|---|
| Pending | Waiting for dependencies, sender/chat budget, worker, or Telegram retry delay |
| Succeeded | The API confirmed the operation; known output IDs are retained |
| Skipped | For example, edit propagation is disabled for an existing publication |
| Held | Review uncertain prior delivery, changed album layout, route mode, or provenance |
| Failed | Definite rejection or invalid content; correct the cause and use the individual safe retry when eligible |
| Uncertain | A dispatched request has no reliable completion; reconcile externally before deliberately creating replacement work |
| Cancelled | Source/configuration generation or namespace changed before dispatch |

Safe retry creates fresh work only for a definite failure under the current source/control generation and current authorization. It does not resend successful targets. Uncertain outcomes are never automatically replayed or offered a retry button. Source edits continue to respect unresolved uncertain route history across multiple later versions.

Source timers measure from the original source send time; separator timers start from the confirmed sticker send time. Timers at/past Telegram's ordinary 48-hour deletion window send the operator a manual-deletion reminder. The report distinguishes that reminder from a confirmed deletion. Existing cleanup survives ordinary rule edits/disabling but explicit channel disconnect cancels undispatched cleanup. A dispatched/uncertain cleanup is never replaced with a duplicate timer. [Deletion rules](https://core.telegram.org/bots/api#deletemessage).

The durable inbox, source planner, action ledger, and operation outbox share PostgreSQL transactions. Redis budgets are shared with existing publishing/status/broadcast work; Redis failure defers sends. Maintenance pauses planning and outbound dispatch while preserving receipts. Leases, source/configuration generations, and destination generations fence stale workers. Dispatched effects can still finish after a setting change; the system does not claim exactly-once Telegram delivery.

Source parts and snapshots contain private channel text, formatting, file references, and configuration. Completed inbox payload removal does not remove these automation records. Restrict database access and apply the deployment's retention/backup policy. This phase supplies no general historical replay or automatic retention UI.

Reference behavior: [auto-complete guide](https://botguide.me/s/ch-en/doc/auto-complete-KOaYuIEkXd), [forwarding guide](https://botguide.me/s/ch-en/doc/forward-AYeaYOPFyS). Membership workflows, billing/collaboration, branded senders, and combined production readiness remain Phases 5–7.
