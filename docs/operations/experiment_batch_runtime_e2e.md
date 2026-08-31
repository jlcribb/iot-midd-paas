# Batch runtime E2E (M6.6A)

The replay runner is intentionally private to Docker Compose. `simulation-replay-runner:8010` resolves only from the Compose network, and no host port is published. Running the batch E2E directly from the host therefore causes every item to persist `SIMULATION_REPLAY_RUNNER_UNAVAILABLE` and the batch to end `FAILED`; this is a test-execution-network mismatch, not a candidate, session, trace, evaluation, or ranking defect.

Run the real pipeline from the Topology runtime container:

```bash
docker exec -e M65_E2E_RUNNER=1 -e M65_E2E_REPORT=1 iotmw-topology-ui \
  sh -lc 'npm test -- --run tests/integration/experiment-batch.e2e.test.ts'
```

The integration test creates a proportional three-candidate search space, derives simulation sessions, invokes the real runner, persists results/traces/evaluations, creates a ranking twice, and confirms batch and ranking idempotency. It cleans ephemeral simulation records after completion. The batch boundary now retains the underlying reachability detail and records the stable item code `SIMULATION_REPLAY_RUNNER_UNAVAILABLE` for this configuration error.
