# Control Observability

## Objetivo

Exponer lectura operativa mínima del `control_engine_worker` desde el dominio operacional sin agregar UI compleja ni duplicar lógica de control.

## Endpoints

### `GET /api/control/recommendations`

Devuelve las últimas recomendaciones persistidas vía auditoría runtime.

Query params:

- `projectId`
- `limit`
  - default `20`
  - rango `1..100`

Fuente:

- `iot_schema.auditoria`
- `accion = CONTROL_RECOMMENDATION_EMITTED`

### `GET /api/control/audit`

Devuelve el trail de auditoría del control engine.

Query params:

- `projectId`
- `status`
  - `processed`
  - `skipped`
  - `error`
- `limit`
  - default `50`
  - rango `1..100`

Fuente:

- `iot_schema.auditoria`
- `entidad = control_engine_worker`

### `GET /api/control/status`

Devuelve un snapshot operativo mínimo del control engine.

Incluye:

- `activity_status`
  - `active`
  - `idle`
  - `stale`
- `latest_audit_at`
- `latest_recommendation_at`
- `latest_skipped_at`
- `enabled_projects`
- `enabled_policies`
- `projects_with_policies`
- contadores últimas 24h

Fuentes:

- `public.projects`
- `public.project_control_policies`
- `iot_schema.auditoria`

## Criterio de estado

`activity_status` se deriva del último audit persistido:

- `idle`: no hay actividad histórica
- `active`: hubo actividad en los últimos 15 minutos
- `stale`: existe historial pero no actividad reciente

## Restricciones

- no edita policies
- no ejecuta control
- no consulta UI legacy
- no toca `core_backend`
- no toca `admin-fastapi`
- no introduce nueva base

## Nota operativa

Los endpoints de observabilidad usan PostgreSQL porque es el camino ya persistido y auditable del runtime.

No dependen del management API de RabbitMQ para no acoplar la lectura operativa a un canal adicional.
