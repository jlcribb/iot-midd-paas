# GDSS-007D Implementation Evidence

Prompt: `MIDD-GDSS-P032-R1`
Date: 2026-10-22
Checkout: `/Users/joseluis/dev/iot-midd-paas-auth-work`

## A. Baseline

Preflight found branch `main`, `HEAD == origin/main == edf2be84004cc691ef2dbb0456e4e8b536765382`, ahead/behind `0/0`, and a dirty tree containing only the authorized accumulated GDSS-007A–C candidate. Source and principal database were both at the single head `0054`.

## B. Scope

Implemented only criterion identity/version, criterion and constraint evaluation, complete comparison membership, pairwise dominance, Pareto membership, and trade-off evidence. No 007E/F/G sensitivity, robustness, recommendation, authorization, decision, policy, control, or actuation capability was added.

## C. Criterion Identity

`gdss_decision_criterion_identity` is project-scoped, canonically keyed, idempotent, and immutable.

## D. Criterion Versioning

`gdss_decision_criterion_version` records direction, exact quantity/unit, target/horizon, deterministic method/version, required inputs, missing/uncertainty semantics, applicability, canonical content, and SHA-256 definition hash. Allocation is serialized per identity; successors are append-only.

## E. Criterion Evaluation

`DecisionCriterionService.evaluateCriterion` binds exact problem, admitted alternative, sealed criterion version, scenario evaluation, outcome set, method version, units, computation inputs, evidence hashes, uncertainty and limitation states. Outcome and interpretation remain separate records.

## F. Constraint Evaluation

Constraint results are separate immutable materializations with exact constraint, evaluation/outcome evidence, result, admissibility, reason, canonical content and hash.

## G. Hard Constraint Semantics

`VIOLATED`, `UNKNOWN`, or `INVALID` hard-constraint evidence never becomes admissible. The isolated PostgreSQL integration retained a numerically adverse alternative as `INADMISSIBLE`; no objective value or preference compensated for it.

## H. Missing/Unknown Semantics

Missing inputs map only to the criterion's explicit `UNKNOWN`, `INCOMPLETE`, or `NOT_APPLICABLE` policy. Unknown values are never zero. Partial or unknown uncertainty makes dominance `UNKNOWN`; failed/invalidated evaluation evidence becomes `INVALID`.

## I. Comparison Set

The immutable manifest binds the exact problem/hash, preference version/hash, risk version/hash, admitted alternative IDs, criterion version IDs, criterion-result IDs, constraint-result IDs, uncertainty conclusion, canonical content and comparison hash.

## J. Completeness

Service and PostgreSQL finalization reconcile members against every admitted alternative and every member's criterion cells against the exact criterion set. Omission fails as `ADVERSE_ALTERNATIVE_OMITTED` or `COMPARISON_SET_INCOMPLETE`.

## K. Membership

Every member preserves alternative, admissibility, vector completeness, constraint status, uncertainty status, reason and scoped Pareto membership. Inadmissible and dominated alternatives remain stored.

## L. Multi-Objective Semantics

No universal score or winner is computed. Contracts and DB guards reject universal-score/recommendation shortcuts. Pairwise vectors preserve criterion-specific direction and range semantics.

## M. Preference Binding

Comparison requires the exact sealed profile already bound to the problem. Explicit-weight mode accepts only complete pre-existing normalized weights; the implementation neither infers nor edits them.

## N. Dominance

Relations are one of `DOMINATES`, `DOMINATED`, `NON_DOMINATED`, `INCOMPARABLE`, or `UNKNOWN`, unique per ordered pair and limited to admissible complete vectors with characterized uncertainty.

## O. Incomparability

Mixed gains/losses produce `INCOMPARABLE`, not inferiority. Missing, partial or unknown comparable evidence produces `UNKNOWN`, never inferred dominance.

## P. Pareto

Pareto membership is derived only as a comparison-scoped analytical property. It creates no recommendation, winner, review, authorization or operational authority.

## Q. Tradeoffs

Each ordered pair persists criterion deltas, advantages, disadvantages, unknown dimensions, constraint differences, uncertainty differences, limitations, canonical content and hash.

## R. Adverse Evidence/Alternatives

All admitted alternatives remain members. All disadvantages and unknowns remain present in trade-offs. Integration explicitly rejects favorable-only roster omission.

## S. Resource Limits

Contracts accept 16 and 32 criteria and reject 33 before persistence. PostgreSQL independently rejects the 33rd criterion. Comparison input is capped at 64 alternatives, 2,048 criterion cells and the bounded 2,016 unique pairs.

## T. Hashing

Namespaces are:

- `midd:gdss:decision-criterion:v1`
- `midd:gdss:criterion-result:v1`
- `midd:gdss:constraint-result:v1`
- `midd:gdss:decision-comparison:v1`
- `midd:gdss:dominance-relation:v1`
- `midd:gdss:tradeoff-assessment:v1`

Canonical member sets are sorted. Golden tests prove insertion-order independence and semantic-change sensitivity. PostgreSQL recomputes hashes from canonical content before accepting scientific rows.

## U. Persistence

Migration `0055_gdss007d_comparison_tradeoff_dominance.py` adds the eight required aggregate tables plus normalized comparison criteria/cells/constraint references and append-only comparison events. It descends only from `0054`.

## V. PostgreSQL Enforcement

Triggers enforce project/problem/version/outcome binding, sealed/current inputs, finite numeric values, hard-constraint fail-closed behavior, exact criterion membership, one cell per member/criterion, completeness, resource limit, relation uniqueness, canonical hashes and post-materialization immutability.

## W. RBAC

Permissions are separated into criterion authoring, criterion sealing and comparison assembly. Operator/admin roles may author/assemble as declared; sealing is admin-only.

## X. AI Boundary

AI is hard-denied from sealing criteria, materializing scientific results, assembling comparisons, deriving authoritative relations, altering weights or suppressing dimensions. Exported boundary remains:

```text
RecommendationAuthority = NONE
PolicyAuthority = NONE
ControlAuthority = NONE
PhysicalAuthority = NONE
```

## Y. Audit

Append-only events cover criterion creation/sealing, criterion and constraint materialization, comparison assembly, dominance derivation, trade-off materialization, invalidation semantics, and AI denial. Sequence and event idempotency are DB-guarded.

## Z. Idempotency

Scientific materializations use canonical-hash create-or-get. Human actions use explicit keys. Same key/different semantics fails. Advisory transaction locks serialize criterion results, constraint results and comparison assembly; the integration test exposed and verified the result-materialization race fix.

## AA. Concurrency

Real PostgreSQL tests passed concurrent criterion-result materialization and concurrent comparison assembly with one effective row, no partial set and no duplicate pair evidence. Earlier A–C concurrency suites were rerun sequentially to avoid their fixture-level global-trigger interference.

## AB. Invariants

The 40-check 007D matrix passed:

| # | Contract | Result |
|---:|---|---|
| 1 | Project-scoped criterion identity | PASS |
| 2 | Criterion successor versioning | PASS |
| 3 | Sealed criterion immutability | PASS |
| 4 | Outcome is not criterion result | PASS |
| 5 | Exact criterion version binding | PASS |
| 6 | Exact scenario evaluation binding | PASS |
| 7 | Exact outcome binding | PASS |
| 8 | Exact method binding | PASS |
| 9 | Exact unit compatibility | PASS |
| 10 | Non-finite numeric rejection | PASS |
| 11 | Missing is not zero | PASS |
| 12 | Unknown uncertainty preserved | PASS |
| 13 | Partial uncertainty prevents dominance | PASS |
| 14 | Constraint result separate from criterion | PASS |
| 15 | Hard violation is inadmissible | PASS |
| 16 | Unknown hard input fails closed | PASS |
| 17 | Soft/advisory state remains visible | PASS |
| 18 | Exact problem/hash binding | PASS |
| 19 | Exact preference/hash binding | PASS |
| 20 | Exact risk/hash binding | PASS |
| 21 | All admitted alternatives represented | PASS |
| 22 | Adverse omission rejected | PASS |
| 23 | Failed/limited evidence not hidden | PASS |
| 24 | Member status/reason retained | PASS |
| 25 | No universal score | PASS |
| 26 | Weights not inferred | PASS |
| 27 | Dominates/dominated orientation | PASS |
| 28 | Equal vectors non-dominated | PASS |
| 29 | Mixed vectors incomparable | PASS |
| 30 | Unknown dominance preserved | PASS |
| 31 | Pareto is not recommendation | PASS |
| 32 | Dominated alternative retained | PASS |
| 33 | Adverse trade-off dimensions retained | PASS |
| 34 | 16 criteria accepted | PASS |
| 35 | 32 criteria accepted | PASS |
| 36 | 33 criteria rejected | PASS |
| 37 | Canonical hash determinism | PASS |
| 38 | PostgreSQL immutability | PASS |
| 39 | Idempotent concurrency | PASS |
| 40 | No recommendation/control authority | PASS |

This covers DEC-INV-03/04/05/06/07/08/22/23/24/25/26/29/30/31/33-foundation/40 while preserving 007A–C.

## AC. Adversarial Tests

Tests cover hard-constraint non-compensability, missing/partial uncertainty, adverse omission, dominated retention, incomparable preservation, exact set mismatch, version substitution, failed/limited evidence states, 33rd criterion rejection, AI sealing/assembly denial, universal shortcut rejection, cross-binding rejection and immutable-history mutation.

## AD. Migration

Isolated database:

```text
0054 -> 0055 PASS
0055 -> 0054 PASS
0054 -> 0055 PASS
current = 0055 (head)
```

The full clean chain to `0054` had already passed before the final cycles. Principal database was verified at `0054`, upgraded exactly once to `0055`, and was not downgraded. Final source head and principal current are both the single head `0055`.

## AE. Performance

Diagnostic maximum-bound run:

```text
alternatives: 64
criteria: 32
unique pairs: 2016
pair criterion cells: 64512
wall time: 133.814 ms (full-suite concurrent run; focused run 19.409 ms)
RSS delta: 7,962,624 bytes (focused run 8,568,832 bytes)
serialized tradeoff bytes: 8,745,111
```

This is diagnostic evidence, not an SLA.

## AF. Regression

```text
GDSS-007D unit: 36 passed
GDSS-007D PostgreSQL integration: 5 passed
GDSS-007A PostgreSQL integration: 13 passed
GDSS-007B PostgreSQL integration: 9 passed
GDSS-007C PostgreSQL integration: 8 passed
topology-next full: 634 passed, 112 skipped (environment-gated integrations)
Python middleware: 179 passed, 6 skipped
Parametric Control Engine: 40 passed
TypeScript: PASS
Next.js production build: PASS
```

The focused PostgreSQL authority/concurrency tests were explicitly enabled; their results are not among the skipped full-suite tests.

## AG. Static Boundary

Static import scans found no MQTT, AMQP, DTE, Control Engine, policy activation, actuator or physical-channel dependency in 007D implementation files. No sensitivity, robustness, recommendation, authorization or decision-record type/table/service was introduced.

## AH. Known Limitations

V1 deterministic criterion methods operate on finite numeric scenario outcomes. Categorical outcomes are preserved upstream but become an explicit `INVALID` criterion result until a governed categorical method/version is authorized. Preference-specific weighted/ordinal presentation is not produced; the exact profile remains bound without creating a universal rank. Staleness/reevaluation workflow remains reserved for later phases and never overwrites a comparison.

## AI. Git Status

The working tree intentionally remains dirty with the accumulated authorized GDSS-007A–D candidate. `git diff --check` passes. No commit, push, tag or release was performed.

## AJ. Final Status

```text
GDSS_007A_IMPLEMENTED
GDSS_007B_IMPLEMENTED
GDSS_007C_IMPLEMENTED
GDSS_007D_IMPLEMENTED
GDSS_007E_NOT_AUTHORIZED
GDSS_007F_NOT_AUTHORIZED
GDSS_007G_NOT_AUTHORIZED

COMPLETED_GDSS_007D_MULTI_CRITERIA_COMPARISON_TRADEOFFS_AND_DOMINANCE
```

GDSS-007D demonstrates governed comparison of multiple admitted alternatives without hiding constraints, uncertainty, failures, adverse alternatives or trade-offs, and without answering which option should be recommended.

## AK. P035-F01 Deterministic Dominance Verification Remediation

During `MIDD-GDSS-P035-R1`, finding `P035-F01` identified a test-harness defect: the PostgreSQL integration asserted only `relation === "DOMINATES"`, even though canonical pair ordering may validly persist the scientifically equivalent inverse orientation as `relation === "DOMINATED"`.

`MIDD-GDSS-P035-R2` changed only `tests/integration/gdss-multicriteria-comparison.persistence.integration.test.ts`. The production dominance algorithm, contracts, repositories, services, schema, migration, hashes, authority and resource limits were unchanged.

The remediated harness now verifies alternative identity, left/right orientation and relation jointly:

```text
left = dominant, right = dominated, relation = DOMINATES  -> PASS
left = dominated, right = dominant, relation = DOMINATED  -> PASS
left = dominant, right = dominated, relation = DOMINATED  -> FAIL
```

Executable revalidation on 2026-10-23:

```text
GDSS-007D unit: 36/36 PASS
GDSS-007D PostgreSQL repeated isolated processes: 10/10 runs, 6/6 tests each PASS
GDSS-007A..F focused unit: 163/163 PASS
GDSS-007A..F PostgreSQL on clean isolated 0057 DB: 46/46 PASS
topology-next full: 709 passed, 123 environment-gated skipped
Python middleware: 179 passed, 6 skipped
Parametric Control Engine: 40/40 PASS
TypeScript: PASS
Next.js production build: PASS
```

The clean isolated database was migrated through the full chain to the single head `0057`. Principal source/database revision remained `0057`; no `0058` was created and the principal database was not downgraded.

DEC-INV-07, DEC-INV-08, DEC-INV-30 and DEC-INV-31 remain satisfied: dominated alternatives remain traceable, incomparable remains distinct, dominance requires complete comparable vectors, and Pareto analysis confers no authority.

One non-product warning was observed: running the accumulated principal test database after ten deliberate 007D fixture repetitions can cause 007E/007F tests that select the globally “latest” fixture to bind unrelated historical fixtures. The authoritative clean isolated A–F regression passed 46/46; no production code or additional harness outside the authorized P035-F01 assertion was changed.

```text
P035-F01 = REMEDIATED
GDSS_007G_NOT_AUTHORIZED
COMPLETED_GDSS_007D_DETERMINISTIC_DOMINANCE_VERIFICATION_REMEDIATION_WITH_WARNINGS
```


### P035-F01 historical classification and remediation status (P036-R2)

```text
ID: P035-F01
Classification: NONDETERMINISTIC_POSTGRESQL_VERIFICATION_ASSERTION
Severity: BLOCKING
Owning phase: GDSS-007D
Status: REMEDIATED
Root cause: orientation-sensitive PostgreSQL test assertion
Remediation: orientation-independent semantic dominance assertion
Revalidation: 10/10 isolated executions PASS
              60/60 tests PASS

A DOMINATES B
=
B DOMINATED BY A

DOMAIN SEMANTICS UNCHANGED
DOMINANCE ALGORITHM UNCHANGED
DATABASE SCHEMA UNCHANGED
```

The severity records the original blocking finding; remediation does not erase that history.
The semantic equivalence above applies when storage canonicalizes the pair orientation.
The revalidation counts preserve the P035 evidence already captured; P036-R2 changes no harness
and does not claim a new execution of those tests.
