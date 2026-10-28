# Separate authorized DocTools baseline repair

Starting feature checkpoint32be20e. Narrow production repair in bots/doctools/citations.py plus tests/bots/doctools/test_review.py; no dependency change, xfail, suppression or broader parser rewrite.

Python3.12 HTMLParser silently ignored unsupported marked declarations such as <![bogus]>, allowing apparently valid later citation metadata to produce a reference. PageMetadata.unknown_decl now raises ValueError for unsupported marked declarations; page_reference already translates it into CitationError. Recognized legacy if/endif conditionals remain readable. parser.close runs inside the same controlled-error boundary. Standard doctypes, comments containing declaration-like text and invalid-byte replacement remain supported.

Original named test now passes without modification to its assertions. Added3 invalid declaration cases with later valid metadata and3 genuine doctype/comment/legacy-conditional cases. DocTools focused80 pass. Frozen full suite630 pass/32 explicit service-dependent skips, no failures. All32 skipped categories have separate passing real disposable service evidence from Phase2:27 PostgreSQL+Redis foundation cases,3 fresh/legacy/concurrency migration cases,1 real-Redis approval and1 runtimee2e. Those unchanged service runs were reused, not treated as default-suite passes. Ruff clean, mypy252 source files clean. Exact .venv/bin/pytest tests/bots/doctools -q --tb=short; .venv/bin/pytest -q --tb=short; .venv/bin/ruff check .; .venv/bin/mypy, saved under evidence/long-running/doctools-repair.

No live calls/deploy/merge. This parser remains tolerant of ordinary HTML; the repair concerns unsupported marked declarations, not a full HTML validity checker. No GroupGuard feature code changes in this scoped repair. Prior reports retain the historically observed failure; current baseline is repaired.

NextPhase3: shared Rose/legacy/entity renderer and actual rules/notes/filters/greeting delivery, buttons/private access/media/repeat cadence/cleaning. Concrete design saved in evidence/long-running/phase03-design.md.

Local checkpoint recorded; continuing according to LONG_RUNNING_MASTER_PLAN.md.
