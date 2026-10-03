# MIDD-IOT — GDSS-003
## Governed Dynamic Simulation Runtime Foundation
### Implementation Record v0.1

**Execution:** `MIDD-GDSS-P008-R2`
**Baseline:** `dade8e6d490ea3adc88aac0353c2e72fee2df47b`
**Migration:** `0041_gdss_dynamic_simulation`
**Physical authority:** `NONE`

## Historical sequence

`P008` stopped correctly when the original catalog lacked a standalone TIME unit. `P008-R1`
introduced the immutable successor `GDSS_UNIT_CONVERSION_V2` and `second@1`. `P008-R2` resumed the
authorized GDSS-003 implementation. V1 remains historical and is not silently extended.

## Production modules

Pure modules under `apps/topology-next/src/lib/gdss/simulation` provide closed contracts and
versions, canonical identities, exact resource limits, binding validation, indexed time,
`EXPLICIT_EULER_V1`, trajectory encoding/decoding, authorization and recovery policy. The pure
runtime imports no database, HTTP, filesystem, environment, MQTT, telemetry, DTE, Control Engine
or actuation capability.

`gdss-simulation.repository.ts` owns PostgreSQL transactions and immutable evidence.
`gdss-simulation.service.ts` maps scoped OAuth project authority to `RUN_SIMULATION` and composes
Transaction A, the pure runtime and Transaction B.

## Temporal and dimensional contract

Every v1 run explicitly binds:

```text
unitConversionCatalogVersion = GDSS_UNIT_CONVERSION_V2
timeUnit = second@1
dimension = [0,0,1,0,0,0,0]
quantity semantics = INTERVAL
affine family = false
```

Binding preflight uses the accepted GDSS-002 dimension vector operations to prove
`dimension(rate) = dimension(state) - TIME`. The transition therefore has
`dimension(rate × dt) = dimension(state)`. V1 catalog selection fails closed.

`step_index` is authoritative. `t(i) = start + i × step` is derived independently and never by
repeated floating accumulation. N transitions produce N+1 points.

## Dynamic binding and solver

Dynamic bindings are independent, project-owned, immutable versioned aggregates tied to one exact
model version and content hash. Roles are closed to STATE, RATE, ALGEBRAIC and PARAMETER and are
never inferred. Lifecycle is `NULL → DRAFT → PUBLISHED → DEPRECATED`; only PUBLISHED executes.

`EXPLICIT_EULER_V1` evaluates the algebraic DAG, then every rate from one immutable pre-step
snapshot, computes all candidates, validates constraints with `FAIL_RUN`, and adopts the candidates
as one logical transition. Instantaneous algebraic SCCs fail closed. No clamping or repair exists.

## Canonical evidence and identities

Separate domain-separated identities are implemented:

```text
dynamic_binding_hash   = SHA256(canonical gdss-dynamic-binding:v1)
simulation_input_hash  = SHA256(canonical gdss-simulation-input:v1)
trajectory_hash        = SHA256(exact canonical trajectory bytes)
simulation_result_hash = SHA256(canonical gdss-simulation-result:v1)
execution_attempt_id   = independent UUID
```

The input identity contains exact V2 and `second@1`. Actor, attempt UUID, idempotency key, database
sequences and wall clock are excluded.

`GDSS_TRAJECTORY_NDJSON_V1` is UTF-8 without BOM, LF-only with final LF, sorted and closed-schema.
Binary64 values use lowercase big-endian hex with normalized zero. Every point is `SIMULATED`.
The adversarial decoder rejects malformed encoding, duplicate keys, index/symbol drift, invalid
binary64, dimensions/units, size/count and hash mismatches.

## Persistence and recovery

Migration 0041 creates exactly seven tables. All reject UPDATE and DELETE through database-level
guards. PostgreSQL BYTEA is the v1 artifact backend, bounded to 16,777,216 bytes.

Transaction A atomically commits attempt, RUNNING event and audit evidence before runtime.
Transaction B atomically inserts/verifies content-addressed bytes, diagnostics, one terminal event
and audit evidence. Hash collisions require exact byte and metadata equality.

`GDSS_SIM_RECOVERY_V1` uses an explicit 900-second abandonment threshold. PostgreSQL row locks with
`SKIP LOCKED` guarantee concurrent workers produce one `FAILED / EXECUTION_INTERRUPTED` terminal
event. Unknown-commit recovery reloads and verifies immutable terminal evidence before retrying.

## Authorization and resources

`RUN_SIMULATION` requires `oauth_session`, a valid user, exact project membership, and operator or
admin role. Viewer, fallback, anonymous and out-of-project actors fail closed. It is not mapped to
model evaluation/publication or any control/deployment/actuation authorization.

`GDSS_SIM_LIMITS_V1` fixes: 64 states, 64 rates, exactly one rate per state, 256 algebraics, 256
parameters, 256 constraints, 10,000 steps, 10,001 points, 8,192 evaluator operations per step,
10,000,000 total operations, 16,777,216 trajectory bytes and 256 diagnostics.

## Analytical and benchmark evidence

The reservoir `dV/dt = Qin - Qout` reaches its analytical result exactly for the selected binary64
fixture and exercises `rate × second → state`. The thermal decay fixture shows decreasing error for
dt 1, 0.5 and 0.25; this is numerical convergence, not scientific validation.

The predeclared benchmark thresholds were 3,000 ms elapsed and 128 MiB heap delta. The 1-state,
10,000-step reservoir produced 10,001 points, 30,000 evaluator operations and a 1,799,270-byte
artifact in 910.251 ms with 14,888,224 bytes measured heap delta during the final complete focused GDSS
matrix: PASS.

## Epistemic and physical boundary

Observed provenance on an input does not propagate to results. Trajectories remain `SIMULATED`,
not OBSERVED, PREDICTED, CALIBRATED or SCIENTIFICALLY_VALIDATED. A successful run is neither an
experiment nor a Digital Shadow/Twin synchronization. Simulation authorizes nothing physical.

## Findings

- Blocking: none in production code or invariant execution.
- Non-blocking: complete regression suites may retain infrastructure-conditioned skips; they are
  reported explicitly at closure.
- Future phase: additional solvers, adaptive steps, stochastic systems, event handling, calibration,
  prediction and external artifact backends require successor contracts.
