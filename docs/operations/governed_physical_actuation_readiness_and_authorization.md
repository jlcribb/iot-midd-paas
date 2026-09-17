# M7.9 — Governed Physical Actuation Readiness and Authorization

M7.9 starts only from an M7.7 `ACTIVE` runtime binding with a successful activation acknowledgement and factual M7.8 `SHADOW`/`DRY_RUN` evidence. It materializes immutable readiness, an authenticated human decision, and a `GOVERNED_PHYSICAL_ACTUATION_INTENT`. It ends there: the intent is SQL-constrained as `PROPOSED_ONLY`, `non_executable=true`, `actuation_enabled=false`, and `physical_effects=false`.

The runtime target declares the future physical contract in `metadata.physical_actuation`. The contract identifies a same-project active actuator asset, capability and output schema, output bounds, interlocks, emergency stop, an isolated future channel, observability, safe state, and configurable `minimum_completed_shadow_cycles` plus `maximum_shadow_failure_rate`. The M7.9 readiness snapshot hashes that declaration together with active-binding identity, persisted shadow-cycle/output evidence and all sixteen ordered gates. Missing emergency stop, interlocks, safety limits, channel isolation, or any physical-effect boundary violation is blocking; insufficient factual shadow evidence and unavailable observability/channel are failed readiness.

The service never imports or invokes `control_actuation_delivery_intents`, `control_actuation_outbox`, MQTT, RabbitMQ, PLC, edge-agent, GPIO, or hardware adapters. Those tables are inspected only as negative evidence: M7.9 requires zero delivery/outbox records for the governed project and does not insert into either. It also records only audit events `PHYSICAL_ACTUATION_READINESS_CREATED`, `PHYSICAL_ACTUATION_AUTHORIZATION_RECORDED`, and `GOVERNED_ACTUATION_INTENT_CREATED`, all with `physical_effects:false`.

## API

- `POST|GET /api/control/promotion/projects/:projectId/runtime-bindings/:bindingId/physical-actuation-readiness`
- `POST|GET /api/control/promotion/projects/:projectId/physical-actuation-readiness/:readinessId/authorization`
- `POST|GET /api/control/promotion/projects/:projectId/physical-actuation-authorizations/:authorizationId/intents`

Authorization accepts only `AUTHORIZE_PHYSICAL_ACTUATION_INTENT`, `REJECT_PHYSICAL_ACTUATION`, or `REQUEST_ACTUATION_REASSESSMENT`. Its actor always comes from the authenticated OAuth/session context; the body is strict and cannot supply an actor identity. The positive decision is eligible only for `PASSED` readiness. One semantic decision per readiness and one intent per authorization are immutable and idempotent; conflicting retries fail.

`edit_policies` is temporarily used for physical readiness, authorization and intent creation because there is no dedicated physical-actuation capability in the current RBAC model. This is explicit **RBAC debt**: a dedicated, more restrictive physical-actuation authorization capability must precede M7.10. Read-only access requires `view_dashboard`.
