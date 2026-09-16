# Governed policy activation and runtime binding (M7.7)

M7.7 starts only from a successful M7.6 execution with a `STAGED` artifact. It adds immutable activation-readiness and human authorization evidence, then atomically creates a `control_runtime_policy_bindings` `ACTIVE` record. This registry is deliberately separate from operational control policies and actuation bindings.

Activation readiness has twelve ordered blocking gates for execution/artifact identity, target/runtime availability and compatibility, exclusive slot, rollback snapshot, binding path and the mandatory disabled control-loop/actuation state. The target declares a non-actuating `DATABASE_RUNTIME_REGISTRY` path. `control_loop_enabled` and `actuation_enabled` are SQL-constrained to `false` on both binding and acknowledgement.

The activation authorization is a separate OAuth/session-derived human decision. Only `AUTHORIZE_POLICY_ACTIVATION` from passed readiness can activate; negative decisions preserve history. The switch is transactional: the prior `ACTIVE` binding is superseded, the new binding becomes active under a partial unique slot index, then a runtime-registry acknowledgement validates target, policy hash and both disabled flags. An invalid acknowledgement rolls the new binding back and restores the prior one. No outbox, RabbitMQ or MQTT path is used.

## Closure evidence

The Docker/PostgreSQL M7.7 E2E covers initial activation, A→B switch-over, and an invalid ACK for a later replacement. It proves A is `SUPERSEDED` while B is the sole `ACTIVE` binding after a valid ACK. For the invalid-ACK case, the attempted replacement is terminal `ROLLED_BACK` with rollback `SUCCEEDED`; the pre-existing B binding is restored as `ACTIVE` with its original policy hash, slot, project, target, and strategy. SQL immutability rejects terminal activation and ACK rewrites. Every observed binding and ACK retains `control_loop_enabled:false`, `actuation_enabled:false`, and `physical_effects:false`; operational actuation delivery/outbox, MQTT commands, and hardware remain unchanged.
