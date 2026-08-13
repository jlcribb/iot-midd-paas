# Control Engine Worker

## Objetivo

Integrar de forma no invasiva el runtime Python de Midd IOT con `parametric-control-engine`.

## Flujo canónico

Telemetry Event  
→ ControlEvaluationRequest  
→ Policy Selection  
→ Evaluation  
→ Recommendation  
→ Publishable Envelope  
→ Audit Envelope

## Feature flag

El worker solo procesa eventos si el proyecto tiene:

```sql
parametric_control_enabled = TRUE
```

El helper runtime consulta `public.projects` y usa `FALSE` como default seguro si
no puede leer el proyecto o el schema aún no fue migrado.

Cuando el proyecto está deshabilitado:

- consume el evento;
- no emite recommendation;
- publica y persiste un audit envelope con `status=skipped` y `skip_reason=feature_flag_disabled`.

## Modo actual

Esta integración mantiene separación de responsabilidades:

- `ingestor` normaliza y persiste telemetría;
- `ingestor` publica `telemetry.events` de forma canónica y best-effort;
- `control_engine_worker` consume esos eventos sin introducir lógica de control fuera del engine;
- `core_backend` y `admin-fastapi` siguen en transición sin romper compatibilidad;
- toda evaluación sigue delegada a `parametric-control-engine`.

La integración runtime queda conectada al bus real RabbitMQ:

- consume `telemetry.events` desde RabbitMQ;
- resuelve policies desde `public.project_control_policies`;
- publica `control.recommendations` y `control.audit` en el exchange topic configurado;
- persiste `control.audit` en `iot_schema.auditoria` como registro runtime liviano;
- `stdout` queda como fallback oficial para smoke y debugging local;
- no agrega lógica de control al runtime Python: solo adapta eventos y delega al engine.
- los nombres canónicos de routing keys y message types quedan centralizados en `src/iot_middleware/services/control_runtime_contract.py`.

## Servicio oficial del stack

En el compose canónico el worker corre como servicio permanente:

```text
control-engine-worker
```

Ese servicio:

- respeta `parametric_control_enabled` real por proyecto;
- no usa `CONTROL_WORKER_FORCE_ENABLED`;
- consume `telemetry.events`;
- publica `control.recommendations` y `control.audit`;
- persiste auditoría en `iot_schema.auditoria`.

Semántica operativa de `audit_persistence`:

- el envelope base nace en `not_attempted`;
- el audit publicado sale en `pending_best_effort`;
- la fila almacenada pasa a `persisted` solo cuando el commit terminó bien;
- si la persistencia falla, el resultado final del worker marca `failed` y queda warning observable en logs.

## Habilitar Control Paramétrico para un proyecto

Camino oficial:

```http
PATCH /api/projects/{projectId}
Content-Type: application/json

{
  "parametric_control_enabled": true
}
```

El mismo campo está visible en la UI oficial de topología para el proyecto seleccionado.

Default seguro:

```text
parametric_control_enabled = false
```

## Publicación real de telemetría

La ingesta oficial publica eventos canónicos hacia RabbitMQ cuando:

- la medición fue normalizada;
- la persistencia fue exitosa;
- el payload resultante incluye `project_id`, `variable`, `value` y `timestamp`;
- `IOT_MW_CONTROL_TELEMETRY_ENABLED=true` o no fue deshabilitado.

Routing contract por defecto:

```text
telemetry.events
```

Si RabbitMQ no está disponible:

- la ingesta conserva su persistencia;
- se registra error claro en logs;
- no se usa ese fallo como criterio para descartar la telemetría persistida.

## Policy source

Camino productivo:

- `PostgreSQLPolicySource`
- tabla `public.project_control_policies`
- match por `project_id + variable + context`
- desempate por especificidad, `priority` y `version`

Fallback permitido solo para smoke/debug:

```text
CONTROL_WORKER_ALLOW_INMEMORY_POLICY_FALLBACK=true
```

Nota importante:

- `CONTROL_WORKER_PUBLISH_MODE=stdout` ya no habilita por sí solo el fallback a `InMemoryPolicySource`;
- si PostgreSQL no resuelve policies y el fallback explícito no está activo, el resultado esperado es audit `status=error`.

Si no hay policy válida y el fallback no está habilitado:

- no se emite recommendation;
- se publica y persiste un audit envelope con `status=error`.

## Comandos útiles

Smoke local directo:

```bash
./scripts/smoke_control_engine.sh
```

Smoke con script Python:

```bash
./venv/bin/python scripts/publish_test_control_event.py
```

Smoke real con RabbitMQ:

```bash
./scripts/smoke_control_engine_rabbitmq.sh
```

Ese smoke cubre ambos casos:

- proyecto `disabled` → sin recommendation, con audit `skipped`;
- proyecto `enabled` → recommendation + audit.

Smoke end-to-end real:

```bash
./scripts/smoke_control_engine_end_to_end.sh
```

Cuando ese smoke se ejecuta desde la raíz del repo en la máquina host, asume el
stack canónico levantado con Docker Compose y published ports locales:

- PostgreSQL: `localhost:5432`
- RabbitMQ: `localhost:5672`
- MQTT: `localhost:1883`
- `/api/control/*`: `http://127.0.0.1:3000`

No requiere overrides manuales para `DB_HOST`/`POSTGRES_HOST` en el camino
host-side habitual.

Ese smoke recrea únicamente el worker y el consumer de recomendaciones con
routing keys aisladas por ejecución. Conserva `telemetry.events` como entrada
canónica MQTT, pero nunca publica el smoke en las colas legacy
`control.recommendations` ni `control.audit`. Al terminar, elimina sus colas
temporales y restaura las rutas canónicas de ambos servicios.

Cubre el canal oficial cuando el entorno completo está disponible:

```text
MQTT
→ ingestor
→ telemetry.events
→ control_engine_worker
→ recommendation aislada de smoke
→ DeliveryIntent
→ transactional outbox
→ dispatch simulated
→ iot_schema.auditoria
→ ActuationResult simulated
```

Si el entorno no está completo, el smoke degrada de forma honesta y distingue:

- `contract-level`
- `component-level`
- `broker-level`
- `database-level`
- `full E2E`

Controles adicionales de auditoría en el smoke:

- `audit_publish`
- `audit_persistence_attempt`
- `audit_database_row`
- `audit_metadata_consistency`

La auditoría persistida PostgreSQL es la evidencia primaria del smoke. La cola
`control.audit` es un fan-out legacy/de integración y no debe ser consumida ni
purgeada por validaciones.

Exit codes del smoke:

- `0`: PASS sin warnings ni skips;
- `1`: FAIL;
- `2`: WARN/SKIP sin fallos duros.

## Variables útiles

- `CONTROL_WORKER_FORCE_ENABLED`
  - bypass manual del feature flag solo para smoke local;
- `CONTROL_WORKER_PUBLISH_MODE`
  - `rabbitmq` por defecto para runtime real;
  - `stdout` para fallback local;
- `CONTROL_WORKER_ALLOW_INMEMORY_POLICY_FALLBACK`
  - habilita `InMemoryPolicySource` solo para smoke/debug;
- `CONTROL_WORKER_INPUT_QUEUE`
  - routing key de telemetría; default `telemetry.events`;
- `CONTROL_WORKER_INPUT_ROUTING_KEY`
  - binding key de entrada; default igual a `CONTROL_WORKER_INPUT_QUEUE`;
- `CONTROL_WORKER_CONSUMER_QUEUE`
  - cola física que consume el worker; default `telemetry.events`;
- `CONTROL_WORKER_RECOMMENDATION_QUEUE`
  - routing key/cola de salida para recomendaciones; default `control.recommendations`;
- `CONTROL_WORKER_AUDIT_QUEUE`
  - routing key/cola de salida para auditoría; default `control.audit`;
- `CONTROL_WORKER_RABBITMQ_HOST`
- `CONTROL_WORKER_RABBITMQ_PORT`
- `CONTROL_WORKER_RABBITMQ_USERNAME`
- `CONTROL_WORKER_RABBITMQ_PASSWORD`
- `CONTROL_WORKER_RABBITMQ_VHOST`
- `CONTROL_WORKER_RABBITMQ_EXCHANGE`
- `DB_HOST` / `POSTGRES_HOST`
  - override del host PostgreSQL para lectura del feature flag y persistencia de auditoría;
- `DB_PORT` / `POSTGRES_PORT`
- `DB_NAME` / `POSTGRES_DB`
- `DB_USER` / `POSTGRES_USER`
- `DB_PASSWORD` / `POSTGRES_PASSWORD`
- `CONTROL_WORKER_SETPOINT`
- `CONTROL_WORKER_GAIN`
- `CONTROL_WORKER_DEADBAND`
- `CONTROL_WORKER_MIN_ACTION`
- `CONTROL_WORKER_MAX_ACTION`
- `IOT_MW_CONTROL_TELEMETRY_ENABLED`
  - habilita/deshabilita la publicación de `telemetry.events` desde la ingesta;
- `IOT_MW_CONTROL_TELEMETRY_ROUTING_KEY`
  - routing key de publicación desde la ingesta; default `telemetry.events`;
- `IOT_MW_CONTROL_TELEMETRY_QUEUE`
  - cola durable asociada a esa publicación; default `telemetry.events`;
- `IOT_MW_CONTROL_TELEMETRY_SOURCE`
  - valor de `source` en el envelope; default `runtime.ingestor`;
- `RABBITMQ_HOST`
- `RABBITMQ_PORT`
- `RABBITMQ_USERNAME`
- `RABBITMQ_PASSWORD`
- `RABBITMQ_VHOST`
- `RABBITMQ_EXCHANGE`

## Verificación operativa rápida

Levantar stack:

```bash
docker compose -f infra/containers/docker-compose.yaml up -d
./scripts/docker-stack.sh check
```

Verificar que el worker esté arriba:

```bash
docker compose -f infra/containers/docker-compose.yaml ps
```

Verificar observabilidad:

- `http://localhost:3000/api/control/status`
- `http://localhost:3000/api/control/recommendations`
- `http://localhost:3000/api/control/audit`

## Migración mínima requerida

Aplicar:

- [add_parametric_control_enabled_to_projects.sql](../../infra/migrations/sql/add_parametric_control_enabled_to_projects.sql)
- [create_project_control_policies.sql](../../infra/migrations/sql/create_project_control_policies.sql)
