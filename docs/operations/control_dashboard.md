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

## Autenticación y acceso de control

El comportamiento por defecto del compose local, y el requerido para
validación RC y producción, es:

```text
CONTROL_RBAC_ALLOW_DEV_FALLBACK=false
```

Con esa configuración, `/api/control/*` requiere autenticación. La
autorización se resuelve mediante memberships persistidos y con alcance por
proyecto: una membership concede acceso únicamente al proyecto y rol
correspondientes, y el acceso entre proyectos se deniega. Las solicitudes
anónimas son rechazadas con `401`.

El fallback de RBAC puede habilitarse sólo de forma explícita con
`CONTROL_RBAC_ALLOW_DEV_FALLBACK=true` para desarrollo local controlado. Es
una conveniencia insegura que reduce las garantías de seguridad: no sustituye
OAuth, no es el mecanismo normal de autorización y nunca debe habilitarse
durante validación RC ni en producción.

## Restricciones de alcance

Este dashboard no reemplaza un panel de administracion. Su objetivo es hacer visible el valor operativo minimo del control engine sin agregar UI compleja ni caminos de mutacion.
