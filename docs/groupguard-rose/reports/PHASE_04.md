# Phase4 real verification and source ownership

Starting ba3ae36. All local gates pass. Continuing automatically to Phases5–12; this is not the final review/deployment handoff.

Delivered actual button/default and text/math/text2 modes. Nonbutton group challenges open a personal scoped PM link; PNGs are generated using Pillow and bundled OFL font. Text selects pictured word, math solves pictured equation, text2 advances four characters with SQL sequence fences. Choice-index callbacks stay within64 bytes at maximum supported IDs. Actual PM/card receipts bind generation/message/chat/thread and invalidate prior cards. Correct question with rules enabled displays actual frozen rules and requires a separate attributable acceptance before release/approval. Plaintext labels preserve literal braces; no fillings.

Settings and panel use fresh change-info/bot-admin rights. Welcomes required for new issuance. Explicit kick duration5m..1day/default5m, legacy captcha_minutes preserved; kick toggle, automatic release60s..1day/off. Captured policy/deadline/answer/progress survives settings changes. Correct release/approval records verified per group; timer release never does. Voluntary leave retains memory; admin kick clears it. Admin promotion retires only CAPTCHA's own mute without punitive API. Three wrong answers apply a real one-hour local temporary owned ban. Kick off expires the interactive card after24h while retaining own mute; documented local choice.

Join requests use actual user_chat_id and original integer request.date+300s contact window; callbacks cannot extend it or approve around active owned bans. Fresh bot invite capability remains required. Group/PM queries, stale/forged/another-user/another-child/changed-message callbacks, original deadlines and current member/bot authority are checked. Group approvals bypass CAPTCHA/newbie automation; CAS stays a security check. Federation/raid integration follows owning phases, not an inferred broad exemption.

Known failed final release may retry within original deadline; unknown punitive mutation stays uncertain and cannot replay. Partial timeout kick receives a durable job that only completes its accepted ban's owed unban, never a second ban. Unattached issuance after240s refunds only transient own verification mute and does not mark human. Other manual/fed/night sources remain. Owned ban removal beside unrelated mute performs actual unban and retains/reapplies mute on rejoin. CAPTCHA no-deadline interrupted kick may retire from actual current member proof; timed punitive/other sources stay active. Primary state/intents commit before ancillary prompt deletion; cleanup failure cannot erase ownership.

Migration0013 adds prompt/progress/question/rules fields and bot/chat/user/semantic join receipts. Receipts commit processing before effects, finish completed/uncertain and suppress concurrent/duplicate identical joins across update IDs; seven-day bounded hash-only retention. No names/private invite URLs stored in receipt. Old config/answer/policy/media stay intact. Identical otherwise-unobservable same-second membership intents cannot be distinguished perfectly; no exactly-once guarantee or full live Rose archive claim.

Ledger824 rows/813 canonical IDs retained; Phase4 scope41:39 tested local subsets/two external CAS/AI delivery limits. Direct external provider operation and deployed Bot API are not certified. All31 published translations/help/UI and subsequent protection/utilities/federations/privacy/final independent review remain required later stages.

| Exact local gate | Result |
|---|---|
| .venv/bin/pytest tests/bots/groupguard/test_phase04.py -q -x |61 passed across standalone/two actual ChildRegistry contexts |
| Prior wired Group Guard regression (collection before latest added CAP cases) |173 passed/one factory-only standalone skip |
| .venv/bin/pytest -q --tb=short (frozen production/catalog) |856 passed/48 explicit skips,0 failures |
| TEST_GG_DATABASE_URL=<gg_long_concurrency> TEST_GG_REDIS_URL=<taskRedis/2> .venv/bin/pytest tests/integration/test_groupguard_foundations.py -q --tb=short |42 passed; concurrent semantic joins, partial kick compensation, interrupted issue/refund and all prior foundations |
| TEST_DATABASE_URL=<gg_long_integration> TEST_REDIS_CLAIM_URL=<taskRedis/1> .venv/bin/pytest tests/integration/test_migrations.py tests/integration/test_groupguard_review.py -q |4 passed; fresh/legacy/schema diff/roundtrip/real Redis |
| TEST_DATABASE_URL=<gglong> TEST_REDIS_URL=<taskRedis/0> .venv/bin/pytest tests/e2e -q |1 runtime pass |
| .venv/bin/ruff check .; .venv/bin/mypy; git diff --check |pass;264 typed source files |

The48 full-suite skips are42 foundation+4 migration/Redis+1 runtime separately passed, plus factory-only standalone inapplicability (both actual child variants exercised). No suppression/xfail/dependency hiding. Recording API supports valid caption/markup edit acknowledgements; failure injection preserved. Existing generation replacement fixture explicitly resets and emits a fresh server event date instead of redelivering a same-second event; all old fence assertions retained. Repeat fixture uses stable distinct due timestamps. Request dates model real integer server dates rather than fractional rounding artifacts. Source/intent state precedes ancillary cleanup.

Evidence: evidence/long-running/phase04; exact code/schema paths and row tests in feature-evidence.csv. Local task-owned services retained for later stages. No live Telegram, production data, deploy/merge or source parity self-certification. Downgrade removes new metadata/receipts; preserve backup before migration rollback. Continuing to prepared phase05-design.md.
