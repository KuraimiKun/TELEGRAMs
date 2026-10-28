# Final Group Guard review handoff

Prepared13 October2026, Asia/Jakarta. The authorized cumulative stages1A closure,1B,1C,2–12 are implemented and locally gated. **Ready for final code review**, with the explicit differences below; this is internal validation, not independent certification, deployed readiness or full live Rose equivalence.

Repository:kunkura/TELEGRAMBOTS, branchwork. Initial source baseline96357ef45c6492e03c626581ce2ee156d2da3816, source tree7895f72031fd4fac13b4ff280ba04b16c8d5842c. Initial818 Phase1A ledger IDs all retained; final824 unique traceability rows. These rows include aliases/permissions/lifecycle, not824 independent features. Baseline cherry-picks cf3afa3067e4 and96357ef45c64, all scoped commits/user autosave593c6c3 retained. DocTools repair556b48b is separate and the original malformed-input assertion passes. Exact final commit/worktree/file identity and complete diff/history are in the archive's REVIEW/IDENTITY.json and manifests; current source/test/locale hashes are also in docs/groupguard-rose/evidence/long-running/phase12/source-closure.sha256.

| Family | Delivered behavior and review entry point |
| --- | --- |
| Delivery/actor foundations | Fresh precise rights/protected targets, immutable bound reviews, real group versus connected source, edits before core routes, durable inbox/outcomes; authz/operations/reviews/pipeline/replay and Phases1A–1C |
| Moderation/message tools | Sanction variants,60s–365d temporary bounds, self-kick, warnings/settings/expiry, approvals, exact promotion intersection, purge/pins/reports/logs; Phase2 |
| Content | Own rich renderer/entities/Unicode/buttons/options, notes/filters/rules/greetings/private links/repeats/media receipts; Phase3 |
| Verification/locks/blocklists | Owned generations/deadlines/request approval, typed modes/locks/exceptions/reaction diagnostics/pattern actions; Phases4–6 |
| Flood/raid/night | Actual effects, independent boundaries, durable cleanup/generations and permission snapshots/restart/ownership; Phase7 |
| Connections/policy/utilities | Current membership/rights, alias disable/cleanup parity, topics/confirmations, bounded owner broadcasts, bot review/silence/loop and native payment-before-cleanup; Phase8 |
| Federations | Own bot-scoped UUID/roles/membership/logs, bounded subscriptions/files/versioned bans/provenance/passive-before-CAP/fanout/quiet/source pages; Phases9–10 |
| Portability/privacy/UI |16 selected modules, actual files/creator/digest/revision/reset guard;19 safe own-data sections and durable cache cleanup;all31 native471-key bundles/25 shared159-key overlays/18 native guides;Phase11 |
| Cumulative repairs | Pure allowlist import, actual /info source pages/anonymous chat IDs, token-to-child-record fence before any runtime/cleanup SDK call;Phase12 audit |

| Check | Observed result |
| --- | --- |
| Final full repository suite |1,579 passed;130 skipped;zero failures;537.86s |
| Final PostgreSQL16/Redis7 foundations |117 passed;120.95s |
| Current migration/Redis review |4 passed;10.60s;fresh/head/base roundtrip and0009 seeded legacy |
| Final runtime E2E |1 passed;36.54s |
| Final Phase11/core/locale focus |138 passed;50.60s |
| Current real-service workloads |6 passed;55.96s |
| Supplemental configured limits/onboarding |6 passed;actual cap/API/SQL/link/branding/sibling effects |
| Related factory/Phase1C |41 passed;15.81s |
| Ruff/mypy/module contracts/pip |Pass;332 typed source files;9 modules;no broken requirements |

```sh
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/python -m pip check
.venv/bin/python -m core bots
.venv/bin/pytest -q --tb=short
.venv/bin/pytest -q tests/core/test_i18n_layering.py tests/test_locales.py tests/bots/groupguard/test_phase11.py --tb=short
.venv/bin/pytest -q docs/groupguard-rose/evidence/long-running/phase12/configured_caps.py --tb=short
TEST_GG_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_concurrency TEST_GG_REDIS_URL=redis://127.0.0.1:56380/2 .venv/bin/pytest -q tests/integration/test_groupguard_foundations.py --tb=short
TEST_GG_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_concurrency TEST_GG_REDIS_URL=redis://127.0.0.1:56380/2 .venv/bin/pytest -q -s tests/integration/test_groupguard_benchmarks.py --tb=short
TEST_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_integration TEST_REDIS_CLAIM_URL=redis://127.0.0.1:56380/1 .venv/bin/pytest -q tests/integration/test_migrations.py tests/integration/test_groupguard_review.py --tb=short
TEST_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gglong TEST_REDIS_URL=redis://127.0.0.1:56380/0 .venv/bin/pytest -q tests/e2e --tb=short
```

The130 default-suite skips are117 foundations+6 service benchmarks+4 migrations/review+1 runtime, all separately passing, and2 standalone factory-only inapplicabilities. Repository live-site cases are deselected by existing -m not live policy. Fast conversation/benchmark fixtures bypass throttling explicitly; actual runtime/middleware checks retain guards. Telegram is a recording SDK, PostgreSQL/Redis are real disposable services.

All117 foundation cases and six workloads use real dedicated PostgreSQL/Redis with a recording Telegram API. Standalone plus two actual ChildRegistry instances share a group; tests assert required/forbidden effects, current rights/replay/failure/ordering and sibling isolation. Fresh/legacy migrations and real runtime lifecycle are separate. Services are task-owned loopback resources and remain available for development; tested tools/start-groupguard-test-services.sh recreates them after environment restoration. Reusable cloud start_skill draft was saved, not published. requirements-verified.txt records95 tested installed distribution versions without credential/direct URL data.

Three instances123456/710011/710012 each process80 parallel delivered fixture updates into16 actual restriction calls and16 deletes: 1.684549–3.840625s. One ban in250 synthetic attached/observed groups yields250 actual SDK bans per instance: 12.889944–13.349636s, peak pending124;100 producer/sweep batches,20/sec realRedis quota, pending work drains. RealPostgreSQL16/Redis7, stateful recording SDK, conversation throttle bypass; already-delivered updates do not model Telegram stopping new messages after mute. These observations are local fixture workloads, not live/production throughput.

Translator32-bundle constructor:2.464785s cold;five warm0.017017–0.041070s;cache256,61 resident parsed resources, observed peakRSS83124KiB onPython3.12.14/Linux/five logical CPUs. Separate bundle args/resolvers and changed-file reload are tested. No production latency/capacity claim.

Remaining differences and external requirements:

- No verified full Rose export adapter/private federation network/cross-bot trust. Own v1 modules and CSV/JSONL/own federation formats are implemented. Five-minute own data interval/retention choices are local;30-minute federation interval is from the supplied digest.
- Native authored31-locale functional/key/placeholder/script/bounds coverage passes; native-language peer review has not certified grammar/tone. Same-language regional bases and Taiwan script/terminology adaptation are disclosed. Unseen Rose runtime-help additions remain unknown.
- runs/saved return an explicit unsupported explanation; antiflood is a documented read-only flood alias. Single-word new notes/legacy broader reads, prefix/cleaning tables and command length1..32 are deliberate recorded choices. Anonymous aggregate reactions lack an attributable removal target and receive a controlled diagnostic.
- Actual optional CAS/AI service behavior, deployed Bot API/version/BotFather event eligibility and live Rose parity are unverified. A source-site retry still returned CONNECT403; supplied50-page condensed digests/addenda and installed SDK introspection are provenance, not full-page archival/live evidence.
- Security/ownership/version/audit/order/uncertain external effects retain minimum records; shared platform preferences/global User/payments persist. Personal commands do not erase external Telegram messages/backups or invent a universal retention period. Remote exactly-once/ownership cannot be promised after an unknown RPC.

Independent review should begin with API_CONTRACTS.md, DECISIONS.md, OPERATOR_GUIDE.md, phase11/12 feature-evidence CSVs and AUDIT.md; then inspect authz/operations/reviews, portable reset/member locking, privacy_cache, token-bound factory startup/pause, fed intent/attachment lock ordering and shared core middleware/i18n/payment changes. Review every824 ledger row alongside actual tests and explicit deviations; count test subsets separately from complete external equivalence. Deployment/canary/manual QA/backup/rollback/data-loss prerequisites are documented but were not run on production.

Archive contents are the actual finished project:source/tests/migrations/locales/assets/licenses/configuration examples/operator and source-provenance reports, plus baseline-to-final diff/history/revision and SHA256 file manifest. Real.env/credentials/private uploads/.git/.venv/cache/container data are excluded. Extraction and every manifest digest are verified; exact archive hash and identity are supplied with delivery. No merge or production deployment occurred; GitHub work branch contains the authorized completed source.
