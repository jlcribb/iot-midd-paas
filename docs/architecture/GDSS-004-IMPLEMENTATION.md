# GDSS-004 — Implementation Record

Status: `COMPLETED_GOVERNED_SIMULATION_EXPERIMENTATION`

Baseline: branch `main`, immutable HEAD `10d454e985f904228c5b62dd5cb12c6b2171e6d2`. The only migration added is `0042_gdss_simulation_experimentation.py`; code and PostgreSQL are at the single Alembic head `0042`.

## Implemented boundary

The production core is under `apps/topology-next/src/lib/gdss/experiment`. It implements closed design/scenario contracts, deterministic eager expansion, expected-value overrides, controlled-input proofs, exact canonical identities and artifacts, governed GDSS-003 trajectory reads, eight metrics, four comparisons, temporal eligibility, result construction, authorization, limits and recovery constants. PostgreSQL adapters implement design lifecycle, Transaction A, bounded claims, exact GDSS-003 links, terminal scenario evidence, one-way abort and Transaction B. The worker uses deterministic idempotency keys and a maximum concurrency of eight.

There is no telemetry, MQTT, Control Engine, DTE, prediction, recommendation, calibration, optimization or physical-action dependency. Results have provenance `SIMULATION_DERIVED` and physical authority `NONE`.

## Persistence and migration evidence

- Exactly 15 `gdss_experiment_*` tables, 14 explicit indexes plus primary/unique indexes, composite ownership FKs, SHA-256 payload checks and closed vocabularies.
- Lifecycle, design freeze, attempt ownership, complete pre-dispatch universe, scenario transitions, single terminal event, abort, result ownership and append-only guards are enforced in PostgreSQL.
- Safe empty-state cycle `0041 → 0042 → 0041 → 0042`: PASS.
- PostgreSQL integration: 6/6 PASS, including Transaction A rollback, no dispatch before commit, two-worker collision resistance, 64-scenario/concurrency-8 dispatch, abort and immutable Transaction B.
- Residual rows after integration cleanup: zero in each of the 15 tables.

## Deterministic evidence

- Focused core/invariant/benchmark tests: 63/63 PASS.
- Invariant closure: `GDS4-INV-01..40` and `GDS4-ARCH-INV-01..12`, 52/52 PASS.
- GDSS-001/002/003 focused regressions with PostgreSQL: 139/139 PASS.
- Full Next suite: 451 PASS, 33 environment-conditioned skips.
- Python middleware: 179 PASS, 6 environment-conditioned skips.
- Parametric Control Engine: 40/40 PASS.
- Strict TypeScript and production Next build: PASS.

## Benchmark evidence

| Gate | Scenarios | Points | Trajectory bytes | Metric ops | Comparison ops | Manifest bytes | Result bytes | Terminal evidence rows | Orchestration event rows | Concurrency | Elapsed | Heap delta | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| A | 4 | 40,004 | 7,197,080 | 120,000 | 15 | 18,129 | 15,417 | 30 | 16 | 4 | 507.582 ms | 41,726,080 | PASS |
| B | 64 | 128,064 | 22,993,152 | 896,192 | 32 | 278,652 | 354,372 | 613 | 256 | 8 | 1,623.337 ms | 42,011,568 | PASS |
| C | 256 | 1,000,000 | 179,766,528 | 27,995,904 | 64 | 1,020,332 | 5,215,554 | 8,517 | 1,024 | 8 | 14,114.850 ms | 411,672,184 | PASS |

Gate B additionally exercised real PostgreSQL/GDSS-003 dispatch persistence for 64 scenarios at concurrency eight in 2,676 ms. Terminal-evidence row accounting is reported separately from append-only orchestration history so both governed dimensions remain visible.

## Scenario-sequence concurrency remediation

`MIDD-GDSS-P012-R1` reproduced an intermittent persistence race in three of five repeated
PostgreSQL runs (and once during the preceding Git-closure gate). Candidate discovery could
retain a stale latest-event view while waiting for a materialized-scenario lock. Because the
scenario-event trigger also took an exclusive lock on the experiment attempt, an unrelated
scenario transaction could delay that insert until another worker had already committed the
same scenario's `CLAIMED` event. The delayed worker then proposed sequence 2 against committed
sequence 2 and correctly raised `Scenario execution sequence gap`.

Sequence is scoped to one materialized scenario and represents semantic transition order, not
experiment-wide database insertion order. The remediation revalidates eligibility and the latest
event after acquiring the scenario lock, refills a bounded claim batch after rejecting stale
candidates, serializes transition allocation per materialized scenario, and uses a shared attempt
lock only to coordinate abort/finalization. Exact `DISPATCHED`, terminal and exhaustion replays are
idempotent, covering client acknowledgement loss without adding semantic events.

Post-remediation evidence: Gate B passed 20/20 consecutive real-PostgreSQL executions at 64
scenarios and concurrency eight, with elapsed dispatch/persistence times from 576 ms to 1,514 ms.
There were zero sequence gaps, duplicate claims, duplicate GDSS-003 links or duplicate terminal
events. The strengthened 6-test PostgreSQL suite also covers claim/reclaim, third-attempt
exhaustion, unknown-commit replay, terminalization collision, abort/claim, abort/terminalization
and a late GDSS-003 result. The safe empty-state migration cycle `0042 → 0041 → 0042` passed.

## Authority statement

What physical action can a successful GDSS-004 experiment authorize?

`NOTHING.`
