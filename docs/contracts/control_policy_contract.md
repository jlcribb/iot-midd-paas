# Control Policy Contract

## Objetivo

Contrato persistente para políticas de control por proyecto.

La tabla canónica es:

```text
public.project_control_policies
```

## Campos operativos

| Campo | Tipo | Requerido | Descripción |
|------|------|-----------|-------------|
| `id` | `uuid` | sí | Identificador de la fila/version concreta. |
| `project_id` | `uuid` | sí | Proyecto dueño de la policy. |
| `variable` | `text` | sí | Variable controlada. |
| `context_selector` | `jsonb object` | sí | Filtro exacto por contexto, por ejemplo `{"sector":"tank_A"}`. |
| `policy_type` | `text` | sí | Tipo de evaluación. Hoy: `proportional` o `threshold`. |
| `params` | `jsonb object` | sí | Parámetros del binding/evaluador. |
| `priority` | `integer` | sí | Desempate entre policies de misma especificidad. Mayor gana. |
| `enabled` | `boolean` | sí | Si está `FALSE`, no participa en la selección. |
| `version` | `integer` | sí | Versión lógica de la policy. Mayor gana dentro de la misma firma. |
| `created_at` | `timestamptz` | sí | Creación. |
| `updated_at` | `timestamptz` | sí | Última actualización. |

## Semántica de selección

1. Se filtra por `project_id`, `variable` y `enabled = TRUE`.
2. El selector del engine exige match exacto de `context_selector` sobre el `context` del evento.
3. Entre candidates válidas, gana:
   - mayor especificidad de contexto;
   - luego mayor `priority`;
   - luego mayor `version`.

## Params soportados

### `policy_type = proportional`

```json
{
  "variable_name": "Tank Level",
  "variable_unit": "units",
  "actuator_name": "control_output",
  "setpoint_value": 70.0,
  "gain": 1.0,
  "deadband": 0.0,
  "min_action": 0.0,
  "max_action": 10.0
}
```

### `policy_type = threshold`

```json
{
  "variable_name": "Tank Level",
  "variable_unit": "units",
  "actuator_name": "control_output",
  "setpoint_value": 70.0,
  "tolerance": 2.0,
  "increase_step": 1.5,
  "decrease_step": 2.0,
  "hold_signal": 0.0
}
```

## Fallback

El fallback a `InMemoryPolicySource` no es camino productivo.

Solo debe usarse para:

- `smoke_control_engine.sh`
- debugging local

Variable explícita:

```text
CONTROL_WORKER_ALLOW_INMEMORY_POLICY_FALLBACK=true
```

La publicación en `stdout` ya no habilita ese fallback por sí sola.
Si el runtime no puede resolver policies PostgreSQL y la variable anterior no está
activa, el resultado esperado es `status=error` auditable.
