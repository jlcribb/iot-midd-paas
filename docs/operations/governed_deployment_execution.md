# Governed deployment execution (M7.6)

M7.6 is the governed bridge from an immutable M7.5 `GovernedDeploymentIntent` to a non-active staged policy artifact. It stops at execution evidence: `DEPLOYED` here means **staged at the logical deployment boundary**, never active, runtime-bound, actuating, or physical.

## Authority and eligibility

M7.5 materialization is already the explicit human authorization boundary for this execution. M7.6 therefore does not add a second implied human decision; the authenticated OAuth/session actor initiates execution with `edit_policies` and is written to audit evidence. Development RBAC fallback is rejected.

Before dispatch, the execution repository locks and verifies the same project-scoped immutable chain: candidate, passed validation, M7.3 approval, preparation, passed readiness, positive M7.5 authorization, and `CREATED` intent. It also verifies the preparation target equals the intent target, checks the exclusive target slot, uses a `DATABASE_STAGING` channel, defines rollback semantics, and has no activation, binding, MQTT, or physical-actuation path.

The deterministic execution identity binds intent hash, policy-version hash, target asset, staging channel, policy, engine, and schema versions. `UNIQUE(governed_deployment_intent_id)` and the intent row lock make same-intent retries converge to one authoritative execution. An additional partial unique index blocks concurrent work in the same target slot.

## Delivery and lifecycle

The pre-existing `control_actuation_delivery_intents` / `control_actuation_outbox` pipeline remains excluded: it is recommendation/actuation-specific and therefore cannot be safely repurposed for a policy artifact. M7.6 stores a separate `control_governed_deployment_staged_artifacts` row in the same PostgreSQL transaction as execution evidence. No RabbitMQ or MQTT message is emitted.

The allowed state machine is `PENDING → RUNNING → SUCCEEDED | FAILED | BLOCKED`; a partial staging failure follows `FAILED → ROLLBACK_PENDING → ROLLED_BACK | ROLLBACK_FAILED`. SQL triggers reject identity changes, illegal transitions, terminal rewrites, and attempt/result rewrites. Attempts are append-only and result hashes bind semantic attempt, delivery, and rollback evidence.

`control_deployment.delivery_mode` on a simulation target supports only test fixture behavior: the default stages successfully; `FAIL_BEFORE_STAGE` yields `FAILED` with `NOT_REQUIRED` rollback; `STAGE_THEN_FAIL` marks the staged artifact `ROLLED_BACK` and produces `ROLLED_BACK` / `SUCCEEDED` rollback evidence. This declaration is not a public request parameter and never selects a physical transport.

## API and audit

- `POST|GET /api/control/promotion/projects/:projectId/policy-version-candidates/:candidateId/deployment-intents/:intentId/executions`
- `GET /api/control/promotion/projects/:projectId/policy-version-candidates/:candidateId/deployment-intents/:intentId/executions/:executionId`

POST accepts no actor, target, activation, delivery-mode, or transport fields. GET requires `view_dashboard`; POST uses temporary `edit_policies` with explicit `rbac_debt:"edit_policies"` until a narrower capability exists.

Audit actions are `GOVERNED_DEPLOYMENT_EXECUTION_CREATED`, `..._STARTED`, `..._SUCCEEDED`, `..._FAILED`, `GOVERNED_DEPLOYMENT_ROLLBACK_STARTED`, and `..._ROLLBACK_COMPLETED` when applicable. All record `execution_context:"SIMULATION"` and `physical_effects:false`.

The M7.6 E2E proves one successful staged delivery and one simulated partial failure with logical rollback, while active policies, runtime bindings, operational actuation delivery/outbox, MQTT, hardware, actuator state, and physical effects remain unchanged/absent.
