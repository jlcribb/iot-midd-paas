# GDSS-005 — Calibration Semantics

Status: `PROPOSED`

## Definition and exclusions

Calibration is estimation of explicitly designated model parameters from an explicitly designated
calibration dataset under an explicitly versioned objective and search method.

```text
CALIBRATION != PARAMETER SWEEP
CALIBRATION != SENSITIVITY ANALYSIS
CALIBRATION != EXPERIMENT COMPARISON
CALIBRATION != VALIDATION
CALIBRATION != OPTIMAL CONTROL
```

The output is a parameter estimate set and scoped fit evidence. It is not an observed parameter,
true parameter, model mutation, prediction, policy recommendation or actuation authorization.

## Design preflight

Before accepting an execution, the service must prove:

1. exact project ownership for published model, binding, observation dataset and calibration design;
2. model and binding hashes match immutable source evidence;
3. dataset artifact/projection hash agreement and published lifecycle;
4. exactly one `CALIBRATION` dataset assignment;
5. explicit series-to-variable mappings and exact alignment manifests;
6. compatible quantity, dimension, unit and affine semantics;
7. one to four calibrated parameters with finite bounded candidate grids;
8. no parameter overlap between calibrated and fixed sets;
9. grid Cartesian product is finite and at most 256;
10. objective, search, failure policy, adequacy criterion and resource profile are known versions;
11. no validation/holdout evidence influenced the design;
12. canonical manifest bytes match `calibrationDesignHash`.

Failure occurs before any GDSS-003 dispatch.

## Deterministic execution

Transaction A persists the complete candidate universe, immutable design manifest and `RUNNING`
event before dispatch. Workers claim candidates with bounded concurrency and dispatch GDSS-003 using
a domain-separated idempotency key derived from project, calibration design hash, parameter-vector
hash and simulation-input hash.

Each candidate produces exactly one governed terminal classification:

```text
SUCCEEDED
INFEASIBLE
SIMULATION_FAILED
NOT_DISPATCHED_ABORTED
```

Successful candidates must bind exact simulation attempt, input, result and trajectory hashes.
Objective evaluation reads verified trajectory evidence and the immutable alignment manifest. It
does not alter GDSS-003 evidence or observation data.

After all candidates are classified, selection orders feasible finite objective values ascending
and uses canonical parameter-vector bytes as the only tie-break. Transaction B stores the estimate
set, selected residual artifact, adequacy assessment, deterministic diagnostics and one terminal
result atomically. Retry recognizes exact existing evidence.

## Candidate failure policy

```text
FAIL_FAST
INFEASIBLE_CANDIDATE
```

`FAIL_FAST` terminates on the first candidate simulation/objective failure in canonical candidate
order. `INFEASIBLE_CANDIDATE` records the failure and continues; if no feasible candidate remains,
the result fails `NO_FEASIBLE_PARAMETER_SET`. Worker completion order never determines selection or
failure identity.

## Objective semantics

V1 supports:

- `RMSE_V1`: one output, unit-bearing, directly interpretable;
- `WEIGHTED_NORMALIZED_MSE_V1`: multi-output, dimensionless with predeclared scales and weights.

Absolute residual uses observation minus simulation after explicit governed conversion. Squared
errors are accumulated in canonical series/point order using the selected finite binary64
arithmetic contract. No objective may use post-run normalization, inferred weights, arbitrary code,
uncertainty-as-variance, missing-as-zero or non-finite values.

The identical precomputed match set is used for every candidate. This prevents candidates from
improving their score by causing different points to disappear.

## Search and identifiability

`FINITE_GRID_SEARCH_V1` enumerates the canonical Cartesian product. It is exhaustive inside declared
bounds but makes no claim about values between grid points or outside bounds. Coordinate search and
generic bounded optimization are deferred because they add convergence, step schedule and local
minimum semantics without being needed by the neutral V1 fixtures.

V1 reports `NOT_ASSESSED` for identifiability. The runtime may emit:

```text
MULTIPLE_EQUIVALENT_MINIMA
OBJECTIVE_SURFACE_FLAT_ON_GRID
BOUNDARY_ESTIMATE
```

These are computational diagnostics, not `IDENTIFIABLE`, `WEAKLY_IDENTIFIABLE` or
`NON_IDENTIFIABLE` scientific findings.

## Dataset roles and leakage

The role vocabulary is:

```text
CALIBRATION
VALIDATION
HOLDOUT
EXPLORATORY
```

GDSS-005 consumes only `CALIBRATION`. Validation and holdout are reserved assignments for a future
independent assessment phase. Independence requires disjoint transitive source-point lineage and
declared windows. Hash equality, shared source records, window overlap or derived-data ancestry
overlap defeats independence.

The following design inputs are considered calibration decisions and may not be selected using
validation/holdout results: parameter list, bounds, grid, mapping, window, missing policy,
normalization, weights, objective, adequacy threshold and tie interpretation. If provenance cannot
prove non-use, no independent validation claim may be emitted.

## Parameter estimates and successor models

Each estimate preserves parameter identity, prior value, estimated value, unit, bounds, grid,
design/dataset/alignment hashes, objective/search versions, model/binding identities, execution and
selected GDSS-003 evidence.

An authorized reviewer may record `ACCEPT_FOR_SUCCESSOR_PROPOSAL` or `REJECT`. Acceptance means only
that a separate future workflow may construct a draft successor model version. It never overwrites
the published source version, changes the binding, activates a policy or validates the model.

## Adequacy

Optional criteria must be declared before execution. For example, an RMSE threshold has the output
quantity's dimension and exact unit; a normalized-MSE threshold is dimensionless. The assessment
compares the selected objective with that criterion and reports one closed conclusion.

```text
LOW_CALIBRATION_ERROR != LOW_OUT_OF_SAMPLE_ERROR
ACCEPTABLE_UNDER_DECLARED_CRITERIA != MODEL_VALID
CALIBRATED_MODEL != PREDICTIVE_MODEL
```

Without independent data GDSS-005 cannot assess generalization or prediction.

## Resource profile

Proposed `GDSS_CALIBRATION_LIMITS_V1`:

| Dimension | Limit | Rationale |
|---|---:|---|
| source references per dataset | 16 | bounded multi-file admission |
| observation series per dataset/design | 8 | small multi-output calibration |
| points per series | 10,001 | matches GDSS-003 maximum trajectory points |
| total dataset points | 80,008 | eight maximum-length series |
| calibrated parameters | 4 | keeps grid interpretation tractable |
| fixed parameter overrides | 32 | aligned with bounded manifest inputs |
| grid values per calibrated parameter | 16 | finite reviewable axis |
| materialized candidates | 256 | matches GDSS-004 scenario ceiling |
| GDSS-003 simulation executions | 256 | one per candidate |
| concurrent simulations | 8 | matches proven GDSS-004 concurrency |
| dispatch attempts per candidate | 3 | matches governed retry precedent |
| matched pairs per candidate | 80,008 | cannot exceed admitted dataset |
| total objective operations | 25,000,000 | bounds 256-candidate aggregation above 20.48M pairs |
| dataset canonical artifact bytes | 33,554,432 | two GDSS-003 trajectory-artifact ceilings |
| residual artifact bytes | 33,554,432 | selected multi-series paired evidence only |
| total calibration artifact bytes | 67,108,864 | manifest, selected residual and result |
| deterministic diagnostics | 512 | bounded candidate and terminal diagnostics |
| wall execution duration | 900 seconds | provisional 15-minute operational ceiling |

Every counter is checked before exceeding the bound. The 900-second and byte limits are proposed
for benchmark confirmation; changing accepted values requires `GDSS_CALIBRATION_LIMITS_V2`.

## Reservoir reference case

Model:

```text
dV/dt = Qin - Qout
```

Fixture:

1. choose declared synthetic truth `Qout*`;
2. use GDSS-003 to generate `V(t)` at exact fixed coordinates;
3. export a distinct immutable source artifact labeled `SYNTHETIC_OBSERVATION`;
4. admit a dataset series for volume with exact unit, time and zero-or-declared synthetic
   measurement uncertainty;
5. calibrate `Qout` with a finite grid that contains `Qout*` and `RMSE_V1`;
6. verify the selected grid estimate equals `Qout*` under the noise-free fixture;
7. retain a disjoint synthetic window/source fixture as holdout boundary evidence, not empirical
   validation.

The test proves computational recovery and provenance, not physical or scientific validity.

## Thermal reference case

Model:

```text
dT/dt = -k(T - Tambient)
```

Fixture:

1. select declared synthetic `k*`, initial temperature and ambient temperature;
2. generate exact `T(t)` evidence and label it synthetic;
3. assign an early, explicit window to `CALIBRATION`;
4. map temperature series to the exact model state with explicit kelvin identity;
5. evaluate a finite `k` grid using `RMSE_V1`;
6. recover `k*` when present in the grid;
7. reserve a non-overlapping later window/source lineage for a future holdout assessment.

Even perfect recovery is not proof that the thermal law predicts a physical system.

## Human and AI boundary

AI may propose mapping, bounds, grid, objective or interpretation. The proposal has no execution
authority. Authorized humans must admit observation evidence, validate and publish the design, run
the calibration, and separately review the estimate. `AI_PROPOSED`, `HUMAN_ACCEPTED`,
`COMPUTATIONALLY_SUPPORTED` and `EMPIRICALLY_VALIDATED` remain distinct.
