# GDSS-008 — Implementation Plan Contract

Mandate: MIDD-GDSS-P038-R1. Date: 2026-10-23.
Status: `COMPLETED_GDSS_008_ARCHITECTURE_AND_IMPLEMENTATION_PLAN_CONTRACT`.
Scope: future architecture and implementation planning only; no implementation is authorized.
Normative source: [GDSS-008-ARCHITECTURE.md](GDSS-008-ARCHITECTURE.md), sections 1–45.
All references to services, tables, SQL guards, APIs and tests are planned artifacts, not existing
GDSS-008 behavior. Architectural acceptance does not equal executable verification.

## 1. Baseline and authority ceiling

Verified checkout `iot-midd-paas-auth-work`, branch main, HEAD = origin/main =
`d5e6897902de035e69846d1bb3f3f325683b2989`; ahead/behind 0/0, clean tree and staged 0.
Read-only live remote check matched; canonical `iotmw-api` Alembic heads/current each returned one
`0057 (head)`. P038 creates only these two documents. No migrations, code, tests, runtime, UI,
commit, push, tag, release, deployment or principal DB mutation. No source table or historical
GDSS-007 evidence document is changed.

```text
RecommendationAuthority = HUMAN_GOVERNED_DECISION_SUPPORT_ONLY
PolicyProposalAuthority = HUMAN_GOVERNED_PROPOSAL_ONLY
PolicyCandidateAuthority = NONE
PolicyAuthority = NONE
ControlAuthority = NONE
PhysicalAuthority = NONE
```

The proposal authority is a future V1 target; P038 enables nothing in runtime. The first rung is
`AUTHORIZED_POLICY_PROPOSAL`, never POLICY_CANDIDATE. All seven phases require separate approval.

## 2. Shared implementation contract

Implementation location, if later authorized: Next.js operational-domain libraries/repositories/
services under a distinct GDSS policy-proposal namespace, separate from existing M7 promotion.
Python runtime, legacy APIs, admin-fastapi, control workers and MQTT remain untouched.
No imports/calls/writes from the new domain to ControlledPolicyVersionRepository, M7 materializers,
activation, deployment, Control Engine, MQTT, AMQP, DTE or actuator subsystems.

V1 origin is an explicit human ACCEPT with exactly one preferred/considered/authorized alternative.
Recommendation-only, override-only, deferred, rejected and multi-selected transfers fail closed.
HumanDecisionScope is derived from its exact recommendation authorization and selected alternative;
DecisionRecord has no scope column. A source correction needs a new origin identity, not rebinding.

Common protocol requirements for all future commands:

- Trusted project-scoped principal; no request-supplied role/actor_kind/authority grant.
- Exact ID, declared source version/schema and verified hash; never latest or name fallback.
- Bounded strict input, expected proposal hash (or draft revision), explicit reason and request key.
- Same key/same semantics replays history with fresh currentness; changed semantics conflicts.
- One transaction reconciles source bindings, normalized rows, canonical content and append-only audit.
- No grant is inferred from response status, AI provenance, existing edit_policies or M7 privileges.
- Read APIs expose workflow state and effective currentness separately, with checkedAt/reasons,
  scope, content/grant hashes, retained adverse evidence and constant authority matrix.

Common future API envelope: JSON strict schemaVersion, resourceProfile, exact bindings,
expectedContentHash/expectedDraftRevision, reason and idempotencyKey for commands. Identity creation
has no expected hash; draft edits require expected revision. Schema/limit failures use the error
model in architecture section 38. GET audit/list pagination uses stable ID cursor, bounded page size
100, never pagination-dependent scientific completeness. A manifest-bound exact read must retrieve
all referenced evidence or fail; a UI page is not a complete evidence package.

## 3. Future API contract (design only)

Base: `/api/control/policy-proposals/projects/[projectId]`. This remains under the official Next.js
operational backend but explicitly names policy-proposals; it grants no existing control authority.
No route is created by P038. No `/activate`, `/execute`, `/deploy`, `/transfer` or `/candidate` route.

| Planned method/path suffix | Input / output | Permission / owner |
|---|---|---|
| POST /namespace | immutable canonical project namespace key; one-time registration | AUTHOR plus human project-admin restriction, A |
| POST /identities | canonical intent key and exact decision origin; identity | AUTHOR, A |
| POST /identities/[identityId]/versions | exact predecessor or null, source manifest, draft intent; DRAFT revision | AUTHOR human initiation, A |
| PATCH /versions/[versionId] | expected draft revision and bounded semantic edits; updated DRAFT revision | AUTHOR, A/B/C |
| GET /versions/[versionId] | exact resource; workflow/currentness/reasons and authority matrix | AUDIT, A/E |
| GET /identities/[identityId]/versions | project-scoped history, no latest-as-authority | AUDIT, A |
| POST /versions/[versionId]/assemble | expected hash/revision, complete package, reason/key; frozen review-required proposal | AUTHOR human adoption, C |
| POST /versions/[versionId]/reviews | exact hash/currentness digest, slot/disclosures/decision/reason/key; immutable review | REVIEW, D |
| POST /versions/[versionId]/authorizations | exact proposal/review/source hashes, narrowed scope, exception if allowed; grant plus currentness | AUTHORIZE, D after E |
| POST /versions/[versionId]/withdrawals | exact version/grant hashes if any, reason/key; immutable withdrawal | WITHDRAW, E |
| POST /versions/[versionId]/reevaluation-triggers | typed exact causal artifact/hash/effect and reason/key; trigger | AUTHOR human or restricted source observer, E |
| POST /versions/[versionId]/reevaluation-triggers/[triggerId]/events | expected sequence, resolution basis, reason/key; event | REVIEW human resolution, E |
| GET /versions/[versionId]/audit | append-only scoped event history, stable cursor | AUDIT, A/D/E |

AUTHOR/REVIEW/AUTHORIZE/WITHDRAW/AUDIT expand to the distinct POLICY_PROPOSAL permissions in
architecture section 37. A restricted observer can only record change evidence, never resolve,
adopt, assemble or authorize. Successor creation uses the identity versions command and exact
predecessor; there is no overwrite endpoint. Inactive phase endpoints must not be exposed.

## 4. Dependency and migration sequence

A -> B -> C -> D -> E -> F -> G. D is tested as a non-enabled gate until E proves source-currentness
and withdrawal races; no release can expose D authorization in isolation. F may start as a boundary
review earlier, but its closure gate covers the final graph. Proposed migrations only:
0058(A), 0059(B), 0060(C), 0061(D), 0062(E). F has no persistence need, so 0063 is unallocated;
G has no feature migration. No migration file is created or run during P038.

Before each authorized future phase: fetch/check baseline, inventory every existing change, verify
Alembic single head/principal read-only and explicit phase authorization. Drift blocks work.
Never quietly retrofit 007 or M7. Required source-lock/namespace/DB-identity prerequisites that cannot
be satisfied inside the phase must be reported for a separate scope decision. No inferred authority.

## GDSS-008A — Policy Proposal Identity, Source Binding & Scope Foundation

Authorization: `GDSS_008A_NOT_AUTHORIZED`.

| Contract field | Phase requirement |
|---|---|
| Purpose | Establish a new project-scoped logical policy intention tied to one exact human ACCEPT, without creating a policy. |
| Scope | Immutable project namespace registry and identity/version/draft core, exact source locator and semantic manifests, scope derivation, canonical core, audit skeleton; no assembly grant. |
| Inputs | Exact 007 recommendation candidate/authorization, ACCEPT DecisionRecord, one selected alternative, problem scope and all upstream hash bindings; trusted human request. |
| Outputs | DRAFT identity/version with expected revision, verified derived HumanDecisionScope, canonical semantic preview and exact reference manifest. |
| Entities | ProjectNamespaceRegistry, PolicyProposalIdentity, PolicyProposalVersion, recommendation_ref, decision_ref and audit_event; preserve origin and predecessor lineage. |
| Services | Planned PolicyProposalSourceBindingService, PolicyProposalDraftService and project-scoped repository; source reads only into 007. |
| Migration | Proposed 0058 after 0057: namespace/identity/version/source refs/audit, scoped uniqueness and draft/source guards. No source or M7 table alteration assumed. |
| RBAC | AUTHOR_POLICY_PROPOSAL human initiates/adopts origin; AUDIT reads. AI draft assistance is distinct and cannot adopt/assemble. |
| SoD | Capture canonical author/source recommendation authorizer principals for future D checks; authoring does not authorize. |
| Hashing | Define semantic projection, separator midd:gdss:policy-proposal:v1, project namespace, source hashes and derived scope hash; golden vectors before persistence use. |
| Immutability | Identity/source origin immutable; DRAFT content changes under revision check; no post-DRAFT child mutation from foundation APIs. |
| Idempotency | Scoped create keys and canonical draft request digest; preview is not authority; assembly deduplication reserved for C. |
| Concurrency | Identity/decision quota and successor allocation locks; same-key races; conflicting origin/branch requests fail without partial rows. |
| Resource limits | 16 logical identities per decision; 16 objectives/64 constraints source scope compatibility; strict scope qualifiers and 16 MiB eventual package guard. |
| Invariants | POL-INV-01,02,09,20,21,38,39; exact human origin is independently proven, not assumed from an action string. |
| Adversarial tests | Cases 4,15,16,22,25; non-ACCEPT, multiple alternatives, forged actor, unsupported qualifier and decision-source hash substitution. |
| PostgreSQL enforcement | Composite project FK, exact source/hash/selected-row guards, immutable origin, unique project/key and identity/version; direct SQL injection/bypass tests. |
| API contract | Human-admin namespace registration, identity/version creation, draft PATCH and exact/history GET from section 3; no recommendation auto-materialization or authorizations endpoint. |
| Static boundaries | Forbid all M7 materializers, activation/control/messaging imports and writes; data-only source reads into decision support. |
| Regression | Focused origin/scope/hash unit and clean PostgreSQL source binding suites; retain GDSS-007 invariants and full 007 baseline behavior. |
| Recovery | Rollback failed drafts atomically; retry safe keys; reject duplicate predecessor branch; preserve denied audit without mutating source history. |
| Non-goals | No objectives/threshold evaluation engine, assembly/review grant, M7 candidate, new human decision or runtime ingestion path. |
| Definition of Done | Explicit authorized scope, exact ACCEPT source and namespace proof, 0058 isolated cycle, unit/SQL/race/hash tests, limits at 50/100/one-over and evidence; status remains DRAFT only. |

## GDSS-008B — Policy Objectives, Constraints, Conditions & Threshold Semantics

Authorization: `GDSS_008B_NOT_AUTHORIZED`.

| Contract field | Phase requirement |
|---|---|
| Purpose | Represent what a future policy could consider as declarative domain-neutral intent with explicit analytical translation. |
| Scope | Objective coverage, constraint translation ledger, non-executable conditions, typed thresholds, proposed validity/monitoring and structured rationale components. |
| Inputs | A draft, source objective/constraint/evaluation roster, source threshold envelopes, source scope and expected draft revision. |
| Outputs | Strict typed intent rows and canonical draft preview with complete required-objective/constraint coverage and no operational parameters. |
| Entities | PolicyObjective, PolicyConstraint, PolicyCondition, PolicyThreshold, PolicyMonitoringRequirement; bounded scope/rationale JSONB on version. |
| Services | Planned PolicyProposalIntentService and PolicyIntentTranslationValidator; no runtime rule evaluator. |
| Migration | Proposed 0059 after 0058: normalized intent children, keys/units/finite-decimal/type/count guards and draft-only parent checks. |
| RBAC | AUTHOR may edit DRAFT within project; AUDIT may inspect exact semantics and derivation ledger. No edit_policies inheritance. |
| SoD | Translation decisions are author proposals; they require independent review in D. No approval through author role. |
| Hashing | Include typed objectives, categories, derivation hashes, decimal thresholds, conjunction conditions, validity and monitoring; semantic edit changes preview hash. |
| Immutability | All intent children editable only while parent DRAFT; bulk/SQL update and deletion after assembly must fail. |
| Idempotency | Explicit revision and edit request keys; reordered sets hash equally; same key/different threshold conflicts. |
| Concurrency | Serialize aggregate draft edits and resource counts on parent; stale revision cannot overwrite threshold or constraint changes. |
| Resource limits | Objectives 16, constraints 64, conditions 64, thresholds 64, monitoring 32; resource table 50/100/one-over plus nested/binary-size guards. |
| Invariants | POL-INV-09,22–27,35,37,38; no automatic HARD->MANDATORY or threshold->setpoint equivalence. |
| Adversarial tests | Cases 9–11,27 plus hard-constraint omission, invented objective, NaN/Infinity, unit mismatch, disguised command key and nested operational alias. |
| PostgreSQL enforcement | Key uniqueness, same-project exact source bindings, typed finite values and units, no operational payload, source translation coverage and child cap triggers. |
| API contract | Draft PATCH accepts only typed objective/constraint/condition/threshold/monitoring/validity components; no arbitrary expression or execute route. |
| Static boundaries | No MQTT/AMQP/DTE topics/routes, physical endpoint, control command, strategy configuration or policy candidate payload accepted. |
| Regression | Canonical/golden/unit and direct-SQL child immutability/count tests; A scope regressions; retain all 007 boundary/constraint semantics. |
| Recovery | Failed multi-child draft edit rolls back all changes; correction under a new key/revision; post-assembly corrections use successors. |
| Non-goals | No executable trigger, policy evaluator, setpoint emission, provisioning, subscription or M7 configuration translation. |
| Definition of Done | Explicit typed translation ledger covers all required source constraints/objectives, all nested escape and boundary tests pass; no runtime consumer and no scientific claims added. |

## GDSS-008C — Evidence, Impact & Policy-Risk Assembly

Authorization: `GDSS_008C_NOT_AUTHORIZED`.

| Contract field | Phase requirement |
|---|---|
| Purpose | Freeze a complete adverse-preserving proposal with separate multidimensional adoption risk and impact. |
| Scope | Exact evidence reconciliation, normalized limitations and rationale, bounded impact/risk manifests, human adoption and atomic scientific assembly. |
| Inputs | A/B draft, full recommendation evidence roster and relevant alternative roster, current source manifests, typed intent, assessment dimensions and human assembly request. |
| Outputs | Canonical bytes/hash and normalized projection agree; EVIDENCE_ASSEMBLED then REVIEW_REQUIRED history; no grant. |
| Entities | evidence_ref, limitation, PolicyImpactAssessment, PolicyProposalRiskAssessment and frozen proposal manifest; audit assembly records. |
| Services | Planned PolicyProposalEvidenceService, PolicyProposalImpactService, PolicyProposalRiskService and PolicyProposalAssemblyService. |
| Migration | Proposed 0060 after 0059: evidence/limitation/assessment tables and assembly completeness/freeze guards, canonical/hash projection reconciliation. |
| RBAC | Human AUTHOR explicitly adopts and assembles; AI can suggest dimensions/text only while DRAFT; AUDIT sees full adverse manifest. |
| SoD | Record adoption principal and all contributors; assembly cannot satisfy D independent review or grant. |
| Hashing | Complete all semantic inputs, independent impact/risk hashes and negative/unknown fields; UUID/session/order independent vectors and source substitution rejection. |
| Immutability | Freeze version and every scientific child/JSONB at assembly atomically; never repair normalized projections by overwriting frozen evidence. |
| Idempotency | Scientific create-or-get by identity/hash with explicit human command key; integrity mismatch is a conflict, never overwrite. |
| Concurrency | Parent lock covers complete child counts and snapshot/hash; concurrent assembly yields same object; one-over evidence cannot persist. |
| Resource limits | Evidence 10000, impact dimensions 16, risk dimensions 32, limitations/assumptions 64 and 16 MiB package; preserve full roster or reject, never truncate. |
| Invariants | POL-INV-11–15,34–38; unknown adoption risk remains unknown and blocks grant, no scalar quality uplift. |
| Adversarial tests | Cases 6–8,24,25,27 plus forged canonical bytes, missing outcome/model refs, favorable-only evidence and source risk aliasing. |
| PostgreSQL enforcement | Exact composite reference FKs, manifest/cardinality/polarity coverage, dimension typing/size, freeze and canonical projection integrity checks under assembly lock. |
| API contract | POST assemble requires exact expected revision/hash and complete package; response includes frozen hash, workflow and no-authority matrix. |
| Static boundaries | No policy_score/proposal_score/policy_confidence/overall_policy_value as authority; no evidence auto-promotion or operational artifact interpretation. |
| Regression | Clean isolated A–C end-to-end, full evidence bounds, hash vectors and SQL mutation tests; 007 regression including adverse and unknown preservation. |
| Recovery | Any missing binding/count/hash aborts assembly; DRAFT remains intact. Frozen corrections require successor; no partial evidence-as-success. |
| Non-goals | No policy activation, causal proof, universal scalar rank, physical adoption safety certification or grant. |
| Definition of Done | Complete normalized/canonical reconciliation, frozen scientific package, distinct risk/impact and executable negative/unknown/boundary proofs; review-ready only. |

## GDSS-008D — Review, SoD & Authorized Policy Proposal

Authorization: `GDSS_008D_NOT_AUTHORIZED`.

| Contract field | Phase requirement |
|---|---|
| Purpose | Define the first and maximum authority rung as an independently human-reviewed consideration grant. |
| Scope | Mandatory review slots, structured decisions, reinforced SoD, optional disabled-by-default human exception, exact one-per-version grant; disabled until E verified. |
| Inputs | Frozen C proposal/hash, source/currentness digest, full adverse disclosures, human principal, review policy, accepted/narrowed scope and reason. |
| Outputs | Immutable reviews and PolicyProposalAuthorization; future effective AUTHORIZED_POLICY_PROPOSAL only when E predicates hold. |
| Entities | PolicyProposalReview, PolicyProposalAuthorization; exception as structured hash-bound authorization provenance plus explicit audit event. |
| Services | Planned PolicyProposalReviewService and PolicyProposalAuthorizationService; no M7 authorizer dependency. |
| Migration | Proposed 0061 after 0060: append-only review/grant tables, one grant/version, human/SoD and scope/review/source guard triggers; grant endpoint stays disabled pending E. |
| RBAC | Distinct REVIEW_POLICY_PROPOSAL and AUTHORIZE_POLICY_PROPOSAL human permissions, trusted admin principal; no AI authority or edit_policies reuse. |
| SoD | Author!=reviewer, author!=authorizer, recommendation authorizer!=proposal authorizer; explicit project-permitted human exception only for named principal inequalities. |
| Hashing | Separate authorization/review domain separators; include exact proposal/source/review hashes, scope overlay, principal semantic key, reason and exception hash. |
| Immutability | Reviews/grants append-only; authorization cannot change evidence, risk, uncertainty, thresholds/objectives or frozen bytes. |
| Idempotency | Same event key/digest returns history with fresh currentness, never resurrects authority; changed scope/reason/key reuse conflicts. |
| Concurrency | Same version lock for grant/withdrawal, exact dependency checks in SERIALIZABLE transaction; one grant even under distinct replay keys. |
| Resource limits | 32 reviews/version including blocking history; mandatory evidence and risk slots cannot be collapsed or bypassed at quota exhaustion. |
| Invariants | POL-INV-03,10,14–19,35,37,40 plus strengthened recommendation-authorizer separation and no scientific modification. |
| Adversarial tests | Cases 1,5,7,17,20,21,23,24,26,28; missing adverse disclosures, review digest drift, forged human context and exception-policy absence. |
| PostgreSQL enforcement | Trusted principal mapping/role isolation, unique grant, immutable events, exact sources/review digests, contained scope and lock/risk checks independent of service validation. |
| API contract | Review command enumerates all five decisions; grant command accepts only exact refs and scope overlay, and remains unexposed until E gate passes. |
| Static boundaries | Grant output explicitly carries consideration-only authority; no call/import into policy candidate, activation/control/physical paths. |
| Regression | Human workflow and SQL bypass/SoD/race/idempotency suites; all A–C freeze/evidence/risk and 007 human-governance regressions. |
| Recovery | Failed authorization rolls back grant and state changes; denial audit recorded safely; blocking review requires successor, not overwrite or fresh-key bypass. |
| Non-goals | No approval of a policy, active/deployed state, candidate materialization, exception to science/currentness or AI exception. |
| Definition of Done | Separate grant and two mandatory exact-hash reviews proven; every authority/SoD/SQL/race test passes with E; no production enablement before A–G closure. |

## GDSS-008E — Currentness, Reevaluation, Withdrawal & Supersession

Authorization: `GDSS_008E_NOT_AUTHORIZED`.

| Contract field | Phase requirement |
|---|---|
| Purpose | Ensure a historical review/grant can never conceal changed evidence, source supersession, expiry or withdrawal. |
| Scope | Direct currentness projection, source checks, typed triggers/events, immutable withdrawal, successor atomics, trusted-time validity and race serialization. |
| Inputs | Exact proposal/grant history plus source recommendation/decision/model/claim/evidence/objective/constraint/preference/risk/scenario/comparison/sensitivity/robustness state. |
| Outputs | Explicit workflow/effective-state/reasons/checkedAt and append-only triggers/resolutions/withdrawals/supersession audit; never replacement proposal. |
| Entities | PolicyProposalWithdrawal, PolicyProposalReevaluationTrigger/Event; predecessor/successor linkage and currentness read projection. |
| Services | Planned PolicyProposalCurrentnessService, PolicyProposalReevaluationService, PolicyProposalWithdrawalService and successor assembly orchestration. |
| Migration | Proposed 0062 after 0061: withdrawal/trigger/event tables, sequence/freeze/lineage guards and source/grant currentness enforcement; no source table changes without separate authorization. |
| RBAC | WITHDRAW human author/admin as scoped; REVIEW resolves exact basis; restricted observer only appends change evidence; AUDIT reads all historical grants. |
| SoD | Neither trigger acknowledgement nor exception can restore withdrawn/invalid source authority. Human resolution never rewrites original reviewer/authorizer. |
| Hashing | Distinct causal trigger/resolution/withdrawal semantic hashes include exact source/grant hashes and reason; checkedAt/DB timestamps excluded. |
| Immutability | Withdrawals, source-change evidence, resolutions and supersession audit append-only; frozen predecessor stays readable with non-current projection. |
| Idempotency | Semantic change deduplication and command keys; replay of historical authorization reports withdrawn/stale/expired currentness instead of reactivating. |
| Concurrency | Prove existing 007 source row/FK/predicate locking with actual revocation/decision supersession paths. Three bounded serializable retries; fail closed if integration cannot serialize safely. |
| Resource limits | Reuse proposal package/ref/review caps; bounded page/diagnostic payloads; immutable history is paginated, never truncated to claim completeness. |
| Invariants | POL-INV-20,21,28–33,37,39,40 and no duplicate effective version/grant or withdrawal split-brain. |
| Adversarial tests | Cases 2,3,16,18,19,23,26,28; source change with no trigger, delayed delivery, source expiry at commit time and conflicting successor branches. |
| PostgreSQL enforcement | Version/source locks, unique event sequence, scoped predecessor chain, one withdrawal and immutable events; grant trigger rechecks source/time predicates and terminal history. |
| API contract | Exact GET recomputes currentness; withdrawal/trigger/events commands use hashes/sequences/reasons; no auto-renew or source-rebinding endpoint. |
| Static boundaries | Trigger effects limited to review/reevaluation/stale/invalidated; no message flow toward M7, policy, control or physical systems. |
| Regression | Temporal boundary tests at before/equal/after validity; clean A–E workflow; real source revocation/decision successor and grant/withdrawal races, SQL bypass. |
| Recovery | Acknowledgement alone does not clear causes; unchanged evidence may satisfy review-only resolution, material changes require successor; source-invalid stays fail-closed. |
| Non-goals | No principal cleanup, background automatic replacement, policy candidate transfer, scheduler-created renewal or operational rollback. |
| Definition of Done | Currentness agrees with every exact dependency even without trigger; source races and withdrawals linearize correctly; D may only become test-enabled after this gate. |

## GDSS-008F — M7 Transfer Boundary & Future Policy-Candidate Interface Contract

Authorization: `GDSS_008F_NOT_AUTHORIZED`.

| Contract field | Phase requirement |
|---|---|
| Purpose | Prove AUTHORIZED_POLICY_PROPOSAL ends before M7 candidate authority, and specify only a future independently authorized translation boundary. |
| Scope | Contract vocabulary, explicit rejection of automatic transfer, static import/call/role review and negative tests; no adapter or transfer route. |
| Inputs | Final A–E artifacts and actual M7.2 repository/materializer/validator contracts for boundary comparison, not invocation. |
| Outputs | Documented future transfer request requirements and enabled negative boundary proofs; no candidate, configuration or transfer record. |
| Entities | No new persisted entity. Future TransferRequest is conceptual and requires a later architecture/authorization. |
| Services | No transfer/materializer service. Boundary checks attach to existing planned proposal validators/audit and tests only. |
| Migration | None. 0063 is unallocated because V1 needs no F persistence; adding it requires explicit architecture revision and authorization. |
| RBAC | No TRANSFER/ACTIVATE capability introduced. Existing proposal AUDIT permission cannot invoke M7 creation. |
| SoD | Future transfer would require independent human/M7 governance; proposal SoD exception never waives M7 eligibility or authority. |
| Hashing | No candidate/policy-version hash produced. Future translation hash/schema must be defined under separate authorization, not aliased to proposal hash. |
| Immutability | Document the exact frozen proposal/grant provenance required for any future process; never mutate A–E or M7 artifacts. |
| Idempotency | No executable transfer exists to replay. Negative tests verify duplicate proposal reads do not create M7 records. |
| Concurrency | Parallel authorized-proposal reads/exports cannot create candidates; DB-role test denies concurrent M7 writes from proposal role. |
| Resource limits | Boundary scans cover all new files/transitive dependencies and role privileges, not a sampled subset; reuse bounded read/export manifests. |
| Invariants | POL-INV-04–08,17,22–24,27,40; candidate/authorization/activation/control/physical are distinct boundaries. |
| Adversarial tests | Cases 9–14 and AI candidate creation; direct SQL M7 write denied, candidate API ID confusion and importing materializer via helper detected. |
| PostgreSQL enforcement | Proposal role has no INSERT/UPDATE/DELETE on M7/policy/runtime tables; grants reviewed/tested independently of superuser negative harness. |
| API contract | No transfer/candidate/activate/deploy/execute endpoints. Conceptual future request would bind exact grant/currentness, translation version, human request and M7 assessment. |
| Static boundaries | No executable path to ControlledPolicyVersionRepository/materializeControlledPolicyVersionCandidate, policy activation, Control Engine, MQTT, AMQP, DTE, actuator or physical endpoint. |
| Regression | Negative integration ensures zero M7/runtime row changes from full A–E workflow; existing M7 tests unchanged and still pass. |
| Recovery | Reject requested transfer with POLICY_CANDIDATE_AUTHORITY_FORBIDDEN; no partial M7 row/artifact/outbox, compensation or implicit retry. |
| Non-goals | No candidate creation, automatic translation, activation readiness assessment, deployment, control authorization or physical capability. |
| Definition of Done | Checked full dependency graph/DB privileges and all escape tests show NO EXECUTABLE PATH; future transfer remains out of scope with no 0063. |

## GDSS-008G — Verification, Adversarial Validation & Closure

Authorization: `GDSS_008G_NOT_AUTHORIZED`.

| Contract field | Phase requirement |
|---|---|
| Purpose | Establish executable evidence that the entire future proposal workflow satisfies science, governance, isolation and no-execution limits. |
| Scope | Verification and evidence reconciliation only; forty invariants, twenty-eight attacks, benchmarks/limits, PostgreSQL authority, regressions and closure report. |
| Inputs | Separately authorized A–F candidate, frozen architecture/plan, exact source commit, isolated disposable DB and enabled test matrix. |
| Outputs | Future A–G evidence manifest, count/skip reconciliation, migration/authority/currentness/static results and explicit closure decision; no feature implementation. |
| Entities | No feature entity/table; evidence documents reference exact code/test/schema/artifact hashes and environment versions. |
| Services | Exercise planned services end-to-end; do not add service behavior during verification. |
| Migration | None. Verify 0057->0058->0059->0060->0061->0062 and isolated reversible phase cycles only under later test authorization; no principal migration in P038. |
| RBAC | All project roles, unauthenticated/service/AI principals and forged-body roles exercised; runtime trusted identity boundaries demonstrated. |
| SoD | Positive independent humans, named single-admin exception if enabled, reinforced separation and every AI/exception bypass tested. |
| Hashing | Golden vectors for proposal, impact/risk, review/grant/withdrawal/events; UUID/order/idempotency stability and every semantic mutation changes hash. |
| Immutability | SQL UPDATE/DELETE and child insertion after freeze; audit/grant/review/withdrawal/event append-only checks and tampered projection detection. |
| Idempotency | Repeat workflow and replay after withdrawal/expiry; same-key changed-semantics conflicts; no duplicate effective grant/version. |
| Concurrency | Actual successor, assembly, review, grant, withdrawal, source-change and trigger races; persist counts and linearization outcomes, not only Promise resolution. |
| Resource limits | Every architecture section 40 limit at 50%, 100%, one-over; data distribution, bytes/RSS/time/lock wait, repeated cold/warm samples, concurrent admission and no truncation. |
| Invariants | POL-INV-01..40 each linked to enabled executable U/P/S/W evidence; no missing owner or critical skip. |
| Adversarial tests | All section 42 cases 01..28 with protected-state checks and audit outcomes, including transitive/static/role escapes. |
| PostgreSQL enforcement | Fresh clean isolated disposable database, sequential source-to-proposal workflow and SQL bypass/races; principal only read-only heads/current inspection. |
| API contract | Future contract/integration checks for every supported route, scoped absence, strict errors, exact hashes and fresh currentness on historical replay. |
| Static boundaries | Full changed/transitive dependency scan, no M7/control/messaging/physical execution, no universal scalar authority; classify guards/docs/negative tests separately. |
| Regression | Future full topology-next unit/integration, explicit GDSS-007 and M7 compatibility, TypeScript and production build; Python/PCE regressions verify unaffected runtime; justify every skip. |
| Recovery | A failed gate blocks closure; classify finding and seek narrowly authorized remediation, then repeat affected proof and final integrity checks; no silent feature repair. |
| Non-goals | No implementation, scope expansion, commit/publication, DB hygiene cleanup, principal mutation or deployment through closure verification. |
| Definition of Done | 40/40 invariants and 28/28 attacks pass with executable evidence; all boundaries/races/hash/limits/migrations/regression pass, no critical skips, complete architecture/evidence reconciliation and final authority NONE for policy/control/physical. |

## 5. Verification ownership and acceptance matrix

Architecture sections 41–42 are normative: all POL-INV-01..40 and attacks 01..28 must have a named
phase owner and enabled test/evidence reference. IDs may not be renumbered to hide failures.
U/P/S/W proof types are complementary: mocked unit tests cannot establish PostgreSQL authority,
and declaration-only static assertions cannot establish no executable path. Test exact negative
state, retained adverse history and error classification as well as success paths.

Resource gates use the exact architecture profile and rationale, not guessed capacity: identities
8/16/17; objectives 8/16/17; constraints 32/64/65; conditions 32/64/65; thresholds 32/64/65;
monitoring 16/32/33; evidence 5000/10000/10001; reviews 16/32/33; impact 8/16/17; risk 16/32/33.
Include payload/nesting/key/assumption/limitation bounds and concurrent one-over SQL bypass.
Benchmarks are planned diagnostics, not an SLA or a claim that GDSS-008 already passed.

Security traceability: source escalation/substitution/widening (A), constraint/threshold tampering
(B), adverse omission/risk suppression (C), AI/SoD/replay (D), stale-source/withdrawal/supersession
(E), direct M7/policy/control/physical escape (F), complete adversarial cross-phase proof (G).
No future feature may change this authority ceiling without a separately approved architecture.

## 6. PostgreSQL evidence and recovery policy

Preserve P035-F01 history: NONDETERMINISTIC_POSTGRESQL_VERIFICATION_ASSERTION, originally BLOCKING,
REMEDIATED with 10/10 isolated processes and 60/60 tests PASS. Do not rewrite existing harnesses or
counts during P038. Future deterministic tests must accept scientifically equivalent canonical pair
orientations and reject the inverse semantic relation.

The principal DB contains accumulated historical test fixtures. Preserve
`TEST_ENVIRONMENT_HYGIENE_WARNING` / `NON_BLOCKING`. Future authoritative verification must use a
CLEAN ISOLATED DISPOSABLE DATABASE with a deterministic complete fixture chain. No globally-latest
fixture selection; every suite binds exact project/version/hash and explicit setup artifacts.
Prior GDSS-007 clean PostgreSQL 46/46 PASS remains historical evidence, not GDSS-008 evidence.
No principal cleanup, migrations, stamp or fixture mutation is authorized by P038.

For later authorized work, failures roll back atomically. DB migration repair/cycles only in
explicitly authorized disposable test environments; never downgrade shared principal. Freeze
violations demand successors. A source integration/locking deficiency blocks the phase for a scoped
contract review; do not expand into 007/M7 refactors. A rejected/withdrawn/expired grant cannot be
restored through retries, a new request key, AI assistance or a SoD exception.

## 7. Final design state

```text
GDSS_008A_NOT_AUTHORIZED
GDSS_008B_NOT_AUTHORIZED
GDSS_008C_NOT_AUTHORIZED
GDSS_008D_NOT_AUTHORIZED
GDSS_008E_NOT_AUTHORIZED
GDSS_008F_NOT_AUTHORIZED
GDSS_008G_NOT_AUTHORIZED

COMPLETED_GDSS_008_ARCHITECTURE_AND_IMPLEMENTATION_PLAN_CONTRACT
YES — AUTHORIZED POLICY PROPOSAL WITHOUT POLICY EXECUTION AUTHORITY
```

This answers the design closure question only. Recommendation can inform an explicit human decision;
that decision can support a separate versioned proposal; reviewed proposal may receive a distinct
consideration-only authorization. It cannot automatically become a candidate, approved policy,
active rule, control command or actuator instruction. A future governed transfer requires new
architecture and explicit authorization. No implementation, Git publication or runtime enablement
is authorized by this plan.
