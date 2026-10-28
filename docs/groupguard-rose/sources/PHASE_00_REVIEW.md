# Review of the first cloud Phase 0 report

Reviewed 12 October 2026. Evidence is the user's pasted report; cloud artifacts/tests have not been independently inspected.

## Verdict

Repository audit and reported baseline are provisionally useful. Phase 0 remains incomplete: zero Rose pages were retrieved; the 201-row matrix is primarily existing-code inventory plus unresolved requested areas, not an exhaustive sourced parity ledger. Do not mark the 56 externally-dependent rows as fundamental product dependencies when their common cause was denied documentation access.

Reported checks: contracts/lint/types passed; focused suite 32 passed; full suite 158 passed and 2 skipped; the two PostgreSQL tests reportedly passed separately. The API/diagnostic limitations are appropriately disclosed. This review does not certify those results or unseen implementation.

## Confirmed baseline mismatch

Local Git contains both reported cloud HEAD `e474c59784c47f4055cdc0eab7a74d111a1ff66b` and local reference `d55fc44fe1a63ba5788125c1325d2a855944d5e0`. Cloud HEAD's tracked tree equals `44ff18f39d2fbbc8583eb5e0ddbd013ffd20f83f` locally. Local reference adds:

1. `17f563460d2d74ac7d0be70989c94c663e91d9d9` — CV bot and shared improvements.
2. `d55fc44fe1a63ba5788125c1325d2a855944d5e0` — document bot, worker and runtime harness.

Tree difference: 65 files, 5998 insertions, 44 deletions, including Group Guard protection, shared SDK/throttling/payment/AI/file/UI changes, migration revisions 0008/0009 and `tests/e2e`. Its absence in the cloud report is explained by source-version difference, not a reason to design a second harness. Refresh the baseline after importing these commits. Do not cherry-pick only the Group Guard snippet and leave shared test/migration state behind.

`CLOUD_BASELINE.bundle` was created from these two reachable commits excluding cloud HEAD's history. Local `git bundle verify` succeeded. It advertises reference HEAD at d55fc44 and requires prerequisite 44ff18f. SHA256: `61869c1cae2bc35ae3aa1cc8080fdbe8656ddaf22c6c69a8b7ae3503f74768cb`.

## Blueprint review

Retain the existing framework and focused services. Actor separation, exact permission checks, explicit action outcomes, immutable challenge identity, versioned content/configuration and tenant-scoped state are appropriate directions.

Do not pre-build the full future schema, a platform-wide replacement dispatcher, a generic global durable inbox, every federation table or an arbitrary retention system in the foundation phase. First document concrete necessities and costs. Introduce minimum opt-in Group Guard seams and additive state as the owning implementation phase requires it. Privacy periods are proposals, not approved or sourced requirements.

Group Guard creator authority for anonymous messages is a confirmed local priority. Stale cache, temporary aliases and false success messages deserve early fixes. Source semantics now establish that automated silent actions require creator enablement and a log channel; manual silent commands have a separate contract. Broadcast authority is for bot owners, not arbitrary group admins. New source details include exact/lookalike and custom-clone name/username blocklists; include them explicitly.

## Next step

Phase 0B aligns source baseline, decomposes the supplied offline source digest into the matrix, reruns checks and returns concrete foundation contracts. It makes no new Rose feature implementation. A bounded Phase 1A can then address attributable authorization, permission freshness, parser safety and truthful action outcomes, followed by routing and atomic-state subphases. The exact next implementation prompt follows the Phase 0B report.
