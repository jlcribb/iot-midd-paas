# M5.3 deterministic simulation replay

A READY `control_simulation_sessions` row is an immutable experiment definition.
`control_simulation_runs` records one independent execution of that definition;
it never changes the session or duplicates its snapshots.

The runner reads only the four READY snapshots.  It creates an in-memory policy
source from the frozen policy, advances an immutable `SimulationClock` over the
canonical `(timestamp, event_id)` dataset order, and invokes the same
parametric-control-engine adapter and evaluators used for recommendations.

`control_simulation_run_events` is simulation-only persistence.  It is not an
operational recommendation, delivery intent, outbox event, publisher input, or
transport message.  Every run has `physical_effects_allowed=false` and its
context rejects operational outbox, transport, and physical effects.

The synchronous runner accepts at most 500 frozen records.  A mismatched
control-engine or clock-model version fails closed.  Two runs of the same READY
session are intentionally allowed and must compare only their ordered domain
output, never their IDs or wall-clock timestamps.
