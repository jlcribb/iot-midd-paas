# Control Policy Management

## Objetivo

Permitir gestión operacional mínima de `public.project_control_policies` desde
`apps/topology-next`, sin acoplar lógica de control al frontend ni modificar el
worker del runtime.

## UI

Ruta:

```text
/control/policies
```

Capacidades expuestas:

- listar policies persistidas;
- crear una policy nueva;
- editar `params`, `context_selector`, `priority` y `enabled`;
- deshabilitar una policy existente.

La pantalla no ejecuta evaluaciones ni calcula recomendaciones. Solo usa APIs de
Next.js como write path hacia PostgreSQL.

## APIs

### GET `/api/control/policies`

Lista policies. Soporta filtros opcionales:

- `projectId`
- `variable`
- `enabled=true|false`

### POST `/api/control/policies`

Crea una policy nueva.

Payload mínimo:

```json
{
  "project_id": "uuid",
  "variable": "tank_level",
  "policy_type": "proportional",
  "context_selector": {
    "sector": "tank_A"
  },
  "params": {
    "variable_name": "Tank Level",
    "actuator_name": "control_output",
    "setpoint_value": 70.0,
    "gain": 1.0,
    "deadband": 0.0,
    "min_action": 0.0
  },
  "priority": 10,
  "enabled": true
}
```

### PATCH `/api/control/policies/[id]`

Actualiza solo campos operativos:

- `params`
- `context_selector`
- `priority`
- `enabled`

Cuando hay cambios reales, la implementación incrementa `version`
automáticamente para mantener coherencia con el contrato operacional.

### DELETE `/api/control/policies/[id]`

No borra físicamente la fila. Ejecuta soft-disable:

- `enabled = false`
- incremento automático de `version` si la policy estaba activa

## Validaciones básicas

- `project_id` debe ser UUID válido;
- `variable` no puede ser vacía;
- `policy_type` soportado: `proportional` o `threshold`;
- `context_selector` debe ser objeto JSON;
- `params` debe ser objeto JSON;
- `priority` debe ser entero no negativo;
- `params` se validan con shape básica según `policy_type`.

## Notas operacionales

- El runtime sigue usando `PostgreSQLPolicySource` como source of truth.
- La UI no reemplaza el feature flag de proyecto:
  si `parametric_control_enabled = false`, el worker seguirá auditando `skipped`.
- Esta fase no modifica:
  - `control_engine_worker`
  - evaluators
  - `core_backend`
  - `admin-fastapi`
  - ingesta
