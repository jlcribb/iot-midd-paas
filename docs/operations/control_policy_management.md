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
- deshabilitar una policy existente;
- previsualizar qué policy quedaría seleccionada para un contexto dado;
- mostrar warnings de gobernanza cuando hay overlap exacto entre policies enabled.

La pantalla no ejecuta evaluaciones ni calcula recomendaciones. Solo usa APIs de
Next.js como write path hacia PostgreSQL.

## RBAC operacional

La superficie `/control` y `/control/policies` aplica un RBAC mínimo con scope
por proyecto, sin tocar el runtime Python.

Roles soportados:

- `viewer`: puede ver dashboard y policies;
- `operator`: puede ver, crear, editar y habilitar/deshabilitar policies dentro de su scope;
- `admin`: mismas capacidades que `operator` y permiso reservado para delete físico futuro.

Resolución del actor actual:

- headers HTTP `x-control-user-id`, `x-control-user-name`, `x-control-user-role`, `x-control-project-ids`;
- cookies `control_user_id`, `control_user_name`, `control_user_role`, `control_project_ids`;
- defaults de entorno para operación local.

Variables de entorno útiles:

- `CONTROL_RBAC_DEFAULT_USER_ID`
- `CONTROL_RBAC_DEFAULT_USER_NAME`
- `CONTROL_RBAC_DEFAULT_ROLE`
- `CONTROL_RBAC_DEFAULT_PROJECT_SCOPE`

`CONTROL_RBAC_DEFAULT_PROJECT_SCOPE` acepta `*` / `all` o una lista CSV de
`project_id`.

## APIs

### GET `/api/control/access`

Devuelve:

- actor actual resuelto;
- permisos efectivos;
- proyectos visibles dentro del scope operacional.

### GET `/api/control/policies`

Lista policies visibles para el actor actual. Soporta filtros opcionales:

- `projectId`
- `variable`
- `enabled=true|false`

### POST `/api/control/policies`

Crea una policy nueva si el actor tiene permiso `edit_policies` y acceso al
`project_id` indicado.

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

Si el patch cambia `enabled`, también exige permiso `toggle_policies`.

### DELETE `/api/control/policies/[id]`

No borra físicamente la fila. Ejecuta soft-disable:

- `enabled = false`
- incremento automático de `version` si la policy estaba activa

La operación queda protegida como acción de `toggle_policies`.

### POST `/api/control/policies/preview`

Permite simular la selección de policy para un `project_id + variable + context`
sin tocar el runtime ni persistir cambios. El actor debe tener visibilidad sobre
ese proyecto.

Payload esperado:

```json
{
  "project_id": "uuid",
  "variable": "tank_level",
  "context": {
    "sector": "tank_A",
    "mode": "night"
  },
  "candidate_policy": {
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
      "gain": 1.5,
      "deadband": 0.0,
      "min_action": 0.0
    },
    "priority": 10,
    "enabled": true,
    "version": 2
  }
}
```

La respuesta informa:

- selección actual para ese contexto;
- selección hipotética incluyendo la candidate policy;
- si la candidate policy ganaría o no;
- conflictos exactos detectados;
- warnings operacionales para revisión antes de guardar.

## Validaciones y gobernanza

- `project_id` debe ser UUID válido;
- `variable` no puede ser vacía;
- `policy_type` soportado: `proportional` o `threshold`;
- `context_selector` debe ser objeto JSON;
- `params` debe ser objeto JSON;
- `priority` debe ser entero no negativo;
- `params` se validan por `policy_type`.

Reglas vigentes por policy type:

- `proportional` requiere `setpoint_value` y `gain`, con `gain > 0`;
- `proportional` valida además `deadband >= 0`, `min_action >= 0` y `max_action >= min_action` si existe;
- `threshold` sigue el contrato actual del runtime y requiere `setpoint_value`, `tolerance`, `increase_step`, `decrease_step` y `hold_signal`;
- `threshold` valida `tolerance >= 0`, `increase_step >= 0` y `decrease_step >= 0`.

Reglas de conflicto:

- solo se analizan policies `enabled = true`;
- el conflicto se evalúa dentro del mismo `project_id + variable`;
- si dos policies tienen el mismo `context_selector` exacto y también el mismo `priority + version`, la UI y el API lo tratan como conflicto bloqueante (`selection_tie`);
- si existe otra policy enabled de mismo scope exacto con mayor `priority/version`, la nueva policy queda marcada como `shadowed_by_enabled_policy`;
- si la nueva policy desplaza a otra de menor `priority/version`, se informa como `shadows_enabled_policy`.

Estas validaciones no reemplazan el selector runtime: solo reducen configuraciones ambiguas antes de persistirlas.

## Auditoría de cambios

Los cambios write-path desde `apps/topology-next` registran auditoría en
`iot_schema.auditoria` usando:

- `entidad = project_control_policies`
- `accion = CONTROL_POLICY_CREATED | CONTROL_POLICY_UPDATED | CONTROL_POLICY_DISABLED`
- `cambios = { antes, despues }`
- `contexto` con metadata del subsistema, claves operacionales básicas y actor
  que ejecutó la acción

Esto no modifica el `control_engine_worker`; solo agrega trazabilidad sobre el
origen de cambios de configuración.

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
