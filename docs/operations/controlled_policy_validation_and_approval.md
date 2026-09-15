# Controlled policy validation and approval (M7.3)

M7.3 adds immutable validation evidence and a single authoritative approval to an existing M7.2 controlled-policy version candidate. It is a governance boundary only: it does not activate a policy, create a runtime binding, publish MQTT, enqueue an outbox message, or affect hardware.

## Lifecycle

1. An authorized operator creates (or replays) validation for a candidate.
2. The deterministic engine records these blocking gates: candidate immutability, promotion assessment, configuration schema and hash, provenance, version identity, project scope, and absence of operational binding.
3. `ERROR` in a gate yields `BLOCKED`; otherwise a `FAIL` yields `FAILED`; all passes yield `PASSED`.
4. A reviewer can record exactly one approval evidence record. `APPROVE_FOR_CONTROLLED_DEPLOYMENT_PREPARATION` requires `PASSED`; `REJECT` and `REQUEST_REVALIDATION` remain available as governed negative outcomes.

Both artifacts carry canonical hashes. Validation creation is idempotent by project, candidate, and validation policy version. Approval replay is idempotent only when the decision, normalized rationale, reviewer, and bound validation hash produce the same approval hash; a different decision conflicts.

## API and authorization

`GET` endpoints require `view_dashboard`; creation and approval use the existing temporary `edit_policies` capability. Project scope is enforced on every path.

- `POST|GET /api/control/promotion/projects/:projectId/policy-version-candidates/:candidateId/validations`
- `GET /api/control/promotion/projects/:projectId/policy-version-candidates/:candidateId/validations/:validationId`
- `POST|GET /api/control/promotion/projects/:projectId/policy-version-candidates/:candidateId/validations/:validationId/approval`

Approval POST body: `{ "decision": "APPROVE_FOR_CONTROLLED_DEPLOYMENT_PREPARATION|REJECT|REQUEST_REVALIDATION", "rationale": "at least 10 characters" }`.

## Persistence and audit

Migration `0032` adds `control_controlled_policy_validations`, `control_controlled_policy_validation_gate_results`, and `control_controlled_policy_approvals`. Update triggers enforce immutability. The audit trail records `CONTROLLED_POLICY_VALIDATION_CREATED` and `CONTROLLED_POLICY_APPROVAL_RECORDED`, including project, normalized actor, policy version hash, validation/approval hashes, and `physical_effects:false`.

No M7.3 record is a deployable or activated policy. It is only controlled-deployment preparation evidence for a later, separately authorized milestone.
