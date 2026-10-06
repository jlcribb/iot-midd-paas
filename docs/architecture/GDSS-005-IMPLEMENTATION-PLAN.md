# MIDD-IOT — GDSS-005
## Governed Observation, Calibration & Model Adequacy — Implementation Plan v0.1

**Prompt:** `MIDD-GDSS-P015`

**Status:** `IMPLEMENTATION_NOT_AUTHORIZED`

**Baseline:** `main@79f5fe8efde94de817d7e3403e234d81124e632a`, Alembic `0042`

**Architecture package:** GDSS-005 P014, accepted without modification

**Contract remediation:** `MIDD-GDSS-P015-R1`; findings `P015-F01..F04` closed documentarily

**Alignment identity remediation:** `MIDD-GDSS-P015-R2`; finding `P015-F05` closed documentarily

**Relational binding & synthetic provenance remediation:** `MIDD-GDSS-P015-R3`; `P015-F06` closed documentarily; `P015-F07` closed documentarily

---

## 1. Purpose, authority and exclusions

This document turns the accepted GDSS-005 architecture into an implementation-ready, reviewable plan. It freezes contracts, relational shape, canonical encodings, deterministic algorithms, transaction boundaries, recovery rules, authorization, limits, tests and migration sequencing before code is authorized.

This plan does **not** authorize or introduce:

- migration `0043` or any database mutation;
- production TypeScript, Python, SQL, worker, API or UI code;
- tests, fixtures or runtime executions;
- changes to the six accepted P014 documents;
- interpolation, resampling, extrapolation, live telemetry acquisition or stochastic optimization;
- push, tag or remote publication.

Capabilities strengthened: **A1 Digital Twin**, **C5 Policies**, **C6 Audit**, and **A2 Benchmark**. The implementation must reuse GDSS-001 governance, GDSS-002 expressions/units, GDSS-003 simulation and GDSS-004 orchestration; it must not create a parallel control flow.

## 2. Frozen implementation profile

| Contract | Frozen value |
|---|---|
| Observation time | `GDSS_OBSERVATION_TIME_V1` |
| Dataset artifact | `GDSS_OBSERVATION_DATASET_ARTIFACT_V1` |
| Calibration manifest | `GDSS_CALIBRATION_MANIFEST_V1` |
| Residual artifact | `GDSS_CALIBRATION_RESIDUALS_V1` |
| Result artifact | `GDSS_CALIBRATION_RESULT_V1` |
| Search | `FINITE_GRID_SEARCH_V1` |
| Objectives | `RMSE_V1`, `WEIGHTED_NORMALIZED_MSE_V1` |
| Simulation solver | GDSS-003 `EXPLICIT_EULER_V1` |
| Unit conversion | GDSS-002 `GDSS_UNIT_CONVERSION_V2` |
| Identifiability | `NOT_ASSESSED` |
| Hash | SHA-256, lowercase 64-character hex |
| Database migration | proposed `0043_gdss_observation_calibration.py`, revision `0043`, down revision `0042` |

No implementation may silently substitute a contract version.

## 3. Exact temporal contract

### 3.1 Representation and range

`measurement_time_us` is an integer count of microseconds from `1970-01-01T00:00:00Z` in the proleptic Gregorian calendar. The supported UTC interval is inclusive:

- `0001-01-01T00:00:00.000000Z` = `-62135596800000000`;
- `9999-12-31T23:59:59.999999Z` = `253402300799999999`.

Both values fit PostgreSQL `BIGINT`. PostgreSQL stores `BIGINT`; TypeScript uses `bigint`; canonical JSON and every hash projection use `{"$int64":"<decimal>"}`, where the decimal member matches `^-?(0|[1-9][0-9]*)$`. JavaScript `number` is forbidden for absolute timestamps. A timestamp with more than six fractional digits is rejected, never rounded. A timestamp without an explicit UTC offset is rejected unless a governed source contract fixes one unambiguously; normalization always produces UTC.

`measurement_time_us`, `ingestion_time`, `processing_time`, GDSS-003 `simulation_time`, and worker `wall_clock_execution_time` are five distinct domains. Only `measurement_time_us` participates in alignment; the others are operational/provenance timestamps and cannot change computational identity.

### 3.2 Origin and simulation coordinate

Every calibration design fixes one explicit `measurement_time_origin_us` and binds it to the exact GDSS-003 coordinate `simulation_t0`. For a point:

```text
elapsed_us = checked_bigint_subtract(measurement_time_us, measurement_time_origin_us)
simulation_coordinate = simulation_t0 + exact_us_to_declared_time_unit(elapsed_us)
```

The implementation must reject overflow and any `abs(elapsed_us) > 9007199254740991`. Conversion divides the signed integer by the exact rational microseconds-per-unit and rounds once to IEEE-754 binary64 using the runtime's frozen conversion routine. The result is normalized from `-0` to `+0`, must be finite, and is compared with the enumerated GDSS-003 grid by canonical binary64 bits. Matching is exact; nearest-neighbour matching, tolerance windows, inferred origins, interpolation, resampling and extrapolation are forbidden.

### 3.3 Temporal validation order

1. Parse and normalize source timestamp.
2. Enforce UTC range and microsecond precision.
3. Detect duplicate coordinates within a series.
4. Subtract the explicit origin with checked `bigint` arithmetic.
5. Convert using the declared time unit and frozen unit contract.
6. Compare canonical bits against the complete GDSS-003 time grid.
7. Materialize matched/excluded evidence and enforce the minimum matched count.

## 4. Observation provenance, source allowlist and epistemic boundary

### 4.1 Closed source allowlist

Only these source types are valid:

| Source type | Required immutable evidence |
|---|---|
| `GOVERNED_FILE_ARTIFACT` | artifact identity, raw-byte SHA-256, media type, parser contract/version, original channel, physical-system identity |
| `GOVERNED_DATABASE_SNAPSHOT` | snapshot identity, database logical identity, transaction/snapshot marker, canonical export artifact identity and hash, query contract/version, original channel, physical-system identity |
| `SYNTHETIC_FIXTURE` | fixture artifact identity/hash, generator identity/version/content hash, seed if applicable, declared non-physical channel |

The following are excluded: `LIVE_MQTT`, a mutable database query, “latest” records, device lookups, URLs, remote retrieval during calibration, and any source lacking an immutable content identity. Calibration reads only governed local artifacts already admitted.

Required common fields are `source_type`, `source_identity`, `source_artifact_identity`, `source_content_sha256`, `channel_identity`, the applicable parser/query/generator contract and bounded provenance metadata. Every point additionally carries `source_record_identity` and `source_record_sha256`. `physical_system_identity` is intentionally conditional, not common: it is required for physical evidence and forbidden for synthetic evidence.

### 4.2 Epistemic origin

`epistemic_origin` is exactly one of:

- `PHYSICAL_OBSERVATION`;
- `SYNTHETIC_OBSERVATION`.

A dataset cannot mix origins. Synthetic evidence must never be relabelled physical, and physical evidence must never be silently synthesized or repaired.

For `PHYSICAL_OBSERVATION`, every source reference must be `GOVERNED_FILE_ARTIFACT` or `GOVERNED_DATABASE_SNAPSHOT`, with non-empty `physical_system_identity` and `channel_identity`. When the upstream source claims instrument-based measurement, `instrument_identity` is required and `instrument_calibration_metadata` is required when mandated/available under that governed source contract; missing provenance is never invented.

For `SYNTHETIC_OBSERVATION`, every source reference must be `SYNTHETIC_FIXTURE`, `physical_system_identity` must be SQL `NULL`, and the source must provide fixture artifact identity/content hash, generator identity/version/content hash, declared non-physical channel identity and seed when applicable. Placeholder physical identities such as `synthetic`, `none`, `N/A` or `virtual-device` are forbidden. Null is the positive epistemic assertion that no physical system supplied the observation.

The combinations `PHYSICAL_OBSERVATION + SYNTHETIC_FIXTURE`, `SYNTHETIC_OBSERVATION + physical_system_identity`, `SYNTHETIC_OBSERVATION + physical source type`, and any mixed physical/synthetic source set fail closed as `SOURCE_EPISTEMIC_ORIGIN_MISMATCH`. Derived or mixed evidence requires a future architecture and is out of scope.

## 5. Quality, uncertainty and resolution

### 5.1 Point quality contract

| Quality | Numeric value | Objective eligibility | Uncertainty | Diagnostic |
|---|---|---|---|---|
| `ACCEPTED` | required and finite | eligible after exact alignment | required; `UNKNOWN` is explicit | optional |
| `SUSPECT` | required if supplied; finite | excluded | allowed only with value | required |
| `REJECTED` | optional; finite if supplied | excluded | allowed only with value | required |
| `MISSING` | forbidden | excluded | must be `UNKNOWN` | required |
| `DEVICE_ERROR` | optional; finite if supplied | excluded | allowed only with value | required |

An `ACCEPTED` point outside the exact simulation grid fails alignment for the whole execution. Non-accepted points are retained as excluded evidence with their diagnostic. No invalid or excluded point contributes to an objective. The design's minimum matched count is checked after all exclusions.

### 5.2 Uncertainty contract

The only modes are:

- `UNKNOWN`: no numeric bound;
- `ABSOLUTE_BOUND`: finite `bound >= 0` in the series unit;
- `RELATIVE_BOUND`: finite dimensionless `bound >= 0`.

Zero is a valid known bound and is distinct from `UNKNOWN`. Resolution is a separate optional finite value strictly greater than zero in the series unit; it is not uncertainty and never supplies an objective weight implicitly.

## 6. Lifecycle and immutability

Datasets and calibration designs use `DRAFT → VALIDATED → PUBLISHED → DEPRECATED`.

- `DRAFT`: editable only while no execution attempt references the version.
- `VALIDATED`: content frozen; publication metadata may be added through a governed transition.
- `PUBLISHED`: the only state eligible for new execution; immutable.
- `DEPRECATED`: immutable, blocks new attempts, preserves historical validity.

A successor is a new identity version copied into `DRAFT`; mutation-in-place is forbidden. Once any attempt references a version, a database trigger freezes it even if it remains `DRAFT`. Lifecycle events are append-only and monotonically sequenced.

A CalibrationDesign is validated and published solely from its frozen declarative content, including `AlignmentSpecification`. Publication does not require an execution attempt, `AlignmentResult`, `alignment_hash`, simulation result, residual, estimate or adequacy result. Static validation proves that mappings and references resolve, dimensions/units and `ABSOLUTE|INTERVAL` semantics are compatible, temporal origin and `simulation_t0` relationship are declared, policy versions are supported, minimum matched count is structurally valid, quality/exclusion rules are closed, interpolation/resampling/extrapolation are absent, and objective requirements are structurally satisfiable. It cannot claim that all points will match, calibration will succeed or fit will be acceptable.

Dataset role is contextual (`CALIBRATION`, `VALIDATION`, `HOLDOUT`, `EXPLORATORY`) and belongs to a calibration dataset assignment, not to intrinsic dataset content. V1 fitting consumes only `CALIBRATION`; the other roles are reserved and must not influence grid, objective, winner selection or adequacy. Therefore `observation_dataset_hash` excludes role, while `calibration_design_hash` includes each assignment and its role. This is the necessary literal reconciliation of P015's “dataset hash includes dataset role” phrase with the accepted P014 architecture; it changes no P014 document and prevents one immutable dataset from acquiring contradictory intrinsic identities.

## 7. Canonical encoding and content addressing

### 7.1 Canonical JSON profile

All JSON artifacts use UTF-8 without BOM, lexicographically sorted object keys, no insignificant whitespace and semantic array order. Binary64 values use the existing canonical object `{"$binary64":"<16 lowercase hex digits>"}` after normalizing `-0` to `+0`; non-finite values are rejected. Signed 64-bit integers use `{"$int64":"<canonical decimal>"}`. UUIDs are lowercase hyphenated strings. JSON artifacts have no trailing newline.

NDJSON artifacts consist of one independently canonical JSON object per line, UTF-8, LF only, including a final LF. Record order is part of identity and is specified per artifact. Artifact byte hashes are SHA-256 of the exact bytes.

### 7.2 Authoritative identity taxonomy

| Identity class | Meaning | Examples | Hash participation |
|---|---|---|---|
| computational/content | what governed content was supplied, computed and obtained | dataset, alignment, design, parameter vector, estimate set, result and artifact content hashes | derived only from canonical semantic content |
| operational execution | which execution activity produced or transported evidence | calibration attempt UUID, GDSS-003 attempt identity, worker, claim token, lease, retry and transport idempotency key | excluded from computational hashes |
| governance/audit | who authorized, reviewed or published institutional evidence | actor, review, publication, authorization and audit identities | excluded from computational hashes; linked relationally |

The classes may reference one another through typed governed relationships, but are never conflated. The digest input for computational hashes is `UTF8(domain) || 0x00 || canonical_payload_bytes`.

| Computational identity | Domain | Exact ordered projection |
|---|---|---|
| `observation_dataset_hash` | `midd:gdss:observation-dataset:v1` | version contract; epistemic origin; sources by ordinal; series by ordinal; points by series/point ordinal; values, coordinates, quality, uncertainty, resolution and source-provenance hashes |
| `calibration_design_hash` | `midd:gdss:calibration-design:v1` | exact `gdss_identity.id`, `gdss_version.id/version_number/content_hash`, `gdss_dynamic_binding.id`, `gdss_dynamic_binding_version.id/version_number/dynamic_binding_hash`; ordered dataset assignments/hashes/roles; canonical `AlignmentSpecification`; ordered parameter base values, units, bounds, grids/fixed overrides; objective/scales/weights; predeclared adequacy criteria; search, GDSS-002/GDSS-003 solver/time/trajectory and resource/recovery versions. It excludes `alignment_hash` and every execution-derived outcome. |
| `alignment_hash` | `midd:gdss:observation-alignment:v1` | calibration design hash; ordered dataset hashes; canonical `AlignmentSpecification` projection; simulation grid manifest hash; origin and `simulation_t0`; time/unit conversion contracts; ordered mapping identities; every matched/excluded point outcome, converted value, simulation coordinate, quality disposition and exclusion reason |
| `parameter_vector_hash` | `midd:gdss:calibration-parameter-vector:v1` | ordered model parameter identities and canonical candidate values |
| `parameter_estimate_set_hash` | `midd:gdss:parameter-estimate-set:v1` | design hash; ordered observation dataset hashes; alignment hash; winning candidate ordinal/vector hash; objective version and canonical result bits; canonical tie rule; exact selected GDSS-003 computational input/result/trajectory content hashes and solver contract; ordered parameter identities, base/estimated values, units, bounds and grid/axis hashes; exact model and dynamic-binding identities/versions/hashes |
| `calibration_result_hash` | `midd:gdss:calibration-result:v1` | design hash; ordered observation dataset hashes; alignment hash; estimate-set hash; residual artifact semantic/content hash; canonical model-adequacy semantic content/hash; semantic result outcome `ESTIMATE_COMPUTED`; ordered semantic diagnostics that qualify result meaning |

`calibration_design_hash` is computable before publication and excludes `alignment_hash`, runtime match/exclusion outcomes, alignment manifest bytes, candidate/GDSS-003 evidence, residuals, winner, estimates, adequacy result and every operational/governance identity. No separate `alignment_specification_hash` is introduced because the specification has no independent governance lifecycle; its canonical projection is directly part of design identity. `alignment_hash` is execution-admission evidence and binds the already-frozen design hash, never the reverse.

Changing only `binding_version_id`, its governed `version_number`, or `dynamic_binding_hash` is a semantic design change and changes `calibration_design_hash` even if numerical simulation behavior happens to be equivalent. The same binding identity with a successor version/hash also changes the design hash and every valid downstream computational identity while unrelated observation dataset hashes remain unchanged. “Latest”, display-name resolution, runtime inference and mutable lookup are forbidden.

`parameter_estimate_set_hash` deliberately excludes adequacy because adequacy is computed from the selected estimate and residuals after the estimate exists. `calibration_result_hash` depends on both and closes the DAG without a back-edge. All computational hashes exclude calibration/GDSS-003 attempt UUIDs, actor, worker, claim/lease, retry count/timing, wall-clock timestamps, audit/publication/reviewer identities, transport idempotency keys and database sequences. Attempt terminal state is operational and is excluded from `calibration_result_hash`; its semantic consequences are already represented by adequacy and semantic diagnostics. A failed or aborted attempt that cannot materialize a valid estimate has no calibration result hash.

The relational point UUID is its reference identity and point ordinal is authoritative content order. There is no independent point semantic hash: source-record hash plus dataset hash is the governed evidence boundary. The five top-level computational identities remain dataset, alignment, design, estimate-set and result hashes; parameter-vector hashes are subordinate candidate identities.

### 7.3 Acyclic hash dependency graph

```text
ObservationDataset ──> observation_dataset_hash ─────────────────┐
          │                                                       │
          ▼                                                       │
CalibrationDesign                                                │
  └── AlignmentSpecification                                     │
          │                                                       │
          ▼                                                       │
calibration_design_hash                                          │
          ├────────────────────────────┐                          │
          ▼                            ▼                          │
AlignmentResult                 Candidate Universe                │
          │                            │                          │
          ▼                            ▼                          │
alignment_hash                 parameter_vector_hashes            │
          │                            │                          │
          │                            ▼                          │
          │                GDSS-003 computational evidence        │
          │                            │                          │
          └──────────────┬─────────────┘                          │
                         ▼                                        │
              ParameterEstimateSet <──────────────────────────────┘
                         │
                         ▼
              parameter_estimate_set_hash
                         │
                ┌────────┴────────┐
                ▼                 ▼
            Residuals       Model Adequacy
                └────────┬────────┘
                         ▼
               CalibrationResult
                         │
                         ▼
              calibration_result_hash
```

There is no dependency from design to `alignment_hash`, and no dependency from result or adequacy back into the estimate set. The graph has **no hash cycle** and **no temporal materialization cycle**: declarative design exists before execution; `AlignmentResult` and `alignment_hash` exist only after governed admission applies that design.

### 7.4 Artifact formats

| Artifact | Media type | Canonical record order |
|---|---|---|
| `GDSS_OBSERVATION_DATASET_ARTIFACT_V1` | `application/vnd.midd.gdss-observation-dataset+ndjson;version=1` | header; sources by ordinal; series by ordinal; points by series ordinal then point ordinal |
| `GDSS_CALIBRATION_MANIFEST_V1` | `application/vnd.midd.gdss-calibration-manifest+json;version=1` | canonical JSON containing design/dataset/grid/universe bindings and an `alignment_result` section ordered by mapping, series and point ordinal |
| `GDSS_CALIBRATION_RESIDUALS_V1` | `application/vnd.midd.gdss-calibration-residuals+ndjson;version=1` | header; residuals by series key then point ordinal; exclusions by same order; summary |
| `GDSS_CALIBRATION_RESULT_V1` | `application/vnd.midd.gdss-calibration-result+json;version=1` | canonical JSON |

Artifacts use the existing DB-backed byte storage pattern so metadata and bytes can commit atomically. External object storage is out of scope for v1.

## 8. Exact mappings and alignment

### 8.1 AlignmentSpecification

`AlignmentSpecification` is the declarative governed component of CalibrationDesign known before validation/publication. It is represented by typed fields in `gdss_calibration_version`, dataset assignments and series mappings plus their canonical design projection; it is not a new table and has no separate top-level hash.

Its exact content is: alignment contract/version `EXACT_COORDINATE_MATCH_V1`; `measurement_time_origin_us ↔ simulation_t0`; declared simulation time unit; time and unit conversion contract versions; exact-match policy; explicit `NONE` for interpolation, resampling and extrapolation; ordered series-to-model-variable mappings; quantity identities; dimension requirements; source/target units; `ABSOLUTE|INTERVAL`; objective-inclusion declarations; minimum matched count; the closed point-quality eligibility policy; explicit missing/excluded evidence policy; duplicate-coordinate fail-closed policy; and non-finite fail-closed policy. Semantics already present in typed design/mapping fields are referenced once in canonical order rather than duplicated.

Each mapping binds the exact `SystemModelVersion`, exact `DynamicModelBindingVersion`, dataset series identity and exact GDSS model variable identity. Display names are never resolution keys; zero or multiple identity matches fail. Unit dimensions and absolute/interval semantics must match before conversion.

### 8.2 Repository binding identity reconciliation

The committed GDSS-001/003 representation is authoritative:

| Concept | Actual repository relation/type | Immutable identity/content proof |
|---|---|---|
| SystemModel identity | `public.gdss_identity` / `SystemModelIdentity` | `id`, project ownership; immutable trigger |
| SystemModelVersion | `public.gdss_version` / `SystemModelVersion` | `id`, `identity_id`, `version_number`, `content_hash`; `UNIQUE(identity_id,id)` and governed freeze |
| DynamicModelBinding identity | `public.gdss_dynamic_binding` | `id`, `project_id`; append-only and unique project/name |
| DynamicModelBindingVersion | `public.gdss_dynamic_binding_version` / `DynamicBindingSnapshot` | `id`, `binding_id`, `version_number`, `model_version_id`, canonical content, `dynamic_binding_hash`; append-only |

`gdss_dynamic_binding_version.model_version_id` is a restrictive FK to `gdss_version(id)`, and `UNIQUE(id,model_version_id)` supplies the exact binding-version/model-version relational target already used by GDSS-003. `dynamic_binding_hash` is SHA-256 over canonical `gdss-dynamic-binding:v1` semantic content and includes the exact model/content relationship. Binding lifecycle events establish `DRAFT → PUBLISHED → DEPRECATED`; only a published immutable binding is executable. No GDSS-003 contract change is required.

One CalibrationDesign binds exactly one DynamicModelBindingVersion at design level. Series mappings do not duplicate binding identity; their targets are validated inside that frozen model/binding context. A future need for multiple bindings in one design is `REQUIRES_GDSS_005_ARCHITECTURE_REVIEW`.

Before `VALIDATED`, static validation must prove: the exact model version and binding version exist; both projects match the calibration project; the binding version belongs to the exact model version and identity; stored model/binding version numbers and content hashes reconcile; both references meet their lifecycle requirements; every fixed/calibrated parameter belongs to the exact model version and binding parameter set; every mapping target resolves exactly once within the intersection of model artifacts and binding state/algebraic/output context; zero, multiple and cross-version matches fail; and deprecated historical references remain readable but are never replaced implicitly by successors. Any contradiction is semantic `MODEL_BINDING_MISMATCH`, never `UNKNOWN_QUANTITY_MAPPING`.

### 8.3 AlignmentResult

`AlignmentResult` is immutable **derived computational evidence**, created only during governed execution admission by applying the frozen specification to the exact published design/hash, observation dataset versions/hashes, simulation temporal grid manifest, mappings, temporal origin and conversion contracts. It is neither observed, simulated, predicted, a calibrated parameter nor scientific validation; it links observation evidence to simulation coordinates without erasing either origin.

The epistemic separations are invariant: `OBSERVED ≠ SIMULATED`; `ALIGNMENT ≠ OBSERVATION`; `ALIGNMENT ≠ SIMULATION`; `ALIGNMENT ≠ CALIBRATION RESULT`; `CALIBRATION ≠ VALIDATION`; `FIT ≠ PREDICTION`; and `CALIBRATED PARAMETER ≠ TRUE PARAMETER`.

The `alignment_result` section of `GDSS_CALIBRATION_MANIFEST_V1` contains every relevant source point exactly once as `MATCHED` or `EXCLUDED`, with deterministic reason, source point/dataset/series/mapping identities and hash, quality disposition and, when applicable, canonical simulation coordinate, converted observation value and target trajectory coordinate. There is no silent omission. Canonical order is mapping identity, series ordinal, then point ordinal. Recomputing the same design, datasets, grid and specification must yield byte-identical section content and `alignment_hash` regardless of attempt UUID, worker, concurrency, retries or wall-clock time.

At admission, canonical recomputation from governed inputs must reconcile relational references and manifest bytes. A supplied arbitrary hash or mismatch fails closed as `ARTIFACT_RECONCILIATION_FAILURE` or `IDENTITY_MISMATCH`; neither artifact nor database projection wins. No new artifact kind is required.

## 9. Finite candidate universe

`FINITE_GRID_SEARCH_V1` is exhaustive and deterministic:

1. Sort calibrated parameters by exact model parameter identity using UTF-8 byte order.
2. Normalize each declared candidate value to canonical binary64; reject non-finite values and semantic duplicates, including `-0/+0`.
3. Sort each value list by finite numeric ascending order, breaking impossible equalities by canonical bits.
4. Enumerate the Cartesian product with the last parameter varying fastest.
5. Assign contiguous ordinal `0..N-1` and compute the domain-separated parameter-vector hash.
6. Persist the entire `PENDING` universe and its manifest before any GDSS-003 dispatch.

Every parameter binds its exact model parameter identity, base value, unit, lower and upper bounds. Calibrated axes additionally carry a finite, dimension-compatible, in-bounds, canonical, non-empty value list; fixed overrides carry one in-bounds value. No grid is generated at runtime. Fixed parameters are frozen in the design manifest but are not axes. The selected candidate is the feasible candidate with the least objective value; canonical binary64-bit equality is a tie, resolved by the lowest candidate ordinal.

## 10. Deterministic objective arithmetic

All observations are converted first with `GDSS_UNIT_CONVERSION_V2`. All operations are IEEE-754 binary64 in the explicit order below; fused multiply-add, parallel reductions and extended-precision accumulation are forbidden. After each operation, normalize `-0` to `+0` and reject NaN or infinity. Finite subnormals and underflow to zero are preserved as produced by the frozen runtime.

For `RMSE_V1`, exactly one included series is permitted, so cross-dimensional aggregation is impossible and the result has that series' dimension/unit. Iterate its points by ordinal. For each point compute `r = observed - simulated`, then `q = r * r`, then left-fold `sum = sum + q`. Require `n > 0`, divide once by `n` and call the frozen square-root routine once.

For `WEIGHTED_NORMALIZED_MSE_V1`, iterate series by mapping key. For every point compute `r`, `z = r / normalization_scale`, `q = z * z`, and left-fold the series sum. Divide once by the series matched count, multiply once by the series weight, and left-fold the weighted numerator. Left-fold the weights independently and divide numerator by total weight once. Scale and weight must be finite and strictly positive.

The residual artifact records observed, simulated, residual and objective contribution canonical bits for every matched point. An empty objective, zero total weight or a non-finite intermediate is terminal failure, never a candidate winner.

## 11. Relational design: exact 21-table proposal

All UUID PKs use application-generated UUIDs. All timestamps are `TIMESTAMPTZ NOT NULL`. Hashes use `CHAR(64)` plus lowercase-hex checks. Enumerations are `TEXT` plus closed `CHECK` constraints to keep migration evolution explicit. JSON payloads are `JSONB` only for bounded diagnostic/provenance extensions; governed semantic fields remain typed columns. Foreign-key deletion is `RESTRICT`. Every append-only table gets a trigger rejecting `UPDATE` and `DELETE`.

All 21 tables are project-owned through a direct or transitive project FK, are owned by the same database owner used by migration `0042`, and grant application writes only to the official `apps/topology-next` backend role. Workers receive no direct ad-hoc mutation authority; repository transactions are the write boundary. No table uses cascading evidence deletion.

### 11.1 Observation tables (6)

1. **`gdss_observation_dataset_identity`** — `id` PK; `project_id` FK; stable `dataset_key`; created actor/time. Unique `(project_id,dataset_key)`. Index `(project_id,created_at)`.
2. **`gdss_observation_dataset_version`** — `id` PK; identity FK; positive `version_number`; `epistemic_origin` (`PHYSICAL_OBSERVATION|SYNTHETIC_OBSERVATION`); `state`; contract versions; optional dataset/artifact hashes until validation; created/validated/published/deprecated actor/time; row version. Unique `(dataset_identity_id,version_number)`, partial unique on non-null `dataset_hash`, checks for state metadata and origins. Index `(dataset_identity_id,state)` and `(dataset_hash)`. Origin is stored only here and is immutable once validated/referenced; it is not duplicated into source rows.
3. **`gdss_observation_source_reference`** — `id` PK; version FK; positive ordinal; source type/identity, artifact/fixture identity and hash, channel, nullable physical-system/instrument metadata, parser/query identity, nullable generator identity/version/content hash/seed and bounded provenance. Unique `(dataset_version_id,ordinal)` and `(dataset_version_id,source_identity)`. Row-local checks require physical-system/channel for physical source types and forbid synthetic-generator fields; for `SYNTHETIC_FIXTURE` they require complete fixture/generator/non-physical-channel provenance and `physical_system_identity IS NULL`. A cross-row source-origin guard locks/reads the parent dataset origin and enforces the exact allowed pairing; lifecycle validation rescans all sources before `VALIDATED`. Index artifact hash, `(dataset_version_id,source_type)` and non-null physical-system identity.
4. **`gdss_observation_series`** — `id` PK; version FK; positive ordinal; exact series key, quantity identity, dimension, unit, uncertainty/resolution defaults. Unique `(dataset_version_id,ordinal)` and `(dataset_version_id,series_key)`. Index quantity identity.
5. **`gdss_observation_point`** — `id` PK; series FK; source-reference FK; non-negative ordinal; `measurement_time_us BIGINT`; optional binary64 value bits; quality; uncertainty mode/bound bits; resolution bits; source-record identity/hash; diagnostic code/details. Unique `(series_id,ordinal)`, `(series_id,measurement_time_us)`, and `(series_id,source_record_identity)`. Checks implement the quality/uncertainty matrix. Index `(series_id,measurement_time_us)` and source-record hash.
6. **`gdss_observation_dataset_lifecycle_event`** — `id` PK; version FK; positive sequence; from/to state; actor; reason; event time; resulting dataset hash. Unique `(dataset_version_id,sequence)`. Index `(dataset_version_id,event_time)`; append-only.

Source-origin cardinality enforcement is explicitly layered. `PG` enforces closed source/origin vocabularies, field nullability/shape, source-type conditional checks and parent FK; the `gdss005_guard_source_origin` trigger enforces parent-origin/source-type consistency and blocks incompatible parent-origin change. `APP` verifies raw artifact/generator hashes, declared non-physical channel semantics and conditional instrument contract metadata. `BOTH` rescan the complete source set on validation/admission, reject mixed origin and emit `SOURCE_EPISTEMIC_ORIGIN_MISMATCH`. No child copy of `epistemic_origin` is introduced.

### 11.2 Calibration design tables (6)

7. **`gdss_calibration_identity`** — `id` PK; project FK; stable `calibration_key`; created actor/time. Unique `(project_id,calibration_key)`.
8. **`gdss_calibration_version`** — `id` PK; identity FK; positive version; state; `model_identity_id UUID` FK `gdss_identity(id)`; `model_version_id UUID`, `model_version_number INTEGER`, `model_content_hash CHAR(64)`; `binding_id UUID` FK `gdss_dynamic_binding(id)`; `binding_version_id UUID`, `binding_version_number INTEGER`, `dynamic_binding_hash CHAR(64)`; search/objective/time/unit contracts; origin; minimum match; design hash; resource/recovery profile versions; lifecycle actor/times. Restrictive composite FKs are `(model_identity_id,model_version_id) → gdss_version(identity_id,id)` and `(binding_version_id,model_version_id) → gdss_dynamic_binding_version(id,model_version_id)`; `binding_version_id` also references its PK and a guard proves its `binding_id`, version number, project, lifecycle and hash equal the stored typed projection. Unique `(calibration_identity_id,version_number)`, partial unique design hash. Positive-version/lowercase-hash and state/objective checks; indexes `(model_version_id)`, `(binding_version_id)`, `(model_identity_id,model_version_number)`, `(binding_id,binding_version_number)`, design/model/binding hashes and lifecycle state. These columns freeze with the design and no latest/display-name/runtime resolution is legal.
9. **`gdss_calibration_dataset_assignment`** — `id` PK; calibration version FK; dataset version FK; positive ordinal; role; assignment weight bits. Unique `(calibration_version_id,ordinal)` and `(calibration_version_id,dataset_version_id,role)`. Role check `CALIBRATION|VALIDATION|HOLDOUT|EXPLORATORY`; only `CALIBRATION` contributes to fitting.
10. **`gdss_calibration_series_mapping`** — `id` PK; assignment FK; observation series FK; exact version-local model quantity identity; mapping key; source/target unit and dimension; `ABSOLUTE|INTERVAL`; conversion contract; included flag; scale/weight bits. Unique `(dataset_assignment_id,mapping_key)` and `(dataset_assignment_id,observation_series_id)`. Checks objective fields; indexes quantity identity. It does not duplicate binding identity: validation resolves the target exactly once inside the design-level `model_version_id + binding_version_id` context and rejects zero, multiple, cross-version or outside-binding targets.
11. **`gdss_calibration_parameter`** — `id` PK; calibration version FK; parameter identity; positive ordinal; base value/unit/lower/upper bound bits; mode `CALIBRATED|FIXED`; fixed value bits; candidate-values canonical JSON; candidate count; axis hash. Unique `(calibration_version_id,ordinal)` and parameter identity. Checks calibrated/fixed exclusivity, dimensions, finite values and inclusive bounds.
12. **`gdss_calibration_lifecycle_event`** — analogous to observation lifecycle, with unique version/sequence and resulting design hash; append-only.

### 11.3 Execution and evidence tables (9)

13. **`gdss_calibration_artifact`** — `id` PK; project FK; artifact kind/version/media type; raw bytes `BYTEA`; byte length; content SHA-256; semantic hash when applicable; created actor/time. Unique `(project_id,content_sha256,artifact_kind,artifact_version)`; byte-length/hash trigger; immutable.
14. **`gdss_calibration_execution_attempt`** — `id` PK; calibration version FK; positive `attempt_number`; admission identity/idempotency key; design/model and ordered dataset hashes; alignment hash; calibration-manifest artifact FK; recovery/resource profiles; requested actor/time; abort requested actor/time/reason; operational terminal state/time. Unique `(calibration_version_id,attempt_number)` and `(project_id,idempotency_key)` through denormalized project FK; indexes terminal/state timestamps. Governed columns are immutable except the one-way abort request and one-way terminalization guarded by triggers. The attempt references `alignment_hash`; its UUID and terminal state never enter that or any computational hash.
15. **`gdss_calibration_execution_event`** — `id` PK; attempt FK; positive sequence; `event_class` (`COMPUTATIONAL_EXECUTION_EVENT|GOVERNANCE_PUBLICATION_EVENT`); typed `event_type`; actor/worker; event time; reason; result artifact/hash; audit-correlation identity and manifest/artifact refs. Unique `(attempt_id,sequence)`; partial unique `(attempt_id)` for computational terminal event types and partial unique `(attempt_id,result_hash)` for `RESULT_PUBLISHED`; append-only. Computational sequence begins `ACCEPTED`, continues `RUNNING` and receives exactly one terminal alternative. A later governance event `RESULT_PUBLISHED` is permitted without changing the terminal event or attempt state. Absence/presence of that typed event is authoritative `UNPUBLISHED|PUBLISHED` state.
16. **`gdss_calibration_candidate_evaluation`** — `id` PK; attempt FK; candidate ordinal; positive sequence; parameter-vector hash and canonical vector; state; claim token/worker/lease; dispatch attempt; GDSS-003 execution/attempt identities; objective bits; failure code; trajectory and residual artifact refs; created time. Unique `(attempt_id,candidate_ordinal,sequence)`, `(attempt_id,parameter_vector_hash,sequence)`; index `(attempt_id,state,candidate_ordinal)` and lease expiry. Sequence 1 is immutable `PENDING` and is the stable row-lock root; later rows are append-only state events. Terminal candidate states cannot recur.
17. **`gdss_calibration_parameter_estimate_set`** — `id` PK; attempt FK unique; selected candidate ordinal/hash; objective/version/bits; model/binding, dataset/alignment/design and selected GDSS-003 computational evidence references; estimate-set hash; tie rule; created time. Non-unique index on estimate-set hash permits distinct legitimate attempts to reproduce the same computational identity; immutable.
18. **`gdss_calibration_parameter_estimate`** — `id` PK; estimate-set FK; positive ordinal; parameter identity; base/estimated value, unit, lower/upper bound and grid/axis hash. Unique `(estimate_set_id,ordinal)` and parameter identity; immutable.
19. **`gdss_model_adequacy_assessment`** — `id` PK; attempt FK unique; classification; declared criteria/hash; residual-summary artifact FK; reserved validation/holdout metrics; `identifiability='NOT_ASSESSED'`; bounded rationale; created time. Closed classification check; immutable.
20. **`gdss_calibration_estimate_review`** — `id` PK; estimate-set FK; positive sequence; decision `ACCEPT_FOR_SUCCESSOR_PROPOSAL|REJECT`; reviewer; reason; event time. Unique `(estimate_set_id,sequence)`; one terminal decision enforced by trigger; append-only. Absence of a row is the unreviewed state.
21. **`gdss_calibration_diagnostic`** — `id` PK; attempt FK; optional candidate ordinal/point FK; positive sequence; `diagnostic_class` (`SEMANTIC|OPERATIONAL`); stage; severity; closed diagnostic/failure code; canonical semantic-content hash when class is semantic; bounded details; time. Unique `(attempt_id,sequence)`; indexes class/failure/stage/candidate; append-only. Operational actor, timing and retry details remain execution evidence and are excluded from computational hashes.

### 11.4 Trigger and FK rules

Before mutation, lifecycle triggers lock the parent version, validate legal transition and actor capability, and assign the next sequence under the same transaction. Freeze triggers reject changes to any version content at `VALIDATED` or later, and to any version referenced by an attempt. Candidate insertion locks its sequence-1 root, requires `sequence = max+1`, validates the transition/lease token and forbids a second terminal state. Execution-event insertion locks the attempt, applies monotonic sequence, enforces exactly one computational terminal event and permits only the typed governance publication event afterward. Estimate/result rows require a reconciled complete candidate universe before terminalization. Publication requires a terminal result but never mutates it. Artifact FKs are deferrable initially deferred only within finalization/publication transactions; no committed dangling reference is possible.

## 12. Transaction, concurrency and recovery model

### 12.1 Admission transaction

At `SERIALIZABLE`, admission follows this order:

1. receive the authorized `RUN_CALIBRATION` request;
2. resolve and lock the exact `PUBLISHED` CalibrationDesign;
3. verify its frozen `calibration_design_hash`, computed solely from pre-execution semantics;
4. resolve and lock every exact `PUBLISHED` ObservationDataset version assigned by the design;
5. verify the ordered `observation_dataset_hash` values;
6. resolve and freeze the exact GDSS-003 temporal-grid contract/manifest required by the design, without dispatching a simulation;
7. apply the frozen `AlignmentSpecification` to those exact inputs;
8. materialize canonical `AlignmentResult` in memory;
9. compute `alignment_hash` from design hash, datasets, grid, specification and outcomes;
10. verify minimum matched count and every alignment gate;
11. enumerate/materialize the complete canonical candidate universe;
12. materialize `GDSS_CALIBRATION_MANIFEST_V1`, binding design hash, ordered dataset hashes, alignment result/hash, universe, GDSS-002/003 contracts and resource/recovery profiles;
13. allocate or reconcile the idempotent governed execution attempt;
14. persist attempt, manifest bytes, alignment reference and all sequence-1 `PENDING` candidates;
15. append `ACCEPTED` then `RUNNING` plus institutional audit evidence;
16. commit all DB-backed bytes and metadata atomically;
17. only after commit may any GDSS-003 candidate dispatch begin.

On serialization or constraint failure, retry the whole transaction with the same operational idempotency key and recompute/reconcile alignment from immutable inputs; after the retry budget, emit no partial attempt. No dispatch can occur before complete alignment plus candidate-universe commit.

The attempt graph is exactly `ACCEPTED → RUNNING → {COMPLETED, COMPLETED_WITH_WARNINGS, FAILED, ABORTED}`. Braced states are mutually exclusive terminal alternatives and exactly one is allowed. Attempt state `SUCCEEDED` does not exist.

- `COMPLETED`: the entire declared universe is reconciled, a valid winner and immutable result are materialized, and no semantic diagnostic of severity `WARNING|ERROR|FATAL` qualifies that result.
- `COMPLETED_WITH_WARNINGS`: the same complete valid result exists, with one or more result-bound `SEMANTIC/WARNING` diagnostics and no semantic `ERROR|FATAL`; examples are poor fit under predeclared criteria, equivalent minima or a declared comparability limitation.
- `FAILED`: no valid calibration result can be materialized because of an unrecoverable computational/orchestration failure, no feasible candidate, or semantic/operational `ERROR|FATAL` that prevents complete governed evidence.
- `ABORTED`: an authorized nonterminal abort governs the final outcome; late evidence remains historical and cannot change it.

A recovered operational retry/lease/serialization event cannot by itself select `COMPLETED_WITH_WARNINGS`. Search completion remains independent from adequacy endorsement.

### 12.2 Candidate work

Workers claim independent sequence-1 roots with `FOR UPDATE SKIP LOCKED`, append `CLAIMED` with a random claim token and lease, then append `DISPATCHED` with the stable operational GDSS-003 idempotency identity. That identity is derived from calibration attempt plus candidate ordinal; retry attempt identity is recorded separately. A result is attached only when operational identities and the parameter-vector/content hashes reconcile. Candidate states remain `PENDING → CLAIMED → DISPATCHED → {SUCCEEDED, INFEASIBLE, SIMULATION_FAILED, NOT_DISPATCHED_ABORTED}`. Candidate `SUCCEEDED` is not CalibrationExecutionAttempt `COMPLETED`; candidate failure classification is not calibration terminal classification.

No shared floating reduction occurs between workers. Candidate objective computation is wholly local and deterministic. A duplicate/late delivery with the same evidence hash is idempotently ignored; a conflicting delivery produces `IDENTITY_MISMATCH` and fails the calibration.

Unknown commit recovery covers “DB commit succeeded, acknowledgement lost” by using operational identity for event lookup and computational hashes for content reconciliation. It recomputes/verifies `AlignmentResult` and `alignment_hash` from design hash, ordered dataset hashes, frozen grid and specification instead of trusting mutable runtime state. The same already-committed operational event returns the existing row. The same computational content produced under a different legitimate attempt receives a distinct attempt/event identity but the same alignment and downstream hashes. The same claimed operational identity with conflicting content fails closed. Recovery cannot create a duplicate alignment, candidate, GDSS-003 link, objective row, computational terminal or publication event.

### 12.3 Finalization transaction

At `SERIALIZABLE`, lock the attempt, verify that every declared ordinal has exactly one candidate terminal, recompute the universe/hashes, choose the winner by objective then ordinal, persist residual/result artifacts, estimate set, parameter estimates, adequacy assessment and semantic diagnostics, derive the deterministic attempt classification above, and append exactly one computational terminal event plus institutional audit. Successful finalization selects `COMPLETED` or `COMPLETED_WITH_WARNINGS`, never `SUCCEEDED`. The immutable result is initially `UNPUBLISHED`, represented by absence of a publication event.

### 12.4 Review and publication transactions

Estimate review and result publication are independent later admin transactions; neither recomputes nor mutates an estimate, adequacy artifact or computational hash. Review appends `ACCEPT_FOR_SUCCESSOR_PROPOSAL|REJECT` to `gdss_calibration_estimate_review` and its AuditLog event.

Publication runs at `SERIALIZABLE`, locks the terminal attempt/result reference, verifies `PUBLISH_CALIBRATION_RESULT`, exact `calibration_result_hash`, immutable result artifact and matching institutional AuditLog correlation, then appends `GOVERNANCE_PUBLICATION_EVENT/RESULT_PUBLISHED` to `gdss_calibration_execution_event`. The event contains admin actor, timestamp, reason, exact target attempt/result/artifact identities, exact result hash and audit ID. Exact duplicate publication is idempotently returned; a conflicting duplicate fails closed. Publication cannot change the computational terminal event or hashes and conveys no scientific, predictive, successor-model, control or actuation authority.

All three review/publication combinations are legal because publication exposes governed evidence rather than endorsing the estimate: published while unreviewed, published after `REJECT`, and published after `ACCEPT_FOR_SUCCESSOR_PROPOSAL`. Conversely, a reviewed result may remain unpublished. `ACCEPT_PARAMETER_ESTIMATE ≠ PUBLISH_CALIBRATION_RESULT`.

### 12.5 Recovery profile

Proposed `GDSS_CALIBRATION_RECOVERY_V1`:

| Setting | Value | Classification |
|---|---:|---|
| claim lease | 120 s | benchmark required |
| claim timeout | 120 s | benchmark required; equals lease expiry |
| recovery scan | 30 s | freeze after benchmark |
| abandonment threshold | 900 s | benchmark required |
| dispatch attempts | 3 | freeze |
| retry backoff | 1 s, 5 s | freeze |
| terminalization attempts | 3 | freeze |
| terminalization backoff | 1 s, 5 s | freeze |
| maximum orchestration duration | 900 s | benchmark required |

An expired claim is recoverable only when no matching terminal row exists. The recovery worker locks the candidate root, appends a new claim with a new token and retains the same GDSS-003 execution identity. Source datasets and candidate vectors are never mutated during recovery.

An authorized abort sets the one-way abort request, prevents new claims, and terminalizes all undispatched candidates as `NOT_DISPATCHED_ABORTED`. Already dispatched GDSS-003 work may finish; its late immutable evidence is retained, but cannot turn the calibration into success. Final state is `ABORTED` after all in-flight dispatches reconcile or the governed abandonment rule fires.

## 13. Adequacy and institutional decisions

V1 adequacy uses exactly `FIT_COMPUTED_NO_ADEQUACY_CLAIM`, `ACCEPTABLE_UNDER_DECLARED_CRITERIA`, `POOR_FIT_UNDER_DECLARED_CRITERIA`, `INSUFFICIENT_EVIDENCE`, and `INCOMPARABLE`. The first, fourth and fifth may be generated from frozen structural rules. `ACCEPTABLE` or `POOR_FIT` is legal only when the published calibration design contains the exact threshold, metric and comparison rule before execution; those criteria participate in `calibration_design_hash`. No threshold may be inferred after seeing results. GDSS-005 does not consume `VALIDATION` or `HOLDOUT` assignments as independent validation authority. Identifiability is always the literal `NOT_ASSESSED`; equivalent minima may only generate a diagnostic.

An estimate is not institutional merely because it minimizes an objective. Admin review references the immutable estimate/adequacy hashes and records `ACCEPT_FOR_SUCCESSOR_PROPOSAL` or `REJECT`; no review row means unreviewed. Acceptance means only that the evidence may inform a future separately governed successor-model proposal. It does not create/publish a model, validate science, grant predictive/control readiness or authorize actuation. Result publication is the typed append-only `RESULT_PUBLISHED` domain event correlated to the existing institutional AuditLog; it is separate from review and no result mutates the source model or control policy.

## 14. Authorization and audit mapping

The implementation adds a GDSS-005 capability facade over existing `viewer|operator|admin`; it does not invent a second auth model.

The exact logical capabilities are `READ_OBSERVATION`, `ADMIT_OBSERVATION`, `CREATE_CALIBRATION`, `VALIDATE_CALIBRATION_DESIGN`, `RUN_CALIBRATION`, `ACCEPT_PARAMETER_ESTIMATE`, and `PUBLISH_CALIBRATION_RESULT`. `RUN_CALIBRATION ≠ ACCEPT_PARAMETER_ESTIMATE ≠ PUBLISH_CALIBRATION_RESULT`.

| Action | viewer | operator | admin | Existing permission anchor |
|---|---:|---:|---:|---|
| read datasets/designs/evidence | yes | yes | yes | `view_dashboard` |
| admit/edit draft observation | no | yes | yes | `edit_policies` |
| validate observation/design | no | yes | yes | `edit_policies` |
| publish/deprecate observation/design | no | no | yes | admin role + `edit_policies` |
| create calibration draft | no | yes | yes | `edit_policies` |
| run calibration | no | yes | yes | operator/admin role + `edit_policies` |
| abort own/any calibration | no | own | any | operator/admin role |
| accept for successor proposal/reject estimate | no | no | yes | admin role |
| publish calibration result | no | no | yes | admin role |

Audit envelopes are mandatory for admission, validation, publication, deprecation, run admission, abort request, terminalization, estimate review and result publication. Each includes actor, project, action, target/version, before/after state, semantic hashes, reason, correlation/idempotency identities and timestamp. For result publication, AuditLog is the institutional authorization record and the correlated typed `RESULT_PUBLISHED` execution-event row is the immutable domain projection and authoritative published-state proof. Worker claims and leases remain operational execution evidence rather than institutional audit noise.

## 15. Closed failure vocabulary

The v1 failure codes are:

`INVALID_DATASET`, `UNSUPPORTED_SOURCE_TYPE`, `SOURCE_HASH_MISMATCH`, `SOURCE_EPISTEMIC_ORIGIN_MISMATCH`, `MODEL_BINDING_MISMATCH`, `UNKNOWN_QUANTITY_MAPPING`, `AMBIGUOUS_QUANTITY_MAPPING`, `DIMENSION_MISMATCH`, `TEMPORAL_ORIGIN_MISSING`, `TEMPORAL_COORDINATE_OUT_OF_RANGE`, `TEMPORAL_ALIGNMENT_FAILURE`, `DUPLICATE_MEASUREMENT_COORDINATE`, `INSUFFICIENT_OBSERVATIONS`, `INVALID_UNCERTAINTY`, `INVALID_GRID`, `CANDIDATE_LIMIT_EXCEEDED`, `NONFINITE_OBJECTIVE`, `SIMULATION_FAILURE`, `DISPATCH_RETRY_EXHAUSTED`, `NO_FEASIBLE_PARAMETER_SET`, `RESOURCE_LIMIT_EXCEEDED`, `ARTIFACT_RECONCILIATION_FAILURE`, `LEAKAGE_DETECTED`, `IDENTITY_MISMATCH`, and `ABORTED_BY_AUTHORITY`.

Every diagnostic additionally carries the closed class `SEMANTIC|OPERATIONAL`. It has stage (`ADMISSION|ALIGNMENT|DISPATCH|SIMULATION|OBJECTIVE|FINALIZATION|REVIEW|PUBLICATION`), severity (`INFO|WARNING|ERROR|FATAL`) and optional candidate/point/result reference. Candidate failure classification and attempt terminal classification are separate from diagnostics and never inferred from free text.

The deterministic input/computation/evidence failures are `SEMANTIC`: `INVALID_DATASET`, `UNSUPPORTED_SOURCE_TYPE`, `SOURCE_HASH_MISMATCH`, `SOURCE_EPISTEMIC_ORIGIN_MISMATCH`, `MODEL_BINDING_MISMATCH`, `UNKNOWN_QUANTITY_MAPPING`, `AMBIGUOUS_QUANTITY_MAPPING`, `DIMENSION_MISMATCH`, `TEMPORAL_ORIGIN_MISSING`, `TEMPORAL_COORDINATE_OUT_OF_RANGE`, `TEMPORAL_ALIGNMENT_FAILURE`, `DUPLICATE_MEASUREMENT_COORDINATE`, `INSUFFICIENT_OBSERVATIONS`, `INVALID_UNCERTAINTY`, `INVALID_GRID`, `CANDIDATE_LIMIT_EXCEEDED`, `NONFINITE_OBJECTIVE`, `SIMULATION_FAILURE`, `NO_FEASIBLE_PARAMETER_SET`, `RESOURCE_LIMIT_EXCEEDED`, `ARTIFACT_RECONCILIATION_FAILURE`, `LEAKAGE_DETECTED`, and `IDENTITY_MISMATCH`. `MODEL_BINDING_MISMATCH` applies during design validation or admission when typed model/binding identity, version, project, lifecycle, hash or target context disagree. `SIMULATION_FAILURE` is semantic only for a deterministic GDSS-003 model/solver outcome with exact computational evidence; transient transport/infrastructure conditions use operational codes.

The existing `DISPATCH_RETRY_EXHAUSTED` and `ABORTED_BY_AUTHORITY` codes are `OPERATIONAL`. V1 also closes the operational evidence codes as `WORKER_RETRY`, `LEASE_EXPIRED`, `SERIALIZATION_RETRY`, `TEMPORARY_DISPATCH_FAILURE_RECOVERED`, and `RECOVERY_SCAN`. Result-qualifying semantic diagnostic codes are `EQUIVALENT_OBJECTIVE_MINIMA`, `POOR_FIT_UNDER_DECLARED_CRITERIA`, `INSUFFICIENT_MATCHED_EVIDENCE`, and `DECLARED_COMPARABILITY_LIMITATION`.

Only ordered, result-bound `SEMANTIC` diagnostics whose canonical content changes governed result meaning participate in `calibration_result_hash`. `OPERATIONAL` diagnostics never participate in computational hashes; they remain append-only execution/audit evidence. A recovered operational event never causes `COMPLETED_WITH_WARNINGS`. A semantic `WARNING` on an otherwise complete result does; any semantic or unrecovered operational `ERROR|FATAL` that prevents valid result materialization causes `FAILED` and no result hash. Candidate failure codes remain the applicable closed subset. Attempt terminal alternatives are exactly `COMPLETED`, `COMPLETED_WITH_WARNINGS`, `FAILED`, and `ABORTED`.

## 15.1 Relational/artifact reconciliation and leakage

The relational projection and artifact are two proofs of the same governed content, not competing authorities. On admission the service applies `f(calibration_design_hash, ordered dataset hashes, simulation grid manifest, AlignmentSpecification) → AlignmentResult → alignment_hash`, regenerates canonical manifest bytes and commits only exact equality with typed references. Finalization applies the same rule to result artifacts; recovery repeats both comparisons. Any mismatch is `ARTIFACT_RECONCILIATION_FAILURE`; neither “artifact wins” nor “database wins” is allowed.

Leakage is checked at three levels. SQL uniqueness prevents the same dataset version from holding conflicting roles in one design and supports indexed source/window comparison. Design validation requires disjoint source lineage for `CALIBRATION`, `VALIDATION` and `HOLDOUT`, non-overlapping measurement windows, no shared source-record hashes, and proves that only `CALIBRATION` data selected mappings, grids, objective configuration or adequacy criteria. Execution admission repeats those proofs under locks against the published hashes. `EXPLORATORY` is never executable. Failure is `LEAKAGE_DETECTED`. Reserved validation/holdout evidence is represented but not consumed by GDSS-005 V1.

## 16. Resource limits and disposition

Proposed `GDSS_CALIBRATION_LIMITS_V1`:

| Limit | Value | Disposition |
|---|---:|---|
| source references/dataset | 16 | `FREEZE` |
| series/dataset | 8 | `FREEZE` |
| points/series | 10,001 | `FREEZE` |
| total points/dataset | 80,008 | `FREEZE` |
| calibrated parameters | 4 | `FREEZE` |
| fixed parameters | 32 | `FREEZE` |
| grid values/parameter | 16 | `FREEZE` |
| total candidates | 256 | `FREEZE` |
| GDSS-003 simulations | 256 | `FREEZE` |
| concurrent candidates | 8 | `FREEZE` |
| dispatch attempts/candidate | 3 | `FREEZE` |
| matched pairs/candidate | 80,008 | `FREEZE` |
| diagnostics/attempt | 512 | `FREEZE` |
| deterministic objective operations | 100,000,000 | `ADJUST` from draft 25,000,000 |
| dataset artifact bytes | 32 MiB | `BENCHMARK_REQUIRED` |
| residual artifact bytes | 32 MiB | `BENCHMARK_REQUIRED` |
| aggregate calibration artifacts | 64 MiB | `BENCHMARK_REQUIRED` |
| orchestration duration | 900 s | `BENCHMARK_REQUIRED` |

The objective-operation adjustment is required because `256 × 80,008` matched pairs already exceeds 20.48 million, and each weighted pair requires multiple ordered binary64 operations. The counter must count every add, subtract, multiply, divide and square root defined in section 10. All limits are admission checks; none may truncate evidence silently.

## 17. Predeclared benchmark gates

Benchmarks use fixed committed fixtures, warm runtime, three measured repetitions after one warm-up, and record host/CPU, Node/PostgreSQL versions, elapsed wall time, peak RSS, DB growth, artifact bytes and all semantic hashes. Repetitions must produce identical hashes and winners.

| Gate | Fixture and workload | Required result |
|---|---|---|
| B1 — small deterministic | one-state reservoir, one calibrated parameter, 9 candidates, 1 series × 1,001 points, RMSE; publish design before any attempt; then attempts A/B with distinct UUIDs at concurrency 1 and repeat at concurrency 8 | before execution: design hash exists and alignment hash does not; after admission: A/B attempt UUIDs differ while alignment, every parameter-vector, estimate-set and result hashes, winner and objective bits are identical at concurrency 1/8; <30 s/run, peak RSS <256 MiB, artifacts <4 MiB |
| B2 — multi-series/concurrent | independent reservoir + thermal states, calibrated outflow and heat-loss, 8×8=64 candidates, 2 series × 2,001 points, weighted normalized MSE, concurrency 1 reference and concurrency 8 attempts | known ordinal pair; alignment and all downstream computational hashes independent of attempt/concurrency; <120 s, peak RSS <512 MiB, no duplicate dispatch/terminal row |
| B3 — declared ceiling | 4 parameters × 4 values = 256 candidates, 8 series × 10,001 points = 80,008 points, concurrency 8 | completes within 900 s, peak RSS <1 GiB, dataset/residual each <32 MiB, aggregate <64 MiB, operation count ≤100,000,000, exact universe reconciliation |

Any threshold failure blocks freezing every `BENCHMARK_REQUIRED` value. A failure cannot be “fixed” by weakening evidence, reducing the fixture after measurement or raising a limit without a new reviewed plan.

The reservoir fixture is exactly `dV/dt = Qin - Qout`, observes `V(t)`, calibrates `Qout`, marks origin `SYNTHETIC_OBSERVATION`, and includes the known `Qout*` in the grid. The thermal fixture is exactly `dT/dt = -k(T - Tambient)`, observes `T(t)`, calibrates `k`, uses a calibration window, and reserves a disjoint source lineage/window for boundary tests; that holdout is not consumed as validation evidence.

A separate concurrency stress gate runs the B2 workload 20 consecutive times at concurrency 8. PASS requires distinct attempt UUIDs, zero duplicate claims, duplicate GDSS-003 links, duplicate candidate terminals, duplicate attempt terminals, identity drift and persistent test residue. It also requires identical alignment, parameter-vector, estimate-set and result hashes, winner and objective bits in every run and against the concurrency-1 reference. Independent candidates remain independently locked; a global attempt mutex is forbidden.

## 18. Implementation modules and dependency direction

Planned paths under the official operational backend, `apps/topology-next/src/lib/gdss/`:

```text
observation/contracts.ts
observation/time.ts
observation/source.ts
observation/quality.ts
observation/uncertainty.ts
observation/canonical.ts
observation/dataset.ts
observation/alignment.ts
observation/limits.ts
observation/versions.ts
observation/diagnostics.ts
calibration/contracts.ts
calibration/design.ts
calibration/grid.ts
calibration/objective.ts
calibration/candidate.ts
calibration/residual.ts
calibration/result.ts
calibration/limits.ts
calibration/recovery.ts
calibration/canonical.ts
calibration/versions.ts
calibration/authorization.ts
repositories/gdss-observation.repository.ts
repositories/gdss-calibration.repository.ts
services/gdss-observation.service.ts
services/gdss-calibration.service.ts
workers/gdss-calibration.worker.ts
```

Pure contract/canonical/objective modules depend only on GDSS-002 primitives. Alignment depends on observation plus GDSS-003 manifests. Calibration orchestration depends on a GDSS-003 adapter and reuses GDSS-004 patterns without importing GDSS-004 persistence semantics. Repositories depend on the relational schema; services own authorization and transactions; workers call services and never bypass repositories. No HTTP route or UI is included in this implementation slice.

Calibration calls GDSS-003 directly; it does not create or require a GDSS-004 `ExperimentExecution` or persistence identity. GDSS-004 contributes only the materialize-before-dispatch, claim/recovery, append-only evidence, reconciliation and concurrency patterns.

## 19. Migration `0043` plan and reversible cycle

### 19.1 Upgrade order

1. Assert one Alembic head and down revision `0042`; assert the required GDSS-003 identities, uniqueness constraints and restrictive relationships exist exactly as reconciled in section 8.2; create reusable trigger functions `gdss005_reject_mutation`, `gdss005_guard_dataset_freeze`, `gdss005_guard_calibration_freeze`, `gdss005_guard_lifecycle_transition`, `gdss005_guard_execution_event`, `gdss005_guard_candidate_event`, `gdss005_guard_artifact_integrity`, `gdss005_guard_finalization`, `gdss005_guard_model_binding_coherence`, and `gdss005_guard_source_origin`.
2. Create, in order: `gdss_observation_dataset_identity`, `gdss_observation_dataset_version`, `gdss_observation_source_reference`, `gdss_observation_series`, `gdss_observation_point`, `gdss_observation_dataset_lifecycle_event`.
3. Create, in order: `gdss_calibration_identity`, `gdss_calibration_version`, `gdss_calibration_dataset_assignment`, `gdss_calibration_series_mapping`, `gdss_calibration_parameter`, `gdss_calibration_lifecycle_event`.
4. Create, in order: `gdss_calibration_artifact`, `gdss_calibration_execution_attempt`, `gdss_calibration_execution_event`, `gdss_calibration_candidate_evaluation`, `gdss_calibration_parameter_estimate_set`, `gdss_calibration_parameter_estimate`, `gdss_model_adequacy_assessment`, `gdss_calibration_estimate_review`, `gdss_calibration_diagnostic`.
5. Create typed checks with their tables, then the exact model-identity/model-version and binding-version/model-version restrictive FKs, remaining unique constraints and restrictive FKs in dependency order, then the indexes declared in section 11.
6. Attach source-origin and model-binding coherence guards; artifact-integrity/freeze triggers; dataset/calibration freeze and lifecycle triggers; execution/candidate sequence-transition triggers; append-only triggers; and finalization guard, in that order. Trigger names use `trg_gdss005_<table>_<purpose>`.
7. Verify all 21 tables, ten functions, constraints, indexes and triggers through catalog assertions, including the exact referenced GDSS-003 relation/column/constraint signatures.

### 19.2 Downgrade order

Downgrade is authorized only on a disposable test database explicitly marked for the migration-cycle test, after row counts and ownership prove that all GDSS-005 rows are fixture-owned and no unknown evidence exists. Drop triggers first; then the 21 tables in the exact reverse of steps 4, 3 and 2; then the ten trigger functions in reverse creation order. Production downgrade with evidence is a STOP condition requiring a separately approved preservation/export procedure.

### 19.3 Required migration-cycle proof

On a fresh disposable database: upgrade `0042→0043`; verify catalog; load only named GDSS-005 fixtures; run DDL constraint/trigger probes, including model/binding mismatch and physical/synthetic source-cardinality probes; remove fixture data through the explicit test cleanup; downgrade `0043→0042`; verify zero GDSS-005 relations and functions; upgrade again to `0043`; verify catalog equivalence, the GDSS-003 FK targets and one Alembic head. Capture commands, revision outputs, catalog manifests and checksums as evidence.

## 20. Forty-invariant verification matrix

Every test must record fixture identity, command/test name, database proof query and evidence artifact. `PG` means PostgreSQL-enforced; `APP` means deterministic application enforcement; `BOTH` means both.

| ID | Normative invariant | Layer | Positive test | Negative/adversarial test | PostgreSQL proof | Fixture / expected evidence |
|---|---|---|---|---|---|---|
| GDS5-INV-01 | Observed evidence is never classified as simulated. | BOTH | admit physical observation | supply trajectory as observation | kind check/FK | source-kind / rejection trace |
| GDS5-INV-02 | Telemetry is not automatically a governed observation. | BOTH | published admission succeeds | latest-value row used directly | published-version FK | raw-vs-admitted / audit |
| GDS5-INV-03 | Physical evidence requires a physical-system identity; synthetic evidence forbids one, requires governed fixture/generator provenance and cannot mix with physical sources. | BOTH | physical file/snapshot with identity and synthetic fixture with SQL `NULL` each validate in separate datasets | null physical identity, synthetic placeholder/non-null identity, incompatible source type or mixed origins fails `SOURCE_EPISTEMIC_ORIGIN_MISMATCH` | row checks + source-origin trigger/freeze | physical/synthetic cardinality matrix / dataset manifests and SQL traces |
| GDS5-INV-04 | Derived evidence preserves transitive lineage; V1 rejects transforms. | APP | untransformed source accepted | smoothed point rejected | no transform schema path | transformed-source / diagnostic |
| GDS5-INV-05 | Dataset is immutable once validated or used. | BOTH | create successor | update/delete point fails | freeze trigger | published-dataset / SQL error |
| GDS5-INV-06 | Dataset correction creates a successor version. | BOTH | successor draft linked | in-place corrected time fails | version unique/freeze | correction / version rows |
| GDS5-INV-07 | Every point resolves to exact source evidence. | BOTH | point/source hash resolves | orphan/unhashed record fails | restrictive FK/not-null | orphan-point / constraint trace |
| GDS5-INV-08 | Measurement time is distinct from ingestion/processing time. | BOTH | alignment uses measurement time | ingestion time substituted | typed fields/hash projection | time-domains / alignment hash |
| GDS5-INV-09 | Time zone, clock source and precision are explicit. | BOTH | UTC micros boundary accepted | local/sub-microsecond rejected | bigint/range/source checks | time-matrix / parse evidence |
| GDS5-INV-10 | Duplicate series timestamps fail closed. | BOTH | distinct coordinates | duplicate insert | unique(series,time) | duplicate-time / SQL error |
| GDS5-INV-11 | Missing differs from zero and absent evidence. | BOTH | explicit zero and missing coexist | missing encoded zero | quality/value check | missing-zero / row proof |
| GDS5-INV-12 | Unknown uncertainty differs from zero uncertainty. | BOTH | UNKNOWN and zero bound coexist | missing bound decoded zero | tagged-union check | uncertainty / canonical bytes |
| GDS5-INV-13 | Instrument calibration differs from model calibration. | BOTH | instrument metadata remains source evidence | certificate used as estimate | separated FKs/types | instrument / lineage proof |
| GDS5-INV-14 | Observation quality is a closed vocabulary. | BOTH | all five legal states | unknown state rejected | quality check | quality-matrix / SQL trace |
| GDS5-INV-15 | No outlier is removed implicitly. | BOTH | fixed exclusion manifest repeats | residual-based deletion fails | frozen alignment reference | outlier / census+hash |
| GDS5-INV-16 | Observation-to-model mapping resolves exactly once inside the design's frozen SystemModelVersion and DynamicModelBindingVersion. | BOTH | exact version-local target maps once | display name, zero/multiple target, successor or target outside binding context fails | mapping unique/FKs + model-binding guard | mapping-context / diagnostic and FK proof |
| GDS5-INV-17 | Mapping validates quantity, dimension, unit and `ABSOLUTE|INTERVAL` inside that exact model/binding context. | BOTH | compatible context-local conversion | affine semantic mismatch or quantity from another version/binding fails | mapping checks + model-binding guard | unit-semantics / conversion and context proof |
| GDS5-INV-18 | Declarative `AlignmentSpecification` is explicit and design-hash-bound; materialized `AlignmentResult` is execution evidence. | BOTH | publish design with specification and no attempt/alignment hash | runtime default or design dependency on result rejected | typed design fields; no pre-execution alignment FK | design-only / design hash and zero attempts |
| GDS5-INV-19 | V1 performs no interpolation, resampling or extrapolation. | APP | exact grid matches | nearest/linear fill rejected | no derived-point path | sparse-grid / census |
| GDS5-INV-20 | Every included observation exactly matches a simulation coordinate in admission-created `AlignmentResult`. | BOTH | canonical bits equal after specification application | near coordinate or arbitrary supplied hash fails | manifest/result hash reconciliation | near-grid / ordered alignment result |
| GDS5-INV-21 | Every candidate in one attempt uses the identical admission-frozen match set. | BOTH | all bind one alignment hash | candidate-specific set rejected | attempt alignment hash + candidate manifest guard | candidate-pair / proof query |
| GDS5-INV-22 | Calibration differs from sweep, comparison, validation and control. | APP | calibration aggregate used | GDSS-004 result treated as estimate | closed result kind | type-boundary / rejection |
| GDS5-INV-23 | Design binds exact immutable model identity/version/hash, binding identity/version/hash, dataset versions/hashes and declarative alignment semantics, never latest/inferred references or execution-time alignment outcomes. | BOTH | exact frozen relational refs and hashes publish without attempt | wrong-model binding, implicit successor, binding hash/version mismatch, latest lookup or alignment-hash input fails `MODEL_BINDING_MISMATCH` | composite restrictive FKs + coherence trigger/hash projection checks | design-publication / relational and hash projection transcript |
| GDS5-INV-24 | Calibration never mutates source model or binding. | BOTH | estimate stored separately | published parameter overwrite fails | read-only FK/freeze | source-model / row snapshot |
| GDS5-INV-25 | Calibrated parameter is not observed or true. | BOTH | estimate epistemic kind | `trueParameter` claim rejected | closed fields/checks | estimate / schema proof |
| GDS5-INV-26 | Optimizable is not identifiable; V1 is `NOT_ASSESSED`. | BOTH | literal stored | identifiable claim rejected | adequacy check | flat-grid / diagnostic |
| GDS5-INV-27 | Objective vocabulary and mathematics are closed/versioned. | BOTH | two V1 objectives run | arbitrary callback rejected | objective check | objective-golden / bits |
| GDS5-INV-28 | Dimensionally incompatible errors are never aggregated. | BOTH | normalized compatible series | raw kelvin+volume squared fails | mapping/objective checks | multi-series / diagnostic |
| GDS5-INV-29 | Non-finite objective arithmetic fails the candidate. | BOTH | finite candidate ranks | NaN/overflow cannot win | objective terminal check | overflow / candidate failure |
| GDS5-INV-30 | Search is deterministic, finite, exhaustive and bounded. | BOTH | full canonical grid | random/adaptive/limit+1 fails | universe count/unique | 2x3 grid / universe hash |
| GDS5-INV-31 | Worker order, timing and legitimate attempt identity do not affect alignment or downstream computational identity. | BOTH | distinct attempt UUIDs at concurrency 1/8 yield identical alignment/vector/estimate/result hashes, winner and objective bits | completion-order or attempt UUID contaminating any hash fails golden projection | ordinal/tie constraints; estimate hash non-unique | B1 A/B / attempt rows plus identical hashes |
| GDS5-INV-32 | Successful candidate binds exact GDSS-003 evidence. | BOTH | identities/hashes reconcile | trajectory substitution fails | unique attachment/hash trigger | GDSS result / reconciliation |
| GDS5-INV-33 | Retry/unknown commit creates no duplicate event/result and does not alter computational identity. | BOTH | lost-ACK same event returns committed row; separate attempt reproduces same hashes | conflicting same identity or second terminal/publication fails | operational unique + transition/publication triggers | retry / event census and cross-attempt hashes |
| GDS5-INV-34 | Calibration data is not independent validation data. | BOTH | disjoint reserved role | same points in both roles fails | role/source indexes + admission | leakage / diagnostic |
| GDS5-INV-35 | Uncertain lineage fails an independence claim closed. | BOTH | transitive lineage proven | shared/unknown lineage fails | stored lineage/hash query | derived-holdout / proof |
| GDS5-INV-36 | Residual evidence preserves exact observation and simulation operands. | BOTH | every pair traceable | untraceable aggregate fails | finalization census/FKs | residual / artifact hash |
| GDS5-INV-37 | Low calibration error is not predictive/scientific validation. | BOTH | scoped fit claim accepted | `MODEL_TRUE`/predictive claim fails | adequacy vocabulary check | low-error / claim scan |
| GDS5-INV-38 | Compute estimate differs from human acceptance, result publication and successor proposal. | BOTH | independent review/publication combinations persist | publication mutating hash or automatic model creation fails | review table + typed publication event/no mutation path | review-publication matrix / audit correlations |
| GDS5-INV-39 | AI proposal is not accepted or executable authority. | APP | proposal must re-enter normal draft flow | AI response dispatched directly | no AI authority columns | AI-boundary / dependency scan |
| GDS5-INV-40 | Physical authority is `NONE`; neither completion, review nor publication creates an M7 path. | APP | completed/published result remains NONE | policy/actuation link fails | no authority FK/route | published-result boundary scan / answer `NOTHING` |

Additional plan acceptance invariant (does not renumber the canonical 40):

| ID | Requirement | Positive proof | Negative proof |
|---|---|---|---|
| `P015-R1-ACCEPTANCE-01` | Two independent legitimate attempts with identical governed inputs and identical computational evidence produce identical dataset, alignment, design, parameter-vector, estimate-set and result hashes despite different attempt UUID, worker, completion order, retries and wall-clock timing. | B1 A/B plus concurrency 1/8 compares every hash, winner and objective bits while proving distinct attempt UUIDs. | Change one semantic input (one canonical grid value), prove the affected vector/design identity and every dependent downstream computational hash changes while unrelated upstream hashes remain identical. |
| `P015-R2-ACCEPTANCE-01` | A CalibrationDesign is validated/published using only declarative `AlignmentSpecification`; `AlignmentResult` and `alignment_hash` arise only during governed admission; design hash excludes alignment hash, while alignment hash binds design hash; no hash or temporal materialization cycle exists. | Publish with design hash and zero attempts/alignment hashes, then run A/B and prove identical alignment/downstream hashes under distinct attempt UUIDs. | N1 change specification and require design/downstream hashes to change; N2 change only operational identity and require all computational hashes unchanged; N3 publication without execution passes; N4 arbitrary supplied alignment hash fails closed. |
| `P015-R3-ACCEPTANCE-01` | CalibrationDesign binds one exact immutable SystemModelVersion and one exact DynamicModelBindingVersion through real GDSS-003 identities, versions, hashes and relationships; binding-version semantics participate in design identity. | Publish with exact composite FKs and matching typed projection; change only to a successor binding version/hash changes design, alignment, estimate-set and result hashes while assigned observation dataset hashes remain unchanged. | Binding for another model, implicit successor/latest resolution, wrong binding identity/version/hash or mapping outside the exact context fails `MODEL_BINDING_MISMATCH`; operational-only identity changes leave all computational hashes unchanged. |
| `P015-R3-ACCEPTANCE-02` | Source provenance has exclusive cardinality: physical datasets require physical source types and non-null physical-system identity; synthetic datasets require governed fixture/generator provenance and SQL-null physical-system identity. | Separate physical and synthetic fixtures pass their exact contracts and preserve distinct manifests. | Physical null identity, synthetic non-null/placeholder physical identity, incompatible source type or mixed-origin source set fails `SOURCE_EPISTEMIC_ORIGIN_MISMATCH`. |

R2 identity test cases are frozen as follows:

- **N1 — semantic specification change:** create a successor `DRAFT`, change `measurement_time_origin_us` (and separately mapping target identity), validate it, and prove `calibration_design_hash`, valid `alignment_hash`, estimate-set hash and result hash change while the original published version remains immutable.
- **N2 — operational-only change:** vary attempt UUID, worker, concurrency, retry/lease history and wall clock; prove dataset, design, alignment, vector, estimate-set and result hashes remain identical.
- **N3 — publication without execution:** validate/publish a design, prove `calibration_design_hash` exists while attempt count is zero and `alignment_hash` does not exist; expected `PASS`.
- **N4 — arbitrary alignment identity:** submit a caller-provided alignment hash or mismatched manifest; admission recomputes from governed inputs and fails closed on mismatch.
- **Dataset outcome sensitivity:** use the same specification/design semantics with a different immutable assigned observation dataset version. Its dataset hash and resulting alignment/downstream identities change; this is a changed governed input, not an in-place design mutation.

### 20.1 Security and persistence-negative suites

The security suite proves that calibration cannot query MQTT, latest telemetry or device state; call Control Engine or DTE; authorize a physical action; create a control policy; create/publish a successor model automatically; load an arbitrary executable objective/transformation/search method; execute user code, shell, dynamic import or `eval`. The database suite directly attempts published dataset/design/point mutation; a binding for another model; implicit binding successor resolution; wrong model/binding identity, version or hash; a mapping target outside the exact model/binding context; synthetic evidence with a physical-system identity; physical evidence with null identity; mixed-origin sources; cross-version mapping; duplicate ordinal/vector/GDSS-003 attachment; a second terminal event; illegal lifecycle transition; result/estimate/review mutation; artifact/hash mismatch; and claim-after-abort. Architectural authority is accepted only when real PostgreSQL rejects the SQL-level cases.

V1 adds no AI fields. If a future input is marked `AI_PROPOSED` for mappings, bounds, grid or objective configuration, it has no execution authority and must traverse the same draft validation, publication and run authorization as a human proposal.

### 20.2 Reuse and compatibility proof

- GDSS-001 supplies model/version/parameter identities and lifecycle patterns; semantic change required: **NO**.
- GDSS-002 supplies units, dimensions, `ABSOLUTE|INTERVAL`, canonical binary64 and conversion V2; semantic change required: **NO**.
- GDSS-003 supplies exact simulation, solver/time and trajectory evidence; semantic change required: **NO**.
- GDSS-004 supplies orchestration patterns only; no experiment identity or semantic dependency is introduced; semantic change required: **NO**.
- P014 architecture remains accepted and unchanged; semantic change required: **NO**.

Implementation discovery requiring any semantic change is `REQUIRES_GDSS_005_ARCHITECTURE_REVIEW`. The implementation closure must rerun the complete GDSS-001 through GDSS-004 regression suites.

### 20.3 Server/API and authority boundary

V1 is server-side only: HTTP API **NO**, UI **NO**, live-ingestion endpoint **NO**. Boundaries are frozen as follows:

```text
Control Engine dependency: NONE
DTE dependency:            NONE
MQTT dependency:           NONE
Live telemetry dependency: NONE
Physical actuation:        NONE
Prediction authority:      NONE
Recommendation authority:  NONE
Scientific authority:      NONE
```

What physical action can a successful GDSS-005 calibration authorize? **NOTHING.** Successful execution is not acceptable fit; acceptable fit is not validation; validation is not prediction; prediction is not control authority.

### 20.4 Persistence residual gate

Before implementation closure, every new GDSS-005 table must contain zero residual test rows and all named fixture projects/audit rows must be removed through fixture-owned cleanup. Unknown or non-test evidence must not be deleted; its presence is a STOP condition.

## 21. Delivery sequence and gates

1. **Contract gate:** implement pure time, quality, uncertainty, canonical encoding, grid and objective modules with golden vectors; pass invariants 02–18 and 23–25, 31–33.
2. **DDL gate:** implement migration `0043`, repository types and catalog tests; pass the complete reversible cycle and DB portions of all 40 invariants.
3. **Observation gate:** implement admission, lifecycle, artifact and exact alignment services; pass invariants 01–22 and resource boundary fixtures.
4. **Calibration gate:** implement universe admission, candidate worker, GDSS-003 idempotent dispatch and finalization; pass invariants 23–38, including crash/recovery races.
5. **Governance gate:** implement authorization facade and audit envelopes; pass invariants 39–40 and negative role matrix.
6. **Benchmark gate:** execute B1–B3; freeze or formally revise all benchmark-required thresholds.
7. **Closure gate:** full tests, typecheck/lint, migration-cycle evidence, exact diff classification and controlled local Git closure under a separately authorized prompt.

Each gate is independently reviewable. A later gate cannot waive an earlier failure.

## 22. Required verification commands after implementation authorization

The implementing prompt must discover and use repository-native commands, then at minimum collect: Alembic heads/current/history; migration upgrade/downgrade/upgrade evidence on a disposable DB; focused unit and integration tests; PostgreSQL invariant probes; TypeScript typecheck and lint for affected workspace; deterministic reruns at concurrency 1 and 8; benchmark B1–B3; `git diff --check`; exact file classification; and final status with no unrelated staged changes.

This plan deliberately does not execute those commands because no code or migration is authorized in P015.

## 23. STOP conditions

Implementation must stop and request architectural review if any of the following occurs:

- P014 semantics must be changed rather than merely implemented;
- the committed GDSS-003 schema lacks the immutable model/binding identity, version, hash, project, lifecycle or relational proof required by section 8.2;
- a CalibrationDesign legitimately requires multiple DynamicModelBindingVersions rather than exactly one;
- exact binding-version-to-model-version coherence cannot be proved without changing an upstream GDSS-001/003 semantic contract;
- legitimate synthetic evidence requires a non-null physical-system identity or legitimately mixes physical and synthetic sources;
- closing P015-F06 or P015-F07 would require reopening P015-F01..F05, P014, or GDSS-001..004;
- a design hash would require an execution-time alignment result or alignment hash;
- `AlignmentSpecification` or `AlignmentResult` would require a 22nd table or new artifact kind;
- relational binding or source-provenance enforcement would require a 22nd table or fifth artifact kind;
- a fourth source type, interpolation, stochastic optimizer or automatic model mutation is required;
- exact time conversion cannot be proven cross-runtime by canonical bits;
- an accepted point cannot be traced to immutable source evidence;
- an external artifact backend is required for atomicity;
- PostgreSQL cannot enforce append-only/freeze/terminal uniqueness as specified;
- GDSS-003 lacks stable idempotent execution identity or immutable trajectory evidence;
- candidate evidence would need deletion or silent overwriting for recovery;
- the 21-table design needs semantic table removal/addition rather than a naming-only adjustment;
- the migration finds pre-existing `gdss_observation_*`, `gdss_calibration_*` or `gdss_parameter_estimate*` relations/data;
- a downgrade would destroy non-fixture evidence;
- any invariant lacks a positive case, negative case, DB proof and captured evidence;
- benchmark B3 exceeds a hard upstream GDSS-003/004 limit or requires weakening evidence;
- authorization cannot map to the existing role/permission model without privilege broadening;
- unrelated working-tree changes overlap an implementation target.

## 24. Plan acceptance criteria

This plan is ready for implementation authorization only when reviewers accept:

- the exact int64/bigint temporal contract and origin conversion;
- the closed source, quality and uncertainty contracts;
- the exact real-schema SystemModelVersion/DynamicModelBindingVersion relational projection and one-binding-per-design rule;
- the exclusive physical/synthetic source cardinality and layered `PG|APP|BOTH` enforcement;
- all 21 tables, constraints, triggers and transaction boundaries;
- deterministic grid/objective/hash/artifact formats;
- the separation `AlignmentSpecification ≠ AlignmentResult`, with design hash upstream of alignment hash;
- publication of a valid design before any execution or alignment result exists;
- the absence of hash and temporal-materialization cycles;
- the computational/operational/governance identity taxonomy and acyclic hash DAG;
- absence of attempt, retry, worker, audit and publication identity from computational hashes;
- the conflict-free attempt/candidate state vocabularies and deterministic terminal rules;
- typed append-only result publication within the existing 21-table architecture;
- separation of estimate review, result publication and computational finalization;
- semantic/operational diagnostic classification and cross-attempt reproducibility proof;
- recovery, abort, idempotency and compensation semantics;
- the role/audit mapping and failure vocabulary;
- each resource disposition and the three predeclared benchmark gates;
- all 40 invariant test rows and migration-cycle proof;
- both `P015-R3` acceptance rows, with P015-F06 and P015-F07 closed without reopening earlier findings;
- every STOP condition.

Until that authorization, the authoritative outcome is documentation only: **no GDSS-005 production implementation exists or is implied by this plan**.
