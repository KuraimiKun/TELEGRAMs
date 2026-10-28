# Phase 0B report review

Reviewed 12 October 2026, Asia/Jakarta. Input: `reports/PHASE_00B_CLOUD_REPORT.txt`.

## Verdict

Provisionally accept Phase 0B and authorize Phase 1A through `PHASE_01A_PROMPT.md`. This is acceptance of the reported planning/audit evidence for sequencing work, not certification of unseen cloud code. The complete project still requires independent source review in Phase 12. No application code was changed by this local review.

## Evidence supporting progression

- The report records conflict-free, provenance-preserving cherry-picks of the two supplied baseline commits, ending at `96357ef45c6492e03c626581ce2ee156d2da3816`. The reported source tree is `7895f72031fd4fac13b4ff280ba04b16c8d5842c`. The reviewer independently verified that the local reference at `d55fc44fe1a63ba5788125c1325d2a855944d5e0` has that tree. Cloud execution remains agent-reported.
- The supplied bundle/manifest were reportedly verified, and all 20 original audit artifacts preserved. No Phase 1 production changes were reported.
- The ledger now has 812 traceability rows, retains 150 existing IDs, maps all 51 former planning areas, and accounts for S01–S50 plus T01. These rows include aliases, variants, permissions and lifecycle cases; they are not 812 distinct completed features.
- Specification evidence is accurately labeled reviewer-supplied condensed source material. Direct cloud retrieval is still zero; neither full-page archival completeness nor live Rose behavior was established.
- Reported checks: dependency health, nine bot contracts, Ruff and mypy pass; focused Group Guard/factory/locales tests pass 36/36; full default suite has 257 passed, one failed, three skipped. The three service-dependent tests were separately executed against disposable PostgreSQL/Redis and passed (two integration, one runtime e2e). Telegram calls were mocked.
- The report gives concrete actor, authorization, duration and action-result proposals and ten reproduced baseline defect observations. This is enough to bound implementation without prematurely building later phases.

## Conditions and corrections carried into Phase 1A

1. **Keep the baseline failure visible.** `tests/bots/doctools/test_review.py::test_malformed_html_and_invalid_encoding_are_controlled` failed in the supplied baseline: Python 3.12.14's HTML parser accepts the reported malformed declaration and the expected `CitationError` is not raised. Phase 1A must introduce no additional failures. Do not edit DocTools, weaken the test, add an xfail or suppress it to obtain a green total. A separate repair will be required before final acceptance.
2. **Correct the source question for `/kickme`.** The official disabling page's example supplies its basic self-kick purpose. Resolve that part of Q01; keep uncertain optional syntax and the meanings of other catalog-only names separate. Implementation belongs to Phase 2; disabling integration belongs to Phase 8. See `PHASE_01A_SOURCE_ADDENDUM.md`.
3. **Split S32 by behavior.** Federation roles, reason policy, owner notifications and log setup belong to Phase 9; ban-list export/import and directed subscriptions belong to Phase 10. Update affected row ownership and recompute counts without deleting or replacing stable IDs.
4. **Anonymous approval authenticates the approving human.** Telegram does not reveal which human originally sent an anonymous group message. A sufficiently privileged human may approve the displayed immutable operation under their own current authority. Do not claim the original anonymous person was identified. Owner-only operations require that the approving human is the actual current creator. Optional `/anonadmin on` assumptions remain Phase 2.
5. **Authorize all steps of a compound action.** A single `caller_right` parameter is insufficient if an operation sanctions and deletes. Use a set of required rights or an equivalent explicit contract; deny before any domain mutation when the union is not satisfied.
6. **Define action postconditions explicitly.** A successful sanction followed by a failed log is different from a failed sanction. A ban followed by a failed unban is a partial kick, not a completed kick. Warning reset and user-facing text must use the intended sanction's completion, not aggregate truthiness.
7. **Adopt the proposed safe sanction interval deliberately.** Temporary ban/mute input is limited to 60 seconds through 365 days inclusive, with a deadline check at dispatch. This is our safety policy, not a Rose-sourced range. Reject unsafe values explicitly; never clamp or silently make them permanent. Do not apply sanction bounds to flood windows, cleaning delays or general duration utilities. Record the compatibility difference from the existing 30-second/366-day parser limits.
8. **Keep Phase 1A bounded.** No new SQL migration, event-router overhaul, update subscription change, durable inbox, federation system, or general concurrency overhaul. A bounded atomic one-use authorization review and scoped panel bindings are necessary within 1A; configuration/warning/CAPTCHA concurrency and durable lifecycle work remain 1C and Phase 4.

## Sequencing after this review

| Next gate | Scope |
| --- | --- |
| 1A | Attributable actors, precise fresh authorization, safe target/duration contracts, truthful outcomes on existing flows |
| 1B | Protection dispatch, core-handler precedence, edited messages, routing/deep links, required update subscriptions and capability evidence |
| 1C | Concurrent state changes, replay/lifecycle coordination and the minimum persistent deadlines/jobs required by actual transitions |
| 2–11 | Feature implementation following the retained roadmap and corrected ledger ownership |
| 12 | Complete cumulative source handoff, independent review/testing, resolution of baseline failures and release readiness |

P02/P03/P04/P05/P07/P08/P09 remain open after authorization of 1A. P06 is addressed only for truthful sequential outcomes here; concurrent threshold coordination remains 1C. A report must not mark a wider parent behavior complete merely because its authorization layer is repaired.
