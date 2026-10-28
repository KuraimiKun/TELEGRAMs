# Phase6 advanced blocklists

Starting HEAD4e36e2d; all phases through12 remain authorized. This is a local checkpoint, not a final handoff or live Rose/deployment certificate. Continuing directly to7.

Implemented additive typed blocklist entries while preserving legacy phrases/raw text/literal wildcard characters, long legacy literals and unknown JSON fields. Legacy blocklist_warn maps to warn unless a newer mode exists; legacy service writers replace text entries without removing unrelated typed kinds. No SQL schema changes; data normalization persists through existing revisioned JSON CAS updates. PostgreSQL legacy/raw roundtrip and actual prior-schema upgrade pass.

Actual management handles words, quoted phrases, parenthesized multiple triggers, shared reasons, entry action/timer overrides, listing/file output, add/remove and creator-confirmed clear. blocklist no-args lists; with args adds. Existing addblock/rmblock/unblocklist comma aliases retained. Frozen delta operations serialize at chat member0; failed quota batches leave existing entries intact rather than truncate. Defaults nothing/delete-on; configured and per-entry nothing/warn/kick/ban/tban/mute/tmute validated. Deletion off preserves warning/sanction. Reason order entry/configured/localized fallback. Invalid timer never becomes permanent. Current admin/approved users exempt and locks execute first; deletion/restriction capabilities checked as a union before effects. Warning/replay/generation/owned restriction primitives preserved.

Matcher applies NFKD/casefold/accent removal/space normalization and Unicode alphanumeric/underscore word boundaries. ? one non-space, * zero/more non-space, ** arbitrary, escaped literals. Literal find and bitset NFA with forward epsilon transitions avoid regex backtracking. New raw patterns≤256,≤32 wildcards, normalized representation≤1024, text≤32768; legacy literals retain original raw length. Hostile150-pattern/32768-source test bound8s is a local regression budget. This is a bounded interpreter, not a full Unicode visual-equivalence claim.

Every declared typed prefix executes against real native/caption/rich text, document filename/extension, actual forward/via-bot ID/username, sticker/custom-emoji set lookup and observed name/username. Unknown hidden identity/failed pack lookup cannot manufacture a match. username optionally accepts @. Curated Greek/Cyrillic lookalike mapping explicitly local. Declared lookalike:/username: prefixes resolve contradictory source exact example/inline prose; defects retained in decisions/ledger. Observed joins use actual ChatMemberUpdated and actual User/Chat, no invented Message or deletion target. Join warn/mute may coexist with independently owned CAPTCHA; ban/kick consumes join; delete-only continues CAPTCHA. Speaking sees observed changed profiles; no unseen profile-change detection asserted.

Silent entry actions require creator consent plus configured log and explicit selected entry mode; no silent default blocklist mode. Removing consent/log/category selects loud behavior; selected audit failure gets visible ancillary fallback. Consent management remains Phase8. Connected PM/disable metadata/full UI and31 actual locales retain8/11 ownership.50 Phase6 ledger rows are local tested subsets, not broad final parity; all824 existing IDs/813 canonical IDs retained.

| Gate | Result |
|---|---|
| First focused actual dispatcher/matcher run |126 passed/12 failures from new fixture mistakes (filename * cannot span spaces, nonexistent pending accessor, SDK integer edit_date); fixture corrected without relaxing effect/authority assertions |
| Corrected focused (standalone and actual ChildRegistry710011/710012) |138 passed |
| Entry override/optional-@/failed-pack material cases |9 passed |
| Existing GroupGuard and1B regression |20 passed |
| All real PostgreSQL+Redis foundations including concurrent add/remove and intact legacy JSON |54 passed |
| Fresh/legacy/model schema roundtrip and real Redis review claim |4 passed |
| Actual runtime E2E |1 passed |
| Ruff/mypy |pass;274 source files |
| Frozen full suite |1216 passed/60 skipped,0 failures |

60 full skips:54 foundation+4 migration/approval+1 runtime separately passed, one factory-only standalone inapplicability. No xfail, dependency/test suppression or invented API success. Tests use actual SDK methods and child registry with recording transport; successful remote Telegram/Rose behavior is not certified. Source remains reviewer-supplied condensed digest, prior CONNECT403 evidence preserved. Task-owned local services retained for subsequent stages.

Changed production: blocklist_matcher/types/blocklists and handlers/blocklists added; chatconfig/service/operations/content_commands/protect/module/welcome wiring updated; duplicate old shadow blocklist handler removed; four actual EN/AR UI keys. Changed tests: matcher and Phase06 acceptance added, six PostgreSQL concurrency/legacy cases added. Documentation: commands/API/decisions/changelog/progress/ledger/counts/manifest and this report/evidence updated; Phase7 concrete design retained. No shared-core changes in this phase. Exact gate stdout resides in evidence/long-running/phase06.
