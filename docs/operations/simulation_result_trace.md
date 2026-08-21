# M5.4 Simulation Result and Trace

`SimulationResult` is created atomically when a `SimulationRun` reaches
`COMPLETED`. It is not a new experiment and contains no snapshot or live control
state. Its `result_fingerprint` is SHA-256 over schema version, the immutable
`experiment_fingerprint`, and the canonical ordered output evidence only.

Run IDs, actor identity and wall-clock timestamps are excluded. Two runs with
equivalent deterministic outputs therefore have the same fingerprint.

`control_simulation_run_events` remains the sole trace source. Result and trace
reads are project-scoped, ordered by `sequence`, paginated (`limit` 1..500,
`offset` >= 0), and never invoke the evaluator or query live policy/topology.
Completed runs have one result; failed runs intentionally have none.

The result table rejects UPDATEs through a PostgreSQL trigger. Simulation result
and trace never access the operational outbox, publisher, transport, MQTT or
RabbitMQ, and declare no physical effects.
