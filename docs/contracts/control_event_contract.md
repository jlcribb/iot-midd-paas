# Control Event Contract

## Objetivo

Contrato de entrada para `control_engine_worker`.

Flujo canónico:

Telemetry Event  
→ ControlEvaluationRequest  
→ Policy Selection  
→ Evaluation  
→ Recommendation  
→ Publishable Envelope  
→ Audit Envelope

## Canal runtime

- routing key por defecto: `telemetry.events`
- cola por defecto del worker: `telemetry.events`
- exchange por defecto: `iot_middleware`
- constantes oficiales compartidas: `src/iot_middleware/services/control_runtime_contract.py`

## Payload mínimo requerido

```json
{
  "project_id": "00000000-0000-0000-0000-000000000001",
  "variable": "tank_level",
  "value": 72.5,
  "timestamp": "2026-04-28T22:50:40.972634+00:00"
}
```

## Campos soportados

| Campo | Tipo | Requerido | Descripción |
|------|------|-----------|-------------|
| `project_id` | `uuid string` | sí | Proyecto dueño del evento. |
| `variable` | `string` | sí | Variable controlada a evaluar. |
| `value` | `number` | sí | Valor observado de telemetría. |
| `timestamp` | `ISO-8601 string` | sí | Timestamp del evento. |
| `event_id` | `string` | no | Idempotencia/trazabilidad. Si falta, el worker genera uno. |
| `context` | `object` | no | Contexto runtime, por ejemplo `sector`. |
| `source` | `string` | no | Origen del evento. Default `runtime.telemetry`. |
| `event_kind` | `string` | no | Tipo de evento. Default `telemetry.observed`. |
| `quality` | `string` | no | Calidad del dato. Default `raw`. |
| `metadata` | `object` | no | Metadatos libres del evento. |

## Envelope alternativo soportado

El worker también acepta un envelope con `payload` si allí vive el evento canónico:

```json
{
  "payload": {
    "project_id": "00000000-0000-0000-0000-000000000001",
    "variable": "tank_level",
    "value": 72.5,
    "timestamp": "2026-04-28T22:50:40.972634+00:00"
  }
}
```

## Reglas operativas

- Si `parametric_control_enabled = FALSE`, el worker no emite recommendation.
- En caso `disabled`, el worker sí genera un audit envelope con `status=skipped`.
- Si no existe policy persistida para `project_id + variable + context`, el worker no emite recommendation y audita `status=error`.
- `event_id` funciona como identificador primario de correlación entre evento, recommendation y audit.
- La fuente canónica de policies es [control_policy_contract.md](./control_policy_contract.md).
- Toda lógica de control se delega a `parametric-control-engine`.
