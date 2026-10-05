# GDSS-004 — Metrics and Comparison Semantics

Status: `PROPOSED`
Metrics: `GDSS_EXPERIMENT_METRICS_V1`
Comparisons: `GDSS_EXPERIMENT_COMPARISONS_V1`
Implementation: `NOT_AUTHORIZED`

## Separation

A trajectory metric reduces one exact simulated trajectory. A comparison relates two explicitly
identified metric results. `DELTA_FROM_BASELINE` and `PERCENT_DELTA_FROM_BASELINE` are therefore not
v1 metrics.

```text
GDSS-003 trajectory
  -> TrajectoryMetricResult
  -> explicit ExperimentComparison
  -> ComparisonResult
  -> ComparativeFinding
```

All stages preserve `SIMULATION_DERIVED` provenance.

## GovernedTrajectoryReader

The reader is a read-only boundary over a GDSS-003 artifact. Before exposing points it must:

1. resolve by exact project, attempt, result and trajectory hashes;
2. verify SHA-256 against exact stored bytes;
3. require `GDSS_TRAJECTORY_NDJSON_V1` and declared byte/point counts;
4. parse the closed schema and reject duplicate or unknown fields;
5. verify final LF, canonical ordering, contiguous `stepIndex` and the N+1 contract;
6. verify every point has `SIMULATED` epistemic kind;
7. verify state symbols, unit identities, dimensions and finite binary64 values;
8. expose immutable ordered points and completeness classification.

It never repairs, rewrites or stores a second trajectory representation. Malformed or substituted
evidence fails closed.

## Metric vocabulary

```text
INITIAL_VALUE
FINAL_VALUE
MINIMUM
MAXIMUM
ARITHMETIC_POINT_MEAN
LEFT_RECTANGLE_INTEGRAL
PEAK_STEP
TIME_TO_THRESHOLD
```

`PEAK_VALUE` is removed because it would merely alias `MAXIMUM`.

Let canonical points be `p_0 ... p_N`, state value `x_i`, coordinate
`t_i = start + i * step`, and `N = stepCount`.

### INITIAL_VALUE

Return `x_0` at `stepIndex=0`. Absence of point zero is invalid trajectory evidence.

### FINAL_VALUE

Return `x_N` at maximum canonical `stepIndex`. It requires `COMPLETE` trajectory evidence unless
the metric definition names another closed completeness requirement; partial evidence is never
accepted implicitly.

### MINIMUM and MAXIMUM

Return the least/greatest finite numeric value over canonical discrete points only. There is no
interpolation or continuous-extremum claim.

### ARITHMETIC_POINT_MEAN

```text
mean(x) = (sum from i=0 to N of x_i) / (N + 1)
```

Summation is in ascending `stepIndex` under a deterministic finite binary64 accumulation algorithm
fixed by the Implementation Plan. Overflow and non-finite intermediates fail. This is not a
continuous-time or time-weighted mean. Output dimension and quantity semantics equal `x`.

### LEFT_RECTANGLE_INTEGRAL

```text
integral(x) = sum from i=0 to N-1 of x_i * step
```

It requires fixed-step GDSS-003 semantics and a complete trajectory. `N=0` yields canonical positive
zero with dimension `dimension(x) + TIME`. Accumulation follows ascending index. No trapezoid,
interpolation or hidden endpoint weighting is permitted.

Affine absolute quantities are ineligible unless governed GDSS unit semantics establish a valid
interval/canonical multiplication. GDSS-004 never invents affine algebra.

### PEAK_STEP

Peak means numeric maximum. Return the smallest canonical `stepIndex` equal to `MAXIMUM` under exact
canonical binary64 equality. Output is a dimensionless non-negative index, not time.

### TIME_TO_THRESHOLD

The definition binds a finite threshold, governed unit and one direction:

```text
AT_OR_ABOVE: x_i >= threshold
ABOVE:       x_i >  threshold
AT_OR_BELOW: x_i <= threshold
BELOW:       x_i <  threshold
```

Convert threshold through governed GDSS unit semantics, validate dimension and quantity, scan in
ascending index, and select the first qualifying point. There is no interpolation. Return the
simulation-time interval `stepIndex * step`, not absolute coordinate `start + stepIndex * step`.
If no point qualifies, return `NOT_REACHED` without a numeric value.

## Non-finite arithmetic

NaN, infinity, overflow, invalid conversion or non-finite intermediate values produce deterministic
failed/ineligible evidence. Values are never filtered or clamped. Negative zero follows the
existing canonical binary64 contract.

## Units and dimensions

Reuse the exact unit catalog version bound by GDSS-003. Results carry unit, dimension and quantity
semantics.

- Initial/final/min/max/mean retain state dimension.
- Integral adds TIME dimension.
- Peak step is a dimensionless index.
- Time to threshold returns a TIME interval.

Comparisons require compatible dimensions and quantity semantics. Subtracting affine `ABSOLUTE`
values yields an `INTERVAL` under governed GDSS semantics. Absolute-versus-interval and incompatible
affine families are ineligible. No private conversion table exists.

## Comparison vocabulary

### ABSOLUTE_DIFFERENCE

`target - reference`. Both inputs use the same metric definition and compatible dimensions and
quantity semantics. Reference converts to target governed output unit. Output retains input
dimension; affine absolute inputs produce interval semantics.

### RELATIVE_DIFFERENCE

`(target - reference) / reference`. The canonical reference must be nonzero. Output is a
dimensionless ratio. Zero yields `INELIGIBLE_REFERENCE_ZERO`, never Infinity.

### PERCENT_DIFFERENCE

`100 * (target - reference) / reference`. Eligibility matches relative difference. Output uses an
explicit versioned dimensionless percent unit. Zero reference is governed ineligibility.

### ORDERING

After governed conversion, return exactly one of:

```text
TARGET_LESS_THAN_REFERENCE
TARGET_EQUAL_TO_REFERENCE
TARGET_GREATER_THAN_REFERENCE
```

V1 uses exact canonical binary64 comparison, with no implicit tolerance or significance claim.

## Temporal comparability

Every comparison binds `GDSS_TEMPORAL_COMPARABILITY_V1`.

For `FINAL_VALUE`, `MINIMUM`, `MAXIMUM`, `ARITHMETIC_POINT_MEAN`,
`LEFT_RECTANGLE_INTEGRAL` and `PEAK_STEP`, reference and target require identical:

```text
start
step
stepCount
horizon = start + step * stepCount
time-unit identity
ordered temporal coordinates
trajectory completeness requirement
```

`INITIAL_VALUE` requires identical start coordinate and time-unit identity; later sampling and
horizon need not match. `TIME_TO_THRESHOLD` requires identical start, step, horizon, time unit,
threshold, direction and completeness requirement. V1 does not resample, interpolate or normalize.

Temporal overrides make a comparison ineligible unless these metric-specific rules still pass.

## Comparison eligibility algorithm

Before arithmetic, verify:

1. explicit reference and target scenarios exist;
2. their terminal evidence is eligible under completeness policy;
3. required metric results exist and succeeded;
4. metric definition/version hashes match;
5. trajectory/result hashes match scenario mappings;
6. dimensions, units and quantity semantics are compatible;
7. temporal policy passes;
8. relative denominator is valid;
9. operation and result remain finite and bounded.

Any failed gate emits immutable `INELIGIBLE` evidence and a deterministic diagnostic. Nothing is
silently omitted.

## Comparative finding

A finding renders one exact comparison, binding experiment version/execution, definition hashes,
reference and target, metric evidence, comparison value, units/dimension, eligibility and
`SIMULATION_DERIVED` provenance.

Acceptable: “Within ExperimentVersion E1, S2 produced a simulated final volume 12.4% greater than
explicit baseline S0.”

Forbidden: a physical prediction, optimality claim, calibration claim or operational recommendation.
