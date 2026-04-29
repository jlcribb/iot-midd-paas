# Control Engine Demo Guide

## Objetivo

Demostrar el MVP end-to-end del control paramétrico de Midd IOT con evidencia operativa y reproducible.

Este paquete cubre:

- runtime Docker;
- RabbitMQ real;
- `control_engine_worker`;
- policies PostgreSQL por proyecto;
- recommendation + audit;
- observabilidad read-only;
- dashboard `/control`;
- benchmark operativo reproducible.

## Flujo canónico de la demo

```text
Docker stack
→ RabbitMQ
→ control_engine_worker
→ PostgreSQLPolicySource
→ Recommendation
→ Audit
→ /api/control/*
→ /control
→ benchmark operativo
```

Flujo de control que se demuestra:

```text
Telemetry Event
→ ControlEvaluationRequest
→ Policy Selection
→ Evaluation
→ Recommendation
→ Publishable Envelope
→ Audit Envelope
```

## Precondiciones

- Docker Desktop operativo.
- Repo abierto en la raíz del workspace.
- Dependencias Python ya disponibles en `./venv`.
- `apps/topology-next` con dependencias instalables por `npm`.

## Comandos exactos

### 1. Levantar stack base

Desde la raíz del repo:

```bash
docker compose -f infra/containers/docker-compose.yaml up -d
```

### 2. Verificar stack

```bash
docker compose -f infra/containers/docker-compose.yaml ps
```

### 3. Ejecutar smoke real del worker contra RabbitMQ

```bash
./scripts/smoke_control_engine_rabbitmq.sh
```

Ese smoke demuestra dos ramas:

- proyecto `disabled` → no recommendation, audit `skipped`;
- proyecto `enabled` → recommendation + audit.

### 4. Exportar benchmark operativo

```bash
PYTHONPATH=src ./venv/bin/python scripts/export_operational_control_benchmark.py
```

Artefactos generados:

- [operational_control_benchmark.md](../benchmark/operational_control_benchmark.md)
- [operational_control_benchmark.json](../benchmark/operational_control_benchmark.json)

### 5. Levantar frontend operacional en modo local

Desde `apps/topology-next`:

```bash
npm run dev
```

Nota:

- el stack Docker ya expone `topology-ui` en `localhost:3000`;
- `npm run dev` es útil si se quiere demostrar el dominio operacional fuera del contenedor o con recarga local.

## URLs locales relevantes

### Dashboard

- [http://localhost:3000/control](http://localhost:3000/control)

### Endpoints read-only

- [http://localhost:3000/api/control/status](http://localhost:3000/api/control/status)
- [http://localhost:3000/api/control/recommendations](http://localhost:3000/api/control/recommendations)
- [http://localhost:3000/api/control/audit](http://localhost:3000/api/control/audit)

### Infra útil durante la demo

- RabbitMQ management: [http://localhost:15672](http://localhost:15672)
- API Python legacy/transición: [http://localhost:8000](http://localhost:8000)

## Secuencia sugerida para demo

### Paso 1. Infra

Mostrar que el stack responde con Docker:

```bash
docker compose -f infra/containers/docker-compose.yaml ps
```

Mensaje esperado:

- `postgresql` healthy;
- `rabbitmq` up;
- `topology-ui` up;
- servicios principales levantados.

### Paso 2. Runtime real del control

Ejecutar:

```bash
./scripts/smoke_control_engine_rabbitmq.sh
```

Qué mostrar:

- caso `disabled` produce `skipped`;
- caso `enabled` produce recommendation + audit;
- la policy source es PostgreSQL;
- no hay lógica de control fuera del engine.

Referencias:

- [control_engine_worker.md](../operations/control_engine_worker.md)
- [control_policy_contract.md](../contracts/control_policy_contract.md)
- [control_audit_contract.md](../contracts/control_audit_contract.md)

### Paso 3. Observabilidad operativa

Abrir:

- [http://localhost:3000/api/control/status](http://localhost:3000/api/control/status)
- [http://localhost:3000/api/control/recommendations](http://localhost:3000/api/control/recommendations)
- [http://localhost:3000/api/control/audit](http://localhost:3000/api/control/audit)

Qué mostrar:

- estado del engine;
- recomendaciones recientes;
- trail de auditoría persistido.

Referencias:

- [control_observability.md](../operations/control_observability.md)

### Paso 4. Dashboard read-only

Abrir:

- [http://localhost:3000/control](http://localhost:3000/control)

Qué mostrar:

- estado general;
- proyectos con control habilitado;
- policies habilitadas;
- recommendations recientes;
- audit events recientes.

Referencia:

- [control_dashboard.md](../operations/control_dashboard.md)

### Paso 5. Benchmark reproducible

Ejecutar:

```bash
PYTHONPATH=src ./venv/bin/python scripts/export_operational_control_benchmark.py
```

Luego mostrar:

- [operational_control_benchmark.md](../benchmark/operational_control_benchmark.md)
- [operational_control_benchmark.json](../benchmark/operational_control_benchmark.json)

## Resultados actuales a citar

- `policy_driven` obtuvo el menor error medio absoluto agregado: `5.469`
- `proportional` obtuvo el menor esfuerzo total agregado: `80.31`
- `disabled` produjo `0` recommendations y `3` skipped audits

Contexto adicional:

- `threshold` y `policy_driven` empataron en menor cantidad agregada de acciones: `15`
- `policy_driven` aplicó `proportional x8` y `threshold x8`

## Mensaje técnico clave

El MVP demuestra que:

- el control paramétrico ya está integrado al runtime real;
- la habilitación por proyecto funciona;
- las policies son persistentes y seleccionables por contexto;
- toda decisión queda auditada;
- la observabilidad ya es visible desde el dominio operacional;
- el benchmark ya produce evidencia reproducible para tesis, jurado y dirección.

## Documentos de soporte

- [CONTROL_SYSTEM_SPEC.md](../architecture/CONTROL_SYSTEM_SPEC.md)
- [control_engine_worker.md](../operations/control_engine_worker.md)
- [control_observability.md](../operations/control_observability.md)
- [control_dashboard.md](../operations/control_dashboard.md)
- [operational_control_benchmark.md](../benchmark/operational_control_benchmark.md)
- [control_engine_executive_summary.md](./control_engine_executive_summary.md)
