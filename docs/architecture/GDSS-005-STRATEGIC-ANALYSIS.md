# GDSS-005 — Strategic Analysis

Status: `PROPOSED`
Prompt: `MIDD-GDSS-P014`
Baseline: `79f5fe8efde94de817d7e3403e234d81124e632a` / Alembic `0042`

## Strategic answer

Midd-IoT needs a new governed evidence boundary between physical measurements and dynamic-model
computation. GDSS-005 should admit immutable, explicitly sourced observation dataset versions,
align selected observation series with exact GDSS-003 trajectory coordinates, and execute bounded
deterministic parameter estimation without changing any source model, binding, dataset, simulation
or experiment.

The minimum governed chain is:

```text
external raw evidence authority
  -> ObservationDatasetVersion (OBSERVED or SYNTHETIC_OBSERVATION)
  -> explicit series-to-model mapping and exact-time alignment
  -> CalibrationDesignVersion
  -> bounded CalibrationExecutionAttempt
  -> exact GDSS-003 SimulationAttempts
  -> ParameterEstimateSet + residual evidence
  -> ModelAdequacyAssessment under declared criteria
```

Every arrow is explicit, versioned, project-scoped and hash-bound. Operational UUIDs and wall-clock
timestamps never become computational identity. No result receives predictive, recommendation,
scientific or physical authority.

## Epistemic partition

| Concept | Meaning | Explicitly not |
|---|---|---|
| raw measurement | source payload produced outside GDSS | admitted observation |
| governed observation | admitted evidence with source, time, quantity, unit, quality and provenance | telemetry row by implication |
| derived observation | successor evidence produced by a declared transformation | silent cleaning or smoothing |
| simulated value | GDSS-003 output for a model input | observation or prediction |
| parameter estimate | deterministic search result under one design | observed or true parameter |
| calibration fit | objective evidence on calibration data | independent validation |
| adequacy assessment | scoped conclusion under predeclared criteria | truth or generalization |

`MEASURED_SIGNAL != OBSERVATION != DERIVED_OBSERVATION != SIMULATED_VALUE != PREDICTED_VALUE`.
Instrument calibration metadata describes measurement evidence; model calibration estimates model
parameters. The two use different contracts and authority.

## Minimum architecture decisions

1. GDSS stores governed observation representations and immutable source references/hashes, not a
   second raw telemetry authority.
2. A dataset has identity and immutable versions. Corrections produce a successor version.
3. A series owns channel, quantity, unit, sampling and measurement context; points own measurement
   time, optional finite value, quality and uncertainty.
4. V1 alignment supports exact temporal-coordinate matches only. There is no interpolation,
   resampling or extrapolation.
5. V1 calibration uses one published dataset version and one or more explicit series mappings.
6. V1 search supports only exhaustive `FINITE_GRID_SEARCH_V1`, with at most 256 candidates and
   deterministic lexicographic tie-breaking.
7. V1 objectives are `RMSE_V1` for one output and `WEIGHTED_NORMALIZED_MSE_V1` for one or more
   outputs. Arbitrary expressions and callbacks are forbidden.
8. Calibration uses GDSS-003 directly through a separate calibration runtime. It may reuse common
   persistence/worker patterns, but it is not represented as a GDSS-004 experiment.
9. Residuals and results are content-addressed evidence. Only the selected estimate retains a full
   residual artifact; candidate rows retain bounded objective summaries and GDSS-003 identities.
10. Formal identifiability remains `NOT_ASSESSED` in V1. Flat/equivalent minima are diagnostics,
    not claims of identifiability.

## Why calibration is not GDSS-004

GDSS-004 evaluates a declared finite experiment design and reports comparative evidence. A
calibration runtime iteratively evaluates parameter candidates against one fixed observation
alignment and applies a calibration-specific objective and deterministic selection rule. Encoding
that as an experiment would blur parameter sweep, fitting, data role and adequacy semantics.
GDSS-005 should dispatch exact GDSS-003 simulations with deterministic idempotency keys while
retaining its own design, candidate, objective and estimate evidence.

## Data-role and leakage boundary

Dataset role is an assignment within an evidence study, not an intrinsic property of the dataset.
The closed role vocabulary is `CALIBRATION`, `VALIDATION`, `HOLDOUT`, `EXPLORATORY`. The V1
calibration engine consumes only `CALIBRATION`. Validation and holdout assignments establish the
future boundary but produce no validation claim in GDSS-005.

An independence claim fails closed if the transitive source-point lineage or measurement windows
overlap, if derived evidence shares a source point, or if validation evidence influenced bounds,
mapping, objective, search grid or candidate selection. A dataset used for fitting cannot also be
independent validation evidence for that calibration claim.

## Adequacy and authority

Execution success and fit assessment are orthogonal. A completed execution can conclude poor fit;
a low objective value can remain `FIT_COMPUTED_NO_ADEQUACY_CLAIM` when no criterion was declared.
Allowed conclusions are scoped to dataset, model, alignment, objective and search domain.

GDSS-005 may state:

> The declared parameter set minimized the declared objective over dataset D under design C.

It may not state that the parameter is true, the model is scientifically validated, the model
predicts future behavior, or the estimate should be deployed. There is no path from calibration
evidence to an active policy or actuation authorization.

## Compatibility audit

| Phase | Semantic change required | Reuse |
|---|---|---|
| GDSS-001 | NO | exact published SystemModelVersion, parameter and variable identities |
| GDSS-002 | NO | unit/dimension/quantity semantics and canonical finite values |
| GDSS-003 | NO | exact SimulationAttempt, input/result/trajectory hashes and runtime limits |
| GDSS-004 | NO | architectural patterns only; no experiment semantic reuse |

## Findings

### Blocking

None for an implementation-plan phase.

### Non-blocking

- PostgreSQL `timestamptz` precision and canonical epoch representation must be fixed exactly in
  the implementation plan.
- The proposed 900-second execution limit and artifact budgets require benchmark confirmation
  before implementation acceptance.
- External evidence-store reference schemes need an allowlisted provider contract; a generic URL
  must not become an implicit fetch capability.

### Future phase

- governed interpolation/resampling and transformation packages;
- statistical/probabilistic inference and uncertainty propagation;
- formal structural/practical identifiability analysis;
- independent validation workflows and predictive claims;
- Digital Shadow/Twin synchronization;
- human-governed successor-model promotion and any M7 transfer.

## Recommendation

GDSS-005 is ready for a separate implementation-plan phase. The plan must freeze canonical formats,
the exact `0043` DDL, transaction/compensation behavior, source-reference allowlist, timestamp
precision, objective arithmetic, resource thresholds and a 40-invariant test matrix before code is
authorized.
