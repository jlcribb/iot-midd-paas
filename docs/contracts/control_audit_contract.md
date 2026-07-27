# Control Audit Contract

## Objetivo

Contrato de salida auditable del `control_engine_worker`.

Este envelope se:

- publica en RabbitMQ bajo `control.audit` por defecto;
- persiste en `iot_schema.auditoria`;
- sirve como rastro de decisiones, errores y skips por feature flag.

## Routing runtime

- routing key por defecto: `control.audit`
- exchange por defecto: `iot_middleware`
- constantes oficiales compartidas: `src/iot_middleware/services/control_runtime_contract.py`

## Variantes de estado

- `processed`: evaluación completada y recommendation emitida.
- `skipped`: proyecto deshabilitado por feature flag.
- `error`: fallo de evaluación, integración o ausencia de policy válida.

## Envelope base

```json
{
  "audit_id": "audit::evt-123::tank_level",
  "message_type": "control.audit",
  "timestamp": "2026-04-28T22:50:41.113102+00:00",
  "status": "processed",
  "correlation_id": "control::evt-123::tank_level"
}
```

## Envelope `processed`

```json
{
  "audit_id": "audit::evt-123::tank_level",
  "record_type": "control.recommendation.audit",
  "partition_key": "tank_level",
  "message_type": "control.audit",
  "timestamp": "2026-04-28T22:50:41.113102+00:00",
  "status": "processed",
  "project_id": "00000000-0000-0000-0000-000000000001",
  "variable": "tank_level",
  "correlation_id": "control::evt-123::tank_level",
  "payload": {
    "event_id": "evt-123",
    "variable_id": "tank_level",
    "project_id": "00000000-0000-0000-0000-000000000001",
    "correlation_id": "control::evt-123::tank_level",
    "recommendation_channel": "control.recommendations",
    "evaluation": {},
    "adapter_trace": [],
    "runtime_payload": {},
    "policy_selection": {
      "policy_id": "policy::tank_level",
      "selector_name": "static-policy-selector",
      "priority": 10,
      "version": 2,
      "policy_type": "proportional",
      "selection_trace": []
    },
    "input_event": {},
    "delivery": {
      "recommendation_publish": {
        "status": "published",
        "transport": "rabbitmq",
        "routing_key": "control.recommendations"
      },
      "audit_publish": {
        "status": "published",
        "transport": "rabbitmq",
        "routing_key": "control.audit"
      },
      "audit_persistence": {
        "status": "persisted",
        "attempted": true,
        "backend": "postgresql",
        "store": "iot_schema.auditoria",
        "table": "iot_schema.auditoria",
        "attempted_at": "2026-04-28T22:50:41.113102+00:00",
        "completed_at": "2026-04-28T22:50:41.213102+00:00",
        "row_id": 123,
        "rows_affected": 1
      }
    }
  }
}
```

## Envelope `skipped`

```json
{
  "audit_id": "audit::evt-123::tank_level",
  "message_type": "control.audit",
  "timestamp": "2026-04-28T22:50:41.113102+00:00",
  "status": "skipped",
  "project_id": "00000000-0000-0000-0000-000000000001",
  "variable": "tank_level",
  "correlation_id": "control::evt-123::tank_level",
  "input_event": {},
  "recommendation": null,
  "publishable": null,
  "skip_reason": "feature_flag_disabled",
  "payload": {
    "event_id": "evt-123",
    "variable_id": "tank_level",
    "project_id": "00000000-0000-0000-0000-000000000001",
    "correlation_id": "control::evt-123::tank_level",
    "input_event": {},
    "policy_selection": null,
    "evaluation": null,
    "runtime_payload": null,
    "skip_reason": "feature_flag_disabled",
    "delivery": {
      "recommendation_publish": {
        "status": "not_requested",
        "transport": null,
        "routing_key": "control.recommendations"
      },
      "audit_publish": {
        "status": "published",
        "transport": "rabbitmq",
        "routing_key": "control.audit"
      },
      "audit_persistence": {
        "status": "persisted",
        "attempted": true,
        "backend": "postgresql",
        "store": "iot_schema.auditoria",
        "table": "iot_schema.auditoria",
        "attempted_at": "2026-04-28T22:50:41.113102+00:00",
        "completed_at": "2026-04-28T22:50:41.213102+00:00",
        "row_id": 124,
        "rows_affected": 1
      }
    }
  }
}
```

## Envelope `error`

```json
{
  "audit_id": "audit::evt-123::tank_level",
  "message_type": "control.audit",
  "timestamp": "2026-04-28T22:50:41.113102+00:00",
  "status": "error",
  "project_id": "00000000-0000-0000-0000-000000000001",
  "variable": "tank_level",
  "correlation_id": "control::evt-123::tank_level",
  "input_event": {},
  "recommendation": null,
  "publishable": null,
  "error": "detalle del fallo",
  "payload": {
    "event_id": "evt-123",
    "variable_id": "tank_level",
    "project_id": "00000000-0000-0000-0000-000000000001",
    "correlation_id": "control::evt-123::tank_level",
    "input_event": {},
    "policy_selection": null,
    "evaluation": null,
    "runtime_payload": null,
    "error": "detalle del fallo",
    "delivery": {
      "recommendation_publish": {
        "status": "not_requested",
        "transport": null,
        "routing_key": "control.recommendations"
      },
      "audit_publish": {
        "status": "published",
        "transport": "rabbitmq",
        "routing_key": "control.audit"
      },
      "audit_persistence": {
        "status": "persisted",
        "attempted": true,
        "backend": "postgresql",
        "store": "iot_schema.auditoria",
        "table": "iot_schema.auditoria",
        "attempted_at": "2026-04-28T22:50:41.113102+00:00",
        "completed_at": "2026-04-28T22:50:41.213102+00:00",
        "row_id": 125,
        "rows_affected": 1
      }
    }
  }
}
```

## Persistencia

Se guarda en `iot_schema.auditoria` con esta semántica:

- `entidad = control_engine_worker`
- `accion`:
  - `CONTROL_RECOMMENDATION_EMITTED`
  - `CONTROL_SKIPPED_BY_FEATURE_FLAG`
  - `CONTROL_EVALUATION_FAILED`
- `entidad_id = project_id` cuando el UUID es válido
- `cambios = audit envelope completo`
- `contexto.source = control_engine_worker`

## Ciclo de persistencia

- envelope recién construido:
  - `audit_persistence.status = not_attempted`
  - `attempted = false`
- envelope publicado en RabbitMQ antes del resultado definitivo:
  - `audit_persistence.status = pending_best_effort`
  - `attempted = true`
- fila persistida con commit exitoso:
  - `audit_persistence.status = persisted`
  - `attempted = true`
  - `row_id` y `rows_affected` quedan disponibles para trazabilidad

## Nota de consistencia

- `audit_persistence` sigue siendo `best-effort`: la publicación RabbitMQ y la persistencia PostgreSQL no forman una transacción distribuida.
- El mensaje publicado no afirma persistencia futura como ya completada: usa `pending_best_effort` mientras el resultado final todavía no existe.
- La fila observada en `iot_schema.auditoria` puede reflejar `persisted` solo cuando el commit terminó correctamente.
- Registros históricos con `pending_best_effort` siguen siendo válidos y deben interpretarse como evidencia de intento, no como error retroactivo.
