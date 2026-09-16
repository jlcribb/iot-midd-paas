# M7.8 — Governed Shadow Control-Loop Enablement

M7.8 begins only from an M7.7 `ACTIVE` runtime binding with a successful activation and matching runtime acknowledgement. It never changes that binding: `control_loop_enabled` and `actuation_enabled` remain SQL-constrained to `false`.

The persisted chain is `binding → immutable readiness → OAuth/session-derived human authorization → bounded SHADOW or DRY_RUN session → immutable cycles → immutable shadow outputs`. Readiness evaluates twelve blocking gates: active binding/provenance, policy hash, declared simulation inputs, evaluator, output schema, limits, explicit shadow mode, disabled actuation, observability and stop path. The target declares those capabilities in `metadata.control_runtime.control_loop`.

Sessions are bounded by `max_cycles` (1–100) and have a partial unique index for one `RUNNING` session per project/target/strategy slot. Each cycle delegates calculation to the private Python simulation runner, which invokes the canonical `parametric-control-engine` evaluators in a non-actuating context; Next only governs and persists the returned evidence. The cycle saves the immutable input snapshot and hash, policy hash, raw and bounded output, constraints and a `SHADOW` output hash. A missing required input records a failed cycle and terminates the session; it is never converted to a zero output. A governed stop transitions `RUNNING → STOPPING → STOPPED` before any new cycle can be created.

The control-evaluation persistence plane is structurally separate from `control_actuation_delivery_intents`, `control_actuation_outbox`, RabbitMQ and MQTT. All M7.8 records and audit events enforce `physical_effects=false` and `actuation_enabled=false`; shadow outputs are not actuator commands.

## API

- `POST|GET /api/control/promotion/projects/:projectId/runtime-bindings/:bindingId/control-loop-readiness`
- `POST|GET /api/control/promotion/projects/:projectId/control-loop-readiness/:readinessId/authorization`
- `POST|GET /api/control/promotion/projects/:projectId/control-loop-authorizations/:authorizationId/sessions`
- `GET /.../sessions/:sessionId`, `POST /.../sessions/:sessionId/stop`
- `GET /.../sessions/:sessionId/cycles`, `GET /.../sessions/:sessionId/outputs`

Mutating calls use the authenticated actor with `edit_policies`; reads use `view_dashboard`. Development RBAC fallback is rejected. The M6→M7.8 Docker E2E verifies deterministic three-cycle evidence, a stopped running session, controlled missing-input failure, SQL immutability, and unchanged operational delivery/outbox state.
