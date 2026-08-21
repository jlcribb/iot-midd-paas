# M5.2 — Experiment snapshots and reproducible identity

M5.2 prepares an isolated `control_simulation_sessions` record for a future experiment. It does **not** execute, replay, publish or actuate anything.

## Boundary

The only enabled lifecycle transition is `DRAFT -> READY`. A READY session is immutable at database level. `RUNNING`, replay, comparison, fault injection, operational outbox, RabbitMQ transport and physical effects remain outside this phase.

The preparation endpoint is `POST /api/control/simulations/projects/{projectId}/sessions/{sessionId}/prepare`.

It requires an authenticated, project-scoped actor with `edit_policies`. There is no development-role fallback. Reads remain project scoped and use the existing session GET endpoints.

## Materialized inputs

Inside one PostgreSQL transaction the service locks the DRAFT session, reads the selected policy in the same project and captures these independent JSON documents:

| Snapshot | Content |
| --- | --- |
| Policy | ID, project, variable, selector, parameters, priority, enabled flag and version |
| Topology | Source asset identity/state/metadata and, where configured, target asset plus binding ID, version, control point and operation |
| Dataset | Materialized historical or synthetic telemetry records, source kind and explicit `timestamp_ascending_event_id` ordering |
| Configuration | Schema, engine and clock version, virtual start time, trace option, seed and disabled-side-effect declaration |

Every telemetry record must carry the session project ID and the selected policy variable. Cross-project records and duplicate event IDs are rejected before any database preparation operation. `historical` means an already materialized, project-scoped historical set; M5.2 intentionally adds no live telemetry query or replay mechanism.

## Canonical identity

Objects are serialized with lexicographically sorted keys, `undefined` fields omitted, null preserved, finite numbers only and timestamps normalized to UTC ISO-8601. Dataset order is made explicit by `(timestamp, event_id)`. SHA-256 lowercase-hex hashes are persisted for each component. The experiment fingerprint is SHA-256 over schema version and those four component hashes.

This gives equal snapshots equal hashes/fingerprint, while a relevant policy, topology, dataset or configuration change yields a different component hash and therefore a different fingerprint. The stored JSON is a detached canonical copy, not a reference to mutable policy, topology or dataset state.

## Storage and atomicity

Migration `0017` adds the four snapshots, hashes, fingerprint, schema version and `prepared_at` to `public.control_simulation_sessions`, plus indexes for project/status and fingerprint lookup. The READY completeness constraint rejects partial materializations. The lifecycle trigger rejects every READY update and all transitions except `DRAFT -> READY`.

The same SQL transaction performs: session `FOR UPDATE`, policy read `FOR SHARE`, snapshot/hash construction, READY update and the `SIMULATION_SESSION_PREPARED` audit record. A concurrent caller serializes on the session lock; once one caller succeeds, later callers receive the persisted READY record without rebuilding from live state.

## Safety and observability

The configuration snapshot records `execution_context=SIMULATION` and `outbox=false`, `transport=false`, `physical_effects=false`. It has no relation to `control_actuation_outbox`, RabbitMQ publisher, delivery intents or adapters. The audit record includes only project/session identity, actor, schema version, fingerprint and component hashes; it does not duplicate the materialized dataset or store credentials.

M5.3 may consume a READY snapshot through a simulation-only evaluator adapter, but must not change this immutable identity or bridge it into the operational delivery path.
