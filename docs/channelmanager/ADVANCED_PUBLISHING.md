# Advanced publishing walkthrough

Phase 3 extends the existing Channel Manager composer. Apply migrations through `0021_chm_advanced`, then run the same gateway, scheduler, and Channel Manager worker described in [operations](OPERATIONS.md). No new token, external service, or Python dependency is required.

## Formatting and buttons

Open a post, select **Advanced publishing**, then choose **Markdown OLD**, **Markdown NEW**, or **HTML shorthand**. Send replacement text or one supported media item with a formatted caption. Native Telegram formatting and the validated HTML editor remain available.

| Mode | Supported syntax |
|---|---|
| OLD | `*bold*`, `_italic_`, `[label](https://example.com)`, inline code, fenced code, and nested supported formatting |
| NEW | OLD plus `__underline__`, `~strike~`, and `||spoiler||`; escape reserved punctuation with a backslash |
| Shorthand | Normal supported HTML plus generic `</>` closing, `<sp>` spoiler, `<m>` ASCII letters/digits converted to mathematical monospace, `<f>` fullwidth ASCII, `<br>` newline, `<dot>` bullet, and `<inv>` invisible separator |

Shorthand is transformed into Unicode text/entities before sending. It is never passed to Telegram as unsupported tags. Entity ranges are validated in UTF-16 units after transformation. Unbalanced markup, unsafe links, crossed ranges, unsupported attributes, and unsupported Markdown constructs are rejected. The compatibility subset follows the [documented formatting families](https://botguide.me/s/ch-en/doc/create-posts-o7DmqM0oIB); it does not implement every MarkdownV2 extension.

Use **Link buttons** on a post to enter URL or structured buttons. Put `&&` between buttons in one row and use new lines between rows. Send `-` to clear.

```text
Website - https://example.com
Info | popup | A short notification
Details | alert | Text shown in a modal alert
Members | member | -1001234567890 | Member response | Please join first
Copy | copy | Text to copy
Discuss | comments | https://t.me/your_discussion_group
Share | share
Like | vote && Dislike | vote
```

Popup and alert responses are limited to 200 characters; copy text allows 256. Membership buttons require an actively managed channel and live native operator/bot administrator checks during setup/publication. Each click checks current membership; errors fail closed. They provide a short conditional response, not the later locked-media workflow.

Comments use an explicitly supplied Telegram discussion/thread URL. Automatic discovery of a channel's corresponding discussion message is not assumed. Share buttons without a URL acquire the published message link through a separate durable keyboard update after sending. Private-channel links still require membership. Content protection rejects copy/share buttons; remove those buttons or change protection before publishing. Native copy buttons are described by the [Bot API keyboard documentation](https://core.telegram.org/bots/api#inlinekeyboardbutton).

Button styles, custom button emoji, albums, native polls, rich/ephemeral layouts, and automatic comment-thread mapping remain outside this tested subset. Standard labels and explicit discussion links are the fallbacks until live compatibility checks establish support.

## Voting and saved sets

**Vote buttons** accepts up to six distinct labels separated by `|`, such as `👍 | 👎`. These are custom single-choice ballots, separate from native Telegram reactions. A user has one choice per published channel message. Repeating the same callback does nothing; another choice moves the vote. Counters refresh through durable, budgeted keyboard jobs.

**Close current voting** closes current ballots. Ordinary body edits preserve choices, counts, and closure. Changing vote labels or their positions creates a new ballot for the new version; old callbacks cannot vote in it. Old records remain available in the version history. Callback requests are bound to the bot, delivery, content version, actual channel, and message ID.

Use `/presets` to create personal named button sets or channel selections. Enter the name on the first line, then the button syntax or comma-separated channel IDs. Sets can be edited/deleted. Apply them from a post's **Advanced publishing → Apply saved set** menu. Every destination is authorized again when a channel set is applied; a saved set grants no additional rights. Applied values are snapshots, so later preset changes leave saved/scheduled posts intact.

Use `/reactions`, select a channel, then enter default vote labels. New drafts snapshot those labels and the primary channel's saved signature. Channel defaults require native editing rights. Existing drafts retain their saved values. `/signature` and `/timezone` continue to work as described in the basic operator guide.

## Recurring posts

Start with a standalone saved draft and select **Advanced publishing → Make recurring / change rule**. Copy a published or batch item to a new draft first. Enter one setting per line:

```text
anchor=2027-01-10T09:00+07:00
every=2h
weekdays=Mon,Tue,Wed,Thu,Fri
monthdays=1,15
window=22:00-02:00
start=2027-01-10T00:00+07:00
end=2027-12-31T00:00+07:00
dst=skip
replace=yes
```

Only `anchor` is required; the default interval is `24h`. Intervals accept whole `m`, `h`, or `d` units, from one minute through 365 days. The anchor is an earliest instant on the local wall-clock grid in the primary channel's saved timezone. Optional start is inclusive; end is exclusive. Weekday and month-day filters combine with AND and apply to the actual local publication date. Invalid month days are skipped. Overnight windows include their start and exclude their end; equal window endpoints mean all day.

For daylight-saving transitions, nonexistent local instants are skipped. `dst=skip` also skips ambiguous instants; `earlier` or `later` chooses one fold, never both. Enter an explicit UTC offset for an ambiguous anchor/start/end. Preview the next five valid instants and all destinations before confirming activation. A finite rule may have fewer than five remaining instants.

Use `/recurring` to view templates, inspect the next times/error code, edit rules, or pause/resume. Resume starts with a future occurrence. Scheduling is durable in SQL and duplicate sweeps create one occurrence per recurrence/instant. The worker skips missed occurrences by default; a small `recurrence_lateness_grace_seconds` window (30 seconds by default) tolerates normal worker jitter without replaying a downtime backlog. One-off posts retain their separate 300-second default grace.

Every occurrence becomes its own immutable post/delivery set. Root content edits apply to future occurrences in all current destinations, with an impact preview for content replacement. Existing published occurrences retain their versions. Changes cancel obsolete unsent occurrences; an in-flight action must resolve before mutation. Only the creator may change destinations, configure rules, or use pause/resume in the recurrence menu. Authorized edit-all operators can also stop the root through its cancel/detach actions. Live native permissions are checked across every destination. Loss of required rights pauses recurrence with a visible error code.

Deletion timers begin at each actual successful send. With `replace=yes`, a new successful delivery creates a durable obligation to delete the previous successful occurrence in the same channel. Failed or uncertain sends preserve the previous message. Planning cleanup can resume after a crash and never holds the new send transaction while waiting for an older occurrence's lock. Pin/delete/keyboard failures retain their own reports. Deletion outside Telegram's ordinary window becomes a manual reminder. A brief overlap is expected; strict delete-first replacement is not offered.

Pausing cancels unsent occurrences and retains cleanup for already published messages. Detaching/deleting/cancelling the root also pauses recurrence. Explicit channel disconnect stops new work and undispatched cleanup; a request already sent to Telegram may still complete.

## Multipost and weekly calendars

Use `/multipost`, create a batch, and select its channel. Before adding items, choose shared, per-item, or omitted button/vote defaults. **Defaults for newly added posts** also controls notifications, link previews, protection, pinning, signature inclusion, and a shared deletion timer. Changing defaults affects newly added items; existing items retain their snapshots.

**Add / next post** collects one supported post. Per-item modes prompt for its buttons/votes. Open an item for preview or individual edits. **Restart last item** discards the last unqueued item and starts it again. **Remove item** accepts an item number. **Finish collection** retains the batch for later review. Leaving with `/cancel` only exits input; **Cancel remaining batch work** explicitly cancels the batch.

**Plan batch publication** offers immediate sending, a future start, or a weekly calendar. Review the destination and each planned UTC instant, then confirm. Non-calendar items are queued in item order at one-second intervals; API rejections/retries can change actual arrival order, and each item's report remains independent.

Use `/calendars` to create or edit a named weekly calendar for a channel. Enter a name, followed by slots:

```text
Weekday schedule
Mon 09:00
Wed 16:30
Fri 12:00
```

The channel's IANA timezone is saved with the calendar. Ambiguous/nonexistent daylight-saving slots are skipped. Editing a calendar affects new allocations; existing reservations keep their saved UTC instants. Creating/editing calendars requires native editing rights.

Calendar planning distributes active batch items sequentially over available slots, starting now or at a future time. Confirmation reserves every slot and queues the whole batch in one transaction. If another batch takes a previewed slot, the plan is rejected as stale and must be reviewed again. Content changes since preview also invalidate confirmation. Schedule quota failure rolls the complete plan back.

Batch/item cancellation releases unsent reservations while preserving published/uncertain history and existing cleanup obligations. Individual rescheduling relinquishes the old unsent calendar slot. Batch progress lists every item's publication state; opening an item shows its independent delivery/follow-up results. Completed or cancelled batches are retained for review; use a new batch for another publication.

## Limits and operational boundaries

Default limits are 50 personal presets, 20 recurring templates per operator, 20 collecting/ready batches per operator, 50 active items per batch, and 20 calendars per channel. Existing per-channel future-schedule entitlements and operator draft limits still apply. Limits are enforced with bot/channel/calendar row locks and unique reservation keys.

The same worker/profile, lease fencing, shared rate budgets, late one-off policy, and uncertain-delivery handling remain in use. Delivery actions serialize per message so an old counter refresh cannot race a content edit. Cleanup and vote-refresh obligations are separate from publication success. An uncertain send is never automatically replayed.

This phase uses SQL records and mocked Telegram responses plus real disposable PostgreSQL/Redis checks. Live Telegram clients, deployed Bot API compatibility, Compose PostgreSQL 16/Redis 7, canary load, retention, and production rollout still require the relevant Phase 0/7 work. See [Phase 3 verification](PHASE_03_VERIFICATION.md).
