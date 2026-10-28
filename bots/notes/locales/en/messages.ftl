## Notes & Reminders — English. Shared keys (buttons, VIP, admin...) come from core/locales.
notes-start =
    👋 Hello, <b>{ $name }</b>!

    📝 Send me any text and I'll keep it as a note.
    ⏰ Use <code>/remind 10m call mom</code> to get a reminder.
notes-help =
    ℹ️ <b>How it works</b>

    • Any text you send becomes a note — /notes lists them.
    • <code>/remind 30m stretch</code>, <code>/remind 2h …</code>, <code>/remind 1d …</code> or <code>/remind 18:30 …</code> (UTC)
    • /reminders shows what's coming up.
notes-btn-notes = 📝 My notes
notes-btn-reminders = ⏰ Reminders
notes-btn-delete = 🗑 Delete #{ $id }
notes-btn-cancel-reminder = ✖️ Cancel { $when }
notes-btn-admin-tab = 📝 Notes
notes-saved = ✅ Saved as note <b>#{ $id }</b>.
notes-list-title = 📝 <b>Your notes</b> ({ $count }/{ $max })
notes-empty = No notes yet — just send me some text.
notes-limit-notes = 📦 You've reached { $max } notes. Delete some, or get 💎 VIP for more.
notes-remind-usage = ⏰ Usage: <code>/remind 10m text</code> — units m/h/d, or a time like <code>18:30</code> (UTC).
notes-remind-set = ⏰ Got it! I'll remind you at <b>{ $when }</b> UTC.
notes-limit-reminders = ⏰ You already have { $max } upcoming reminders. Get 💎 VIP for more.
notes-reminders-title = ⏰ <b>Upcoming reminders</b> ({ $count })
notes-reminders-empty = Nothing scheduled.
notes-reminder-fire = ⏰ <b>Reminder</b>

    { $text }
notes-adm =
    📝 <b>Notes</b>

    • Stored notes: <b>{ $notes }</b>
    • Pending reminders: <b>{ $pending }</b>
    • Delivered reminders: <b>{ $sent }</b>
vip-perks =
    ✅ Up to { $notes } notes
    ✅ Up to { $reminders } upcoming reminders
vip-status-none = ⚪ Free plan: { $free_notes } notes, { $free_reminders } reminders.
cmd-notes = Your notes
cmd-remind = Set a reminder
cmd-reminders = Upcoming reminders
