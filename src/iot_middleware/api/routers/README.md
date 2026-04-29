# Legacy API Routers

Este directorio contiene routers de la API Python legacy.

## Runtime efectivo actual

Montado por [api.py](/Users/joseluis/dev/iot-middleware%20copia/src/iot_middleware/api/api.py):

- `dashboard_router.py`

No montados en el runtime efectivo actual:

- `auth_router.py`
- `projects_router.py`
- `data_router.py`
- `events_router.py`

## Clasificacion

- `dashboard_router.py`: `legacy-active`
- `auth_router.py`: `legacy-dormant`
- `projects_router.py`: `legacy-dormant`
- `data_router.py`: `legacy-dormant`
- `events_router.py`: `legacy-dormant`

## Nota operativa

Estos routers dormidos se conservan sin cambios funcionales.
No forman parte de la superficie activa de `src/iot_middleware/api/api.py`
y no deben considerarse backend vigente del sistema.
