# Controlled Policy Version Candidate

M7.2 materializes a validated M7.1 proposal into an immutable controlled policy version candidate. It strengthens C4/C5/C6 without changing an active policy, a runtime configuration, deployment state, MQTT, an outbox, or hardware. `physical_effects=false` is persisted in both the candidate and audit context.

## Eligibility and materialization

`POST /api/control/promotion/projects/:projectId/policy-version-candidates` accepts only `{ "proposalId": "UUID" }`. The server resolves all evidence. Creation is allowed only when the proposal is `VALIDATED`, its authoritative assessment is `PASSED`, and the project-scoped M6 candidate and its hashes can be resolved. Failed, blocked, pending, cross-project, or incomplete provenance is rejected.

The pure materializer emits this canonical configuration snapshot:

```json
{"strategy_type":"proportional","strategy_schema_version":1,"parameters":{"gain":0.3,"setpoint_value":50}}
```

Only `proportional` and `threshold` are supported. Simulation IDs, trace IDs, batches, timestamps, and actor data are excluded from configuration and are kept as a frozen provenance hash snapshot.

## Identity, lifecycle, and safety

`configuration_hash` is SHA-256 over the canonical semantic configuration. `policy_version_hash` additionally includes project identity, proposal/assessment/candidate hashes, strategy, version number, materializer version, and schema version. Thus identical configurations may legitimately have different governed provenance identities.

The version namespace is `(project_id, strategy_type)` and labels are `v1`, `v2`, etc. A transaction-level PostgreSQL advisory lock for that namespace, plus a uniqueness constraint, makes allocation concurrency-safe. Replaying the same proposal and materializer returns the same row and emits no second audit event.

The only M7.2 state is terminal `CANDIDATE`. The table has an immutable-update trigger; there are deliberately no activation, deployment, apply, publish, rollback, outbox, or runtime endpoints.

## Access, audit, and reads

GET list/detail requires `view_dashboard`; POST requires the existing `edit_policies` capability. The creation audit is `CONTROLLED_POLICY_VERSION_CANDIDATE_CREATED` and records project, actor, version candidate, strategy, hashes, version number, and `physical_effects=false`.

`GET /api/control/promotion/projects/:projectId/policy-version-candidates?strategyType=proportional` lists candidates. `GET /api/control/promotion/projects/:projectId/policy-version-candidates/:versionCandidateId` retrieves one. A future capability may introduce a distinct `create_controlled_policy_candidate` permission, but M7.2 intentionally reuses `edit_policies`.
