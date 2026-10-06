# GDSS-005 — Proposed Invariant Catalog

Status: `PROPOSED`
Target: `40 invariants`

| ID | Invariant | Enforcement proposal | Negative evidence |
|---|---|---|---|
| GDS5-INV-01 | Observed evidence is never classified as simulated evidence. | closed epistemic kind on dataset and trajectory readers | observation supplied as trajectory |
| GDS5-INV-02 | A measured signal or telemetry row is not automatically a governed observation. | explicit admission transaction and published dataset FK | latest-value row used directly |
| GDS5-INV-03 | Synthetic observation is distinct from physical observation. | immutable `evidence_kind` in dataset identity/hash | synthetic fixture labeled physical |
| GDS5-INV-04 | Derived observation preserves transitive source lineage. | V1 rejects transforms; future successor contract required | smoothed point without source refs |
| GDS5-INV-05 | Dataset version is immutable once validated or used. | lifecycle freeze, append-only guards, restrictive FKs | update/delete published point |
| GDS5-INV-06 | Dataset correction creates a successor version. | predecessor FK and no mutation API | in-place corrected timestamp |
| GDS5-INV-07 | Every point resolves to exact source evidence. | source reference and source-record hash required | orphan or unhashed source record |
| GDS5-INV-08 | Measurement time is distinct from ingestion and processing time. | separate fields; only measurement coordinate in content identity | ingestion time used for alignment |
| GDS5-INV-09 | Time zone, clock source and precision are explicit. | admission validation and canonical epoch micros | local time without offset/source |
| GDS5-INV-10 | Duplicate series timestamps fail closed. | unique series/measurement coordinate constraint | last-write-wins duplicate |
| GDS5-INV-11 | Missing is distinct from zero and from absent evidence. | quality/value conditional checks | missing point materialized as zero |
| GDS5-INV-12 | Unknown uncertainty is distinct from zero uncertainty. | tagged uncertainty union | absent bound decoded as zero |
| GDS5-INV-13 | Instrument calibration is distinct from model calibration. | separate source metadata and calibration aggregates | certificate used as estimate result |
| GDS5-INV-14 | Observation quality uses a closed core vocabulary. | database check and parser allowlist | unknown status silently accepted |
| GDS5-INV-15 | No outlier is removed implicitly. | fixed pre-run match/exclusion manifest | residual-based point deletion |
| GDS5-INV-16 | Observation-to-model mapping is explicit and unambiguous. | exact series and variable FKs/identities | name similarity auto-mapping |
| GDS5-INV-17 | Mapping validates quantity, dimension, unit and quantity semantics. | GDSS-002 catalog/version checks | dimension-only affine mismatch |
| GDS5-INV-18 | Alignment policy is explicit and hash-bound. | alignment manifest and hash in design | runtime default alignment |
| GDS5-INV-19 | V1 performs no interpolation, resampling or extrapolation. | only `EXACT_COORDINATE_MATCH_V1` accepted | nearest/linear fill |
| GDS5-INV-20 | Every included observation exactly matches a simulation coordinate. | precomputed point-to-step manifest | unmatched point rounded to step |
| GDS5-INV-21 | Every candidate uses the identical matched-point set. | alignment hash bound before candidate materialization | candidate-specific missing set |
| GDS5-INV-22 | Calibration is distinct from sweep, comparison, validation and control. | separate aggregate/runtime and closed result kind | GDSS-004 result treated as estimate |
| GDS5-INV-23 | Calibration design binds exact model, binding and dataset versions/hashes. | composite FKs plus manifest reconciliation | latest version lookup |
| GDS5-INV-24 | Calibration never mutates source model or binding. | read-only FKs, no update path, append-only evidence | overwrite published parameter |
| GDS5-INV-25 | Calibrated parameter is not an observed or true parameter. | estimate epistemic kind and forbidden claim fields | `trueParameter=true` result |
| GDS5-INV-26 | Optimizable is not identifiable; V1 identifiability is not assessed. | constant `NOT_ASSESSED`; diagnostic-only flatness | grid minimum labeled identifiable |
| GDS5-INV-27 | Objective vocabulary and mathematics are versioned and closed. | two allowlisted objective versions | arbitrary callback/expression |
| GDS5-INV-28 | Dimensionally incompatible errors are never aggregated. | per-series unit checks and explicit normalization | kelvin squared added to volume squared |
| GDS5-INV-29 | Non-finite objective arithmetic fails the candidate. | finite checks after every operation | NaN ranked as best |
| GDS5-INV-30 | Search is deterministic, finite, exhaustive and resource-bounded. | canonical grid materialization and limits | random/adaptive candidate generation |
| GDS5-INV-31 | Worker order and operational timing do not affect candidate or result identity. | ordinal/vector ordering and canonical tie-break | first worker completion wins tie |
| GDS5-INV-32 | Every successful candidate binds exact GDSS-003 evidence. | attempt/input/result/trajectory hash reconciliation | substituted trajectory |
| GDS5-INV-33 | Retry or unknown commit cannot duplicate candidate, simulation link or terminal result. | idempotency, unique constraints and exact replay | second terminal after lost ACK |
| GDS5-INV-34 | Calibration data is not independent validation data for the same claim. | role assignment and lineage/window disjointness checks | same point IDs in both roles |
| GDS5-INV-35 | Leakage uncertainty fails an independence claim closed. | transitive lineage proof required | derived holdout with shared sources |
| GDS5-INV-36 | Residual evidence preserves exact observation and simulation operands. | selected residual artifact references both hashes/IDs | untraceable aggregate residual |
| GDS5-INV-37 | Low calibration error is not predictive or scientific validation. | scoped adequacy vocabulary; forbidden authority fields | `MODEL_TRUE` or predictive claim |
| GDS5-INV-38 | Compute estimate is distinct from human acceptance and successor proposal. | separate capability and append-only review | automatic model version creation |
| GDS5-INV-39 | AI proposal is not accepted or executable calibration authority. | proposal provenance plus human design lifecycle gate | AI response dispatched directly |
| GDS5-INV-40 | Every GDSS-005 result has physical authority `NONE` and no M7 path. | constant contract, import/route/dependency scans | policy activation or actuation link |

## Cross-cutting closure expectations

The implementation-plan test matrix should combine pure contract/canonicalization tests, adversarial
unit/dimension/time/quality cases, real PostgreSQL append-only/ownership/concurrency tests, exact
GDSS-003 dispatch evidence, golden reference cases, resource boundaries and forbidden-dependency
scans. Every invariant requires at least one positive and one negative test; persistence and retry
invariants require real PostgreSQL.

## Architecture boundaries

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
