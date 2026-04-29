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

## Variantes de estado

- `processed`: evaluación completada y recommendation emitida.
- `skipped`: proyecto deshabilitado por feature flag.
- `error`: fallo de evaluación, integración o ausencia de policy válida.

## Envelope base

```json
{
  "message_type": "control.audit",
  "timestamp": "2026-04-28T22:50:41.113102+00:00",
  "status": "processed"
}
```

## Envelope `processed`

```json
{
  "audit_id": "audit::evt-123::tank_level",
  "record_type": "control.recommendation.audit",
  "partition_key": "tank_level",
  "payload": {
    "event_id": "evt-123",
    "variable_id": "tank_level",
    "project_id": "00000000-0000-0000-0000-000000000001",
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
    "input_event": {}
  }
}
```

## Envelope `skipped`

```json
{
  "message_type": "control.audit",
  "timestamp": "2026-04-28T22:50:41.113102+00:00",
  "status": "skipped",
  "project_id": "00000000-0000-0000-0000-000000000001",
  "variable": "tank_level",
  "input_event": {},
  "recommendation": null,
  "publishable": null,
  "skip_reason": "feature_flag_disabled"
}
```

## Envelope `error`

```json
{
  "message_type": "control.audit",
  "timestamp": "2026-04-28T22:50:41.113102+00:00",
  "status": "error",
  "project_id": "00000000-0000-0000-0000-000000000001",
  "variable": "tank_level",
  "input_event": {},
  "recommendation": null,
  "publishable": null,
  "error": "detalle del fallo"
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
