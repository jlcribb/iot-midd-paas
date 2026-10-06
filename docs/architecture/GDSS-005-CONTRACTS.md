# GDSS-005 — Governed Contracts

Status: `PROPOSED`
Semantic version: `GDSS_CALIBRATION_V1`

## Version registry

```text
observation schema          GDSS_OBSERVATION_DATASET_V1
alignment semantics        GDSS_OBSERVATION_ALIGNMENT_V1
calibration design         GDSS_CALIBRATION_DESIGN_V1
objective                  RMSE_V1 | WEIGHTED_NORMALIZED_MSE_V1
search                     FINITE_GRID_SEARCH_V1
result                     GDSS_CALIBRATION_RESULT_V1
resource profile           GDSS_CALIBRATION_LIMITS_V1
unit catalog               exact GDSS_UNIT_CONVERSION_V2 reference
physical authority         NONE
```

Unknown versions fail closed. A later version must never reinterpret V1 evidence.

## ObservationDatasetVersion

```text
ObservationDatasetVersion {
  id, datasetIdentityId, projectId, versionNumber, predecessorVersionId?
  evidenceKind: PHYSICAL_OBSERVATION | SYNTHETIC_OBSERVATION
  title, description
  measurementContext
  sourceReferences[]
  series[]
  observationDatasetHash
  schemaVersion: GDSS_OBSERVATION_DATASET_V1
  lifecycleStatus
}
```

`measurementContext` is descriptive, bounded canonical metadata such as system boundary, location
identity and operating regime. It cannot replace explicit source, quantity, unit or time fields.

```text
ObservationSourceReference {
  providerKind: GOVERNED_OBJECT_STORE | DATABASE_SNAPSHOT | SIGNED_IMPORT
  opaqueSourceKey
  sourceArtifactSha256
  mediaType
  byteLength
  capturedBy
  instrumentIdentity?
  instrumentCalibrationEvidenceHash?
}
```

Provider kind is allowlisted. `opaqueSourceKey` is data, never an implicitly fetched URL.

```text
ObservationSeries {
  id, datasetVersionId, seriesKey
  sourceReferenceId
  channelIdentity
  physicalSourceIdentity
  quantityIdentity
  unitIdentity { key, revision }
  dimension [seven SI exponents]
  quantitySemantics: ABSOLUTE | INTERVAL
  clockSourceIdentity
  clockUncertainty?
  samplingSemantics: EVENT_DRIVEN | FIXED_INTERVAL | IRREGULAR
  declaredSamplingInterval?
  points[]
}
```

```text
ObservationPoint {
  id, seriesId, sourceOrdinal
  measurementEpochMicros
  value?: finite canonical binary64
  qualityStatus
  qualityReasonCode?
  uncertainty
  sourceRecordHash
}
```

`measurementEpochMicros` is an exact signed integer UTC coordinate. Original zone/offset and clock
source remain provenance. `ingestedAt` and `processedAt` are audit fields outside computational
identity. A series cannot contain duplicate measurement coordinates. Input order is not semantic;
canonical order is `(seriesKey, measurementEpochMicros, sourceOrdinal)` and a repeated coordinate
fails rather than using source ordinal as a scientific tie-break.

### Quality vocabulary

```text
ACCEPTED
SUSPECT
REJECTED
MISSING
DEVICE_ERROR
```

Detection limit, saturation, out-of-range and manual invalidation remain exact reason codes under a
versioned instrument/domain reason registry; they map to one core status. `MISSING` and
`DEVICE_ERROR` have no numeric value. V1 calibration includes only `ACCEPTED`; every exclusion is
materialized into the alignment hash. Absence of a point is not an explicit `MISSING` point.

### Uncertainty value

```text
ObservationUncertainty =
  { kind: UNKNOWN }
  | { kind: ABSOLUTE_BOUND, magnitude, unitIdentity }
  | { kind: RELATIVE_BOUND, fraction }

instrumentResolution?: { magnitude, unitIdentity }
```

Magnitudes are finite and non-negative; relative fraction is dimensionless. Resolution and an
accuracy/tolerance bound retain their source evidence. Neither creates a probability distribution
or an optimization weight. `UNKNOWN` is distinct from a zero bound.

## ObservationSimulationAlignment

```text
ObservationSimulationAlignment {
  seriesId
  modelVariableRef { kind: STATE | ALGEBRAIC, identity }
  quantityIdentity
  observationUnitIdentity
  modelUnitIdentity
  dimension
  quantitySemantics
  observationOriginEpochMicros
  simulationStart
  simulationTimeUnitIdentity
  window { startEpochMicros, endEpochMicros }
  temporalMethod: EXACT_COORDINATE_MATCH_V1
  missingPolicy: ACCEPTED_ONLY_FAIL_IF_BELOW_MINIMUM
  minimumMatchedPoints
  normalizationScale?
  objectiveWeight?
}
```

The alignment expands into an immutable ordered match manifest:

```text
{ observationPointId, measurementEpochMicros, simulationStepIndex,
  observationCanonicalValue, simulationCoordinate }
```

Unknown quantity, ambiguous variable, unsupported conversion, non-exact coordinate, duplicate
coordinate or too few accepted points fails closed. There is no interpolation, resampling,
extrapolation, smoothing or implicit outlier removal.

## CalibrationDesignVersion

```text
CalibrationDesignVersion {
  id, calibrationIdentityId, projectId, versionNumber, predecessorVersionId?
  systemModelVersionId
  modelContentHash
  dynamicBindingVersionId
  dynamicBindingHash
  observationDatasetVersionId
  observationDatasetHash
  datasetRole: CALIBRATION
  alignments[]
  calibratedParameters[]
  fixedParameters[]
  objectiveDefinition
  searchDefinition
  candidateFailurePolicy
  adequacyCriterion?
  semanticVersions
  resourceProfile: GDSS_CALIBRATION_LIMITS_V1
  calibrationDesignHash
  lifecycleStatus
}
```

```text
CalibratedParameter {
  parameterRef
  priorValue
  unitIdentity
  dimension
  quantitySemantics
  lowerBound, upperBound
  candidateValues[]
}
```

Candidate values must be unique, finite, ordered canonically and within inclusive bounds. The prior
value remains provenance and must be present in the grid unless the design explicitly records why
it is excluded. Fixed parameters are exact governed overrides and cannot overlap calibrated
parameters.

## Objective contracts

Residual at matched point `i` in series `s` is:

```text
r[s,i] = observedCanonicalValue[s,i] - simulatedCanonicalValue[s,i]
```

The subtraction follows GDSS-002 unit, dimension and affine quantity rules. Point residual has the
series dimension; squared residual has the squared dimension.

### RMSE_V1

Valid for exactly one alignment:

```text
RMSE = sqrt(sum(i=1..n, r[i]^2) / n)
```

`n` is the exact matched accepted-point count and must meet `minimumMatchedPoints`. Result dimension
and unit equal the mapped quantity. SSE and MSE are retained as diagnostic components but are not
separate V1 selection objectives because, on one fixed match set, they produce the same ordering.

### WEIGHTED_NORMALIZED_MSE_V1

Valid for one or more alignments. Each alignment declares positive finite normalization scale
`a_s` in its quantity unit and positive finite dimensionless weight `w_s`:

```text
seriesMSE_s = sum(i=1..n_s, (r[s,i] / a_s)^2) / n_s
objective   = sum(s, w_s * seriesMSE_s) / sum(s, w_s)
```

The result is dimensionless. Normalization is explicit and cannot be inferred from observed range,
uncertainty or post-run residuals. Canonical binary64 operation order is series key then point time.
Any non-finite intermediate fails the candidate. Missing or non-accepted points are excluded only
by the predeclared alignment manifest; the match set cannot change between candidates.

## Search contract

```text
FiniteGridSearchV1 {
  method: FINITE_GRID_SEARCH_V1
  parameterOrder: canonical parameter identity order
  enumeration: lexicographic Cartesian product
  termination: EXHAUSTIVE_OR_GOVERNED_ABORT
  tieRule: lowest canonical parameter-vector bytes
}
```

There is no random seed, stochastic method, adaptive grid or convergence tolerance. All candidate
manifests are materialized before dispatch. Candidate simulations use exact GDSS-003 identities and
idempotency. `OPTIMIZABLE` never implies `IDENTIFIABLE`; V1 result is always
`identifiabilityStatus: NOT_ASSESSED`.

## Execution and result contracts

```text
CalibrationExecutionAttempt {
  id                         // operational UUID
  projectId
  calibrationDesignVersionId
  calibrationDesignHash
  requestedBy
  idempotencyKey?
  acceptedAt                 // operational only
}
```

```text
CandidateEvaluation {
  candidateOrdinal
  parameterVectorHash
  parameterAssignments
  gdssSimulationAttemptId
  simulationInputHash
  simulationResultHash?
  trajectoryHash?
  state: SUCCEEDED | INFEASIBLE | SIMULATION_FAILED
  objectiveValue?
  matchedPointCount
  diagnosticCodes[]
}
```

```text
ParameterEstimateSet {
  calibrationDesignHash
  datasetHash
  alignmentHashes[]
  selectedCandidateOrdinal
  estimates[] {
    parameterRef, priorValue, estimatedValue, unitIdentity, bounds
  }
  objectiveVersion, objectiveValue
  searchMethodVersion
  identifiabilityStatus: NOT_ASSESSED
  parameterEstimateSetHash
}
```

```text
CalibrationResult {
  status: COMPLETED | COMPLETED_WITH_WARNINGS | FAILED | ABORTED
  executionAttemptId
  calibrationDesignHash
  parameterEstimateSetHash?
  residualArtifactHash?
  adequacyAssessment
  diagnostics[]
  provenance: CALIBRATION_DERIVED
  physicalAuthority: NONE
  calibrationResultHash
}
```

Execution completion does not imply acceptable fit. A result never mutates model or binding.

## Adequacy assessment

```text
FIT_COMPUTED_NO_ADEQUACY_CLAIM
ACCEPTABLE_UNDER_DECLARED_CRITERIA
POOR_FIT_UNDER_DECLARED_CRITERIA
INSUFFICIENT_EVIDENCE
INCOMPARABLE
```

An acceptance criterion is an optional, versioned, pre-execution threshold dimensionally
compatible with the objective. Without it, only `FIT_COMPUTED_NO_ADEQUACY_CLAIM` is possible.
Adequacy is scoped to the exact calibration dataset and never means validation, truth or prediction.

## Failure vocabulary

```text
INVALID_DATASET
UNKNOWN_QUANTITY_MAPPING
DIMENSION_MISMATCH
TEMPORAL_ALIGNMENT_FAILURE
INSUFFICIENT_OBSERVATIONS
NONFINITE_OBJECTIVE
SEARCH_LIMIT_EXCEEDED
NO_FEASIBLE_PARAMETER_SET
SIMULATION_FAILURE
RESOURCE_LIMIT_EXCEEDED
DATASET_ROLE_CONFLICT
EVIDENCE_LEAKAGE_DETECTED
ARTIFACT_INTEGRITY_FAILURE
IDENTITY_MISMATCH
ABORT_REQUESTED
```

Failure stage and bounded deterministic details accompany each code. Stack traces, wall time and
worker identity are operational diagnostics and excluded from computational identity.

## Computational identity

The minimal non-redundant hashes are:

```text
observation_dataset_hash
  SHA256(domain "midd:gdss:observation-dataset:v1" + canonical admitted evidence)

alignment_hash
  SHA256(domain "midd:gdss:observation-alignment:v1" + mapping, policy and exact match manifest)

calibration_design_hash
  SHA256(domain "midd:gdss:calibration-design:v1" + exact versions, hashes, parameters,
         alignment hashes, objective, search, failure policy, criterion and limits)

parameter_estimate_set_hash
  SHA256(domain "midd:gdss:parameter-estimate-set:v1" + selected governed evidence)

calibration_result_hash
  SHA256(domain "midd:gdss:calibration-result:v1" + status, estimate hash, residual hash,
         adequacy and deterministic diagnostics)
```

`calibration_input_hash` is rejected as redundant with the immutable design hash. Candidate
simulation input/result/trajectory hashes remain GDSS-003 identities. Canonicalization uses sorted
keys, closed arrays in semantic order, epoch microseconds, canonical unit identities and finite
binary64 bytes. UUIDs, ingestion/processing/execution times, worker IDs and database insertion order
are excluded unless they are exact governed references whose content hash is also bound.

## Proposed migration 0043

`0043` is required but not created. Proposed normalized tables:

| Table | Purpose |
|---|---|
| `gdss_observation_dataset_identity` | project-scoped canonical dataset identity |
| `gdss_observation_dataset_version` | immutable version, predecessor, kind, schema and hash |
| `gdss_observation_source_reference` | provider/key/hash/media/instrument provenance |
| `gdss_observation_series` | channel, source, quantity, unit, clock and sampling contract |
| `gdss_observation_point` | exact time/value/quality/uncertainty/source-record hash |
| `gdss_observation_dataset_lifecycle_event` | append-only dataset lifecycle |
| `gdss_calibration_identity` | project-scoped canonical calibration identity |
| `gdss_calibration_version` | immutable model/binding/dataset/objective/search design |
| `gdss_calibration_dataset_assignment` | exact version and role; future partition boundary |
| `gdss_calibration_series_mapping` | series-to-variable alignment and objective component |
| `gdss_calibration_parameter` | calibrated/fixed parameter definition and bounds |
| `gdss_calibration_lifecycle_event` | append-only design lifecycle |
| `gdss_calibration_artifact` | content-addressed manifest/residual/result bytes |
| `gdss_calibration_execution_attempt` | operational attempt and immutable design identity |
| `gdss_calibration_execution_event` | append-only accepted/running/terminal history |
| `gdss_calibration_candidate_evaluation` | candidate vector and exact GDSS-003 link |
| `gdss_calibration_parameter_estimate_set` | selected candidate and estimate-set hash |
| `gdss_calibration_parameter_estimate` | one immutable parameter estimate with provenance |
| `gdss_model_adequacy_assessment` | scoped criterion, conclusion and evidence hashes |
| `gdss_calibration_estimate_review` | human accept/reject-for-proposal decision |
| `gdss_calibration_diagnostic` | bounded deterministic diagnostic evidence |

Governance-critical ownership, role, mapping, parameter, candidate, estimate and lifecycle relations
are relational. Canonical manifest, residual and result artifacts are byte-verified against their
relational projections. Composite project/version foreign keys prevent cross-project substitution.
All evidence tables reject update/delete; lifecycle and execution state advance through append-only
events.

## Authorization contract

```text
READ_OBSERVATION
ADMIT_OBSERVATION
CREATE_CALIBRATION
VALIDATE_CALIBRATION_DESIGN
RUN_CALIBRATION
ACCEPT_PARAMETER_ESTIMATE
PUBLISH_CALIBRATION_RESULT
```

`COMPUTE_PARAMETER_ESTIMATE != ACCEPT_PARAMETER_ESTIMATE`. Acceptance only permits a separately
governed successor-model proposal; it does not mutate a model or establish scientific validation.
AI-proposed mappings, bounds, grids or interpretations remain proposals until explicit human
admission/validation and never bypass these capabilities.
