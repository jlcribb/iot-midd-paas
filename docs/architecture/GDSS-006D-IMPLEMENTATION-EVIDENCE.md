# GDSS-006D — Implementation Evidence

Prompt: `MIDD-GDSS-P021-R1`
Status: `COMPLETED_GDSS_006D_METRICS_BASELINES_AND_UNCERTAINTY_FOUNDATION`

## A. Baseline

- Checkout: `/Users/joseluis/dev/iot-midd-paas-auth-work`.
- Branch: `main`; baseline HEAD: `dee81328f4a73b525f8d7236d8ee799044b9cabc`.
- Initial source and principal database revision: single Alembic head/current `0046`.
- Existing uncommitted GDSS-006A/B/C material was preserved; no unrelated material was incorporated.

## B. Scope Implemented

Implemented only versioned metric definitions/results, exact-version baselines and predictions,
same-pair-set comparisons, typed uncertainty sources/assessments, prediction intervals, empirical
coverage and uncertainty completeness. No evidence set, capability assessment, predictive claim,
revalidation workflow, aggregate score, ML/RL or physical control authority was introduced.

## C. Files Changed

- Domain: `metric-contracts.ts`, `metric-canonical.ts`, `metric-diagnostics.ts`,
  `metric-engine.ts` and validation barrel exports.
- Persistence/service: `gdss-metrics-uncertainty.repository.ts`,
  `gdss-metrics-uncertainty.service.ts`, strict request schemas and DB error mappings.
- HTTP: twelve project-scoped route families for definitions, results, baselines, comparisons,
  assessments, intervals, coverage and completeness.
- Database: `0047_gdss006d_metrics_baselines_uncertainty.py`.
- Verification: `gdss-metrics-uncertainty.test.ts` and the extended PostgreSQL custody/run suite.
- Documentation: this evidence record and the GDSS-006 implementation-plan status.

## D. Migration 0047

Migration `0047` adds fourteen normalized, project-scoped tables: metric identity/version/result;
baseline identity/version/prediction/metric-result/comparison; uncertainty source/method/assessment;
prediction interval; interval assessment; and uncertainty completeness assessment. Composite foreign
keys, allowlist checks, semantic/content uniqueness, temporal guards and immutable-history triggers
enforce the boundary. Isolated cycle `0046 -> 0047 -> 0046 -> 0047`: PASS.

## E. Metric Definitions

Definitions use immutable identity/version rows with canonical content, implementation identifier,
formula version, directionality, required inputs, unit/aggregation/missingness semantics and validity
constraints. The exact V1 allowlist is `MAE_V1`, `RMSE_V1`, `BIAS_V1`, `SMAPE_V1`,
`TRAJECTORY_RMSE_V1`, `PEAK_MAGNITUDE_ERROR_V1`, `PEAK_TIMING_ERROR_V1`,
`STEADY_STATE_DEVIATION_V1`, `INTERVAL_COVERAGE_V1` and `MEAN_INTERVAL_WIDTH_V1`.

## F. Metric Formulas

- MAE: mean absolute prediction error; RMSE/trajectory RMSE: square root of mean squared error.
- Bias: signed mean of `prediction - observation`.
- SMAPE: mean `2*abs(p-o)/max(abs(p)+abs(o), declared floor)`; both-zero contributes zero.
- Peak magnitude error: absolute difference between maxima.
- Peak timing error: declared signed or absolute peak-time delta in seconds.
- Steady-state deviation: signed mean tail deviation over a predeclared count, only when the observed
  tail satisfies the declared steady-state tolerance.
- Interval coverage: inclusive observed-in-bounds fraction; mean interval width: mean `upper-lower`.

## G. Metric Results

A result binds the exact metric version, immutable pair set, model version/hash, protocol version,
target, horizon, unit, exclusion-policy hash, raw binary64 result, canonical content and SHA-256.
Only complete pair sets whose integrity assessments are all `PASS` are eligible. Results are retained
even when unfavorable; lifecycle semantics are only `COMPUTED` or explicit invalidation evidence.

## H. Pair-Set Governance

PostgreSQL verifies one project, target, horizon, model version/hash, protocol and compatible unit for
the full immutable pair set. Hidden exclusion or partial membership is rejected. Baseline and model
results cannot be compared unless metric version and pair-set identity are exactly equal.

## I. Baseline Model

The exact allowlist is `NAIVE_LAST_VALUE_V1`, `HISTORICAL_MEAN_V1`, `SEASONAL_NAIVE_V1` and
`AUTHORIZED_REFERENCE_MODEL_V1`. Identity and immutable version are separate; every version binds
target, horizon, algorithm/input policy and, where applicable, a declared window, seasonal lookup and
fallback, or exact authorized reference model version/hash.

## J. Baseline Generation

Generation is deterministic for the declared baseline version and pair set. Inputs must have both
measurement and availability times no later than each forecast origin. Last-value ordering is explicit;
historical mean uses the declared window; seasonal naive uses the declared offset/lookup/fallback; the
reference-model baseline requires an exact project/version/hash and a pre-origin commitment.

## K. Baseline Comparison

Model and baseline metrics are computed with the same metric definition and pair set. A versioned rule
with explicit directionality and tolerance yields only `MODEL_OUTPERFORMS_BASELINE`,
`MODEL_EQUIVALENT_TO_BASELINE`, `MODEL_UNDERPERFORMS_BASELINE` or `INCONCLUSIVE`. No global verdict
or aggregate score is derived.

## L. Uncertainty Sources

All eight sources are representable exactly: measurement, parameter, initial-condition, input,
model-structural, numerical, predictive and domain uncertainty. Source identity is project/scope/type
bound and content addressed.

## M. Uncertainty Assessments

Knowledge states are `KNOWN_QUANTIFIED`, `KNOWN_UNQUANTIFIED`, `UNKNOWN` and `NOT_APPLICABLE`.
Allowed methods are only `DECLARED_BOUNDS`, `SUPPLIED_INTERVAL` and `EMPIRICAL_COVERAGE`.
Assessments preserve assumptions, dependencies, scope, unit, coverage target and provenance. `UNKNOWN`
cannot carry fabricated zero or bounds.

## N. Prediction Intervals

Intervals bind an exact prediction, finite ordered bounds, coverage level strictly between zero and one,
matching unit and explicit method/version. DB time prevents creation after observation availability; an
unknown availability on an already paired observation also fails closed.

## O. Coverage

Coverage is assessed only when every pair in the set has one interval at the same declared coverage
level. The immutable assessment records inclusive empirical coverage, mean width, eligible/total count,
pair set and hash. Completeness is separately classified as complete, partial, insufficient or unknown.

## P. Hashing & Determinism

Domain-separated SHA-256 covers metric definition/result, baseline/version/prediction/result/comparison,
uncertainty source/assessment, interval and completeness content. Canonical key ordering and sorted
identity collections make insertion order irrelevant while semantic changes alter hashes.

## Q. Numerical Policy

The policy is IEEE-754 binary64, finite values only, NaN/infinities rejected, negative zero normalized
to positive zero and rounding restricted to presentation. Scientific values are persisted without
pre-storage rounding. Reference-vector assertions use explicit tolerances.

## R. Authorization

All mutations require authenticated, project-scoped `RUN_VALIDATION`; viewers and development fallback
are rejected by the existing authorization layer. Authorization grants scientific computation only.
Physical authority remains `NONE`.

## S. Audit

Scientific writes and audit records share one transaction. Actions cover metric-definition creation,
metric computation, baseline version/prediction/result/comparison, uncertainty assessment, prediction
interval creation, interval coverage and uncertainty completeness.

## T. API/Services

The official Next.js backend exposes strict project-scoped commands for all implemented entities.
Services parse canonical contracts, enforce permission before persistence, compute results internally
from governed records and never accept caller-supplied scientific results as authoritative.

## U. Domain Errors

Typed errors include metric allowlist/input/pair-set/unit/immutability failures, baseline allowlist,
pair-set, future-leakage and model-version failures, uncertainty source/method/state failures, and
prediction-interval/late-interval failures. PostgreSQL trigger messages map back to HTTP domain errors.

## V. Invariants

The implementation exercises the GDSS-006 metric/baseline/uncertainty portion of the existing 40
invariants: exact versions and sets, deterministic formulas, immutable evidence, prospective baseline
inputs, explicit unknowns, interval timing, error/uncertainty separation and zero physical authority.
No invariant was renumbered or reinterpreted.

## W. Tests

- GDSS-006D domain: 12/12 PASS.
- Real PostgreSQL GDSS-006A/B/C/D focused regression: 24/24 PASS.
- Durable PostgreSQL custody/run/006D concurrency suite: 11/11 PASS.
- Migration cycle and static boundary scans: PASS.

## X. Numerical Reference Tests

Manual vectors cover MAE, RMSE, signed bias, SMAPE including both-zero/near-zero, trajectory RMSE,
peak magnitude/timing, steady-state tail, interval coverage and mean width. Non-finite inputs, invalid
bounds and unstable steady state fail closed. Error and uncertainty are tested as independent axes.

## Y. Adversarial Tests

PASS: model/baseline pair-set mismatch, future baseline leakage, metric-result and metric-definition
mutation, hidden invalid-pair inclusion, invalid SMAPE input, incompatible units, interval creation after
observation, zero fabrication for unknown uncertainty, wrong reference model, baseline-version
substitution, unfavorable-result retention and forbidden-boundary scans.

## Z. Concurrency

Durable real-PostgreSQL races cover the same metric result, baseline prediction, comparison and
uncertainty assessment. Each produced one effective materialization or the declared deterministic
conflict, with no duplicate scientific state.

## AA. Performance

Diagnostic 10,000-pair focal sample: MAE+RMSE 1.294 ms, trajectory RMSE 0.374 ms, baseline generation
0.179 ms and interval coverage 1.360 ms. A full-suite sample under concurrent test load measured
10.720 ms, 0.273 ms and 1.912 ms for MAE+RMSE, baseline generation and coverage respectively. These
measurements are observations, not SLAs.

## AB. Regression

- topology-next: 510 passed / 74 skipped; exit 0.
- Python runtime: 179 passed / 6 skipped; exit 0.
- Parametric Control Engine: 40 passed; exit 0.
- TypeScript typecheck: PASS.
- Next.js production build: PASS and includes all GDSS-006D routes.

## AC. Backward Compatibility

GDSS-001..005 and GDSS-006A/B/C regressions remain green. The change is additive and does not alter
Control Engine, MQTT/DTE, telemetry ingestion, calibration meaning, simulation behavior or existing
evidence. Error and uncertainty remain orthogonal and no negative result is discarded.

## AD. Alembic Status

Source: one head, `0047`. Principal local database: `0047 (head)`. The disposable verification cycle
also ended at `0047` before cleanup; the principal database was never downgraded.

## AE. Git Status

All GDSS-006A/B/C/D code, migrations, tests and canonical documents remain local and uncommitted on
`main`, as authorized. No commit, push, tag or remote publication occurred.

## AF. Risks / Warnings

- Binary64 reductions are deterministic for the canonical ordered pair set and current implementation,
  but are not promised bit-identical across arbitrary future runtimes or altered reduction order.
- Empirical coverage describes the assessed set; it is not proof of universal predictive capability.
- Seasonal/reference baselines are only as meaningful as their declared lookup/fallback contracts and
  governed source provenance.
- `UNKNOWN` and partial completeness are intentionally first-class outcomes, not failures or zeros.

## AG. Final Status

`COMPLETED_GDSS_006D_METRICS_BASELINES_AND_UNCERTAINTY_FOUNDATION`

GDSS-006D answers what the governed results show. It does not decide whether the model possesses a
predictive capability and does not authorize any physical action.

## P024-R3 corrective addendum

P024 found that the planned hard limits were not executable in every layer. P024-R3 preserves the
contract and makes the implementation conform: a protocol selects metric definitions by distinct
`(metric_key, metric_version)` pairs in its acceptance criteria (maximum 16), while distinct baseline
versions actually evaluated against pair sets bound to that protocol are capped at 8. Migration
`0051` adds transaction-scoped advisory locking and PostgreSQL triggers for direct-SQL and concurrent
bypass resistance. Boundary evidence accepts 16/8 and rejects 17/9 with
`RESOURCE_LIMIT_EXCEEDED`. No metric formula, baseline algorithm or historical result was changed.
