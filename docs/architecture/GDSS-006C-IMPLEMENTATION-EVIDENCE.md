# GDSS-006C — Implementation Evidence

Prompt: `MIDD-GDSS-P020-R1`
Status: `COMPLETED_GDSS_006C_VALIDATION_RUNS_PREDICTION_COMMITMENT_AND_PAIRING`

## A. Baseline

- Checkout: `/Users/joseluis/dev/iot-midd-paas-auth-work`
- Branch: `main`; baseline HEAD: `dee81328f4a73b525f8d7236d8ee799044b9cabc`.
- Initial single Alembic head/current: `0045`; GDSS-006A, GDSS-006B and canonical GDSS-006 documents were classified as the only existing uncommitted material.
- No unrelated files were incorporated.

## B. Scope Implemented

Implemented only validation runs, scientific prediction records, platform commitments, governed observation references, deterministic prediction–observation pairs, integrity assessments and immutable pair sets. No metric, baseline, uncertainty, domain-position evaluation, evidence set, capability assessment, claim or control authorization was introduced.

## C. Files Changed

- Domain: `run-contracts.ts`, `run-canonical.ts`, `run-lifecycle.ts`, `run-integrity.ts`, `run-authorization.ts`, `run-diagnostics.ts`, plus validation barrel exports.
- Persistence/service: `gdss-validation-run.repository.ts`, `gdss-validation-run.service.ts`, DB error mapping and request validators.
- HTTP: project-scoped run, transition, prediction, commitment, observation-reference, pair and pair-set routes.
- Migration: `0046_gdss006c_validation_runs_prediction_pairing.py`.
- Verification: `gdss-validation-run.test.ts` and the PostgreSQL custody/run integration suite.
- Canonical documentation: this evidence file and the GDSS-006 implementation-plan status.

## D. Migration 0046

`0046` creates nine normalized relations: validation run, run event, prediction record, prediction commitment, observation reference, prediction–observation pair, pair integrity assessment, prediction pair set and pair-set member. Foreign keys, composite project keys, unique semantic hashes/idempotency keys and trigger guards enforce the governed boundary.

Isolated cycle on `gdss006c_verify_20261007`: `0045 -> 0046 -> 0045 -> 0046` PASS. The disposable database was used so the principal database was never downgraded.

## E. ValidationRun Model

Every run stores exact protocol/model/partition/snapshot/domain identifiers and hashes, optional exact holdout/evaluation reference, independence state, run mode, creator and DB time. No `latest` resolution exists. Holdout use requires the exact GDSS-006B evaluation reference and `OPENED_FOR_EVALUATION + INDEPENDENT`.

## F. Run Lifecycle

`CREATED -> READY -> RUNNING -> COMPLETED|FAILED`, with governed invalidation edges. Events are append-only, sequenced and idempotent; the DB serializes competing starts. `COMPLETED` means execution ended and carries no acceptance semantics. Direct row mutation is rejected.

## G. PredictionRecord

The scientific content includes the exact model/hash, target, forecast origin, typed horizon, predicted value/unit, input/parameter/boundary hashes, mode and optional complete trajectory reference/hash. It excludes row, worker and session identity. A prediction must match its running run's model and mode.

## H. Prediction Commitment

Prediction and commitment are separate rows. One transaction locks the prediction, verifies its semantic hash, writes one append-only commitment, obtains `committed_at` from `clock_timestamp()`, and writes audit evidence. Retrying returns the existing physical commitment. Post-commit prediction update and commitment update/delete fail.

## I. Trust Model

Trust class is exactly `PLATFORM_PROSPECTIVE`: PostgreSQL transaction + DB time + append-only record + SHA-256 + same-transaction audit. It is explicitly not external cryptographic timestamping or third-party notarization.

## J. Observation Reference

References preserve external observation identity, source, target/value/unit, source content hash, measurement/availability/ingestion times, provenance reference and successor relation. Unknown times/provenance remain explicit `null`; no timestamp is invented.

## K. Temporal Integrity

Forecast origin, prediction creation, DB commitment, observation measurement, availability, ingestion and pairing time are distinct. Strong prospectivity requires `committed_at < availability_time`. Unknown availability yields `TEMPORAL_INTEGRITY_UNKNOWN`; later commitment yields retained `PREDICTION_AFTER_OBSERVATION` evidence.

## L. Prediction–Observation Pairing

V1 contracts are `EXACT_TIMESTAMP`, `NEAREST_WITHIN_TOLERANCE`, `WINDOW_AGGREGATE` and `EXACT_EVENT_ID`. Tolerance/unit/direction, aggregate identity, event identity and conversion identity/version are strict when applicable. Nearest selection is derived deterministically from eligible observations, preventing caller cherry-picking.

## M. Pair Integrity

Assessments distinguish PASS, temporal unknown, post-observation prediction, target/horizon/unit mismatch, rule violation, ineligible observation and invalidation. Target, horizon, unit and project mismatches are rejected at persistence; temporal violations remain retained and audited.

## N. Pair Sets

Pair identities are canonically sorted/de-duplicated before hashing. Membership, target, horizon and scope are verified at materialization. Set and member rows are immutable; any membership change requires a new set/hash.

## O. Hashing & Determinism

Domain-separated SHA-256 namespaces are used for run, prediction, commitment, observation reference, pair, integrity and pair set. Tests prove ordering stability and sensitivity to value, horizon, model, inputs, observation, rule, tolerance, membership, target and horizon.

## P. Authorization

`RUN_VALIDATION` is project-scoped and granted to authenticated OAuth operators/admins; viewers and development fallback are rejected. The same permission covers prediction generation/commitment inside the governed run. No unnecessary commitment permission was added.

## Q. Audit

Run creation/transitions, prediction creation/commitment, observation reference creation, pairing, integrity assessment and pair-set materialization write the required audit actions in the same transaction as scientific state.

## R. API/Services

All required service operations exist: create/ready/start/complete/fail/invalidate run, create/commit prediction, create observation reference, pair/assess and materialize pair set. Official Next.js project-scoped POST routes expose those commands with strict envelopes and authenticated actor resolution.

## S. Domain Errors

The required validation-run, commitment, observation, temporal, mismatch, immutability and cross-project codes are typed and mapped from PostgreSQL trigger failures to HTTP domain errors.

## T. Invariants

GDSS-006C exercises VAL-INV-12, 15 and 23–25 and supports 37 without renumbering: prediction is not predictive evidence; exact versions bind; prospective ordering is demonstrable; evidence is immutable; no authority crosses into actuation.

## U. Tests

- GDSS-006C domain: 9/9 PASS.
- Real PostgreSQL GDSS-006A/B/C focused regression: 24/24 PASS.
- Real PostgreSQL concurrency/custody/run suite: 11/11 PASS.
- Migration cycle: PASS.

## V. Adversarial Tests

PASS: post-observation commitment retained as violation, unknown availability fail-closed, prediction and commitment tampering rejected, wrong model/protocol rejected, target/horizon/unit mismatches rejected, pair/run/pair-set mutation rejected, deterministic nearest selection enforced, and exact holdout bindings enforced by DB triggers.

## W. Concurrency

Real PostgreSQL tests execute competing holdout opens and competing validation-run starts, prediction commitments and pair inserts. Outcomes are one lifecycle transition, one physical commitment and one effective pair; retries are deterministic/idempotent or conflict explicitly.

## X. Performance

Diagnostic full-suite sample: 1,000 prediction hashes in 121.097 ms; one 10,000-member pair-set canonical hash in 14.648 ms. Focused sample was 25.486 ms and 6.813 ms respectively. PostgreSQL holdout/open concurrency diagnostic was 201.203 ms. These are observations, not SLAs.

## Y. Regression

- topology-next: 498 passed / 74 skipped.
- Python runtime: 179 passed / 6 skipped.
- Parametric Control Engine: 40 passed.
- TypeScript typecheck: PASS.
- Next.js production build: PASS, including all GDSS-006C routes.
- Static forbidden-boundary scan: PASS.

## Z. Backward Compatibility

GDSS-001..005 and GDSS-006A/B remained green. The change is additive and does not alter Control Engine, MQTT/DTE, telemetry, calibration meaning, simulation semantics or existing persisted evidence.

## AA. Alembic Status

Source: one head, `0046`. Principal local database: `0046 (head)`. The isolated cycle also ended at `0046`.

## AB. Git Status

All GDSS-006A/B/C code, migrations, tests and canonical documentation remain local and uncommitted on `main`, as authorized. No push, tag or remote publication occurred.

## AC. Risks / Warnings

- `PLATFORM_PROSPECTIVE` proves ordering only inside the Midd-IoT/PostgreSQL trust boundary; it is not an external TSA.
- Unit conversion is traceable by identity/version but the conversion engine is not implemented in this phase.
- Near-duplicate evidence detection remains the declared GDSS-006B limitation.
- Failed runs and invalid temporal pairs intentionally remain stored as audit evidence.

## AD. Final Status

`COMPLETED_GDSS_006C_VALIDATION_RUNS_PREDICTION_COMMITMENT_AND_PAIRING`

The phase governs whether a value existed before its target observation became epistemically available. It makes no assertion about predictive quality; that remains GDSS-006D.
