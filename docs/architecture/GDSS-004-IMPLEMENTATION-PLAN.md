# GDSS-004 — Implementation Plan v0.1

Status: `PROPOSED`
Prompt: `MIDD-GDSS-P011`
Baseline: `10d454e985f904228c5b62dd5cb12c6b2171e6d2` / Alembic `0041`
Implementation: `NOT_AUTHORIZED`

## 1. Fixed decisions

```text
MIGRATION_IMPLEMENTATION_DECISION = 0042_REQUIRED_BY_APPROVED_DESIGN
migration filename = 0042_gdss_simulation_experimentation.py
table count = 15
numeric semantics = GDSS_EXPERIMENT_NUMERIC_V1
scenario expansion = GDSS_EXPERIMENT_EXPANSION_V1
metrics = GDSS_EXPERIMENT_METRICS_V1
comparisons = GDSS_EXPERIMENT_COMPARISONS_V1
temporal comparability = GDSS_TEMPORAL_COMPARABILITY_V1
recovery = GDSS_EXPERIMENT_RECOVERY_V1
limits = GDSS_EXPERIMENT_LIMITS_V1
physical authority = NONE
```

Migrations `0001..0041` remain immutable. P011 creates no migration, production module or test.

## 2. Production file plan

Pure core under `apps/topology-next/src/lib/gdss/experiment/`:

| File | Responsibility | Side effects |
|---|---|---|
| `contracts.ts` | Closed TypeScript types for design, scenario, evidence and results. | none |
| `versions.ts` | All literal semantic/version constants. | none |
| `limits.ts` | Frozen `GDSS_EXPERIMENT_LIMITS_V1` and counters. | none |
| `canonical.ts` | Canonical projections and four hash functions. | cryptographic hash only |
| `diagnostics.ts` | Closed codes, stages, severity and fail-closed error mapping. | none |
| `design.ts` | Design validation, lifecycle-independent semantic validation. | none |
| `expansion.ts` | Bounded Cartesian cardinality and canonical ordered expansion. | none |
| `scenario.ts` | Overrides, expected-value checks and controlled-input proof. | none |
| `trajectory-reader.ts` | Pure decoder/verifier over caller-supplied GDSS-003 bytes. | none |
| `metrics.ts` | Exact trajectory-local algorithms and operation accounting. | none |
| `comparisons.ts` | Eligibility and four comparison algorithms. | none |
| `temporal-comparability.ts` | Metric-specific deterministic temporal rules. | none |
| `authorization.ts` | Capability-to-existing-project-role decision functions. | none |
| `recovery.ts` | Recovery constants and pure reconciliation decisions. | none |
| `index.ts` | Explicit public exports only. | none |

Adapters outside the pure core:

| File | Responsibility |
|---|---|
| `apps/topology-next/src/lib/repositories/gdss-experiment.repository.ts` | PostgreSQL transactions, locks, persistence, artifact equality and audit writes. |
| `apps/topology-next/src/lib/services/gdss-experiment.service.ts` | Authorized lifecycle/design API and orchestration composition. |
| `apps/topology-next/src/lib/services/gdss-experiment-worker.ts` | Bounded claim/dispatch/recovery/terminalization loop. |

The pure core may import existing GDSS canonical, dimensional, unit and GDSS-003 contract helpers.
It may not access DB, HTTP, filesystem, environment, MQTT, telemetry, Control Engine, DTE, devices
or actuation. Repository code may access PostgreSQL only. The service/worker may invoke the existing
GDSS-003 service through an injected interface; they must not fork its runtime.

There is deliberately no pure-core `orchestrator.ts`: orchestration necessarily crosses transaction
and GDSS-003 adapter boundaries. Its deterministic decisions live in pure expansion/recovery
functions, while side-effectful coordination is split between `gdss-experiment.service.ts` and
`gdss-experiment-worker.ts`. This prevents a misleading persistence-capable module inside the
mathematical core.

## 3. Exact TypeScript contracts

Use opaque aliases for `UUID`, `Sha256Hex`, `CanonicalOrdinal` and governed unit/dimension types.
Every object is readonly after validation.

```text
ExperimentLifecycle = DRAFT | VALIDATED | PUBLISHED | DEPRECATED
ScenarioType = BASELINE | ALTERNATIVE | COUNTERFACTUAL
OverrideTargetKind = PARAMETER | INITIAL_CONDITION | TEMPORAL_CONFIGURATION
CompletenessPolicy = ALL_REQUIRED_SCENARIOS | ALLOW_PARTIAL_EXPLICIT
ExperimentTerminalStatus = COMPLETED | COMPLETED_WITH_FAILURES | FAILED | ABORTED
ScenarioDispatchState = PENDING | CLAIMED | DISPATCHED | TERMINAL_SUCCESS |
                        TERMINAL_FAILURE | NOT_DISPATCHED_ABORTED
MetricStatus = SUCCEEDED | NOT_REACHED | INELIGIBLE | FAILED
ComparisonStatus = SUCCEEDED | INELIGIBLE | FAILED
```

`CLAIMED` is an operational lease projection, not immutable semantic evidence. The durable scenario
execution row is append-only except for lease fields explicitly updated under guarded transitions;
semantic GDSS-003 link fields may be assigned once only. Terminal classifications never change.

Core interfaces mirror `GDSS-004-CONTRACTS.md` and add these exact result forms:

```text
ScalarMetricResult = { status:SUCCEEDED, value, unit, dimension, quantitySemantics }
PeakStepResult = { status:SUCCEEDED, stepIndex }
ThresholdMetricResult =
  { status:SUCCEEDED, stepIndex, elapsed:{value,unit,dimension:TIME,semantics:INTERVAL} } |
  { status:NOT_REACHED }
IneligibleMetricResult = { status:INELIGIBLE, diagnosticCode }
FailedMetricResult = { status:FAILED, diagnosticCode }
```

No union contains an implicit numeric placeholder for absent evidence.

## 4. Canonical serialization and identities

Reuse the exact established GDSS implementation:

```text
stableValue(number) = {"$binary64":"<16 lowercase big-endian IEEE-754 hex>"}
-0 normalizes to +0
NaN and infinities rejected
object keys lexicographically sorted
array order preserved as semantic
JSON.stringify output
UTF-8, no BOM, no trailing LF, no insignificant whitespace
```

Define:

```text
canonicalEnvelope(schema,value) = canonicalJson({schema,value})
domainHash(schema,value) = SHA256(UTF8(canonicalEnvelope(schema,value)))
```

Exact identities:

```text
experiment_design_hash =
  domainHash("gdss-experiment-design:v1", canonicalDesignProjection)

scenario_definition_hash =
  domainHash("gdss-experiment-scenario:v1", canonicalScenarioProjection)

experiment_execution_manifest_hash =
  SHA256(exact GDSS_EXPERIMENT_MANIFEST_JSON_V1 bytes)

experiment_result_hash =
  SHA256(exact GDSS_EXPERIMENT_RESULT_JSON_V1 bytes)

experiment_execution_attempt_id = UUIDv4
```

Manifest bytes are precisely
`UTF8(canonicalEnvelope("gdss-experiment-execution-manifest:v1", manifestProjection))`.
Result bytes use schema `gdss-experiment-result:v1`. Thus artifact hash and semantic identity are
the same value without a second representation.

### Design projection

Includes exact experiment semantic content; model version/content hash; binding version/hash;
GDSS-003 dynamic/solver/constraint/resource versions; GDSS-002 expression/evaluator/unit versions;
research question and hypothesis; canonically ordered factors with ordered domains; controlled
inputs; metric/comparison definitions; completeness and temporal policies; expansion, numeric,
metric, comparison and experiment limit versions. Excludes IDs that are storage-only, lifecycle
events, actor and time.

### Scenario projection

Includes design hash, ordinal, explicit type including baseline designation, explicit reference,
factor assignments, overrides with provenance, controlled-input proof hash and exact GDSS-003
`simulation_input_hash`. Baseline therefore participates directly in scenario identity.

### Manifest projection

Includes design hash, all semantic versions and policies, full metric/comparison plan and every
scenario projection in canonical ordinal order. It excludes attempt UUID, actor, timestamps,
workers, latencies, dispatch order and retries.

### Result projection

Includes manifest hash, experiment terminal/completeness classifications, and every scenario in
manifest order with dispatch/terminal classification, GDSS-003 result/trajectory hashes or explicit
absence/failure classification. It also includes ordered metric results, comparison results,
`INELIGIBLE` evidence, findings and identity-relevant diagnostics. Consequently complete, partial,
absent and aborted outcomes cannot collide.

## 5. Scenario expansion and overrides

Factors sort lexicographically by `(targetKind, canonicalTargetIdentity, factorKey)` using Unicode
code-point comparison over normalized ASCII identifiers. Factor value order is explicit semantic
author ordinal; the ordinal is persisted and hash-bound. Reordering values creates a different
design. The last canonical factor varies fastest.

Value validation:

- reject empty domains and duplicates after governed unit conversion;
- normalize `-0` to `+0` before duplicate detection;
- reject non-finite values;
- compare semantically equivalent values in canonical governed units;
- reject incompatible dimensions or affine quantity semantics;
- permit affine absolute values only for targets declared `ABSOLUTE` and interval values only for
  compatible `INTERVAL` targets.

Cardinality uses checked integer multiplication before allocation. It must be `1..256`.

For each scenario, copy the exact base manifest, apply overrides in canonical factor order, compare
actual base value with declared expected value after governed conversion, and emit
`EXPECTED_VALUE_MISMATCH` on inequality. Diff the final canonical manifest against the base; every
difference must map one-to-one to an authorized override or fail `UNDECLARED_VARIATION`. Run the
existing GDSS-003 preflight and input hash function. No dispatch occurs until Transaction A commits
all scenarios and artifact bytes.

## 6. Governed trajectory reader API

```text
read(input: {
  expectedProjectId,
  expectedSimulationAttemptId,
  expectedSimulationResultHash,
  expectedTrajectoryHash,
  expectedMediaType:
    "application/vnd.midd.gdss-trajectory+ndjson;version=1",
  expectedFormatVersion:"GDSS_TRAJECTORY_NDJSON_V1",
  expectedByteLength,
  expectedPointCount,
  expectedCompleteness,
  payload:Uint8Array
}) -> ReadonlyTrajectory
```

It verifies exact SHA-256, byte length, metadata, canonical decoder round-trip equality, header,
point count, contiguous indices, state symbols, unit revisions, dimensions, finite values and
epistemic kind. It exposes immutable points in canonical order. No repair, recanonicalization,
write, caching authority or alternate trajectory type is permitted.

## 7. Numeric and metric algorithms

`GDSS_EXPERIMENT_NUMERIC_V1` uses strict left-to-right IEEE-754 binary64 operations in ascending
canonical `stepIndex`. Each addition/multiplication rounds to binary64 as JavaScript `number`.
This is chosen over pairwise/compensated summation because it is simplest to specify, matches the
runtime and has one unambiguous order. Any non-finite input or intermediate fails closed. No
parallel reduction is allowed.

Operation accounting counts one comparison, addition, subtraction, multiplication, division or
governed scalar conversion as one operation. Point access is free. A metric reserves its worst-case
operations atomically before producing evidence.

| Metric | Exact algorithm and eligibility | Output | Max counted operations for P points |
|---|---|---|---:|
| INITIAL_VALUE | Require point 0; read x0. Partial allowed only when point 0 present and definition permits. | original governed scalar | 0 |
| FINAL_VALUE | Require COMPLETE and x at P-1. | original governed scalar | 0 |
| MINIMUM | COMPLETE by default; scan left-to-right with exact `<`; equal keeps first; normalize -0. | value in point unit | P-1 |
| MAXIMUM | Same using `>`; equal keeps first. | value in point unit | P-1 |
| ARITHMETIC_POINT_MEAN | Require P≥1 and policy-eligible trajectory; left-to-right P additions from +0, then divide by P. | same dimension/unit semantics | P+1 |
| LEFT_RECTANGLE_INTEGRAL | Require COMPLETE fixed step; for i=0..P-2 multiply xi×step then add left-to-right. P=1 returns +0. Reject affine ABSOLUTE. | dimension(x)+TIME, canonical derived unit | 2(P-1) |
| PEAK_STEP | Require eligible MAXIMUM scan; return first maximum index. | dimensionless integer stepIndex | P-1 |
| TIME_TO_THRESHOLD | Convert threshold once, then first exact direction comparison; no interpolation. | first stepIndex plus elapsed interval; or NOT_REACHED | conversion cost + ≤P |

Empty trajectory is invalid GDSS-003 evidence. `NOT_REACHED` is a successful governed outcome for
the threshold metric, but a comparison requiring a numeric threshold result is `INELIGIBLE`.

## 8. Comparison algorithms

Both inputs must be successful results of the identical metric definition hash. Convert reference
to target's governed representation before arithmetic. Temporal compatibility is checked first.

| Operation | Binary64 formula | Output |
|---|---|---|
| ABSOLUTE_DIFFERENCE | one subtraction `target-reference` | compatible input dimension; ABSOLUTE−ABSOLUTE yields INTERVAL |
| RELATIVE_DIFFERENCE | subtraction then division by exact nonzero reference | dimensionless ratio |
| PERCENT_DIFFERENCE | relative difference then multiply by binary64 100 | dimensionless percent |
| ORDERING | exact `<`, `===`, `>` after conversion | closed ordering enum |

Exact `+0` or `-0` reference is `INELIGIBLE_REFERENCE_ZERO`; no epsilon. Invalid conversion is
`INELIGIBLE_UNIT_SEMANTICS`. Non-finite output is `FAILED_NON_FINITE_COMPARISON`.

## 9. Temporal comparability

Implement pure validators returning a closed diagnostic:

- `INITIAL_VALUE`: identical canonical start binary64 and time-unit identity.
- `FINAL_VALUE`, `MINIMUM`, `MAXIMUM`, `ARITHMETIC_POINT_MEAN`,
  `LEFT_RECTANGLE_INTEGRAL`, `PEAK_STEP`: identical start, step, stepCount, derived horizon,
  time-unit identity, ordered temporal-coordinate identity and completeness requirement.
- `TIME_TO_THRESHOLD`: all previous temporal fields plus identical threshold canonical value/unit,
  direction and completeness requirement.

No resampling, interpolation, normalization or tolerance. Failure is
`INELIGIBLE_TEMPORAL_MISMATCH` with the first canonical mismatched field.

## 10. Exact resource profile

```text
GDSS_EXPERIMENT_LIMITS_V1

canonicalDesignBytes                262,144       STORAGE
factors                             8             STRUCTURAL
valuesPerFactor                     32            STRUCTURAL
expandedScenarios                   256           COMPUTATIONAL
overridesPerScenario                32            STRUCTURAL
controlledInputs                    256           STRUCTURAL
metricDefinitions                   32            STRUCTURAL
comparisonDefinitions               64            STRUCTURAL
totalReferencedTrajectoryPoints     1,000,000     COMPUTATIONAL
aggregateReferencedTrajectoryBytes  268,435,456   STORAGE
metricOperations                    32,000,000    COMPUTATIONAL
comparisonOperations                4,096         COMPUTATIONAL
diagnostics                         512           STORAGE
concurrentScenarioDispatches        8             OPERATIONAL
dispatchAttemptsPerScenario         3             OPERATIONAL
orchestrationDurationSeconds        3,600         OPERATIONAL
manifestArtifactBytes               4,194,304     STORAGE
resultArtifactBytes                 16,777,216    STORAGE
```

The limits permit the suggested scale but prevent the unacceptable product of 256 maximum-size
GDSS-003 trajectories. Preflight uses declared upper bounds; runtime accounts exact bytes, points
and operations before admitting the next unit of work. Exceeding a budget produces no partial metric
presented as valid. Any future increase requires `GDSS_EXPERIMENT_LIMITS_V2`.

## 11. Recovery constants

```text
GDSS_EXPERIMENT_RECOVERY_V1

dispatchLeaseSeconds           60
claimDurationSeconds           60
claimBatchSize                 8
abandonmentThresholdSeconds    900
maximumDispatchAttempts        3        # initial + 2 retries
dispatchBackoffSeconds         [1,5]
maximumTerminalizationAttempts 3
terminalizationBackoffSeconds  [1,5]
recoveryScanIntervalSeconds    30
```

These are operational only and excluded from semantic hashes except the recovery policy version.
Changing values requires `GDSS_EXPERIMENT_RECOVERY_V2`.

## 12. Benchmark gates fixed before implementation

| Gate | Workload | Predeclared PASS thresholds |
|---|---|---|
| A — small reservoir | 4 scenarios, 1 factor, 10,001 points each, 3 metrics, 9 baseline comparisons, concurrency 4 | ≤15 s wall, ≤96 MiB heap delta, manifest ≤256 KiB, result ≤1 MiB, exact analytical values/hashes |
| B — medium neutral | 64 scenarios, 2,001 points each, 8 metrics, 32 comparisons, concurrency 8 | ≤90 s wall, ≤256 MiB heap delta, ≤128,064 referenced points, ≤64 MiB trajectory bytes, metric ops ≤4.5M, artifacts within governed limits |
| C — upper profile | 256 scenarios, total points 1,000,000, 32 metric definitions exercised within 32M operations, 64 comparisons, concurrency 8 | ≤300 s wall, ≤512 MiB heap delta, manifest ≤4 MiB, result ≤16 MiB, experiment-owned DB rows ≤9,300, no limit breach |

Each benchmark records scenarios, GDSS-003 attempts, points/bytes, metric/comparison operations,
artifact bytes, concurrency, wall/CPU time, heap delta, DB row counts and terminal status. Thresholds
include orchestration and evidence construction. A benchmark may use precomputed governed GDSS-003
evidence to isolate metric/artifact cost, but at least Gate A and one Gate B run exercise real
dispatch/persistence.

## 13. Exact 0042 relational schema

Migration `0042_gdss_simulation_experimentation.py`, with `down_revision="0041"`, creates exactly 15
tables. `TIMESTAMPTZ` values are audit/operational metadata and never computational identity.

### 13.1 Design tables

```sql
CREATE TABLE public.gdss_experiment_identity (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
  canonical_name TEXT NOT NULL CHECK(length(canonical_name) BETWEEN 1 AND 128),
  description TEXT NOT NULL DEFAULT '' CHECK(length(description) <= 4096),
  created_by TEXT NOT NULL CHECK(length(created_by) BETWEEN 1 AND 256),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(project_id,canonical_name), UNIQUE(id,project_id)
);

CREATE TABLE public.gdss_experiment_version (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_identity_id UUID NOT NULL,
  project_id UUID NOT NULL,
  version_number INTEGER NOT NULL CHECK(version_number > 0),
  predecessor_version_id UUID NULL,
  model_version_id UUID NOT NULL REFERENCES public.gdss_version(id) ON DELETE RESTRICT,
  binding_version_id UUID NOT NULL REFERENCES public.gdss_dynamic_binding_version(id) ON DELETE RESTRICT,
  model_content_hash CHAR(64) NOT NULL CHECK(model_content_hash ~ '^[0-9a-f]{64}$'),
  dynamic_binding_hash CHAR(64) NOT NULL CHECK(dynamic_binding_hash ~ '^[0-9a-f]{64}$'),
  research_question TEXT NOT NULL CHECK(length(research_question) BETWEEN 1 AND 4096),
  hypothesis TEXT NULL CHECK(hypothesis IS NULL OR length(hypothesis) BETWEEN 1 AND 4096),
  base_simulation_manifest JSONB NOT NULL CHECK(jsonb_typeof(base_simulation_manifest)='object'),
  base_simulation_input_hash CHAR(64) NOT NULL CHECK(base_simulation_input_hash ~ '^[0-9a-f]{64}$'),
  completeness_policy TEXT NOT NULL CHECK(completeness_policy IN ('ALL_REQUIRED_SCENARIOS','ALLOW_PARTIAL_EXPLICIT')),
  semantic_versions JSONB NOT NULL CHECK(jsonb_typeof(semantic_versions)='object'),
  canonical_design TEXT NOT NULL CHECK(octet_length(convert_to(canonical_design,'UTF8')) BETWEEN 2 AND 262144),
  experiment_design_hash CHAR(64) NOT NULL CHECK(experiment_design_hash ~ '^[0-9a-f]{64}$'),
  created_by TEXT NOT NULL CHECK(length(created_by) BETWEEN 1 AND 256),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY(experiment_identity_id,project_id) REFERENCES public.gdss_experiment_identity(id,project_id) ON DELETE RESTRICT,
  FOREIGN KEY(predecessor_version_id) REFERENCES public.gdss_experiment_version(id) ON DELETE RESTRICT,
  UNIQUE(experiment_identity_id,version_number),
  UNIQUE(experiment_identity_id,experiment_design_hash),
  UNIQUE(id,project_id)
);

CREATE TABLE public.gdss_experiment_lifecycle_event (
  id BIGSERIAL PRIMARY KEY,
  experiment_version_id UUID NOT NULL REFERENCES public.gdss_experiment_version(id) ON DELETE RESTRICT,
  sequence INTEGER NOT NULL CHECK(sequence BETWEEN 1 AND 4),
  from_status TEXT NULL CHECK(from_status IS NULL OR from_status IN ('DRAFT','VALIDATED','PUBLISHED','DEPRECATED')),
  to_status TEXT NOT NULL CHECK(to_status IN ('DRAFT','VALIDATED','PUBLISHED','DEPRECATED')),
  actor TEXT NOT NULL CHECK(length(actor) BETWEEN 1 AND 256),
  reason TEXT NOT NULL CHECK(length(reason) BETWEEN 1 AND 4096),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(experiment_version_id,sequence)
);

CREATE TABLE public.gdss_experiment_factor (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_version_id UUID NOT NULL,
  project_id UUID NOT NULL,
  ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 7),
  factor_key TEXT NOT NULL CHECK(length(factor_key) BETWEEN 1 AND 128),
  target_kind TEXT NOT NULL CHECK(target_kind IN ('PARAMETER','INITIAL_CONDITION','TEMPORAL_CONFIGURATION')),
  target_identity TEXT NOT NULL CHECK(length(target_identity) BETWEEN 1 AND 256),
  unit_identity JSONB NULL CHECK(unit_identity IS NULL OR jsonb_typeof(unit_identity)='object'),
  ordered_values JSONB NOT NULL CHECK(jsonb_typeof(ordered_values)='array' AND jsonb_array_length(ordered_values) BETWEEN 1 AND 32),
  provenance JSONB NOT NULL CHECK(jsonb_typeof(provenance)='object'),
  FOREIGN KEY(experiment_version_id,project_id) REFERENCES public.gdss_experiment_version(id,project_id) ON DELETE RESTRICT,
  UNIQUE(experiment_version_id,ordinal),
  UNIQUE(experiment_version_id,factor_key),
  UNIQUE(experiment_version_id,target_kind,target_identity),
  UNIQUE(id,experiment_version_id)
);

CREATE TABLE public.gdss_experiment_controlled_input (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_version_id UUID NOT NULL,
  project_id UUID NOT NULL,
  ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 255),
  target_kind TEXT NOT NULL CHECK(target_kind IN ('PARAMETER','INITIAL_CONDITION','TEMPORAL_CONFIGURATION')),
  target_identity TEXT NOT NULL CHECK(length(target_identity) BETWEEN 1 AND 256),
  expected_governed_value JSONB NOT NULL,
  unit_identity JSONB NULL CHECK(unit_identity IS NULL OR jsonb_typeof(unit_identity)='object'),
  FOREIGN KEY(experiment_version_id,project_id) REFERENCES public.gdss_experiment_version(id,project_id) ON DELETE RESTRICT,
  UNIQUE(experiment_version_id,ordinal),
  UNIQUE(experiment_version_id,target_kind,target_identity),
  UNIQUE(id,experiment_version_id)
);

CREATE TABLE public.gdss_experiment_metric_definition (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_version_id UUID NOT NULL,
  project_id UUID NOT NULL,
  ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 31),
  metric_key TEXT NOT NULL CHECK(length(metric_key) BETWEEN 1 AND 128),
  operation TEXT NOT NULL CHECK(operation IN ('INITIAL_VALUE','FINAL_VALUE','MINIMUM','MAXIMUM','ARITHMETIC_POINT_MEAN','LEFT_RECTANGLE_INTEGRAL','PEAK_STEP','TIME_TO_THRESHOLD')),
  metric_version TEXT NOT NULL CHECK(metric_version='GDSS_EXPERIMENT_METRICS_V1'),
  state_symbol TEXT NOT NULL CHECK(length(state_symbol) BETWEEN 1 AND 256),
  definition JSONB NOT NULL CHECK(jsonb_typeof(definition)='object'),
  definition_hash CHAR(64) NOT NULL CHECK(definition_hash ~ '^[0-9a-f]{64}$'),
  FOREIGN KEY(experiment_version_id,project_id) REFERENCES public.gdss_experiment_version(id,project_id) ON DELETE RESTRICT,
  UNIQUE(experiment_version_id,ordinal), UNIQUE(experiment_version_id,metric_key),
  UNIQUE(experiment_version_id,definition_hash), UNIQUE(id,experiment_version_id)
);

CREATE TABLE public.gdss_experiment_comparison_definition (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_version_id UUID NOT NULL,
  metric_definition_id UUID NOT NULL,
  project_id UUID NOT NULL,
  ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 63),
  comparison_key TEXT NOT NULL CHECK(length(comparison_key) BETWEEN 1 AND 128),
  operation TEXT NOT NULL CHECK(operation IN ('ABSOLUTE_DIFFERENCE','RELATIVE_DIFFERENCE','PERCENT_DIFFERENCE','ORDERING')),
  comparison_version TEXT NOT NULL CHECK(comparison_version='GDSS_EXPERIMENT_COMPARISONS_V1'),
  reference_selector JSONB NOT NULL CHECK(jsonb_typeof(reference_selector)='object'),
  target_selector JSONB NOT NULL CHECK(jsonb_typeof(target_selector)='object'),
  required_scenario_selectors JSONB NOT NULL CHECK(jsonb_typeof(required_scenario_selectors)='array'),
  temporal_policy TEXT NOT NULL CHECK(temporal_policy='GDSS_TEMPORAL_COMPARABILITY_V1'),
  definition_hash CHAR(64) NOT NULL CHECK(definition_hash ~ '^[0-9a-f]{64}$'),
  FOREIGN KEY(experiment_version_id,project_id) REFERENCES public.gdss_experiment_version(id,project_id) ON DELETE RESTRICT,
  FOREIGN KEY(metric_definition_id,experiment_version_id) REFERENCES public.gdss_experiment_metric_definition(id,experiment_version_id) ON DELETE RESTRICT,
  UNIQUE(experiment_version_id,ordinal), UNIQUE(experiment_version_id,comparison_key),
  UNIQUE(experiment_version_id,definition_hash), UNIQUE(id,experiment_version_id)
);
```

### 13.2 Artifact and execution tables

```sql
CREATE TABLE public.gdss_experiment_artifact (
  hash CHAR(64) PRIMARY KEY CHECK(hash ~ '^[0-9a-f]{64}$'),
  media_type TEXT NOT NULL CHECK(media_type IN (
    'application/vnd.midd.gdss-experiment-manifest+json;version=1',
    'application/vnd.midd.gdss-experiment-result+json;version=1')),
  format_version TEXT NOT NULL CHECK(format_version IN ('GDSS_EXPERIMENT_MANIFEST_JSON_V1','GDSS_EXPERIMENT_RESULT_JSON_V1')),
  byte_length INTEGER NOT NULL CHECK(byte_length BETWEEN 2 AND 16777216),
  payload BYTEA NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK(octet_length(payload)=byte_length),
  CHECK(encode(digest(payload,'sha256'),'hex')=hash),
  CHECK((format_version='GDSS_EXPERIMENT_MANIFEST_JSON_V1' AND byte_length<=4194304) OR
        (format_version='GDSS_EXPERIMENT_RESULT_JSON_V1' AND byte_length<=16777216))
);

CREATE TABLE public.gdss_experiment_execution_attempt (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
  experiment_version_id UUID NOT NULL,
  experiment_design_hash CHAR(64) NOT NULL CHECK(experiment_design_hash ~ '^[0-9a-f]{64}$'),
  manifest_hash CHAR(64) NOT NULL REFERENCES public.gdss_experiment_artifact(hash) ON DELETE RESTRICT,
  scenario_count INTEGER NOT NULL CHECK(scenario_count BETWEEN 1 AND 256),
  requested_by TEXT NOT NULL CHECK(length(requested_by) BETWEEN 1 AND 256),
  idempotency_key TEXT NULL CHECK(idempotency_key IS NULL OR length(idempotency_key) BETWEEN 1 AND 256),
  abort_requested BOOLEAN NOT NULL DEFAULT FALSE,
  abort_requested_by TEXT NULL,
  abort_requested_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY(experiment_version_id,project_id) REFERENCES public.gdss_experiment_version(id,project_id) ON DELETE RESTRICT,
  UNIQUE(id,project_id), UNIQUE(id,experiment_version_id),
  CHECK((abort_requested=FALSE AND abort_requested_by IS NULL AND abort_requested_at IS NULL) OR
        (abort_requested=TRUE AND abort_requested_by IS NOT NULL AND abort_requested_at IS NOT NULL))
);
CREATE UNIQUE INDEX gdss_experiment_attempt_idempotency_uq
  ON public.gdss_experiment_execution_attempt(project_id,idempotency_key)
  WHERE idempotency_key IS NOT NULL;

CREATE TABLE public.gdss_experiment_materialized_scenario (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_attempt_id UUID NOT NULL,
  project_id UUID NOT NULL,
  ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 255),
  scenario_type TEXT NOT NULL CHECK(scenario_type IN ('BASELINE','ALTERNATIVE','COUNTERFACTUAL')),
  reference_scenario_ordinal INTEGER NULL CHECK(reference_scenario_ordinal IS NULL OR reference_scenario_ordinal BETWEEN 0 AND 255),
  scenario_definition_hash CHAR(64) NOT NULL CHECK(scenario_definition_hash ~ '^[0-9a-f]{64}$'),
  simulation_input_hash CHAR(64) NOT NULL CHECK(simulation_input_hash ~ '^[0-9a-f]{64}$'),
  factor_assignments JSONB NOT NULL CHECK(jsonb_typeof(factor_assignments)='array'),
  authorized_overrides JSONB NOT NULL CHECK(jsonb_typeof(authorized_overrides)='array' AND jsonb_array_length(authorized_overrides)<=32),
  controlled_input_proof_hash CHAR(64) NOT NULL CHECK(controlled_input_proof_hash ~ '^[0-9a-f]{64}$'),
  materialized_simulation_manifest JSONB NOT NULL CHECK(jsonb_typeof(materialized_simulation_manifest)='object'),
  FOREIGN KEY(experiment_attempt_id,project_id) REFERENCES public.gdss_experiment_execution_attempt(id,project_id) ON DELETE RESTRICT,
  UNIQUE(experiment_attempt_id,ordinal), UNIQUE(experiment_attempt_id,scenario_definition_hash),
  UNIQUE(id,experiment_attempt_id), UNIQUE(id,project_id)
);

CREATE TABLE public.gdss_experiment_scenario_execution (
  id BIGSERIAL PRIMARY KEY,
  experiment_attempt_id UUID NOT NULL REFERENCES public.gdss_experiment_execution_attempt(id) ON DELETE RESTRICT,
  materialized_scenario_id UUID NOT NULL,
  sequence INTEGER NOT NULL CHECK(sequence > 0),
  state TEXT NOT NULL CHECK(state IN ('PENDING','CLAIMED','DISPATCHED','TERMINAL_SUCCESS','TERMINAL_FAILURE','NOT_DISPATCHED_ABORTED')),
  claim_token UUID NULL,
  lease_expires_at TIMESTAMPTZ NULL,
  dispatch_attempt INTEGER NOT NULL CHECK(dispatch_attempt BETWEEN 0 AND 3),
  gdss_simulation_attempt_id UUID NULL REFERENCES public.gdss_simulation_attempt(id) ON DELETE RESTRICT,
  simulation_input_hash CHAR(64) NOT NULL CHECK(simulation_input_hash ~ '^[0-9a-f]{64}$'),
  simulation_result_hash CHAR(64) NULL CHECK(simulation_result_hash IS NULL OR simulation_result_hash ~ '^[0-9a-f]{64}$'),
  trajectory_hash CHAR(64) NULL REFERENCES public.gdss_simulation_artifact(hash) ON DELETE RESTRICT,
  failure_classification TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY(materialized_scenario_id,experiment_attempt_id) REFERENCES public.gdss_experiment_materialized_scenario(id,experiment_attempt_id) ON DELETE RESTRICT,
  UNIQUE(materialized_scenario_id,sequence)
);

CREATE TABLE public.gdss_experiment_execution_event (
  id BIGSERIAL PRIMARY KEY,
  experiment_attempt_id UUID NOT NULL REFERENCES public.gdss_experiment_execution_attempt(id) ON DELETE RESTRICT,
  sequence INTEGER NOT NULL CHECK(sequence IN (1,2)),
  status TEXT NOT NULL CHECK(status IN ('RUNNING','COMPLETED','COMPLETED_WITH_FAILURES','FAILED','ABORTED')),
  result_hash CHAR(64) NULL REFERENCES public.gdss_experiment_artifact(hash) ON DELETE RESTRICT,
  completeness TEXT NULL CHECK(completeness IS NULL OR completeness IN ('COMPLETE','PARTIAL','ABORTED')),
  failure_classification TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(experiment_attempt_id,sequence)
);

CREATE TABLE public.gdss_experiment_metric_result (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_attempt_id UUID NOT NULL REFERENCES public.gdss_experiment_execution_attempt(id) ON DELETE RESTRICT,
  materialized_scenario_id UUID NOT NULL,
  metric_definition_id UUID NOT NULL REFERENCES public.gdss_experiment_metric_definition(id) ON DELETE RESTRICT,
  status TEXT NOT NULL CHECK(status IN ('SUCCEEDED','NOT_REACHED','INELIGIBLE','FAILED')),
  result JSONB NOT NULL CHECK(jsonb_typeof(result)='object'),
  result_hash CHAR(64) NOT NULL CHECK(result_hash ~ '^[0-9a-f]{64}$'),
  trajectory_hash CHAR(64) NULL REFERENCES public.gdss_simulation_artifact(hash) ON DELETE RESTRICT,
  simulation_result_hash CHAR(64) NULL CHECK(simulation_result_hash IS NULL OR simulation_result_hash ~ '^[0-9a-f]{64}$'),
  operation_count BIGINT NOT NULL CHECK(operation_count>=0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY(materialized_scenario_id,experiment_attempt_id) REFERENCES public.gdss_experiment_materialized_scenario(id,experiment_attempt_id) ON DELETE RESTRICT,
  UNIQUE(experiment_attempt_id,materialized_scenario_id,metric_definition_id),
  UNIQUE(experiment_attempt_id,result_hash), UNIQUE(id,experiment_attempt_id)
);

CREATE TABLE public.gdss_experiment_comparison_result (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_attempt_id UUID NOT NULL REFERENCES public.gdss_experiment_execution_attempt(id) ON DELETE RESTRICT,
  comparison_definition_id UUID NOT NULL REFERENCES public.gdss_experiment_comparison_definition(id) ON DELETE RESTRICT,
  reference_metric_result_id UUID NULL,
  target_metric_result_id UUID NULL,
  status TEXT NOT NULL CHECK(status IN ('SUCCEEDED','INELIGIBLE','FAILED')),
  result JSONB NOT NULL CHECK(jsonb_typeof(result)='object'),
  result_hash CHAR(64) NOT NULL CHECK(result_hash ~ '^[0-9a-f]{64}$'),
  operation_count INTEGER NOT NULL CHECK(operation_count>=0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY(reference_metric_result_id,experiment_attempt_id) REFERENCES public.gdss_experiment_metric_result(id,experiment_attempt_id) ON DELETE RESTRICT,
  FOREIGN KEY(target_metric_result_id,experiment_attempt_id) REFERENCES public.gdss_experiment_metric_result(id,experiment_attempt_id) ON DELETE RESTRICT,
  UNIQUE(experiment_attempt_id,comparison_definition_id),
  UNIQUE(experiment_attempt_id,result_hash)
);

CREATE TABLE public.gdss_experiment_diagnostic (
  id BIGSERIAL PRIMARY KEY,
  experiment_attempt_id UUID NOT NULL REFERENCES public.gdss_experiment_execution_attempt(id) ON DELETE RESTRICT,
  sequence INTEGER NOT NULL CHECK(sequence BETWEEN 1 AND 512),
  code TEXT NOT NULL CHECK(length(code) BETWEEN 1 AND 128),
  severity TEXT NOT NULL CHECK(severity IN ('ERROR','WARNING','INFO')),
  stage TEXT NOT NULL CHECK(stage IN ('DESIGN','EXPANSION','MATERIALIZATION','DISPATCH','TRAJECTORY_READ','METRIC','COMPARISON','TERMINALIZATION','ABORT','RECOVERY','PERSISTENCE')),
  materialized_scenario_id UUID NULL REFERENCES public.gdss_experiment_materialized_scenario(id) ON DELETE RESTRICT,
  details JSONB NOT NULL DEFAULT '{}' CHECK(jsonb_typeof(details)='object'),
  message TEXT NOT NULL CHECK(length(message) BETWEEN 1 AND 4096),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(experiment_attempt_id,sequence)
);
```

### 13.3 Required indexes

```sql
CREATE INDEX gdss_experiment_identity_project_idx ON gdss_experiment_identity(project_id,canonical_name);
CREATE INDEX gdss_experiment_version_identity_idx ON gdss_experiment_version(experiment_identity_id,version_number);
CREATE INDEX gdss_experiment_version_base_idx ON gdss_experiment_version(model_version_id,binding_version_id);
CREATE INDEX gdss_experiment_lifecycle_version_idx ON gdss_experiment_lifecycle_event(experiment_version_id,sequence);
CREATE INDEX gdss_experiment_attempt_project_idx ON gdss_experiment_execution_attempt(project_id,created_at);
CREATE INDEX gdss_experiment_attempt_version_idx ON gdss_experiment_execution_attempt(experiment_version_id,created_at);
CREATE INDEX gdss_experiment_scenario_attempt_idx ON gdss_experiment_materialized_scenario(experiment_attempt_id,ordinal);
CREATE INDEX gdss_experiment_scenario_input_idx ON gdss_experiment_materialized_scenario(simulation_input_hash);
CREATE INDEX gdss_experiment_scenario_event_latest_idx ON gdss_experiment_scenario_execution(materialized_scenario_id,sequence DESC);
CREATE INDEX gdss_experiment_scenario_claim_idx ON gdss_experiment_scenario_execution(state,lease_expires_at);
CREATE INDEX gdss_experiment_event_attempt_idx ON gdss_experiment_execution_event(experiment_attempt_id,sequence);
CREATE INDEX gdss_experiment_metric_attempt_idx ON gdss_experiment_metric_result(experiment_attempt_id,materialized_scenario_id);
CREATE INDEX gdss_experiment_comparison_attempt_idx ON gdss_experiment_comparison_result(experiment_attempt_id);
CREATE INDEX gdss_experiment_diagnostic_attempt_idx ON gdss_experiment_diagnostic(experiment_attempt_id,sequence);
```

### 13.4 Database functions and triggers

Migration 0042 creates exact guards:

1. `gdss_experiment_version_validate`: verifies identity/project, predecessor same identity, exact
   model/binding/project relationship, binding-model relationship, content hashes and supported
   semantic versions.
2. `gdss_experiment_design_mutation_guard`: permits INSERT/UPDATE/DELETE of version design and child
   definition rows only while latest lifecycle is DRAFT; identity keys/version lineage are never
   updateable. VALIDATED+ rejects all mutation.
3. `gdss_experiment_lifecycle_guard`: under row lock permits only NULL→DRAFT→VALIDATED→PUBLISHED→
   DEPRECATED with contiguous sequence; validation rechecks design hash and limits.
4. `gdss_experiment_attempt_guard`: requires exact project, PUBLISHED version, matching design hash,
   manifest artifact format and hash.
5. `gdss_experiment_running_guard`: before first RUNNING event locks attempt, requires sequence 1,
   exact scenario count, contiguous ordinals, at most/exactly one declared baseline according to
   comparison definitions, one PENDING scenario event per scenario, manifest hash equality and no
   prior GDSS dispatch link.
6. `gdss_experiment_scenario_event_guard`: contiguous sequence; PENDING→CLAIMED→DISPATCHED→terminal,
   or expired CLAIMED→CLAIMED retry; attempt count ≤3; exact scenario input hash; GDSS link may be
   assigned once; terminal is final; abort permits PENDING/expired CLAIMED→NOT_DISPATCHED_ABORTED.
7. `gdss_experiment_execution_event_guard`: only sequence 1 RUNNING and sequence 2 terminal; locks
   attempt; terminal requires result-format artifact with exact hash, all scenarios classified, and
   status-specific eligibility.
8. `gdss_experiment_abort_guard`: the only permitted UPDATE to attempt is false→true assignment of
   all three abort fields by authorized repository path while no terminal exists; reversal rejected.
9. `gdss_experiment_reject_evidence_mutation`: rejects UPDATE/DELETE on lifecycle events,
   materialized scenarios, scenario execution events, experiment execution events, metric results,
   comparison results, artifacts and diagnostics.
10. Deferred constraint triggers on comparison/metric rows verify definition ownership by the same
    ExperimentVersion as the attempt and exact project consistency.

Artifact INSERT performs DB `digest` equality and repository collision byte equality. Essential
integrity therefore does not depend solely on TypeScript.

## 14. Lifecycle implementation

Creation inserts the version/design rows and lifecycle event `(1,NULL,DRAFT)` in one transaction.
DRAFT edits recompute canonical design/hash atomically. Validation runs all semantic/resource gates
then inserts `(2,DRAFT,VALIDATED)`; its row lock freezes content. Publication is
`(3,VALIDATED,PUBLISHED)` and deprecation `(4,PUBLISHED,DEPRECATED)`. Only PUBLISHED may create an
execution attempt. A change after validation creates a successor DRAFT with predecessor ID and a
new version number. Lifecycle labels confer no scientific, predictive or physical authority.

## 15. Authorization implementation

Reuse `ControlActor`/OAuth session and existing exact project-role resolution; introduce no identity
store or header actor. Capability mapping is exact:

| Capability | viewer | operator | admin |
|---|---:|---:|---:|
| READ_EXPERIMENT | yes | yes | yes |
| CREATE_EXPERIMENT | no | yes | yes |
| VALIDATE_EXPERIMENT | no | yes | yes |
| PUBLISH_EXPERIMENT | no | no | yes |
| RUN_EXPERIMENT | no | yes | yes |
| DEPRECATE_EXPERIMENT | no | no | yes |
| ABORT_EXPERIMENT | no | no | yes |

Every service entry point requires `auth_source="oauth_session"`, non-empty user, exact project in
`project_ids` and effective project role. `all_projects` is accepted only under the existing trusted
admin semantics; it never arises from a request header. `RUN_SIMULATION` does not satisfy
`RUN_EXPERIMENT`.

## 16. Transaction A

Precompute and validate the complete scenario universe and manifest bytes outside the transaction
without side effects. Then one `SERIALIZABLE` repository transaction:

1. locks the PUBLISHED ExperimentVersion and latest lifecycle event;
2. resolves an existing exact idempotency row or inserts attempt;
3. inserts/byte-verifies manifest artifact;
4. inserts all materialized scenarios in ordinal order;
5. inserts one PENDING scenario-execution event per scenario;
6. inserts RUNNING event sequence 1, activating DB completeness guards;
7. writes audit `GDSS_EXPERIMENT_STARTED`;
8. commits.

No service/worker reference to dispatch is returned until commit acknowledgement. Unknown commit
resolution queries `(project_id,idempotency_key)`, then verifies version, design and manifest hashes;
exact match returns the existing attempt, mismatch fails conflict. Integration tests inject failure
at artifact, scenario, PENDING, RUNNING and audit insert and prove zero attempt-owned residue.

## 17. Dispatch orchestration

A worker transaction selects up to eight latest PENDING or expired CLAIMED scenario states for one
RUNNING non-aborted attempt, using `FOR UPDATE ... SKIP LOCKED`. It appends CLAIMED with UUID token,
`lease_expires_at=clock_timestamp()+interval '60 seconds'` and incremented dispatch attempt, then
commits before external GDSS-003 invocation.

Idempotency key:

```text
gdss-experiment:v1:<project UUID>:<manifest hash>:<scenario definition hash>
```

It is ≤256 ASCII characters and passed to GDSS-003. The GDSS-003 manifest must reproduce the
persisted `simulation_input_hash` before invocation. After acceptance, a transaction appends
DISPATCHED with exact GDSS attempt ID and input hash. After GDSS terminal evidence exists, it appends
TERMINAL_SUCCESS or TERMINAL_FAILURE with exact result/trajectory/failure identity.

A lost acknowledgement is reconciled through the same GDSS-003 idempotency key and exact hashes.
Retry occurs only for lease expiration or closed retryable transport/unknown-commit categories,
after 1 then 5 seconds, and stops after three total attempts. Semantic rejection, authorization,
resource or identity mismatch is terminal failure. Eight is the global per-process/project attempt
claim maximum; repository advisory/project locking plus row claims prevents dispatch storms across
workers. No process-local mutex is correctness-critical.

## 18. Completeness and terminal classification

Each comparison resolves its explicit reference/target selectors to exact materialized ordinals at
Transaction A and persists them inside the manifest. Required scenario set is their union unless an
explicit larger set is present.

`ALL_REQUIRED_SCENARIOS`:

- any required scenario failure/absence makes affected comparisons
  `INELIGIBLE_MISSING_REQUIRED_SCENARIO`;
- experiment terminal status is FAILED, never COMPLETED_WITH_FAILURES.

`ALLOW_PARTIAL_EXPLICIT`:

- successful scenario evidence is retained;
- every unavailable metric/comparison has explicit ineligibility;
- if at least one scenario fails/absent but remaining evidence is internally valid, status is
  COMPLETED_WITH_FAILURES;
- foundational integrity/resource/orchestration failure still yields FAILED.

COMPLETED requires every materialized required scenario TERMINAL_SUCCESS, every required metric
SUCCEEDED or a definition-valid NOT_REACHED, every required comparison SUCCEEDED, and a persisted
result artifact. FAILED uses one closed primary classification:

```text
SCENARIO_FAILURE
METRIC_FAILURE
COMPARISON_INELIGIBLE
ARTIFACT_INTEGRITY_FAILURE
ORCHESTRATION_FAILURE
RECOVERY_FAILURE
RESOURCE_LIMIT_EXCEEDED
IDENTITY_MISMATCH
```

Detailed diagnostics remain bounded structured evidence, not the status vocabulary.

## 19. Transaction B

One worker first constructs deterministic metric/comparison evidence and result bytes from a
consistent read snapshot. It then opens `SERIALIZABLE`, locks attempt and latest execution event,
revalidates all scenario terminal identities and budgets, and:

1. inserts or byte-verifies the result artifact;
2. inserts metric results in `(scenario ordinal, metric ordinal)` order;
3. inserts comparisons in comparison ordinal order;
4. inserts bounded deterministic diagnostics;
5. inserts sequence-2 terminal event with result hash/completeness/failure class;
6. writes the matching audit action;
7. commits.

Any error rolls back all Transaction B rows. Terminal states that require evidence always reference
the result artifact, including FAILED and ABORTED. Unknown commit reads sequence 2 and exact result
artifact bytes/hash; exact match returns existing terminal evidence, absence retries, conflict fails
`IDENTITY_MISMATCH`. Integration tests inject each insert/audit failure and prove no partial
terminal evidence.

## 20. Abort

An admin invokes abort only while latest experiment event is RUNNING. One transaction locks the
attempt, sets the one-way abort fields and audits `GDSS_EXPERIMENT_ABORT_REQUESTED`. Workers stop
claiming immediately. PENDING and expired CLAIMED scenarios receive append-only
NOT_DISPATCHED_ABORTED events. DISPATCHED GDSS-003 attempts are not cancelled or rewritten.

Transaction B builds an ABORTED result with every scenario classified as success/failure,
dispatched-pending-at-freeze or never-dispatched. Once ABORTED commits, late GDSS-003 terminals
remain discoverable in GDSS-003 and may be audit-linked by operational reconciliation, but they do
not insert experiment metric/comparison rows and cannot change the frozen result/event/hash.

## 21. Recovery and unknown commit

Every 30 seconds, workers claim abandoned RUNNING experiments whose latest progress is older than
900 seconds, with `FOR UPDATE ... SKIP LOCKED`. Recovery recomputes no identity from wall clock. It
reconciles the committed manifest in ordinal order:

- PENDING: eligible for normal claim;
- expired CLAIMED: exact idempotency lookup, then attach/dispatch/retry within attempt cap;
- DISPATCHED: read exact GDSS-003 attempt terminal evidence;
- terminal scenario: verify hashes and leave immutable;
- abort requested: stop new dispatch and execute abort terminalization;
- all scenario states resolved: retry Transaction B.

Two or more recovery workers can produce only one next append/event because row locks and unique
sequence constraints serialize transitions. There is no delete/rewrite compensation. Unknown
Transaction A, scenario-link and Transaction B outcomes always follow: read authoritative state,
verify exact identity/bytes, return exact existing result or retry absence. A mismatch is never
treated as success.

Reaching `orchestrationDurationSeconds=3600` closes new claims and records
`ORCHESTRATION_TIMEOUT`. Already-dispatched GDSS-003 attempts are reconciled once at that boundary
without cancellation. `ALL_REQUIRED_SCENARIOS` terminalizes FAILED with ORCHESTRATION_FAILURE;
`ALLOW_PARTIAL_EXPLICIT` may terminalize COMPLETED_WITH_FAILURES only when retained evidence is
valid and every unavailable comparison is explicit. Later GDSS-003 results remain external
immutable evidence and cannot mutate the frozen result, matching the abort late-result rule.
Wall-clock duration is audit metadata, never a hash input.

## 22. Diagnostic codes

Closed v1 codes include:

```text
INVALID_DESIGN
RESOURCE_LIMIT_EXCEEDED
CARTESIAN_OVERFLOW
DUPLICATE_FACTOR_TARGET
DUPLICATE_FACTOR_VALUE
EXPECTED_VALUE_MISMATCH
UNDECLARED_VARIATION
INVALID_UNIT_SEMANTICS
INVALID_AFFINE_OPERATION
IDENTITY_MISMATCH
CROSS_PROJECT_REFERENCE
CROSS_VERSION_REFERENCE
ARTIFACT_INTEGRITY_FAILURE
MALFORMED_TRAJECTORY
INELIGIBLE_TEMPORAL_MISMATCH
INELIGIBLE_REFERENCE_ZERO
INELIGIBLE_UNIT_SEMANTICS
INELIGIBLE_MISSING_REQUIRED_SCENARIO
NON_FINITE_METRIC
NON_FINITE_COMPARISON
DISPATCH_RETRY_EXHAUSTED
ORCHESTRATION_TIMEOUT
EXECUTION_INTERRUPTED
ABORT_REQUESTED
LATE_RESULT_AFTER_ABORT
```

## 23. Security and adversarial plan

Tests must cover scenario explosion and multiplication overflow; duplicate targets/values;
undeclared variation; expected-value mismatch; cross-project/version experiment and GDSS-003
references; trajectory/hash substitution; malformed/noncanonical artifact; same-hash/different-byte
collision defense; oversized design/manifest/result; point/byte/operation exhaustion; zero
denominator; non-finite values; invalid affine operations; temporal mismatch; duplicate dispatch;
retry storms; unauthorized create/validate/publish/run/abort/deprecate; terminal mutation; direct SQL
UPDATE/DELETE; worker-order permutation; every unknown-commit branch; and concurrent recovery.

Static tests reject imports or tokens for `eval`, `Function`, dynamic import, callbacks/plugins,
arbitrary metric/comparison expressions, filesystem, MQTT, telemetry, Control Engine, DTE, device
and actuation APIs in the pure core.

## 24. Append-only table policy

| Table | UPDATE | DELETE |
|---|---|---|
| identity | reject | reject |
| version/design children | only semantic DRAFT edit under guard; reject after VALIDATED | only DRAFT child replacement under guarded transaction; identity/version deletion rejected |
| lifecycle event | reject | reject |
| execution attempt | only one-way abort fields | reject |
| materialized scenario | reject | reject |
| scenario execution event | reject | reject |
| experiment execution event | reject | reject |
| metric/comparison result | reject | reject |
| artifact | reject | reject |
| diagnostic | reject | reject |

## 25. Migration verification plan

P012 may create only `0042_gdss_simulation_experimentation.py`. It must prove code head and DB head
0042 with one Alembic head. Under explicit test-owned empty-table verification, execute
0041→0042→0041→0042. Before downgrade query all 15 GDSS-004 tables and refuse if any unknown or
non-test evidence exists. Downgrade drops tables in reverse FK order, then guard functions; it never
modifies 0001..0041.

## 26. Regression acceptance

Future acceptance runs:

```text
focused GDSS-004 unit/security/invariant suites
GDSS_DB_TEST=1 focused GDSS-004 PostgreSQL integration suites
GDSS-001 full suite
GDSS-002 original and temporal-extension suites
GDSS-003 full 74-test suite including PostgreSQL
npm test                              # full apps/topology-next
npm run typecheck
npm run build
PYTHONPATH=src:apps/parametric-control-engine/src pytest tests
PYTHONPATH=src:apps/parametric-control-engine/src pytest apps/parametric-control-engine/tests
alembic heads/current
git diff --check
secret scan over affected files
```

Existing infrastructure-conditioned skips remain visible; every required GDSS PostgreSQL test is
also run with its enabling flag and must pass. No new functional regression is accepted.

## 27. Invariant-to-test matrix

All rows are `NOT_TESTED` during P011. Proposed test filenames use
`tests/unit/gdss-experiment.*.test.ts` and
`tests/integration/gdss-experiment.persistence.integration.test.ts`.

| ID | Statement | Enforcement | Unit test | Integration / PostgreSQL | Negative/adversarial evidence | Status |
|---|---|---|---|---|---|---|
| GDS4-INV-01 | Experiment differs from simulation execution. | types, separate tables/FKs | ontology compile/assertions | schema/FK inspection | cross-ID substitution | NOT_TESTED |
| GDS4-INV-02 | Scenario differs from simulation execution. | types, scenario mapping | identity assertions | mapping FK test | scenario ID used as attempt | NOT_TESTED |
| GDS4-INV-03 | Counterfactual is not observed history. | closed type/provenance | contract assertions | persisted provenance | forbidden observed field | NOT_TESTED |
| GDS4-INV-04 | Finding is not empirical finding. | result schema | provenance assertions | artifact round-trip | empirical classification rejected | NOT_TESTED |
| GDS4-INV-05 | Finding is not recommendation. | no recommendation field | closed-schema test | artifact projection | action/recommendation key rejected | NOT_TESTED |
| GDS4-INV-06 | Result is not prediction. | authority constants | authority test | persisted artifact | prediction field rejected | NOT_TESTED |
| GDS4-INV-07 | Scenario binds exact ExperimentVersion. | composite FKs/hash | materializer version test | cross-version FK/trigger | successor substitution | NOT_TESTED |
| GDS4-INV-08 | Scenario execution binds exact GDSS-003 evidence. | guard and exact hashes | reconciliation unit test | real GDSS link | similar/latest run rejected | NOT_TESTED |
| GDS4-INV-09 | Baseline/reference is explicit. | manifest/DB guard | selector tests | RUNNING guard | missing/duplicate baseline | NOT_TESTED |
| GDS4-INV-10 | Factors are explicit. | design schema | factor validation | factor persistence | undeclared factor | NOT_TESTED |
| GDS4-INV-11 | Controlled inputs cannot vary silently. | scenario diff proof | controlled proof test | proof hash persistence | UNDECLARED_VARIATION | NOT_TESTED |
| GDS4-INV-12 | Expansion is deterministic. | pure canonical expansion | repeated/permuted expansion | persisted ordinal comparison | map/DB order perturbation | NOT_TESTED |
| GDS4-INV-13 | Expansion is finite/bounded. | checked cardinality/limits | boundary/property tests | transaction count guard | overflow/explosion | NOT_TESTED |
| GDS4-INV-14 | Worker order cannot change semantic order. | manifest ordinal order | permutation test | concurrent completion test | reverse completion | NOT_TESTED |
| GDS4-INV-15 | Parallelism cannot change identity. | canonical projections | serial/parallel hash test | 8-worker run | scheduling perturbation | NOT_TESTED |
| GDS4-INV-16 | Failed scenario cannot be completed. | closed terminal aggregation | status matrix | terminal guard | failed-as-success insert | NOT_TESTED |
| GDS4-INV-17 | Partial evidence is explicit. | completeness policy | aggregation test | result artifact/rows | silent omission attempt | NOT_TESTED |
| GDS4-INV-18 | Metric definitions are versioned. | check/hash | version mismatch | DB CHECK | implicit latest | NOT_TESTED |
| GDS4-INV-19 | Metric dimensions are validated. | GDSS units | all metric dimension tests | persisted dimension projection | incompatible/affine cases | NOT_TESTED |
| GDS4-INV-20 | Metrics preserve simulation provenance. | hash-bound result | metric projection | real trajectory mapping | forged trajectory/result hash | NOT_TESTED |
| GDS4-INV-21 | No duplicate trajectory authority. | reference-only contracts | artifact-shape test | payload/table scan | trajectory payload injection | NOT_TESTED |
| GDS4-INV-22 | Historical results immutable. | append-only triggers | repository contract | UPDATE/DELETE rejection | direct SQL mutation | NOT_TESTED |
| GDS4-INV-23 | Model successor cannot alter history. | exact version/hash | successor identity test | FK/hash persistence | swap successor model | NOT_TESTED |
| GDS4-INV-24 | Binding successor cannot alter history. | exact version/hash | successor identity test | FK/hash persistence | swap successor binding | NOT_TESTED |
| GDS4-INV-25 | Solver successor cannot alter history. | hash-bound version | version test | artifact persistence | implicit latest solver | NOT_TESTED |
| GDS4-INV-26 | Sweep is not calibration. | no observation/fitting contract | vocabulary scan | artifact scan | calibrated status rejected | NOT_TESTED |
| GDS4-INV-27 | Exploration is not optimization. | no objective/optimizer | vocabulary/import scan | artifact scan | optimal status rejected | NOT_TESTED |
| GDS4-INV-28 | Experiment is not Digital Twin. | dependency boundary | AST/import scan | build graph check | telemetry sync import | NOT_TESTED |
| GDS4-INV-29 | Experiment is not control policy. | contract boundary | AST/import scan | service dependency scan | policy/action output | NOT_TESTED |
| GDS4-INV-30 | Physical authority is zero. | literal NONE | output assertions | artifact assertions | altered authority rejected | NOT_TESTED |
| GDS4-INV-31 | No telemetry acquisition. | pure boundary | import scan | runtime dependency scan | telemetry symbol fixture | NOT_TESTED |
| GDS4-INV-32 | No MQTT dependency. | pure boundary | import scan | package/dependency scan | MQTT import fixture | NOT_TESTED |
| GDS4-INV-33 | No Control Engine dependency. | pure boundary | import scan | dependency scan | engine import fixture | NOT_TESTED |
| GDS4-INV-34 | No DTE dependency. | pure boundary | import scan | dependency scan | DTE import fixture | NOT_TESTED |
| GDS4-INV-35 | No actuation dependency. | pure boundary | import/API scan | side-effect scan | actuation call fixture | NOT_TESTED |
| GDS4-INV-36 | Resources are bounded. | limits/counters/DB checks | every boundary ±1 | PostgreSQL/artifact limits | aggregate exhaustion | NOT_TESTED |
| GDS4-INV-37 | Identity excludes worker timing. | canonical projection | mutate metadata hash equality | reordered worker run | timestamps/retries changed | NOT_TESTED |
| GDS4-INV-38 | Same experiment reproduces manifest. | deterministic hash | exact-byte repeat test | two attempts same manifest | DB/order perturbation | NOT_TESTED |
| GDS4-INV-39 | Comparison reference is explicit. | definition schema/FK | selector resolution | persistence guard | missing target/reference | NOT_TESTED |
| GDS4-INV-40 | Science needs external authority. | authority/schema | vocabulary test | artifact scan | scientific-valid status | NOT_TESTED |
| GDS4-ARCH-INV-01 | Every scenario class changes result identity. | result projection | success/failure/absent/abort hashes differ | artifact persistence | omit failed row | NOT_TESTED |
| GDS4-ARCH-INV-02 | Temporal compatibility precedes comparison. | pure validator | metric-specific matrix | result eligibility persistence | mismatched horizon | NOT_TESTED |
| GDS4-ARCH-INV-03 | Zero reference is ineligible. | comparison guard | +0/-0 cases | ineligible row | Infinity attempt | NOT_TESTED |
| GDS4-ARCH-INV-04 | Dispatch requires committed full manifest. | Transaction A/RUNNING guard | service sequencing mock | rollback then dispatch denial | dispatch from memory | NOT_TESTED |
| GDS4-ARCH-INV-05 | No author executable metric code. | closed unions/import scan | parser/schema rejection | persisted definition check | eval/callback/dynamic import | NOT_TESTED |
| GDS4-ARCH-INV-06 | Abort preserves evidence. | append-only/abort flow | aggregation test | abort with completed rows | delete/rewrite attempt | NOT_TESTED |
| GDS4-ARCH-INV-07 | Recovery cannot duplicate scenario. | unique ordinal/hash | recovery idempotency | concurrent workers | duplicate insert | NOT_TESTED |
| GDS4-ARCH-INV-08 | Recovery cannot duplicate GDSS link. | idempotency/exact guard | reconciliation branches | concurrent dispatch link | second different attempt | NOT_TESTED |
| GDS4-ARCH-INV-09 | Missing evidence becomes INELIGIBLE. | eligibility engine | every missing branch | persisted comparison row | omission from result | NOT_TESTED |
| GDS4-ARCH-INV-10 | Completion order cannot change hashes. | canonical manifest order | permutation/property test | concurrent run hashes | reverse/chaotic order | NOT_TESTED |
| GDS4-ARCH-INV-11 | Manifest contains no trajectory bytes. | artifact schema | deep-key/payload scan | DB byte/reference inspection | embedded NDJSON | NOT_TESTED |
| GDS4-ARCH-INV-12 | One RUNNING and one terminal maximum. | execution event trigger | state matrix | concurrent terminal inserts | third event/update/delete | NOT_TESTED |

Acceptance requires all 52 rows PASS with linked test output, plus `40/40` baseline and `12/12`
architecture refinements reported separately. Documentation remains `52 NOT_TESTED` in P011.

## 28. Fixture acceptance

Reservoir fixture uses `Qin=[8,10,12,14]`, explicit baseline 10, fixed Qout/V0/time, metrics
FINAL_VALUE and LEFT_RECTANGLE_INTEGRAL, and absolute/percent/ordering comparisons. Future expected
values derive analytically from `V_i = V0 + i*dt*(Qin-Qout)` and the exact left rectangle sum.

Thermal fixture uses `k=[0.01,0.02,0.04,0.08]`, fixed initial/ambient/time, FINAL_VALUE and
TIME_TO_THRESHOLD, and is labeled only `SENSITIVITY_EXPLORATION`. Hydroponics runs only after both
neutral fixtures and may not introduce core vocabulary.

## 29. Implementation sequence for P012

1. Add contracts, versions, diagnostics and frozen limits.
2. Add canonical projections, artifact encoding and four hash identities.
3. Add design validation, canonical factor ordering, checked expansion and override/control proof.
4. Add pure trajectory reader over GDSS-003 bytes.
5. Add numeric v1 and metric engine with atomic operation budgets.
6. Add temporal validators and comparison engine.
7. Implement migration 0042 exactly, then inspect DDL constraints/triggers/indexes.
8. Implement repository primitives and append-only transaction helpers.
9. Implement authorized design/lifecycle service.
10. Implement Transaction A and unknown-commit acceptance recovery.
11. Implement bounded claim/lease/idempotent GDSS-003 dispatch worker.
12. Implement result aggregation and Transaction B.
13. Implement abort and frozen late-result behavior.
14. Implement abandoned recovery, concurrent workers and unknown-commit branches.
15. Add neutral fixtures and analytical expected values.
16. Add unit/security/adversarial suites.
17. Add PostgreSQL transaction/concurrency/append-only tests.
18. Complete and run the 52-invariant matrix.
19. Run safe 0041→0042→0041→0042 migration cycle.
20. Run full regression, three predeclared benchmarks and final diff/secret/state gates.

Each step must leave typecheck and its focused tests green before advancing. No API/UI is required
for foundation closure unless a later prompt explicitly authorizes it.

## 30. P012 acceptance gates

```text
module boundary scan                         PASS
all 52 GDSS-004 invariants                  PASS
neutral analytical fixtures                 PASS
real PostgreSQL atomicity/concurrency        PASS
append-only UPDATE/DELETE rejection          PASS
0042 code/DB single head                     PASS
safe migration cycle                         PASS
resource boundary ±1 tests                   PASS
benchmark A/B/C                              PASS
GDSS-001/002/003 regressions                 PASS
full Next / Python / Control regressions     PASS
strict typecheck and production build        PASS
git diff check and secret scan               PASS
residual test-owned DB evidence              0
```

## 31. P012 stop conditions

Stop rather than redesign if implementation requires any GDSS-001/002/003 semantic change; a new
trajectory representation or solver; arbitrary metric/comparison code; calibration, optimization,
adaptive search or prediction; telemetry, MQTT, Control Engine, DTE or physical authority; migration
beyond 0042; mutation of 0001..0041; dispatch before committed full materialization; more than one
terminal; or identities that depend on worker timing/order. Also stop on unexplained baseline drift,
unknown persistent evidence before downgrade, unbounded resource dimension or inability to make
recovery idempotent.

## 32. Authority boundary

```text
Control Engine dependency: NONE
DTE dependency:            NONE
MQTT dependency:           NONE
Telemetry binding:         NONE
Physical actuation:        NONE
Prediction authority:      NONE
Recommendation authority:  NONE
Scientific authority:      NONE
```
