# Runtime reproducibility

The Python services in the canonical Compose stack install dependencies during
`docker compose build`, not during normal service startup. The shared
`infra/containers/Dockerfile.python-runtime` is used by `api`, `ingestor`, the
control worker, the outbox publisher, and both simulated-delivery consumers.
Dashboard and admin use their own preprovisioned Dockerfiles.

## Build and start

From the repository root:

```bash
docker compose -f infra/containers/docker-compose.yaml build
docker compose -f infra/containers/docker-compose.yaml up -d
docker compose -f infra/containers/docker-compose.yaml ps
```

Dependency manifests are copied into the images and validated with `pip check`
at build time. Compose bind-mounts source code and the local configuration for
development, but Python packages remain in the image's site-packages. Rebuild
the affected image after changing a requirements file.

No standard Python service command runs `pip install`, so normal startup does
not need access to a Python package index.

## Readiness and smoke validation

Container state alone is not readiness. The RC3 smoke continues to require the
service process, critical imports, and startup log markers:

```bash
./scripts/smoke_control_engine_end_to_end.sh
```

The smoke uses isolated control queues and preserves the legacy
`control.recommendations`, `control.audit`, and simulated-actuation DLQ queues.
It validates the simulated-only control path; it does not enable physical
actuation.
