# MIDD-IOT — GDSS-003
## Governed Dynamic Simulation Runtime Foundation
### Persistence Architecture v0.1

**Version:** `v0.1`
**Status:** `PROPOSED_FOR_REVIEW`
**Implementation:** `NOT_YET_AUTHORIZED`
**Baseline:** `dade8e6d490ea3adc88aac0353c2e72fee2df47b`
**Alembic baseline:** `0040`

## Formal decision

Select option C: relational immutable manifests plus content-addressed trajectory artifacts.

```text
MIGRATION_ARCHITECTURE_DECISION = 0041_LIKELY_REQUIRED
0041 AUTHORIZATION = NOT_GRANTED
```

Ephemeral-only execution is insufficient for governed reproducibility and audit. Persisting only a
manifest loses result evidence. Normalizing every point into PostgreSQL creates unbounded row volume
and couples scientific artifacts to transactional query storage. Hybrid persistence preserves
queryable identity/status while separating potentially large immutable bytes.

## Proposed logical records

Names are reserved proposals, not current schema:

```text
gdss_dynamic_binding_identity
gdss_dynamic_binding_version
gdss_simulation_execution
gdss_simulation_diagnostic
gdss_simulation_artifact
```

Binding identity is project-owned. Binding version references one exact `gdss_version`, stores
canonical binding content/hash, version and predecessor, and follows an explicit governance
lifecycle separate from the model lifecycle. Only an immutable published binding is executable.

Each execution stores attempt UUID, project, exact model/binding IDs and hashes, input manifest/hash,
status, termination reason, result hash, artifact reference, actor and audit timestamps. Diagnostics
are append-only and sequence ordered. No row references `control_simulation_sessions` or
`control_simulation_runs`.

Every manifest persists `unitConversionCatalogVersion: GDSS_UNIT_CONVERSION_V2`. This exact value
participates in `simulation_input_hash`; current/latest catalog resolution is forbidden.

## Trajectory artifact

The canonical artifact uses a versioned media type and encoding, strict step-index order, sorted
state symbols and canonical binary64 values. Its SHA-256 is computed over exact canonical bytes.
Relational metadata stores hash, size, media type, format version and opaque storage locator.

The architecture requires a content-addressed artifact abstraction but does not select or provision
an object-store product in P007. An implementation plan must resolve the existing storage facility,
transaction boundary and garbage-collection policy before migration authorization.

Missing or hash-mismatched artifacts fail closed as `ARTIFACT_UNAVAILABLE` or
`ARTIFACT_INTEGRITY_FAILURE`; metadata alone must not masquerade as a reproducible trajectory.

## Immutability and attempts

- Published binding versions are immutable; changes create successors.
- Every accepted execution creates a new `execution_attempt_id`, even when input hash matches.
- A completed or failed attempt and its diagnostic/artifact linkage are immutable.
- Idempotent request handling may return the same attempt only for an explicit request idempotency
  key; it must not silently deduplicate all equal computations.
- Equal input hashes may yield equal deterministic result hashes while preserving distinct attempts.
- Model, solver or unit-catalog changes never reinterpret historical executions.

The preferred database enforcement is append-only events/rows plus update/delete guards, consistent
with GDSS lifecycle and immutable authorization evidence already present in the repository.

## Partial results

A failed attempt may persist the last valid committed points in a `PARTIAL` artifact. The execution
remains `FAILED`; its result hash binds failure status, termination reason and partial artifact hash.
Invalid candidate values are diagnostics, not trajectory points. Retention policy must treat partial
evidence independently from complete results.

## Audit separation

Actor, request/completion wall-clock, request ID and operational storage metadata belong to audit
identity. They are excluded from binding, input, trajectory and result hashes. Audit writes use the
existing scoped audit convention but cannot mutate computational evidence.

## Transaction and artifact integrity

Implementation must avoid a committed success row pointing to unavailable bytes. Acceptable future
protocol: write and verify immutable artifact, then atomically commit terminal execution metadata;
on failure record a non-success terminal state. Locator changes, if operationally required, must be
separate audited metadata and cannot change artifact identity.

## Retention and export

Retention must never delete an artifact while a governed execution still claims reproducibility.
Export includes model/binding snapshots, input manifest, artifact, deterministic diagnostics and
hash verification instructions. Current database defaults, latest versions, telemetry and wall
clock are never reproduction inputs.

## Deferred implementation decisions

P007 does not choose database columns, indexes, object-store vendor, artifact compression, quotas,
retention duration or migration SQL. Those require an approved implementation plan and explicit
`0041` authorization.
