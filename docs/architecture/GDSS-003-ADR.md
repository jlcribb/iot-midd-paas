# MIDD-IOT — GDSS-003
## Governed Dynamic Simulation Runtime Foundation
### Architecture Decision Record v0.1

**Version:** `v0.1`
**Status:** `PROPOSED_FOR_REVIEW`
**Implementation:** `NOT_YET_AUTHORIZED`
**Baseline:** `dade8e6d490ea3adc88aac0353c2e72fee2df47b`
**Alembic baseline:** `0040`

## Decision

GDSS-003 introduces a domain-neutral, deterministic simulation architecture above GDSS-001 and
GDSS-002. It does not modify the GDSS-001 model contract. An independently versioned
`DynamicModelBinding` maps one exact `SystemModelVersion` to dynamic roles. Execution is represented
by `GDSSSimulationExecution`, never by the existing Control Engine `SimulationRun`.

The normative v1 semantic is `DETERMINISTIC_CONTINUOUS_TIME_V1` with solver
`EXPLICIT_EULER_V1`, fixed step, integer `step_index`, binary64 numeric semantics and simultaneous
state updates. Every input is explicit and every output is `SIMULATED` with physical authority
`NONE`.

## Repository evidence

- GDSS-001 persists strict `Variable`, `Parameter` and `Formula` schemas. `Variable.computational_role`
  includes `STATE`, but there is no canonical `RATE` role. `Formula` owns expression source,
  `input_refs` and `output_ref`.
- GDSS-002 exposes `GDSS_EXPR_V1`, `GDSS_EVALUATOR_V1` and `GDSS_EXPR_LIMITS_V1`; GDSS-003
  explicitly selects successor catalog `GDSS_UNIT_CONVERSION_V2` because it adds governed interval
  `second@1`. V1 remains immutable historical semantics. Evaluation remains read-only and scoped.
- Existing `control_simulation_sessions`, `control_simulation_runs` and replay services represent
  Control Engine policy replay, virtual timestamps and operational evidence. They are not GDSS
  dynamic-model execution.
- GDSS lifecycle/audit uses immutable events and `iot_schema.auditoria`; immutable execution
  evidence is an established repository convention.

## Core decisions

1. `DynamicModelBinding` is separate from `SystemModelVersion`, project-owned, immutable once
   published, versioned by successor, and content-addressed by `dynamic_binding_hash`.
2. Multiple bindings may target the same model version; each has a distinct identity and version.
3. Bindings reference only artifacts in the exact bound version. They never alter `content_hash`.
4. Roles are `STATE`, `RATE`, `ALGEBRAIC`, `PARAMETER`; role and epistemic kind are orthogonal.
5. A rate binding explicitly maps one `state_ref` to one governed `formula_ref` whose output has
   dimension `state / time`. Names never imply roles.
6. `step_index` is authoritative. `t(i) = start + i × step`; repeated timestamp accumulation is not
   canonical. `start` and `step` use canonical finite binary64 plus an exact governed time unit.
7. Step 0 is the initial snapshot. `stepCount = N` performs N transitions and yields N+1 points.
8. Algebraic formulas form an acyclic, stable-symbol-ordered DAG. Instantaneous cycles fail closed.
   Temporal units resolve explicitly under `GDSS_UNIT_CONVERSION_V2`; no latest lookup exists.
9. Every Euler rate uses the same immutable pre-step snapshot; candidates are committed together.
10. Constraint violation in v1 is `FAIL_RUN`; silent clamping and continue-on-violation are excluded.
11. Logical capability `RUN_SIMULATION` maps to scoped OAuth operator/admin roles. It grants no
    publication, control, deployment or actuation authority.
12. Identical inputs may produce multiple immutable execution attempts. Computational identity,
    attempt identity and result identity remain separate.

## Persistence decision

Select hybrid persistence: immutable relational binding/run manifests and diagnostics, with the
canonical trajectory as a content-addressed artifact referenced by hash, byte length, media type and
storage locator. `PREPARED` requests are not historical runs; execution creates an append-only
attempt. Completed and failed attempts are immutable. Failed attempts may retain an explicitly
partial artifact.

This architecture implies new persisted concepts and therefore:

```text
MIGRATION_ARCHITECTURE_DECISION = 0041_LIKELY_REQUIRED
```

Migration `0041` remains explicitly unauthorized.

## Collision decision

Namespace strategy A is selected. Canonical names use the GDSS prefix and future persistence uses
`gdss_dynamic_*` / `gdss_simulation_*`. No foreign key, service call or semantic dependency targets
`control_simulation_sessions`, `control_simulation_runs`, replay runners, `first_order.py` or the
Control Engine worker.

## Consequences and exclusions

The architecture supports reproducible fixed-step ODE execution, analytical fixtures and later
Forrester specialization. It excludes adaptive solvers, events, stochasticity, calibration,
prediction, experiments, Digital Shadow/Twin, telemetry, MQTT, DTE, Control Engine and actuation.

The following remain distinct:

```text
declared model != evaluated expression != simulated state != observed state
simulated future != predicted physical future
completed execution != scientific validation
GDSS simulation != Control Engine replay
simulation evidence != physical authority
```

## Architecture acceptance answers

1. Binding is separate to add temporal meaning without retrofitting GDSS-001 or changing its hash.
2. A state is an exact version-local Variable referenced by one `StateBinding`.
3. A `RateBinding` explicitly joins state, formula and output with rate/state-time dimensions.
4. Algebraics reuse GDSS-002 formulas and execute as a deterministic acyclic DAG per step.
5. Every initial condition is explicit, unit-bearing and provenance-bearing in the run manifest.
6. Integer `step_index` is authoritative simulation time ordering.
7. It prevents accumulated timestamp drift and gives stable identity and ordering.
8. `EXPLICIT_EULER_V1` means frozen-snapshot rates and `x_next = x + rate * dt` in binary64.
9. Rates read one immutable snapshot and all validated candidates commit together.
10. Instantaneous algebraic SCCs fail closed; no v1 algebraic-loop solver exists.
11. V1 constraint violation fails the run and never clamps values.
12. Input identity covers exact model/binding, inputs, time, solver, versions, limits and policy.
13. Result identity covers input hash, status, termination, trajectory and deterministic diagnostics.
14. Execution-attempt identity is an opaque UUID excluded from computational hashes.
15. Binding and execution manifests persist as immutable evidence.
16. Trajectories are content-addressed canonical artifacts linked from relational manifests.
17. Failed runs may retain `PARTIAL` trajectories through the last valid point.
18. Published bindings and terminal execution evidence are immutable.
19. `0041_LIKELY_REQUIRED`; migration creation remains unauthorized.
20. `RUN_SIMULATION` authorizes scoped operator/admin computational execution.
21. It authorizes no publication, prediction, experiment, control, deployment or actuation.
22. Versioned preflight limits and incremental counters bound every resource category.
23. Canonical snapshots, manifests, versions, artifacts and hashes establish reproduction.
24. Reservoir checks constant-rate correctness; thermal relaxation checks convergence.
25. Numerical error compares solver output to analysis; model error needs external evidence.
26. A future simulation coordinate is an internal model consequence, not a claim about reality.
27. A run lacks hypothesis, design, comparison and interpretation governance.
28. It has no physical identity, observation synchronization or twin lifecycle.
29. GDSS namespaces have no dependency on existing `control_*` replay concepts.
30. Simulation can authorize `NOTHING PHYSICAL`.

> A simulated trajectory is reproducible computational evidence about a governed model under
> explicit assumptions; it is neither observed reality nor authority to alter reality.
