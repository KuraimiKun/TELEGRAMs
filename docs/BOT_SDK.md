# Writing a bot

A bot is a Python package under `bots/<slug>/` that exports `module = MyBot()`, an instance of
`core.sdk.module.BotModule`. The platform discovers it, builds an isolated aiogram `Dispatcher` for it,
and gives it the whole core: users, payments, VIP, referrals, force-subscribe, admin panel, broadcasts,
scheduling, i18n, metrics.

```bash
python -m core new-bot quiz --title "Quiz Bot"     # working skeleton + smoke test in tests/bots/quiz
python -m core makemigrations -m "add quiz tables" && python -m core migrate
python -m core bots && python -m core dev
```

`bots/notes` is a complete, small reference implementation.

## 1. The module contract

```python
class QuizBot(BotModule):
    slug = "quiz"                       # 2-32 chars [a-z0-9_]; env vars are QUIZ_*
    title = "Quiz Bot"
    table_prefix = "quiz_"              # every table of this bot starts with it (unique per bot)
    features = {Feature.ADMIN, Feature.LANG, Feature.VIP, Feature.REFERRAL, Feature.BROADCAST,
                Feature.FORCE_SUB, Feature.GROUPS, Feature.DAILY_STATS}
    env_model = QuizEnv                 # subclass of BaseBotEnv (token, admin_ids, log_channel_id, ...)
    settings_model = QuizSettings       # subclass of BaseBotSettings — editable live in /admin
    locales_dir = Path(__file__).parent / "locales"
    default_plans = [PlanSpec("1 Month VIP", days=30, stars=100)]
```

| Hook | Purpose |
|---|---|
| `async setup(ctx)` | Create your services and store them in `ctx.extras` (injected into handlers by name) |
| `routers(ctx)` | Return **fresh** `Router`s — never module-level singletons (one dispatcher per bot) |
| `commands()` | `CommandSpec`s for the command menu; descriptions are localized via `cmd-<command>` keys |
| `admin_sections()` | Extra `/admin` tabs: `AdminSection(tab, title_or_i18n_key, router_factory)` |
| `processes()` | Long-running processes (`python -m core run <slug> <name>`); stop when `ctx.shutdown` is set |
| `scheduled_jobs()` | `ScheduledJob(name, interval, handler, timeout)` — single-flight across replicas, wall-clock persisted |
| `factory_jobs()` | `FactoryJob(name, interval, handler, timeout)` — one scheduled sweep across children of this template |
| `async stats(ctx)` | `StatLine`s shown in `/admin → Stats` and the daily report |
| `throttle_rate(user)` | Seconds between accepted messages/callbacks (default 1.0 free / 0.4 VIP) |
| `throttle_exempt(event)` | Default false; exempt bounded media collection from per-message throttling |
| `async vip_info(ctx)` | Variables for your `vip-perks` / `vip-status-none` messages (show real limits) |
| `async reset_user_limits(ctx, user_id)` | Backs the admin "Reset limits" button |
| `async on_force_sub_passed(ctx, user, payload, chat_id)` | Resume a request after the user joined the required channels |

## 2. What a handler receives

Every handler can declare these parameters (aiogram injects them by name):

- `ctx: BotContext` — `ctx.bot`, `ctx.sm` (SQLAlchemy sessions), `ctx.redis`, `ctx.keys(...)` (namespaced
  Redis keys), `ctx.settings`, `ctx.users`, `ctx.subs`, `ctx.payments`, `ctx.groups`, `ctx.broadcast`,
  `ctx.audit`, `ctx.forcesub`, `ctx.translator`, `ctx.username`, `ctx.ai`, plus everything in `ctx.extras`.
- `user: BotUser` — this user's membership in *this* bot (lang, VIP, ban, prefs, referral data).
  Absent for plain group chatter (no link, no command), which is intentionally not tracked.
- `t: Translate` — `t("key", var=value)` in the user's language; `lang: str` — that language code.
- `is_new_user: bool` on the first update of a new member.

## 3. Rules

1. **Escape untrusted text** (user names, titles, any input) with `core.ui.text.esc` — messages use HTML.
2. **Use `core.ui.respond.show(event, text, kb)`** to answer a button press by editing its message: it
   handles messages that can no longer be edited (older than 48 h).
3. **Count your core action** with `await core.sdk.actions.record_user_action(ctx, user_id)` — this is
   what qualifies referrals and rewards referrers.
4. **Gate with force-subscribe** (if enabled) before the core action:
   ```python
   if not await require_subscription(ctx, user, chat_id, t, payload={"text": text}):
       return  # prompt shown; on_force_sub_passed(payload) runs after the user joins
   ```
5. **Callback data**: core uses the `c_` prefix; choose your own short prefix. Bind menus to their owner
   (see `PendingRequest` in socialdownload) and never trust ids from callback data without a check.
6. **Redis keys** always via `ctx.keys("part", ...)`. Durable state (queues, locks) on `ctx.redis`;
   evictable caches on `ctx.cache_redis or ctx.redis`.
7. **Money and VIP** only through `ctx.subs` / `ctx.payments` (ledgered, idempotent, row-locked).
8. **Admin screens**: build with `core.routers.admin.common` (`admin_router`, `nav`, `btn`, `markup`,
   `back_row`, `show`), record mutations with `ctx.audit.record(admin_id, "thing.action", target, ...)`.

## 4. Translations

- Put strings in `locales/<lang>/messages.ftl`. Core strings (buttons, VIP, admin, errors) live in
  `core/locales` and can be overridden by a bot. Language codes are resolved with aliases and fall back
  to `DEFAULT_LANG`.
- Pass numbers as values (`t("x", count=n)`); they are rendered as plain text. Format grouping yourself
  where wanted (`f"{n:,}"`).
- `tests/test_locales.py` enforces that every language of a bot has the same keys **and variables**, and
  that every key used in code exists.

## 5. Data

- Models subclass `core.db.base.Base`, table names start with `table_prefix`, timestamps use
  `TZDateTime()`, Telegram ids use `BigInt`.
- `python -m core makemigrations -m "..."` writes the next sequential Alembic revision; commit it.

## 6. Testing

`tests/conftest.py` provides an in-memory database, fakeredis and a recording Bot API session:

```python
async def test_my_command(sm, redis, api, tmp_path, builders):
    ctx = await build_test_ctx(discover(["quiz"])[0], sm, redis, api, tmp_path)
    dp = build_dispatcher(ctx)
    await dp.feed_update(ctx.bot, builders["message"]("/ping", user_id=1))
    assert api.calls("SendMessage")[-1].text == ctx.translator.get("en", "quiz-pong")
```

`api.responses["MethodName"] = value_or_callable` scripts Bot API replies.

`tests/e2e/test_platform_flow.py` also runs the CLI gateway, scheduler and document worker against a
mock HTTP Bot API with real PostgreSQL and Redis 7+. Set `TEST_DATABASE_URL` to a local role with
`CREATE DATABASE` permission and `TEST_REDIS_URL` to an empty disposable Redis database. The harness
creates/drops a private PostgreSQL database, clears that Redis database afterward, injects scripted
AI and checks full webhook conversations plus clean shutdown. It never reads the workspace `.env`
inside its runtime subprocess or calls live Telegram/AI services.

## 7. Factory templates

A template uses the same module, handlers, tables and locales as a standalone bot. Declare its factory
key and reduced feature set on the module:

```python
class FeedbackBot(BotModule):
    slug = "feedback"
    table_prefix = "fb_"
    standalone = False
    factory_template = "feedback"
    child_features = {Feature.ADMIN, Feature.LANG, Feature.BROADCAST}
```

`standalone=False` excludes a package from gateway, scheduler and process discovery. It still appears
in `discover(..., include_templates=True)` and `factory_templates()` and is validated by
`python -m core bots`. A module can be both standalone and a template: `anonymous` and `groupguard`
do this. Template keys must be unique; `feedback` and `custom` are the factory-only keys.

Child contexts have `ctx.child` with `owner_id`, `template`, `factory_username` and `branding`;
`ctx.slug` and Redis keyspace are `c<telegram_bot_id>`. Always scope database operations by
`ctx.bot_id` and Redis operations through `ctx.keys`, including when multiple children share a
module. The child owner is an admin; platform super-admins retain their normal access.
Use `ctx.features` when checking enabled capabilities. Child VIP/payments and referrals are disabled
because payments to a child token belong to its owner.

`core.factory.branding.credit(ctx, t)` renders the factory attribution for child start/help screens.
Respect `ctx.child.branding`; the factory controls whether its VIP owner may remove it. Token
lifecycle operations belong to `ChildService`, which encrypts tokens, updates webhooks and publishes
`platform:factory:changed`. `ChildRegistry` listens for that event and evicts the cached context.

Ordinary `scheduled_jobs()` run for standalone contexts. For periodic child work, define
`factory_jobs()` whose handler receives the shared `ChildRegistry` and sweeps relevant children.
Group Guard uses this for captcha expiry and night mode. Do not create a timer or scheduler per child.

## 8. AI layer

`SharedInfra` builds one metered `AIClient` per process. `ctx.ai` is `None` when the selected provider
has no API key. Hide optional AI buttons in that case and return the localized `ai-unavailable`
message when the action is requested directly. Claude (`AI_PROVIDER=anthropic`) is the default;
OpenAI (`AI_PROVIDER=openai`) uses the same interface. `AI_MODEL` and `AI_FAST_MODEL` override the
provider's configured model defaults.

```python
from core.ai.base import AIError, AIUnavailable, Attachment

if ctx.ai is None:
    await message.answer(t("ai-unavailable"))
    return
try:
    result = await ctx.ai.ask(
        "Analyze this document in the user's language.",
        system="Return factual, concise advice.",
        bot=ctx.metric_name,
        user_id=user.user_id,
        attachments=[Attachment.pdf(pdf_bytes)],
        schema={"type": "object", "properties": {"summary": {"type": "string"}},
                "required": ["summary"], "additionalProperties": False},
        max_tokens=2000,
    )
except AIUnavailable:
    await message.answer(t("ai-unavailable"))
except AIError:
    await message.answer(t("error-unknown"))
else:
    await message.answer(esc(result.data["summary"]))
```

`ask` accepts a string or a sequence of `Turn(role, text)`, optional `Attachment.image(...)` or
`Attachment.pdf(...)`, a JSON schema, token limit and `fast=True` for brief classification or hints.
`AIResult` contains `text`, parsed `data`, `model`, `input_tokens` and `output_tokens`. Provider
implementations subclass `AIProvider` and implement `complete(AIRequest) -> AIResult` plus `close()`.
Keep provider-specific SDK calls out of bot handlers.

The client records daily shared and per-bot/user Redis token counters and request/token metrics.
`AI_DAILY_TOKEN_BUDGET` and `AI_CONCURRENCY` protect capacity; apply the bot's `DailyQuota` separately
for user-facing free/VIP action limits. Never treat a provider response as trusted HTML. Tests can
assign the client returned by `tests.fake_ai.fake_ai(redis, reply)` to `ctx.ai` for scripted output
without API calls.

Use `core.files.scratch_dir` and `fetch_bytes` for capped Telegram downloads and temporary cleanup.
Do not store original documents, passwords or extracted content in persistent SQL job metadata.
CV reports store only the resulting analysis summary and `/forget` removes it. Document Tools uses
temporary Redis jobs containing Telegram file references, pasted text, operation passwords and
generated summaries/quizzes for retries. Jobs expire after six hours without renewal and are deleted
on completion; leases renew the job TTL. Baskets expire ten minutes after the first file. Protect Redis and its AOF/backups
with the same access controls as other private user data.
