# Channel Help feature analysis

Research date: 28 October 2026. Target: a new bot in this repository.

## Scope and evidence

I reviewed the [Channel Help guide](https://botguide.me/s/ch-en), all 18 sections in its main navigation, and its linked button and keyword guides. The inventory below describes documented behavior. It does not claim that the running Telegram bot was exercised, that its performance was measured, or that its private implementation is known. Screenshots and embedded demonstrations may expose details that the accompanying text does not specify; those details remain validation tasks.

The product combines four jobs: publishing channel content, automating repeated work, managing subscriber entry and exit, and re-engaging people through private messages. Channels are its primary managed resource; groups are auxiliary destinations, required memberships, discussion groups, and log destinations.

## Complete documented feature inventory

The release labels below are our proposed implementation order: **R1** publishing MVP, **R2** publishing automation, **R3** member onboarding, **R4** collaboration, growth, and commercial completion. They are not Channel Help plan names. Effort labels are relative, not estimates of the competitor's implementation.

| ID / feature | Documented capabilities | Value and implementation implication | Release / effort |
|---|---|---|---|
| CH-01 Channel connection and permissions | Channel-only primary operation; administrator setup; posting, editing, deletion, and invitation permissions. Human administrators' rights determine access, including own-post versus all-post editing/deletion. [Getting started](https://botguide.me/s/ch-en/doc/getting-started-Gz9vRfL6h7). | A channel is a separate authorization boundary. Connecting a channel must verify both the operator and the bot. | R1 / medium |
| CH-02 Post creation | Text/media composer with previews; incoming captions retained or replaced; attached media below text; Telegram entities, HTML, legacy Markdown, and newer Markdown; notifications, link previews, protected content, reply targets, signatures, pinning, saving, sending/deletion schedules, multi-channel delivery, and reaction buttons. HTML mode includes custom shorthand. [Create posts](https://botguide.me/s/ch-en/doc/create-posts-o7DmqM0oIB). | One reusable composition model should power every feature. Separate content from delivery settings and destination-specific outcomes. | R1 core; R2 advanced / high |
| CH-03 Post library and management | Saved posts across channels; sent/scheduled lists per channel; schedule overview; content/media edits; resend/share; add/remove attachments; reaction counts, removal and vote closure; publish scheduled posts early; reschedule; remove management records alone or also delete channel messages. [My posts](https://botguide.me/s/ch-en/doc/my-posts-7phybImZJP). | A draft, its published messages, and its management record are different objects. Detaching management must not imply remote deletion. | R1; R2 voting / high |
| CH-04 Recurring posts | Configurable anchor time and interval; weekday/month-day selection; daily time windows, including overnight windows; start/end dates; replacing the previous occurrence; per-occurrence deletion timer; shared schedules across channels, synchronized edits, and creator-controlled destination changes. [Recurring posts](https://botguide.me/s/ch-en/doc/recurring-posts-TXd2GXvOy3). | Recurrence requires an explicit calendar engine and independent occurrence records. Deletion failures must remain visible. | R2 / high |
| CH-05 Multipost and publication calendars | Batch composition with shared defaults/signature; default, per-post, or omitted buttons/reactions; restart current post, cancel batch, add/remove/review posts; publish together, schedule together, delete after a duration, or distribute sequentially across named weekly calendars starting now or later. [Multipost](https://botguide.me/s/ch-en/doc/multipost-d2LXxcjivJ). | Batch creation and multi-channel fan-out solve different problems. Reserve calendar slots atomically to prevent overlapping batches. | R2 / high |
| CH-06 Auto-complete | Automatically enrich manually published channel messages using named sets: header, signature, buttons, attached photo/video/GIF, separator sticker, and reaction buttons. Filters include trigger words, excluded words, media type, and a removable leading trigger command. Sets support deletion timers and word replacement. Albums receive signatures only. [Auto-complete](https://botguide.me/s/ch-en/doc/auto-complete-KOaYuIEkXd). | This is rule-based post processing, not AI text generation. Set ordering, repeated edits, formatting offsets, and forwarding order need explicit rules. | R2 / high |
| CH-07 Locked posts | Separate locked/unlocked versions; mandatory unlock button; channel membership and optionally ordered additional required chats; scheduling, deletion, notifications, protection, and pinning. A lead-acquisition option requires starting Channel Help; disabling that requirement needs Premium. [Locked post](https://botguide.me/s/ch-en/doc/locked-post-2LMFz8umm5). | Unlocking is user-specific access control. Delivery must never expose the unlocked version to ineligible viewers. Validate the demonstrated presentation before promising identical behavior. | R4 / high |
| CH-08 Welcome and approval | Private approval-link onboarding; configurable text/media/buttons, preview and attached media; custom welcome bot selection, also added to the channel. Immediate, delayed, and bulk-count/all approval; mathematical captcha with introductory post and expiry (documented default one hour); ordered required chats; Must Share invitations, invite threshold, dynamic placeholders, and optional approval after a timeout. Captcha requires a custom bot in the documented flow. [Welcome](https://botguide.me/s/ch-en/doc/welcome-bSa5dSZ6GL). | Several gates must cooperate in one persisted state machine. Approval must wait for every enabled condition, including delays, rather than each feature independently approving users. | R3; R4 invitation growth / very high |
| CH-09 Goodbye and departure actions | Private goodbye message depends on welcome; custom-bot pre-welcome encourages interaction so subsequent messages are reachable. Optional permanent or timed departure bans; optional linked discussion-group ban with the bot installed there. [Goodbye](https://botguide.me/s/ch-en/doc/goodbye-c0lMDaLiSy). | Distinguish voluntary departure from removal and bot-enforced changes. Temporary enforcement needs a durable unban obligation. | R3 / medium |
| CH-10 Broadcast and leads | Channel-associated private outreach to people who started Channel Help, including former subscribers. Documented minimum is 1,000 leads. Welcome, Must Share, Force Join, and locked-post flows acquire leads; using a custom bot does not acquire leads for the main bot. [Broadcast](https://botguide.me/s/ch-en/doc/broadcast-FyjRNNVaID). | Reachability belongs to a sending bot; audience association belongs to a channel. A subscriber count is not a private-message audience. The minimum is a competitor rule, not an automatic requirement for us. | R4 / high |
| CH-11 Event log | Configurable secondary logging channel; bot must administer that destination. Change/remove destination, choose log language, and toggle events; joins are an explicit example. The text does not enumerate every available event. [Event log](https://botguide.me/s/ch-en/doc/event-log-afjY9b1pVG). | Publish only events we actually observe or perform. Keep an internal audit trail independent of Telegram log delivery. | R1 internal; R3 external / medium |
| CH-12 Join filters | Total block; a configurable join threshold over ten seconds with kick/ban outcomes; name/username keywords; alphabet filters; language allowlist or blocklist. Matching users are rejected before welcome/captcha processing. [Join filters](https://botguide.me/s/ch-en/doc/join-filters-PsJKXWzuG3). | Evaluate admission filters first. Language/alphabet checks are configurable profile rules, not reliable measures of a person's identity or trustworthiness. | R3 / high |
| CH-13 Forwarding | Route manually sent source-channel posts to channels and/or groups. Optional branded sender for groups; channel copy mode omits source attribution. Choose original versus auto-completed content; reaction/comment buttons are excluded. Trigger-word, excluded-word, and media filters control routing. Destination permissions and channel plan requirements apply. [Forward](https://botguide.me/s/ch-en/doc/forward-AYeaYOPFyS). | Model a routing graph with cycle protection, provenance, independent destination status, and an explicit original/transformed payload choice. | R2; R4 branded sender / high |
| CH-14 Reusable settings | Per-channel default reaction buttons, named reusable button sets, named channel selections, and channel signatures (documented limit 250 characters) with default activation. Sets can be edited/deleted and used by composer/multipost. [Settings](https://botguide.me/s/ch-en/doc/settings-GWPnttdhbf). | Distinguish personal reusable presets from channel-wide configuration. Snapshot selected defaults so later preset edits do not silently alter scheduled content. | R1 signatures; R2 presets / medium |
| CH-15 Service-message cleanup | Selective automatic removal of channel service messages; changing the channel title is the documented example. The text does not enumerate the complete selector list. [Service messages](https://botguide.me/s/ch-en/doc/service-messages-Iep8CiUdwf). | Use a supported-message allowlist and report messages that cannot be removed. | R3 / low-medium |
| CH-16 Virtual administrators | Application-level posting/editing/deletion delegation without making the person a Telegram administrator. Add via known identity/ID/forward, require channel membership and non-admin status, configure permissions, edit/revoke access. [Virtual admins](https://botguide.me/s/ch-en/doc/virtual-admins-ug5vFhPxRN). | This requires channel-scoped application roles, not platform administrator access. Every callback and background action needs authorization. | R4 / high |
| CH-17 Modular integration | A custom bot handles captcha and welcome, then Modular handles interactions, broadcasts, manual/automatic replies, menus, and shop modules. Guide limits this integration to private channels. [Channel Help X Modular](https://botguide.me/s/ch-en/doc/channel-help-x-modular-FfO1wUZnjE). | Our factory can provide a native branded experience. An actual integration with the external Modular service is separate work requiring its documented contract. Shop functionality is outside this channel-manager scope. | R4 native equivalent / high |
| CH-18 Plans and entitlements | Free core plus channel-specific Plus, Premium, and Business subscriptions and a trial; tiered quotas and advanced-feature access. [Plans](https://botguide.me/s/ch-en/doc/plans-AB051OL9TA). | Channel entitlements are a new billing resource in this repository. Existing personal VIP status cannot represent them accurately. | R1 entitlement foundation; R4 checkout / high |

### Button subsystem

The [button guide](https://botguide.me/s/ch-en-buttons) documents link, popup/alert, membership-dependent popup, clipboard-copy, comments, and text-sharing buttons. It includes green/red/primary styling, one custom emoji per button, multiple buttons per row with `&&`, and newline-separated rows. Comments require a linked discussion group with the bot installed. Albums cannot carry these keyboards in the documented flow.

Our proposed editor should use structured button objects internally, offer a guided editor, and optionally accept this compact input syntax. Validate limits before preview. Store callback content server-side and bind callbacks to the correct bot, channel, post, and user where applicable. Keep native Telegram reactions separate from the custom vote buttons described in this guide.

### Keyword subsystem

The [keyword guide](https://botguide.me/s/en-keywords) documents whole-token matching, quoted whole-message matching, zero-or-more/one-or-more/optional-character wildcards inside tokens, and all-required-word matching using `&&`. Its prose mentions ordering while an example reverses the words; order semantics need validation.

Our proposal is a bounded parser with documented case, punctuation, Unicode, and conjunction behavior. Avoid exposing unrestricted regular expressions as the default configuration.

## Competitor's published commercial structure

These are guide-listed prices and quotas at research time, not verified checkout quotes or proposed prices for our bot. [Plans](https://botguide.me/s/ch-en/doc/plans-AB051OL9TA).

| Item | Plus | Premium | Business |
|---|---|---|---|
| Listed monthly price | $2.99 | $7.49 | $14.99 |
| Recurring posts | 5 | 50 | 100 |
| Auto-complete sets | 1 | 5 | 100 |
| Forwarding groups | 1 | 5 | 10 |
| Required chats in welcome | 1 | 3 | 5 |
| Additional inclusions | Multipost, timed approval, filters, logs, custom welcomes | Prior benefits; recurring deletion timers, word replacement, bulk approval, virtual admins | Prior benefits; highest sending priority |

The trial is one month at Business level but permits one recurring post. Plans are selected per channel. Renewals are manual; upgrades are prorated, added channels align to existing expiry, downgrades wait until period end, and cancellation disables benefits immediately. The guide cautions that displayed dollar prices can differ by client/store.

Our recommendation: start with configurable per-channel feature entitlements and simple prepaid periods. Add prorated upgrades and aligned multi-channel purchases only after the payment ledger supports them. Choose our Stars prices separately.

## Gaps and ambiguities that must stay visible

1. **Reaction maximum:** Create Posts says ten, while defaults and Auto-complete describe six. Use a configurable tested limit; do not present either as universal.
2. **Locked-post presentation:** the guide describes a personal reveal but does not explain its transport. Prototype user-specific delivery before committing to visual parity.
3. **Welcome reachability:** a long captcha/approval timer does not establish a long private-message delivery window. Separate pending admission, temporary reachability, and durable private-chat interaction.
4. **Auto-complete precedence:** multiple matching sets, handling later manual edits, and precise type coverage are not fully specified. Define deterministic behavior for our product.
5. **Forwarding lifecycle:** handling edits, deletions, albums, failures, loops, and posts sent by other integrations needs an explicit contract.
6. **Bulk approval:** no historical request-import contract is given. Our queue will contain requests durably observed after installation; the UI must state that boundary.
7. **Identity:** arbitrary usernames and hidden forwards may not identify a resolvable user. Support verified known users, numeric IDs, and invitation deep links.
8. **Logs and cleanup:** the public text gives examples rather than exhaustive event/message-type catalogs. Publish a tested support matrix for our bot.
9. **Scheduling:** timezone, daylight-saving transitions, missed executions, overlapping calendar batches, and invalid month days are unspecified. They need product rules, not guesses.
10. **Performance and service promises:** no throughput, reliability, or delivery-latency measurements were established in this review.

## Product recommendation

Add a separate **Channel Manager** bot rather than placing this interface inside Group Guard. Channel publishing has different resources, permissions, and workflows. Reuse the platform and review Group Guard's durability patterns, but keep channel-specific models and services independent.

The most useful first release is a reliable publishing workflow. The hardest work is durable Telegram side effects, authorization across channels and delegated operators, subscriber-gate orchestration, channel-specific audiences, and channel-specific billing. Rich menus are necessary, but they are not the main engineering risk.

The detailed implementation proposal is in [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md).
