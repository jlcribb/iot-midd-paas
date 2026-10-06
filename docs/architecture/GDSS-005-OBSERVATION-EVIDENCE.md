# GDSS-005 — Observation Evidence

Status: `PROPOSED`

## Admission boundary

GDSS-005 does not subscribe to devices, MQTT, a latest-value table or a live telemetry runtime. An
authorized actor admits a finite dataset from an immutable source snapshot. Admission verifies the
source hash, parses through an allowlisted importer, validates every series and point, constructs a
canonical dataset artifact/projection, and records a new dataset version.

```text
RAW_MEASUREMENT
  -> source snapshot + cryptographic identity
  -> quality assessment outside or during governed admission
  -> GOVERNED_OBSERVATION
```

V1 does not create transformed/derived observations. A future transformation package may produce a
successor dataset version only when it binds source point identities, transformation version,
parameters and output hash. Unit conversion used during alignment is a comparison operation and
does not rewrite the admitted observation.

## Minimum first-class concepts

| Concept | V1 form | Reason |
|---|---|---|
| ObservationSource | immutable reference value | avoids second raw-data authority |
| ObservationDataset | identity plus immutable versions | correction/version lineage |
| ObservationSeries | relational child | channel/quantity/unit/time contract |
| ObservationPoint | relational child | exact time/value/quality evidence |
| MeasurementChannel | section of series | no independent lifecycle needed |
| MeasurementContext | bounded dataset metadata | system/location/operating context |
| ObservationQuality | point value object | preserves admission status |
| ObservationProvenance | source, series and point fields | exact attribution |
| ObservationTransformation | future versioned package | V1 forbids silent transforms |

## Provenance requirements

Every admitted point is reachable from:

```text
project
dataset identity/version/hash
source provider/key/artifact hash
physical source identity
instrument identity and calibration-evidence hash, when applicable
measurement channel
quantity identity, dimension, unit revision and quantity semantics
clock source and uncertainty
measurement time
sampling semantics
quality status and reason
uncertainty declaration
source record hash and ordinal
```

Dataset audit additionally records ingestion and processing timestamps and the admitting actor.
Those timestamps answer operational questions but do not replace measurement time and do not alter
the computational dataset hash.

Instrument calibration is provenance about how a measurement was produced. Model calibration is a
computation that estimates model parameters. An instrument certificate never becomes a model
parameter estimate, and a model fit never certifies an instrument.

## Temporal semantics

| Time | Owner | Computational role |
|---|---|---|
| measurement time | observation point | included in dataset and alignment identity |
| ingestion time | admission audit | excluded from computational identity |
| processing time | admission/calibration operation | excluded from computational identity |
| simulation time | GDSS-003 trajectory | included through exact simulation identity |
| wall-clock execution time | worker/attempt | operational only |

Measurement coordinates are canonical signed epoch microseconds in UTC. Original textual timestamp,
zone/offset, clock source and clock uncertainty remain provenance. A missing or ambiguous zone, an
unknown clock source where one is required, and timestamp precision beyond the declared source
precision fail admission rather than being guessed.

### Sampling cases

- Fixed interval: declare exact positive interval and TIME unit; observed coordinates must conform.
- Irregular: every coordinate is explicit and sorted canonically; no interval is inferred.
- Event-driven: coordinates are explicit and no periodic completeness is claimed.
- Duplicate coordinate in one series: invalid dataset.
- Out-of-order source records: retained by source ordinal but canonicalized by measurement time.
- Missing sample: explicit `MISSING` point with no value, distinct from no source record.

## Quality

The core vocabulary is intentionally small:

| Status | Numeric value | Calibration V1 |
|---|---|---|
| `ACCEPTED` | required | eligible |
| `SUSPECT` | optional | excluded |
| `REJECTED` | optional | excluded |
| `MISSING` | forbidden | excluded |
| `DEVICE_ERROR` | forbidden | excluded |

Instrument/domain conditions such as below detection limit, saturation and manual invalidation are
preserved as versioned reason codes rather than expanding core control flow. Manual invalidation
requires actor, reason and successor dataset version; historical admitted evidence is not updated.

There is no automatic outlier deletion. V1 has no statistical outlier method. If a point is
excluded, its pre-existing quality status, exact reason and point identity appear in the immutable
alignment manifest. A calibration result cannot retroactively change the inclusion set.

## Measurement uncertainty

V1 represents bounded metadata only:

- absolute bound in the observation quantity unit;
- relative dimensionless bound;
- instrument resolution as separate metadata;
- explicit unknown.

The value is not automatically interpreted as a standard deviation, confidence interval,
probability distribution or objective weight. Zero uncertainty is an explicit finite declaration
with source evidence; missing metadata becomes `UNKNOWN`, never zero. Probabilistic propagation and
Bayesian inference are future work.

## Raw evidence authority

GDSS stores source references and hashes. The raw payload remains in its governed source system.
Import is read-only and occurs only during explicit admission. Reproduction verifies the same
source bytes by hash; it does not query a live channel. If retention policy requires a copy, it must
be an immutable evidence-store object referenced by the same contract, not an unconstrained blob in
GDSS tables.

## Alignment semantics

An alignment is a governed join, not a nearest-neighbor lookup:

1. resolve the exact published dataset version and series;
2. resolve exact model variable identity and GDSS-003 trajectory evidence;
3. verify quantity, dimension and affine quantity semantics;
4. convert units through the exact governed unit catalog;
5. apply the declared observation window;
6. retain only predeclared `ACCEPTED` points;
7. map the declared observation origin to simulation start;
8. require exact equality with a trajectory coordinate;
9. produce an ordered match/exclusion manifest and its hash.

V1 methods:

```text
temporal method: EXACT_COORDINATE_MATCH_V1
interpolation:    NONE
resampling:       NONE
extrapolation:    NONE
smoothing:        NONE
```

An observation coordinate may align to a subset of trajectory coordinates; the trajectory need not
be resampled. Every calibration candidate uses the identical match manifest. A candidate whose
trajectory cannot satisfy it is infeasible or fails according to the design's declared policy.

## Residual evidence

For the selected estimate, the residual artifact contains one record per match:

```text
seriesId
observationPointId
measurementEpochMicros
simulationStepIndex
observation canonical value/unit
simulation canonical value/unit
residual canonical value/unit
observation dataset/alignment hash
simulation input/result/trajectory hash
```

This preserves provenance to both operands without copying source observations or trajectory bytes.
Relational adequacy rows retain aggregate counts and hashes; unsuccessful/unselected candidates
retain objective summaries and GDSS-003 references rather than full residual series.

## Future telemetry producer

A future ingestion layer may create an immutable snapshot, quality assessment and source hash, then
request dataset admission through the same contract. GDSS-005 still receives a finite explicit
dataset and never imports MQTT, subscribes to live state or interprets the latest measurement.
