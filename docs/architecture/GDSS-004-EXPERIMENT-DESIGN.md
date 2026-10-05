# GDSS-004 — Experiment Design and Scenario Expansion

Status: `PROPOSED`
Expansion semantics: `GDSS_EXPERIMENT_EXPANSION_V1`
Implementation: `NOT_AUTHORIZED`

## Design objective

An `ExperimentVersion` declares one reproducible computational question over one exact GDSS-003
base simulation specification. It separates deliberately varied factors from controlled inputs and
defines the complete scenario universe before execution.

```text
ResearchQuestion
+ optional Hypothesis
+ exact BaseSimulationManifest
+ ExperimentalFactors
+ ControlledInputs
+ MetricDefinitions
+ ComparisonDefinitions
+ CompletenessPolicy
= immutable ExperimentDesign
```

A hypothesis is descriptive context, not fact. Simulation consistency with a hypothesis is neither
empirical confirmation nor scientific validation.

## Closed relevant-input universe

GDSS-004 v1 may vary only:

```text
PARAMETER
INITIAL_CONDITION
TEMPORAL_CONFIGURATION
```

Temporal targets are closed to fields already owned by the GDSS-003 manifest: `start`, `step`,
`stepCount` and time-unit identity. A target is addressed by canonical kind and identity, never by
array position.

Formula, topology, state-variable set, dynamic binding, model version, solver or semantic-version
changes are not overrides. Comparing those requires a future model-comparison capability.

## Validation before expansion

Validation performs, in order:

1. exact project and ExperimentVersion ownership;
2. published base GDSS-003 model and binding identity resolution;
3. closed semantic-version resolution;
4. unique factor keys and canonical target identities;
5. finite non-empty factor domains;
6. no duplicate canonical values within a factor;
7. factor values compatible with governed unit/dimension/quantity semantics;
8. factors and controlled inputs are disjoint;
9. every relevant input is classified as varied or controlled;
10. every `expectedPreviousValue` equals the exact governed base value;
11. metric and comparison definitions are valid and bounded;
12. Cartesian scenario count and aggregate resource estimates are within
    `GDSS_EXPERIMENT_LIMITS_V1`.

Failure occurs before persistence or dispatch.

## Canonical factor and value order

Factor order is lexicographic over `(targetKind, canonicalTargetIdentity, factorKey)`. Each value is
canonicalized into governed unit identity and canonical binary64 representation. Value order is the
explicit author-declared order after duplicate canonical values are rejected. Database, map and UUID
order are irrelevant.

The last factor in canonical factor order varies fastest. For `F1=[a,b]`, `F2=[x,y,z]`, the ordered
product is `(a,x), (a,y), (a,z), (b,x), (b,y), (b,z)`. Scenario ordinal is the zero-based index in
this product and is hash-bound. Worker scheduling never changes it.

## Baseline and explicit scenarios

A comparison plan that uses a baseline requires exactly one explicitly marked `BASELINE` scenario.
No ordinal implies baseline. Its factor combination is declared and must belong to the Cartesian
domain.

`ALTERNATIVE` and `COUNTERFACTUAL` are explicit classifications. A counterfactual additionally
names its reference scenario and remains a simulated world, never observed history.

An explicitly authored scenario may supplement the Cartesian set only when it uses the same closed
override contract, is counted during preflight and has deterministic canonical position after the
Cartesian scenarios ordered by canonical scenario key. Runtime-created scenarios are forbidden.

## Materialization algorithm

For each ordered factor combination:

1. copy the exact immutable base manifest;
2. create one authorized override per factor target;
3. verify each expected previous value against the base;
4. apply overrides by canonical target identity;
5. prove every controlled input is byte-semantically unchanged after canonicalization;
6. prove all relevant differences are explained by authorized overrides;
7. validate the resulting manifest under GDSS-003 preflight contracts;
8. compute the GDSS-003 `simulation_input_hash` using GDSS-003 authority;
9. compute `scenario_definition_hash` under the GDSS-004 domain;
10. assign the immutable canonical ordinal.

Any unexplained difference is `UNDECLARED_VARIATION`. No scenario is dispatched during this
algorithm.

## Materialize-before-dispatch gate

```text
validate complete design
  -> expand complete finite universe
  -> canonicalize and hash all scenarios
  -> persist all scenarios and execution manifest
  -> COMMIT Transaction A
  -> dispatch may begin
```

The system must prove Transaction A committed before calling GDSS-003. A crash before commit leaves
no dispatchable experiment execution. A crash after commit leaves a recoverable, fully known
scenario universe.

## Controlled-condition proof

For each relevant input `r`:

```text
if r is a factor target:
    materialized(r) must equal the factor value
else:
    materialized(r) must equal base(r)
```

The proof is canonical evidence and may be recomputed. Unit-equivalent author input is normalized
only through the governed GDSS unit catalog selected by the base manifest. No private conversion
exists.

## Idempotent materialization

`(experiment_execution_attempt_id, scenario_definition_hash)` is unique. Re-materializing the same
design produces the same ordered hashes. A persisted ordinal/hash mismatch is an integrity failure,
not a successor scenario.

## Resource preflight

Before Transaction A, calculate and bound design bytes, factors, values, Cartesian cardinality,
explicit scenarios, overrides, controlled inputs, artifact sizes, metric/comparison operations,
trajectory point/byte upper bounds and maximum dispatch/retry work. Arithmetic overflow fails
closed. V1 has no generators, random sampling, adaptive factors or scenario discovery.

## Reservoir reference flow

```text
dV/dt = Qin - Qout
Qout = 8
factor Qin = [8,10,12,14]
explicit baseline Qin = 10
controlled: Qout, V0, start, step, stepCount, timeUnit
```

Four scenarios are committed before four idempotent GDSS-003 dispatches. `FINAL_VALUE(V)` is read
from each verified trajectory and comparisons explicitly reference Qin=10. The analytical solution
is future test evidence, not empirical authority.

## Thermal reference flow

```text
dT/dt = -k(T - Tambient)
factor k = [0.01,0.02,0.04,0.08]
metrics: FINAL_VALUE(T), TIME_TO_THRESHOLD(T)
classification: SENSITIVITY_EXPLORATION
```

This is neither calibration nor optimization. Temporal compatibility is required before comparing
results.

## Hydroponics reference domain

Hydroponic examples may be packaged after neutral fixtures. Their terms must not enter core
contracts, enums or algorithms. The core knows governed symbols, dimensions, factors, scenarios,
metrics and comparisons.

## Exclusions

No adaptive search, random generation, Monte Carlo process, model comparison, calibration,
optimization, AI-selected scenario, telemetry-derived override, control-policy generation or
physical action is part of v1.
