# GDSS-007 — Governed Decision Support, Scenario Evaluation & Recommendation Foundation

## Implementation Plan Contract

Status: `COMPLETED_GDSS_007_ARCHITECTURE_AND_IMPLEMENTATION_PLAN_CONTRACT`

Architecture source: `docs/architecture/GDSS-007-ARCHITECTURE.md`

Versioned contract baseline: `main@edf2be84004cc691ef2dbb0456e4e8b536765382`; `origin/main`
synchronized at implementation preflight. Controlled GDSS-007A–F implementation advances Alembic
source and principal database to the single head `0057`.

Authorization state:

```text
GDSS_007A_IMPLEMENTED
GDSS_007B_IMPLEMENTED
GDSS_007C_IMPLEMENTED
GDSS_007D_IMPLEMENTED
GDSS_007E_IMPLEMENTED
GDSS_007F_IMPLEMENTED
GDSS_007G_VERIFIED

GDSS_007_IMPLEMENTED_AND_VERIFIED
```

```text
PolicyAuthority = NONE
ControlAuthority = NONE
PhysicalAuthority = NONE
```

## 1. Delivery strategy and non-negotiable boundary

Implementation, if separately authorized, proceeds in seven independently reviewable phases. Each
functional phase owns one forward migration, domain contracts, persistence, services, future API
contracts, tests and evidence. No phase may modify migrations `0044..0051`, reinterpret GDSS-006
objects, resolve `latest`, add operational authority or create an implicit bridge to M7.

```text
Decision support output
  -> human review
  -> decision-support authorization
  -> optional Human DecisionRecord
```

No arrow continues to policy, control or actuation. Any future transfer begins a separately governed
policy proposal under separate authorization.

## 2. Phase and migration sequence

| Phase | Objective | Proposed migration | Completion artifact |
|---|---|---:|---|
| 007A | freeze meaning, scope, objectives, constraints, preferences and risk | 0052 | sealed problem version |
| 007B | define immutable alternatives and scenario manifests | 0053 | admitted alternatives/scenarios |
| 007C | execute scenarios and preserve consequences | 0054 | exact evaluation/outcome evidence |
| 007D | compare all alternatives without universal score | 0055 | complete comparison/trade-off set |
| 007E | assess bounded sensitivity, robustness and risk | 0056 | stability/risk evidence |
| 007F | govern recommendation, review, authorization and actual decision | 0057 | human-governed decision-support history |
| 007G | prove invariants, adversarial behavior and closure | none expected | closure evidence |

No migration is created by this planning task. A defect discovered in 007G returns to its owning
phase under explicit remediation authorization; 007G never hides it with a verification-only patch.

## 3. Shared implementation conventions

- Domain code: `apps/topology-next/src/lib/gdss/decision-support/`.
- Repositories/services: phase-local `gdss-decision-*` modules in the official Next.js backend.
- PostgreSQL owns project scope, exact references, versions, lifecycle, immutability, uniqueness,
  completeness and human-authority history.
- Scientific content uses canonical JSON plus domain-separated SHA-256; IDs and timestamps do not
  silently enter scientific identity.
- Large manifests are content-addressed artifacts with byte/hash/relational reconciliation.
- Strict request schemas reject policy, control, actuator and authority fields.
- Every materialization is transactional and idempotent; scientific mutation and audit share the
  transaction.
- Unknown model/evidence/claim/domain/preference/risk/currentness fails closed.
- All static/runtime outputs return policy/control/physical authority `NONE`.

## 4. GDSS-007A — Decision Problem, Objectives & Constraints Foundation

### Scope

Define and seal the question before alternatives are evaluated: context, target, horizon, exact
models/evidence/claims, objectives, constraints, preference profile, risk profile and limits.

### Inputs

- project and immutable `DecisionContextSnapshot`;
- exact `SystemModelVersion`/binding IDs and hashes;
- exact GDSS-006 evidence set, capability assessment, authorized-current claim and domain scope;
- human-authored objectives, constraints, preferences and risk rules.

### Outputs

A project-scoped `DecisionProblemVersion` that is `SEALED`, exact-hash bound and immutable before
result access. Invalid/limited/conflicting GDSS-006 states are classified explicitly; V1 blocks
limited capability from later recommendation authorization.

### Entities

```text
DecisionContextSnapshot
DecisionProblemIdentity / DecisionProblemVersion / DecisionProblemEvent
DecisionProblemModelReference / DecisionProblemEvidenceReference
DecisionObjective / DecisionConstraint
DecisionPreferenceProfileIdentity / Version / Item
DecisionRiskProfileIdentity / Version / Dimension
DecisionResourceProfile
```

### Migration

Proposed `0052_gdss007a_decision_problem_foundation.py`. It creates only 007A tables, project-aware
FKs to existing exact objects, draft/freeze triggers, lifecycle/audit guards and count limits. It
does not alter GDSS-001..006 tables.

### Services and future API

`DecisionProblemService`, `DecisionPreferenceService` and `DecisionRiskProfileService` create drafts,
successors, reconcile exact evidence currentness and seal. Future routes live under
`/api/control/decision-support/projects/[projectId]/problems/...`; no route is authorized yet.

### Permissions

`AUTHOR_DECISION_PROBLEM`, `SEAL_DECISION_PROBLEM`, `AUDIT_DECISION_SUPPORT`. OAuth project
membership is mandatory. AI may draft only and cannot seal. Protocol-style self-approval is denied;
single-admin human exception requires `SOD_EXCEPTION`.

### Hashes

`decision_context_hash`, `decision_problem_hash`, `preference_profile_hash`, `risk_profile_hash` and
`resource_profile_hash`, each with its own domain prefix and canonical exact-reference arrays.

### Invariants

Primary ownership: DEC-INV-03..06, 11..13, 17..21, 24..26 and 40 foundations.

### Tests

- positive/negative strict schemas and domain-neutral objective directions;
- sealed-before-evaluation lifecycle, successor allocation and illegal transitions;
- exact GDSS-006 claim/evidence/capability/domain scope and currentness;
- limited/conflicting/failed/insufficient evidence conservative admission;
- hard constraint unknown/violation behavior;
- missing preference/uncertainty behavior;
- weight completeness and canonical sum;
- project/version substitution through service and direct SQL;
- immutable sealed rows, normalized children and append-only events;
- golden vectors, idempotency, concurrent version allocation and SoD/AI denial.

### Resource limits

At/over tests for 16 objectives, 64 constraints and the shared profile limits. Benchmarks at 8/16/17
objectives and 32/64/65 constraints record wall/RSS/rows/artifact bytes.

### Recovery

Drafts may be abandoned. A sealed mistake creates a successor and supersession event. Unknown commit
is reconciled by project, identity, predecessor and content hash. After dependent evidence exists,
rollback is forward-fix/feature-disable, not destructive downgrade.

### Non-goals

No alternatives, simulations, comparison, recommendation, policy bridge or physical authority.

### Definition of Done

Migration `0052` upgrades cleanly from `0051`; source/principal remain single head; exact evidence
admission, lifecycle, DB bypass, hash, RBAC/SoD, project/version isolation and resource tests pass;
full regression passes; implementation evidence and controlled phase Git closure are produced.

## 5. GDSS-007B — Alternative & Scenario Definition

### Scope

Define what changes, what remains fixed and which immutable model scenarios evaluate each admitted
alternative. Preserve provenance and distinguish alternative identity from scenario identity.

### Inputs

A sealed problem, exact resource profile, human/deterministic/AI-suggested alternative proposals,
exact model/input/parameter snapshots, assumptions and boundary conditions.

### Outputs

Admitted immutable `DecisionAlternativeVersion`s and `ScenarioDefinition`s with a complete roster
bound to the problem and exact model/input hashes.

### Entities

```text
DecisionAlternativeIdentity / DecisionAlternativeVersion / AlternativeEvent
DecisionVariable / FixedVariableAssertion / AlternativeProvenance
ScenarioDefinition / ScenarioAssumption / ScenarioBoundaryCondition
ScenarioUncertaintyCondition / ScenarioAdmissionEvent
```

### Migration

Proposed `0053_gdss007b_alternatives_scenarios.py`: versioned alternatives, normalized variable and
scenario children, immutable admission events, exact project/problem/model FKs, count triggers and
concurrent successor uniqueness.

### Services

`DecisionAlternativeService` validates scope/provenance and manages successors.
`DecisionScenarioDefinitionService` materializes exact scenarios and reconciles the alternative
roster. No simulation execution occurs.

### Permissions

`DEFINE_DECISION_ALTERNATIVE` and `AUDIT_DECISION_SUPPORT`. AI may submit an `AI_SUGGESTED` draft
through a human-scoped workflow but cannot admit, suppress or modify the sealed roster.

### Hashes

`alternative_hash` and `scenario_hash`; any decision-variable, fixed assertion, assumption,
boundary, model/input or method change changes identity.

### Invariants

Primary ownership: DEC-INV-02, 07, 14..16, 22, 27 and 40.

### Tests

- all four provenance modes and exact predecessor chains;
- alternative is not scenario and neither accepts actuation/policy fields;
- scope/horizon/model/input mismatch rejection;
- AI provenance without authority;
- roster completeness and unfavorable alternative preservation;
- scenario assumptions/boundaries normalized and immutable;
- counterfactual classification rejects causal wording/fields;
- project isolation, direct SQL mutation, idempotency and concurrent successor allocation;
- canonical ordering/golden hashes and one-over limits.

### Resource limits

At/over 64/65 alternatives and 128/129 scenarios per alternative; 50% gates at 32 and 64. Scenario
materialization benchmarks also prove bounded canonical artifact size and row counts.

### Recovery

Draft alternatives may be abandoned. Admitted alternatives/scenarios are corrected only by
successor problem/alternative/scenario manifests. Partial bulk materialization is transactionally
rolled back or reconciled by canonical hash.

### Non-goals

No scenario execution, optimization, causal inference, ranking, policy candidate or control path.

### Definition of Done

`0053` clean upgrade; immutable admitted roster; exact provenance/scope/hash; 64/128 boundaries;
concurrency, project/version isolation, counterfactual and authority scans; full regression and phase
evidence pass.

## 6. GDSS-007C — Scenario Evaluation & Consequence Modeling

### Scope

Execute admitted scenarios through the existing governed simulation boundary and preserve exact
consequences, failures, limitations and artifacts. It consumes GDSS-003 semantics without redefining
simulation.

### Inputs

Sealed problem, admitted alternative/scenario, exact model and input hashes, simulation method and
resource profile.

### Outputs

Immutable `ScenarioEvaluation`s and typed `ScenarioOutcome`s bound to exact simulation
attempt/result/artifact evidence. Every roster member has a terminal or explicit missing/failure
state.

### Entities

```text
ScenarioEvaluation / ScenarioEvaluationAttempt / ScenarioEvaluationEvent
ScenarioOutcome / ScenarioDiagnostic / ScenarioArtifactReference
ScenarioEvaluationCompletenessAssessment
```

### Migration

Proposed `0054_gdss007c_scenario_evaluations.py`: evaluation lifecycle/events, exact simulation refs,
outcomes, artifacts, completeness and admission-capacity enforcement. No GDSS-003 mutation.

### Services

`DecisionScenarioEvaluationService` admits bounded work, invokes the existing simulation service in
non-operational context, persists terminal evidence and recovers unknown commits by manifest/result
hash. A worker may be authorized later only for this bounded queue.

### Permissions

`RUN_SCENARIO_EVALUATION`, `AUDIT_DECISION_SUPPORT`. AI cannot escalate resource profiles or alter
terminal evidence. Existing simulation authorization does not imply recommendation authority.

### Hashes

`scenario_evaluation_hash`, `scenario_outcome_hash`, `evaluation_completeness_hash`; retry attempts
remain operational identities outside scientific result identity.

### Invariants

Primary ownership: DEC-INV-06, 14, 18, 27..29, 39 and 40.

### Tests

- exact model/input/alternative/scenario/method binding;
- deterministic replay and changed-input hash sensitivity;
- failed/limited results preserved and counted;
- artifact bytes/hash/projection reconciliation and tamper rejection;
- bounded admission before work allocation;
- no runtime/policy/actuator dependency or side effect;
- DB lifecycle/immutability, idempotency, crash/unknown-commit recovery;
- concurrent admission/terminalization and project/version isolation;
- simulated counterfactual output cannot claim causal evidence.

### Resource limits

At/over 8,192/8,193 total evaluations and inherited 128/129 per alternative. Benchmarks at 4,096 and
8,192 use bounded lightweight canonical fixtures plus representative simulation gates; record wall,
RSS, artifact bytes, DB rows and terminal failure evidence.

### Recovery

Admission and terminalization are append-only. Failed attempts remain; a retry has new attempt ID.
Artifact/DB ambiguity is reconciled by content hash and fails as `ARTIFACT_INTEGRITY_FAILURE` when
bytes differ.

### Non-goals

No criteria, comparison, recommendation, live telemetry, causal inference or physical execution.

### Definition of Done

`0054` clean upgrade; exact deterministic evaluation/artifact evidence; complete failure retention;
8,192 boundary; PostgreSQL concurrency/recovery; static authority scan; full regression and evidence.

## 7. GDSS-007D — Multi-Criteria Comparison, Trade-offs & Dominance

### Scope

Evaluate versioned criteria and constraints, assemble every admitted alternative, calculate explicit
trade-offs and Pareto/dominance relations without a universal score or forced ranking.

### Inputs

Sealed problem/profile versions, complete scenario-evaluation roster, exact outcome/uncertainty
evidence and versioned criterion definitions.

### Outputs

Immutable complete `DecisionComparisonSet`, criterion/constraint evaluations, dominance relations
and trade-off assessments, including adverse and incomparable outcomes.

### Entities

```text
DecisionCriterionIdentity / DecisionCriterionVersion
CriterionEvaluation / ConstraintEvaluation
DecisionComparisonSet / DecisionComparisonMember
DecisionDominanceRelation / TradeoffAssessment
ComparisonCompletenessAssessment
```

### Migration

Proposed `0055_gdss007d_multicriteria_comparison.py`: criterion registry, normalized results,
comparison manifests/members, pairwise relations, trade-offs, completeness and freeze triggers.

### Services

`DecisionCriterionService` seals domain-neutral deterministic methods.
`DecisionComparisonService` materializes complete vectors and relations using an explicit preference
profile. It rejects omitted alternatives, mismatched units/scope and hard-constraint violations.

### Permissions

`ASSEMBLE_DECISION_COMPARISON`, `AUDIT_DECISION_SUPPORT`. Preference editing remains 007A authority;
comparison assembly cannot change profiles or source evidence.

### Hashes

`criterion_definition_hash`, `criterion_result_hash`, `constraint_result_hash`,
`comparison_set_hash`, `dominance_relation_hash`, `tradeoff_assessment_hash`.

### Invariants

Primary ownership: DEC-INV-03..08, 22..24, 26, 29..31, 33 and 40.

### Tests

- manual/golden criterion vectors, units and uncertainty semantics;
- multi-objective vectors never collapse to a universal score;
- hard constraints reject despite favorable preferences;
- complete roster/adverse results and failed evaluations retained;
- `DOMINATES`, `DOMINATED`, `NON_DOMINATED`, `INCOMPARABLE`, `UNKNOWN` vectors;
- incomparable never ordered as inferior;
- explicit weighted/ordinal/unweighted preference behavior;
- project/version/profile substitution, direct SQL immutability and idempotency;
- concurrent comparison materialization returns one deterministic result.

### Resource limits

At/over 32/33 criteria, while reusing 64 alternatives and 64 constraints. Benchmarks cover 16/32/33
criteria and the maximum 2,016 alternative pairs (64,512 pair-criterion comparisons).

### Recovery

Incomplete source evidence prevents materialization. Same manifest returns existing comparison;
changed profile or source requires a successor. No partial comparison is exposed as complete.

### Non-goals

No stochastic optimization, recommendation authorization, preference inference or policy ranking.

### Definition of Done

`0055` clean upgrade; complete immutable comparison; all dominance states; no score/constraint
bypass; 32-criterion boundary; concurrency/DB authority/isolation; full regression and evidence.

## 8. GDSS-007E — Sensitivity, Robustness & Risk Assessment

### Scope

Assess how conclusions change across predeclared bounded variations and distinguish expected merit,
robustness and risk. Reconcile the sealed 007A risk profile without synthesizing a risk score.

### Inputs

Exact comparison set, admitted scenarios, preference/risk versions and predeclared sensitivity
dimensions/levels.

### Outputs

Immutable `SensitivityAssessment`, points, `RobustnessAssessment` and per-dimension
`DecisionRiskAssessment` with completeness, unknowns and limitations.

### Entities

```text
SensitivityAssessment / SensitivityDimension / SensitivityPoint
RobustnessAssessment / RobustnessScenarioResult
DecisionRiskAssessment / DecisionRiskDimensionResult
DecisionQualityProfile
```

### Migration

Proposed `0056_gdss007e_sensitivity_robustness_risk.py`: bounded sensitivity points, scenario-complete
robustness, independent risk dimensions and seven-axis decision-quality profile.

### Services

`DecisionSensitivityService`, `DecisionRobustnessService` and `DecisionRiskAssessmentService` use
only predeclared deterministic methods. They never adapt levels, weights or reward functions.

### Permissions

`ASSESS_DECISION_ROBUSTNESS`, `ASSESS_DECISION_RISK`, `AUDIT_DECISION_SUPPORT`. These permit
materialization, not editing sealed profiles or authorizing recommendations.

### Hashes

`sensitivity_assessment_hash`, `sensitivity_point_hash`, `robustness_assessment_hash`,
`risk_assessment_hash`, `decision_quality_profile_hash`.

### Invariants

Primary ownership: DEC-INV-05, 06, 08, 12, 13, 26, 29, 30, 32 and 40.

### Tests

- deterministic one-factor levels and insertion-order independence;
- missing level/failed scenario completeness;
- expected-best vs robust vs low-risk counterexamples;
- unknown uncertainty/risk never zero;
- changed preference/risk profile stales dependent assessments;
- seven dimensions required independently, no total/confidence score;
- hash golden vectors, project/version isolation and immutable results;
- concurrent create-or-get, bounded allocation and DB bypass.

### Resource limits

At/over 16/17 sensitivity dimensions, maximum nine levels per dimension and existing scenario limit.
Benchmarks use 8/16/17 dimensions, reporting point rows, wall, RSS and artifact bytes.

### Recovery

Incomplete assessments remain explicit and cannot feed authorization. Changed inputs create a
successor assessment. Unknown commit reconciles by exact input/result hash.

### Non-goals

No global stochastic sensitivity, Bayesian networks, learned risk, automatic optimization or
recommendation authorization.

### Definition of Done

`0056` clean upgrade; deterministic bounded sensitivity; exact robustness completeness; independent
risk/quality dimensions; 16-dimension limit; stale-trigger behavior; DB/concurrency/regression and
phase evidence pass.

## 9. GDSS-007F — Governed Recommendation & Human Decision Record

### Scope

Assemble an explainable recommendation candidate from exact current inputs, require independent
human review/authorization, preserve revocation/currentness and record the actual human decision
separately.

### Inputs

Sealed/evaluated problem, complete comparison, sensitivity/robustness/risk evidence, current exact
GDSS-006 claims and all supporting/adverse evidence. Positive authorization requires
`EVIDENCE_OF_CAPABILITY`; limited/conflicting/failed/insufficient states cannot authorize in V1.

### Outputs

Structured recommendation candidate/rationale/limitations, review, decision-support authorization
or rejection, revocation/currentness, reevaluation triggers and append-only `DecisionRecord` plus
optional outcome observation reference.

### Entities

```text
RecommendationCandidate / RecommendationAlternative
RecommendationEvidenceReference / RecommendationRationale / RecommendationLimitation
RecommendationReview / RecommendationAuthorization / RecommendationRevocation
DecisionRecord / DecisionRecordAlternative / DecisionRejectionReason / DecisionSupersession
DecisionOutcomeObservation
DecisionReevaluationTrigger / DecisionReevaluationEvent
```

### Migration

Proposed `0057_gdss007f_recommendation_human_decision.py`: immutable assembled candidates,
normalized support/adverse refs, human review/authorization/revocation, append-only decisions and
reevaluation history with exact project/hash/currentness constraints.

### Services and future API

`DecisionRecommendationService` assembles/explains and projects currentness.
`RecommendationGovernanceService` reviews/authorizes/rejects/revokes under locks and SoD.
`HumanDecisionRecordService` records actual decisions/overrides. Future routes are under
`/api/control/decision-support/projects/[projectId]/recommendations/...` and `/decisions/...`.

### Permissions

```text
AUTHOR_RECOMMENDATION
REVIEW_RECOMMENDATION
AUTHORIZE_RECOMMENDATION
REVOKE_RECOMMENDATION
RECORD_HUMAN_DECISION
AUDIT_DECISION_SUPPORT
```

Recommendation author differs from authorizer. Single-admin exception is human-only, explicit and
audited. AI is denied review-as-authority, authorization, revocation and human-decision recording
before parsing/materialization.

### Hashes

`recommendation_hash`, `recommendation_rationale_hash`, `recommendation_review_hash`,
`recommendation_authorization_hash`, `recommendation_revocation_hash`, `decision_record_hash`,
`decision_outcome_reference_hash`, `reevaluation_trigger_hash`.

### Invariants

Primary ownership: DEC-INV-01, 02, 09..16, 19..21, 33..40.

### Tests

- exact positive chain to decision-support `AUTHORIZED` with all authority outputs `NONE`;
- limited/conflicting/failed/insufficient/currentness branches fail conservatively;
- scope subset, rationale completeness and adverse alternative/evidence inclusion;
- authorization cannot widen scope or improve evidence/quality dimensions;
- author/reviewer/authorizer SoD and audited single-admin exception;
- AI with admin role denied all authoritative operations;
- expiry, model/evidence/claim/domain/profile change and new-adverse-evidence triggers;
- revocation/currentness/history, human accept/reject/defer/more-evidence/override paths;
- decision outcome does not become validation evidence;
- direct SQL immutability/append-only/uniqueness and cross-project substitution;
- concurrent authorization, revocation and decision recording; idempotency conflicts;
- explanation answers why/why-not/evidence/contradiction/assumptions/change/unknown.

### Resource limits

At/over 10,000/10,001 recommendation evidence references. Candidate alternatives remain bounded by
64. Benchmarks at 5,000/10,000/10,001 record canonical bytes, DB rows, wall and RSS.

### Recovery

Unknown authorization/revocation/decision commits are reconciled by exact hashes and idempotency
keys. Stale/revoked candidates remain historical. Corrections use successor candidates/decisions;
no update/delete. No recovery path can activate policy or control.

### Non-goals

No policy candidate creation, deployment, control session, actuation, automatic replacement or
automatic outcome-to-evidence promotion.

### Definition of Done

`0057` clean upgrade; authorized positive decision-support path and every conservative negative
state; human/AI/SoD/currentness/override boundaries; 10k refs; DB bypass/concurrency/idempotency;
static no-execution scan; full regression and phase evidence pass.

## 10. GDSS-007G — Verification, Adversarial Validation & Closure

### Scope

Verification only. Execute DEC-INV-01..40, all adversarial cases, PostgreSQL authority/concurrency,
resource benchmarks, hashing/artifact reconciliation, currentness, full regressions and static
boundaries. It adds no scientific feature.

### Inputs and outputs

Inputs are committed 007A..F outputs. Output is
`docs/architecture/GDSS-007G-CLOSURE-EVIDENCE.md`, exact test counts, migration proof and a local Git
closure candidate. Closure/publication require separate authorizations.

### Entities and migration

No new entity or feature migration expected. If verification discovers a contract failure, stop and
return it to the owning phase; no silent fix.

### Services and permissions

No production service. Verification uses read/audit access and isolated databases. No operational
permission is added.

### Hashes and invariants

Re-execute every golden vector and DEC-INV-01..40; no new hash domain.

### Tests

- complete unit/service/PostgreSQL/integration/concurrency/adversarial matrices;
- clean `0051 -> 0052 -> 0053 -> 0054 -> 0055 -> 0056 -> 0057` isolated upgrade;
- source/principal single head and no downgrade of principal;
- all resource gates at 50%, 100%, one-over;
- project/version/model/evidence/profile isolation;
- negative/adverse/incomparable/unknown history preservation;
- AI/SoD/human decision/currentness and static operational-boundary scans;
- full topology-next, Python middleware, Parametric Control Engine, typecheck and production build;
- skip audit and exact repository classification.

### Resource limits and recovery

All eight boundaries must pass. Verification-only authorization permits no production remediation.
Failure reports finding, owner, contract/actual behavior and minimal required remediation.

### Non-goals

No code, migration, feature, commit, push, tag, release, deployment or runtime activation unless a
later prompt explicitly authorizes the relevant closure step.

### Definition of Done

40/40 invariants, at least 20/20 adversarial scenarios, 8/8 resource boundaries, single head 0057,
PostgreSQL/concurrency/hash/artifact/audit/currentness/authority/full-regression gates all pass with no
critical skip or blocking drift. Final answer must remain decision support without execution
authority.

## 11. DEC-INV-01..40 executable test matrix

| Invariant | Required executable evidence | Owner |
|---|---|---|
| 01 | candidate creation versus separate human authorization | 007F |
| 02 | strict schemas/static scan reject control command | 007B/F |
| 03 | independent vectors accepted; global score rejected | 007A/D |
| 04 | favorable objectives cannot compensate hard violation | 007A/D |
| 05 | missing preference fails; explicit zero remains distinct | 007A/E |
| 06 | unknown uncertainty retained through evaluation/recommendation | 007C/E/F |
| 07 | dominated alternative remains in comparison/history | 007B/D |
| 08 | incomparable pair remains unordered and retained | 007D/E |
| 09 | AI admin authorization/review/decision attempts denied | 007F |
| 10 | revoked claim makes dependent recommendation stale | 007F |
| 11 | model substitution creates reevaluation requirement | 007A/F |
| 12 | preference successor stales comparison/recommendation | 007A/D/F |
| 13 | risk successor stales assessment/recommendation | 007A/E/F |
| 14 | simulated counterfactual causal field/claim rejected | 007B/C |
| 15 | policy-candidate fields/transfer rejected; static scan | 007B/F |
| 16 | all contracts return physical authority `NONE` | all |
| 17 | unsealed problem evaluation rejected | 007A/C |
| 18 | exact IDs/hashes accepted; substitution rejected | all |
| 19 | equal/narrower recommendation scope accepted; wider rejected | 007A/F |
| 20 | limited capability gives review-only, never authorized | 007A/F |
| 21 | conflicting/failed/insufficient evidence cannot become positive | 007A/F |
| 22 | complete roster accepted; omitted alternative rejected | 007B/D |
| 23 | unfavorable result retained; update/delete rejected | 007C/D |
| 24 | unknown hard constraint fails closed | 007A/D |
| 25 | explicit complete human profile accepted; implicit weights rejected | 007A |
| 26 | independent risk dimensions accepted; scalar truth rejected | 007A/E |
| 27 | alternative/scenario identities differ and bind exactly | 007B/C |
| 28 | evaluation exact manifest/artifact reconciliation | 007C |
| 29 | failed/limited evaluations included in completeness | 007C/D/E |
| 30 | complete comparable vector required for dominance | 007D |
| 31 | Pareto conclusion changes only through successor scope/profile | 007D |
| 32 | expected/robust/low-risk counterexamples remain distinct | 007E |
| 33 | adverse evidence/alternatives required in rationale | 007D/F |
| 34 | authorization cannot mutate scope or quality dimensions | 007F |
| 35 | SoD denial and explicit human exception audit | 007F |
| 36 | authorized recommendation and actual decision separate | 007F |
| 37 | alternative human override append-only with reason | 007F |
| 38 | trigger marks stale/review; no automatic replacement | 007F |
| 39 | outcome observation cannot enter validation evidence automatically | 007F |
| 40 | static/runtime policy/control/physical authority all `NONE` | all/007G |

## 12. Mandatory adversarial matrix

| # | Scenario | Required assertion | Owner |
|---:|---|---|---|
| 1 | AI authorizes recommendation | stable 403 before repository call | 007F |
| 2 | hard violation with highest merit | inadmissible; no authorization | 007A/D/F |
| 3 | missing preference as zero | `PREFERENCE_REQUIRED` | 007A |
| 4 | missing uncertainty as zero | `UNCERTAINTY_INSUFFICIENT` | 007C/E |
| 5 | revoked claim as basis | stale/claim-not-current | 007F |
| 6 | unfavorable alternative omitted | comparison incomplete | 007D |
| 7 | dominated alternative deleted | immutable/append-only rejection | 007D |
| 8 | cross-project alternative | project-aware FK/service rejection | 007B |
| 9 | model version substitution | exact-hash mismatch/reevaluation | 007A/C |
| 10 | preference changed after evaluation | successor + stale trigger | 007A/D/F |
| 11 | risk changed after recommendation | reevaluation required | 007E/F |
| 12 | counterfactual as causal proof | schema/semantic rejection | 007B/C |
| 13 | direct recommendation-to-policy | authority forbidden/static absence | 007F/G |
| 14 | direct recommendation-to-actuator | physical authority forbidden | 007F/G |
| 15 | unsupported model | evidence insufficient | 007A/F |
| 16 | out-of-domain used in-domain | scope/domain mismatch | 007A/F |
| 17 | rationale omits contradiction | recommendation incomplete | 007F |
| 18 | AI changes weights | AI authority forbidden | 007A |
| 19 | stale recommendation as current | stale projection blocks use | 007F |
| 20 | override history overwritten | DB append-only rejection | 007F |

## 13. Resource and performance gate matrix

| Resource | 50% | 100% accepted | One-over rejected | Owner |
|---|---:|---:|---:|---|
| alternatives/problem | 32 | 64 | 65 | 007B |
| objectives/problem | 8 | 16 | 17 | 007A |
| constraints/problem | 32 | 64 | 65 | 007A |
| criteria/comparison | 16 | 32 | 33 | 007D |
| scenarios/alternative | 64 | 128 | 129 | 007B/C |
| evaluations/problem | 4,096 | 8,192 | 8,193 | 007C |
| sensitivity dimensions | 8 | 16 | 17 | 007E |
| recommendation evidence refs | 5,000 | 10,000 | 10,001 | 007F |

Each benchmark records semantic workload, wall time, RSS, canonical artifact bytes, relational rows,
indexes touched and rejection-before-allocation evidence. These are safety bounds, not performance
SLAs. A limit change requires a new versioned resource profile and benchmark evidence.

## 14. PostgreSQL and concurrency plan

Direct SQL bypass tests cover project-aware FKs, version uniqueness, sealed/admitted/evaluated
immutability, complete rosters, hard constraints, normalized preference weights, append-only history,
authorization/revocation uniqueness and resource limits.

Real concurrency tests cover:

```text
problem successor allocation
preference/risk successor allocation
alternative successor allocation
scenario materialization and capacity reservation
evaluation admission and terminalization
comparison materialization
sensitivity/robustness materialization
recommendation assembly
recommendation authorization and revocation
human decision recording
reevaluation trigger creation/resolution
```

The result is one effective mutation or a deterministic idempotent result—never split brain,
duplicate active authority, limit race bypass or overwritten history.

## 15. Future API contract

The canonical future root is:

```text
/api/control/decision-support/projects/[projectId]/...
```

Proposed resource groups are `problems`, `preferences`, `risk-profiles`, `alternatives`, `scenarios`,
`evaluations`, `criteria`, `comparisons`, `sensitivity-assessments`, `robustness-assessments`,
`recommendations`, `reviews`, `authorizations`, `revocations`, `decisions` and
`reevaluation-triggers`. Routes accept no actor identity from bodies, use strict schemas and never
expose an execution/activation endpoint. This task creates none of them.

## 16. Security and static boundary plan

Every phase scans its source/import graph for MQTT, AMQP, DTE, Control Engine, policy activation,
actuator and physical-channel dependencies. Strict contracts reject `policyCandidate`,
`controlCommand`, `actuator`, `physicalAuthority` and equivalent escape fields. Security tests cover
weight/constraint/evidence/rationale tampering, AI elevation, cross-project contamination, stale
replay, currentness race and audit/history mutation.

```text
GDSS RECOMMENDATION != M7 POLICY CANDIDATE
```

No implementation may import M7 promotion/deployment/activation services. A future transfer is an
external consumer of an immutable recommendation, not a method on GDSS-007.

## 17. Observability, audit and retention

Operational logs record duration, counts, limit rejection, denial, contention and integrity errors
without becoming decision evidence. Audit records exact aggregate/version/hash, actor/provider,
action, reason, idempotency and result; sensitive values remain in governed artifacts.

Scientific/decision history uses superseded/revoked/invalidated states, not deletion. A future
institutional privacy process may erase protected payloads while preserving tombstone/hash/audit
evidence; it is outside V1.

## 18. Full regression and skip policy

Each phase runs its focused unit/PostgreSQL/service/integration/concurrency tests, TypeScript
typecheck, production build and affected regression. 007G runs the complete topology-next suite,
Python middleware, Parametric Control Engine and GDSS-001..006 matrices. Environment-gated tests are
explicitly enabled for final PostgreSQL/concurrency verification. No skip may cover an invariant,
adversarial case, DB authority, resource limit, AI/human boundary or no-execution boundary.

## 19. Documentation and evidence by phase

Each authorized phase creates `GDSS-007X-IMPLEMENTATION-EVIDENCE.md` with baseline, exact diff,
migration, contracts, DB enforcement, tests, performance, limitations, Git status and authority
boundary. 007G creates the consolidated closure evidence only after every current-run gate passes.

Architecture and plan remain design contracts; their proposed migration numbers become effective
only under phase authorization and must be reconciled against the then-current single Alembic head.

## 20. Total Definition of Done

GDSS-007 is implemented and verified only when all of the following are true:

- 007A..007F are separately implemented, evidenced and locally closed;
- 007G proves 40/40 invariants and at least 20/20 adversarial cases;
- 8/8 resource profiles accept the bound and reject one-over;
- clean upgrade from 0051 through the effective final single head passes;
- exact current evidence/claim/model/domain/preference/risk binding passes;
- incomplete, adverse, dominated, incomparable, failed and unknown states remain visible;
- PostgreSQL bypass/concurrency, hash/artifact/idempotency/audit/history tests pass;
- human review, SoD, AI denial, override and reevaluation behavior pass;
- no automatic recommendation replacement, policy proposal, control or actuation exists;
- complete regression, typecheck/build, skip audit and documentation reconciliation pass;
- final evidence answers `YES — DECISION SUPPORT WITHOUT EXECUTION AUTHORITY`.

## 21. Final contract status

The architecture-plan task authorized documents only. Subsequent controlled authorizations verified
GDSS-007A through GDSS-007F without authorizing GDSS-007G, commit, push, tag or release.

```text
GDSS_007A_IMPLEMENTED
GDSS_007B_IMPLEMENTED
GDSS_007C_IMPLEMENTED
GDSS_007D_IMPLEMENTED
GDSS_007E_IMPLEMENTED
GDSS_007F_IMPLEMENTED
GDSS_007G_VERIFIED

GDSS_007_IMPLEMENTED_AND_VERIFIED
```

```text
COMPLETED_GDSS_007_ARCHITECTURE_AND_IMPLEMENTATION_PLAN_CONTRACT
YES — DECISION SUPPORT WITHOUT EXECUTION AUTHORITY
```
