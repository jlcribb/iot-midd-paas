# MIDD-IOT — GDSS-003
## Governed Dynamic Simulation Runtime Foundation
### Dynamic Semantics v0.1

**Version:** `v0.1`
**Status:** `PROPOSED_FOR_REVIEW`
**Implementation:** `NOT_YET_AUTHORIZED`
**Baseline:** `dade8e6d490ea3adc88aac0353c2e72fee2df47b`
**Alembic baseline:** `0040`

## Semantic model

`DynamicModelBinding` supplies temporal meaning without editing the declarative model. A GDSS-001
Variable with computational role `STATE` is only a candidate state; it becomes a v1 dynamic state
when an executable binding references it. A rate is an explicit relationship among a state, a
GDSS-001 Formula and its output Variable. Parameters and algebraic auxiliaries are also explicit.

```text
syntax != dynamic role
dynamic role != epistemic kind
STATE != Forrester STOCK
RATE != Forrester FLOW
```

All bound artifacts must belong to one exact `SystemModelVersion`. Cross-version references,
duplicate outputs, missing bindings and inferred roles are invalid.

## Dimensional rules

Let `T` be the seven-vector time dimension. For every bound state `x` and rate `r`:

```text
dimension(r) = dimension(x) - T
dimension(r × dt) = dimension(x)
```

Time and values explicitly use `GDSS_UNIT_CONVERSION_V2`; `second@1` supplies the canonical TIME
interval and all V1 units remain semantically identical. Catalog selection participates in input
identity; no implicit latest version exists. GDSS-002 conversion rules remain authoritative. Affine absolute states may be
updated only by affine intervals; absolute + absolute and other prohibited affine operations remain
invalid. Missing dimension is not dimensionless.

## Algebraic semantics

Algebraic bindings reuse governed GDSS-002 formulas and the same safe expression language. Their
dependency graph is constructed from exact symbols, deduplicated and sorted. A deterministic
topological order evaluates auxiliaries from the current state snapshot and explicit parameters.
An SCC representing an instantaneous algebraic loop terminates before stepping with
`INSTANTANEOUS_ALGEBRAIC_LOOP_UNSUPPORTED`.

State-mediated feedback is legal because the prior state breaks the same-step cycle. Simulation
does not make arbitrary algebraic cycles solvable.

## Time semantics

The canonical trajectory coordinate is a non-negative integer `step_index`. Configuration contains
finite canonical binary64 `start`, positive `step`, integer `stepCount` and an exact TIME unit.

```text
t(i) = start + i * step
i in [0, stepCount]
```

The coordinate is derived independently for each index. Wall clock, observation timestamps and
device timestamps have no role. Step 0 records initial state; N transitions produce N+1 points.

## EXPLICIT_EULER_V1

For immutable pre-step snapshot `S(k)`:

1. Evaluate every algebraic binding from `S(k)` and parameters.
2. Evaluate every rate from that same snapshot and algebraic environment.
3. Validate dimensions and finite values.
4. Compute every candidate `x_i(k+1) = x_i(k) + r_i(k) * dt`.
5. Validate finite candidates and governed constraints.
6. Commit all candidates as one logical snapshot.

No candidate becomes visible to another rate at the same step. Stable symbol ordering controls
evaluation and serialization, never object insertion or database row order. Any arithmetic change
requires a successor solver version.

## Constraints

V1 uses `constraintPolicy = FAIL_RUN`. Applicable GDSS-001 constraints are referenced explicitly by
the binding and evaluated against next-state candidates before logical commit. Violation emits
`CONSTRAINT_VIOLATION`, preserves an incomplete diagnostic trace and fails the run. It never clamps,
repairs or reclassifies a value. More permissive or event-like policies require later versioned
semantics.

## Numerical status versus scientific meaning

Finite arithmetic and solver completion establish computational execution only. They do not prove
stability, convergence for arbitrary models, physical plausibility or scientific validity.
Numerical approximation error is measured against analytical references; model error requires
external scientific evidence and is outside GDSS-003.

## Reference systems

Reservoir fixture:

```text
dV/dt = Qin - Qout
V(t) = V0 + (Qin - Qout)t
```

Constant derivative makes Euler exact within binary64 semantics and verifies units, indexing and
simultaneous transition machinery.

Thermal fixture:

```text
dT/dt = -k(T - Tambient)
T(t) = Tambient + (T0 - Tambient)exp(-kt)
```

Runs at decreasing `dt` must demonstrate convergence toward the analytical solution without making
a scientific-validation claim. A later hydroponic volume fixture may use the identical core.

## Forrester boundary

Core provides state, rate, algebraic, parameter, time, solver and trajectory semantics. A future
System Dynamics package may explicitly map STOCK, FLOW, AUXILIARY, CONNECTOR, SOURCE and SINK.
Those terms never become universal GDSS ontology, and no mapping is inferred.

## Epistemic and authority boundary

Initial provenance remains attached to inputs. Every evolved state is `SIMULATED`, not observed or
predicted. Runs are not experiments, counterfactual claims, Digital Shadows or Digital Twins.
Simulation produces no recommendation and authorizes nothing physical.
