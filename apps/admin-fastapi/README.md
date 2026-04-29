# admin-fastapi

Aplicacion FastAPI de administracion del sistema.

## Estado

Clasificacion actual: `transition`

Este componente no es el backend operacional oficial del dominio. Se mantiene como aplicacion transicional mientras el dominio operacional converge sobre `apps/topology-next`.

## Ubicacion canonica

- `apps/admin-fastapi/*`

## Compatibilidad temporal

- `containers/admin -> ../apps/admin-fastapi`

Esto permite conservar:

- `python -m containers.admin.main`
- referencias existentes en compose
- imports actuales basados en `containers.admin.*`

## Notas

- hoy el admin mezcla CRUD viejo, routers SQL directos y `core_backend`;
- `core_backend` no fue movido en esta etapa;
- su exposicion HTTP queda aislada bajo `/api/transition/core-backend/*`, no como superficie normal del admin;
- `dashboard` tampoco fue movido en esta etapa.
