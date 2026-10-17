# MIDD-IOT — GDSS-006B Implementation Evidence

**Authorization:** `MIDD-GDSS-P019-R1`; corrective remediation `MIDD-GDSS-P024-R2`

**Status:** `COMPLETED_GDSS_006B_LINEAGE_DEPTH_CONTRACT_REMEDIATION`

**Original baseline:** `main@dee81328f4a73b525f8d7236d8ee799044b9cabc`, uncommitted GDSS-006A, Alembic `0044 (head)`

**Remediation baseline:** same Git commit with legitimate uncommitted GDSS-006A..F material,
source and principal database at `0049`.

**Effective Alembic revision after remediation:** `0050 (head)`; one head

## Implemented boundary

GDSS-006B implements persistent evidence-unit identity, explicit and cycle-protected lineage,
versioned partition plans, exact immutable dataset snapshots, governed single-use holdouts,
append-only access/exposure evidence, deterministic independence impact and fail-closed overlap,
leakage and duplicate checks.

It does not implement validation execution, prediction records or commitments, observation pairing,
metrics, baselines, executable uncertainty, evidence sets, capability assessments, predictive claims
or physical authority.

## Files and services

- Contracts, canonical hashing, lifecycle, authorization, diagnostics and independence analysis:
  `apps/topology-next/src/lib/gdss/validation/partition-*.ts`.
- Transactional persistence: `gdss-evidence-custody.repository.ts`.
- Governed operations: `gdss-evidence-custody.service.ts`.
- Ten API routes under `/api/control/validation/projects/:projectId/` for units, lineage, partitions,
  snapshots, holdouts and access.
- PostgreSQL and adversarial tests plus this implementation evidence.

## Migration 0045

Migration `0045_gdss006b_evidence_partition_holdout_custody.py` creates thirteen normalized tables,
ten guard/ledger functions, nineteen triggers and supporting indexes. It enforces project scope,
version uniqueness, exact bindings, immutable evidence/snapshots/published plans/holdouts,
append-only histories, lifecycle legality, idempotency and single-use custody.

The final migration was verified on the disposable database `gdss006b_verify_20261007`:

```text
0044 -> 0045 -> 0044 -> 0045  PASS
```

No destructive downgrade was applied to the primary local database.

## Corrective migration 0050

Closure verification discovered that the original GDSS-006B implementation used a traversal cap
of 64 while the Implementation Plan contract was 16. `MIDD-GDSS-P024-R2` remediates that mismatch
forward-only; historical migration `0045` was not edited. Migration
`0050_gdss006b_lineage_depth_contract_remediation.py` replaces only the lineage guard function,
retains project isolation and cycle detection, serializes graph extensions per project, and rejects
an insertion whose combined ancestor/new-edge/descendant path would exceed 16 edges.

Before principal upgrade, the persisted-data assessment reported zero lineage rows, zero paths and
zero projects over depth 16, and maximum depth zero. No evidence was deleted, normalized or
rewritten. Isolated `0049 -> 0050 -> 0049 -> 0050` and clean
`0043 -> 0044 -> 0045 -> 0046 -> 0047 -> 0048 -> 0049 -> 0050` both passed. Only after those
checks, the principal database was upgraded `0049 -> 0050`; it was not downgraded.

## Evidence units and lineage

V1 granularities are single observation, time window, dependent group, derived feature and
aggregated unit. Source identity/version/hash, semantic group, measurement interval, event time,
availability time and ingestion time remain distinct.

Lineage relations are `DERIVED_FROM`, `AGGREGATED_FROM`, `TRANSFORMED_FROM`, `IMPUTED_FROM`,
`GROUPED_WITH` and `TEMPORALLY_DEPENDENT_ON`. Derivative cycles are rejected in both service and DB.
The original implementation limit was 64. After the P024-R2 remediation, the canonical and effective
limit is 16 in TypeScript and PostgreSQL: the current/root unit is depth 0, the first edge is depth 1,
the sixteenth edge is accepted, and any required seventeenth edge raises
`LINEAGE_DEPTH_LIMIT_EXCEEDED`. Exceeding the bound means independence is not provable and fails
closed; it is never interpreted as no overlap. Each published plan includes its exact canonical
lineage references, so changing lineage changes the plan hash.

## Partition governance and snapshots

Roles are calibration, validation, holdout, benchmark, external validation and challenge. Lifecycle:

```text
DRAFT -> REVIEW_REQUIRED -> APPROVED -> PUBLISHED
REVIEW_REQUIRED -> DRAFT
PUBLISHED -> SUPERSEDED | INVALIDATED
```

Only drafts are mutable. Publication rejects direct/transitive overlap, dependent-group splitting,
future availability beyond cutoff, exact content/source/declared semantic duplicates and unknown
lineage or availability. Snapshots canonicalize membership order and become immutable immediately
after atomic materialization.

## Holdout custody and exposure

Lifecycle:

```text
SEALED -> OPENED_FOR_EVALUATION -> CONSUMED -> RETIRED
SEALED | OPENED_FOR_EVALUATION | CONSUMED -> INVALIDATED
```

`CONSUMED -> SEALED` is impossible. Resealing never restores independence. Opening binds exact
published partition, snapshot, sealed protocol and model version/hashes. `HoldoutAccessEvent`,
`HoldoutExposureLedger` and `HoldoutEvaluationReference` are separate append-only records.

Exposure effects are `NO_EPISTEMIC_IMPACT`, `POTENTIAL_CONTAMINATION`,
`INDEPENDENCE_COMPROMISED` and `HUMAN_REVIEW_REQUIRED`. Ambiguity becomes
`INDEPENDENCE_UNKNOWN`, never independent by default. Material result exposure can permanently mark
the holdout compromised after consumption.

## Authorization, SoD and audit

Existing OAuth project membership is reused. Operators/admins may author; admins publish partitions,
seal holdouts and open holdouts. The partition author cannot open that partition's holdout. The stack
does not yet have a first-class model-tuner identity; actor provenance and the stricter partition
author/opener separation are used, and this remains the sole controlled SoD warning.

Every creation, link, transition, opening, access and compromise writes to the existing audit system.
No payload values are copied into audit context.

## Historical tests and adversarial evidence

```text
GDSS-006B unit + PostgreSQL:      22/22 PASS
real two-connection concurrency: 10/10 PASS
topology-next full regression:   489 passed, 73 skipped
TypeScript typecheck:            PASS
Next.js production build:        PASS
Python runtime:                  179 passed, 6 skipped
Parametric Control Engine:       40/40 PASS
isolated migration cycle:        PASS
```

Adversarial coverage includes direct and multi-hop overlap, cycles, depth exhaustion, group leakage,
temporal leakage, three deterministic duplicate strategies, unknown independence, cross-project
assignment, evidence/snapshot/published-plan mutation, access/ledger mutation, double opening,
post-consumption reuse, resealing and material exposure followed by compromise.

The concurrency fixture used two PostgreSQL connections against the same sealed holdout. Exactly one
opening succeeded, one deterministic conflict was returned, and one opening transition/reference
was persisted.

## P024-R2 verification evidence

The resource boundary was exercised as edge depth, not node count:

```text
depth 0/1/8/15/16 TypeScript: PASS
depth 17 TypeScript:           LINEAGE_DEPTH_LIMIT_EXCEEDED
depth 8 PostgreSQL direct SQL: PASS
depth 16 PostgreSQL direct SQL: PASS
depth 17 PostgreSQL direct SQL: LINEAGE_DEPTH_LIMIT_EXCEEDED (HTTP/domain mapping 409)
depth 16 overlap:              TRANSITIVE_LINEAGE_OVERLAP
depth 17 without overlap:      LINEAGE_DEPTH_LIMIT_EXCEEDED
direct and multi-hop cycles:   EVIDENCE_LINEAGE_CYCLE
concurrent joint depth 17:     exactly one extension accepted; one rejected
```

This proves the database boundary cannot be bypassed through direct SQL to persist a deeper lineage
and later misclassify it as independent. The project advisory transaction lock prevents concurrent
extensions from each validating against stale closure.

Final P024-R2 regression on the remediation checkout:

```text
GDSS-006B domain unit tests:             15/15 PASS
GDSS-006A/006B PostgreSQL + concurrency: 26/26 PASS
topology-next full regression:           539 passed, 76 skipped
TypeScript typecheck:                    PASS
Next.js production build:                PASS
Python runtime:                          179 passed, 6 skipped
Parametric Control Engine:               40/40 PASS
static authority/boundary scans:          PASS
git diff whitespace check:                PASS
```

## Performance observations

Original observations are retained as historical evidence and are not valid-boundary demonstrations:

```text
lineage/overlap traversal, depth 59: 0.106 ms targeted run
10,000-unit snapshot hash:          17.691 ms targeted run
ordinary transactional open:        9.823 ms
two-connection competing open:     104.216 ms total race
```

P024-R2 observations on the local verification host; diagnostic only, not contractual SLAs:

```text
depth 8 accepted:             0.027 ms
depth 16 accepted:            0.051 ms
depth 17 fail-closed path:     0.096 ms
10,000-unit snapshot hash:    16.432 ms
```

The lineage limit is an enforcement/resource guard, not scientific content and not an input to any
canonical scientific or evidence identity. Therefore no hash version changed and no historical
evidence hash was modified.

## Invariants and authority boundary

This phase implements the GDSS-006B portions of `VAL-INV-08`, `16..22`, supports `35`, and preserves
`VAL-INV-40`. Calibration evidence remains distinct from reserved evidence; exposure is historical;
consumption is irreversible; no evidence record grants physical or predictive authority.

```text
Validation execution: NONE
Prediction authority: NONE
Predictive claim:     NONE
Control authority:    NONE
Physical authority:   NONE
```

## Git state

GDSS-006A..F and this corrective 006B remediation remain locally classified and uncommitted. No
push, tag, release or remote publication was performed. The canonical architecture was not
rewritten, and GDSS-006G closure evidence was not created.

## P024-R3 corrective addendum

P024 verification discovered that an OAuth-authenticated actor with `auth_provider=ai` and an admin
role could open a holdout. P024-R3 centralized the existing GDSS-006F AI provenance predicate and
made it an authority-denial attribute for `OPEN_HOLDOUT`, independent of RBAC elevation. Unit,
service and real-route tests now return `403 AI_AUTHORITY_FORBIDDEN` before repository execution;
human custodian RBAC is unchanged. No holdout data, lifecycle meaning or historical audit record was
rewritten. Corrective migration `0051` supplies the related cross-phase resource enforcement but
does not persist identity policy. GDSS-006G remains pending.
