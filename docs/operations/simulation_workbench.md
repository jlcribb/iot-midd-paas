# Simulation Workbench (M5.5)

`/control/simulations` is an authenticated, project-scoped viewer and launcher
for the persisted M5 simulation model. It is not an operational control panel.

## Boundary

- It creates a `DRAFT` through the governed session API.
- It sends materialized telemetry records to the existing prepare contract.
  The server validates, orders, snapshots, hashes, and fingerprints them.
- A `READY` experiment is rendered as immutable evidence and can create many
  independent replay runs.
- Result and trace values are read from the M5.4 persisted result/trace APIs.
- No action in the UI can access an outbox, publisher, transport, hardware, or
  a physical-effect path.

The only reproducibility indicator compares opaque server-materialized result
fingerprint strings for completed runs of one session. It does not replay,
diff events, or infer recommendation/actionability/result semantics.

## Roles and scope

The server page requires the existing OAuth-backed control actor. Every API
request remains authorized by existing control RBAC and project membership.
The UI may hide mutation controls for globally read-only access, but it never
implements a separate authorization matrix; the API is authoritative. A
read-only user can inspect sessions, runs, results, and traces that are in
their project scope.

## Operational notes

The selected `project`, `session`, and `run` are retained in the workbench URL
when valid for the authenticated scope. Trace data uses the backend's
`limit`/`offset` pagination. A failed or cancelled run deliberately shows no
invented result. A missing result for an incomplete run remains "not
materialized" rather than being synthesized by the client.

The run list is a read model from the isolated replay runner. Its optional
`result_fingerprint` is evidence already persisted in
`control_simulation_results`; it is not recomputed in Next.js.
