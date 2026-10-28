# Cumulative internal audit

13 October2026, Asia/Jakarta. Internal source/test review; independent reviewing agent still required.

Revisited current actor/namespace/fresh capability and callback contracts(authz/operations/reviews/policies), durable inbox/webhook acknowledgement and SDK identity(shared registry/gateway/factory), queued lease/generation/version/unknown-outcome handling(durable/replay/fair_sweeps), owned restriction/CAP/night/raid reset, selected portability/media/destinations, federation SQL lock ordering/graph/files/quotas, privacy SQL/cache retention and core native rendering/aliases/cache. Prior per-stage designs/reports/tests are retained and reused; this is not a claim of independent certification or live Rose parity.

Findings addressed before/at final gate:
- Selected raid replacement kept active generation/deadline; retire transient state/jobs, preserve real punitive bans.
- Own privacy inventory omitted bot-specific platform membership/payments/entitlement/child/audit metadata;19 safe sections now expose them without charge IDs/tokens/raw audit payload. Shared User/preferences and active security remain.
- Nested CAPTCHA restoration could reacquire its own one-slot engine semaphore; count outer task only while retaining distinct row locks, with SQLite/realPG restoration outcome tests.
- Regional/script tags could fall past authored content; longest installed prefix/legacy alias resolution preserves installed native content and older absent-bundle behavior.
- Factory locale parsing repeated all resources per child; bounded parsed-AST cache shares source only, compiled resolvers/arguments stay isolated and changed file metadata reloads. Constructor measurements are recorded separately.
- Nonempty allowlist import constructed a message action with invalid message_id0; pure shared validator and semantic import/link regression pass on SQLite and real PostgreSQL. Empty-only module roundtrip evidence did not cover this case; final closure requires the nonempty repair and gate.

Initial new test fixture mistakes(required challenge fields/payload/generation width) were corrected without changing denial/effect assertions. An inventory joined_at assumption was removed after existing SQLite/PG tests identified the nonexistent field. Interrupted/failed initial runs are not counted as acceptance. Environment restoration lost /tmp runs/services; repeatable own-service startup and repository evidence now replace those volatile paths.

Deliberate limits:bounded direct/graph jobs and quotas, active security/uncertain effect retention, anonymous reaction aggregate has no attributable target, unsupported runs/saved explanations, own schema only, optional CAS/AI remote service behavior and deployed Bot API/live Rose capability unverified. Every final ledger status remains a tested subset where evidence is local.

/info had an unassigned guard_federation_info hook; replaced with the actual public scoped status renderer, with independently bounded profile/source messages. Anonymous /id now uses real sender_chat instead of the pseudo-user. Initial new test built a Message payload at Update level; corrected nested fixture use without weakening effect/tenant assertions.

Critical tenant finding:ChildRegistry and pause cleanup decrypted a child row without binding the token prefix to the requested bot_id. Swapping encrypted sibling tokens could select sibling context/cleanup before the existing GetMe/token check. decrypt_token now accepts expected_bot_id and both child callers require it before SDK/context construction; malformed/nonmatching tokens returnNone, pause fences target row and records safe diagnostic without any sibling RPC. Token-swap tests pass on SQLite and realPG; actual ordinary factory/lifecycle regression is included. This is distinct from a token/API GetMe mismatch, which the existing registry already rejects.
