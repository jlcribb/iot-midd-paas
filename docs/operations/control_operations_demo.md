# Control Operations governed demo

This is a **DEVELOPMENT / DEMONSTRATION ONLY** fixture for M4.4. It is not a production seed, does not create OAuth credentials, and does not enable `CONTROL_RBAC_ALLOW_DEV_FALLBACK`.

The harness uses one marked, deterministic project. It grants only `viewer` to `jl.infodata@gmail.com` for that project, creates no membership for any unrelated project, and removes only that marked project's records during cleanup.

Run the commands from the repository root with the canonical Docker Compose stack already healthy:

```bash
docker compose -f infra/containers/docker-compose.yaml exec api \
  bash -lc 'PYTHONPATH=/app/src:/app/apps/parametric-control-engine/src python /app/scripts/control_operations_demo.py prepare'
docker compose -f infra/containers/docker-compose.yaml exec api \
  bash -lc 'PYTHONPATH=/app/src:/app/apps/parametric-control-engine/src python /app/scripts/control_operations_demo.py verify'
```

`prepare` is idempotent: it first removes only the marked fixture and then recreates a project with the same scoped membership, three policies, one valid binding, two persisted canonical recommendations, and one fully simulated acknowledged delivery. Recommendation and audit publications use `control.recommendations.demo.v1` and `control.audit.demo.v1`; telemetry and legacy consumer queues are never consumed by the harness.

The demo shows:

- a healthy enabled policy with a valid simulated binding;
- an enabled recommendation-only policy with no binding;
- an enabled policy evaluated into a recommendation, outbox event, simulated command, and `acknowledged` delivery;
- a disabled policy;
- an intentionally empty attention list. No synthetic failure, retry, or dead-letter state is fabricated.

For real visual confirmation, start the Next.js app with `CONTROL_RBAC_ALLOW_DEV_FALLBACK=false`, authenticate through the configured OAuth provider as `jl.infodata@gmail.com`, then open `/control` and select **Control Operations Demo — DEVELOPMENT ONLY**. Inspect the policy states, recommendation list, acknowledged delivery, and empty attention panel.

Cleanup is required as soon as the visual check is complete:

```bash
docker compose -f infra/containers/docker-compose.yaml exec api \
  bash -lc 'PYTHONPATH=/app/src:/app/apps/parametric-control-engine/src python /app/scripts/control_operations_demo.py cleanup'
```

The cleanup command refuses to delete an existing project unless its metadata contains the exact demo namespace marker. It also purges only `control.recommendations.demo.v1` and `control.audit.demo.v1`; it never consumes or purges legacy control queues.
