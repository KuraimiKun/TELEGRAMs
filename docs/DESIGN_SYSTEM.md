# Design system

Visual and interaction conventions shared by every bot so they feel like one product. Architecture and
the bot contract are documented in [BOT_SDK.md](BOT_SDK.md); running the platform in
[OPERATIONS.md](OPERATIONS.md).

## Messages

- HTML parse mode everywhere. Bold for the subject (`<b>`), `<code>` for ids and values users may copy.
- First line: emoji + bold title (`core.ui.text.title(E.STATS, "Analytics")` → `📊 <b>Analytics</b>`).
- Key/value lists: `kv("Users", "1,234")` → `• Users: <b>1,234</b>`.
- Escape every untrusted string with `esc()` (names, media titles, admin input, exception text).
- Numbers: group large counts (`f"{n:,}"`), never ids. Durations: `human_duration(125)` → `2:05`;
  sizes: `human_size(1_500_000_000)` → `1.4 GB`; speeds: `human_speed(...)`.
- Progress: `progress_bar(75)` → `▰▰▰▰▰▰▰▰▱▱`, edited at most every 3 s (6 s in groups).

## Keyboards

- One action per button, verb first ("🔍 Search", "🗑 Delete #12"). Two buttons per row by default.
- The last row navigates: `⬅️ Back` (to the parent screen) and/or `✖️ Close`.
- Lists paginate with `◀️ 2/5 ▶️` rows (`core.routers.admin.common.pager`).
- Destructive or paid actions get an explicit confirmation step.
- Pressing a button edits the message in place (`core.ui.respond.show`); typed input gets a reply.

## Emoji tokens (`core.ui.emoji.E`)

Navigation `BACK ⬅️`, `CLOSE ✖️`, `REFRESH 🔄` · states `OK ✅`, `ERR ❌`, `WARN ⚠️`, `INFO ℹ️`,
`WAIT ⏳`, `LOCK 🔒` · sections `STATS 📊`, `USERS 👤`, `GROUP 👥`, `BROADCAST 📢`, `CHANNELS 📡`,
`SETTINGS ⚙️`, `LANG 🌍`, `VIP ⭐`, `GIFT 🎁` · actions `ADD ➕`, `EDIT ✏️`, `DELETE 🗑`.
Prefer these over ad-hoc emoji.

## States users should always understand

| Situation | Pattern |
|---|---|
| Work takes time | Status message that is edited (queued → progress → done/error), with a Cancel button |
| Limit reached | Say which limit, when it resets, and offer 💎 VIP |
| Not allowed | Short reason; in groups stay silent rather than spamming the chat |
| Something failed | Plain-language cause (`error-<code>`), what to try next; never a stack trace |

## Language

Write strings in `locales/en` first, keep them short and friendly, then add every other language with
the same keys and variables (enforced by tests). Admin screens are localized too.
