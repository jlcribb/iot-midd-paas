# MIDD-IOT — GDSS-006A Implementation Evidence

**Authorization:** `MIDD-GDSS-P018-R1`

**Status:** `COMPLETED_GDSS_006A_CONTRACTS_PROTOCOL_AND_DOMAIN_FOUNDATION_WITH_WARNINGS`

**Baseline:** `main@dee81328f4a73b525f8d7236d8ee799044b9cabc`

**Final Alembic revision:** `0044 (head)`; one head

## Implemented boundary

GDSS-006A implements governed, project-scoped and versioned validation-protocol and validity-domain
contracts. It provides structured targets, explicit horizons, declarative acceptance criteria and
policies, the twelve authorized revalidation triggers, exact model/domain bindings, deterministic
hashes, protected lifecycles, RBAC, separation of duties, audit history, persistence and the minimal
HTTP surface required to manage those contracts.

It does not partition evidence, expose holdout data, run validation, generate or pair predictions,
execute metrics, assess uncertainty, construct evidence sets, grant predictive capability, publish
predictive claims, integrate with physical systems, or introduce ML/RL/adaptive learning.

## Migration and relational enforcement

Migration `0044_gdss006a_validation_protocol_domain_foundation.py` creates thirteen normalized
tables, eight guard functions, eighteen triggers, project/version/hash constraints and exact foreign
keys. Identity and lifecycle history are append-only. Scientific content and normalized projections
are mutable only in `DRAFT`; database triggers reject direct mutation after that state.

The required isolated migration cycle passed:

```text
0043 -> 0044 -> 0043 -> 0044
```

The final database and source tree each report a single Alembic head: `0044`.

Version allocation locks the stable identity row with `FOR UPDATE`, computes the next monotonic
number inside that transaction and is backed by `UNIQUE(identity_id, version_number)`. PostgreSQL
tests prove monotonic allocation and collision rejection. A simultaneous two-connection race was
not retained as a repeatable fixture because the suite deliberately rolls back all evidence; this is
the sole controlled verification warning.

## Domain and protocol contracts

- Protocol states: `DRAFT`, `REVIEW_REQUIRED`, `APPROVED`, `SEALED`, `SUPERSEDED`, `INVALIDATED`.
- Protocol edges: `DRAFT -> REVIEW_REQUIRED`, `REVIEW_REQUIRED -> DRAFT|APPROVED`,
  `APPROVED -> SEALED`, `SEALED -> SUPERSEDED|INVALIDATED`.
- Domain states: `DRAFT`, `APPROVED`, `SEALED`, `SUPERSEDED`, `INVALIDATED`.
- Domain edges: `DRAFT -> APPROVED`, `APPROVED -> SEALED`,
  `SEALED -> SUPERSEDED|INVALIDATED`.
- Domain predicates: numeric range, parameter range, temporal range, categorical membership and
  boolean condition, each with shape-specific application and database validation.
- Boundaries: hard, declared operational and unknown.
- Protocol content freezes the exact model identity/version/number/hash and exact sealed validity
  domain version/hash. No `latest` lookup exists.

## Hashing and determinism

Canonical UTF-8 JSON uses deterministic field order, semantic-array ordering and IEEE-754 binary64
number normalization. SHA-256 hashes use NUL-delimited domain separation:

```text
gdss006:validation-protocol:v1
gdss006:validity-domain:v1
```

UUIDs, row identifiers, timestamps, workers and sessions are excluded from scientific content.
Tests prove order stability and hash changes for predicates, horizons and acceptance criteria.
PostgreSQL recomputes and verifies the same hash at seal time.

## Authorization, SoD and audit

Existing OAuth project membership is reused. Operators and administrators may author; only
administrators may approve. Author/approver separation is the default. Same-actor approval requires
an administrator, a non-empty exception reason and proof that the project has no second enabled
administrator. The lifecycle event records `sod_exception=true`; the exception grants no evidence
or physical authority.

Creation, update and every authorized lifecycle transition write to the existing
`iot_schema.auditoria` transactionally. Lifecycle tables also retain immutable ordered events with
idempotency keys.

## Verification

```text
GDSS-006A unit + PostgreSQL targeted: 21/21 PASS
topology-next full regression:       477 passed, 63 skipped
TypeScript typecheck:                PASS
Next.js production build:           PASS
Python runtime regression:           179 passed, 6 skipped
Parametric Control Engine:           40/40 PASS
Alembic migration cycle:             PASS
Alembic final state:                 0044 (head)
Static forbidden-capability scan:    PASS
Secret scan:                         PASS
```

Environment-gated skips are pre-existing integration categories; the new GDSS-006A PostgreSQL suite
was run separately against real PostgreSQL and passed all thirteen persistence tests.

Adversarial coverage rejects sealed protocol/domain mutation, lifecycle jumps, self-approval,
duplicate versions, malformed predicate shapes, absent model versions, cross-project domain
bindings, invalidated-protocol reactivation, draft hash injection, semantic hash reuse and forbidden
predictive/physical fields.

## Invariant boundary

This phase establishes the applicable foundations for `VAL-INV-01..07`, `09`, `14`, `15`, `26`,
`27`, `29`, `32`, `37` and `40`. It does not claim execution evidence for invariants owned by later
phases. In particular, calibration remains distinct from validation, protocol/domain meaning is
predeclared and exact, scopes cannot become claims, and every GDSS-006A artifact has physical
authority `NONE`.

```text
Control Engine dependency: NONE
MQTT dependency:           NONE
DTE dependency:            NONE
Physical authority:        NONE
Validation execution:      NONE
Predictive claim:          NONE
```

What physical action can GDSS-006A authorize? **NOTHING.**

## Git and publication

All GDSS-006A implementation and its two source-of-truth documents remain local and uncommitted.
No push, tag, release or remote publication was performed. A commit was intentionally omitted under
the prompt's conservative rule because the two canonical GDSS-006 documents arrived as pre-existing
untracked material and must remain explicitly classified at controlled Git closure.
