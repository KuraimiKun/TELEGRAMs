cmd-channels = Your channels
cmd-connect = Connect a channel
cmd-help = Channel Manager help
cmd-newpost = Create a post
cmd-posts = Your posts
cmd-signature = Set a channel signature
cmd-timezone = Set a channel timezone
cmd-cancel = Cancel the current input
chm-start =
    📣 <b>Channel Manager</b>
    Connect your Telegram channels and check their permissions.
chm-list = 📣 <b>Your channels</b>
chm-empty = No accessible channels on this page. Connect a channel to begin.
chm-connect-help =
    ➕ <b>Connect a channel</b>
    Add this bot as an administrator of your channel with permission to post messages.
    Then send <code>/connect @channelname</code> or <code>/connect -1001234567890</code>.
    You must be the channel owner or an administrator allowed to post.
chm-connect-denied = Connection failed. Check the channel reference, your posting permission, the bot's administrator/posting rights, and your channel limit.
chm-connected = ✅ Channel setup saved. Your status confirmation will arrive shortly.
chm-denied = Access denied or this menu has expired. Open /channels again and check your current channel permissions.
chm-channel =
    📣 <b>{ $title }</b>
    • Channel: <code>{ $id }</code>
    • Status: <b>{ $status }</b>
    • Missing bot permissions: { $missing }
chm-disconnect-confirm = Disconnect <b>{ $title }</b> from Channel Manager? Pending work that has not been dispatched will be cancelled.
chm-disconnected = ✅ Channel management disconnected. The bot can be removed from the channel or reconnected with /connect.
chm-notice = 📣 <b>{ $title }</b> — channel status: <b>{ $status }</b>.
chm-admin =
    📣 <b>Channel Manager diagnostics</b>
    • Active channels: { $channels }
    • Pending operations: { $pending }
    • Failed operations: { $failed }
    • Uncertain deliveries: { $uncertain }
    • Pending channel events: { $inbox_pending }
    • Failed channel events: { $inbox_failed }
chm-admin-inbox-error = Event <code>{ $id }</code> · { $code }
chm-btn-channels = 📣 My channels
chm-btn-connect = ➕ Connect a channel
chm-btn-refresh = 🔄 Refresh
chm-btn-disconnect = Disconnect
chm-btn-confirm = Confirm disconnect
chm-btn-admin = 📣 Channel Manager
chm-right-post = Post messages
chm-right-edit = Edit messages and pin posts
chm-right-delete = Delete messages
chm-right-invite = Approve and invite members
chm-right-restrict = Ban members
chm-none = None
chm-state-observed = Awaiting setup
chm-state-active = Active
chm-state-degraded = Missing posting permission
chm-state-removed = Bot removed
chm-state-disconnected = Disconnected
chm-btn-new-post = ✍️ New post
chm-btn-posts = 📚 Posts
chm-btn-preview = 👁 Preview
chm-btn-body = ✏️ Edit content
chm-btn-buttons = 🔗 Link buttons
chm-btn-clone = 📋 Copy to a new draft
chm-btn-publish = 📣 Publish now
chm-btn-schedule = 🕓 Schedule / reschedule
chm-btn-targets = 📡 Destinations
chm-btn-options = ⚙️ Post options
chm-btn-save = 💾 Save draft
chm-btn-cancel-post = Cancel remaining sends
chm-btn-delete-post = 🗑 Delete published messages
chm-btn-detach = Stop managing this post
chm-btn-confirm-publish = Confirm publication
chm-btn-html = Edit content as HTML
chm-btn-delete-after = Deletion timer
chm-btn-reply = Reply to a message
chm-btn-open = Open message · { $channel }
chm-btn-share = Share link
chm-btn-retry-followups = Retry failed edits / pins / deletions
chm-filter-all = All
chm-filter-drafts = Drafts
chm-filter-scheduled = Queued / scheduled
chm-filter-published = Published
chm-choose-channel = Select a connected channel. If it is missing, use /connect first.
chm-content-prompt = Send text or one photo, video, GIF, or document with an optional caption. Telegram formatting is preserved. Albums are not supported here. Use /cancel to leave.
chm-content-html = Send the replacement content with HTML formatting. Supported tags: b, i, u, s, code, pre, blockquote, tg-spoiler, and a href. Escape literal angle brackets. Use /cancel to leave.
chm-buttons-prompt = Send link buttons as “Label - https://example.com”. Separate buttons in a row with && and rows with new lines. Send - to clear.
chm-targets-prompt = Send up to 10 connected channel IDs separated by commas. You must have current permission in every destination.
chm-schedule-prompt = Send YYYY-MM-DD HH:MM in { $timezone }, or include an explicit UTC offset, for example 2027-01-10T15:30+07:00. Ambiguous or missing local times require an explicit offset.
chm-delete-after-prompt = Send a duration such as 30m, 2h, or 3d. Timers of 48 hours or longer create manual deletion reminders. Send - to disable.
chm-reply-prompt = Send a message ID from the primary channel, or - to clear. Replies are supported only when that channel is the sole destination.
chm-signature-usage = Use <code>/signature -1001234567890</code>. You need permission to edit others' channel messages.
chm-signature-prompt = Send the channel signature, with Telegram formatting, up to 250 characters. Send - to clear. Existing drafts keep their saved signature.
chm-settings-saved = ✅ Channel settings saved. New drafts use the updated values.
chm-library = 📚 <b>Post library</b>
chm-post =
    📨 <b>Post { $id }</b>
    • Status: <b>{ $status }</b>
    • Destinations: { $targets }
chm-delivery = • { $channel }: { $status } (v{ $version }); edit: { $edit }; pin: { $pin }; deletion: { $deletion }
chm-send-at = • Send time: { $when }
chm-delete-after-value = • Deletion timer: { $seconds } seconds after sending
chm-now = Now
chm-publish-confirm =
    📣 <b>Confirm publication</b>
    { $targets }
    Successful and uncertain previous deliveries will not be resent. Only unsent or definitely failed destinations are queued.
chm-reminder-only = ⏳ This timer creates a manual deletion reminder because automatic deletion will be unavailable.
chm-options = ⚙️ <b>Post options</b>
chm-opt-notifications = Notify subscribers
chm-opt-preview = Show link preview
chm-opt-protected = Protect content
chm-opt-pin = Pin after publication
chm-opt-signature = Include saved signature
chm-opt-caption = Caption above media
chm-draft-saved = 💾 Draft saved. Open /posts to continue.
chm-input-cancelled = Input cancelled. Saved drafts remain in /posts.
chm-confirm-delete = Delete the known published messages and cancel remaining sends? Uncertain deliveries with no known message ID require manual review.
chm-confirm-detach = Stop managing this post and cancel its remaining work? Published messages will remain in their channels.
chm-confirm-cancel = Cancel the remaining sends? Messages already published will remain in their channels.
chm-detached = Management stopped. Published messages remain in their channels.
chm-delete-reminder = 🗑 Manual deletion reminder: channel <code>{ $channel }</code>, message <code>{ $id }</code>. Open the channel and delete it manually.
chm-post-state-draft = Draft
chm-post-state-queued = Queued
chm-post-state-pending = Pending
chm-post-state-sent = Published
chm-post-state-partial = Partially published
chm-post-state-failed = Failed
chm-post-state-uncertain = Delivery uncertain — review before retrying
chm-post-state-cancelled = Cancelled
chm-post-state-held = Held after a missed schedule
chm-post-state-deleted = Deleted
chm-post-state-detached = Management stopped
chm-job-none = Not requested
chm-job-pending = Pending
chm-job-running = In progress
chm-job-succeeded = Done
chm-job-failed = Failed
chm-job-uncertain = Uncertain
chm-job-cancelled = Cancelled
chm-job-reminder = Manual reminder
chm-error-content = The content or settings are invalid. Check the input and try again.
chm-error-length = The text, caption, or signature exceeds its supported length.
chm-error-media = Send supported media uploaded to this bot. Files from another bot cannot be reused directly.
chm-error-album = Albums are not supported in this composer. Send one media item per post.
chm-error-html = The HTML is invalid or uses unsupported tags or attributes. Correct it and resend.
chm-error-buttons = Check the button format. Use up to 10 rows with at most 4 link buttons each.
chm-error-url = Use a valid http, https, or tg link.
chm-error-entities = The text formatting is invalid. Reformat the message and resend.
chm-error-caption = Caption placement is supported only for photos, videos, and GIFs.
chm-error-time = Use a valid future date/time or supported duration. Add a UTC offset for ambiguous local times.
chm-error-reply = Replies require one destination: the primary channel. Use a positive message ID from that channel.
chm-error-targets = Select between 1 and 10 connected channels.
chm-error-stale = This post has changed. Reopen /posts to use its current menu.
chm-error-busy = A delivery action is in progress. Wait for its result and refresh the post.
chm-error-limit = The draft or scheduled-post limit has been reached. Remove unused drafts or cancel a schedule.
chm-error-conversion = A published media message cannot be changed to text here. Copy it to a new draft instead.
chm-error-published_settings = These publication settings cannot change after sending. Copy the post to a new draft.
chm-error-already_sent = There are no safe unsent destinations to queue. Copy the post to a new draft for another publication.
chm-error-access = Access denied. Check your current rights in every destination and the bot's required permissions.

chm3-advanced = Advanced publishing
chm3-batch-options = Defaults for newly added posts
chm3-hub = Advanced publishing: choose a tool. Open a post's Advanced menu to format it or make it recurring.
chm3-recurring = Recurring posts
chm3-series = Recurring templates
chm3-batches = Multipost batches
chm3-presets = Saved button / channel sets
chm3-calendars = Weekly calendars
chm3-markdown = Markdown OLD
chm3-markdown2 = Markdown NEW
chm3-shorthand = HTML shorthand
chm3-reactions = Vote buttons
chm3-apply-set = Apply saved set
chm3-repeat = Make recurring / change rule
chm3-close-votes = Close current voting
chm3-post-panel = Advanced options. Changes affect the post in these destinations: { $targets }. Custom vote buttons are separate from native Telegram reactions.
chm3-format-prompt = Send replacement text or one supported media item with a formatted caption. OLD supports *bold*, _italic_, links and code. NEW adds __underline__, ~strike~, ||spoiler||; escape reserved punctuation with a backslash. Shorthand supports &lt;/&gt;, &lt;sp&gt;, &lt;m&gt;, &lt;f&gt;, &lt;br&gt;, &lt;dot&gt;, and &lt;inv&gt;. /cancel leaves input.
chm3-reactions-prompt = Send up to six distinct vote labels separated by |, for example 👍 | 👎. Send - to clear. Editing published choices starts a new version with a new ballot.
chm3-buttons-prompt = Use Label - https://example.com, or Label | popup | text, alert | text, copy | text, comments | https://t.me/…, share, vote, or member | -100… | member text | other text. Include the label before every type. Separate buttons with && and rows with new lines. Send - to clear.
chm3-rule-prompt = Send one setting per line. Required: anchor=2027-01-10T09:00+07:00. Optional: every=2h, weekdays=Mon,Tue, monthdays=1,15, window=22:00-02:00, start=2027-01-10T00:00+07:00, end=2027-12-31T00:00+07:00, dst=skip (or earlier/later), replace=yes (or no). Intervals use m/h/d. Missed occurrences are skipped. Replacement sends first, then deletes the previous successful occurrence.
chm3-confirm-series = Confirm recurring publication to { $targets }.
    Next occurrences:
    { $times }
    Replace previous after success: { $replace }. Each occurrence keeps its own deletion timer.
chm3-series-panel = Recurrence { $id }: { $status }
    Destinations: { $targets }
    Next five rule times:
    { $times }
    Last issue: { $error }
chm3-series-active = Active
chm3-series-paused = Paused
chm3-series-finished = Finished
chm3-pause = Pause
chm3-resume = Resume
chm3-edit-rule = Edit recurrence rule
chm3-recurring-template = Recurring template: content edits apply to future occurrences in all listed destinations. Only its creator can change destinations. Use Recurring posts to pause or resume.
chm3-confirm-shared-edit = Apply this content to future recurring occurrences in { $targets }? Existing published occurrences keep their own versions.
chm3-yes = Yes
chm3-no = No
chm3-add = Add / next post
chm3-finish = Finish collection
chm3-restart = Restart last item
chm3-remove = Remove item
chm3-shared-buttons = Shared buttons
chm3-shared-reactions = Shared vote labels
chm3-mode-shared = Shared defaults
chm3-mode-per_item = Ask per item
chm3-mode-none = Omit
chm3-plan = Plan batch publication
chm3-use-calendar = Distribute with a calendar
chm3-new-batch = New multipost batch
chm3-cancel-batch = Cancel remaining batch work
chm3-batch-panel = Batch { $id }: { $status }
    Items: { $count }
    Progress: { $progress }
    Defaults and modes affect newly added items. Open an item to edit or preview it.
chm3-batch-collecting = Collecting
chm3-batch-ready = Ready
chm3-batch-queued = Queued
chm3-batch-cancelled = Cancelled
chm3-collect-prompt = Send one post: text, photo, video, GIF, or document. It is saved durably. Use the batch menu for the next post, or /cancel to leave input.
chm3-remove-prompt = Send the item number to remove. Published or queued batches cannot remove individual items here.
chm3-confirm-batch = Confirm batch publication to channel { $channel } at these UTC instants:
    { $times }
    Calendar slots are reserved together. If another batch takes a previewed slot, request a fresh plan.
chm3-confirm-cancel = Cancel remaining sends? Published messages and their cleanup timers remain. Unsent calendar reservations are released.
chm3-start-prompt = Send a future start time as an ISO date with UTC offset, for example 2027-01-10T09:00+07:00. Calendar planning starts from that instant.
chm3-new-calendar = New calendar
chm3-edit-calendar = Edit calendar
chm3-calendar-prompt = Send the calendar name on the first line, then one weekly slot per line, for example Mon 09:00 and Wed 16:30. Day tokens: Mon Tue Wed Thu Fri Sat Sun. The channel timezone is saved with this calendar; ambiguous/nonexistent DST slots are skipped. Existing reservations keep their UTC times.
chm3-calendar-panel = Calendar: { $name }
    Timezone: { $timezone }
    { $slots }
chm3-new-buttons = New button set
chm3-new-channels = New channel set
chm3-delete-set = Delete saved set
chm3-preset-prompt = Send a name on the first line. For a button set, put button syntax on following lines. For a channel set, put comma-separated channel IDs on the next line. Saved posts keep their snapshots when this set changes.
chm3-preset-panel = Saved set: { $name }
chm3-markup-status = Buttons/count refresh: { $status }
chm3-error-name = Use a unique name between 1 and 64 characters.
chm3-error-closed = Voting is closed.
chm3-error-series_draft = Use a saved draft with no deliveries as the recurring template. Copy a published post to a new draft first.
chm3-error-series_template = This is a recurring template. Manage its rule through Recurring posts, or copy it to a new draft for a one-off send.
chm3-error-batch_queued = This batch is already queued or cancelled. Open its current report; create another batch for new content.
chm3-error-stale_plan = The items or available calendar slots changed. Review a fresh plan and confirm again.
chm-error-markdown = Invalid Markdown or unsupported syntax. Check paired markers, links, and escapes.
chm-interaction-preview = Interactive buttons become active on the published channel message.
chm-vote-recorded = Vote saved. Counts refresh shortly.
chm-membership-required = Join the required channel to use this button.
chm-voting-closed = Voting is closed.
chm-interaction-unavailable = This button is unavailable or its post changed. Open the current channel message.

chm4-choose = Select a channel for auto-complete and forwarding. Native posting and edit-all rights are required.
chm4-channel = Source automation for { $title } ({ $id }). Rules affect future manually published source events. Bot outputs are excluded. Review a set before enabling it.
chm4-sets = Auto-complete sets
chm4-routes = Forwarding routes
chm4-reports = Source and delivery reports
chm4-new-set = New addition set
chm4-new-route = New forwarding route
chm4-config = { $name } · { $status }
    Trigger expressions: { $triggers }; exclusions: { $excludes }
    Media: { $media }
chm4-priority-value = Priority: { $value }. Lower numbers run first; ties use the set ID. Only the first matching active set applies.
chm4-enabled = Enabled
chm4-disabled = Disabled
chm4-header = Header
chm4-signature = Signature
chm4-attachment = Attach photo / video / GIF
chm4-separator = Separator sticker
chm4-replace = Word replacements
chm4-command = Leading trigger command
chm4-priority = Set priority
chm4-on-edits = Enrich manual edits
chm4-remove-command = Remove leading command
chm4-test = Test a sample preview
chm4-destination = Destination
chm4-mode = Copy / forward mode
chm4-content = Original / transformed content
chm4-propagate = Propagate source edits
chm4-trigger = Trigger expressions
chm4-exclude = Excluded expressions
chm4-media = Media selectors
chm4-case = Toggle case sensitivity
chm4-rename = Rename
chm4-enable = Review and enable
chm4-disable = Disable future work
chm4-yes = Yes
chm4-no = No
chm4-route-details = Destination: { $destination }
    Mode: { $mode }; content: { $content }; edit propagation: { $edits }
    Destination-specific callbacks and voting are omitted from copies.
chm4-mode-copy = Copy without attribution
chm4-mode-forward = Forward with attribution
chm4-content-original = Original input
chm4-content-transformed = After auto-complete
chm4-enable-confirm = Enable { $name } for future manual source events? Enrichment can edit source posts and schedule requested deletions. Routes send to their configured destination. Albums support signature additions only. Disabling cancels unsent automation and keeps cleanup already authorized by successful work.
chm4-name-prompt = Send a unique name, up to 64 characters. Use /cancel to leave.
chm4-destination-prompt = Send a connected destination channel ID or group/supergroup ID, such as -1001234567890. You and this bot must currently administer the destination. Private users and branded sender bots are not supported here.
chm4-text-prompt = Send formatted text for this addition, or - to clear. Header limit: 500 UTF-16 units; signature limit: 250. The final message/caption must still fit Telegram's length limit.
chm4-attach-prompt = Send one photo, video, or GIF to this bot, or - to clear. Attachments turn text posts into media posts; an existing media item is retained. Albums receive signatures only.
chm4-sticker-prompt = Send one sticker, or - to clear. It is sent once after successful enrichment of a single source post. Albums do not receive separator stickers.
chm4-replacement-prompt = Send one literal whole-token replacement per line as old => new. Matching uses the filter's case setting. Replacements are simultaneous and do not cascade within a version. Send - to clear.
chm4-keywords-prompt = Send one expression per line; lines mean OR, and && means unordered AND. Examples: hello; c(*)bot; c(+)bot; c(?)bot; "exact message"; bot && help. Words use Unicode NFC/case folding by default and surrounding punctuation is ignored. Up to 20 expressions, eight terms each, four wildcards per term. Send - to clear. Raw regular expressions are not accepted.
chm4-media-prompt = Send comma-separated types: text, photo, video, animation, document, album. Send all for every supported type.
chm4-command-prompt = Send one leading token, for example /ad or Promo, or - to disable. It must be the first word. Use Remove leading command to control removal after matching.
chm4-priority-prompt = Send a priority from 0 to 10000. Lower numbers win; the set ID breaks ties.
chm4-test-prompt = Send a sample text or one supported media item for a private preview. This does not publish or enable the rule. Use /cancel to leave.
chm4-no-match = This sample does not match the configured filters.
chm4-preview-result = Sample preview complete. Fallbacks: { $warnings }
chm4-source-collecting = Collecting / waiting
chm4-source-planned = Planned
chm4-source-ignored = Ignored
chm4-source-held = Held for review
chm4-source-report = Source { $id }, version { $version }: { $status }
    Issue: { $code }
    Fallbacks: { $warnings }
chm4-action-report = v{ $version } · { $kind } → { $destination }: { $status }; { $code }; message IDs: { $ids }
chm4-action-edit = Source edit
chm4-action-copy = Copy / copy edit
chm4-action-forward = Forward
chm4-action-sticker = Separator sticker
chm4-action-delete = Scheduled deletion
chm4-action-reminder = Manual deletion reminder
chm4-state-pending = Pending
chm4-state-succeeded = Done
chm4-state-failed = Failed
chm4-state-uncertain = Uncertain; review before replacing
chm4-state-cancelled = Cancelled
chm4-state-held = Held for review
chm4-state-skipped = Skipped
chm4-retry = Retry definite failure { $id }
chm4-error-keywords = Invalid or excessive keyword syntax. Use bounded token expressions, quoted whole messages, and &&; raw regular expressions are unsupported.
chm4-error-keyword_budget = Matching exceeded its bounded work limit. Shorten the expressions or source content.
chm4-error-filters = Choose supported media types and a single leading trigger token.
chm4-error-replacement = Use distinct literal whole words as replacement keys and old => new on each line.
chm4-error-forward_edits = Edit propagation is supported for copies. Choose copy mode or turn propagation off.
chm4-error-route_cycle = This route would create a forwarding cycle. Choose another destination or disable a conflicting route.
chm4-error-no_safe_retry = Only definite failures can be retried. Review uncertain deliveries externally; create a new source edit after configuration changes.
chm4-error-unsupported_media = This source type is outside the supported automation subset.
chm4-admin = Automation: { $collecting } collecting, { $held } held, { $failed } failed, { $uncertain } uncertain.
chm4-menu = Source automation
cmd-members = Admission and member workflows
chm5-menu = Member workflows
chm5-admin = Members: { $pending } pending, { $held } held, { $uncertain } uncertain; cleanup obligations: { $cleanup }.
chm5-permanent = Permanent
chm5-choose = Select a managed channel. Native posting and invite-user rights are required. Settings start disabled.
chm5-policy = Channel { $channel }: enabled { $state }
    Approval: { $mode }; captcha: { $captcha }; required chats: { $required }.
    Policy changes hold pending requests for explicit adoption. Release and bulk actions still require every gate.
chm5-mode-manual = Manual release
chm5-mode-immediate = Immediate after gates
chm5-mode-timed = Delay after request
chm5-queue = Observed admission queue
chm5-bulk = Bulk release
chm5-mode = Change approval mode
chm5-delay = Approval delay
chm5-expiry = Request expiry
chm5-captcha = Toggle math captcha
chm5-attempts = Captcha attempt limit
chm5-required = Ordered required chats
chm5-content = Welcome and introduction
chm5-filters = Admission filters
chm5-departure = Departure actions
chm5-events = Event log and service cleanup
chm5-results = Recent member action results
chm5-enable = Review and enable
chm5-disable = Disable future member work
chm5-intro = Introduction before approval
chm5-welcome = Welcome after approval
chm5-goodbye = Private goodbye
chm5-filter-summary = Total block: { $block }; requests/joins per 10 seconds: { $rate }; rejection: { $outcome }.
chm5-outcome-decline = Decline request / temporary removal after join
chm5-outcome-ban = Ban rejected users
chm5-total-block = Toggle total block
chm5-rate = Ten-second threshold
chm5-outcome = Change rejection outcome
chm5-names = Blocked name expressions
chm5-usernames = Blocked username expressions
chm5-alphabet = Profile alphabet rule
chm5-languages = Profile language rule
chm5-unknown-language = Toggle rejection of missing language
chm5-departure-summary = Voluntary-departure ban: { $ban }; duration seconds: { $duration }; linked group: { $group }.
chm5-ban = Toggle voluntary-departure ban
chm5-ban-duration = Departure ban duration
chm5-linked = Linked discussion group
chm5-event-summary = Log channel: { $log }; language: { $language }.
    Events: { $events }
    Cleanup: { $cleanup }
chm5-log-channel = Log destination
chm5-log-language = Toggle log language
chm5-log-events = Select logged events
chm5-cleanup = Select service cleanup
chm5-enable-confirm = Enable this channel's saved member policy? Every enabled gate must pass before approval. Initial contact has Telegram's short request window; later welcome/goodbye delivery requires actual private interaction. Departure bans apply only to voluntary departures. Required chats and moderation rights are checked again at dispatch. Existing held requests need explicit adoption.
chm5-prompt-content = Send formatted text or one photo, video, GIF, or document, or - to clear. This uses the shared composer. Introduction reserves 512 UTF-16 units for admission instructions. Configure link/native-copy buttons separately. Albums, vote callbacks, replies, pins, and content timers are unsupported here.
chm5-prompt-buttons = Send link buttons as Label - https://example.com, && between columns, and new lines between rows. Native copy uses Label | copy | text. Send - to clear. Other callback types are unavailable in member messages.
chm5-prompt-duration = Send a duration such as 60s, 10m, 2h, or 1d. Delay must be shorter than request expiry. Expiry is 1 minute to 7 days; delay is at most 1 day.
chm5-prompt-ban-duration = Send a ban duration from 1 minute to 365 days, such as 1h, or permanent. Timed bans keep a durable safe-unban obligation.
chm5-prompt-attempts = Send the maximum captcha attempts, from 1 to 10. A policy adoption never restores used attempts.
chm5-prompt-required = Send one required chat per line as -1001234567890 https://t.me/example. This bot must administer each chat. Checks follow this order. The admission source cannot require itself. Send - to clear.
chm5-prompt-rate = Send the allowed observed requests/joins in ten seconds, from 1 to 10000, or - to disable. Request arrivals and direct joins are counted separately. Excess users receive the configured rejection action.
chm5-prompt-keywords = Send one bounded keyword expression per line, or - to clear. Whole-token matching, quoted exact messages, token wildcards, and unordered && use the source automation keyword contract.
chm5-prompt-alphabet = Send allow LATIN,ARABIC or block CYRILLIC. Supported scripts: LATIN, ARABIC, CYRILLIC, GREEK, HEBREW, DEVANAGARI, THAI, HANGUL, HIRAGANA, KATAKANA, CJK, OTHER. Use block with no list to clear. Only letters in the displayed name are checked.
chm5-prompt-languages = Send allow en,ar, block en, or any. Codes are lowercase. Missing language is allowed unless its separate rejection toggle is enabled. Profile language is a preference, not proof of identity.
chm5-prompt-linked = Send the source channel's actual linked supergroup ID, or - to clear. Departure bans must be enabled. You and the bot need restriction rights there.
chm5-prompt-log = Send a connected log-channel ID, or - to clear. You need posting rights there and the bot must administer it. Logs contain source/user IDs and event/outcome codes.
chm5-prompt-logevents = Send comma-separated request, approved, declined, expired, joined, left, removed, banned, unbanned, filter_rejected, contact_failed, cleanup_failed. Send all or -.
chm5-prompt-cleanup = Send comma-separated new_chat_title, new_chat_photo, delete_chat_photo, pinned_message, video_chat_started, video_chat_ended, video_chat_scheduled. Send all or -. Only observed allowlisted service messages are removed; Telegram can reject unsupported deletions.
chm5-prompt-bulk = Send a count from 1 to 5000, or all for up to 5000 recorded requests. This snapshots the observed queue for confirmation; it does not enumerate Telegram's unseen queue.
chm5-bulk-confirm = Release the manual condition for { $count } recorded requests? Captcha, required membership, filters, delays, configuration, expiry, and generation checks still apply. Stale/held requests are skipped. No gate is bypassed.
chm5-bulk-result = Selected { $selected }; released { $released }; skipped/stale { $skipped }. Approval results appear in the admission queue.
chm5-request = User { $user }, request generation { $generation }: { $status }
    Reason: { $code }; captcha solved: { $solved }; attempts: { $attempts }; required chats passed: { $required }.
    Expiry: { $expiry }
chm5-action = { $kind }: { $state }; { $code }
chm5-release = Release manual condition
chm5-decline = Decline request
chm5-adopt = Adopt current policy
chm5-copy-start = Copy member continuation link
chm5-retry-queued = Safe retry queued. Successful/uncertain work is not resent.
chm5-invalid = This setting or menu is invalid/stale, or required rights are unavailable. Reopen /members and review the policy. Only definite failures under the current request/policy can be retried.
chm5-continue = Continue privately with this bot
chm5-question = Solve { $a } + { $b }. Starting the bot keeps this workflow reachable beyond the temporary request-contact window.
chm5-ready = Review the required chats, then check progress. Every enabled condition must pass before approval. Continue privately to establish ongoing contact with this bot.
chm5-check = Check all admission conditions
chm5-join-required = Join required chat { $number }
chm5-approved = Your admission is approved. Any configured welcome is delivered only through established private interaction.
chm5-attempts-used = The captcha attempt limit was reached. This request will be declined; old buttons cannot reset it.
chm5-gate-unavailable = Membership verification is temporarily unavailable. No requirement was marked complete. Try again later.
chm5-gate-stale = This request/link is expired, belongs to another user, or no longer matches the current workflow. Ask the channel operator to review your request.
chm5-progress = Progress saved; all admission conditions still apply.
chm5-log = Channel { $channel }; user { $user }; { $event }; { $code }
chm5-event-request = Join request observed
chm5-event-approved = Admission approved
chm5-event-declined = Request declined
chm5-event-expired = Request expired
chm5-event-joined = Member joined
chm5-event-left = Voluntary departure
chm5-event-removed = Administrator/bot removal
chm5-event-banned = Ban confirmed
chm5-event-unbanned = Unban cleanup outcome
chm5-event-filter_rejected = Admission filter rejected
chm5-event-contact_failed = Initial contact unavailable
chm5-event-cleanup_failed = Service cleanup failed
chm5-status-pending = Pending gates
chm5-status-held = Held for adoption/review
chm5-status-approved = Approved
chm5-status-declined = Declined
chm5-status-expired = Expired
chm5-status-superseded = Superseded by rejoin
chm5-status-uncertain = Uncertain; reconcile externally
chm5-status-cancelled = Cancelled
chm5-kind-contact = Initial contact
chm5-kind-approve = Approval
chm5-kind-decline = Decline
chm5-kind-ban = Ban
chm5-kind-unban = Safe unban cleanup
chm5-kind-welcome = Welcome
chm5-kind-goodbye = Goodbye
chm5-kind-log = External event log
chm5-kind-clean = Service cleanup
chm6-choose = Choose a channel.
chm6-channel = Channel: <b>{ $title }</b>
chm6-invalid = This action is unavailable or the input is invalid. Refresh the menu and try again.
chm6-queued = Queued. Check the result after processing.
chm6-saved = Saved.
chm6-invitations = Invitation gate
chm6-invite-policy = Required: { $count }; timeout: { $seconds } seconds; invitation-only bypass: { $bypass }. Captcha and required memberships still apply.
chm6-invite-threshold = Required invitations
chm6-invite-timeout = Invitation timeout
chm6-invite-bypass = Toggle invitation-only bypass
chm6-prompt-threshold = Enter 0 to disable, or the required number of distinct qualifying requests/joins. Self-referrals and repeat invitees do not count.
chm6-invite-progress = Invitation progress: { $count } / { $required }
chm6-share-invite = Share your invitation
chm6-unlock = Unlock privately
chm6-unlock-required = Join the source channel and each required chat, then reopen the original unlock link. Access is checked again when the content is delivered.
chm6-edit-team = Grant, change or revoke access
chm6-delegate = User { $user }; active: { $status }; permissions: { $permissions }
chm6-prompt-team = Send a Telegram user ID followed by comma-separated permissions: create, edit_own, edit_all, delete_own, delete_all, schedules, settings. To revoke, send: USER_ID revoke. Only channel owners or admins with promotion rights may delegate.
chm6-team-confirm = Apply access for user { $user }: { $permissions }?
chm6-adopt = Adopt queued posts
chm6-prompt-adopt = Send the post ID to adopt. Queued work will be held for your review and must be published or scheduled again explicitly.
chm6-adopted = Ownership updated. Review the held post and explicitly publish or schedule it again.
chm6-lock-item = Manage locked post
chm6-new-lock = New locked post
chm6-prompt-teaser = Send the public teaser as text or supported media. Upload media to this bot.
chm6-prompt-secret = Send the private secret content. It will be delivered with content protection after membership checks.
chm6-prompt-requirements = Send ordered requirements, one per line: CHAT_ID https://t.me/… . Send - for only the source channel. You and this bot must administer additional chats.
chm6-lock-created = Saved the public teaser and private secret. Open the post to preview and confirm publication.
chm6-lock-details = Locked content { $id }; active: { $status }.
    Private link: { $url }
chm6-secret-edit = Change private content
chm6-prompt-editsecret = Send the replacement secret content. Public messages will keep the teaser.
chm6-disable-lock = Disable unlock link
chm6-new-campaign = Prepare campaign
chm6-prompt-campaign = Send campaign content. The preview will snapshot only this bot's reachable, channel-associated users who explicitly opted in. Nothing is sent until you confirm.
chm6-campaign-summary = Campaign { $id }
    Snapshot: { $count } recipients; status: { $status }.
    Check the content and audience count before sending. Snapshot expires after 15 minutes.
chm6-send-campaign = Confirm campaign send
chm6-review-unsent = Review definite unsent recipients
chm6-invoices = My invoices and payment review
chm6-catalog = Manage plan catalog
chm6-no-plans = No published plans. Prices must be configured and published by a platform administrator.
chm6-limits = Limits: schedules { $schedules }, rules { $rules }, routes { $routes }, delegates { $delegates }, locked posts { $locks }, campaign recipients { $recipients }.
chm6-invoice-summary = Invoice { $id }
    Channel: { $channel }; plan: { $name }
    { $amount } Stars; { $seconds } seconds; { $kind }.
    Status: { $status }. Quote expires: { $expiry }.
chm6-impact = Potential excess: schedules { $schedules_held }, rules { $rules_held }, routes { $routes_held }, delegates { $delegates_held }, locks { $locks_held }. Excess work is held; saved content and cleanup obligations are retained.
chm6-send-invoice = Send Stars invoice to me
chm6-refund = Review full refund
chm6-refund-confirm = Refund the full { $amount } Stars charge? Its unused channel time will be removed, later paid periods rebased, and dependent upgrades held for review. Consumed time is not transferred. Telegram confirms the refund result.
chm6-checkout-denied = This quote is unavailable or your channel access changed. Request a fresh invoice.
chm6-plan-new = Create unpublished plan
chm6-prompt-plan = Send three lines:
    Plan name
    tier rank days Stars
    schedules rules routes delegates locks recipients invite_threshold branded
    Use yes or no for branded. Numeric limits may be zero. Review the draft before publishing.
chm6-plan-review = Unpublished plan: { $name }; { $days } days; { $stars } Stars. Publishing makes this immutable price version available for new invoices.
chm6-publish-plan = Publish this plan version
chm6-retire-plan = Retire this plan version
chm6-catalog-guide = Plan versions keep their original price and limits. Open a version to review publishing or retirement. No plan is published automatically.
chm6-plan-kind = Renewals and downgrades start after already paid periods. An upgrade applies now for the remaining current period, with a prorated Stars quote.
chm6-renew = Renew / buy next period
chm6-upgrade = Upgrade current period
chm6-downgrade = Schedule lower plan
chm6-payment-review = Review unapplied payment
chm6-control-billing = Open the control bot for billing
chm6-sender-guide = Create a Channel Manager bot in the factory, connect this channel in both bots, then choose an owned active sender. Each sender has its own posts, leads and file IDs. Upload media to the selected sender.
chm6-bind-confirm = Use this bot as the full Channel Manager for the channel? New publication from the control bot will pause. Configure and upload content in the selected sender. Billing stays in the control bot.
chm6-unbind = Return to control sender
chm6-unbind-confirm = Return publication to the control bot? Review held work before explicitly publishing or scheduling it again.
chm6-menu-edit = Configure menu and feedback
chm6-prompt-menu = Send the subscriber menu content. Feedback will be enabled for this menu.
chm6-prompt-menulinks = Send link buttons, one row per line: Label - https://example.com . Send - for no links.
chm6-feedback = Feedback inbox
chm6-prompt-feedback = Send your feedback (up to 3500 characters). It will go to this channel's configured operator.
chm6-reply = Reply privately
chm6-prompt-reply = Send one private reply. It will be queued once for this feedback item.
chm6-subscriber-choose = Choose one of your associated channels.
chm6-subscriber-actions = Choose an action. Campaign subscriptions are optional and separate from admission.
chm6-subscribe = Opt in to campaigns
chm6-unsubscribe = Stop campaigns
chm6-subscribed = Subscribed to this channel's campaigns from this bot.
chm6-unsubscribed = Campaigns stopped for this channel and bot.
chm6-forget-confirm = Remove your campaign lead and feedback data for this channel and bot? A minimal opt-out marker remains to prevent automatic resubscription. Admission and payment records are retained.
chm6-forgotten = Campaign and feedback data removed. You can explicitly subscribe again later.
chm6-result-selected = Selected
chm6-result-pending = Pending
chm6-result-succeeded = Sent
chm6-result-failed = Failed
chm6-result-cancelled = Cancelled
chm6-result-uncertain = Unknown; manual review
chm6-result-skipped = Skipped
chm6-result-refunded = Refunded
chm6-result-refund_uncertain = Refund result unknown; contact support before retrying

chm6-invoice-delivery = Invoice delivery: { $status }. Unknown results require review; request a new quote if needed.

chm6-invoice-native = Channel { $channel }: { $kind }, { $seconds } seconds of service.
chm6-feedback-native = Channel { $channel } · feedback { $id }
    User { $user }
    { $text }
chm6-kind-renew = next prepaid period
chm6-kind-upgrade = current-period upgrade
chm6-kind-downgrade = next-period downgrade

chm6-unlock-source = Source: { $title }. Open the source channel where you found this link.

chm6-payment-manual = A payment of { $amount } in { $currency } needs support review. Native Stars refunds apply only to XTR charges.

chm7-admin = Growth failed / uncertain: { $growth_failed } / { $growth_uncertain }
    Payments / refunds requiring review: { $billing_review } / { $refund_review }
    Paused senders: { $sender_paused }; cleanup backlog: { $cleanup_backlog }
    Oldest due operation / inbox age: { $operation_lag_seconds }s / { $inbox_lag_seconds }s
chm7-paused = This feature is paused for rollout or maintenance. Saved data and required cleanup are retained.

