# Governed deployment authorization and intent (M7.5)

M7.5 records an authenticated human deployment authorization and a separate immutable deployment intent. Neither is deployment, activation, runtime binding, MQTT publication, an outbox command, or hardware control.

## Authorization

An authorization references one complete scoped chain: M7.2 candidate, M7.3 passed validation and preparation approval, M7.4 preparation, and readiness assessment. `AUTHORIZE_CONTROLLED_DEPLOYMENT_INTENT` is permitted only when readiness is `PASSED`. `REJECT_DEPLOYMENT` and `REQUEST_READINESS_REASSESSMENT` preserve a human negative decision without reopening historical readiness.

There is one immutable authoritative authorization per readiness assessment. Its hash canonically binds policy, validation, approval, preparation and readiness hashes; decision; trimmed rationale; OAuth/session-derived authorizer; and authorization policy/schema versions. Body fields cannot provide or override the authorizer.

## Intent

Intent materialization is an explicit second operation. It requires `AUTHORIZE_CONTROLLED_DEPLOYMENT_INTENT` and the still-passed readiness evidence. One immutable `CREATED` intent is allowed per authorization. Its hash binds the policy, preparation, readiness and authorization hashes plus target-asset identity and intent policy/schema versions.

`control_governed_deployment_intents` is intentionally distinct from `control_actuation_delivery_intents` and `control_actuation_outbox`; no M7.5 method reads or writes an operational pipeline.

## API, security and audit

GET uses `view_dashboard`; authorization and intent materialization use the existing least-powerful temporary `edit_policies` capability and audit `rbac_debt:"edit_policies"`. Development fallback is rejected when enabled.

- `POST|GET /api/control/promotion/projects/:projectId/policy-version-candidates/:candidateId/deployment-preparations/:preparationId/readiness-assessments/:assessmentId/authorization`
- `POST|GET /api/control/promotion/projects/:projectId/policy-version-candidates/:candidateId/deployment-preparations/:preparationId/readiness-assessments/:assessmentId/authorization/intent`

Authorization POST accepts only `decision` and bounded `rationale`. Migration `0034` creates immutable authorization and intent evidence, with audit actions `GOVERNED_DEPLOYMENT_AUTHORIZATION_RECORDED` and `GOVERNED_DEPLOYMENT_INTENT_CREATED`; both use `physical_effects:false`.

M7.5 stops at intent evidence. Any real deployment requires a separately authorized execution phase.
