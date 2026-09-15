# M7.2A / M7.3 / M7.4 / M7.5 — Controlled Policy Evidence E2E

The replay runner is intentionally internal to Docker (`simulation-replay-runner:8010`). Do not execute runner-backed M6/M7.1/M7.2 E2E tests from the host: the host cannot resolve that Docker service name and the batch will fail before promotion evidence exists.

Run the canonical M7.2 E2E from an ephemeral container on `containers_default` with the canonical checkout mounted at `/app`:

```sh
docker run --rm --network containers_default \
  -e DB_HOST=postgresql -e DB_PORT=5432 -e DB_NAME=iot_middleware \
  -e DB_USER=iot_user -e DB_PASSWORD=iot_password_2024 \
  -e SIMULATION_REPLAY_RUNNER_URL=http://simulation-replay-runner:8010 \
  -e M72_E2E_RUNNER=1 -e M72_E2E_REPORT=1 \
  -v /Users/joseluis/dev/iot-midd-paas-auth-work:/app \
  -w /app/apps/topology-next node:20-alpine \
  sh -lc 'npm test -- tests/integration/controlled-policy-version.e2e.test.ts'
```

The isolated test creates four real M6→M7.1 chains, materializes controlled candidates v1–v4, performs M7.3 validation and approval on v1, creates an explicit simulation `programmable_node` target with declared readiness capabilities, and records M7.5 human authorization plus a separate governed intent. It checks replay idempotency, conflicting second authorization denial, immutable evidence, M7.5 audit events, and before/after equality for active policies, runtime bindings, delivery intents, and outbox. Its dedicated project is removed in `finally`, so it neither changes active policies nor leaves shared fixture references.

The M6/M7.1 regression remains:

```sh
docker exec -e M65_E2E_RUNNER=1 -e M65_E2E_REPORT=1 iotmw-topology-ui \
  sh -lc 'cd /app/apps/topology-next && npm test -- tests/integration/experiment-batch.e2e.test.ts'
```
