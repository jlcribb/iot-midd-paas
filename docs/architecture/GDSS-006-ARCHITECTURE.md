# GDSS-006 — Governed Validation, Uncertainty & Predictive Evidence Foundation

Status: `PROPOSED_ARCHITECTURE`

Decision: `GOVERNED_PREDICTIVE_VALIDATION`

Implementation status: `NOT_AUTHORIZED`

Physical authority: `NONE`

## 1. Purpose

GDSS-006 defines how Midd-IoT may assemble reproducible, auditable evidence that one exact
`SystemModelVersion` has a bounded predictive capability. It governs validation protocols,
evidence partitions, holdout access, predictions, observation pairing, metrics, baselines,
uncertainty, validity domains, evidence aggregation, capability assessments and predictive claims.

The admissible statement is deliberately scoped:

> For model version M, protocol V and evidence set E, within domain D and horizon H, the evidence
> supports conclusion C with uncertainty U relative to baseline B and limitations L.

The system optimizes for a correct conclusion, including `INSUFFICIENT_EVIDENCE`, rather than for a
positive claim.

## 2. Scope

This architecture covers:

- pre-result validation protocol definition;
- immutable partitioning and transitive leakage analysis;
- governed holdout sealing, exposure and consumption;
- retrospective, pseudo-prospective and prospective prediction evidence;
- immutable prediction-to-observation pairing;
- typed metric and baseline comparison results;
- first-class uncertainty sources, propagation and assessments;
- structured validity domains and extrapolation classification;
- preservation of positive, negative, conflicting and inconclusive evidence;
- evidence-bound capability assessments and human-governed claims;
- deterministic identities, provenance, audit and revalidation triggers.

## 3. Exclusions

GDSS-006 does not implement or authorize:

- production code, migration `0044`, database changes, APIs or UI;
- changes to GDSS-001..005 entities or semantics;
- machine learning, reinforcement learning, online learning or automatic optimization;
- adaptive model updates or continuous drift detection;
- implicit interpolation, imputation, outlier removal or metric selection;
- automatic operational recommendations, policy changes or physical actuation;
- promotion of calibration evidence into validation evidence;
- a universal `validation_score`, `accuracy` or `is_valid` field.

## 4. Immutable baseline

GDSS-006 references, without redefining:

- GDSS-001: model identity/version, lifecycle, provenance and declarative content;
- GDSS-002: safe expressions, units, dimensions and quantity semantics;
- GDSS-003: simulation input, attempt, result and trajectory identities;
- GDSS-004: experiments, scenario comparisons and comparative findings;
- GDSS-005: observation datasets, exact alignment, calibration designs, estimates, residuals and
  adequacy evidence.

The baseline at design time is branch `main`, commit
`dee81328f4a73b525f8d7236d8ee799044b9cabc`, Alembic `0043`, with a clean worktree.

GDSS-005 adequacy remains scoped to the calibration dataset. Its `DatasetAssignment` roles are a
forward-compatible vocabulary, not an implementation of governed validation or holdout semantics.

## 5. Epistemic boundary

The following distinctions are invariants, not documentation advice:

```text
CALIBRATION != VALIDATION
VALIDATION != PREDICTION
PREDICTION != PREDICTIVE_EVIDENCE
PREDICTIVE_EVIDENCE != GENERAL_PREDICTIVE_CAPABILITY
FIT != GENERALIZATION
IN_SAMPLE_FIT != OUT_OF_SAMPLE_EVIDENCE
INTERPOLATION != EXTRAPOLATION
UNCERTAINTY != ERROR
CONFIDENCE != CERTAINTY
MODEL_VALIDITY != UNIVERSAL_VALIDITY
PREDICTIVE_EVIDENCE != CONTROL_AUTHORIZATION
```

Calibration estimates parameters using designated evidence. Validation evaluates frozen model
behavior against evidence excluded from that estimation and from result-driven model selection.
Prediction is an immutable, time-qualified output. Predictive evidence arises only when such an
output is paired under a prior protocol with later-admitted reference evidence. Capability is a
bounded assessment across that evidence; it is neither truth nor universal validity.

## 6. Architectural boundary and flow

```text
SystemModelVersion + DynamicModelBindingVersion
                    |
                    v
ValidationProtocolVersion --> EvidencePartitionPlanVersion --> GovernedHoldout
                    |                         |                    |
                    v                         v                    v
          ValidationDatasetSnapshot --> ValidationRun --> PredictionRecord
                                                        --> PredictionObservationPair
                                                        --> ValidationMetricResult
                                                        --> BaselineComparisonResult
                                                        --> UncertaintyAssessment
                                                        --> DomainValidityAssessment
                                                                    |
                                                                    v
                                                   PredictiveEvidenceSet
                                                                    |
                                                                    v
                                             PredictiveCapabilityAssessment
                                                                    |
                                                                    v
                                                  GovernedPredictiveClaim
```

Each arrow is an exact identity/hash reference. No stage resolves “latest” state during execution.

## 7. Aggregate roots and entities

### 7.1 `ValidationProtocolIdentity` / `ValidationProtocolVersion`

The identity names the validation program; an immutable version defines the result-blind contract.
It binds eligible exact model versions, target, origin/horizon/windows, snapshots, partition plan,
metrics, thresholds, uncertainty methods, baselines, subgroups, domains, missing/outlier policies,
extrapolation rules, acceptance logic, inconclusive rules, invalidation criteria, semantic versions
and resource bounds.

### 7.2 `EvidencePartitionPlanIdentity` / `EvidencePartitionPlanVersion`

Owns exact source dataset versions and hashes, atomic evidence-unit assignments, role, partition
method, temporal cutoff, grouping keys, exclusions, seed when semantic, derivation closure,
justification and author provenance. It never copies or mutates GDSS-005 observations.

### 7.3 `GovernedHoldout`

Owns a sealed manifest reference, permitted purpose, eligible protocol/model hashes, exposure budget,
access policy and append-only `HoldoutAccessEvent`s. Dataset content remains in its governed source;
the aggregate governs independence and disclosure.

### 7.4 `ValidationDatasetSnapshot`

An immutable projection of admitted evidence used by one protocol. It references exact
`ObservationDatasetVersion`s, point/source hashes, transformations, quality/missingness summaries,
partition role and inclusion/exclusion manifest. Derived features require transitive lineage.

### 7.5 `ValidationRun`

An operational aggregate binding one frozen protocol hash, partition hash, model/content hash,
binding hash, input snapshots, execution attempts and terminal evidence. Retries share the same
computational manifest but have distinct operational attempt identities.

### 7.6 `PredictionRecord`

An immutable evidence object containing exact model and producer evidence, forecast origin, issuance
time, target, horizon, value or distribution, interval if declared, input and parameter snapshots,
boundary conditions, domain context, provenance and deterministic hash.

### 7.7 `PredictionObservationPair`

An immutable association between a previously committed prediction and exact admitted observation.
It records prediction issuance/origin, observation measurement time, observation admission time,
pairing time, pairing rule, reference hashes, lag/horizon and temporal-integrity conclusion.

### 7.8 Metric, baseline and uncertainty entities

- `ValidationMetricDefinitionVersion`: typed mathematical contract and applicability.
- `ValidationMetricResult`: exact pair-set input, subgroup/horizon/domain scope and result.
- `PredictiveBaselineVersion`: immutable comparator definition and exact input policy.
- `BaselineComparisonResult`: per-metric model/baseline difference and uncertainty.
- `UncertaintySource`: typed origin, scope, evidence and known/unknown status.
- `UncertaintyPropagationMethodVersion`: closed/versioned propagation contract.
- `PredictionInterval`: level, bounds/distribution, method and target/horizon scope.
- `UncertaintyAssessment`: coverage, sharpness, assumptions, limitations and conclusion.

### 7.9 `ValidityDomainIdentity` / `ValidityDomainVersion`

Owns a structured conjunction/disjunction of versioned predicates over variables, ranges,
parameters, system states, environment, temporal/spatial scale, horizon, topology, equipment or
process class, assumptions and boundary conditions. Text may explain but cannot define the domain.

### 7.10 `DomainValidityAssessment`

Evaluates an exact prediction/context snapshot against an exact domain version and retains each
predicate result plus an aggregate position classification.

### 7.11 `PredictiveEvidenceSet`

An immutable manifest over all relevant validation runs, partitions, predictions, pairs, metrics,
baselines, uncertainty and domain assessments, exclusions, failures, limitations and evidence
polarity. It is append-only by successor version; contrary evidence cannot be deleted.

### 7.12 `PredictiveCapabilityAssessment`

An immutable interpretation of one evidence-set version under a declared assessment method. It
produces a scoped state and a multidimensional evidence-strength profile, never a universal score.

### 7.13 `GovernedPredictiveClaim`

An exact, reviewable assertion binding model version, protocol, evidence set, capability assessment,
domain, horizon, target, metrics, baselines, uncertainty, limitations, negative evidence and claim
wording/template version. Authorization changes claim authority, never evidence strength.

## 8. Value objects

Core value objects are:

```text
EvidenceUnitIdentity         SourceLineageClosure
EvidenceRoleAssignment      TemporalPartitionRule
ForecastOrigin              PredictionHorizon
ObservationWindow           ValidationWindow
PredictionTarget            PairingRule
MetricApplicability         MetricThreshold
SubgroupDefinition          MissingnessPolicy
OutlierPolicy               ExclusionReason
UncertaintyQuantity         CoverageLevel
DomainPredicate             DomainPosition
EvidenceStrengthProfile     EvidenceLimitation
RevalidationTrigger         DeterministicReference
```

`EvidenceUnitIdentity` is the smallest non-overlapping epistemic unit: normally exact source record
plus channel/target/time coordinate, or a declared group/window where dependence requires atomic
assignment. It includes transitive source lineage so derived copies cannot evade overlap detection.

## 9. Closed vocabularies

```text
EvidenceRole =
  CALIBRATION | VALIDATION | HOLDOUT | BENCHMARK |
  EXTERNAL_VALIDATION | CHALLENGE

HoldoutState =
  DRAFT | SEALED | OPENED_FOR_EVALUATION | CONSUMED | RETIRED | INVALIDATED

PredictionMode =
  RETROSPECTIVE | PSEUDO_PROSPECTIVE | PROSPECTIVE

DomainPosition =
  WITHIN_VALIDITY_DOMAIN | NEAR_DOMAIN_BOUNDARY |
  OUTSIDE_VALIDITY_DOMAIN | DOMAIN_UNKNOWN

PredictionPosition =
  INTERPOLATION | BOUNDARY_PREDICTION | EXTRAPOLATION | UNKNOWN_POSITION

EvidencePolarity =
  SUPPORTING | NEGATIVE | CONFLICTING | INCONCLUSIVE |
  INSUFFICIENT | INVALID_EVALUATION

CapabilityState =
  NOT_EVALUATED | INSUFFICIENT_EVIDENCE |
  EVIDENCE_OF_LIMITED_CAPABILITY | EVIDENCE_OF_CAPABILITY |
  CONFLICTING_EVIDENCE | EVIDENCE_OF_FAILURE | INVALIDATED

BaselineConclusion =
  MODEL_OUTPERFORMS_BASELINE | MODEL_EQUIVALENT_TO_BASELINE |
  MODEL_UNDERPERFORMS_BASELINE | INCONCLUSIVE

ClaimState =
  DRAFT | EVIDENCE_ASSEMBLED | REVIEW_REQUIRED | AUTHORIZED |
  REJECTED | SUPERSEDED | REVOKED
```

Unknown vocabulary versions fail closed. `VALID`/`INVALID` is forbidden as a model-wide summary.

## 10. Lifecycle and immutability

### Protocol

```text
DRAFT -> REVIEWED -> APPROVED -> SEALED -> EXECUTABLE -> RETIRED
```

`SEALED` freezes semantic content and hash. Any change creates a successor version. A protocol must
be sealed before its first governed result is visible. A negative result cannot be repaired by
editing the protocol.

### Holdout

```text
DRAFT -> SEALED -> OPENED_FOR_EVALUATION -> CONSUMED -> RETIRED
                         \---------------------------> INVALIDATED
```

Opening is an auditable disclosure. Evaluation against the preregistered frozen model consumes the
declared use. Any use for tuning, selection, protocol/threshold revision or feature design marks the
holdout consumed for subsequent versions. `INVALIDATED` preserves all prior evidence and reason.

### Validation run

```text
ACCEPTED -> RUNNING -> COMPLETED | COMPLETED_WITH_WARNINGS | FAILED | ABORTED | INVALID
```

Events are append-only; terminal outcomes are immutable. Failure is retained evidence.

### Claim

```text
DRAFT -> EVIDENCE_ASSEMBLED -> REVIEW_REQUIRED -> AUTHORIZED | REJECTED
AUTHORIZED -> SUPERSEDED | REVOKED
```

Revocation is additive. An authorized record is never overwritten or erased.

## 11. Dataset partitioning and leakage resistance

Partitioning operates on `EvidenceUnitIdentity`, not row position. The plan records exact source
hashes, algorithm/version, seed, cutoffs, groups, exclusions and role assignments. Admission checks
compute transitive lineage overlap across source points, windows, derived features, aggregates and
duplicates.

Required controls:

1. direct point/hash disjointness between calibration, validation and holdout;
2. temporal causality: features at forecast origin cannot contain future information;
3. grouped partitioning when units share subject/device/site/process dependence;
4. transformation lineage proving every derived feature's source window;
5. duplicate and near-duplicate detection method/version recorded in the protocol;
6. selection-exposure ledger binding every viewed result to actor, model and purpose;
7. model/protocol freeze before holdout opening;
8. no threshold, subgroup or metric selection after reserved results are observed;
9. explicit policy for repeated comparisons and multiplicity;
10. fail-closed independence classification when lineage is incomplete.

Random seeds are included only when randomness affects membership. A seed does not prove
independence. Temporal validation normally uses a cutoff and embargo/gap, not random splitting.

## 12. Governed holdout

`HOLDOUT_DATASET`, `HOLDOUT_ACCESS_EVENT` and `HOLDOUT_EVALUATION` remain distinct:

- the dataset/snapshot identifies reserved evidence;
- access events record disclosure, actor, purpose, eligible frozen artifacts and material revealed;
- evaluation binds the one permitted protocol/model execution and its results.

A holdout loses independence for a later model or claim when its values, metrics, rankings,
diagnostics or materially informative summaries influence model selection, parameter tuning,
feature engineering, domain definition, thresholds, subgroup choice or protocol revision. It does
not regain independence by resealing. It may remain valid evidence for the exact preregistered model
evaluated before adaptation and remains negative evidence thereafter.

Reuse requires a policy declared before opening: `SINGLE_USE`, `BOUNDED_SEQUENTIAL` with an explicit
statistical correction, or `PROHIBITED_AFTER_DISCLOSURE`. V1 should implement `SINGLE_USE` first.

## 13. Validation protocol architecture

The protocol is the pre-result constitution of an evaluation. Mandatory sections are:

- exact eligible model/content and dynamic binding hashes;
- exact evidence snapshots and partition plan;
- target/quantity/unit, forecast origin and each horizon;
- observation and validation windows;
- inclusion, exclusion, missingness, imputation and outlier rules;
- prediction mode and time-integrity requirements;
- metric definitions, direction, aggregation and thresholds;
- baseline definitions and comparison rules;
- uncertainty sources, methods, levels and adequacy criteria;
- subgroups, structured domain and boundary/extrapolation treatment;
- acceptance, failure, invalid, inconclusive and conflicting-result logic;
- multiplicity policy and operational-relevance thresholds;
- resource limits, semantic versions and revalidation triggers.

Imputation is not implicitly authorized. If a future protocol permits it, the method/version,
inputs, uncertainty effect and imputed-point manifest are identity-bearing.

## 14. Prediction and observation evidence

Evidence strength depends on when and how prediction content was fixed:

- `RETROSPECTIVE`: inputs and observations already existed or were accessible; useful for internal
  reconstruction, weakest against analyst adaptation.
- `PSEUDO_PROSPECTIVE`: historical replay with strict time cutoffs; features and model see only
  information available at each simulated origin, but current analysts may know outcomes.
- `PROSPECTIVE`: prediction bytes are committed under a trusted clock before the target observation
  window is available; strongest temporal evidence, but not automatically external evidence.

For prospective evidence, `prediction_timestamp < observation measurement availability` and the
prediction hash must predate observation access. A prediction created after observation is
`PREDICTION_AFTER_OBSERVATION`, an invalid prospective evaluation; relabeling it retrospective does
not erase the violation from audit history.

Pairing never changes prediction bytes. It references exact hashes and applies a predeclared pairing
rule. Observation correction produces a successor observation version and a successor pair/evidence
set, preserving the original.

## 15. Metrics architecture

Metrics are versioned, typed and applicable only to declared target shapes:

- error: MAE, RMSE, SMAPE where denominator semantics permit, bias, median error;
- distribution: log/likelihood scores, CRPS and calibration/coverage curves;
- classification: sensitivity, specificity, precision, recall, ROC-AUC, PR-AUC, Brier score;
- temporal dynamics: lag, phase, peak magnitude/timing and trajectory distance;
- dynamic systems: steady-state, transient response, overshoot, settling time and accumulated
  trajectory deviation.

Every result binds target, unit/dimension, horizon, domain position, subgroup, pair-set hash,
definition version, operation order and missing/exclusion manifest. “Accuracy = 95%” without these
coordinates is not representable as a governed result.

No metric is globally privileged. The protocol defines decision logic before results. Conflicting
metrics yield `CONFLICTING_EVIDENCE` unless a predeclared, scientifically justified aggregation rule
resolves them. Statistical acceptability and operational relevance are separate conclusions.

## 16. Predictive baselines

`PredictiveBaselineVersion` uses the same evidence cutoffs, horizons, targets, pair set and metric
definitions as the evaluated model. Initial allowlisted families may include:

```text
NAIVE_LAST_VALUE
SEASONAL_NAIVE
HISTORICAL_MEAN
DOMAIN_HEURISTIC
SIMPLE_LINEAR_BASELINE
AUTHORIZED_REFERENCE_MODEL
```

Baseline parameters and training windows are immutable inputs. Beating one weak baseline does not
establish capability when a stronger required baseline is matched or superior. Comparisons remain
per baseline and metric; their aggregate interpretation is protocol-defined.

## 17. Uncertainty architecture

Uncertainty is represented as typed sources rather than one number:

```text
MEASUREMENT_UNCERTAINTY
PARAMETER_UNCERTAINTY
INITIAL_CONDITION_UNCERTAINTY
INPUT_UNCERTAINTY
MODEL_STRUCTURAL_UNCERTAINTY
NUMERICAL_UNCERTAINTY
PREDICTIVE_UNCERTAINTY
DOMAIN_UNCERTAINTY
```

Each source records quantity, unit, support/bounds or distribution if justified, estimation evidence,
assumptions, dependence/correlation and `KNOWN | PARTIALLY_KNOWN | UNKNOWN`. `ALEATORIC` and
`EPISTEMIC` are optional orthogonal classifications; they do not replace system-specific sources.

`UncertaintyAssessment` binds sources, propagation method/version, prediction intervals or
distribution, empirical coverage, sharpness, sample sufficiency and limitations. Unknown is never
decoded as zero. Confidence levels are method-scoped, not universal probabilities that the model is
true.

A point predictor can be evaluated without quantified predictive uncertainty, but it cannot receive
an unrestricted `EVIDENCE_OF_CAPABILITY`. At most it receives limited/incomplete evidence with an
explicit uncertainty gap, unless the protocol justifies why uncertainty is not applicable to a
strictly qualitative claim.

Error is the observed discrepancy after pairing. Uncertainty is the declared variability or limit
of knowledge before or around estimation. Low error/high uncertainty, high error/low uncertainty,
both high and both low are all representable.

## 18. Validity domain and extrapolation

A `ValidityDomainVersion` is a normalized predicate tree. Each leaf declares field identity,
operator, bounds/categories, units, inclusivity, evidence provenance and unknown-data behavior.
Domain evaluation yields every leaf result, distance-to-boundary where meaningful and one aggregate
position.

`NEAR_DOMAIN_BOUNDARY` thresholds are predefined. `DOMAIN_UNKNOWN` is not coerced to in-domain.
Interpolation/extrapolation classification additionally compares current context with the support
of validation evidence, not merely declared physical bounds.

Evidence obtained inside 18–24 °C cannot support a 35 °C claim. Outside-domain predictions may be
generated for exploratory purposes but inherit no in-domain capability and must carry
`EXTRAPOLATION` plus `HUMAN_REVIEW_REQUIRED`.

## 19. Predictive evidence model

Evidence strength is multidimensional. A single PE0–PE5 ladder is rejected as authoritative because
external retrospective evidence, internal prospective evidence and sealed holdout evidence are not
totally ordered. The profile includes at least:

```text
independence:
  IN_SAMPLE | RESAMPLED_INTERNAL | OUT_OF_SAMPLE_INTERNAL |
  SEALED_HOLDOUT | EXTERNAL_INDEPENDENT

temporality:
  RETROSPECTIVE | PSEUDO_PROSPECTIVE | PROSPECTIVE

domain_coverage:
  UNKNOWN | NARROW | PARTIAL | DECLARED_SCOPE_COVERED

uncertainty_completeness:
  NONE | PARTIAL | QUANTIFIED | EMPIRICALLY_ASSESSED

baseline_strength:
  NONE | WEAK | DOMAIN_RELEVANT | MULTIPLE_RELEVANT

replication:
  SINGLE_RUN | REPEATED_INTERNAL | MULTI_PERIOD | EXTERNAL_REPLICATION

data_quality:
  INSUFFICIENT | LIMITED | ACCEPTABLE | STRONG
```

A derived display label may map profiles to PE0–PE5 for communication, but cannot replace axes,
upgrade evidence or participate alone in authorization.

`PredictiveEvidenceSet` contains supporting and adverse evidence, invalid attempts and exclusions.
Successor evidence sets add references; they do not rewrite history.

## 20. Predictive capability assessment

Capability is always a tuple over:

```text
(model version, target, horizon, domain, protocol family,
 metric profile, baseline profile, uncertainty profile, evidence period)
```

The assessment method applies the protocol's predeclared rules and emits state, strength profile,
supporting evidence, negative/conflicting evidence, limitations and expiry/revalidation conditions.
Average success cannot hide subgroup failure, bias, horizon failure or boundary failure.

`EVIDENCE_OF_CAPABILITY` means sufficient evidence for exactly that tuple. It does not mean model
truth, causal validity, future permanence, universal generalization or actuation fitness.

## 21. Governed predictive claims

Claims use a closed, parameterized template rather than free-form promotional language. Required
bindings are model/content hash, protocol hash, evidence-set hash, capability assessment hash,
target, horizon, domain version, performance statements, uncertainty, baselines, limitations,
negative evidence, evidence period and authorization provenance.

Evidence assembly and authorization are independent:

```text
EVIDENCE_STRENGTH != CLAIM_AUTHORIZATION
HUMAN_AUTHORIZATION CANNOT UPGRADE EVIDENCE_STRENGTH
```

Authorization may approve accurate communication of an assessment, reject it, narrow scope or
require more evidence. It cannot broaden domain/horizon, suppress negative evidence or change a
strength axis. New contradictory evidence triggers review and may revoke/supersede the claim while
preserving its historical authorization.

## 22. Negative, conflicting and invalid evidence

Failed validation is evidence. Terminal runs and evidence sets retain:

- model underperformance and systematic bias;
- baseline losses;
- metric/subgroup/horizon conflicts;
- insufficient sample size or uncertainty coverage;
- leakage and temporal-integrity violations;
- artifact/identity failures and protocol deviations;
- out-of-domain and unknown-domain evaluations.

Only scientifically invalid results are excluded from performance aggregation, but they remain in
the audit/evidence manifest with exclusion reason. Negative valid results remain in both aggregate
and interpretation.

## 23. Missingness and evidence quality

Dataset snapshots carry sampling rate, gaps, quality statuses, instrument reliability, resolution,
transformations, aggregation, censoring, imputation and outlier-treatment evidence. The protocol
defines policies; the snapshot records realized conditions and exact affected units.

Post-result exclusion is a protocol deviation unless an explicit anomaly rule decided it without
using target outcomes. Missingness may itself be informative and must not be silently dropped.

## 24. Temporal semantics

`FORECAST_ORIGIN`, `PREDICTION_HORIZON`, `OBSERVATION_WINDOW` and `VALIDATION_WINDOW` are distinct
typed coordinates. Results are grouped by exact horizon or by preregistered horizon buckets.
Combining 5-minute and 24-hour evidence without explicit stratification is forbidden.

Issuance time is an epistemic coordinate for prospective proof. Persistence timestamps remain
operational unless supplied by the trusted evidence-sealing service.

## 25. Deterministic identities

Canonicalization follows existing GDSS conventions: domain-separated SHA-256, sorted object keys,
semantic array order, exact hashes/version identities, canonical units, epoch microseconds and
finite binary64 encodings. Proposed identities are:

```text
validation_protocol_hash
  SHA256("midd:gdss:validation-protocol:v1" + complete sealed semantic protocol)

partition_plan_hash
  SHA256("midd:gdss:evidence-partition:v1" + sources, lineage, assignments and rules)

validation_snapshot_hash
  SHA256("midd:gdss:validation-snapshot:v1" + exact admitted evidence manifest)

prediction_hash
  SHA256("midd:gdss:prediction:v1" + producer evidence, origin, issuance proof,
         target, horizon, outputs, inputs, parameters, boundaries and domain context)

prediction_observation_pair_hash
  SHA256("midd:gdss:prediction-observation-pair:v1" + prediction hash,
         observation evidence, semantic timestamps and pairing rule)

metric_result_hash
  SHA256("midd:gdss:validation-metric-result:v1" + metric version, pair-set hash,
         scope, value and deterministic diagnostics)

uncertainty_assessment_hash
  SHA256("midd:gdss:uncertainty-assessment:v1" + sources, method, scope and results)

domain_assessment_hash
  SHA256("midd:gdss:domain-assessment:v1" + domain version, context and predicate results)

predictive_evidence_set_hash
  SHA256("midd:gdss:predictive-evidence-set:v1" + all evidence references and limitations)

capability_assessment_hash
  SHA256("midd:gdss:capability-assessment:v1" + evidence set, method, scope and conclusion)

predictive_claim_hash
  SHA256("midd:gdss:predictive-claim:v1" + assessment, exact scoped claim and limitations)
```

Random UUIDs, database order, worker identity, retry count and ordinary persistence timestamps are
excluded. Scientifically meaningful cutoffs, forecast/measurement times, seeds, exclusions and
issuance proof are included. Authorization/audit events reference claim hash but do not alter its
scientific content identity.

## 26. Versioning, evidence transfer and revalidation

Changes to model, protocol, snapshot, metric, uncertainty method or domain create new versions and
new downstream identities. A new model version receives no evidence automatically.

An explicit `EvidenceTransferAssessment` may conclude:

```text
NO_TRANSFER
FULL_REVALIDATION_REQUIRED
BOUNDED_INCREMENTAL_VALIDATION_REQUIRED
EQUIVALENCE_EVIDENCE_REQUIRED
```

It never assigns old evidence directly to a new version. Even a one-parameter change requires a
declared equivalence argument or revalidation. Revalidation triggers include formula, parameter,
structure, solver, sensor, topology/environment, operating range, process/species, horizon or
domain change; data/input/parameter/domain/performance drift; and new contradictory evidence.

`MODEL_INVALIDATED` means evidence now contradicts or invalidates a scoped assessment.
`CURRENT_CONDITIONS_OUTSIDE_VALIDATED_DOMAIN` means no inference is available for current context;
it does not by itself falsify in-domain capability.

## 27. Provenance and audit

Every governance-critical object records exact predecessor/reference hashes, actor or system role,
reason, semantic version and append-only lifecycle events. Provenance distinguishes source,
transformation, computational derivation, review and authorization.

Audit events include protocol approval/sealing, partition publication, holdout access/disclosure,
run transitions, prediction commitment, pairing, exclusions, evidence assembly, assessment,
authorization/rejection, supersession/revocation and revalidation decisions. Audit timestamps are
not silently promoted into computational identity.

## 28. Human governance

Proposed capabilities and separation of duties:

```text
AUTHOR_VALIDATION_PROTOCOL
APPROVE_VALIDATION_PROTOCOL
PUBLISH_EVIDENCE_PARTITION
SEAL_HOLDOUT
OPEN_HOLDOUT
RUN_VALIDATION
ASSEMBLE_PREDICTIVE_EVIDENCE
REVIEW_CAPABILITY_ASSESSMENT
AUTHORIZE_PREDICTIVE_CLAIM
REVOKE_PREDICTIVE_CLAIM
AUDIT_PREDICTIVE_EVIDENCE
```

Roles are `PROTOCOL_AUTHOR`, `PROTOCOL_APPROVER`, `EVIDENCE_CUSTODIAN`, `HOLDOUT_STEWARD`,
`VALIDATION_EXECUTOR`, `SCIENTIFIC_REVIEWER`, `CLAIM_AUTHORIZER` and `AUDITOR`. At minimum, holdout
steward is separated from model developer; claim authorizer cannot modify evidence; protocol author
cannot approve a protocol after viewing holdout results. Exact RBAC/SoD policy is an implementation-
plan decision.

AI/LLM output may propose protocols, interpretations or claim drafts with provenance
`AI_PROPOSED`; it cannot seal evidence, open holdouts, upgrade evidence or authorize claims.

## 29. Invariant catalog

| ID | Invariant |
|---|---|
| VAL-INV-01 | Calibration is not validation. |
| VAL-INV-02 | In-sample fit is not out-of-sample evidence. |
| VAL-INV-03 | A prediction is not predictive evidence. |
| VAL-INV-04 | Predictive evidence is not universal model validity. |
| VAL-INV-05 | In-domain validation does not validate outside-domain use. |
| VAL-INV-06 | Uncertainty is not error and unknown uncertainty is not zero. |
| VAL-INV-07 | Human authorization cannot increase evidence strength. |
| VAL-INV-08 | Holdout contamination invalidates independence for affected later claims. |
| VAL-INV-09 | A sealed protocol must precede governed result access. |
| VAL-INV-10 | Model-version change requires explicit evidence-transfer decision. |
| VAL-INV-11 | Negative, conflicting and failed results remain in evidence history. |
| VAL-INV-12 | Prospective prediction commitment must precede observation availability. |
| VAL-INV-13 | Predictive capability is not control authorization. |
| VAL-INV-14 | Claim scope cannot exceed validation scope. |
| VAL-INV-15 | Every result binds the exact model version and content hash. |
| VAL-INV-16 | Calibration and validation roles cannot share an evidence unit or transitive source. |
| VAL-INV-17 | Partition membership is immutable and hash-bound before execution. |
| VAL-INV-18 | Future information cannot enter prediction inputs or derived features. |
| VAL-INV-19 | Group-dependent units cannot cross epistemic partitions. |
| VAL-INV-20 | Incomplete lineage cannot support an independence claim. |
| VAL-INV-21 | Holdout access and disclosure are append-only auditable events. |
| VAL-INV-22 | Consumed holdout cannot silently become independent for an adapted model. |
| VAL-INV-23 | Prediction bytes cannot change after commitment. |
| VAL-INV-24 | Pairing cannot mutate prediction or observation evidence. |
| VAL-INV-25 | Prediction-after-observation cannot count as prospective evidence. |
| VAL-INV-26 | Metric definition, scope and direction precede result computation. |
| VAL-INV-27 | No universal metric or score may erase target/horizon/domain context. |
| VAL-INV-28 | Conflicting metrics remain conflicting unless a prior rule resolves them. |
| VAL-INV-29 | Statistical acceptability is distinct from operational relevance. |
| VAL-INV-30 | Model and baseline use comparable pair sets, horizons and cutoffs. |
| VAL-INV-31 | Beating one baseline does not imply beating all required baselines. |
| VAL-INV-32 | Uncertainty method and assumptions are versioned and evidence-bound. |
| VAL-INV-33 | Domain unknown fails closed; it is not in-domain. |
| VAL-INV-34 | Extrapolation inherits no in-domain capability automatically. |
| VAL-INV-35 | Evidence sets cannot omit valid adverse evidence in their declared scope. |
| VAL-INV-36 | Invalid evaluations remain audited even when excluded from metrics. |
| VAL-INV-37 | Horizon-specific evidence cannot be generalized to another horizon silently. |
| VAL-INV-38 | New contradictory evidence triggers scoped review/revalidation. |
| VAL-INV-39 | Claim revocation/supersession never overwrites historical evidence. |
| VAL-INV-40 | Every GDSS-006 artifact has physical authority `NONE`. |

## 30. Threat and anti-pattern analysis

Forbidden designs and controls:

| Anti-pattern | Required control |
|---|---|
| `validation_score` on `ModelVersion` | scoped result/evidence/assessment aggregates |
| `is_valid = true` | multidimensional state plus domain/horizon |
| `accuracy = 95%` | typed metric, target, dataset, horizon and domain |
| calibration data reused for validation | evidence-unit and lineage disjointness |
| result-driven protocol editing | protocol sealing before result access |
| repeated holdout tuning | exposure ledger and consumption lifecycle |
| deletion of negative results | append-only evidence sets and runs |
| prediction rewritten after outcome | content addressing and temporal commitment |
| evidence silently moved across model versions | exact version binding and transfer assessment |
| “validated model” without scope | claim template rejects absent domain/horizon |
| confidence interpreted as truth | uncertainty method and assumption contract |
| AI elevates evidence | capability checks and human authorization separation |

Primary threats are data leakage, researcher degrees of freedom, weak baseline selection, subgroup
masking, horizon collapse, domain overreach, uncertainty laundering, result suppression and claim
inflation. All fail toward insufficient/conflicting evidence or review.

## 31. Edge-case analysis

| Case | Governed outcome |
|---|---|
| Excellent calibration, poor holdout | `GOOD_CALIBRATION`; `EVIDENCE_OF_FAILURE` for scoped prediction. |
| Moderate fit, good out-of-sample | capability may be supported; calibration quality does not cap it. |
| Good mean metrics, strong bias | negative/conflicting evidence; no aggregate success hides bias. |
| Good at 5 min, poor at 24 h | separate horizon assessments; no 24-hour capability claim. |
| Validated at 18–24 °C, used at 35 °C | `OUTSIDE_VALIDITY_DOMAIN`, `EXTRAPOLATION`, no inherited evidence. |
| Holdout viewed then used for tuning | `CONSUMED`; independence invalid for adapted model. |
| New version changes one parameter | no inheritance; transfer/equivalence assessment required. |
| High instrumental uncertainty | assessment retains it; capability limited or inconclusive. |
| Metrics conflict | `CONFLICTING_EVIDENCE` unless prior decision rule resolves it. |
| Beats absolute but not seasonal baseline | per-baseline outcomes retained; overall rule may be inconclusive/failure. |
| Statistically acceptable, operationally irrelevant | statistical result retained; operational conclusion negative. |
| Prediction created after observation | invalid prospective evaluation; grave temporal violation. |
| Retrospective vs prospective | separate temporality axes; retrospective cannot claim prospective strength. |
| New evidence contradicts authorized claim | review trigger; claim may be revoked/superseded, history preserved. |
| State enters unseen region | `OUTSIDE_VALIDITY_DOMAIN` or `DOMAIN_UNKNOWN`; review required. |

## 32. ADR decisions

| ADR | Decision |
|---|---|
| ADR-GDSS006-001 | Separate calibration and validation aggregates and evidence roles. |
| ADR-GDSS006-002 | Partition atomic evidence units with transitive lineage; govern holdout exposure. |
| ADR-GDSS006-003 | Seal versioned protocols before result access; changes create successors. |
| ADR-GDSS006-004 | Treat uncertainty sources, methods and assessments as first-class evidence. |
| ADR-GDSS006-005 | Define validity domains as structured, versioned predicates. |
| ADR-GDSS006-006 | Aggregate immutable positive and adverse evidence by reference and hash. |
| ADR-GDSS006-007 | Separate capability assessment, claim wording and claim authorization. |
| ADR-GDSS006-008 | Preserve negative, conflicting, failed and invalid evidence append-only. |
| ADR-GDSS006-009 | Use a multidimensional strength profile, not an authoritative PE scalar. |
| ADR-GDSS006-010 | Treat prediction commitment and observation pairing as separate evidence. |
| ADR-GDSS006-011 | Require exact version binding and explicit evidence-transfer assessment. |
| ADR-GDSS006-012 | Keep physical, recommendation and control authority outside GDSS-006. |

Rejected alternatives include embedding validation in calibration, mutable protocols, repeatable
unlogged holdouts, score-only model fields, free-form domains, evidence overwrite, implicit evidence
inheritance and automatic claim authorization.

## 33. Compatibility with GDSS-001..005

- References `SystemModelVersion.content_hash`; does not add validity state to GDSS-001.
- Reuses GDSS-002 quantity/unit semantics for targets, errors, intervals and domain predicates.
- References exact GDSS-003 input/result/trajectory hashes as prediction-producer evidence.
- May cite GDSS-004 experiment evidence, but an experiment result is not automatically validation.
- References GDSS-005 observation/dataset/alignment/calibration hashes without changing them.
- Preserves `OBSERVED`, `SIMULATED`, `PREDICTED`, `MEASURED`, and keeps formula/rule/policy distinct.
- Creates no Control Engine, DTE, MQTT, live telemetry or actuation dependency.

GDSS-005 remains immutable. Validation is a new consumer of exact evidence, not a mode switch on
calibration.

## 34. Future API boundaries

Potential future interfaces, not authorized here:

```text
ValidationProtocolRepository
EvidencePartitionService
HoldoutCustodyService
PredictionCommitmentService
PredictionObservationPairingService
ValidationMetricRegistry
UncertaintyAssessmentService
ValidityDomainAssessmentService
PredictiveEvidenceAssembler
PredictiveCapabilityAssessmentService
PredictiveClaimGovernanceService
RevalidationPolicyService
```

Interfaces accept immutable identities/hashes and return typed outcomes. They do not query live
telemetry, activate policy, recommend control or actuate devices.

## 35. Proposed implementation decomposition

The coherent sequence is:

1. **GDSS-006A — Semantic contracts, protocol and validity-domain foundation.** Define version
   registries, protocol/domain aggregates, canonicalization, lifecycle and foundational invariants.
2. **GDSS-006B — Evidence partitioning and governed holdout custody.** Add evidence units, lineage,
   disjointness, partition plans, exposure ledger and single-use holdout policy.
3. **GDSS-006C — Validation runs, prediction commitment and observation pairing.** Bind exact
   GDSS-003/GDSS-005 evidence, temporal seals, attempts and pairing integrity.
4. **GDSS-006D — Metrics, baselines and uncertainty.** Implement closed registries, typed results,
   comparator parity and uncertainty assessments.
5. **GDSS-006E — Domain assessment and predictive evidence assembly.** Classify domain position,
   interpolation/extrapolation and immutable multidimensional evidence sets.
6. **GDSS-006F — Capability, claims and revalidation governance.** Add scoped assessment,
   authorization/revocation, transfer decisions and drift-trigger vocabulary.
7. **GDSS-006G — Persistence, adversarial verification and controlled closure.** Introduce one
   reviewed migration only after contracts stabilize; append-only DB guards, concurrency/retry,
   hash reconciliation, full invariant matrix and boundary scans.

This ordering puts domain and protocol semantics before evidence exposure and defers claims until all
evidence dimensions exist. Each phase requires separate implementation authorization.

## 36. Proposed implementation constraints

The later implementation plan must resolve:

- exact `0044` schema, ownership and composite project/version foreign keys;
- source-of-truth split between relational governance and content-addressed artifacts;
- trusted prediction timestamp/commitment mechanism;
- atomic holdout opening and exposure-budget transaction;
- lineage closure and duplicate/near-duplicate method;
- exact metric and uncertainty V1 allowlists;
- structured domain predicate grammar and distance semantics;
- deterministic canonical byte formats and artifact compensation;
- capability permissions and separation-of-duty mapping;
- bounded resource profiles and a VAL-INV-01..40 test matrix.

No migration number or table contract is authorized by this document.

## 37. Explicit answers to governance questions

1. **Calibration vs validation:** calibration estimates parameters from designated evidence;
   validation evaluates a frozen exact version using evidence protected from that estimation and
   result-driven selection.
2. **Out-of-sample evidence:** evidence units and transitive lineage excluded from fitting/tuning,
   evaluated under a protocol sealed before results and with temporal/group independence controls.
3. **When holdout independence ends:** when values or informative results influence adaptation,
   selection, thresholds, features, domains or protocol; resealing does not restore independence.
4. **Leakage prevention:** hashed partitions, lineage closure, temporal cutoffs, grouping,
   duplicate checks, exposure ledger, frozen artifacts and fail-closed independence.
5. **Predictive capability:** a scoped evidence-backed assessment for exact model, target, horizon,
   domain, baselines, uncertainty and period—not a property of the model in isolation.
6. **Capability without quantified uncertainty:** only limited/incomplete capability evidence, not
   an unrestricted quantitative claim, except a justified non-quantitative scope.
7. **Uncertainty representation:** typed sources, bounds/distributions, dependencies, propagation
   method, intervals, coverage, sharpness, assumptions and unknown status.
8. **Error vs uncertainty:** error is realized discrepancy; uncertainty quantifies variability or
   limits of knowledge. Neither substitutes for the other.
9. **Validity domain:** a versioned structured predicate tree over system/context/horizon variables,
   supported by evidence and evaluated for every claim scope.
10. **Extrapolation:** it receives no automatic in-domain evidence and requires explicit labeling,
    uncertainty and human review.
11. **Horizon:** evidence and capability are horizon-specific; heterogeneous horizons remain
    stratified unless a prior aggregation rule exists.
12. **Baselines:** they contextualize metrics under identical evidence conditions; multiple
    relevant comparators prevent victory over a deliberately weak reference.
13. **Conflicting metrics:** all remain visible and yield conflicting evidence unless a preregistered
    rule resolves them.
14. **Negative evidence:** stored append-only in runs, metric/baseline results and evidence sets.
15. **Claim governance:** assemble exact evidence, assess capability, review scoped wording, then
    authorize/reject; later evidence may supersede or revoke.
16. **Authorization:** an explicitly permitted human `CLAIM_AUTHORIZER`, subject to separation of
    duties; neither computation nor AI can self-authorize.
17. **Later contradiction:** triggers review/revalidation and possible revocation/supersession while
    preserving history.
18. **New model version:** no automatic inheritance; explicit transfer decision plus equivalence or
    revalidation is required.
19. **Reproduction:** resolve exact hashes/versions, canonical snapshots, sealed protocol,
    partition, prediction/pair manifests, methods and deterministic operation rules.
20. **Preventing a validation score:** separate aggregates, multidimensional strength, mandatory
    target/horizon/domain/baseline/uncertainty bindings, and invariant/test prohibition of scalar
    model-wide validity fields.

## 38. Risks and open questions

Blocking for implementation planning, not for this architecture:

- trusted issuance time and commitment service semantics;
- external-evidence custody and verifier trust model;
- dependence-aware evidence-unit granularity for each domain;
- statistical method for bounded sequential holdout reuse beyond V1;
- approved V1 metrics by model/target family and multiplicity policy;
- uncertainty propagation methods feasible under deterministic resource bounds;
- formal domain-distance semantics for categorical and topological predicates;
- objective evidence-transfer thresholds for narrowly changed model versions;
- claim expiry and revalidation service-level policy;
- privacy/access controls for sealed observations and derived artifacts.

These uncertainties require conservative defaults: single-use holdout, closed method registries,
`DOMAIN_UNKNOWN`, `INSUFFICIENT_EVIDENCE` and human review.

## 39. Authority statement

```text
Control Engine dependency: NONE
DTE dependency:            NONE
MQTT dependency:           NONE
Live telemetry dependency: NONE
Physical actuation:        NONE
Prediction production:     EVIDENCE OBJECT ONLY
Recommendation authority:  NONE
Scientific authority:      NONE
```

What physical action can GDSS-006 authorize? `NOTHING.`

## 40. Architecture recommendation

Proceed to a separately authorized GDSS-006 implementation plan only after review of the open
questions and ADR decisions. Do not create migration `0044` or production code from this document
alone.

Expected architecture closure state:

```text
COMPLETED_GDSS_006_ARCHITECTURE_AND_EPISTEMIC_BOUNDARY
```
