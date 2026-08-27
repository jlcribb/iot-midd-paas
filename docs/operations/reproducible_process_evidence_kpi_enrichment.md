# M6.3A — Reproducible Process Evidence and KPI Enrichment

## Problem and boundary

M6.2 originally had only aggregate result counters, so it could rigorously
derive only `actuation_count`. M6.3A preserves the primary temporal evidence
needed by the evaluator. The sequence is always **raw trace -> derived KPI ->
normalization -> evaluation -> comparison**. It is not production telemetry,
an historian, a ranking, a candidate generator, or an operational actuation
path.

## Trace model and storage decision

`control_simulation_traces` is one immutable trace for one completed M5 run and
one result. `control_simulation_trace_points` stores one row per semantic point:
`sequence_number`, elapsed `simulation_time_seconds`, process value, setpoint,
control output, actuator state and optional constraint state. Rows rather than
a JSONB blob were selected because sequence uniqueness, finite mandatory signal
values, ordered reads and future constrained inspection are materially useful
at the modest M5 cap of 500 records. This is not a generic time-series table.

Time is `elapsed_seconds_from_first_virtual_timestamp:v1`; wall-clock creation
time is never used in a KPI. Point order is contiguous and starts at one.
Malformed sequence/time, NaN, infinity or missing required signal aborts trace
materialization. No interpolation or missing-value imputation is performed.

## Identity and immutability

`trace_hash` is SHA-256 over trace schema version, experiment fingerprint, time
representation and ordered semantic points. It excludes database UUIDs, actor
and created time. Equivalent replay of the same frozen session produces equal
trace hashes; a primary value change produces a different one. A run has one
trace, and rerunning result materialization reuses it. Separate reproducible
runs retain their own result-linked trace rows while exposing the same semantic
hash. Database triggers reject trace and trace-point updates.

The new M5 result schema v2 includes the primary process fields in its canonical
result fingerprint. Evaluation engine v2 also includes `trace_hash`; existing
M6.2 v1 rows remain immutable and interpretable.

## Versioned KPI definitions

All extractors are deterministic functions over persisted points in
`kpi-extractor:v2`; each definition below is v1 and uses the process controlled
unit declared by the frozen policy.

| KPI | Definition | Unit | Required evidence |
| --- | --- | --- | --- |
| `tracking_error:v1` | `MAE = (1/N) Σ |r_i - y_i|` | controlled-unit | setpoint, process value |
| `overshoot:v1` | `max(0, max_i(y_i-r_i))` | controlled-unit | setpoint, process value |
| `undershoot:v1` | `max(0, max_i(r_i-y_i))` | controlled-unit | setpoint, process value |
| `settling_time:v1` | first virtual time from which `|y_i-r_i| <= 1 controlled-unit` for all remaining points | seconds | setpoint, process value, time |
| `control_effort:v1` | `Σ(i>0) |u_i| (t_i-t_{i-1})` | control-unit seconds | control output, time |
| `actuation_count:v2` | count of trace points with `actuator_state != HOLD` | count | actuator state |

The settling band is explicit and versioned in the extractor definition; it is
not inferred from a chart. `energy_cost`, `constraint_violations`,
`stability_score`, `response_time` and `resource_consumption` remain
`NOT_AVAILABLE`: this phase does not invent energy, process safety, or stability
models. For historical results with no trace, only the M6.2 aggregate
`actuation_count` fallback remains available and records that provenance.

`actionable_recommendation_count` is not treated as physical actuation. New
trace-backed `actuation_count` counts simulated non-HOLD control decisions;
neither represents hardware effect.

## Replay, evaluation and comparison

Replay captures process value from the frozen telemetry record, static setpoint
from the frozen binding, evaluator applied control signal and action kind. It
does not compute final KPIs. M6.2 evaluates the trace later; M6.3 compares the
resulting immutable metrics and its pure Pareto function operates only within a
compatible profile/engine/schema cohort.

The E2E fixture persists three four-point simulated water-level trajectories.
It derives five independent available KPIs per evaluation. The first two form a
real metric trade-off: one has lower tracking error while the other has lower
effort (and differs in trajectory extrema/settling), so M6.3 returns
`TRADE_OFF`; Pareto is calculated without persistence or ranking.

## Security and operation

Trace persistence is internal to completed simulation replay. There is no
manual trace mutation endpoint, no UI, no new permission, no broker publish and
no access to outbox, dispatch, MQTT or physical adapters. Result/evaluation
reads retain project scope and existing OAuth/RBAC enforcement. Audit records a
compact `SIMULATION_TRACE_CREATED` event containing trace hash, point count and
schema only. `physical_effects=false` and `REAL_ACTUATION_READY=NO` remain
invariant.
