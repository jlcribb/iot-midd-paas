# GDSS-007 — Governed Decision Support, Scenario Evaluation & Recommendation Foundation

Status: `PROPOSED_ARCHITECTURE`

Decision: `GOVERNED_DECISION_SUPPORT_WITHOUT_EXECUTION_AUTHORITY`

Implementation status:

```text
GDSS_007A_NOT_AUTHORIZED
GDSS_007B_NOT_AUTHORIZED
GDSS_007C_NOT_AUTHORIZED
GDSS_007D_NOT_AUTHORIZED
GDSS_007E_NOT_AUTHORIZED
GDSS_007F_NOT_AUTHORIZED
GDSS_007G_NOT_AUTHORIZED
```

Policy authority: `NONE`

Control authority: `NONE`

Physical authority: `NONE`

## 1. Purpose

GDSS-007 defines how Midd-IoT may transform exact governed observations, models, simulations and
predictive evidence into comparable decision alternatives and an explainable recommendation for
human consideration. It does not decide for the organization and cannot activate policy, control or
actuation.

The admissible output is deliberately bounded:

> For decision-problem version P, evidence/claim scope E, alternatives A and declared preference,
> risk and scenario profiles S, comparison C supports recommendation candidate R with uncertainty,
> trade-offs, adverse results, limitations and review requirements L.

Contractual answer:

```text
YES — DECISION SUPPORT WITHOUT EXECUTION AUTHORITY
```

## 2. Scientific / Operational Boundary

```text
OBSERVATION
!= PREDICTION
!= PREDICTIVE EVIDENCE
!= PREDICTIVE CAPABILITY
!= PREDICTIVE CLAIM
!= DECISION OPTION
!= DECISION EVALUATION
!= RECOMMENDATION
!= HUMAN DECISION
!= POLICY AUTHORIZATION
!= CONTROL AUTHORIZATION
!= PHYSICAL ACTUATION
```

GDSS-007 implements levels 1–4 only: scenario exploration, consequence comparison, decision
support and human-governed recommendation. Levels 5–7—policy activation, control execution and
physical actuation—are absent. An analytically preferred option may remain institutionally
inadmissible. A human decision may differ from a recommendation and still be valid when reasoned and
audited.

All GDSS-007 outputs carry:

```text
PolicyAuthority = NONE
ControlAuthority = NONE
PhysicalAuthority = NONE
```

## 3. Epistemic Model

The decision-support chain is:

```text
DecisionContextSnapshot
  + exact SystemModelVersion(s)
  + current GovernedPredictiveClaim(s)
  + PredictiveCapabilityAssessment(s)
  + PredictiveEvidenceSet(s)
              |
              v
DecisionProblemVersion -> DecisionAlternativeVersion -> ScenarioDefinition
              |                                          |
              v                                          v
Objective / Constraint / Preference / Risk       ScenarioEvaluation
              |                                          |
              +--------------------+---------------------+
                                   v
                         DecisionComparisonSet
                                   |
                  Tradeoff / Sensitivity / Robustness
                                   |
                                   v
                        RecommendationCandidate
                                   |
                    Human Review / Authorization
                                   |
                                   v
                         Human DecisionRecord
```

Every arrow is an exact ID, semantic version and content hash; execution never resolves `latest`.
Evidence polarity and uncertainty propagate without favorable-only filtering. `UNKNOWN` is a state,
not zero. A simulated counterfactual is conditional model output, never observed causal proof.

V1 evidence admission is conservative:

- `EVIDENCE_OF_CAPABILITY` plus an `AUTHORIZED_CURRENT` claim may support recommendation assembly
  when scope, domain and horizon match exactly.
- `EVIDENCE_OF_LIMITED_CAPABILITY` may be displayed in exploration/comparison only, explicitly
  labeled and forced to `DECISION_SUPPORT_REVIEW_REQUIRED`; it cannot support an `AUTHORIZED`
  recommendation in V1.
- `NOT_EVALUATED`, `INSUFFICIENT_EVIDENCE`, `CONFLICTING_EVIDENCE`, `EVIDENCE_OF_FAILURE`, stale,
  revoked or invalidated claims cannot be positive recommendation foundations.

## 4. Decision Problem

`DecisionProblemIdentity` supplies a project-scoped logical key. `DecisionProblemVersion` binds:

- one immutable `DecisionContextSnapshot`;
- target variables and decision horizon;
- exact model/binding versions and hashes;
- exact GDSS-006 evidence sets, capability assessments and current claims;
- exact validity-domain assessments;
- objective, constraint, preference, risk and resource profiles;
- allowed alternative provenance and scenario methods.

Lifecycle:

```text
DRAFT -> REVIEW_REQUIRED -> SEALED -> EVALUATING -> EVALUATED
DRAFT | REVIEW_REQUIRED | SEALED -> INVALIDATED
SEALED | EVALUATED -> SUPERSEDED
```

Only `DRAFT` content is mutable. `SEALED` freezes scientific inputs before scenario results are
available. `EVALUATING` and later are immutable and append events. A correction creates a successor.

## 5. Objectives

`DecisionObjective` is a normalized child of a problem version. It declares key, direction,
quantity/unit, target, horizon, evaluation criterion version, aspiration/acceptance bounds,
required status and ordinal display order. Domain-neutral directions are `MINIMIZE`, `MAXIMIZE`,
`TARGET_RANGE` and `MAINTAIN_WITHIN`.

Multiple objectives remain independent. No implicit normalization, weighting or domain-specific
hydroponic objective is permitted. Missing required objective evidence makes the alternative
incomplete, not neutral.

## 6. Constraints

`DecisionConstraint` types are:

```text
HARD_CONSTRAINT
SOFT_CONSTRAINT
ADVISORY_CONSTRAINT
```

Each version declares scope, typed predicate/method, unit, threshold, required inputs, missing-data
semantics, provenance and explanation. A hard-constraint violation makes an alternative
`INADMISSIBLE`; no objective, preference or favorable score may compensate for it. Unknown required
hard-constraint input also fails closed. Soft/advisory violations remain visible dimensions and
cannot be silently discarded.

## 7. Preferences

`DecisionPreferenceProfileIdentity/Version` records human-governed priority relations or optional
weights over exact objective/criterion versions. Profiles are explicit, versioned, scope-bound,
reviewed and immutable after sealing.

V1 supports `UNWEIGHTED_PARETO`, `ORDINAL_PRIORITY` and `EXPLICIT_NORMALIZED_WEIGHTS`. Weights must
be complete, finite, non-negative and sum canonically to one when that mode is selected. They rank
only among admissible alternatives; they cannot erase constraints or uncertainty. Missing preference
is `PREFERENCE_REQUIRED`, never weight zero. AI may draft but may not set, change or approve weights.

## 8. Risk

`DecisionRiskProfileIdentity/Version` contains independent typed dimensions. Each
`DecisionRiskDimension` declares source, severity class, likelihood knowledge state, reversibility,
recoverability, uncertainty, acceptance rule and scope. No universal `risk_score` exists.

Risk states include `ACCEPTABLE`, `CONDITIONALLY_ACCEPTABLE`, `UNACCEPTABLE` and `UNKNOWN` per
dimension. A required `UNACCEPTABLE` dimension rejects recommendation authorization. Required
`UNKNOWN` yields review or incomparability according to the sealed profile; it is never zero risk.

## 9. Alternatives

`DecisionAlternativeIdentity/Version` specifies exactly what changes and remains fixed, decision
variables, parameter deltas, structural assumptions, horizon, applicable constraints, provenance,
author and predecessor. Provenance is one of:

```text
HUMAN_PROPOSED
DETERMINISTICALLY_GENERATED
AI_SUGGESTED
DERIVED_FROM_PRIOR_ALTERNATIVE
```

AI provenance adds no authority. Only draft alternatives are editable; admission freezes them.
Alternatives are project/problem scoped and cannot embed actuator topics, policy activation intents,
control commands or physical endpoints. An alternative is a scientific option, not an instruction.

## 10. Scenarios

An alternative may map to multiple immutable `ScenarioDefinition`s. A scenario binds exact
alternative, model version, input/context snapshot, initial conditions, parameter set, perturbations,
boundary conditions, assumptions, uncertainty condition, method and resource profile.

`ScenarioAssumption` and `ScenarioBoundaryCondition` are normalized typed children. Free text may
explain but cannot define a scientific input. Scenario identity changes for any semantic change.
Counterfactual labels must say `SIMULATED_COUNTERFACTUAL`; they cannot claim observed causality.

## 11. Evaluations

`ScenarioEvaluation` records one admitted scenario execution and exact simulation attempt/result,
method version, output artifact/hash, terminal state and diagnostics. `ScenarioOutcome` provides
typed target/horizon/criterion-ready projections without replacing the original simulation artifact.

States are `PENDING`, `RUNNING`, `COMPLETED`, `COMPLETED_WITH_LIMITATIONS`, `FAILED` and
`INVALIDATED`. Failed/limited evaluations remain members of completeness checks. Retries have
distinct attempts but a stable scientific manifest. No wall-clock metadata enters the content hash.

## 12. Criteria

`DecisionCriterionIdentity/Version` declares key, direction, unit/dimension, deterministic V1
evaluation method, required inputs, missing-data semantics, uncertainty semantics and applicability.
Arbitrary executable expressions are excluded unless they use the already-governed GDSS-002 safe
expression contract under a separately declared method version.

`CriterionEvaluation` binds exact alternative, scenario/outcome set, criterion version, value,
units, uncertainty, evidence references and computation method. An invalid or unfavorable result is
retained. `ConstraintEvaluation` is separate so hard admissibility can never be collapsed into merit.

## 13. Multi-objective Comparison

`DecisionComparisonSet` is an immutable complete manifest over every admitted in-scope alternative,
criterion and constraint result, scenario outcome, uncertainty conclusion, risk result, trade-off,
dominance relation and limitation. Completeness reconciles the sealed problem/alternative roster;
omitting an unfavorable alternative yields `ADVERSE_ALTERNATIVE_OMITTED`.

The system may expose criterion vectors and a preference-specific ordering, but never a universal
score. Comparisons under a different preference/risk profile are successor comparison sets, not
rewrites.

## 14. Dominance

Pairwise dominance is computed only across admissible alternatives with comparable, complete
criterion vectors under the same problem, scope, units and uncertainty rules. Results are:

```text
DOMINATES
DOMINATED
NON_DOMINATED
INCOMPARABLE
UNKNOWN
```

`INCOMPARABLE` is not inferior. Unknown or materially overlapping uncertainty prevents unsupported
dominance. Dominated alternatives remain in the comparison and historical record. Pareto-front
membership is derived, scope-specific and not recommendation authority.

## 15. Sensitivity

V1 supports bounded deterministic one-factor-at-a-time sensitivity over predeclared preference,
assumption or parameter dimensions and finite declared levels. `SensitivityAssessment` binds the
base comparison and immutable `SensitivityPoint`s, recording whether admissibility, dominance or
preferred-set membership changes.

No global stochastic sensitivity, posterior inference or adaptive sampling is included. Missing
points make the assessment incomplete rather than stable.

## 16. Robustness

`RobustnessAssessment` evaluates an alternative across the exact admitted scenario set and records
constraint satisfaction frequency/counts, outcome envelope, worst declared case, missing/failure
states and stability of dominance/preference conclusions. It produces independent dimensions, not
a scalar score.

```text
BEST_EXPECTED != ROBUST_ACROSS_SCENARIOS != LOW_RISK
```

A favorable expected outcome with critical unknowns may remain `INCOMPARABLE` or
`REVIEW_REQUIRED`.

## 17. Recommendation

`RecommendationCandidate` is a structured, immutable-on-assembly decision-support statement. It
binds problem, preferred alternative set, scope, comparison, sensitivity/robustness/risk results,
supporting and contradicting evidence, limitations, uncertainty, trade-offs, validity period,
review requirements and provenance (`HUMAN_AUTHORED`, `DETERMINISTICALLY_DERIVED`, `AI_ASSISTED`).

Candidate lifecycle:

```text
DRAFT -> EVIDENCE_ASSEMBLED -> REVIEW_REQUIRED -> AUTHORIZED | REJECTED
AUTHORIZED -> SUPERSEDED | REVOKED
```

`EXPIRED_REVIEW_REQUIRED`, `STALE_REVIEW_REQUIRED` and `INVALIDATED` are currentness projections or
append-only events, never destructive rewrites. `AUTHORIZED` means a human approved the candidate
for presentation/use as decision support only.

Recommendation quality remains seven dimensions:

```text
EVIDENCE_ADEQUACY
DOMAIN_FIT
UNCERTAINTY_ACCEPTABILITY
ROBUSTNESS
CONSTRAINT_SATISFACTION
TRADEOFF_CLARITY
RISK_ACCEPTABILITY
```

No `recommendation_confidence` or aggregate quality score exists.

## 18. Human Review

`RecommendationReview` records reviewer, decision (`APPROVE_FOR_AUTHORIZATION`, `REJECT`,
`REQUEST_MORE_EVIDENCE`, `REQUEST_REVISION`), rationale, exact candidate hash and disclosed adverse
evidence. Authorization requires all mandatory reviews and an exact current-input reconciliation.

The author cannot authorize their own recommendation. A human single-admin exception requires an
explicit `SOD_EXCEPTION` reason and audit event. AI cannot review as authority, authorize, revoke or
use the exception.

## 19. Human Decision

`DecisionRecord` is separate from recommendation authorization. It records one of `ACCEPT`,
`REJECT`, `DEFER`, `REQUEST_MORE_EVIDENCE` or `SELECT_DIFFERENT_ALTERNATIVE`, actor, reason, exact
recommendation version/hash, selected alternative(s), exceptions and DB-assigned timestamp.

Human override is explicit and audited, not automatically an error. Decision records and rejection
reasons are append-only; correction uses supersession. A later `DecisionOutcomeObservation` may
reference the decision and exact governed observation, but:

```text
DECISION OUTCOME != VALIDATION EVIDENCE
```

Promotion requires a future governed GDSS-006 evidence process.

## 20. Re-evaluation

Append-only triggers are:

```text
MODEL_CHANGED              EVIDENCE_CHANGED
CLAIM_REVOKED              CLAIM_EXPIRED
DOMAIN_CHANGED             OBJECTIVE_CHANGED
CONSTRAINT_CHANGED         PREFERENCE_CHANGED
RISK_PROFILE_CHANGED       SCENARIO_CHANGED
NEW_ADVERSE_EVIDENCE       OBSERVED_OUTCOME_DIVERGED
```

Each trigger identifies affected objects and projects `REVIEW_REQUIRED`, `REEVALUATION_REQUIRED`,
`STALE` or `INVALIDATED`. It never replaces a recommendation automatically, activates policy or
executes control. Resolution is a human-governed append-only event linked to a successor evaluation
or an explicit no-change rationale.

## 21. AI Governance

AI may suggest alternatives, summarize outcomes, identify trade-offs, draft rationale, highlight
uncertainty and identify missing evidence. All AI output carries provenance.

AI may not change preferences/weights, suppress alternatives or adverse evidence, seal problems,
authorize recommendations, make institutional decisions, record a human decision, authorize policy,
control or actuation, or use SoD exceptions. `auth_provider=ai` is denied at service and route
boundaries before persistence regardless of project membership or nominal role.

## 22. Persistence

PostgreSQL is authoritative for project scope, exact references, lifecycle, uniqueness,
immutability, completeness and human authority. Critical relations are normalized; JSONB is limited
to bounded typed value payloads, display metadata and diagnostics with semantic versions.

| Table | Principal keys / relations | Enforcement / indexes |
|---|---|---|
| `gdss_decision_problem_identity` | id, project, logical key | unique project/key; immutable |
| `gdss_decision_problem_version` | identity/version/predecessor, context, horizon, preference/risk/resource refs, hash | unique identity/version; draft-only content; state/hash indexes |
| `gdss_decision_problem_model_ref` | problem, exact model/binding ID+hash | project-aware FK; unique ref |
| `gdss_decision_problem_evidence_ref` | problem, evidence/capability/claim IDs+hashes | exact/current reconciliation; polarity retained |
| `gdss_decision_objective` | problem, ordinal, criterion, target/direction/unit | max-count trigger; immutable after seal |
| `gdss_decision_constraint` | problem, ordinal, type, method/unit/threshold | hard/soft/advisory checks; immutable after seal |
| `gdss_decision_preference_identity/version` | project key; version/predecessor/mode/hash | reviewed/sealed lifecycle; unique version/hash |
| `gdss_decision_preference_item` | profile, objective/criterion, priority/weight | complete references; normalized-weight trigger |
| `gdss_decision_risk_identity/version` | project key; version/predecessor/hash | sealed lifecycle; project-aware |
| `gdss_decision_risk_dimension` | profile, key, source/severity/likelihood/reversibility/recoverability/rule | independent dimensions; count bound |
| `gdss_decision_alternative_identity/version` | problem key; version/predecessor/provenance/hash | exact problem; draft/admitted freeze; successor allocation lock |
| `gdss_decision_variable` | alternative, variable ref, fixed/change mode, typed value/unit | unique semantic variable; no actuator/policy fields |
| `gdss_scenario_definition` | problem, alternative, model/input/method/resource hashes | immutable admitted manifest; count bounds |
| `gdss_scenario_assumption` | scenario, key/type/value/reference | normalized key; bounded typed payload |
| `gdss_scenario_boundary_condition` | scenario, variable/time/value/unit | exact unit/time semantics |
| `gdss_scenario_evaluation` | scenario, attempt/result/artifact IDs+hashes, state, manifest hash | idempotency/hash unique; lifecycle and terminal freeze |
| `gdss_scenario_outcome` | evaluation, target/horizon/quantity/unit/value/hash | immutable; exact result provenance |
| `gdss_decision_criterion_identity/version` | project key; version/method/direction/unit/hash | unique version; sealed freeze |
| `gdss_criterion_evaluation` | alternative, criterion, outcome set, value/unit/uncertainty/hash | unique exact inputs; immutable |
| `gdss_constraint_evaluation` | alternative, constraint, result/evidence/hash | hard violation admission guard |
| `gdss_decision_comparison_set` | problem, preference/risk refs, manifest/hash/state | complete roster reconciliation; immutable |
| `gdss_decision_comparison_member` | comparison, alternative, admissibility | all admitted alternatives required |
| `gdss_decision_dominance_relation` | comparison, left/right, relation, rationale hash | unique ordered pair; no deletion |
| `gdss_tradeoff_assessment` | comparison, alternative pair/set, criterion deltas/hash | immutable; adverse dimensions retained |
| `gdss_sensitivity_assessment/point` | comparison, dimension/level, derived relation/hash | bounded dimensions/levels; completeness |
| `gdss_robustness_assessment` | comparison, alternative, scenario manifest, multidimensional result/hash | exact scenario completeness; immutable |
| `gdss_recommendation_candidate` | problem/comparison/exact refs, state/provenance/validity/hash | no authority fields; immutable after assembly |
| `gdss_recommendation_alternative` | candidate, alternative, disposition/ordinal | preferred and considered sets normalized |
| `gdss_recommendation_evidence_ref` | candidate, evidence/claim/result polarity/hash | supporting and adverse completeness |
| `gdss_recommendation_limitation` | candidate, code/severity/scope | append-only candidate content |
| `gdss_recommendation_review` | candidate/reviewer/decision/reason/hash | human-only; unique idempotency |
| `gdss_recommendation_authorization` | candidate, authorizer, exact hashes, scope, SoD reason | one effective authorization; row/advisory lock |
| `gdss_recommendation_revocation` | candidate/authorization, actor/reason/trigger/hash | append-only; uniqueness/idempotency |
| `gdss_decision_record` | candidate/authorization, actor/action/reason/hash | human-only append; exact current recommendation |
| `gdss_decision_record_alternative` | decision, selected/rejected alternative, reason | preserves override and rejection history |
| `gdss_decision_outcome_observation` | decision, governed observation ref/hash | no automatic evidence promotion |
| `gdss_decision_reevaluation_trigger/event` | affected object/type/state/reason/resolution | append-only sequence; currentness indexes |
| `gdss_decision_audit_event` | aggregate/type/sequence/actor/action/reason/hashes | append-only; unique sequence/idempotency |

Composite project-aware FKs or constraint triggers prevent cross-project substitution. Lifecycle and
audit mutation share a transaction. Scientific history is never physically deleted through the API.

## 23. Hashing

All scientific identities use RFC-8785-equivalent canonical JSON conventions already used by GDSS,
UTF-8, explicit binary64/time/unit semantics, sorted semantic sets and domain-separated SHA-256:

```text
midd:gdss:decision-problem:v1
midd:gdss:decision-alternative:v1
midd:gdss:decision-scenario:v1
midd:gdss:scenario-evaluation:v1
midd:gdss:decision-criterion:v1
midd:gdss:criterion-result:v1
midd:gdss:decision-comparison-set:v1
midd:gdss:sensitivity-assessment:v1
midd:gdss:robustness-assessment:v1
midd:gdss:recommendation-candidate:v1
midd:gdss:human-decision-record:v1
```

`CONTENT_HASH != PERSISTENCE_ID`. Actor, DB timestamp and retry attempt are excluded unless they are
part of the declared semantics. Canonical artifacts reconcile bytes, SHA-256 and relational
projections. Same semantics produce the same hash; any semantic change produces a different hash.

## 24. Lifecycle

Draft content is mutable only before sealing/admission. Problem, alternative and scenario evaluation
manifests freeze before result use. Comparison sets, assembled recommendations, reviews,
authorizations, revocations and decision records are immutable or append-only. Correction always
uses a successor with predecessor reference.

Scientific materializations use create-or-get by canonical input hash. Human events use an explicit
idempotency key. Same key/same content returns the existing row; same key/different content fails
closed. Concurrent successor allocation and authorization use transaction locks and uniqueness.

## 25. RBAC / SoD

Capabilities are:

```text
AUTHOR_DECISION_PROBLEM
SEAL_DECISION_PROBLEM
DEFINE_DECISION_ALTERNATIVE
RUN_SCENARIO_EVALUATION
ASSEMBLE_DECISION_COMPARISON
AUTHOR_RECOMMENDATION
REVIEW_RECOMMENDATION
AUTHORIZE_RECOMMENDATION
REVOKE_RECOMMENDATION
RECORD_HUMAN_DECISION
AUDIT_DECISION_SUPPORT
```

They extend project-scoped OAuth RBAC and do not reuse `edit_policies` as final authority. Operators
may author/evaluate; admins seal/authorize/revoke/record decisions; viewers may audit according to
existing membership. Exact role mapping is fixed in 007A/F tests. Recommendation author and
authorizer differ; the only human exception is explicit, reasoned and audited single-admin SoD.

## 26. Errors

Stable error codes include:

```text
DECISION_PROBLEM_NOT_SEALED          DECISION_PROBLEM_FROZEN
DECISION_INPUT_NOT_CURRENT           ALTERNATIVE_SCOPE_MISMATCH
ALTERNATIVE_NOT_ADMITTED             HARD_CONSTRAINT_VIOLATED
PREFERENCE_REQUIRED                  PREFERENCE_PROFILE_MISMATCH
UNCERTAINTY_INSUFFICIENT             RISK_UNACCEPTABLE
SCENARIO_NOT_ADMISSIBLE              SCENARIO_EVALUATION_INCOMPLETE
COMPARISON_SET_INCOMPLETE            ADVERSE_ALTERNATIVE_OMITTED
CRITERION_SCOPE_MISMATCH             DOMINANCE_NOT_DETERMINABLE
RECOMMENDATION_SCOPE_EXCEEDS_EVIDENCE
RECOMMENDATION_EVIDENCE_INSUFFICIENT
RECOMMENDATION_AUTHORIZATION_FORBIDDEN
STALE_RECOMMENDATION                 CLAIM_NOT_CURRENT
MODEL_REEVALUATION_REQUIRED          SOD_VIOLATION
AI_AUTHORITY_FORBIDDEN               DECISION_AUTHORITY_FORBIDDEN
POLICY_AUTHORITY_FORBIDDEN           PHYSICAL_AUTHORITY_FORBIDDEN
IDEMPOTENCY_CONFLICT                 ARTIFACT_INTEGRITY_FAILURE
RESOURCE_LIMIT_EXCEEDED              CROSS_PROJECT_DECISION_REFERENCE
```

Validation failures are 400/409/422 as appropriate; authorization is 403; absence is 404. Database
constraint names map to the same stable codes without leaking SQL details.

## 27. Security

Threats and controls:

| Threat | Required control |
|---|---|
| recommendation manipulation | exact hashes, immutable candidate and human review |
| weight tampering | sealed preference versions and relational weights |
| constraint suppression | complete sealed roster; hard-constraint DB guard |
| evidence/alternative omission | completeness reconciliation and adverse polarity refs |
| AI authority elevation | provider-aware deny before persistence; DB actor provenance |
| cross-project contamination | composite FKs plus service scope |
| stale recommendation replay | exact currentness reconciliation and triggers |
| rationale tampering | structured rationale hash and immutable assembly |
| history overwrite | append-only review/auth/revocation/decision events |
| model/version substitution | exact IDs and hashes, never `latest` |
| causal overclaim | mandatory simulated-counterfactual classification |
| actuator escape | strict schemas, static scans, no operational dependency |

Future APIs use `/api/control/decision-support/projects/[projectId]/...`, OAuth project scope and
strict request schemas. No endpoint is authorized by this architecture task.

## 28. Resource Limits

V1 uses identity-bearing `GDSS_DECISION_LIMITS_V1`:

| Boundary | Limit | Rationale and bounded work |
|---|---:|---|
| alternatives per problem | 64 | permits broad exploration; pairwise dominance is 2,016 pairs |
| objectives per problem | 16 | 1,024 alternative-objective cells at maximum |
| constraints per problem | 64 | 4,096 explicit constraint evaluations |
| criteria per comparison | 32 | at most 64,512 pair-criterion dominance comparisons |
| scenarios per alternative | 128 | supports uncertainty grids without unbounded fan-out |
| scenario evaluations per problem | 8,192 | exact product of 64×128; admission reserves capacity |
| sensitivity dimensions | 16 | bounded one-factor analysis; maximum 9 declared levels each |
| recommendation evidence refs | 10,000 | aligns with GDSS-006 evidence manifest bound |

Limits fail before bulk allocation and are enforced in schemas/services plus PostgreSQL where races
matter. Each implementing phase must benchmark 50%, 100% and one-over. Diagnostics record wall time,
RSS, artifact bytes, relational row counts and rejection latency. Required one-over cases are
65/17/65/33/129/8,193/17/10,001. No empirical SLA is claimed before implementation evidence exists.

## 29. Invariants

| ID | Invariant |
|---|---|
| DEC-INV-01 | Recommendation is not authorization. |
| DEC-INV-02 | Recommendation is not a control command. |
| DEC-INV-03 | Multi-objective evaluation is not a universal score. |
| DEC-INV-04 | A hard constraint cannot be traded away. |
| DEC-INV-05 | Unknown preference is not zero weight. |
| DEC-INV-06 | Unknown uncertainty is not zero. |
| DEC-INV-07 | A dominated alternative remains traceable. |
| DEC-INV-08 | Incomparable is not inferior. |
| DEC-INV-09 | AI cannot authorize a recommendation or decision. |
| DEC-INV-10 | Claim revocation invalidates current recommendation use. |
| DEC-INV-11 | Model-version change requires reevaluation. |
| DEC-INV-12 | Preference change requires reevaluation. |
| DEC-INV-13 | Risk-profile change requires reevaluation. |
| DEC-INV-14 | Simulated counterfactual is not causal proof. |
| DEC-INV-15 | Recommendation is not an M7 policy candidate. |
| DEC-INV-16 | Recommendation confers no physical authority. |
| DEC-INV-17 | A sealed decision problem precedes result-bearing evaluation. |
| DEC-INV-18 | Every decision input is exact-version and content-hash bound. |
| DEC-INV-19 | Decision scope cannot exceed current claim/evidence scope. |
| DEC-INV-20 | Limited capability cannot authorize a V1 recommendation. |
| DEC-INV-21 | Conflicting/failed/insufficient evidence cannot be silently made positive. |
| DEC-INV-22 | All admitted alternatives appear in the comparison set. |
| DEC-INV-23 | Unfavorable criteria and outcomes remain in history. |
| DEC-INV-24 | Hard-constraint unknown fails closed. |
| DEC-INV-25 | Preference weights are explicit, complete, versioned and human-governed. |
| DEC-INV-26 | Risk dimensions remain independent; no universal risk score exists. |
| DEC-INV-27 | Alternative and simulation scenario are distinct exact identities. |
| DEC-INV-28 | Evaluation binds exact model, input, scenario, method and output artifact. |
| DEC-INV-29 | Failed/limited scenario evaluations count toward completeness. |
| DEC-INV-30 | Dominance requires comparable complete criterion vectors. |
| DEC-INV-31 | Pareto membership is scope/preference specific, not authority. |
| DEC-INV-32 | Best expected, robust and low risk are distinct conclusions. |
| DEC-INV-33 | Recommendation rationale discloses adverse evidence and alternatives. |
| DEC-INV-34 | Authorization cannot widen scope or improve decision-quality dimensions. |
| DEC-INV-35 | Recommendation author and authorizer are separated or explicitly excepted. |
| DEC-INV-36 | Human decision is distinct from recommendation authorization. |
| DEC-INV-37 | Human override remains reasoned, append-only and traceable. |
| DEC-INV-38 | Reevaluation triggers never replace recommendations automatically. |
| DEC-INV-39 | Decision outcomes are not validation evidence without governed admission. |
| DEC-INV-40 | Every GDSS-007 artifact has policy/control/physical authority `NONE`. |

## 30. Adversarial Cases

| # | Attack | Expected fail-closed result |
|---:|---|---|
| 1 | AI authorizes recommendation | `AI_AUTHORITY_FORBIDDEN` |
| 2 | hard constraint violated but weighted result is highest | alternative `INADMISSIBLE` |
| 3 | missing preference treated as zero | `PREFERENCE_REQUIRED` |
| 4 | missing uncertainty treated as zero | `UNCERTAINTY_INSUFFICIENT` |
| 5 | revoked claim remains basis | `CLAIM_NOT_CURRENT`; recommendation stale |
| 6 | unfavorable alternative omitted | `ADVERSE_ALTERNATIVE_OMITTED` |
| 7 | dominated alternative deleted | immutable/append-only failure |
| 8 | cross-project alternative injected | `CROSS_PROJECT_DECISION_REFERENCE` |
| 9 | model version silently substituted | `MODEL_REEVALUATION_REQUIRED` |
| 10 | preference changed after evaluation | successor required; current stale |
| 11 | risk profile changed after recommendation | `REEVALUATION_REQUIRED` |
| 12 | counterfactual presented as causal proof | causal-claim schema rejection |
| 13 | recommendation promoted directly to policy | `POLICY_AUTHORITY_FORBIDDEN` |
| 14 | recommendation sent directly to actuator | `PHYSICAL_AUTHORITY_FORBIDDEN` |
| 15 | unsupported model/capability used | `RECOMMENDATION_EVIDENCE_INSUFFICIENT` |
| 16 | out-of-domain evidence used as in-domain | scope/domain mismatch |
| 17 | rationale omits contradictory evidence | comparison/recommendation incomplete |
| 18 | AI changes weights | `AI_AUTHORITY_FORBIDDEN` |
| 19 | stale recommendation shown as current | `STALE_RECOMMENDATION` |
| 20 | human override history overwritten | append-only trigger rejection |

Additional tests cover idempotency conflicts, concurrent authorization/revocation, scenario artifact
tampering, exact-hash substitution, one-over resource limits and suppressed failed evaluations.

## 31. Non-goals

V1 excludes policy proposal transfer, policy execution, control authorization, actuation, RL, online
policy optimization, Bayesian decision networks, causal inference, multi-agent negotiation,
automatic preference/reward learning, global stochastic sensitivity, continuous autonomous
reevaluation, real-time autonomous optimization and UI implementation.

GDSS-007 does not alter migrations `0044..0051` or redefine `PredictiveEvidenceSet`,
`PredictiveCapabilityAssessment` or `GovernedPredictiveClaim`. Future transitions
`Recommendation -> Policy Candidate -> Control Authorization -> Actuation` require separate phases
and authorizations.

## 32. Phase Decomposition

| Phase | Scope | Proposed migration | Output |
|---|---|---:|---|
| GDSS-007A | problem, context, objectives, constraints, preferences, risk | 0052 | sealed decision problem |
| GDSS-007B | alternatives and scenario definitions | 0053 | admitted immutable alternatives/scenarios |
| GDSS-007C | scenario evaluation and consequences | 0054 | exact immutable evaluation evidence |
| GDSS-007D | criteria, comparison, trade-offs and dominance | 0055 | complete comparison set |
| GDSS-007E | sensitivity, robustness and risk assessment | 0056 | multidimensional stability evidence |
| GDSS-007F | recommendation, review, authorization and human decision | 0057 | governed decision-support record |
| GDSS-007G | verification, adversarial validation and closure | none expected | closure evidence |

Migrations are proposals only. No migration, code, API or runtime change is authorized here.

## 33. Closure Criteria

GDSS-007 can close only when:

- DEC-INV-01..40 have executable positive/negative evidence;
- all 20 adversarial cases fail closed;
- exact GDSS-006 currentness/scope is enforced without modifying GDSS-006;
- all eight resource boundaries pass at 50%, 100% and reject one-over;
- PostgreSQL proves project/version isolation, immutability, append-only history and concurrency;
- hashes/artifacts are deterministic and reconciled;
- adverse alternatives/evidence and unknowns are preserved;
- AI, SoD, human review and human decision boundaries pass;
- static scans show no MQTT, AMQP, DTE, Control Engine, policy activation, actuator or physical path;
- full GDSS-001..006 regression, TypeScript, build and clean migration 0051→0057 pass;
- policy, control and physical authority remain `NONE`.

Final constitutional result:

```text
RECOMMENDATION != AUTHORIZATION
ANALYTICAL BEST OPTION != ORGANIZATIONAL DECISION
ORGANIZATIONAL DECISION != CONTROL AUTHORIZATION
SIMULATED COUNTERFACTUAL != OBSERVED CAUSAL EFFECT
```

```text
COMPLETED_GDSS_007_ARCHITECTURE_AND_IMPLEMENTATION_PLAN_CONTRACT
YES — DECISION SUPPORT WITHOUT EXECUTION AUTHORITY
```
