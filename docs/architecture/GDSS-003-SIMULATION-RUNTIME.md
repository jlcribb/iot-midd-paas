# MIDD-IOT — GDSS-003
## Governed Dynamic Simulation Runtime Foundation
### Simulation Runtime v0.1

**Version:** `v0.1`
**Status:** `PROPOSED_FOR_REVIEW`
**Implementation:** `NOT_YET_AUTHORIZED`
**Baseline:** `dade8e6d490ea3adc88aac0353c2e72fee2df47b`
**Alembic baseline:** `0040`

## Runtime boundary

The proposed runtime is a pure GDSS module above the GDSS-002 expression core. It receives frozen
model/binding snapshots and a complete input manifest and returns an immutable computational result.
It has no database, network, filesystem, environment, clock, MQTT, telemetry, DTE, Control Engine
or actuation capability. A future adapter may load/persist governed artifacts; the core may not.

## Preflight

Before allocating a trajectory, the adapter and pure runtime must:

1. authorize `RUN_SIMULATION` for exact project scope;
2. load one exact model and published binding version;
3. verify model content and binding hashes;
4. validate all version identifiers, requiring explicit `GDSS_UNIT_CONVERSION_V2` and resolving
   `timeUnit` under that exact catalog;
5. resolve every binding locally and reject cardinality/cross-version errors;
6. validate unique state/rate mappings, algebraic DAG and dimensions;
7. require exactly one initial state and every referenced parameter;
8. validate finite temporal configuration and resource limits;
9. canonicalize and hash the input manifest;
10. create a distinct execution attempt.

No partial configuration is repaired from defaults or external state.

## Exact execution algorithm

1. Convert explicit inputs to canonical units and build immutable `snapshot(0)`.
2. Emit canonical point `step_index = 0`.
3. For each `k` from `0` through `stepCount - 1`:
   - derive `t(k)` directly from configuration;
   - evaluate the algebraic DAG in stable symbol order from `snapshot(k)`;
   - evaluate every rate against the same snapshot/environment;
   - validate rate dimension, operation budgets and finiteness;
   - compute all Euler next-state candidates without mutating the snapshot;
   - validate candidate finiteness and explicit constraints;
   - enforce trajectory byte/point and total-operation budgets;
   - atomically adopt candidates as `snapshot(k+1)`;
   - emit point `k+1` in stable state-symbol order.
4. Complete with `END_TIME_REACHED` after exactly `stepCount` transitions.
5. Canonicalize trajectory and deterministic diagnostics, then compute result identity.

Any failing sub-step emits a stable diagnostic and ends the attempt as `FAILED`; the invalid
candidate is never emitted as a successful point.

## Status and termination

Execution status is `RUNNING`, `COMPLETED`, `FAILED` or, only when a future cancellation contract is
implemented, `ABORTED`. `COMPLETED` requires `END_TIME_REACHED`, a complete N+1-point trajectory and
valid result hash. Failure status and termination reason are separate.

A failed execution may retain points through the last valid committed snapshot as `PARTIAL`. The
failing step, diagnostic code and stage are recorded. Partial evidence is immutable and cannot be
queried as a completed result.

## Resource governance

The profile must bound states, rates, algebraics, step count, points, operations per step, total
operations, artifact bytes and diagnostics. Preflight rejects obviously excessive configurations;
incremental counters stop runtime work before any category is exceeded. `stepCount + 1` is checked
without overflow. Serialization is bounded and streaming/counted; no unbounded in-memory output is
permitted.

Threat mitigations:

| Threat | Architectural mitigation |
|---|---|
| tiny step / huge horizon | explicit bounded stepCount; no horizon-derived unbounded loop |
| state/dependency explosion | binding and graph limits before execution |
| algebraic cycle abuse | deterministic SCC rejection |
| pathological rates/divergence | finite checks at every stage; fail closed |
| trajectory exhaustion | point and byte budgets with incremental accounting |
| malformed/cross-version binding | exact local resolution plus hash checks |
| solver spoofing | closed key/version registry |
| serialization abuse | canonical closed schema and byte limit |
| repeated expensive runs | project authorization; future quota/rate policy at adapter boundary |

## Determinism and concurrency

The runtime uses no hidden clock or random source. All maps serialize by stable symbol. Identical
inputs under the same versioned runtime produce the same trajectory/result hashes. Separate calls
may have distinct attempt IDs and audit times. Parallel attempts cannot share mutable state.

## Explainability

For any point, evidence identifies exact model/binding hashes, input manifest, step index,
pre-step state, algebraic order, rate formulas, solver/version, units and diagnostics. Algebraic and
rate traces may be generated as bounded optional diagnostic artifacts; they are not mandatory
canonical trajectory content.

## Reproducibility package

A portable package contains the canonical model snapshot and hash, binding snapshot and hash, input
manifest, all semantic/version identifiers, resource profile, canonical trajectory artifact,
diagnostics and hashes. Immutable IDs alone are sufficient only while their governed artifacts are
available and hash-verifiable; export must include snapshots to remove that external dependency.

Audit actor, request ID and wall-clock timestamps accompany the execution envelope but never affect
computational identity.

## Isolation

Existing Control Engine replay uses `control_simulation_sessions`, policy/topology/dataset snapshots,
virtual timestamps and a Python replay runner. GDSS simulation uses none of them. It does not call
`first_order.py`, `control_engine_worker.py`, simulation replay APIs or control routes. Sharing is
limited to general repository infrastructure only after separate review.
