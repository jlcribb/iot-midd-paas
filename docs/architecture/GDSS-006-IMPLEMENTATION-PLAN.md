# GDSS-006 — Governed Validation, Uncertainty & Predictive Evidence Foundation

## Implementation Plan Contract

Status: `GDSS_006A_THROUGH_006G_VERIFIED`; `GDSS_006_IMPLEMENTED_AND_VERIFIED`

Architecture source: `docs/architecture/GDSS-006-ARCHITECTURE.md`

Implementation authorization: `MIDD-GDSS-P018-R1` for GDSS-006A, `MIDD-GDSS-P019-R1` for GDSS-006B, `MIDD-GDSS-P020-R1` for GDSS-006C, `MIDD-GDSS-P021-R1` for GDSS-006D, `MIDD-GDSS-P022-R1` for GDSS-006E, `MIDD-GDSS-P023-R1` for GDSS-006F, corrective remediation `MIDD-GDSS-P024-R2` for the GDSS-006B lineage-depth contract, and corrective remediation `MIDD-GDSS-P024-R3` for canonical resource limits and the cross-phase AI authority boundary

Final verification and closure: `MIDD-GDSS-P025-R1`; evidence in `docs/architecture/GDSS-006G-CLOSURE-EVIDENCE.md`

Corrective migration classification: `0050` is the GDSS-006B lineage remediation; `0051` is the GDSS-006 cross-phase resource/AI-authority remediation. Neither is a new functional phase.

Physical authority: `NONE`

Implementation evidence: `docs/architecture/GDSS-006A-IMPLEMENTATION-EVIDENCE.md`

GDSS-006B evidence: `docs/architecture/GDSS-006B-IMPLEMENTATION-EVIDENCE.md`

GDSS-006C evidence: `docs/architecture/GDSS-006C-IMPLEMENTATION-EVIDENCE.md`

GDSS-006D evidence: `docs/architecture/GDSS-006D-IMPLEMENTATION-EVIDENCE.md`

GDSS-006E evidence: `docs/architecture/GDSS-006E-IMPLEMENTATION-EVIDENCE.md`

GDSS-006F evidence: `docs/architecture/GDSS-006F-IMPLEMENTATION-EVIDENCE.md`

The remaining GDSS-006G phase description is a planning contract only. Its final verification and
closure remain pending after the corrective P024-R2 and P024-R3 remediations recorded here.

## 1. Baseline and non-negotiable boundary

The plan targets branch `main` at
`dee81328f4a73b525f8d7236d8ee799044b9cabc`, Alembic `0043`. GDSS-001..005 remain immutable.

```text
Observation
  != Calibration Evidence
  != Validation Evidence
  != Predictive Evidence
  != Predictive Capability
  != Predictive Claim
  != Control Authorization
```

No phase may add physical authority, MQTT/DTE/Control Engine dependency, live-telemetry access,
automatic adaptation, ML/RL, or reinterpret GDSS-005 fit as validation.

## 2. Architectural reconciliation and final sequence

The architecture's 006A–006G sequence is retained. `ValidityDomainIdentity/Version` begins in 006A
because a sealed protocol must bind its scope before evidence is exposed; 006E adds domain
evaluation, position classification and evidence consumption rather than redefining it.

| Phase | Epistemic objective | Migration | Completion output |
|---|---|---|---|
| 006A | Predeclare immutable validation meaning and domain scope | 0044 + corrective 0051 binding check | sealed protocol/domain contracts |
| 006B | Prove partition roles and govern holdout disclosure | 0045 + corrective 0050/0051 | published partition and single-use custody |
| 006C | Commit predictions and pair them without temporal rewriting | 0046 | immutable validation-run/pair evidence |
| 006D | Compute typed performance, baseline and uncertainty evidence | 0047 + corrective 0051 | versioned result evidence |
| 006E | Evaluate domain position and materialize complete evidence sets | 0048 + corrective 0051 authorization | immutable evidence set/strength profile |
| 006F | Assess scoped capability and govern claims/revalidation | 0049 + corrective 0051 profile reconciliation | reviewed/authorized or rejected claims |
| 006G | Prove all invariants and close | none expected | adversarial and regression closure evidence |

The phase migrations were originally proposed rather than pre-reserved. 006G introduces no feature
migration; a defect found there returns to its owning phase and requires an explicitly reviewed
corrective migration.
That process produced forward-only `0050` for the GDSS-006B lineage-depth mismatch; the effective
source and principal head became `0050`. P024-R3 then produced forward-only `0051`, enforcing the
canonical 16-metric/8-baseline limits and the AI authority-denial boundary. Source and principal head
are now `0051`; GDSS-006G verification and closure completed under `MIDD-GDSS-P025-R1`.

## 3. Shared implementation conventions

- TypeScript domain contracts live under `apps/topology-next/src/lib/gdss/validation/`.
- Repositories and services follow existing `gdss-*` repository/service boundaries.
- PostgreSQL is authoritative for governance relations, ownership, uniqueness and state history.
- Large canonical manifests are content-addressed artifacts with relational projections and byte/hash
  reconciliation, following GDSS-003..005.
- APIs, when later authorized, remain in the official Next.js backend and use existing authenticated
  project membership. No second authentication system is introduced.
- Scientific state changes and audit writes share one database transaction.
- Unknown semantic versions, hashes, domain inputs or lineage fail closed.
- Every phase adds unit, PostgreSQL, service, integration and boundary tests appropriate to its scope.

## 4. GDSS-006A — Contracts, Protocol & Domain Foundation

### Scope and inputs

Input is an exact published `SystemModelVersion`, optional exact dynamic binding, governed target
definitions, domain scope and author-proposed protocol. Output is a versioned protocol that can be
reviewed, approved and sealed without executing validation.

### Entities and value objects

```text
ValidationProtocolIdentity       ValidationProtocolVersion
ValidationTarget                ValidationHorizon
ValidationAcceptanceCriterion   ValidationExclusionPolicy
ValidationMissingnessPolicy     ValidationOutlierPolicy
ValidationMultiplicityPolicy    ValidationRevalidationTrigger
ValidityDomainIdentity          ValidityDomainVersion
DomainPredicate                 DomainBoundary
```

V1 domain predicate types are `NUMERIC_RANGE`, `CATEGORICAL_MEMBERSHIP`, `TEMPORAL_RANGE`,
`PARAMETER_RANGE`, `SYSTEM_STATE_RANGE`, `ENVIRONMENTAL_RANGE` and
`TOPOLOGY_CONFIGURATION_MATCH`. Spatial geometry and arbitrary expressions are deferred. Assumptions
and boundary conditions are structured key/version/reference assertions, not executable text.

### Protocol lifecycle

```text
DRAFT -> REVIEW_REQUIRED -> APPROVED -> SEALED
DRAFT | REVIEW_REQUIRED | APPROVED -> INVALIDATED
SEALED -> SUPERSEDED | INVALIDATED
```

Only `DRAFT` content is mutable. `REVIEW_REQUIRED`, `APPROVED` and later changes occur through
append-only lifecycle events; returning to draft creates a successor version. `SEALED` requires
exact hashes for model, domain, policies, metrics requested by identifier/version, baselines,
uncertainty requirements and resource profile. A sealed or executed version is never edited.

### Services and permissions

`ValidationProtocolService` creates drafts/successors, validates and seals. `ValidityDomainService`
validates predicate grammar and versions. Permissions are `AUTHOR_VALIDATION_PROTOCOL` and
`APPROVE_VALIDATION_PROTOCOL`; seal requires approver authority. V1 records same-actor authorship as
a separation warning and forbids self-approval for `admin`-capable multi-member projects; a
single-admin project may self-approve only with an explicit `SOD_EXCEPTION` audit reason. This uses
existing membership/RBAC and extends its permission vocabulary.

### Invariants, tests and acceptance

Owns VAL-INV-01..07, 09, 14, 15, 26, 27, 29, 32, 37 and 40 foundations. Tests cover lifecycle,
successor creation, exact version binding, domain grammar, policy completeness, canonical hashing,
self-approval controls and all forbidden universal-score/authority fields.

Acceptance requires deterministic golden hashes across insertion order, PostgreSQL freeze guards,
project isolation, append-only lifecycle, and zero changes to GDSS-001 model tables.

### Non-goals, recovery and closure

No partitions, holdout data, runs or results. Drafts may be abandoned; post-seal correction creates
a successor and supersedes the old version. Migration downgrade is allowed only before any later
phase references 0044 rows. Git closure requires focused tests, typecheck, build, migration
upgrade/downgrade/upgrade on an isolated database, exact diff review and one phase commit.

## 5. GDSS-006B — Evidence Partitioning & Holdout Custody

### Scope and entities

```text
EvidencePartitionPlanIdentity   EvidencePartitionPlanVersion
EvidenceUnitIdentity            EvidenceLineageReference
EvidenceRoleAssignment          ValidationDatasetSnapshot
GovernedHoldout                 HoldoutAccessEvent
HoldoutExposureLedger           HoldoutEvaluation
```

Inputs are exact GDSS-005 dataset/source/point hashes plus a sealed protocol. Output is a published,
hash-bound partition and, where declared, a sealed single-use holdout.

### Partition and leakage rules

An evidence unit is the smallest independent assignment unit: source record/channel/time coordinate,
or a protocol-declared group/window. Lineage edges point from derived units to every transitive
source. Publication computes closure and rejects:

- direct or transitive cross-role overlap;
- duplicate source-record/content identities across roles;
- dependent group splitting;
- feature windows extending beyond forecast origin;
- validation/holdout inputs used by calibration, tuning or selection;
- missing lineage for an independence claim.

Duplicate detection V1 is exact identity/hash plus protocol-declared natural key. Probabilistic
near-duplicate detection is deferred and its absence is an explicit limitation.

### Holdout custody and exposure ledger

V1 policy is `SINGLE_USE`:

```text
DRAFT -> SEALED -> OPENED_FOR_EVALUATION -> CONSUMED -> RETIRED
SEALED | OPENED_FOR_EVALUATION | CONSUMED -> INVALIDATED
```

Opening locks the holdout row, checks sealed eligible model/protocol hashes, inserts exactly one
append-only event and marks `OPENED_FOR_EVALUATION` atomically. Result disclosure or any use for
tuning/selection marks it `CONSUMED`. Resealing is impossible and never restores independence.

Each exposure event records actor, reason, resource hash, DB-generated timestamp, scope, access type,
outcome, model/protocol hashes and independence effect. Payload values are not copied to the audit
record. Events reject update/delete.

### Services, permissions and tests

`EvidencePartitionService`, `LineageClosureService` and `HoldoutCustodyService`; permissions
`PUBLISH_EVIDENCE_PARTITION`, `SEAL_HOLDOUT`, `OPEN_HOLDOUT`. The holdout opener cannot be the model
tuner/partition author unless an audited `SOD_EXCEPTION` is approved by another admin; AI actors are
always rejected.

Owns VAL-INV-08, 16..22 and supports 35. Positive/negative tests prove closure, temporal windows,
groups, exact duplicates, missing lineage, concurrent opening, consumption, forbidden reopen and
append-only exposure.

### Non-goals, recovery and closure

No validation execution or metric calculation. A failed open transaction exposes nothing. An
unknown commit after successful open is reconciled by idempotency key and returned event; never open
again. Invalidated holdouts remain retained. Phase closure uses real PostgreSQL concurrency tests.

## 6. GDSS-006C — Validation Runs, Predictions & Pairing

### Scope and entities

```text
ValidationRun                   ValidationRunEvent
PredictionRecord                PredictionCommitment
ObservationReference            PredictionObservationPair
PairIntegrityAssessment         ValidationArtifact
```

A run binds sealed protocol, published partition, exact model/content/binding, snapshot and holdout
state. It produces predictions and immutable pair evidence; it computes no metrics.

### Prediction commitment V1

The canonical prediction artifact contains model/content hash, simulation/input/parameter hashes,
forecast origin, target, horizon, values, optional declared interval, boundary/domain context and
producer provenance. A single PostgreSQL transaction:

1. verifies all references and canonical bytes;
2. stores/reconciles the content-addressed artifact;
3. inserts an immutable commitment with unique prediction hash;
4. assigns `committed_at` from PostgreSQL `clock_timestamp()`;
5. appends the audit event.

The application cannot supply or update `committed_at`. The DB time plus append-only row and artifact
hash proves ordering within the governed Midd-IoT trust boundary. It does not constitute an external
trusted timestamp. Therefore V1 calls this `PLATFORM_PROSPECTIVE`; `EXTERNAL_PROSPECTIVE` requires a
future signed timestamp authority or independently witnessed receipt.

### Temporal integrity

Separate coordinates are `forecast_origin`, `prediction_time`, DB `committed_at`, observation
`measurement_time`, source/admission `observation_ingestion_time`, and DB `pairing_time`.
Prospective eligibility requires commitment before the earliest governed availability of the target
observation, not merely before ingestion into Midd-IoT. Unknown prior availability degrades
temporality. A pair created after the fact remains stored with `PREDICTION_AFTER_OBSERVATION` and is
excluded from prospective strength.

### Services, permission and tests

`ValidationRunService`, `PredictionCommitmentService`, `ObservationPairingService`; permission
`RUN_VALIDATION`. Operations use idempotency keys. Runs are append-only
`ACCEPTED -> RUNNING -> terminal`; commitment and pairs are immutable.

Owns VAL-INV-12, 15, 23..25 and supports 37. Tests cover all three prediction modes, timestamp
ordering, mutation rejection, stale hashes, cross-project references, observation successors,
retry/unknown commit and concurrent pair creation.

### Non-goals, recovery and closure

No metrics, claims or external TSA. Orphan artifact writes are reconciled by content hash; DB failure
leaves an unreferenced artifact eligible for governed garbage collection, never evidence. Partial
runs retain committed predictions and failure events. Closure includes deterministic replay and
artifact/relational reconciliation.

## 7. GDSS-006D — Metrics, Baselines & Uncertainty

### Entities

```text
ValidationMetricDefinitionIdentity/Version  ValidationMetricResult
PredictiveBaselineIdentity/Version          BaselineComparisonResult
UncertaintySource                          UncertaintyAssessment
UncertaintyPropagationMethodVersion        PredictionInterval
```

### V1 allowlists

Continuous scalar: `MAE_V1`, `RMSE_V1`, `BIAS_V1`. Relative: `SMAPE_V1` only when the sealed
protocol declares a positive denominator floor and treatment of both-zero pairs. Dynamic:
`TRAJECTORY_RMSE_V1`, `PEAK_MAGNITUDE_ERROR_V1`, `PEAK_TIMING_ERROR_V1`,
`STEADY_STATE_DEVIATION_V1`. Every formula, operation order, units, prerequisites, missing policy,
aggregation, directionality, interpretation and implementation ID is immutable and hashed.

Probabilistic scores are excluded from V1 because current governed prediction contracts do not
provide full distributions. Declared intervals may be assessed using `INTERVAL_COVERAGE_V1` and
`MEAN_INTERVAL_WIDTH_V1`; this does not imply a distribution.

Baseline V1: `NAIVE_LAST_VALUE_V1`, `HISTORICAL_MEAN_V1`, `SEASONAL_NAIVE_V1` and
`AUTHORIZED_REFERENCE_MODEL_V1`. `DOMAIN_HEURISTIC` and `SIMPLE_LINEAR_BASELINE` are deferred until
their parameter/training contracts are governed. Model and baseline must share pair-set hash,
target, horizon, cutoff, metric and exclusion policy.

### Uncertainty V1

All eight architectural source kinds are representable with status
`KNOWN_QUANTIFIED | KNOWN_UNQUANTIFIED | UNKNOWN | NOT_APPLICABLE`. V1 supports declared absolute/
relative bounds, supplied prediction intervals and empirical interval coverage. It records structural
and domain uncertainty qualitatively. Monte Carlo, Bayesian inference and implicit independence
assumptions are excluded. `DECLARED_BOUND_ENVELOPE_V1` is the only propagation method and requires
explicit dependence assumptions; otherwise the result is `UNKNOWN`.

### Services, tests and closure

`ValidationMetricRegistry`, `ValidationMetricService`, `PredictiveBaselineService`,
`UncertaintyAssessmentService`; execution permission is inherited from `RUN_VALIDATION`, registry
publication requires admin protocol authority.

Owns VAL-INV-06, 26..32 and 37. Golden-vector tests cover formulas, units, operation order,
non-finite values, SMAPE edge cases, pair-set mismatch, weak/strong baselines, unknown uncertainty
and interval coverage. No later phase is needed. Recovery is deterministic re-materialization under
the same unique input hash; conflicting bytes fail integrity.

## 8. GDSS-006E — Domain Assessment & Predictive Evidence Sets

### Scope and entities

```text
DomainValidityAssessment       PredictivePositionAssessment
PredictiveEvidenceSet          PredictiveEvidenceReference
PredictiveEvidenceLimitation   PredictiveEvidenceConflict
PredictiveEvidenceNegativeFinding
EvidenceStrengthProfile        EvidenceStrengthAxisAssessment
EvidenceCompletenessAssessment
```

006E consumes the 006A domain version. Numeric predicates support inclusive/exclusive bounds and a
conservative exact-boundary rule: without a governed tolerance, only equality with an included
declared bound proves `NEAR_DOMAIN_BOUNDARY`. Categorical predicates use exact membership; boolean
conditions use their existing declarative contract. V1 has no categorical distance, so no “near”
category exists. Missing or incompatible predicate inputs yield `DOMAIN_UNKNOWN`. Spatial geometry
is deferred.

Position is based on both domain predicates and observed validation support. Inside declared bounds
but outside evidence support is `EXTRAPOLATION`, not interpolation.

An evidence set references exact model, protocol, partition, holdout state, runs, pair sets, metric
results, baseline comparisons, uncertainty/domain assessments, exclusions, violations, negative
evidence and provenance. Materialization locks inputs, verifies completeness, stores a canonical
manifest/artifact and immutable relational projection. Successors add new evidence; they never edit.

The strength profile has seven independent axes: independence, temporality, domain coverage,
uncertainty completeness, baseline strength, replication and data quality. Each uses
`UNKNOWN | INSUFFICIENT | LIMITED | ADEQUATE | STRONG` plus axis-specific evidence. No total score.

`GdssPredictiveEvidenceService` requires `ASSEMBLE_PREDICTIVE_EVIDENCE`. Owns VAL-INV-04, 05,
33..37. Tests prove fail-closed unknowns,
boundary behavior, extrapolation, adverse-evidence completeness, immutable materialization,
concurrent deduplication and successor semantics.

No capability or claim decision occurs. Failed assembly commits no evidence set; retry by input hash
returns the existing set. Phase closure includes byte/hash reconciliation and scope completeness.

## 9. GDSS-006F — Capability, Claims & Revalidation

### Entities and scope

```text
PredictiveCapabilityAssessment  PredictiveClaimIdentity
GovernedPredictiveClaim         PredictiveClaimReview
PredictiveClaimAuthorization    PredictiveClaimRevocation
RevalidationTriggerAssessment   EvidenceTransferAssessment
```

Capability is exactly bound to `(model_version, target, horizon, validity_domain_version,
protocol_family, metric_profile, baseline_profile, uncertainty_profile, evidence_period)` and one
evidence-set hash. States are `NOT_EVALUATED`, `INSUFFICIENT_EVIDENCE`,
`EVIDENCE_OF_LIMITED_CAPABILITY`, `EVIDENCE_OF_CAPABILITY`, `CONFLICTING_EVIDENCE`,
`EVIDENCE_OF_FAILURE`, `INVALIDATED`. Assessments are immutable materializations; new evidence creates
a successor assessment.

Claim lifecycle is:

```text
DRAFT -> EVIDENCE_ASSEMBLED -> REVIEW_REQUIRED -> AUTHORIZED | REJECTED
AUTHORIZED -> SUPERSEDED | REVOKED
```

Only draft structured fields are mutable. Human text is rendered from a versioned template. An
authorized claim cannot be edited. Authorization may narrow or reject scope, never upgrade strength.
Claim `valid_through` is optional structured scope; expiry makes reads report
`HUMAN_REVIEW_REQUIRED` but does not delete or rewrite authorization.

### Revalidation and transfer

Represent all architectural trigger kinds. Detection may be manual/event-driven in V1; continuous
drift detection is deferred. Contradictory evidence creates a review-required trigger atomically.
V1 `EvidenceTransferAssessment` default and only positive implementation outcome is
`FULL_REVALIDATION_REQUIRED`; `TRANSFER_REJECTED` records incompatible requests. Partial transfer and
equivalence are vocabulary-reserved but not executable. Therefore `NO_AUTOMATIC_TRANSFER` is exact.

### Permissions and tests

Services are `PredictiveCapabilityService`, `PredictiveClaimService` and `RevalidationService`.
Permissions: `REVIEW_CAPABILITY_ASSESSMENT`, `AUTHORIZE_PREDICTIVE_CLAIM`,
`REVOKE_PREDICTIVE_CLAIM`, `AUDIT_PREDICTIVE_EVIDENCE`. Claim author and authorizer must differ,
subject only to the documented single-admin `SOD_EXCEPTION`; AI can propose a draft but can never
review, authorize or revoke.

Owns VAL-INV-03, 04, 07, 10, 11, 13, 14, 35, 38..40. Tests cover every state, claim grammar,
scope-subset proof, authorization replay, concurrency, revocation, contradictory evidence,
version transfer and AI denial.

No policy recommendation or actuation. Unknown commit is reconciled by claim/input hash and
idempotency key. Revocation is append-only and repeat requests return the existing event.

## 10. GDSS-006G — Verification, Adversarial Validation & Closure

006G adds no substantive domain capability. It executes the complete VAL-INV-01..40 matrix, twenty
adversarial scenarios, PostgreSQL concurrency/immutability tests, canonical golden vectors,
cross-version/project isolation, artifact reconciliation, full GDSS regressions and dependency
scans.

Inputs are committed outputs of 006A–F. Outputs are an implementation-evidence document, exact test
counts, resource benchmark evidence, migration head proof and controlled Git closure candidate.
Failures return to the owning phase; 006G does not hide them through test-only exceptions.

Acceptance requires all invariants executable, all critical adversarial cases fail closed, no
negative evidence loss, no physical authority/dependency and clean upgrade from 0043 through the
final head. Recovery means no production repair under a verification-only authorization. Git closure
requires exact diff classification and separate publication authorization.

## 11. Persistence plan

All IDs are UUID operational keys; all identity tables have `(project_id, canonical_key)` unique.
Every version has `(identity_id, version_number)` unique and predecessor FK. Composite project-aware
FKs or trigger checks prevent cross-project substitution.

| Table/aggregate | Keys and normalized relations | Checks, immutability, indexes |
|---|---|---|
| `gdss_validation_protocol_identity` | PK id; project FK; logical key | unique project/key; immutable |
| `gdss_validation_protocol_version` | identity/version/predecessor; exact model, binding, domain FKs; protocol hash | closed state/version; hash unique when sealed; draft freeze trigger; indexes model/domain/state |
| `gdss_validation_protocol_target` | protocol FK; ordinal; quantity/unit/horizon | unique protocol/ordinal and semantic target; freezes with protocol |
| `gdss_validation_protocol_policy` | protocol FK; typed normalized policy and bounded JSON detail | type/version checks; freezes with protocol |
| `gdss_validation_protocol_event` | protocol FK; sequence; from/to; actor/reason | append-only; legal-transition trigger; unique sequence |
| `gdss_validity_domain_identity` | PK/project/logical key | immutable; unique project/key |
| `gdss_validity_domain_version` | identity/version/predecessor; domain hash | sealed freeze; unique hash/version |
| `gdss_domain_predicate` | domain FK; ordinal/type/operator/unit/bounds/categories/reference | closed types; bounded JSON only for typed operand; freezes with domain |
| `gdss_evidence_partition_identity/version` | project key; protocol/dataset hashes; plan hash | published freeze; unique version/hash |
| `gdss_evidence_unit` | partition FK; exact source dataset/record/hash/channel/time/group | unique semantic unit; source/project coherence |
| `gdss_evidence_lineage` | child/ancestor unit FKs; depth | unique edge; depth cap; cycle rejection |
| `gdss_evidence_role_assignment` | unit FK; role; partition | one role per plan; overlap trigger |
| `gdss_validation_dataset_snapshot` | partition/protocol; manifest artifact/hash | immutable; unique snapshot hash |
| `gdss_governed_holdout` | partition/snapshot; policy/state; eligible hashes | single-use checks; row lock transitions; project coherence |
| `gdss_holdout_access_event` | holdout/sequence/idempotency; actor, scope, effect, DB time | append-only; unique sequence/idempotency; access indexes |
| `gdss_holdout_evaluation` | holdout/run; model/protocol; outcome | unique holdout for SINGLE_USE |
| `gdss_validation_run` | project/protocol/partition/model/snapshot; attempt/idempotency | unique idempotency; exact hash checks; state index |
| `gdss_validation_run_event` | run/sequence/type/actor/reason | append-only legal lifecycle |
| `gdss_validation_artifact` | project/kind/media/payload or backend key; bytes/SHA-256 | content reconciliation; immutable; unique kind/hash |
| `gdss_prediction_record` | run; target/horizon/origin; exact hashes; prediction hash | immutable; unique prediction hash within project |
| `gdss_prediction_commitment` | prediction; DB committed_at; commitment hash/trust class | insert-only; unique prediction; no application timestamp |
| `gdss_observation_reference` | pair scope; GDSS-005 dataset/point/source hashes and times | exact FK/hash coherence |
| `gdss_prediction_observation_pair` | prediction/observation/rule; pair hash | immutable; unique semantic pair/hash |
| `gdss_pair_integrity_assessment` | pair; temporal state/details hash | immutable; closed result |
| `gdss_metric_definition_identity/version` | logical key/version; canonical formula metadata/hash | immutable registry; same ID/version cannot change |
| `gdss_validation_metric_result` | definition; pair-set/horizon/domain/subgroup; result hash | immutable; finite/unit checks; unique input/result identity |
| `gdss_baseline_identity/version` | logical key/version/config/hash | immutable registry |
| `gdss_baseline_comparison_result` | model/baseline metric results; pair-set hash | identical-scope trigger; immutable |
| `gdss_uncertainty_source` | run/evidence scope; kind/status/value/unit/reference | tagged status/value constraints; immutable |
| `gdss_uncertainty_method_version` | registry ID/version/content hash | immutable allowlist |
| `gdss_prediction_interval` | prediction/method/level/bounds | ordered finite bounds; immutable |
| `gdss_uncertainty_assessment` | evidence scope/sources/method/result hash | immutable; source manifest required |
| `gdss_domain_validity_assessment` | domain/context/predicate results/hash | immutable; exact domain version |
| `gdss_predictive_position_assessment` | domain assessment/support manifest/classification | immutable; closed class |
| `gdss_predictive_evidence_set` | project/model/protocol/partition/version/predecessor/hash/artifact | immutable; unique input manifest/hash |
| `gdss_predictive_evidence_reference` | set; typed exact evidence FK/hash; polarity | all required types; no delete; index polarity |
| `gdss_evidence_strength_axis` | set; axis/level/evidence details | seven unique axes; no aggregate score |
| `gdss_capability_assessment` | evidence set; exact scope/state/hash/predecessor | immutable; unique scope/evidence hash |
| `gdss_predictive_claim_identity/version` | project key; assessment/scope/template/hash | drafts mutable; frozen after evidence assembly |
| `gdss_predictive_claim_event` | claim/sequence/lifecycle/actor/reason | append-only legal transitions |
| `gdss_predictive_claim_review` | claim/reviewer/decision/rationale | immutable; reviewer separation checks |
| `gdss_predictive_claim_authorization` | claim/authorizer/decision/hash/idempotency | immutable; one effective decision; SoD trigger/service check |
| `gdss_predictive_claim_revocation` | claim/actor/reason/trigger/idempotency | append-only; unique effective revocation |
| `gdss_revalidation_trigger_assessment` | model/claim/evidence; type/state/hash | immutable event evidence; unresolved index |
| `gdss_evidence_transfer_assessment` | source/target model; result/reason/hash | V1 results restricted; immutable |

Lifecycle, exposure, execution, authorization and revocation events stay normalized. Bounded policy
operands, predicate values and diagnostic details may use JSONB with schema version and size checks;
ownership, versions, roles, references, states, hashes and evidence polarity never live only in JSON.

## 12. Migration plan

- `0044`: protocol/domain identities, versions, targets, policies, predicates and lifecycle guards.
- `0045`: partition, units, lineage, role assignment, snapshots, holdouts and exposure ledger.
- `0046`: validation runs/events/artifacts, predictions, commitments, observation refs and pairs.
- `0047`: metric/baseline registries and results, uncertainty sources/methods/intervals/assessments.
- `0048`: domain/position assessments, evidence sets/references and strength axes.
- `0049`: capability, claim lifecycle/review/authorization/revocation, revalidation and transfer.
- `0050`: corrective GDSS-006B lineage-depth enforcement at the canonical 16-edge boundary; no new
  scientific capability and no historical evidence rewrite.
- `0051`: corrective cross-phase enforcement of canonical metric/baseline limits and the AI
  authority-denial boundary; no new scientific capability.

Each migration must upgrade from the immediately prior head, have downgrade ordered by FK dependency,
and pass isolated upgrade/downgrade/upgrade. Once scientific evidence exists, operational rollback is
forward-fix or feature disablement; destructive downgrade is not a production retention strategy.

## 13. Hashing and determinism

Use domain-separated SHA-256 and existing canonical JSON/binary64/unit/time rules. Required hashes:

```text
validation_protocol_hash       midd:gdss:validation-protocol:v1
validity_domain_hash           midd:gdss:validity-domain:v1
partition_plan_hash            midd:gdss:evidence-partition:v1
validation_snapshot_hash       midd:gdss:validation-snapshot:v1
prediction_hash                midd:gdss:prediction:v1
prediction_commitment_hash     midd:gdss:prediction-commitment:v1
pair_hash                      midd:gdss:prediction-observation-pair:v1
pair_set_hash                  midd:gdss:prediction-pair-set:v1
metric_definition_hash         midd:gdss:validation-metric-definition:v1
metric_result_hash             midd:gdss:validation-metric-result:v1
baseline_definition_hash       midd:gdss:predictive-baseline:v1
baseline_comparison_hash       midd:gdss:baseline-comparison:v1
uncertainty_assessment_hash    midd:gdss:uncertainty-assessment:v1
domain_assessment_hash         midd:gdss:domain-assessment:v1
evidence_set_hash              midd:gdss:predictive-evidence-set:v1
capability_assessment_hash     midd:gdss:capability-assessment:v1
predictive_claim_hash          midd:gdss:predictive-claim:v1
```

Include exact semantic references, versions, policies, formulas, predicates, evidence identities,
forecast/measurement times, semantic seed and exclusions. Exclude random UUID, DB row order, actor
session, worker, retry and ordinary created-at times. `committed_at` participates in commitment and
temporal-integrity evidence, not in prediction content hash. Audit events need no content identity
unless referenced as evidence; their sequence and DB time remain immutable audit coordinates.

Every hash has golden vectors, permutation tests, one-bit mutation tests and TypeScript/PostgreSQL
artifact reconciliation. `CONTENT_HASH != PERSISTENCE_ID`.

## 14. Immutability, concurrency and idempotency

| Object/operation | Model | Concurrency/idempotency |
|---|---|---|
| protocol/domain draft | `MUTABLE_DRAFT` | optimistic version or row lock; update not idempotent |
| seal protocol/domain | `IMMUTABLE_AFTER_SEAL` | lock version; idempotent by version/hash |
| partition publication | immutable after publication | lock; idempotent by plan hash |
| holdout exposure ledger | `APPEND_ONLY` | holdout row lock; unique idempotency key |
| open holdout | append-only transition | serial lock; exactly one successful open |
| run events | `APPEND_ONLY` | sequence lock; idempotent admission key |
| prediction commitment | `IMMUTABLE_ALWAYS` | unique prediction hash; idempotent commitment |
| pair/result/assessment | `IMMUTABLE_ALWAYS` | unique canonical input hash; create-or-get |
| evidence set materialization | `IMMUTABLE_ALWAYS` | advisory/row lock over manifest hash; create-or-get |
| claim draft | `MUTABLE_DRAFT` | optimistic version |
| claim authorization | immutable event | lock claim; unique effective decision/idempotency |
| revocation | `APPEND_ONLY` | lock authorization; repeated request returns same event |

Two successor versions serialize on their identity and allocate `max(version)+1` under lock plus
unique constraint. Database triggers reject update/delete of immutable scientific and audit rows.

## 15. Authorization and separation of duties

Extend existing project-scoped membership/RBAC; do not use generic `edit_policies` as the long-term
scientific permission. During phased rollout, the new permission registry maps viewer/operator/admin
compatibly but services always ask the named GDSS capability.

| Action | Required capability | SoD rule |
|---|---|---|
| author protocol | `AUTHOR_VALIDATION_PROTOCOL` | actor recorded |
| approve/seal protocol | `APPROVE_VALIDATION_PROTOCOL` | different actor; explicit exception path |
| publish partition | `PUBLISH_EVIDENCE_PARTITION` | cannot conceal overlap findings |
| seal/open holdout | `SEAL_HOLDOUT` / `OPEN_HOLDOUT` | opener differs from tuner/author by default |
| run validation | `RUN_VALIDATION` | exact sealed inputs only |
| assemble evidence | `ASSEMBLE_PREDICTIVE_EVIDENCE` | cannot omit scoped adverse results |
| review capability | `REVIEW_CAPABILITY_ASSESSMENT` | evidence immutable |
| authorize claim | `AUTHORIZE_PREDICTIVE_CLAIM` | author != authorizer by default |
| revoke claim | `REVOKE_PREDICTIVE_CLAIM` | reason and trigger required |
| audit | `AUDIT_PREDICTIVE_EVIDENCE` | read-only |

Single-admin exceptions are explicit, reasoned, separately flagged and never upgrade evidence.
AI-authenticated/provenance actors are hard-denied for open, strength assessment authorization,
claim authorization and adverse-evidence exclusion.

## 16. Future API and service contract

No endpoint is authorized now. Future routes are project-scoped under `/api/control/validation/projects/[projectId]`.

| Group | Methods | Permission and mutation | Idempotency / principal failures |
|---|---|---|---|
| protocols | create/update draft, submit, approve, seal, successor, read | author/approve; lifecycle transaction | create/seal keys; not sealed, stale version, SoD |
| validity-domains | create/update/seal/successor/evaluate | author/approve or assemble | hash idempotency; unknown predicate/input |
| partitions | create/publish/read | publish | plan hash; overlap/leakage/lineage errors |
| holdouts | seal/open/consume/retire/read ledger | seal/open | event key; not sealed, consumed, independence compromised |
| validation-runs | admit/start/complete/abort/read | run | admission key; frozen-input mismatch |
| predictions | commit/read | run | prediction hash; commitment missing/tampering |
| pairings | create/read | run | pair hash; temporal violation retained |
| metrics | register/read/materialize result | admin/run | definition/input hash; not allowed/nonfinite |
| baselines | register/evaluate/compare | admin/run | definition/input hash; pair-set mismatch |
| uncertainty | register source/method, assess/read | run | input hash; unsupported method/unknown source |
| evidence-sets | materialize/successor/read | assemble | manifest hash; incomplete/omitted negative evidence |
| capability | assess/read/successor | review | scope/input hash; insufficient/conflicting evidence |
| claims | draft/assemble/review/authorize/reject/revoke/read | author/review/authorize/revoke | event key; scope excess/SoD/stale authorization |

Inputs use strict versioned schemas; outputs return IDs plus content hashes and lifecycle state.
Mutation services write governance audit in the same transaction.

## 17. Domain error model

Closed initial codes:

```text
VALIDATION_PROTOCOL_NOT_SEALED       VALIDATION_PROTOCOL_FROZEN
ILLEGAL_PROTOCOL_TRANSITION         VALIDITY_DOMAIN_NOT_SEALED
DOMAIN_PREDICATE_UNSUPPORTED        DOMAIN_INPUT_MISSING
EVIDENCE_PARTITION_OVERLAP          TRANSITIVE_LINEAGE_OVERLAP
EVIDENCE_LINEAGE_INCOMPLETE         DEPENDENT_GROUP_SPLIT
TEMPORAL_LEAKAGE_DETECTED           FUTURE_INFORMATION_LEAKAGE
HOLDOUT_NOT_SEALED                  HOLDOUT_ALREADY_OPENED
HOLDOUT_ALREADY_CONSUMED            HOLDOUT_INDEPENDENCE_COMPROMISED
MODEL_VERSION_MISMATCH              PROJECT_SCOPE_MISMATCH
PREDICTION_COMMITMENT_MISSING       PREDICTION_COMMITMENT_TAMPERED
PREDICTION_AFTER_OBSERVATION        PAIRING_RULE_MISMATCH
METRIC_NOT_ALLOWED                  METRIC_PREREQUISITE_FAILED
NONFINITE_METRIC_RESULT             BASELINE_PAIRSET_MISMATCH
UNCERTAINTY_METHOD_NOT_ALLOWED      UNCERTAINTY_SOURCE_UNKNOWN
DOMAIN_UNKNOWN                      OUTSIDE_VALIDITY_DOMAIN
EVIDENCE_SET_INCOMPLETE             NEGATIVE_EVIDENCE_OMITTED
INSUFFICIENT_EVIDENCE               CONFLICTING_EVIDENCE
CLAIM_SCOPE_EXCEEDS_EVIDENCE        CLAIM_AUTHORIZATION_FORBIDDEN
CLAIM_ALREADY_TERMINAL              STALE_AUTHORIZATION_REPLAY
EVIDENCE_TRANSFER_FORBIDDEN         PHYSICAL_AUTHORITY_FORBIDDEN
ARTIFACT_INTEGRITY_FAILURE          IDENTITY_MISMATCH
RESOURCE_LIMIT_EXCEEDED             IDEMPOTENCY_CONFLICT
```

Each error has stable code, stage, bounded deterministic details and audit disposition. Stack traces
and infrastructure timing remain operational diagnostics.

## 18. Test architecture

- **Unit:** schemas, lifecycle, hash vectors, policy validation, formulas, domain predicates.
- **Persistence:** real PostgreSQL FKs, checks, triggers, freeze/delete rejection, project/version
  isolation, lifecycle sequences and artifact reconciliation.
- **Service:** RBAC, SoD, idempotency, holdout custody, evidence completeness and claim scope.
- **Integration:** protocol-to-claim workflow with GDSS-003/005 references and failure recovery.
- **Concurrency:** simultaneous holdout open, successor allocation, evidence materialization,
  authorization, revocation and double admission.
- **Adversarial:** leakage, tampering, stale substitution, suppression and overclaiming.
- **Regression:** GDSS-001..005 unit/integration suites, topology build/typecheck, Python and Control
  Engine baselines appropriate to closure.
- **Static boundaries:** no MQTT, DTE, Control Engine runtime, live telemetry, policy activation or
  actuation imports/routes.

Critical invariants receive positive and negative tests. Persistence/retry/concurrency invariants use
real PostgreSQL, not mocks.

## 19. VAL-INV-01..40 test matrix

| Invariant | Required tests |
|---|---|
| 01 | reject calibration result as validation run input; accept separate validation evidence |
| 02 | reject in-sample role as out-of-sample; accept disjoint partition |
| 03 | prediction alone yields `NOT_EVALUATED`; paired set may form evidence |
| 04 | reject universal capability/claim fields; retain scoped assessment |
| 05 | in-domain positive and outside-domain non-transfer negative |
| 06 | four error/uncertainty combinations; unknown never zero |
| 07 | authorization cannot change strength axes; narrowing succeeds |
| 08 | tuning exposure consumes holdout; pristine sealed holdout remains independent |
| 09 | execution rejected before seal; sealed protocol accepted |
| 10 | successor model requires full revalidation; exact model accepted |
| 11 | failed/negative run appears in evidence set; omission rejected |
| 12 | prior commitment accepted; post-observation commitment flagged |
| 13 | no control/actuation capability in result; static dependency scan |
| 14 | equal/narrower claim accepted; wider domain/horizon rejected |
| 15 | exact model/content hash accepted; substituted version/hash rejected |
| 16 | disjoint lineage accepted; shared direct/transitive unit rejected |
| 17 | published membership frozen; successor plan accepted |
| 18 | cutoff-safe feature accepted; future-window feature rejected |
| 19 | intact group accepted; cross-partition group rejected |
| 20 | complete closure accepted; missing ancestor fails independence |
| 21 | exposure insert accepted; update/delete rejected |
| 22 | consumed holdout reopen/reseal rejected; historical event retained |
| 23 | exact prediction replay idempotent; changed committed bytes rejected |
| 24 | new corrected observation creates successor pair; pair update rejected |
| 25 | retrospective record retained; prospective strength rejected after observation |
| 26 | registered version accepted; post-result/new definition rejected |
| 27 | scoped metric accepted; universal score contract rejected |
| 28 | predeclared combination accepted; silent conflict collapse rejected |
| 29 | statistical and operational conclusions stored separately |
| 30 | identical pair scope accepted; baseline mismatch rejected |
| 31 | multiple baseline results retained; one win cannot erase another loss |
| 32 | registered uncertainty method accepted; unversioned/implicit method rejected |
| 33 | proven membership accepted; missing predicate input returns unknown |
| 34 | interpolation support accepted; extrapolation inheritance rejected |
| 35 | complete adverse set accepted; selective evidence set rejected |
| 36 | invalid result excluded from aggregate but retained in audit/evidence refs |
| 37 | exact horizon result accepted; cross-horizon claim rejected |
| 38 | contradictory evidence creates review trigger and blocks current claim |
| 39 | successor/revocation append accepted; historical overwrite/delete rejected |
| 40 | all artifacts return `physicalAuthority: NONE`; physical path scan empty |

## 20. Mandatory adversarial scenarios

| # | Attack/test | Expected result |
|---:|---|---|
| 1 | calibration dataset reused as holdout | `EVIDENCE_PARTITION_OVERLAP` |
| 2 | duplicate record across partitions | rejected by identity/hash/natural key |
| 3 | derived feature leaks holdout source | `TRANSITIVE_LINEAGE_OVERLAP` |
| 4 | future observation in prediction input | `FUTURE_INFORMATION_LEAKAGE` |
| 5 | holdout opened before model/protocol freeze | `VALIDATION_PROTOCOL_NOT_SEALED` |
| 6 | holdout reopened after tuning | `HOLDOUT_ALREADY_CONSUMED` |
| 7 | prediction altered after commitment | `PREDICTION_COMMITMENT_TAMPERED` |
| 8 | prediction committed after observation availability | retained, prospective strength invalid |
| 9 | metric threshold changed after result | frozen protocol/definition rejection |
| 10 | baseline uses different pair set | `BASELINE_PAIRSET_MISMATCH` |
| 11 | ModelVersion changed without revalidation | `MODEL_VERSION_MISMATCH` |
| 12 | domain predicate value unavailable | `DOMAIN_UNKNOWN` |
| 13 | extrapolation labeled interpolation | position reconciliation failure |
| 14 | negative evidence omitted | `NEGATIVE_EVIDENCE_OMITTED` |
| 15 | materialized evidence set altered | immutable trigger/hash failure |
| 16 | claim wider than evidence | `CLAIM_SCOPE_EXCEEDS_EVIDENCE` |
| 17 | human authorizer upgrades strength | rejected; original evidence unchanged |
| 18 | AI attempts claim authorization/open | `CLAIM_AUTHORIZATION_FORBIDDEN` |
| 19 | revoked claim presented as current | read projection marks revoked, never current |
| 20 | contradictory evidence without review | transaction creates trigger or blocks assembly |

## 21. Performance and resource boundaries

V1 profiles are identity-bearing and fail before work allocation. Initial hard safety caps are:

```text
pair records per ValidationRun       100,000
metric definitions per protocol          16
domain predicates per version             64
baselines per protocol                      8
transitive lineage depth                   16
evidence references per EvidenceSet    10,000
```

Rationale: at a conservative 512 bytes canonical metadata per pair, 100k pairs bounds a pair
manifest near 50 MiB before indexes/artifacts; 16 metrics bounds scalar passes to 1.6M pair-metric
evaluations; 64 predicates and 8 baselines exceed expected V1 model scope while preventing unbounded
payloads; depth 16 catches cycles/runaway derivations; 10k evidence refs force aggregation manifests
rather than row-copying. 006C–E benchmarks must measure wall time, RSS, artifact bytes and DB rows at
50%, 100% and one-over-limit. Limits may only change by a versioned profile with benchmark evidence.

## 22. Security, retention and observability

| Threat | Control |
|---|---|
| holdout disclosure | separate custodian permission, opaque refs, minimal ledger detail, access audit |
| hash tampering | canonical bytes, SHA-256, DB artifact reconciliation, immutable rows |
| forged timestamp | DB-assigned commitment time; trust-class disclosure; future external TSA |
| unauthorized protocol edit | draft-only update, freeze triggers, lifecycle permission |
| result suppression | completeness query and required adverse references |
| unauthorized claim promotion | named permission, SoD, transaction/audit, AI denial |
| stale authorization replay | claim/evidence hashes, lifecycle lock, idempotency conflict |
| cross-project evidence reuse | composite project/version FKs and service scope checks |
| version substitution | exact IDs plus content hashes at every boundary |

Scientific evidence is not physically deleted by GDSS APIs. Use `SUPERSEDED`, `REVOKED`,
`INVALIDATED` or `RETIRED`. A future institutional privacy/retention process may cryptographically
erase protected payloads while retaining tombstone/hash/audit evidence, but is out of scope.

Sensitive sealed payloads use the existing governed storage and project access boundary; audit logs
store hashes and scope, not values. External independence requires signed-import or governed-object
provenance plus an independent custodian assertion; otherwise classify it internal/unknown.

Operational logs/metrics include failures, duration, counts, denials, lock contention and integrity
violations. They never become predictive evidence automatically:

```text
OPERATIONAL_OBSERVABILITY != PREDICTIVE_EVIDENCE
```

## 23. ADR-to-phase mapping

| ADR | Owner | Artifacts/tests | Principal risk |
|---|---|---|---|
| 001 calibration-validation separation | 006A | protocol/model refs; INV-01/02 | semantic collapse |
| 002 partition/holdout | 006B | partition, lineage, ledger; INV-08/16-22 | leakage |
| 003 protocol immutability | 006A | lifecycle/freeze; INV-09/17/26 | retrospective editing |
| 004 uncertainty first-class | 006D | sources/methods/assessment; INV-06/32 | false certainty |
| 005 explicit validity domain | 006A/006E | predicates/assessment; INV-05/33/34 | overgeneralization |
| 006 evidence aggregation | 006E | evidence set/references; INV-35/36 | cherry-picking |
| 007 claim governance | 006F | claim lifecycle/auth; INV-07/14/39 | claim inflation |
| 008 negative/conflicting evidence | 006E/006F | polarity/triggers; INV-11/28/35/38 | suppression |
| 009 multidimensional strength | 006E | seven axes; INV-27/35 | reductive score |
| 010 commitment/pair separation | 006C | commitment/pair; INV-12/23-25 | temporal forgery |
| 011 version binding/transfer | 006F | transfer assessment; INV-10/15 | silent inheritance |
| 012 no physical authority | all/006G | contracts and scans; INV-13/40 | authority escape |

## 24. Resolved architectural decisions

- Trusted time V1: PostgreSQL-assigned append-only commitment time; strength is internal platform
  prospective, not external cryptographic time.
- External evidence: exact hash/provenance plus independent custodian assertion; otherwise no
  external-independence classification.
- Dependent units: protocol-declared group key is atomic; missing required key fails publication.
- Holdout reuse: `SINGLE_USE` only.
- Metrics: conservative deterministic scalar/dynamic allowlist; no probability distributions.
- Uncertainty: sources/status, declared bounds/interval coverage; one bounded propagation method.
- Categorical distance: exact membership only; missing is unknown, mismatch outside.
- Version equivalence: not implemented; full revalidation only.
- Claim expiry: optional structured `valid_through` causes review, never evidence deletion.
- Privacy: inherit governed storage/RBAC, minimize audit payload; new privacy subsystem deferred.

No open decision blocks implementation planning. Each deferred feature fails toward the conservative
default rather than becoming implicit behavior.

## 25. Definition of Done by phase

| Phase | Required closure evidence |
|---|---|
| 006A | 0044 verified; protocol/domain hashes/lifecycle/freeze/RBAC tests; no execution path |
| 006B | 0045 + corrective 0050/0051 verified; 16-edge leakage/lineage boundary, AI-denied holdout opening and concurrent single-use holdout tests; exposure audit |
| 006C | 0046 verified; commitment/pair temporal and retry/artifact tests; all modes explicit |
| 006D | 0047 + corrective 0051 verified; golden metric/baseline/uncertainty vectors, 16/8 resource boundaries and mismatch failures |
| 006E | 0048 + corrective 0051 verified; domain/position/evidence completeness, AI-denied authoritative assembly and immutable-set tests |
| 006F | 0049 + corrective 0051 verified; 16/8 profiles, scope/SoD/claim/revocation/revalidation/transfer tests; no authority path |
| 006G | 40/40 invariants, 20/20 adversarial, concurrency, limits, full regression and clean diff |

Every phase additionally reports scope, inputs/outputs, entities, migration, services, permissions,
tests, non-goals, rollback/recovery and exact Git closure evidence as specified in sections 4–10.

## 26. Total GDSS-006 closure criteria

GDSS-006 is implemented only when:

- VAL-INV-01..40 pass executable positive/negative coverage;
- critical leakage and holdout contamination fail closed;
- protocol/domain are versioned, sealable and immutable;
- prediction commitment and pairing prove their declared temporal trust class;
- metrics/baselines are versioned and scope-comparable;
- uncertainty and domain are first-class;
- evidence sets preserve all scoped adverse evidence;
- capability is exact-scope-bound;
- claims are structured, human-governed, revocable and historical;
- no model version inherits evidence automatically;
- no GDSS-001..005 regression or semantic mutation exists;
- physical, recommendation and control authority remain `NONE`.

## 27. Original proposed implementation files

The planning baseline proposed the following shape. Authorized phases subsequently used a
phase-local split recorded in the 006A..006F evidence documents:

```text
apps/topology-next/src/lib/gdss/validation/{contracts,versions,canonical,protocol,domain,
  partition,lineage,holdout,prediction,pairing,metrics,baselines,uncertainty,evidence,
  capability,claims,revalidation,limits,diagnostics,authorization,index}.ts
apps/topology-next/src/lib/repositories/gdss-validation.repository.ts
apps/topology-next/src/lib/services/gdss-validation.service.ts
apps/topology-next/src/lib/workers/gdss-validation.worker.ts
apps/topology-next/tests/{unit,integration}/gdss-validation.*.test.ts
infra/migrations/alembic/versions/0044_*.py ... 0051_*.py
docs/architecture/GDSS-006-{CONTRACTS,INVARIANTS,ADR,IMPLEMENTATION-EVIDENCE}.md
```

The exact implemented split remained phase-local; no empty scaffolding was created.

## 28. Final recommendation

The independently authorized 006A..006G sequence is implemented and verified. Final executable
closure evidence is recorded in `docs/architecture/GDSS-006G-CLOSURE-EVIDENCE.md`; predictive
claims remain separate from recommendation, control and physical authority.

```text
COMPLETED_GDSS_006_IMPLEMENTATION_PLAN_CONTRACT
```
