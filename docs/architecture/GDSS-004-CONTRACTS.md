# GDSS-004 — Governed Experiment Contracts

Status: `PROPOSED`
Semantic version: `GDSS_EXPERIMENT_V1`
Implementation: `NOT_AUTHORIZED`

## Closed versions

```text
experiment semantics        GDSS_EXPERIMENT_V1
scenario expansion          GDSS_EXPERIMENT_EXPANSION_V1
metric semantics            GDSS_EXPERIMENT_METRICS_V1
comparison semantics        GDSS_EXPERIMENT_COMPARISONS_V1
manifest format             GDSS_EXPERIMENT_MANIFEST_JSON_V1
result format               GDSS_EXPERIMENT_RESULT_JSON_V1
recovery policy             GDSS_EXPERIMENT_RECOVERY_V1
limits profile              GDSS_EXPERIMENT_LIMITS_V1
provenance                  SIMULATION_DERIVED
physical authority          NONE
```

No contract resolves an implicit `latest` version.

## Ontology

### Experiment

Conceptual identity for a research question. It owns versions, not execution evidence directly.

### ExperimentVersion

Immutable exact design version. It contains the question, optional hypothesis, exact GDSS-003 base
manifest identity, factors, controlled inputs, metric definitions, comparison definitions,
completeness policy and all semantic versions.

### ScenarioDefinition

Design-time declaration of scenario type, explicit reference relation and authorized overrides. It
is not executable until materialized against the exact base manifest.

### MaterializedScenario

One ordered, canonical, fully resolved scenario produced before dispatch. It binds an exact
`ExperimentVersion`, scenario hash, ordinal, materialized GDSS-003 input manifest and input hash.

### ExperimentExecution

One attempt to execute one exact published `ExperimentVersion` and its complete materialized
scenario universe. Attempt identity is operational and differs from manifest identity.

### ScenarioExecution

Append-only mapping between one materialized scenario and an independently committed GDSS-003
attempt/result. It does not own trajectory bytes.

### TrajectoryMetric

Versioned trajectory-local reduction executed by a closed metric vocabulary over one verified
GDSS-003 trajectory.

### ExperimentComparison

Versioned relation between explicit reference and target metric results. It declares eligibility,
units, temporal policy and comparison operation.

### ComparativeFinding

Immutable narrative-safe structured evidence derived from one exact eligible comparison. It has
`SIMULATION_DERIVED` provenance and no recommendation field.

## ExperimentVersion contract

```text
ExperimentVersion {
  experimentVersionId
  experimentIdentityId
  versionNumber
  predecessorVersionId?
  projectId
  lifecycleStatus
  researchQuestion
  hypothesis?
  baseSimulationManifest
  baseSimulationInputHash
  factors[]
  controlledInputs[]
  explicitScenarios[]
  metrics[]
  comparisons[]
  completenessPolicy
  semanticVersions
  limitProfile
  experimentDesignHash
}
```

The base manifest binds exact GDSS-003 model version/content hash, dynamic binding version/hash,
solver, temporal configuration, expression/evaluator/catalog versions and resource profile.
Structural model or binding changes are not v1 overrides.

## Factors and controlled inputs

```text
ExperimentalFactor {
  factorKey
  targetKind: PARAMETER | INITIAL_CONDITION | TEMPORAL_CONFIGURATION
  targetIdentity
  orderedValues[]
  unitIdentity?
  provenance
}

ControlledInput {
  targetKind
  targetIdentity
  expectedGovernedValue
  unitIdentity?
}
```

All relevant base inputs belong to the closed universe `PARAMETERS`, `INITIAL_CONDITIONS` and
`TEMPORAL_CONFIGURATION`. Each is either deliberately varied or controlled. Overlap is invalid.

## Scenario contracts

```text
ScenarioType = BASELINE | ALTERNATIVE | COUNTERFACTUAL

ScenarioOverride {
  targetKind
  targetIdentity
  expectedPreviousValue
  replacementValue
  unitIdentity?
  provenance
}

MaterializedScenarioManifest {
  experimentVersionId
  experimentDesignHash
  ordinal
  scenarioType
  explicitReferenceScenarioKey?
  authorizedOverrides[]
  materializedSimulationManifest
  simulationInputHash
  scenarioDefinitionHash
}
```

The declared previous value must equal the governed base value after canonical unit resolution.
Any difference not attributable to an authorized override is `UNDECLARED_VARIATION` and fails
closed. Baseline is explicit and never inferred from ordinal.

## Execution contracts

```text
ExperimentExecutionAttempt {
  attemptId
  projectId
  experimentVersionId
  experimentDesignHash
  experimentExecutionManifestHash
  status
  requestedBy
}

ScenarioExecutionEvidence {
  materializedScenarioId
  scenarioDefinitionHash
  dispatchStatus
  gdssSimulationAttemptId?
  simulationInputHash
  trajectoryHash?
  simulationResultHash?
  terminalClassification
  diagnostics[]
}
```

`requestedBy` is audit metadata and excluded from computational hashes.

## Completeness

```text
EvidenceCompletenessPolicy =
  ALL_REQUIRED_SCENARIOS |
  ALLOW_PARTIAL_EXPLICIT
```

Every comparison declares its exact required scenario set. Under either policy, absent or failed
required evidence yields an `INELIGIBLE` comparison with a deterministic diagnostic. Partial policy
permits an explicitly partial result; it never silently removes a scenario.

## Metric contract

```text
TrajectoryMetricDefinition {
  metricKey
  metricVersion: GDSS_EXPERIMENT_METRICS_V1
  operation
  stateSymbol
  expectedUnitIdentity
  expectedDimension
  requiredTrajectoryCompleteness
  threshold? { value, unitIdentity, direction }
}

TrajectoryMetricResult {
  definitionHash
  materializedScenarioId
  simulationResultHash
  trajectoryHash
  status: SUCCEEDED | INELIGIBLE | FAILED
  value? | stepIndex? | notReached?
  unitIdentity
  dimension
  quantitySemantics
  provenance: SIMULATION_DERIVED
}
```

The exact mathematics are normative in `GDSS-004-METRICS-AND-COMPARISON.md`.

## Comparison and finding contracts

```text
ExperimentComparisonDefinition {
  comparisonKey
  comparisonVersion: GDSS_EXPERIMENT_COMPARISONS_V1
  operation
  metricDefinitionHash
  referenceScenarioKey
  targetScenarioKey
  requiredScenarioKeys[]
  temporalComparabilityPolicy
}

ComparisonResult {
  definitionHash
  status: SUCCEEDED | INELIGIBLE | FAILED
  referenceMetricResultHash
  targetMetricResultHash
  value? | ordering?
  unitIdentity
  dimension
  diagnostic?
  provenance: SIMULATION_DERIVED
}

ComparativeFinding {
  experimentVersionId
  experimentExecutionAttemptId
  comparisonDefinitionHash
  referenceScenarioHash
  targetScenarioHash
  metricDefinitionHash
  referenceMetricResultHash
  targetMetricResultHash
  comparisonResultHash
  unitsAndDimension
  eligibilityStatus
  provenance: SIMULATION_DERIVED
  physicalAuthority: NONE
}
```

There is no implicit recommendation, prediction or empirical-claim field.

## Canonical identities

Canonical JSON reuses the established GDSS `canonicalJson` contract: UTF-8, no BOM, sorted object
keys, closed schemas, semantic array order, no insignificant whitespace, and every finite number
encoded as `{ "$binary64": <16 lowercase big-endian IEEE-754 hex digits> }` with `-0` normalized to
`+0`. There is no trailing LF. Hashes are lowercase SHA-256 over the exact canonical JSON bytes of
the domain-separated `{schema,value}` envelope. This makes manifest/result identity equal to the
exact stored artifact bytes rather than to a competing prefixed representation.

```text
experiment_design_hash
  SHA256(canonicalJson({schema:"gdss-experiment-design:v1",value:design}))

scenario_definition_hash
  SHA256(canonicalJson({schema:"gdss-experiment-scenario:v1",value:scenario}))

experiment_execution_manifest_hash
  SHA256(canonicalJson({schema:"gdss-experiment-execution-manifest:v1",value:manifest}))

experiment_result_hash
  SHA256(canonicalJson({schema:"gdss-experiment-result:v1",value:result}))
```

Design identity includes exact base GDSS-003 identities, factors and ordered values, controlled
inputs, metrics, comparisons, policies and semantic versions. Scenario identity includes the design
hash, ordinal, type, reference and fully resolved simulation input identity. Result identity binds
every materialized scenario in precommitted ordinal order, including success, failure, never
dispatched and aborted classifications, plus metric/comparison evidence and result completeness.

Excluded from all semantic hashes: attempt UUID, actor, audit timestamps, worker identity, worker
order, completion order, latency and operational retry metadata.

## Authorization contract

Authorization requires `auth_source=oauth_session`, a non-empty user, exact project membership and
the capability-to-role mapping in the ADR. Project mismatch, header actor fallback and unscoped
global permission fail closed.

```text
RUN_SIMULATION != RUN_EXPERIMENT
RUN_EXPERIMENT != PUBLISH_EXPERIMENT
RUN_EXPERIMENT != ABORT_EXPERIMENT
```

## Authority contract

```text
epistemic provenance:       SIMULATION_DERIVED
physical authority:         NONE
prediction authority:       NONE
recommendation authority:   NONE
scientific authority:       NONE
```
