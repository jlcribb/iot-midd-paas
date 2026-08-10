# Gobierno de control paramétrico por proyecto

## Fuente de verdad

`public.project_control_memberships` define el scope persistente de un actor OAuth.
Cada fila contiene un email normalizado, un proyecto, un rol (`viewer`, `operator` o
`admin`) y su estado. Los usuarios OAuth sin membership activa reciben scope vacío y
no obtienen acceso global implícito.

`allProjects` queda reservado para el fallback de desarrollo explícitamente habilitado;
las sesiones OAuth se resuelven desde memberships y usan `allProjects=false`.

## Roles

- `viewer`: consulta recursos de control dentro de su scope.
- `operator`: administra policies dentro de su scope, pero no cambia la activación del
  motor.
- `admin`: puede cambiar `parametric_control_enabled` únicamente dentro de su scope.

Si un actor tiene memberships con roles diferentes, el rol efectivo se evalúa por
proyecto para operaciones sensibles.

## Activación de control

`PATCH /api/projects/:projectId` requiere una sesión OAuth válida si el payload incluye
`parametric_control_enabled`. La actualización se rechaza por defecto si falta
membership, el proyecto está fuera de scope o el rol no es `admin`.

Un cambio efectivo actualiza el proyecto e inserta
`PARAMETRIC_CONTROL_ENABLED_CHANGED` en `iot_schema.auditoria` dentro de la misma
transacción. La auditoría conserva actor, rol, proyecto, before/after, timestamp y el
identificador de solicitud cuando está disponible. Los no-op no generan auditoría.

La barra lateral del workspace de Topology muestra el estado persistido de control
paramétrico por proyecto. Consume el snapshot de acceso existente y sólo habilita el
toggle cuando el backend informó la capacidad derivada para ese proyecto. `viewer` y
`operator` pueden ver el estado dentro de su scope, pero quedan en modo read-only;
los proyectos fuera de scope tampoco ofrecen mutación. La UI pide confirmación y el
backend sigue siendo la autoridad final para autorización y auditoría.

## Bootstrap administrativo

La migración crea la tabla vacía para preservar el principio fail-closed. Antes de
administrar control en un proyecto, un administrador de base de datos debe crear una
membership explícita para el email OAuth normalizado y el proyecto correspondiente.
No se deben inferir memberships ni otorgar acceso global a usuarios OAuth existentes.

Ejemplo conceptual (sustituir los placeholders fuera de Git):

```sql
INSERT INTO public.project_control_memberships (actor_email, project_id, role)
VALUES ('admin@example.invalid', '<project-uuid>', 'admin');
```

La baja se realiza con `enabled=false`; nunca se deben usar credenciales OAuth en esta
tabla o en archivos versionados.
