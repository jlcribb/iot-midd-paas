# GDSS-007A — Implementation Evidence

Prompt: `MIDD-GDSS-P029-R1`
Scope: Decision Problem, Objectives, Constraints, Preferences & Risk Foundation
Date: 2026-10-19

## A. Baseline

Preflight passed on `/Users/joseluis/dev/iot-midd-paas-auth-work`, branch `main`, with clean working
tree, `HEAD == origin/main == edf2be84004cc691ef2dbb0456e4e8b536765382`, ahead/behind `0/0`,
Alembic source/principal `0051 (head)` and one head. The versioned architecture and plan were the
normative sources.

## B. Scope

Implemented only GDSS-007A. No alternative, scenario evaluation, comparison, sensitivity,
robustness, recommendation, human-decision, policy, control or physical-actuation entity or service
was introduced. GDSS-007B..G remain not authorized.

## C. Entities

Implemented project-scoped immutable identities and governed versions for decision problems,
preference profiles and risk profiles; exact context snapshots; normalized objectives, constraints,
preference items, risk dimensions, model/binding references, evidence/capability/claim/domain
references and append-only audit events.

## D. Lifecycle

The full state vocabulary is represented. Phase-local operations expose `DRAFT -> REVIEW_REQUIRED
-> SEALED` and invalidation only. Drafts may be updated; scientific children and content freeze from
review onward. Corrections can allocate a monotonic successor. PostgreSQL rejects illegal jumps.

## E. GDSS-006 Binding

Problem creation reconciles exact model version/hash, dynamic binding version/hash, evidence-set
ID/hash, capability-assessment ID/hash, predictive-claim ID/hash, validity-domain ID/hash, target and
horizon. No `latest` lookup exists. The service enforces:

```text
DecisionProblemScope <= ClaimScope <= CapabilityScope <= EvidenceScope
```

Only `AUTHORIZED_CURRENT` claims are accepted. Revoked, superseded, expired, stale, unresolved or
otherwise non-current claims fail with `CLAIM_NOT_CURRENT`.

## F. Objectives

Objectives are normalized and independent, with direction, quantity/unit, target, horizon, exact
criterion reference/hash, aspiration/acceptance bounds, required flag and ordinal. No global utility
or decision score exists.

## G. Constraints

Hard, soft and advisory constraints retain typed method, scope, unit, threshold, inputs, missing
semantics, provenance and explanation. A hard violation is inadmissible. Unknown required hard input
must use `FAIL_CLOSED` and is inadmissible.

## H. Preferences

Implemented unweighted Pareto, ordinal priority and explicit normalized weights. Explicit weights
must be complete, finite, non-negative and sum canonically to one. Explicit zero remains distinct
from a missing preference. Profiles are versioned, reviewed, sealed, scope-bound and audited.

## I. Risk

Risk remains multidimensional across source, severity, likelihood knowledge, reversibility,
recoverability, uncertainty, acceptance rule and scope. States are independent: acceptable,
conditionally acceptable, unacceptable and unknown. Unknown knowledge cannot be stored as acceptable
and must select review-required or fail-closed handling. No scalar risk score exists.

## J. Resource Limits

`GDSS_DECISION_LIMITS_V1` is enforced before materialization in Zod and transactionally in
PostgreSQL with an advisory lock:

| Resource | Half | Limit | One-over |
|---|---:|---:|---:|
| objectives/problem | 8 PASS | 16 PASS | 17 rejected |
| constraints/problem | 32 PASS | 64 PASS | 65 rejected |

No additional numeric 007A limit was invented.

## K. Hashing

SHA-256 over canonical JSON uses `midd:gdss:decision-problem:v1`, plus separately namespaced
preference/risk hashes. Own persistence identity, predecessor and idempotency metadata are excluded;
exact scientific references remain included. Golden tests prove insertion-order invariance and
single-semantic-mutation sensitivity. `CONTENT_HASH != PERSISTENCE_ID`.

## L. Persistence

Migration `0052_gdss007a_decision_problem_foundation.py` creates the 13 authorized relational
tables, indexes, functions and triggers. Migration `0044..0051` and every GDSS-006 entity remain
unchanged.

## M. PostgreSQL Enforcement

PostgreSQL enforces project-aware foreign keys, version uniqueness, monotonic predecessors, lifecycle
legality, post-review freeze, exact model/binding/evidence/capability/claim/domain hashes, 16/64
limits, preference completeness and weight normalization, unknown-risk structure, current claim at
problem sealing and append-only audit. One-over, direct mutation and illegal transition tests pass.

## N. RBAC

Dedicated permissions are implemented independently of `edit_policies`:

```text
AUTHOR_DECISION_PROBLEM
SEAL_DECISION_PROBLEM
AUDIT_DECISION_SUPPORT
```

Project membership and project-specific role are required.

## O. SoD

Author and sealer must differ. A single human administrator may use a reasoned `SOD_EXCEPTION`,
recorded as its own immutable event. Unreasoned self-sealing fails with `SOD_VIOLATION`.

## P. AI Boundary

AI may draft structures. AI review, sealing and SoD exception are hard-denied even for an admin and
denials can be audited. The exported boundary is:

```text
PolicyAuthority = NONE
ControlAuthority = NONE
PhysicalAuthority = NONE
```

## Q. Audit

Create, draft update, review submission, seal, invalidation, SoD exception and AI denial have stable
event forms, sequence and content hash. Direct SQL `UPDATE` and `DELETE` both fail.

## R. Idempotency

Scientific drafts use canonical content hashes and transactional locks for create-or-get behavior.
Human transitions use explicit idempotency keys. Replaying the same event resolves deterministically;
same key with different entity/content returns `IDEMPOTENCY_CONFLICT`. PostgreSQL errors are mapped to
stable domain errors rather than leaked.

## S. Concurrency

Real PostgreSQL tests prove one effective decision-problem successor, preference successor, risk
successor and problem seal under concurrent calls. Identity row locks, advisory locks, unique
constraints and replay reconciliation prevent duplicate versions, split-brain lifecycle and multiple
effective seals.

## T. Migration

On isolated `gdss007a_migration_test`:

```text
clean chain -> 0051 -> 0052       PASS
0052 -> 0051 -> 0052              PASS
final isolated current            0052 (head)
```

This clean chain includes `0043 -> ... -> 0051 -> 0052`. Only after the cycle passed, the principal
database was upgraded once from `0051` to `0052`; it was never downgraded.

## U. Invariants

007A foundations are executable for DEC-INV-03, 04, 05, 06, 09, 10, 11, 12, 13, 17, 18, 19, 20,
21, 24, 25, 26 and 40. Invariants requiring alternatives or later phases are not claimed complete.

## V. Tests

Focused results:

```text
GDSS-007A unit                         11 passed
GDSS-007A real PostgreSQL              13 passed
TypeScript typecheck                   PASS
```

The PostgreSQL fixture establishes exact pre-existing GDSS-006 rows in the disposable isolated DB;
all GDSS-007A triggers and constraints are enabled during the assertions.

## W. Regression

```text
topology-next full                     557 passed, 90 skipped (647 total)
topology-next production build         PASS
Python middleware + Control Engine     219 passed, 6 skipped
```

Skipped tests are pre-existing opt-in integration suites. GDSS-007A's real PostgreSQL suite was run
explicitly with `GDSS_DB_TEST=1` and passed.

## X. Static Boundary

The GDSS-007A executable import graph contains no MQTT, AMQP, DTE, Control Engine, policy activation,
actuator or physical-channel dependency. Forbidden scalar/action shortcuts are absent from runtime
code. Static-search matches for `decision_score` and `risk_score` occur only in negative unit-test
assertions; `ControlActor`/`control-access` imports are existing authentication/RBAC types, not control
execution.

## Y. Known Limitations

- 007A intentionally exposes services and persistence rather than public API routes.
- `EVALUATING`, `EVALUATED` and `SUPERSEDED` are represented by the constitutional lifecycle but are
  not phase-local service operations before 007B+.
- No recommendation eligibility result creates a recommendation or grants execution authority.
- Opt-in legacy integration suites remain outside the default full-suite invocation; this phase's
  PostgreSQL integration was executed separately and is not skipped in the reported focused gate.

## Z. Git Status

The implementation remains an uncommitted local candidate as required. No commit, push, tag, release
or deployment was performed by P029-R1.

## AA. Final Status

```text
GDSS_007A_IMPLEMENTED
GDSS_007B_NOT_AUTHORIZED
GDSS_007C_NOT_AUTHORIZED
GDSS_007D_NOT_AUTHORIZED
GDSS_007E_NOT_AUTHORIZED
GDSS_007F_NOT_AUTHORIZED
GDSS_007G_NOT_AUTHORIZED

COMPLETED_GDSS_007A_DECISION_PROBLEM_OBJECTIVES_CONSTRAINTS_PREFERENCES_AND_RISK_FOUNDATION

PolicyAuthority = NONE
ControlAuthority = NONE
PhysicalAuthority = NONE
```
