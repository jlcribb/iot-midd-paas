# Control Dashboard

## Objetivo

El dashboard de control expone una vista operacional minima y de solo lectura del `control_engine_worker` desde `apps/topology-next`.

No permite:

- editar policies;
- ejecutar acciones de control;
- cambiar feature flags;
- introducir logica de control en Next.js.

Ruta principal:

```text
/control
```

## Fuentes de datos

La pagina consume los endpoints read-only ya disponibles en el backend operacional:

- `GET /api/control/status`
- `GET /api/control/recommendations`
- `GET /api/control/audit`

El origen efectivo de lectura es PostgreSQL, reutilizando la observabilidad persistida del dominio de control.

## Que muestra

### Estado general

- actividad del control engine;
- ultimo audit conocido;
- ultima recommendation conocida;
- ultimo evento `skipped`.

### Configuracion operativa

- proyectos con `parametric_control_enabled = true`;
- policies habilitadas;
- proyectos con policies persistidas.

### Actividad de las ultimas 24 horas

- cantidad de recommendations;
- cantidad de eventos `skipped`;
- cantidad de errores;
- cantidad total de audit events.

### Tablas read-only

- `Recommendations recientes`: ultimas decisiones emitidas por el worker con policy, prioridad y version.
- `Audit events recientes`: ultimos envelopes auditados con estado `processed`, `skipped` o `error`.

## Uso recomendado en demo

Secuencia sugerida:

1. Levantar el stack Docker.
2. Habilitar `parametric_control_enabled` para el proyecto desde la capa oficial de proyectos.
3. Confirmar que exista al menos una `project_control_policy` habilitada.
4. Ejecutar `./scripts/smoke_control_engine_end_to_end.sh`.
5. Abrir `/control`.
6. Mostrar primero el bloque de estado.
7. Mostrar luego recommendation y audit para evidenciar trazabilidad.

En el compose local de desarrollo, `/api/control/*` queda accesible vía dev fallback de RBAC para facilitar validación operacional sin OAuth manual.

## Restricciones de alcance

Este dashboard no reemplaza un panel de administracion. Su objetivo es hacer visible el valor operativo minimo del control engine sin agregar UI compleja ni caminos de mutacion.
