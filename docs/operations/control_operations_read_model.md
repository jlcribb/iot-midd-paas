# Control Operations Read Model (M4.2)

## Purpose and boundary

M4.2 adds a typed, project-scoped, read-only operational view for parametric control. It is a backend contract for a future UI; it does not add M4.3 screens, write paths, queue consumers, policy semantics, or migrations.

The routes are protected by the existing control session/RBAC path and authorize `view_dashboard` for the requested project before issuing read-model queries. The read model is limited to the project identifier in every source query; it does not expose arbitrary audit, delivery, outbox, or project tables.

## Source-of-truth map

| Operational concern | Source of truth | Notes |
| --- | --- | --- |
| Project mode | `public.projects.parametric_control_enabled` | `false` produces `INACTIVE`; `true` is `SIMULATED`, never real-device actuation. |
| Policy configuration | `public.project_control_policies` | Includes enabled state and bound source asset. |
| Actuation binding | `public.project_control_policy_actuation_bindings` + scoped `public.assets` | Validity is derived from enabled binding, target eligibility, and `metadata.control_capabilities`. |
| Recommendation timeline | `iot_schema.auditoria` for `control_engine_worker` / `CONTROL_RECOMMENDATION_EMITTED` | Historical rows can omit `recommendation_id`; those values remain `null` rather than fabricated. |
| Delivery lifecycle | `public.control_actuation_delivery_intents` | Intent status, retry count, expiry and last error. |
| Publication lifecycle | newest matching `public.control_actuation_outbox` event by project and command | This is a bounded read-only join, not a retry/reset operation. |
| Acknowledgement | delivery intent status `acknowledged` | No separate acknowledgement table is invented. |
| Dead-letter queue | RabbitMQ queue only | There is no persistent per-project dead-letter record, so the API deliberately does **not** assert `DEAD_LETTERED` for an item. A final failed intent remains `FAILED`. |

## API contract

All routes return the existing success/error envelope. `projectId` is a UUID path parameter and must be authorized for the authenticated actor.

| Route | Read model |
| --- | --- |
| `GET /api/control/operations/projects/{projectId}/summary` | Project mode, policy/binding/recommendation/delivery/attention counts and last activity. |
| `GET /api/control/operations/projects/{projectId}/policies` | Effective policy status, configured state, binding state and actionability. |
| `GET /api/control/operations/projects/{projectId}/bindings` | Binding target, advertised capabilities, validity and reason. |
| `GET /api/control/operations/projects/{projectId}/recommendations` | Audited recommendation events and a same-project delivery link where present. |
| `GET /api/control/operations/projects/{projectId}/deliveries` | Delivery intent, latest outbox result and acknowledgement projection. |
| `GET /api/control/operations/projects/{projectId}/attention` | Invalid binding, retrying/final/expired delivery and failed outbox indicators. |

All collection routes support `limit` and `offset`. `recommendations` additionally supports `policyId` and `correlationId`; `deliveries` supports `status`, `recommendationId`, `commandId`, and `correlationId`. Pagination is deterministic (`variable,priority,version,id` for policies/bindings; `ts,id DESC` for recommendations; `created_at,id DESC` for deliveries), defaults to `limit=25, offset=0`, and has a hard maximum of 100. Empty optional parameters are ignored. Invalid non-numeric, non-integer, negative, zero, or over-limit pagination values return a validation error.

The projection exposes only actual stable identifiers. A recommendation links to a delivery by `recommendation_id`; for legacy audit entries which lack that identifier it may link by same-project `correlation_id`. It never reconstructs an ID from content.

## State normalization

| Derived state | Meaning |
| --- | --- |
| `HEALTHY` | Enabled project/policy with a valid actionable binding. |
| `INACTIVE` | Project control disabled or policy disabled. |
| `RECOMMENDATION_ONLY` | Enabled policy with no actuation binding. |
| `MISCONFIGURED` | Binding disabled, target unavailable/ineligible, disallowed non-programmable self-target, or target lacks declared control-point/operation capability. |
| `PENDING` | Received/validated/ready/dispatched intent or pending/publishing outbox event. |
| `PUBLISHED` | Latest matching outbox event was published. |
| `ACKNOWLEDGED` | Delivery intent was acknowledged. |
| `RETRYING` | Delivery intent is retry pending. |
| `FAILED` | Rejected/failed-final intent or failed outbox event. |
| `EXPIRED` | Delivery intent expired. |

`DEAD_LETTERED` is intentionally not represented as an item state: M4.2 has no durable per-project evidence for it. The platform should show queue-level DLQ evidence only when a future auditable persistence model exists.

## Boundaries and operational safety

This capability is simulated-only, additive and read-only. It performs no direct device execution, no queue reset/retry/purge, no policy mutation, and no feature-flag mutation. The existing runtime and M4.1 container baseline are unchanged. Status is a projection of persisted/audited events at query time, not a new workflow authority.

## Verification

From `apps/topology-next`:

```bash
npm run typecheck
npm test -- --run tests/unit/control-operations.service.test.ts
```

The unit suite covers derived policy/binding status, project-disabled behavior, bounded pagination, same-project recommendation-to-delivery correlation, delivery/attention normalization, and rejection of cross-project access before repository queries.
