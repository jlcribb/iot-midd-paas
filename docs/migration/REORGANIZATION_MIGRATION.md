# Reorganization Migration Log

Fecha: 2026-04-20

## Objetivo

Dejar trazabilidad explicita de la reorganizacion del repo.

## Cambios realizados en esta iteracion

### Estructura creada

Se creo el esqueleto objetivo:

- `apps/`
- `packages/`
- `infra/`
- `docs/architecture/`
- `docs/operations/`
- `docs/migration/`
- `docs/legacy/`

Subdirectorios agregados:

- `apps/ingest-python/`
- `apps/api-python-legacy/`
- `apps/admin-fastapi/`
- `apps/topology-next/`
- `apps/cognitive-core/`
- `apps/parametric-control-engine/`
- `apps/dte/`
- `packages/shared-contracts/`
- `packages/shared-docs/`
- `infra/containers/`
- `infra/migrations/`
- `infra/env/`

### Documentacion actualizada

- `README.md` fue reescrito para reflejar la arquitectura real y la clasificacion oficial/transition/legacy/experimental.
- se agrego ADR:
  - `docs/architecture/ADR-001-repository-architecture.md`
- se agrego este documento de migracion.

### Limpieza de la raiz del repositorio

Se movio documentacion historica desde la raiz a `docs/legacy/` para reducir ruido y dejar el entrypoint documental principal concentrado en `README.md`.

Archivos movidos:

- `COMANDOS_EJECUTAR.md`
- `DEPLOYMENT_DASHBOARD.md`
- `DEVELOPMENT_SUMMARY_PROCESSOR.md`
- `DEVELOPMENT_SUMMARY_STORAGE.md`
- `ESTADO_SISTEMA.md`
- `ESTRUCTURA_BASES_DATOS.md`
- `GUIA_INICIO_RAPIDO.md`
- `INICIAR_ADMIN.md`
- `INSTALL_TESTING.md`
- `PLAN_TESTING_PRODUCCION.md`
- `README_API_REST.md`
- `README_AUDITORIA.md`
- `README_CRUD_REPOSITORIES.md`
- `README_DEMOSTRACION.md`
- `README_INGESTA.md`
- `README_MAIN_SCRIPT.md`
- `README_MONITORING.md`
- `README_MULTI_PROTOCOL.md`
- `README_PARTITIONING.md`
- `README_POSTGRESQL.md`
- `SOLUCION_PYTEST.md`
- `SOLUCION_PYTEST_FINAL.md`
- `iot_middleware_status_20260115_180854.txt`

Ademas se corrigieron referencias activas desde:

- `examples/README_DHT22_SBC.md`
- `scripts/README_GESTOR.md`
- `scripts/install_demo_dependencies.sh`
- `containers/admin/README.md`
- documentos internos ya movidos a `docs/legacy/`

### Mudanza de `next-backend` a `apps/topology-next`

Se movio el backend/UI operacional desde:

- `next-backend/`

hacia:

- `apps/topology-next/`

Para preservar compatibilidad con comandos existentes, se dejo un symlink temporal:

- `next-backend -> apps/topology-next`

Esto permite:

- usar la ruta canonica nueva para la arquitectura;
- mantener operativo el baseline viejo mientras se actualizan scripts y tooling.

### Mudanza de Alembic a `infra/migrations`

Se movieron:

- `alembic/` -> `infra/migrations/alembic/`
- `alembic.ini` -> `infra/migrations/alembic.ini`

Compatibilidad temporal mantenida:

- `alembic -> infra/migrations/alembic`
- `alembic.ini -> infra/migrations/alembic.ini`

Esto permite mantener comandos existentes mientras la ruta canonica pasa a ser:

```bash
alembic -c infra/migrations/alembic.ini upgrade head
```

### Split de infraestructura desde `containers/` hacia `infra/containers`

Se movieron:

- `containers/podman-compose.yaml` -> `infra/containers/podman-compose.yaml`
- `containers/mosquitto/*` -> `infra/containers/mosquitto/*`
- `containers/postgresql/*` -> `infra/containers/postgresql/*`
- `containers/influxdb/*` -> `infra/containers/influxdb/*`

Compatibilidad temporal mantenida:

- `containers/podman-compose.yaml` como archivo de compatibilidad
- `containers/mosquitto -> ../infra/containers/mosquitto`
- `containers/postgresql -> ../infra/containers/postgresql`
- `containers/influxdb -> ../infra/containers/influxdb`

En esta etapa no se movieron:

- `containers/admin/*`
- `containers/dashboard/*`

La ruta canonica nueva para levantar infraestructura local es:

```bash
podman compose -f infra/containers/podman-compose.yaml up -d
```

La ruta legacy aun soportada es:

```bash
podman compose -f containers/podman-compose.yaml up -d
```

### Split de `containers/admin` hacia `apps/admin-fastapi`

Se movio:

- `containers/admin/*` -> `apps/admin-fastapi/*`

Compatibilidad temporal mantenida:

- `containers/admin -> ../apps/admin-fastapi`

Actualizaciones minimas realizadas:

- Dockerfile del admin ahora copia desde `apps/admin-fastapi/`
- compose instala requirements desde `/app/apps/admin-fastapi/requirements.txt`
- el comando de runtime se mantiene en `python -m containers.admin.main`

En esta etapa no se movieron:

- `containers/dashboard/*`
- `src/iot_middleware/core_backend/*`

### Split de `containers/dashboard` hacia `apps/monitoring-dashboard`

Se movio:

- `containers/dashboard/*` -> `apps/monitoring-dashboard/*`

Compatibilidad temporal mantenida:

- `containers/dashboard -> ../apps/monitoring-dashboard`

Actualizaciones minimas realizadas:

- Dockerfile del dashboard ahora copia desde `apps/monitoring-dashboard/`
- compose instala requirements desde `/app/apps/monitoring-dashboard/requirements.txt`
- el comando de runtime se mantiene en `python -m containers.dashboard.main`

En esta etapa no se movieron:

- `src/iot_middleware/core_backend/*`

### Limpieza de artefactos historicos en `containers/`

Se movieron fuera de `containers/` los archivos historicos que no forman parte del runtime ni de la capa de compatibilidad:

- `containers/README.md` -> `docs/legacy/containers/README.md`
- `containers/development_log_20250812_190645.md` -> `docs/legacy/containers/development_log_20250812_190645.md`
- `containers/iot_middleware_status_20250812_190637.txt` -> `docs/legacy/containers/iot_middleware_status_20250812_190637.txt`

Ademas, scripts y documentacion operativa pasaron a preferir:

- `infra/containers/podman-compose.yaml`
- `apps/admin-fastapi`
- `apps/monitoring-dashboard`

La compatibilidad temporal se mantiene mediante:

- `containers/podman-compose.yaml`
- `containers/admin -> ../apps/admin-fastapi`
- `containers/dashboard -> ../apps/monitoring-dashboard`
- `containers/mosquitto -> ../infra/containers/mosquitto`
- `containers/postgresql -> ../infra/containers/postgresql`
- `containers/influxdb -> ../infra/containers/influxdb`

### Aislamiento de exposicion de `core_backend`

`src/iot_middleware/core_backend/*` permanece sin cambios internos, pero deja de exponerse como superficie normal del admin.

Cambio realizado:

- antes: `apps/admin-fastapi` montaba `core_backend` bajo `/api/*`
- ahora: `apps/admin-fastapi` lo monta bajo `/api/transition/core-backend/*`

Motivo:

- dejar claro que `core_backend` es una capa de `transition`;
- evitar que compita visualmente con la implementacion oficial del dominio en `apps/topology-next`;
- preparar su retiro posterior sin mezclar esta fase con borrado de logica.

### Clasificacion de routers dormidos en `src/iot_middleware/api/`

Se documentaron como `legacy-dormant` los routers presentes en `src/iot_middleware/api/routers/` que no estan montados por `src/iot_middleware/api/api.py`:

- `auth_router.py`
- `projects_router.py`
- `data_router.py`
- `events_router.py`

Se mantiene como `legacy-active`:

- `dashboard_router.py`

No se movieron archivos ni se altero `api.py` en esta etapa.

### Democion operativa de `main.py`

`main.py` se mantiene en el repo, pero deja de tratarse como entrypoint preferido del sistema.

Clasificacion:

- `transition`
- `manual-only`

Rutas canonicas promovidas:

- stack local: `infra/containers/podman-compose.yaml`
- dominio operacional oficial: `apps/topology-next`
- runtime de ingesta Python: `python -m iot_middleware.services.ingestor`

`main.py` se conserva runnable para workflows manuales o de desarrollo transicional.

### Segmentacion interna de `src/iot_middleware/storage/db_handler.py`

Se mantuvo el archivo unico, pero se hicieron explicitas sus fronteras internas:

- `official runtime infrastructure`
  - conexiones
  - sesiones
  - health checks
  - metrics
  - factory `create_database_handler(...)`
- `transition telemetry write path`
  - `DatabaseHandler.write_telemetry(...)`
  - aliases preservados `insert_sensor_data(...)` e `insert_influxdb(...)`
- `legacy bootstrap / compatibility`
  - bootstrap de esquema en runtime
  - helper module-level `insert_sensor_data(...)`
  - defaults hardcodeados encapsulados en `_build_legacy_default_configs()`

No se cambio el comportamiento observable de `api.py`, `ingestor` ni del runtime actual.

## Que NO se movio todavia

Para preservar funcionalidad y baseline, en esta iteracion no se movio codigo productivo desde sus rutas actuales:

- `src/iot_middleware/*`
- `containers/podman-compose.yaml`

## Motivo de esta restriccion

Los riesgos actuales incluyen:

- imports Python y tooling;
- comandos documentados y scripts existentes;
- acoplamiento del admin con multiples capas del dominio;
- `containers/` con `.git` propio incrustado;
- coexistencia de runtime legacy y runtime oficial.

## Pendiente para la siguiente iteracion

1. Definir primer movimiento fisico de bajo riesgo.
2. Decidir tratamiento tecnico de `containers/` y su `.git` interno.
3. Preparar matriz de equivalencias entre `core_backend` y `apps/topology-next`.
4. Reubicar documentacion legacy fuera de la raiz.
5. Evaluar wrappers temporales para mover codigo sin romper entrypoints.
6. Actualizar gradualmente scripts y tooling para usar `infra/migrations/alembic.ini` como ruta explicita.

## Criterio para la siguiente fase

La siguiente fase puede mover codigo solo si:

- mantiene `./scripts/smoke_core.sh` funcional;
- mantiene `cd apps/topology-next && npm test` funcional;
- mantiene temporalmente `cd next-backend && npm test` funcional;
- documenta el cambio de path y comandos asociados;
- no mezcla mudanza estructural con nuevas features.
