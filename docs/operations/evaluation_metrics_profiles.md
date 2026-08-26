# M6.1 Evaluation Metrics and Profiles

M6.1 establishes the versioned vocabulary used by later adaptive-experimentation phases to evaluate **simulation** evidence. It does not execute strategies, score candidates, modify policies, publish to an operational outbox, or enable any physical effect.

`control_evaluation_metrics` is a global, versioned catalog. The initial catalog includes tracking error, settling time, overshoot, undershoot, control effort, energy cost, actuation count, constraint violations, stability score, response time and resource consumption. A metric declares its direction and a normalization method; M6.2 supplies the deterministic calculation.

`control_evaluation_profiles` is project-scoped and immutable. Creating a profile with an existing code creates the next version; it never edits the earlier definition. Its metric weights must be positive, use unique active weightable metrics and sum exactly to `1`.

The governed API is:

```text
GET  /api/control/evaluation/metrics
GET  /api/control/evaluation/projects/{projectId}/profiles
POST /api/control/evaluation/projects/{projectId}/profiles
```

Metric reads require an authenticated control actor with dashboard visibility. Profile reads require project dashboard visibility; creation requires `edit_policies` in the same project. Creation writes a compact audit record marked `execution_context=SIMULATION` and `physical_effects=false`.

M6.1 has no route to operational policy mutation, delivery intent, transactional outbox, publisher, transport, MQTT or physical actuation. `REAL_ACTUATION_READY=NO` and `PHYSICAL_EFFECTS=false` remain unchanged.
