# GDSS-007B — Implementation Evidence

Prompt: `MIDD-GDSS-P030-R1`
Scope: Alternative & Scenario Definition
Date: 2026-10-22

## A. Baseline

Preflight passed on `/Users/joseluis/dev/iot-midd-paas-auth-work`, branch `main`. `HEAD` and
`origin/main` were `edf2be84004cc691ef2dbb0456e4e8b536765382`, ahead/behind `0/0`. The dirty
working tree contained only the authorized GDSS-007A candidate. Alembic source and principal were
single-head `0052`.

## B. Scope

Implemented only GDSS-007B definitions. No scenario execution, result, outcome, criterion
evaluation, comparison, ranking, sensitivity, robustness, recommendation, decision record, policy,
control or actuation capability was introduced. GDSS-007C..G remain unauthorized.

## C. Alternative Identity

`gdss_decision_alternative_identity` is immutable and unique by project, exact problem version and
canonical key. Project-aware foreign keys prevent substitution.

## D. Alternative Versioning

Versions bind an exact identity, monotonic version/predecessor, exact sealed problem hash and context,
changes, fixed assertions, normalized variables, deltas, structural assumptions, horizon,
constraints, scope, provenance, author and hash. Corrections allocate successors.

## E. Alternative Lifecycle

Implemented `DRAFT -> REVIEW_REQUIRED -> ADMITTED`, rejection from draft/review and admitted
supersession. Only drafts are mutable; admitted content and normalized children are frozen.

## F. Decision Variables

Strict normalized modes are `FIXED`, `SET_TO`, `DELTA`, `RANGE` and `STRUCTURAL_CHANGE`, with typed
value, unit, baseline/change semantics, scope and ordinal. Unknown and opaque properties fail closed.

## G. Provenance

The four authorized provenance classes are preserved verbatim. An AI actor may only create
`AI_SUGGESTED` alternatives; it cannot silently become `HUMAN_PROPOSED`.

## H. Alternative Admission

Admission requires a `SEALED` exact problem, compatible project/scope/horizon, known variables and
constraint references, and provenance present in the problem allowlist. Admission is human-only.

## I. Scenario Identity

Each scenario is a separately hashed, persistence-identified scientific manifest. Alternative ID and
scenario ID are structurally distinct and tested as such.

## J. Scenario Definition

Scenarios bind exact problem, admitted alternative, model version/hash, context/input snapshot,
initial conditions, parameter set, perturbations, uncertainty, method and resource profile. No
execution state or output entity exists.

## K. Assumptions

Assumptions are normalized by key, type, typed value, optional exact reference, scope, provenance
and ordinal. Explanatory text has no scientific authority.

## L. Boundary Conditions

Boundary conditions normalize variable, time window, typed value, unit, scope, method semantics and
ordinal. Admitted children are immutable.

## M. Counterfactual Semantics

Only `BASELINE_CONDITION` and `SIMULATED_COUNTERFACTUAL` are accepted. `CAUSAL_EFFECT` and
`OBSERVED_CAUSAL_RESULT` are rejected by both contract and PostgreSQL manifest guards.

## N. Exact Model/Input Binding

No `latest` lookup exists. PostgreSQL and services reconcile exact model/version/hash, exact problem
context, alternative hash, method allowlist and nested scope on insert and draft update.

## O. Resource Limits

`GDSS_DECISION_LIMITS_V1` enforces 64 alternatives/problem, 128 scenarios/alternative and the
global logical ceiling `64 * 128 = 8192`. Tests prove 32/64 accepted, 65 rejected; 64/128 accepted,
129 rejected; concurrent one-over attempts persist exactly one final slot.

## P. Hashing

SHA-256 canonical JSON uses `midd:gdss:decision-alternative:v1` and
`midd:gdss:decision-scenario:v1`. Persistence IDs, predecessor, retry/idempotency and row order are
excluded; exact scientific references remain included. Golden order/mutation vectors pass.

## Q. Persistence

Migration `0053_gdss007b_alternative_scenario_definition.py` creates alternative identity/version,
decision variable, scenario definition, assumption, boundary condition and append-only definition
event tables. No evaluation table exists. Migration `0052` and GDSS-006 tables were not edited.

## R. PostgreSQL Enforcement

Project/problem/model FKs, sealed-problem admission, allowed provenance/methods, exact hashes,
monotonic successors, lifecycle, draft-only mutation, operational-payload rejection, counterfactual
classification, 64/128/8192 bounds and append-only history are database-enforced.

## S. RBAC

Dedicated `DEFINE_DECISION_ALTERNATIVE`, `ADMIT_DECISION_ALTERNATIVE` and existing
`AUDIT_DECISION_SUPPORT` permissions are project-scoped. `edit_policies` is not used.

## T. AI Boundary

AI may draft/suggest but cannot submit authoritative review, admit alternatives/scenarios or use a
SoD exception. Denials are auditable. AI + admin does not become human scientific authority.

## U. SoD

Author and admitter differ. A reasoned, human-only single-admin exception is represented and audited;
PostgreSQL rejects same-actor admission without it.

## V. Audit

Create, update draft, submit, admit, reject, supersede, SoD exception and AI-denial events are
sequenced, hashed and append-only. Direct SQL update/delete fails.

## W. Idempotency

Scientific materialization uses canonical hashes plus transactional/advisory locks. Lifecycle uses
explicit keys. Same key with different semantics fails as `IDEMPOTENCY_CONFLICT`.

## X. Concurrency

Real PostgreSQL tests cover one effective alternative successor, alternative admission, scenario
materialization, scenario admission and resource-limit races. No duplicate version, double admission,
65th alternative or 129th scenario survives.

## Y. Invariants

007B foundations are executable for DEC-INV-07, 08 where definition-level applicable, 14, 17, 18,
19, 22/23 foundations, 27 and 40. Evaluation/comparison-dependent completion is not claimed.

## Z. Adversarial Tests

Coverage includes cross-project/missing-model injection, cross-problem binding, causal overclaim,
AI admission, one-over resources, admitted-content mutation, direct draft binding substitution and
all seven operational-payload smuggling keys.

## AA. Migration

Clean chain through `0052 -> 0053` passed. Isolated `0053 -> 0052 -> 0053` passed after final trigger
hardening. Principal upgraded once `0052 -> 0053` and was never downgraded.

## AB. Regression

```text
GDSS-007A + GDSS-007B focused unit       29 passed
GDSS-007B real PostgreSQL                 9 passed
Topology full                           575 passed, 99 skipped (674 total)
Python middleware + Control Engine      219 passed, 6 skipped
TypeScript typecheck                    PASS
Next.js production build                PASS
```

The skipped TypeScript tests are opt-in integration suites; the GDSS-007B PostgreSQL suite was run
explicitly and passed.

## AC. Static Boundary

The 007B executable graph imports no MQTT, AMQP, DTE, Control Engine, policy activation, actuator or
physical-channel dependency. Operational terms occur only in strict rejection guards and adversarial
tests, never as executable output fields.

## AD. Known Limitations

- 007B exposes domain services and persistence, not public API routes.
- Scenarios are definitions only; execution and outcomes remain 007C.
- The 8,192 ceiling is additionally implied by the concurrently enforced 64×128 bounds and has an
  explicit global trigger guard.
- No recommendation or downstream authority is created by admission.

## AE. Git Status

GDSS-007A and GDSS-007B remain one uncommitted local candidate. No commit, push, tag, release or
deployment was performed.

## AF. Final Status

```text
GDSS_007A_IMPLEMENTED
GDSS_007B_IMPLEMENTED
GDSS_007C_NOT_AUTHORIZED
GDSS_007D_NOT_AUTHORIZED
GDSS_007E_NOT_AUTHORIZED
GDSS_007F_NOT_AUTHORIZED
GDSS_007G_NOT_AUTHORIZED

RecommendationAuthority = NONE
PolicyAuthority = NONE
ControlAuthority = NONE
PhysicalAuthority = NONE

COMPLETED_GDSS_007B_ALTERNATIVE_AND_SCENARIO_DEFINITION
```
