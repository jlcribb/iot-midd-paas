# M6.2 — Deterministic Experiment Evaluation Engine

M6.2 evaluates one immutable M5 `SimulationResult` against one immutable M6.1
evaluation-profile version. It is simulation evidence only: it does not compare
evaluations, rank candidates, recommend policy changes, publish a message, or
reach an operational delivery component.

## Data model and identity

`control_experiment_evaluations` records the project, M5 run/result, profile
ID/version, lifecycle status, score, constraint summary, engine/schema version
and `evaluation_hash`. `control_experiment_evaluation_metrics` stores the raw
KPI, availability, normalized value, weighted contribution and snapshots of
the metric direction, normalization configuration and profile constraint.

The unique `(simulation_result_id, evaluation_profile_id, engine_version)`
identity makes repeated evaluation idempotent. The first request persists the
evaluation, metric evidence and one audit record; an equivalent retry returns
that same row. Evaluations are immutable at database level.

The hash is SHA-256 over canonical JSON. It includes the M5 result fingerprint,
profile ID/version, metric versions/configurations, raw values, weights,
constraint evidence, score, engine version and schema version. It excludes IDs
generated for the evaluation, actor and wall-clock timestamps. Numeric values
are canonicalized to nine decimal places only for persisted/hash evidence;
calculation precedes that boundary.

## KPI extraction and availability

M5 currently persists aggregate result counts and trace labels, not process
value/setpoint/control vectors. The extractor can therefore derive only
`actuation_count` rigorously from `actionable_recommendation_count`.

All other initial catalog metrics are persisted as `NOT_AVAILABLE`, with a
reason, until a later M5 result schema supplies the required evidence. In
particular, `failed_domain_event_count` is **not** silently reinterpreted as a
safety-constraint violation. `MISSING`, `NOT_APPLICABLE` and `INVALID` remain
separate availability states for future extractors. Required unavailable data
produces `NOT_EVALUABLE` and never becomes zero or a reweighted score.

## Normalization v1

All definitions are explicit in `control_evaluation_metrics.normalization_config`
with `schema_version=1`; the engine validates method, direction and parameters.
No candidate-relative bounds or hidden defaults are used.

| Direction/method | Formula (clipped to `[0,1]`) |
| --- | --- |
| `MINIMIZE` / `MIN_MAX` | `(value - worst) / (best - worst)` |
| `MAXIMIZE` / `MIN_MAX` | `(value - worst) / (best - worst)` |
| `TARGET` / `TARGET_DISTANCE` | `1` inside tolerance; otherwise linear distance to `worst_distance` |
| `RANGE` / `RANGE_DISTANCE` | `1` in range; linear decay across `soft_margin` outside |

For `MINIMIZE`, `best < worst`; for `MAXIMIZE`, `best > worst`. The initial
catalog parameters are persisted by migration `0021`: count-like actuation is
`best=0, worst=100`; timing uses `0..3600`; normalized stability uses
`worst=0, best=1`. They are governed catalog data, not runtime constants.

The score is `Σ(weight × normalized_value)`. Required availability is strict.
If only optional metrics are unavailable, the status is
`COMPLETED_WITH_WARNINGS` and the score is the un-renormalized partial sum; it
must not yet be used for cross-experiment comparison.

## Constraints

M6.2 introduces explicit profile constraints rather than interpreting arbitrary
metadata JSON. A profile can declare one `MINIMUM`, `MAXIMUM` or `RANGE`
constraint per profile metric, with optional `critical=true`. Constraint results
are `SATISFIED`, `VIOLATED`, `UNKNOWN` or `NOT_APPLICABLE` and are independent
from performance score. A critical violation may coexist with a high score.

## Governed API

```text
POST /api/control/evaluation/projects/{projectId}/evaluations
GET  /api/control/evaluation/projects/{projectId}/evaluations
GET  /api/control/evaluation/projects/{projectId}/evaluations/{evaluationId}
```

The POST body is `{ "simulationResultId": "…", "evaluationProfileId": "…" }`.
Reads require OAuth-authenticated `view_dashboard`; evaluation creation requires
project-scoped `edit_policies`. Both result and profile are loaded with the URL
project scope, so cross-project IDs are not disclosed. Creation writes the
compact `EXPERIMENT_EVALUATION_CREATED` audit envelope with simulation context
and `physical_effects=false`.

## Safety boundaries and current limits

This engine has no UI and no access to operational outbox, publisher, transport,
RabbitMQ, MQTT, adapters or physical actuation. `REAL_ACTUATION_READY=NO` and
`PHYSICAL_EFFECTS=false` remain invariant.

M6.3 may compare already persisted evaluations. It must not reinterpret
`NOT_EVALUABLE` as score zero, alter M6.2 hashes, or mutate profiles/results.
