# Experiment comparison and Pareto analysis (M6.3)

M6.3 compares immutable M6.2 `ExperimentEvaluation` evidence only. It does not
rerun a simulation, extract a KPI, rank candidates, recommend an action, or
touch operational outbox/transport paths.

## Semantic cohort and compatibility

`checkComparisonCompatibility()` requires the same project, evaluation profile
identifier and version, evaluation schema and engine version, and the same
metric code/version set. `NOT_EVALUABLE`, `INVALID_INPUT`, and pending evidence
produce an immutable `INCOMPARABLE` comparison, never an implicit loss. Project
scope is enforced before either evaluation is loaded.

The directional pair is explicit: baseline -> candidate. Normalized values use
the M6.2 convention that higher is better. The versioned policy stores epsilon
`0.000001`; deltas at or inside epsilon are `EQUIVALENT`. Missing optional
evidence is recorded as `UNAVAILABLE`, excluded from dominance, and reflected
by `coverage_ratio` instead of being imputed.

## Constraints and Pareto

Metric relation and constraints are independent. A newly introduced critical
constraint violation prevents a global `BETTER` relation and yields
`TRADE_OFF`, even when normalized metrics otherwise dominate. Pareto is a pure
function, is not persisted in M6.3, and accepts only one compatible semantic
cohort. Non-evaluable or incompatible members are returned as explicit
exclusions; they are not silently mixed into a front.

## Persistence, identity, and audit

Migration `0022` creates immutable `control_experiment_comparisons` and metric
evidence rows. `comparison_hash` canonically includes ordered baseline and
candidate evaluation hashes, engine/schema, epsilon policy, relations,
coverage, and constraint semantics. It intentionally excludes row IDs, actor,
and timestamps. Repeating the same request returns the existing comparison and
does not duplicate `EXPERIMENT_COMPARISON_CREATED` audit. Reversing the ordered
pair has a different identity.

## Operations

`GET` comparison endpoints require `view_dashboard`; `POST` requires
`edit_policies`. The capability is simulation-only and stores
`physical_effects_allowed=false`. Current M6.2 runtime evidence exposes only
`actuation_count`; broader Pareto fronts remain mathematically valid but await
future immutable KPI evidence. A comparison delivery failure is not an outbox
or dispatch-DLQ event: M6.3 does not publish broker messages.
