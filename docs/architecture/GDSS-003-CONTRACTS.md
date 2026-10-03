# MIDD-IOT — GDSS-003
## Governed Dynamic Simulation Runtime Foundation
### Contracts v0.1

**Version:** `v0.1`
**Status:** `PROPOSED_FOR_REVIEW`
**Implementation:** `NOT_YET_AUTHORIZED`
**Baseline:** `dade8e6d490ea3adc88aac0353c2e72fee2df47b`
**Alembic baseline:** `0040`

All shapes are normative architecture proposals, not implemented APIs.

## Concept classification

| Concept | Purpose/owner | Classification | Persisted / mutable / versioned | Hash participation | Epistemic meaning |
|---|---|---|---|---|---|
| DynamicSemanticVersion | runtime semantics | CANONICAL | registry; immutable; versioned | input/binding | computational |
| DynamicModelBinding | project binding identity | CANONICAL | yes; identity immutable | identity reference | declarative mapping |
| DynamicModelBindingVersion | exact model mapping | CANONICAL | yes; draft then immutable; versioned | binding hash/input | declarative mapping |
| DynamicRole | binding vocabulary | CANONICAL | registry; immutable; versioned by semantic version | binding | computational |
| StateBinding | binding version | CANONICAL | within binding; immutable when published | binding/input | computational role |
| RateBinding | binding version | CANONICAL | within binding; immutable when published | binding/input | computational role |
| AlgebraicBinding | binding version | CANONICAL | within binding; immutable when published | binding/input | computational role |
| ParameterBinding | binding version | CANONICAL | within binding; immutable when published | binding/input | computational role |
| InitialCondition | execution input | CANONICAL | in manifest; immutable per attempt | input | source provenance retained |
| TemporalConfiguration | execution input | CANONICAL | in manifest; immutable | input | simulation coordinate only |
| SolverDefinition/Version | solver registry | CANONICAL | immutable; versioned | input/result interpretation | numerical method |
| SimulationResourceProfile | runtime governance | CANONICAL | immutable; versioned | input | execution bound |
| GDSSSimulationExecution | project execution attempt | PERSISTED | append-only terminal evidence | attempt ID excluded | computational evidence |
| SimulationExecutionStatus | execution | DERIVED/PERSISTED | terminal immutable | result | not governance lifecycle |
| SimulationTerminationReason | execution | DERIVED/PERSISTED | terminal immutable | result | computational outcome |
| SimulationInputManifest | execution | CANONICAL/PERSISTED | immutable | input hash source | explicit assumptions |
| GDSSSimulationTrajectory | result artifact | PERSISTED | immutable/content-addressed | trajectory/result | SIMULATED |
| SimulationPoint | trajectory | CANONICAL | immutable and index ordered | trajectory | SIMULATED |
| SimulationDiagnostic | execution evidence | DERIVED/PERSISTED | append-only/bounded | deterministic fields in result | computational diagnostic |
| SimulationResult | execution outcome | DERIVED/PERSISTED | immutable | result hash | SIMULATED or failed evidence |

`owner` means aggregate ownership, not physical authority. Optional per-step algebraic/rate traces
are `EPHEMERAL` unless retained as bounded diagnostic artifacts.

## Versions and roles

```text
DynamicSemanticVersion = DETERMINISTIC_CONTINUOUS_TIME_V1
SolverVersion          = EXPLICIT_EULER_V1
UnitConversionCatalogVersion = GDSS_UNIT_CONVERSION_V2
DynamicRole            = STATE | RATE | ALGEBRAIC | PARAMETER
```

## DynamicModelBinding

```text
DynamicModelBindingVersion {
  bindingIdentityId, bindingVersion, predecessorVersionId?
  projectId, modelVersionId, modelContentHash
  dynamicSemanticVersion
  states[], rates[], algebraics[], parameters[], constraints[]
  provenance[], dynamicBindingHash
}

StateBinding { stateRef, stateUnitRef, stateDimension, constraintRefs[] }
RateBinding  { rateRef, stateRef, formulaRef, outputRef, rateUnitRef, rateDimension }
AlgebraicBinding { algebraicRef, formulaRef, outputRef }
ParameterBinding { parameterRef }
```

Every reference resolves exactly once inside `modelVersionId`. Each state has exactly one rate
binding in v1. A formula may serve one rate only through an explicit binding. Algebraic outputs and
state refs are unique. Binding versions are immutable; a semantic change creates a successor.
Draft governance may precede publication, but only an immutable published binding version is
executable. Multiple binding identities may target the same model version.

`dynamicBindingHash = SHA-256(canonical("gdss-dynamic-binding:v1", semantic fields))`; project,
exact model identity/content hash, mappings, constraints, dynamic version and provenance identities
participate. Audit timestamps, database IDs and display ordering do not. The hash is separate from
and cannot alter GDSS-001 `content_hash`.

## Inputs and time

```text
InitialCondition {
  stateRef, value, unitIdentity, quantitySemantics?, provenance
}

ParameterInput {
  parameterRef, value, unitIdentity, quantitySemantics?, provenance
}

TemporalConfiguration {
  start: finite binary64
  step: positive finite binary64
  stepCount: non-negative integer
  timeUnit: exact unit identity with dimension TIME
  unitConversionCatalogVersion: GDSS_UNIT_CONVERSION_V2
}
```

Exactly one effective initial condition exists for every state and one explicit value for every
referenced parameter. Defaults, telemetry, prior runs and wall clock are forbidden. `step_index` is
the authoritative coordinate; `t(i)` is independently derived from canonical start/step and never
from a previous timestamp.

## Solver and resource profile

```text
SolverDefinition { key: EXPLICIT_EULER, version: EXPLICIT_EULER_V1,
                   numericSemantics: IEEE754_BINARY64 }

SimulationResourceProfile {
  profileVersion,
  maxStates, maxRates, maxAlgebraics, maxStepCount,
  maxTrajectoryPoints, maxOperationsPerStep, maxTotalOperations,
  maxTrajectoryBytes, maxDiagnostics
}
```

Every limit is finite, positive where applicable, included in input identity and checked before and
during execution. Exact initial thresholds require implementation benchmarking.

## Execution contracts

```text
SimulationInputManifest {
  projectId, modelVersionId, modelContentHash
  dynamicBindingIdentityId, dynamicBindingVersion, dynamicBindingHash
  dynamicSemanticVersion, solverVersion
  initialConditions[], parameterInputs[], temporalConfiguration
  expressionLanguageVersion, evaluatorVersion, unitConversionCatalogVersion
  simulationResourceProfile, constraintPolicy: FAIL_RUN
  simulationInputHash
}

GDSSSimulationExecution {
  executionAttemptId
  simulationInputHash
  status: RUNNING | COMPLETED | FAILED | ABORTED
  terminationReason
  trajectoryArtifact?, diagnostics[]
  simulationResultHash?
  actorAuditMetadata
}
```

`RUNNING` exists only for an accepted attempt, whether execution is synchronous or asynchronous.
There is no persisted mutable `PREPARED` execution. `ABORTED` requires an explicit future governed
cancellation mechanism; v1 may omit producing it until such a mechanism exists.

## Trajectory and result

```text
GDSSSimulationTrajectory {
  completeness: COMPLETE | PARTIAL
  pointCount
  points ordered by strictly increasing step_index
}

SimulationPoint {
  stepIndex
  states: sorted map stateRef -> canonical value/unit
  epistemicKind: SIMULATED
}

TrajectoryArtifactRef {
  artifactHash, byteLength, mediaType, storageLocator, canonicalFormatVersion
}

SimulationDiagnostic {
  code, severity, stage, stepIndex?, stateRef?, rateRef?, formulaRef?,
  expected?, actual?, message
}
```

Canonical trajectory contains states only. Algebraic and rate values are optional diagnostic traces
and do not inflate the canonical trajectory. A partial trajectory is retained only as failed
execution evidence and is marked `PARTIAL`; it can never produce a completed status.

Stable termination reasons are `END_TIME_REACHED`, `NON_FINITE_STATE`, `NON_FINITE_RATE`,
`EXPRESSION_FAILURE`, `DIMENSION_FAILURE`, `CONSTRAINT_VIOLATION`, `RESOURCE_LIMIT_EXCEEDED`,
`INVALID_CONFIGURATION`, `INSTANTANEOUS_ALGEBRAIC_LOOP_UNSUPPORTED`, `SOLVER_FAILURE` and
`ABORTED_BY_AUTHORIZED_REQUEST`.

## Identities

```text
simulation_input_hash = SHA-256(canonical("gdss-simulation-input:v1", manifest without hash))
trajectory_hash       = SHA-256(canonical trajectory artifact bytes)
simulation_result_hash = SHA-256(canonical("gdss-simulation-result:v1",
  simulation_input_hash, status, termination_reason, completeness,
  trajectory_hash?, canonical deterministic diagnostics))
execution_attempt_id  = opaque UUID, never part of computational hashes
```

Maps and bindings sort by stable symbol; numbers use GDSS-002 normalized binary64 encoding.
Diagnostic codes and deterministic fields participate; human messages and audit metadata do not.

## Authorization and epistemology

`RUN_SIMULATION` requires OAuth session, exact project membership and effective `operator` or
`admin`. `viewer` fails closed. It authorizes creation of computational evidence only. It does not
authorize model lifecycle changes, publication, prediction claims, experiments, ControlPolicy,
deployment, recommendation or actuation.

Every output point is `SIMULATED`, even when an input provenance is `OBSERVED`. The result exposes
`physicalAuthority: NONE`.
