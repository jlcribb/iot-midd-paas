# Changelog

## control-engine-mvp-rc1

Estado:

```text
Release Candidate interno
```

### Alcance consolidado

- Fase 1: integración runtime + RabbitMQ + auditoría + feature flag
- Fase 2: policies PostgreSQL por proyecto
- Fase 3: observabilidad read-only
- Fase 4: dashboard mínimo `/control`
- Fase 5: benchmark operativo reproducible
- Fase 6: paquete demostrable y documental

### Cambios funcionales principales

- `control_engine_worker` consume eventos reales y delega evaluación al `parametric-control-engine`
- las recommendations y audits quedan publicadas y auditadas
- el feature flag por proyecto bloquea ejecución con `skipped` auditable
- la selección de policy usa PostgreSQL por `project_id + variable + context`
- Next.js expone endpoints read-only y dashboard mínimo para control
- el benchmark operativo exporta resultados reproducibles a `docs/benchmark`

### Resultados actuales destacados

- `policy_driven` menor error medio absoluto agregado: `5.469`
- `proportional` menor esfuerzo total agregado: `80.31`
- `disabled`: `0` recommendations + `3` skipped audits

### Decisiones de producto/arquitectura

- runtime oficial local: `Docker Desktop`
- `Podman`: deprecated
- no IA en este MVP
- no acciones automáticas en este MVP

### Deuda técnica conocida

- `postgis/postgis:16-3.4` corre como `linux/amd64` sobre host `arm64`
- el smoke RabbitMQ puede requerir permisos elevados en entornos restringidos
- fallback in-memory permitido solo para debug/smoke

### Referencias

- [RC1 release note](docs/releases/control_engine_mvp_rc1.md)
- [Demo guide](docs/demo/control_engine_demo_guide.md)
- [Operational benchmark](docs/benchmark/operational_control_benchmark.md)
