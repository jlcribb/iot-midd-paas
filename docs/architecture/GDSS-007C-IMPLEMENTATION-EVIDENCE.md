# GDSS-007C — Implementation Evidence

## A. Baseline

Implementation was performed in `/Users/joseluis/dev/iot-midd-paas-auth-work` on `main` at
`edf2be84004cc691ef2dbb0456e4e8b536765382`. `origin/main` resolved to the same commit and the
ahead/behind tuple was `0/0`. The initial tree contained only the authorized accumulated GDSS-007A
and GDSS-007B candidate. Alembic source and principal database were both at the single head `0053`.

## B. Scope

This increment adds only governed scenario evaluation and normalized consequence evidence. It does
not add criterion/constraint evaluation, comparison, dominance, ranking, sensitivity, robustness,
recommendation, decision, policy, control or actuation semantics.

## C. Scenario Evaluation Identity

`GDSS_SCENARIO_EVALUATION_V1` canonically binds scenario, alternative, problem, model, context,
input, method, resource profile and scientific execution manifest. Persistence identifiers,
idempotency keys, worker/host, wall clock, retry and attempt number are excluded. PostgreSQL verifies
the stored canonical bytes against `scenario_evaluation_hash` using
`midd:gdss:scenario-evaluation:v1` plus NUL byte framing.

## D. Lifecycle

The database enforces `PENDING -> RUNNING -> COMPLETED | COMPLETED_WITH_LIMITATIONS | FAILED`, plus
the authorized invalidation transitions. `FAILED -> COMPLETED` and `COMPLETED -> RUNNING` are
rejected. Terminal attempts and evaluations are immutable.

## E. Exact Binding

Service and trigger checks resolve exact project-scoped IDs and hashes for ScenarioDefinition,
DecisionAlternativeVersion, DecisionProblemVersion and SystemModelVersion, and compare the frozen
context snapshot, input hash, method version and resource profile. Draft/rejected scenarios and
silent scenario/model/context/input/method substitutions fail closed.

## F. Execution Manifest

The strict manifest declares `GDSS_SCIENTIFIC_SIMULATION_V1`, bounded inputs, required typed output
roster, ordered method parameters and `MODEL_CONDITIONAL_OUTPUT`. Unknown keys and operational,
causal, score or recommendation shortcuts are rejected.

## G. Attempt Semantics

Attempts have independent IDs, monotonic numbers, technical metadata and terminal diagnostics.
Failed attempts remain append-only. A retry requires the preceding attempt to be `FAILED` and does
not consume another scientific evaluation slot or change `scenario_evaluation_hash`.

## H. Result Artifact

Every successful terminalization requires exactly one result artifact for its attempt, canonical
UTF-8 bytes, SHA-256 content hash, bounded media type and canonical metadata. Payload size is capped
at 16 MiB.

## I. Scenario Outcomes

Outcomes normalize target, horizon, quantity, unit, numeric/categorical/unknown value, uncertainty,
limitation, exact-method provenance and output reference/hash. Numeric NaN and infinities are
rejected. Outcome canonical bytes and `midd:gdss:scenario-outcome:v1` hashes are verified by the DB.
An outcome is evidence of what the model produced; it is not a criterion evaluation.

## J. Failure Preservation

`FAILED` evaluations and their diagnostics/attempts persist. Delete and later completion are
rejected by PostgreSQL.

## K. Limitation Preservation

`COMPLETED_WITH_LIMITATIONS` requires an explicit limitation or missing output. Diagnostics,
limitations, missing outputs, uncertainty and `UNKNOWN` values remain queryable. A complete state
cannot silently omit declared output roster members.

## L. Counterfactual Boundary

The executable contract accepts only `MODEL_CONDITIONAL_OUTPUT`. Simulated counterfactual output is
never upgraded to observed causal effect, predictive capability, governed predictive claim or
recommendation.

## M. Resource Limits

The contractual count is scientific evaluations per problem. Attempts do not count. Real
PostgreSQL tests proved 4,096 and 8,192 persisted evaluations, rejection of 8,193 with
`RESOURCE_LIMIT_EXCEEDED`, and a two-client boundary race with exactly one winner.

## N. Hashing

Golden tests prove stable hashes across insertion order and idempotency changes, and distinct hashes
for scenario, model, input and method changes. PostgreSQL independently recomputes evaluation and
outcome hashes from stored canonical content.

## O. Artifact Reconciliation

Canonical bytes are reconciled to their SHA-256 hash before and during insertion. Artifact or
relational outcome mutation fails as `ARTIFACT_INTEGRITY_FAILURE`. Content-identical artifacts may
legitimately occur in different evaluations; uniqueness is scoped to evaluation/attempt identity.

## P. Persistence

Migration `0054_gdss007c_scenario_evaluation_consequences.py` creates
`gdss_scenario_evaluation`, `gdss_scenario_evaluation_attempt`,
`gdss_scenario_result_artifact`, `gdss_scenario_outcome` and
`gdss_scenario_evaluation_event`. No comparison table was introduced.

## Q. PostgreSQL Enforcement

Composite project-aware foreign keys, exact-binding triggers, advisory transaction locks, strict
lifecycle guards, canonical-hash verification, artifact digest verification, completeness checks,
append-only event sequencing and immutable evidence triggers are authoritative below the service.

## R. RBAC

Operators/admins may use `RUN_SCENARIO_EVALUATION`; only admins may use
`INVALIDATE_SCENARIO_EVALUATION`; project viewers/operators/admins retain governed audit access.

## S. AI Boundary

AI authority is hard-denied for admission, execution, result materialization, failure and
invalidation, with denial auditing when an evaluation exists. The exported boundary remains
`RecommendationAuthority = PolicyAuthority = ControlAuthority = PhysicalAuthority = NONE`, with
`aiMayFabricateOutcome = false` and `aiMayInvalidateEvaluation = false`.

## T. Audit

Append-only events cover `ADMIT`, `START`, `ATTEMPT_FAILED`, `ARTIFACT_RECONCILED`, `COMPLETE`,
`COMPLETE_WITH_LIMITATIONS`, `FAIL`, `INVALIDATE` and `AI_AUTHORITY_DENIAL`, with monotonic sequence,
actor kind, reason, transition and content hash.

## U. Idempotency

Same canonical scientific identity is create-or-get even with a different request idempotency key.
Lifecycle operations use explicit idempotency keys; same key with incompatible semantics is rejected.

## V. Concurrency

Real PostgreSQL tests cover concurrent admission, start replay, terminal conflict, artifact
materialization, retry and capacity boundary. No duplicate scientific identity, split terminal,
split artifact or 8,193rd row survived.

## W. Invariants

007C provides executable foundations for DEC-INV-14, 18, 27, 28, 29, 32, 39 and 40 while
preserving 007A/007B. Comparison- and recommendation-owned invariants are not claimed complete.

## X. Adversarial Tests

Coverage includes draft/rejected scenarios, model/method/input substitution, missing/cross-project
references, cross-evaluation attempt injection, artifact/projection tampering, failed-evaluation
deletion, limitation suppression, 8,193rd admission, double terminalization, AI fabrication,
causal overclaim, operational-payload smuggling, non-finite numerics and unknown-value coercion.

## Y. Migration

On isolated `gdss007c_migration_test`, the clean chain `0001 -> ... -> 0053 -> 0054` passed and the
required final cycle `0054 -> 0053 -> 0054` passed. Only then was the principal database upgraded
once from `0053` to `0054`; it was never downgraded. Source has one head, `0054`.

## Z. Regression

```text
GDSS-007A/B/C focused unit                 52 passed
GDSS-007A + GDSS-007B real PostgreSQL      22 passed
GDSS-007C real PostgreSQL                   8 passed
topology-next full                         598 passed, 107 skipped (705 total)
Python middleware + Control Engine         219 passed, 6 skipped
TypeScript typecheck                       PASS
Next.js production build                   PASS
```

The skipped TypeScript tests are opt-in integration suites; all three relevant GDSS-007 PostgreSQL
suites were invoked explicitly. Python integration skips require their separate external fixtures.

## AA. Static Boundary

The 007C executable graph imports no MQTT, AMQP, DTE, Control Engine, policy activation, actuator or
physical-channel dependency. Operational/recommendation/causal terms occur only in fail-closed
rejection patterns and adversarial tests.

## AB. Known Limitations

- 007C exposes domain services and persistence, not new public API routes or a worker.
- The existing simulation boundary is represented by a strict scientific execution manifest; a
  future worker integration requires separate authorization.
- Completeness is preserved for 007D but no cross-alternative comparison is performed.

## AC. Git Status

GDSS-007A, GDSS-007B and GDSS-007C remain one uncommitted local candidate. No commit, push, tag,
release or deployment was performed.

## AD. Final Status

```text
COMPLETED_GDSS_007C_SCENARIO_EVALUATION_AND_CONSEQUENCE_MODELING
```
