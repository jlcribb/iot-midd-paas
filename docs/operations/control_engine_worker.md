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

Esta integración es deliberadamente no invasiva:

- no modifica `ingestor`;
- no altera `core_backend` ni `admin-fastapi`;
- no agrega lógica de control al runtime Python;
- delega toda evaluación al `parametric-control-engine`.

La integración runtime queda conectada al bus real RabbitMQ:

- consume `telemetry.events` desde RabbitMQ;
- resuelve policies desde `public.project_control_policies`;
- publica `control.recommendations` y `control.audit` en el exchange topic configurado;
- persiste `control.audit` en `iot_schema.auditoria` como registro runtime liviano;
- `stdout` queda como fallback oficial para smoke y debugging local;
- no agrega lógica de control al runtime Python: solo adapta eventos y delega al engine.

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

## Migración mínima requerida

Aplicar:

- [add_parametric_control_enabled_to_projects.sql](/Users/joseluis/dev/iot-middleware%20copia/infra/migrations/sql/add_parametric_control_enabled_to_projects.sql)
- [create_project_control_policies.sql](/Users/joseluis/dev/iot-middleware%20copia/infra/migrations/sql/create_project_control_policies.sql)
