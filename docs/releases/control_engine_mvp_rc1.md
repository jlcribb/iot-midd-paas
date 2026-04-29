# Control Engine MVP RC1

## Estado

Baseline interna demostrable del MVP de control paramétrico.

Clasificación:

```text
Release Candidate interno
```

Versión documental:

```text
control-engine-mvp-rc1
```

## Objetivo de esta release

Congelar el estado actual del MVP como referencia estable para:

- demo técnica;
- jurado o dirección;
- paper o memoria;
- punto de partida de la siguiente etapa.

## Fases completadas

### Fase 1

- integración runtime no invasiva;
- RabbitMQ real;
- auditoría persistente;
- feature flag por proyecto.

### Fase 2

- policies PostgreSQL por proyecto;
- selección por contexto, prioridad y versión.

### Fase 3

- endpoints read-only de observabilidad:
  - `/api/control/status`
  - `/api/control/recommendations`
  - `/api/control/audit`

### Fase 4

- dashboard mínimo read-only en `/control`.

### Fase 5

- benchmark operativo reproducible;
- exportación de artefactos técnicos en `docs/benchmark`.

### Fase 6

- paquete demostrable;
- guía de demo técnica;
- resumen ejecutivo.

## Decisiones explícitas de la release

- runtime oficial local: `Docker Desktop`
- comando canónico de contenedores: `docker compose`
- `Podman`: deprecated / histórico
- IA: fuera de alcance en este MVP
- acciones automáticas: fuera de alcance en este MVP
- toda lógica de control permanece en `apps/parametric-control-engine`

## Validación oficial de RC1

### Infra

```bash
docker compose -f infra/containers/docker-compose.yaml up -d
docker compose -f infra/containers/docker-compose.yaml ps
```

### Runtime de control

```bash
./scripts/smoke_control_engine_rabbitmq.sh
./scripts/smoke_core.sh
```

### Benchmark

```bash
PYTHONPATH=src ./venv/bin/python scripts/export_operational_control_benchmark.py
```

### Tests del engine

```bash
PYTHONPATH=apps/parametric-control-engine/src ./venv/bin/pytest apps/parametric-control-engine/tests -q
```

### Dominio operacional

```bash
cd apps/topology-next
npm test
npm run typecheck
npm run dev
```

## Resultado actual del benchmark

Baseline vigente tomada de [operational_control_benchmark.md](../benchmark/operational_control_benchmark.md):

- `policy_driven` menor error medio absoluto agregado: `5.469`
- `proportional` menor esfuerzo total agregado: `80.31`
- `threshold` y `policy_driven` menor cantidad agregada de acciones: `15`
- modo `disabled`: `0` recommendations + `3` skipped audits

## Checklist de release

- [x] control engine integrado a runtime real
- [x] RabbitMQ operativo
- [x] auditoría persistente
- [x] feature flag por proyecto
- [x] policies persistentes por proyecto
- [x] observabilidad read-only
- [x] dashboard `/control`
- [x] benchmark operativo reproducible
- [x] documentación de demo
- [x] decisiones de runtime explicitadas

## Deuda técnica conocida

### Compatibilidad de contenedores

- `postgis/postgis:16-3.4` corre como `linux/amd64` sobre host `arm64`
- funciona en el entorno actual, pero conviene monitorear performance y evaluar imagen multiarch/arm64 más adelante

### Ejecución del smoke RabbitMQ

- `./scripts/smoke_control_engine_rabbitmq.sh` puede requerir permisos elevados en algunos entornos sandbox o runners restringidos para abrir sockets locales

### Fallback de policy source

- `InMemoryPolicySource` queda permitido solo para debug y smoke
- no es camino productivo ni debe usarse como runtime oficial

## Comandos canónicos consolidados

### Stack local

```bash
docker compose -f infra/containers/docker-compose.yaml up -d
docker compose -f infra/containers/docker-compose.yaml logs -f
docker compose -f infra/containers/docker-compose.yaml down
```

### Validación funcional

```bash
./scripts/smoke_control_engine_rabbitmq.sh
./scripts/smoke_core.sh
```

### Benchmark

```bash
PYTHONPATH=src ./venv/bin/python scripts/export_operational_control_benchmark.py
```

### Dashboard y observabilidad

- [http://localhost:3000/control](http://localhost:3000/control)
- [http://localhost:3000/api/control/status](http://localhost:3000/api/control/status)
- [http://localhost:3000/api/control/recommendations](http://localhost:3000/api/control/recommendations)
- [http://localhost:3000/api/control/audit](http://localhost:3000/api/control/audit)

## Próximos incrementos recomendados

### 1. Editor de policies

- gestión operacional de `project_control_policies`
- fuera de este RC

### 2. Cognitive Core

- capa de análisis superior sobre el control paramétrico
- sin romper el flujo canónico

### 3. IA opcional

- solo posterior a contracts, auditoría y governance más fuertes
- explícitamente fuera de este MVP RC1

## Documentos relacionados

- [CHANGELOG.md](../../CHANGELOG.md)
- [control_engine_demo_guide.md](../demo/control_engine_demo_guide.md)
- [control_engine_executive_summary.md](../demo/control_engine_executive_summary.md)
- [control_engine_worker.md](../operations/control_engine_worker.md)
- [control_dashboard.md](../operations/control_dashboard.md)
- [operational_control_benchmark.md](../benchmark/operational_control_benchmark.md)
- [CONTROL_SYSTEM_SPEC.md](../architecture/CONTROL_SYSTEM_SPEC.md)
