# monitoring-dashboard

Aplicacion experimental de monitoreo en tiempo real para Midd IOT.

## Estado

Clasificacion actual: `experimental`

No forma parte del backend operacional oficial del dominio. Se mantiene como dashboard de monitoreo y runtime/demo auxiliar.

## Ubicacion canonica

- `apps/monitoring-dashboard/*`

## Compatibilidad temporal

- `containers/dashboard -> ../apps/monitoring-dashboard`

Esto permite conservar:

- `python -m containers.dashboard.main`
- referencias existentes en compose
- imports y rutas de runtime actuales

## Notas

- `core_backend` no fue movido en esta etapa;
- el dashboard sigue siendo una pieza experimental;
- el path legacy bajo `containers/dashboard` se mantiene solo por compatibilidad.
