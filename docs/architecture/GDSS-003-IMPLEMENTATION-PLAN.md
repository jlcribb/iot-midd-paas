# MIDD-IOT — GDSS-003
## Governed Dynamic Simulation Runtime Foundation
### Implementation Plan v0.1

**Version:** `v0.1`
**Status:** `PROPOSED_FOR_REVIEW`
**Implementation:** `NOT_YET_AUTHORIZED`
**Architecture approval:** `APPROVED_WITH_FINDINGS`
**Baseline:** `dade8e6d490ea3adc88aac0353c2e72fee2df47b`
**Alembic baseline:** `0040`
**Planned migration:** `0041_gdss_dynamic_simulation` — `NOT_YET_AUTHORIZED`

## 1. Purpose and authority

This plan resolves the findings required before implementation. It authorizes no production code,
test, fixture, runtime, API, UI, schema, migration, commit, tag or push. Execution requires a later
operational prompt.

The implementation will strengthen A1 Digital Twin Foundation while preserving:

```text
model != evaluated expression != simulated state != observation != prediction
simulation != experiment != Control Engine replay != physical authority
```

## 2. Fixed implementation scope

Implement only deterministic fixed-step continuous-time simulation with explicit bindings,
initial conditions, parameters, acyclic algebraics, `EXPLICIT_EULER_V1`, simultaneous state
updates, bounded trajectories, immutable evidence and the reservoir/thermal fixtures.

Exclude adaptive/RK solvers, events, stochasticity, algebraic-loop solving, calibration,
optimization, prediction, experiments, Digital Shadow/Twin synchronization, Control Engine, DTE,
MQTT, telemetry and actuation.

## 3. Target modules

Planned TypeScript modules under `apps/topology-next/src/lib/gdss/simulation/`:

```text
contracts.ts          closed schemas and types
versions.ts           DETERMINISTIC_CONTINUOUS_TIME_V1, EXPLICIT_EULER_V1
canonical.ts          binding/input/trajectory/result canonicalization and hashes
binding.ts            exact-version binding validation and DAG construction
temporal.ts           indexed time semantics
solver.ts             pure explicit Euler transition
runtime.ts            pure bounded execution state machine
trajectory.ts         canonical NDJSON encoder/decoder and byte accounting
diagnostics.ts        stable codes and stages
limits.ts             GDSS_SIM_LIMITS_V1
index.ts              deliberate public surface
```

Adapters remain in `src/lib/services` and `src/lib/repositories`; no runtime module imports DB,
HTTP, filesystem, environment, Control Engine or operational clients.

## 4. Exact migration 0041 schema

If later authorized, `0041_gdss_dynamic_simulation.py` creates exactly seven tables. All UUIDs use
`gen_random_uuid()`, timestamps are audit-only `TIMESTAMPTZ`, hashes are lowercase `CHAR(64)` with
`CHECK (value ~ '^[0-9a-f]{64}$')`, and deletion of referenced evidence is `RESTRICT`.
Creation order is binding identity, binding version, binding lifecycle event, attempt, artifact,
execution event and diagnostic so every foreign key resolves when declared.

### 4.1 `public.gdss_dynamic_binding`

```text
id UUID PK
project_id UUID NOT NULL FK projects(id) ON DELETE RESTRICT
canonical_name TEXT NOT NULL
description TEXT NOT NULL DEFAULT ''
created_by TEXT NOT NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
UNIQUE(project_id, canonical_name)
```

Identity rows are immutable after insert.

### 4.2 `public.gdss_dynamic_binding_version`

```text
id UUID PK
binding_id UUID NOT NULL FK gdss_dynamic_binding(id) ON DELETE RESTRICT
version_number INTEGER NOT NULL CHECK > 0
model_version_id UUID NOT NULL FK gdss_version(id) ON DELETE RESTRICT
predecessor_version_id UUID NULL self-FK ON DELETE RESTRICT
dynamic_semantic_version TEXT NOT NULL CHECK = 'DETERMINISTIC_CONTINUOUS_TIME_V1'
content JSONB NOT NULL
canonical_content TEXT NOT NULL
dynamic_binding_hash CHAR(64) NOT NULL
created_by TEXT NOT NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
UNIQUE(binding_id, version_number)
UNIQUE(binding_id, dynamic_binding_hash)
UNIQUE(id, model_version_id)
```

Content is immutable from insert. The model version's project must match binding ownership; a
constraint trigger validates this because it spans tables. Draft corrections create a new version,
not in-place edits.

### 4.3 `public.gdss_dynamic_binding_lifecycle_event`

```text
id BIGSERIAL PK
binding_version_id UUID NOT NULL FK binding_version(id) ON DELETE RESTRICT
sequence INTEGER NOT NULL CHECK > 0
from_status TEXT NULL
to_status TEXT NOT NULL CHECK IN ('DRAFT','PUBLISHED','DEPRECATED')
actor TEXT NOT NULL
reason TEXT NOT NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
UNIQUE(binding_version_id, sequence)
```

Allowed path is creation event `NULL→DRAFT`, then `DRAFT→PUBLISHED→DEPRECATED`. Current status is a
projection of the latest sequence. Only PUBLISHED is executable. Events are append-only.

### 4.4 `public.gdss_simulation_attempt`

```text
id UUID PK                         -- execution_attempt_id
project_id UUID NOT NULL FK projects(id) ON DELETE RESTRICT
model_version_id UUID NOT NULL FK gdss_version(id) ON DELETE RESTRICT
binding_version_id UUID NOT NULL FK binding_version(id) ON DELETE RESTRICT
simulation_input_manifest JSONB NOT NULL
simulation_input_hash CHAR(64) NOT NULL
requested_by TEXT NOT NULL
idempotency_key TEXT NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
UNIQUE(project_id, idempotency_key) WHERE idempotency_key IS NOT NULL
```

A deferred constraint trigger verifies project/model/binding consistency, PUBLISHED binding state
and stored hashes. Equal input hashes may have different attempt IDs.

### 4.5 `public.gdss_simulation_execution_event`

```text
id BIGSERIAL PK
attempt_id UUID NOT NULL FK gdss_simulation_attempt(id) ON DELETE RESTRICT
sequence INTEGER NOT NULL CHECK > 0
status TEXT NOT NULL CHECK IN ('RUNNING','COMPLETED','FAILED','ABORTED')
termination_reason TEXT NULL
simulation_result_hash CHAR(64) NULL
trajectory_hash CHAR(64) NULL FK gdss_simulation_artifact(hash) ON DELETE RESTRICT
trajectory_completeness TEXT NULL CHECK IN ('COMPLETE','PARTIAL')
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
UNIQUE(attempt_id, sequence)
```

Sequence 1 must be RUNNING. Sequence 2 must be exactly one terminal status. COMPLETED requires
`END_TIME_REACHED`, COMPLETE artifact and result hash. FAILED may reference PARTIAL evidence.
Further events are rejected by constraint trigger. Events are immutable.

### 4.6 `public.gdss_simulation_artifact`

```text
hash CHAR(64) PRIMARY KEY
media_type TEXT NOT NULL CHECK = 'application/vnd.midd.gdss-trajectory+ndjson;version=1'
format_version TEXT NOT NULL CHECK = 'GDSS_TRAJECTORY_NDJSON_V1'
byte_length INTEGER NOT NULL CHECK BETWEEN 1 AND 16777216
payload BYTEA NOT NULL
point_count INTEGER NOT NULL CHECK BETWEEN 1 AND 10001
completeness TEXT NOT NULL CHECK IN ('COMPLETE','PARTIAL')
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
CHECK (octet_length(payload) = byte_length)
```

Insert uses `ON CONFLICT(hash) DO NOTHING`, followed by equality verification of bytes and metadata.
Rows are content-addressed and immutable. This PostgreSQL BYTEA table is the exact v1 artifact
backend; no S3, MinIO, filesystem or InfluxDB dependency is introduced.

### 4.7 `public.gdss_simulation_diagnostic`

```text
id BIGSERIAL PK
attempt_id UUID NOT NULL FK gdss_simulation_attempt(id) ON DELETE RESTRICT
sequence INTEGER NOT NULL CHECK > 0 AND <= 256
code TEXT NOT NULL
severity TEXT NOT NULL CHECK IN ('ERROR','WARNING','INFO')
stage TEXT NOT NULL
step_index INTEGER NULL CHECK >= 0
state_ref TEXT NULL
rate_ref TEXT NULL
formula_ref TEXT NULL
details JSONB NOT NULL DEFAULT '{}'
message TEXT NOT NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
UNIQUE(attempt_id, sequence)
```

Diagnostics are append-only. Human `message` and timestamps never enter result identity.

### 4.8 Guards and indexes

One reusable trigger function rejects UPDATE/DELETE on all seven tables. Insert guards validate
event sequences, terminal requirements and project/version membership. Indexes cover binding
project/name, version binding/order, attempt project/created, attempt input hash, event attempt/
sequence and diagnostic attempt/sequence. No index changes canonical ordering.

## 5. Canonical artifact format

Use `GDSS_TRAJECTORY_NDJSON_V1`, UTF-8 without BOM and LF line endings. Every line is canonical JSON
with lexicographically sorted keys, no insignificant whitespace and a final LF.

Line 1 is the header:

```json
{"completeness":"COMPLETE","format":"GDSS_TRAJECTORY_NDJSON_V1","pointCount":3,"simulationInputHash":"<sha256>","stateSymbols":["temperature"]}
```

Each following line is exactly:

```json
{"epistemicKind":"SIMULATED","states":{"temperature":{"dimension":[0,0,0,0,1,0,0],"unit":{"key":"kelvin","revision":1},"value":{"$binary64":"<16-lowercase-hex>"}}},"stepIndex":0}
```

`stepIndex` is an exact JSON integer. State symbols sort lexicographically. Dimensions retain their
seven-position order. Numbers use normalized big-endian binary64 hex from GDSS-002; `-0` is `+0`;
NaN and Infinity are forbidden. The trajectory does not store computed timestamps, rates or
algebraics. Time is derived from the input manifest and index.

Decoder requirements: reject duplicate keys, unknown fields, invalid UTF-8, CRLF, absent final LF,
out-of-order/non-contiguous indices, symbol-set drift, noncanonical hex, byte/point mismatch and any
value that fails the declared unit/dimension contract.

## 6. Content addressing and identities

```text
dynamic_binding_hash = SHA256(UTF8(canonical JSON domain "gdss-dynamic-binding:v1"))
simulation_input_hash = SHA256(UTF8(canonical JSON domain "gdss-simulation-input:v1"))
trajectory_hash = SHA256(exact GDSS_TRAJECTORY_NDJSON_V1 bytes)
simulation_result_hash = SHA256(UTF8(canonical JSON domain "gdss-simulation-result:v1"))
execution_attempt_id = random UUIDv4 generated by the server
```

Input hash covers model ID/content hash, binding ID/version/hash, dynamic/solver versions, sorted
initial conditions and parameters with provenance identities, temporal configuration, GDSS-002
versions including explicit `unitConversionCatalogVersion: GDSS_UNIT_CONVERSION_V2`,
`GDSS_SIM_LIMITS_V1` and `FAIL_RUN`. `TemporalConfiguration.timeUnit` resolves only under V2 and
GDSS-003 v1 requires `second@1`; changing the catalog version changes input identity. Result hash covers input hash, terminal status,
termination reason, completeness, trajectory hash and deterministic diagnostic fields.

Actor, UUID, idempotency key, DB sequences and wall-clock timestamps are excluded. An optional
idempotency key deduplicates transport retries to the same attempt; equal computational inputs do
not otherwise suppress new attempts.

## 7. Append-only transaction and failure compensation

### 7.1 Accepted attempt

Transaction A inserts the immutable attempt and RUNNING event plus audit record, then commits. If it
fails, no runtime starts and no attempt exists. The pure runtime computes outside a DB transaction,
bounded entirely in memory to 16 MiB plus fixed overhead.

### 7.2 Successful or failed finalization

Transaction B performs, in order:

1. insert/verify content-addressed COMPLETE or PARTIAL artifact;
2. append bounded diagnostics;
3. append exactly one terminal execution event referencing the artifact;
4. append audit evidence;
5. commit atomically.

Because artifact bytes and manifests use the same PostgreSQL transaction, no committed event can
reference missing bytes and no external cleanup protocol is required.

### 7.3 Compensation matrix

| Failure | Required outcome |
|---|---|
| canonical encoding/runtime before B | start new B containing FAILED event, diagnostics and last valid PARTIAL bytes if encodable |
| artifact insert/hash collision mismatch | rollback B; retry B as FAILED with `ARTIFACT_INTEGRITY_FAILURE` and no artifact reference |
| diagnostic/event/audit insert fails | rollback all B writes; retry terminalization with same attempt and deterministic result |
| connection loss with unknown commit | read terminal event by attempt ID; if present verify hashes, otherwise retry B |
| process crash after A before B | recovery job finds RUNNING older than lease threshold and appends FAILED `EXECUTION_INTERRUPTED`; optional valid checkpoint is not assumed |
| retry after terminal event | return immutable existing terminal evidence; never append a second terminal event |

Recovery never changes or deletes evidence. A later implementation may move artifacts to object
storage only under a new backend version and an outbox/staging protocol.

## 8. Partial trajectory persistence

The runtime buffers only valid committed points. On failure at step k, the candidate for k+1 is not
emitted. If at least point 0 exists, encode points `0..k` as PARTIAL, subject to byte limits. If even
initialization fails, no artifact is stored. FAILED result identity binds the partial hash or explicit
absence. APIs must require an explicit `includePartial=true` path and never return PARTIAL through a
completed-result contract.

## 9. Authorization mapping

Add logical GDSS operation `run_simulation` and exported capability `RUN_SIMULATION`. Reuse OAuth
`ControlActor`, exact project membership and effective project role:

| Effective role | Prepare binding draft | Publish binding | Run simulation | Read own-project evidence |
|---|---:|---:|---:|---:|
| viewer | NO | NO | NO | YES |
| operator | YES | NO | YES | YES |
| admin | YES | YES | YES | YES |

Fallback/anonymous/header-only actors fail: auth source must be `oauth_session`, user ID present and
project accessible. `RUN_SIMULATION` is not mapped to existing `edit_policies` and grants no
EVALUATE/PUBLISH/control/deployment/actuation permission.

## 10. Exact resource profile

`GDSS_SIM_LIMITS_V1`:

| Category | Limit |
|---|---:|
| states | 64 |
| rates | 64 and exactly one per state |
| algebraic bindings | 256 |
| parameter bindings | 256 |
| constraints | 256 |
| stepCount | 10,000 |
| trajectory points | 10,001 |
| evaluator operations per step | 8,192 |
| total evaluator operations | 10,000,000 |
| canonical trajectory bytes | 16,777,216 |
| diagnostics | 256 |

GDSS-002 source/token/AST/function limits remain independently enforced per expression. Preflight
checks counts and overflow-safe point/operation upper bounds. Runtime increments exact counters and
fails before exceeding a limit. Threshold changes require `GDSS_SIM_LIMITS_V2`, not configuration
mutation. Benchmarks must validate these values before release; failure to meet bounded runtime or
memory is blocking, not permission to silently raise them.

## 11. Implementation sequence

1. Authorize and add migration 0041 with SQL constraint tests.
2. Implement contracts, versions, canonicalization and limits without I/O.
3. Implement binding resolver, dimensional checks and algebraic DAG.
4. Implement indexed time, Euler solver and pure bounded runtime.
5. Implement NDJSON encoder/decoder and golden hashes.
6. Implement repositories with append-only guards and atomic finalization.
7. Implement project-scoped authorization service; no public API is required unless separately
   authorized.
8. Add neutral analytical fixtures, hydroponic fixture only after neutral gates pass.
9. Run invariant, security, regression, migration and benchmark gates.

No Control Engine, DTE, MQTT, telemetry, simulation replay or actuation module may be imported.

## 12. Forty-invariant test matrix

| Invariant | Planned evidence |
|---|---|
| 01 | exact model ID/hash and cross-version rejection |
| 02 | fake wall/device/observation timestamps cannot affect hashes/output |
| 03 | missing and duplicate initial conditions fail |
| 04 | exhaustive closed-role schema tests |
| 05 | misleading symbol/formula names do not assign roles |
| 06 | state/rate/time dimensional positive and negative vectors |
| 07 | missing/unknown/spoofed solver version fails |
| 08 | each temporal field changes input hash |
| 09 | omitted, zero, negative and non-finite step fails |
| 10 | repeated/cross-process golden trajectory hash equality |
| 11 | coupled two-state fixture proves pre-step snapshot use |
| 12 | state feedback passes; same-step algebraic SCC fails |
| 13 | every emitted point is SIMULATED |
| 14 | output schema cannot express PREDICTED |
| 15 | no scientific-validation field/state/transition exists |
| 16 | OBSERVED initial provenance still yields SIMULATED points |
| 17 | missing input fails without telemetry/DB lookup |
| 18 | forbidden MQTT import/source scan and denied-I/O harness |
| 19 | forbidden Control Engine/replay import scan |
| 20 | forbidden DTE import scan |
| 21 | result always exposes physical authority NONE |
| 22 | no control/deployment/actuation repository calls |
| 23 | exact and over-limit test for every profile category |
| 24 | NaN, Infinity, overflow and divergent-rate failures |
| 25 | injected step failure yields FAILED/PARTIAL, never COMPLETED |
| 26 | SQL UPDATE/DELETE rejected for terminal evidence |
| 27 | model successor does not alter old execution bytes/hashes |
| 28 | solver golden change requires different version |
| 29 | input/result domain-separated hash assertions |
| 30 | core source contains no Forrester vocabulary/dependency |
| 31 | result has no experiment/hypothesis/comparison contract |
| 32 | no physical identity or synchronization contract |
| 33 | constraint violation fails and never clamps |
| 34 | paired dynamic-feedback/algebraic-cycle fixtures |
| 35 | model content/expression hashes unchanged before/after run |
| 36 | no FK/import/name reuse from `control_simulation_*` |
| 37 | binding create/publish leaves GDSS content hash unchanged |
| 38 | step index continuity and independently derived time |
| 39 | shuffled maps/DB rows yield identical canonical trajectory |
| 40 | equal inputs: distinct attempt UUIDs, equal computational hashes |

All 40 must pass before implementation closure. Additional mandatory suites cover reservoir exactness,
thermal convergence as dt decreases, artifact decoder adversarial cases, crash/unknown-commit
recovery, idempotency, PostgreSQL rollback, migration downgrade/upgrade, typecheck, production build,
complete Next regression and unaffected Python regression.

## 13. Acceptance gates

- One Alembic head at authorized `0041`; DB upgraded and schema constraints inspected.
- 40/40 invariants PASS with executed evidence; none inferred from documentation.
- Reservoir matches analytical solution within defined binary64 tolerance.
- Thermal error decreases across approved dt sequence; no scientific-validity claim.
- Same manifest produces byte-identical trajectory across repeated runs.
- All limit boundaries and security payloads fail closed.
- Terminal evidence survives restart and rejects mutation.
- Full regression, typecheck and production build pass.
- Architecture boundaries remain `NONE` for Control Engine, DTE, MQTT, telemetry and actuation.
- Final Git scope contains only authorized GDSS-003 implementation; commit/push/tag require separate
  authorization.

## 14. Findings resolved

| Required finding | Resolution |
|---|---|
| 0041 exact schema | seven-table append-only design in section 4 |
| canonical format | strict canonical NDJSON v1 in section 5 |
| storage backend | PostgreSQL BYTEA content-addressed artifact table |
| content-addressing | SHA-256 over exact canonical bytes |
| execution/attempt identity | UUID attempt separate from input/result hashes |
| append-only transaction model | immutable attempt plus ordered execution events |
| DB/artifact compensation | same-transaction artifact/event finalization and recovery matrix |
| partial persistence | last valid points only, explicit PARTIAL + FAILED |
| authorization | scoped OAuth operator/admin `RUN_SIMULATION` |
| resource thresholds | exact `GDSS_SIM_LIMITS_V1` values |
| invariant tests | explicit 40-row matrix |

> This plan specifies how GDSS-003 may be implemented. It does not authorize implementation.
