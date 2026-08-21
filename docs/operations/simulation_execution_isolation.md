# M5.1 Simulation execution isolation

M5.1 introduces a foundation for future experiments without adding replay,
synthetic scenarios, a workbench, or a second control implementation.

## Shared semantics, explicit contexts

`parametric-control-engine` remains the source of policy evaluation and
recommendation semantics.  `ExecutionContext` declares whether those semantics
are being used in `LIVE` or `SIMULATION`:

| Concern | LIVE | SIMULATION |
| --- | --- | --- |
| Clock | `SystemClock` | session-scoped `SimulationClock` seed |
| Persistence namespace | operational | `simulation:{session_id}` |
| Event/observability namespace | `control` | `simulation` |
| Correlation namespace | `control` | `simulation:{session_id}` |
| Topology/policy source | live/active | snapshot slots, not yet materialized |
| Physical effects | always false | always false |
| Operational outbox/transport | allowed only by LIVE | denied structurally |

`SIMULATION` is not the M4 simulated dispatch consumer.  M4 simulated dispatch
is part of the operational live pipeline and continues to use the transactional
outbox and its at-least-once publisher.  M5 simulation is an experimental
environment that never receives access to those components.

## Side-effect boundary

Operational outbox insertion and the RabbitMQ publisher require an explicit
`ExecutionContext`.  A simulation context raises
`OperationalSideEffectForbidden` before any operational outbox SQL is executed
and before a publisher can be constructed.  This is tested as a negative
integration proof.  Future simulation output must use a simulation-only adapter
and persistence namespace; it must not add a conditional branch to the live
outbox or publisher.

All existing live delivery payloads remain simulated-only and retain
`physical_effects=false`.  M5.1 introduces no physical adapter, device
transport, MQTT command publication, hardware readiness, or automatic
actuation.

## SimulationSession

`public.control_simulation_sessions` is separate from operational delivery,
outbox, and audit tables.  Each row is project-scoped, has a mandatory
`SIMULATION` execution context, basic lifecycle, creator and timestamps.
`snapshot_refs` and `metadata` remain DRAFT annotations. M5.2 adds the
immutable `DRAFT -> READY` preparation boundary, materialized snapshots and a
reproducible fingerprint; see `simulation_experiment_snapshots.md`.

The minimal API is project-scoped and RBAC-protected:

```text
POST /api/control/simulations/projects/{projectId}/sessions
GET  /api/control/simulations/projects/{projectId}/sessions
GET  /api/control/simulations/projects/{projectId}/sessions/{sessionId}
```

Creation requires the existing `edit_policies` permission; reads require
`view_dashboard`. OAuth memberships remain fail-closed and
`CONTROL_RBAC_ALLOW_DEV_FALLBACK=false` remains required for governed runtime.

M5.1 did not write these records into the live worker/outbox audit stream or
its operational metrics namespace. M5.2 adds only the transactional
`SIMULATION_SESSION_PREPARED` record, still without an operational delivery
event. A future simulation event stream may add
`SIMULATION_SESSION_CREATED`, `STARTED`, `COMPLETED`, `FAILED`, and `CANCELLED`
inside the simulation namespace; M5.1 intentionally does not fabricate those
lifecycle events before it implements their transitions.

## M5.1 boundary

M5.1 does not implement `/run`, replay, comparison, fault injection, snapshot
fingerprinting, lifecycle transitions, a simulation UI, or any simulation
transport.  Those capabilities require a later design phase after immutable
snapshot and dataset semantics are defined.
