# MIDD-IOT — GDSS-005 Implementation Evidence

**Prompt chain:** `MIDD-GDSS-P016` → `MIDD-GDSS-P016-V1` → `MIDD-GDSS-P016-R1` → `MIDD-GDSS-P016-R2`

**Status:** `COMPLETED_GDSS_005_SCHEMA_ABORT_REMEDIATION_AND_GOVERNED_CEILING_CLOSURE`

**Baseline:** `main@79f5fe8efde94de817d7e3403e234d81124e632a`

**Final Alembic revision:** `0043 (head)`; one head

## Evidence history

The evidence sequence is intentionally preserved. P016 produced the initial implementation evidence. P016-V1 detected that the first benchmark was a computational proxy and therefore could not substantiate governed database/runtime claims. P016-R1 replaced that overclaim with real GDSS-003 and PostgreSQL execution, exposing the 0043 abort mismatch and the B3 resource failure. P016-R2 corrected those implementation defects and completed the governed verification.

No earlier architecture package was reopened. The correction remained inside the uncommitted GDSS-005/0043 boundary, plus the narrow GDSS-003 artifact-write remediation required by the authorized B3 ceiling.

## Implemented boundary

GDSS-005 implements immutable governed observation evidence, exact observation/simulation alignment, bounded deterministic finite-grid calibration, exact GDSS-003 evidence linkage, lease recovery, governed abort, reproducible parameter-estimate evidence, content-addressed artifacts, scoped model-adequacy evidence and separately governed review/publication.

It adds no HTTP route, UI, live ingestion, MQTT, Control Engine, DTE, prediction, recommendation, control or physical authority. A calibration result cannot authorize physical action.

## R2 remediations

- 0043 permits `PENDING|CLAIMED → NOT_DISPATCHED_ABORTED` only after governed attempt abort metadata and one immutable `ABORTED` execution event exist. Dispatched and terminal evidence cannot be rewritten as not dispatched.
- Abort is atomic: attempt metadata, one terminal event, pending-candidate closure and audit evidence commit together; late dispatched evidence remains immutable and does not replace the `ABORTED` attempt terminal.
- Claim recovery uses a new token after lease expiry, preserves parameter-vector identity and permits exactly one GDSS-003 attachment and candidate terminal.
- Observation validation reconstructs the relational dataset, canonicalizes it and rejects semantic/byte mismatch with `ARTIFACT_RECONCILIATION_FAILURE`.
- The governed fixture is the literal reservoir/thermal system `dV/dt = Qin - Qout` and `dT/dt = -k(T - Tambient)`, with SI-compatible catalog dimensions and canonical shared unit revisions.
- Worker memory is bounded by retaining full residuals only for the current winner; all candidate objective, identity, operation and terminal evidence remains persisted.
- Residual evidence uses canonical `GDSS_CALIBRATION_RESIDUALS_V1` NDJSON with header, ordered per-series tuples and summary; every residual point remains represented.
- Large trajectory payloads use a zero-copy buffer view and a PostgreSQL advisory transaction lock, serializing only the large content-addressed artifact write without changing candidate concurrency or workload.

## Relational and migration evidence

- Tables: 21.
- Guard functions: 10.
- Table triggers: 28.
- Constraints: 181.
- Indexes: 77.
- Exact model FK: `(model_identity_id, model_version_id) → gdss_version(identity_id, id)`.
- Exact binding FK: `(binding_version_id, model_version_id) → gdss_dynamic_binding_version(id, model_version_id)`.
- Required migration cycle `0042 → 0043 → 0042 → 0043`: PASS.
- All 21 tables were empty before downgrade; 0042 contained no GDSS-005 relations/functions; the final database is `0043 (head)`.
- Final residue: zero live rows in all 21 GDSS-005 tables.

## Governed runtime evidence

### B1

- Literal reservoir equation; 1,001 observations; 9 candidates.
- Concurrency 1/8 produced identical alignment, vector, estimate-set and result identities.
- Winner `Qout=1`; objective bits `0000000000000000`.
- Counts per attempt: 9 claims, 9 dispatches, 9 GDSS-003 links, 9 candidate terminals, one attempt terminal.
- Final observed wall time: 984.257 ms (reference) and 1,760.280 ms (concurrency eight).

### B2

- Literal reservoir and thermal equations; 4,002 compared values per candidate; 64 candidates.
- Concurrency 1/8 produced identical computational identity.
- Winner `{Qout:1,k:1}`; objective bits `0000000000000000`.
- Final reference/concurrency-eight wall time: 8,420.599/9,104.152 ms; maximum observed RSS 269,664,256 bytes.
- Cancellation probe `{Qout:0.75,k:1.25}` had objective `14.662284573815068`, proving the two series cannot cancel into a false optimum.

### B3 governed ceiling

- Workload unchanged: 8 series, 80,008 points, `4×4×4×4=256` candidates, concurrency eight.
- Final retry wall time: 243,522 ms; contractual limit: 900,000 ms.
- Winner `{Qout:1,k:1,p3:1,p4:2}`; objective bits `0000000000000000`.
- Objective operations: 81,936,640; contractual limit: 100,000,000.
- Periodic Node RSS sampling: the final retry revalidated `<1 GiB`; the last fully captured exact sample for the same governed workload was 588,480,512 bytes (561.22 MiB).
- Alignment hash: `c597e72e5d33f972cc0568879dc87c43f9ac614f924132bcf703a36e88801e2d`.
- Counts: 256 claims, 256 dispatches, 256 unique GDSS-003 links, 256 candidate terminals and one attempt terminal.
- Dataset artifact: 31,509,661 bytes.
- Manifest artifact: 18,278,511 bytes.
- Residual artifact: 16,002,406 bytes.
- Result artifact: 511 bytes.
- Aggregate: 65,791,089 bytes; contractual limit: 67,108,864 bytes.
- PostgreSQL remained running with `OOMKilled=false` and restart count zero.

One pre-retry execution completed in 967,610 ms and failed only the 900,000 ms wall limit. Its fixture was cleaned, PostgreSQL had no OOM/restart, ordinary `VACUUM ANALYZE` reclaimed test-table reuse, and the exact unchanged workload then passed in 243,522 ms. This is retained as environment-pressure evidence, not suppressed.

## Concurrency, recovery and abort evidence

- Twenty real database attempts: 20 distinct attempt IDs, zero duplicate claims, zero duplicate GDSS-003 links, zero duplicate candidate terminals, zero duplicate attempt terminals and zero identity drift.
- Expired-lease recovery: two claim events/tokens for the same candidate/vector, one dispatch, one attachment and one terminal.
- Governed abort: 63 pending candidates became `NOT_DISPATCHED_ABORTED`, zero post-abort claims, one `ABORTED` attempt terminal, dispatched evidence retained, late `SUCCEEDED` evidence accepted without changing attempt terminality.
- Relational/canonical dataset mismatch and stored metadata/payload mismatch both fail closed.

## Verification matrix

- GDSS-005 invariants and kernel benchmarks: 18/18 PASS; the 14 invariant tests cover the 40 stable invariant records.
- GDSS-005 PostgreSQL enforcement: 10/10 PASS.
- GDSS-001 PostgreSQL: 12/12 PASS.
- GDSS-002 PostgreSQL: 1/1 PASS.
- GDSS-003 + GDSS-004 PostgreSQL: 12/12 PASS.
- Full `topology-next`: 469 passed, 50 environment-gated skips; guarded integration suites were run separately above.
- TypeScript `tsc --noEmit`: PASS.
- Next.js production build: PASS.
- General Python suite: 179 passed, 6 environment-gated skips.
- Parametric Control Engine: 40/40 PASS.
- Lint: not applicable; the package defines no lint script.

The PostgreSQL suites were finally run in isolated fixture families because accepted GDSS-001 test fixtures and the current GDSS-002 canonical catalog use incompatible definitions for the same global unit revision. Parallel execution can race on that global catalog and was observed to fail closed with `GDSS catalog revision immutable`; isolated governed runs all pass. No production catalog guard was weakened.

## Findings and authority boundary

R2 findings `R2-F01..R2-F06` are closed. No blocking or non-blocking implementation finding remains for controlled local Git closure. Publication, tag, release and remote operations remain future-scope actions.

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

What physical action can GDSS-005 authorize? **NOTHING.**

## Recommendation

`READY_FOR_GDSS_005_CONTROLLED_GIT_CLOSURE`
