# GDSS-005 — Architecture Decision Record

Status: `PROPOSED`
Decision: `GOVERNED_OBSERVATION_AND_DETERMINISTIC_CALIBRATION_FOUNDATION`

## Context

GDSS-001 through GDSS-004 govern declarative models, safe mathematics, deterministic simulation and
comparative experimentation. None admits physical observation evidence or estimates parameters from
it. Treating telemetry rows as observations or representing fitting as an experiment would collapse
source provenance, temporal semantics, data roles and scientific authority.

## Decision

Introduce two new aggregates and one execution boundary:

1. `ObservationDatasetVersion` admits a finite immutable set of governed observation series and
   points backed by immutable external source evidence references.
2. `CalibrationDesignVersion` binds exact model/binding/dataset versions, mappings, parameters,
   objective, grid search and resource profile.
3. `CalibrationExecutionAttempt` evaluates the finite grid through GDSS-003 and produces immutable
   parameter-estimate, residual and adequacy evidence.

The aggregates are project-scoped and independently lifecycle-governed. Published source models,
bindings and datasets are never mutated.

## Observation decisions

- A raw payload is not copied by default. GDSS persists provider kind, opaque source key, media type,
  byte length and SHA-256, plus instrument/channel provenance.
- `MeasurementChannel` and `MeasurementContext` are contract sections of `ObservationSeries`, not
  independent aggregates in V1.
- Quality and uncertainty are value objects on a point. Transformation history is absent in V1;
  derived observation datasets require a future versioned transformation vocabulary.
- V1 accepts physical and synthetic evidence, always with distinct `evidenceKind`.
- Measurement time participates in dataset identity. Ingestion and processing timestamps are audit
  metadata and do not participate in computational identity.

## Temporal and alignment decisions

An alignment maps an exact observation series to an exact model state/algebraic output and declares
the observation origin, simulation start, time unit, temporal window, inclusion policy and mapping.
V1 requires exact coordinates after governed unit conversion. Irregular observation sampling is
allowed only when every included timestamp equals a trajectory coordinate. Duplicate timestamps,
ambiguous time zones, missing clock-source identity and non-exact coordinates fail closed.

No interpolation, resampling or extrapolation is available in V1. This keeps alignment auditable and
prevents a hidden numerical method from entering calibration identity.

## Calibration decisions

- Definition: estimation of explicitly designated model parameters from one explicitly designated
  calibration dataset under a versioned objective and deterministic finite grid.
- Search: `FINITE_GRID_SEARCH_V1` only; full enumeration; canonical parameter order; canonical value
  order; lexicographic tie-break on canonical parameter vectors.
- Objectives: `RMSE_V1` and `WEIGHTED_NORMALIZED_MSE_V1` only.
- Formal identifiability is `NOT_ASSESSED`. Equivalent-minimum and flat-objective diagnostics do not
  confer identifiability.
- Calibration dispatches GDSS-003 directly. GDSS-004 remains unchanged and is not a calibration
  façade.
- Candidate simulation failure is recorded deterministically. Design policy declares whether any
  failure fails the execution (`FAIL_FAST`) or makes that candidate infeasible (`INFEASIBLE_CANDIDATE`).

## Persistence decision

Migration `0043` is required because immutable dataset lineage, point-level quality/time evidence,
calibration definitions, candidate-to-simulation links and human estimate review are
governance-critical relationships. JSON artifacts alone cannot enforce ownership, cardinality,
append-only history or cross-project integrity.

`0043` is proposed only; it is not created by this phase. The normalized table proposal is in the
contracts document. Large canonical dataset/residual/result representations are content-addressed;
relational rows remain the authoritative governance projection.

## Lifecycle decision

Observation dataset and calibration design use separate:

```text
DRAFT -> VALIDATED -> PUBLISHED -> DEPRECATED
```

`VALIDATED` means contract/provenance consistency. `PUBLISHED` means immutable and admissible for
new execution. Neither state means true data or a validated scientific model. Execution uses
append-only `ACCEPTED -> RUNNING -> terminal` events, where terminal is `COMPLETED`,
`COMPLETED_WITH_WARNINGS`, `FAILED` or `ABORTED`.

## Rejected alternatives

| Alternative | Reason rejected |
|---|---|
| treat telemetry rows as observations | implicit source, quality, time and admission authority |
| query latest sensor values during execution | non-reproducible and live-runtime coupling |
| store raw telemetry inside GDSS | creates a second raw-data authority |
| represent calibration as GDSS-004 sweep | erases fitting objective, data role and estimate semantics |
| arbitrary objective expression | expands executable language and dimensional ambiguity |
| stochastic optimizer | seed/platform/dependency and resource-governance burden |
| interpolate by default | hidden numerical assumption changes evidence |
| overwrite model parameters | destroys published model identity and history |
| use calibration fit as validation | data leakage and invalid generalization claim |

## Consequences

Positive consequences are exact provenance, reproducibility, deterministic resource bounds and a
clear successor-model proposal boundary. Costs are a new migration, explicit dataset admission,
point-level storage, calibration-specific orchestration and deliberately narrow V1 mathematics.

## Authority statement

```text
Control Engine dependency: NONE
DTE dependency:            NONE
MQTT dependency:           NONE
Live telemetry dependency: NONE
Physical actuation:        NONE
Prediction authority:      NONE
Recommendation authority:  NONE
Scientific authority:      NONE
```

What physical action can GDSS-005 authorize? `NOTHING.`
