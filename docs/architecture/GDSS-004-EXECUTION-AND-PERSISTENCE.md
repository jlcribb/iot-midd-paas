# GDSS-004 — Execution, Persistence and Recovery

Status: `PROPOSED`
Migration decision: `0042_LIKELY_REQUIRED`
Implementation and migration: `NOT_AUTHORIZED`

## Persistence decision

GDSS-004 requires new relational identities, ownership constraints, lifecycle and append-only
evidence that cannot be represented safely by GDSS-003 tables. A future
`0042_gdss_simulation_experimentation` migration is likely required. This is a candidate schema for
the Implementation Plan, not migration authorization.

## Candidate relational model

All project-owned tables carry `project_id` directly or enforce it through composite foreign keys.

### Design and lifecycle

| Candidate table | Purpose and key relationships |
|---|---|
| `gdss_experiment_identity` | Conceptual identity; project-owned canonical name. |
| `gdss_experiment_version` | Immutable version, predecessor, lifecycle projection and design hash; exact GDSS-003 base model/binding. |
| `gdss_experiment_lifecycle_event` | Ordered append-only DRAFT→VALIDATED→PUBLISHED→DEPRECATED events. |
| `gdss_experiment_factor` | Closed target and canonical ordered value domain; exact version FK. |
| `gdss_experiment_controlled_input` | Exact controlled target/value/unit; exact version FK. |
| `gdss_experiment_metric_definition` | Closed metric operation/version and state/threshold semantics. |
| `gdss_experiment_comparison_definition` | Operation/version, explicit reference/target, metric and temporal policy. |

Factor values may use a child relation for ordinal uniqueness and typed integrity. Essential
ownership, lifecycle, ordinals, references and hashes must not exist solely in opaque JSON.

### Execution and evidence

| Candidate table | Purpose and key relationships |
|---|---|
| `gdss_experiment_execution_attempt` | Attempt identity, exact version/design/manifest hashes, requester and acceptance data. |
| `gdss_experiment_materialized_scenario` | Pre-dispatch set, ordinal/hash/type, canonical manifest and GDSS-003 input hash. |
| `gdss_experiment_scenario_execution` | Append-only dispatch mapping and exact GDSS-003 attempt/input/result/trajectory hashes. |
| `gdss_experiment_execution_event` | Sequence 1 RUNNING and optional sequence 2 terminal only. |
| `gdss_experiment_metric_result` | Immutable per-scenario result or ineligibility bound to definition and trajectory evidence. |
| `gdss_experiment_comparison_result` | Immutable eligible/ineligible result bound to exact metric results. |
| `gdss_experiment_artifact` | Content-addressed manifest/result bytes, format, length and SHA-256. |
| `gdss_experiment_diagnostic` | Bounded ordered deterministic diagnostics by stage and evidence owner. |

Audit records remain in the existing audit authority.

## Integrity proposal

Candidate constraints/triggers enforce exact project/version ownership; version lineage; lifecycle
ordering and immutable published content; unique scenario ordinal/hash; committed scenario count
equal to manifest count; no dispatch before Transaction A; exact GDSS-003 mapping; no cross-project
attachment; append-only attempts/scenarios/mappings/events/results/artifacts/diagnostics; exactly one
RUNNING plus at most one terminal; terminal immutability; and exact-byte artifact collision checks.

## Canonical artifacts

Use the minimum two experiment-owned artifacts.

### ExperimentExecutionManifestArtifact

`GDSS_EXPERIMENT_MANIFEST_JSON_V1` contains design hash, semantic versions, completeness policy,
exact base GDSS-003 identities and every materialized scenario in canonical ordinal order. Each
binds its definition hash, type/reference, overrides, controlled-input proof and simulation input
hash. It excludes actor, attempt UUID, timestamps and dispatch data. Exact bytes produce the
manifest hash and commit in Transaction A.

### ExperimentResultArtifact

`GDSS_EXPERIMENT_RESULT_JSON_V1` contains manifest hash; every scenario in the same order; success,
failure, never-dispatched and aborted classifications; GDSS-003 input/result/trajectory hashes;
ordered metric/comparison evidence; comparative findings; completeness; and deterministic
diagnostics. Findings remain inside this result artifact to avoid a third authority. Relational
projections must agree byte-semantically. No artifact contains trajectory bytes.

## Transaction A — acceptance and materialization

One PostgreSQL transaction persists:

```text
ExperimentExecutionAttempt
+ complete ordered MaterializedScenario set
+ scenario execution placeholders
+ manifest artifact and hash
+ RUNNING event sequence 1
+ audit
+ COMMIT
```

Validation, bounded expansion and hashes complete before the transaction. Dispatch requires an
observable successful commit. Rollback leaves no dispatchable attempt.

## Independent bounded dispatch

Workers claim undispatched rows using database concurrency protection such as row locks,
`SKIP LOCKED`, leases and bounded batches. Database state, not a process mutex, is authoritative.

Each GDSS-003 request uses idempotency derived from project, manifest hash and scenario hash. Retry
may attach an existing attempt only when project, `simulation_input_hash`, scenario idempotency and
immutable versions all match. Never attach by latest run, similar parameters, actor or project
alone.

```text
PostgreSQL experiment transaction
    != distributed transaction across N GDSS-003 runs
```

Every simulation commits independently; orchestration assumes partial progress and recovery.

## Transaction B — result terminalization

When policy permits terminalization:

1. lock the non-terminal attempt;
2. reconcile every scenario against immutable GDSS-003 evidence;
3. read trajectories through `GovernedTrajectoryReader`;
4. compute bounded metrics in canonical definition/scenario order;
5. compute comparisons in canonical definition order;
6. build findings and canonical result artifact;
7. persist projections, artifact, diagnostics, one terminal event and audit in one transaction;
8. commit.

Rollback leaves `RUNNING` and retryable. Unknown commit recovery reads immutable sequence 2 and
verifies expected result hash before retry.

## Terminal classification

- `COMPLETED`: every required scenario and required metric/comparison succeeded.
- `COMPLETED_WITH_FAILURES`: failures are explicit, policy is `ALLOW_PARTIAL_EXPLICIT`, remaining
  evidence is valid, and unavailable comparisons are persisted `INELIGIBLE`.
- `FAILED`: `ALL_REQUIRED_SCENARIOS` cannot be satisfied, foundational evidence is invalid, or no
  valid canonical result can be produced.
- `ABORTED`: authorized abort stopped future dispatch and records all scenario classes.

Sequence 2 is immutable. A terminal attempt cannot acquire a third event.

## Abort semantics

Only project admins with `ABORT_EXPERIMENT` may abort a non-terminal attempt. The request is
idempotent and audited. It atomically closes future dispatch, does not invent GDSS-003 cancellation,
preserves completed/failed/dispatched evidence, classifies never-dispatched scenarios, and
terminalizes once as `ABORTED`.

Already-running simulations may finish independently. Late results may append only operational
reconciliation/audit evidence that cannot alter the terminal event, result artifact or hash.

## Recovery policy

`GDSS_EXPERIMENT_RECOVERY_V1` requires Implementation Plan values for abandonment, leases, retries
and backoff. Database locks make recovery concurrency safe.

| Condition | Recovery action |
|---|---|
| Abandoned RUNNING | Reconcile full manifest, resume eligible dispatch or terminalize by policy. |
| Partial dispatch | Dispatch only rows without reconciled attempt identity. |
| Duplicate dispatch | Resolve same GDSS-003 idempotent attempt; conflicting identity fails. |
| GDSS-003 completed before mapping commit | Attach only by exact idempotency/input/version identity. |
| Unknown mapping commit | Verify immutable mapping hashes before retry. |
| Worker crash | Lease expires; another worker claims without semantic duplication. |
| Transaction B unknown commit | Accept exact sequence-2 result hash or fail conflict. |
| Concurrent recovery | Database locking permits one semantic transition. |

Worker timing, retries and order never change computational identity.

## Resource architecture

`GDSS_EXPERIMENT_LIMITS_V1` independently bounds:

```text
canonical design bytes
factors
values per factor
expanded scenarios
overrides per scenario
controlled inputs
metric definitions
comparison definitions
total referenced trajectory points
aggregate referenced trajectory bytes
metric operations
comparison operations
diagnostics
concurrent scenario dispatches
dispatch attempts and retries
orchestration duration
manifest artifact bytes
result artifact bytes
```

Exact values require benchmarks in the Implementation Plan. No limit is inherited implicitly from
GDSS-003; each scenario also satisfies simulation limits and each expression satisfies expression
limits.

## Security and dependency boundary

Fail closed on scenario-count overflow, oversized designs/artifacts, operation exhaustion,
dispatch/retry storms, cross-project/version references, hash or trajectory substitution, malformed
artifacts and unauthorized lifecycle/run/abort actions.

V1 has no `eval`, `Function`, callback, plugin, dynamic import, arbitrary expression, scripting
runtime, optimizer or AI provider. It requires no MQTT, telemetry, Control Engine, DTE, device
access or actuation.
