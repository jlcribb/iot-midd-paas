# Deployment preparation and operational readiness (M7.4)

M7.4 records immutable evidence for a possible future deployment. It does not deploy, activate, bind a runtime, publish MQTT, create an operational outbox command, or affect hardware. `READINESS_PASSED` means only that the recorded target declarations and current governed evidence are sufficient for a later, separately authorized phase.

## Target scope and preparation

The canonical v1 target scope is an existing `public.assets` row in the same project. A target reference is not a policy/runtime binding. Creation requires the authoritative M7.3 chain: candidate, `PASSED` validation, and `APPROVE_FOR_CONTROLLED_DEPLOYMENT_PREPARATION` approval.

Preparations are immutable and idempotent by project, candidate, target asset, and preparation policy. Their canonical hash binds project/candidate identity, policy-version hash, validation hash, approval hash, target asset, policy version and schema version. It excludes database IDs created for the artifact and timestamps.

## Readiness declarations and gates

The target asset must explicitly declare only evidence the topology contract can represent, under `metadata.control_readiness`:

```json
{
  "supported_strategy_types": ["proportional"],
  "supported_strategy_schema_versions": [1],
  "runtime_capabilities": ["strategy_evaluator", "input_signal", "output_channel", "policy_schema"],
  "security_boundary": { "governed_control": true },
  "observability": { "telemetry": true, "runtime_status": true, "control_output": true, "audit_path": true }
}
```

Missing declarations fail readiness rather than being assumed. The assessment records 12 blocking gates: M7.3 approval, version identity, provenance, target scope/topology/compatibility, runtime declarations, security boundary, conflicting active binding, rollback evidence, observability, and no deployment execution. `ERROR` produces `BLOCKED`; otherwise `FAIL` produces `FAILED`; only all `PASS` produces `PASSED`. `NO_PRIOR_POLICY` is explicit rollback evidence for a first deployment target, not fabricated rollback history.

The readiness hash canonically binds the preparation hash, sorted gate results, readiness policy, engine, and schema version. Final assessment and gate rows are immutable.

## API and RBAC

GET endpoints require `view_dashboard`; preparation and assessment creation use the existing least-powerful temporary `edit_policies` capability and write `rbac_debt:"edit_policies"` into audit context.

- `POST|GET /api/control/promotion/projects/:projectId/policy-version-candidates/:candidateId/deployment-preparations`
- `GET /api/control/promotion/projects/:projectId/policy-version-candidates/:candidateId/deployment-preparations/:preparationId`
- `POST|GET /api/control/promotion/projects/:projectId/policy-version-candidates/:candidateId/deployment-preparations/:preparationId/readiness-assessments`
- `GET /api/control/promotion/projects/:projectId/policy-version-candidates/:candidateId/deployment-preparations/:preparationId/readiness-assessments/:assessmentId`

Preparation POST body: `{ "targetAssetId": "UUID" }`. No deploy, activate, apply, enable, bind, or execute endpoint exists.

## Audit and boundary

Migration `0033` adds immutable preparation, readiness assessment, and gate-result tables. It emits `CONTROLLED_DEPLOYMENT_PREPARATION_CREATED` and `OPERATIONAL_READINESS_ASSESSMENT_CREATED`, both with `physical_effects:false`. Security readiness requires the target declaration and `CONTROL_RBAC_ALLOW_DEV_FALLBACK=false`; enabled development fallback blocks readiness.

M7.4 ends at evidence. A future deployment requires an additional explicit human authority boundary.
