# Midd IOT

Plataforma de middleware IoT orientada a inteligencia operacional.

Midd IOT no busca competir en transporte de datos, device management o infraestructura cloud IoT generalista. Su foco es:

- inteligencia operacional;
- control adaptativo parametrico;
- sistemas de decision orientados a eventos;
- integracion con gemelos digitales.

## Principio central

> Midd IOT no existe para conectar dispositivos.
> Existe para volverlos inteligentes.

## Arquitectura

La verdad arquitectonica del sistema es:

```text
Protocols -> Events -> Cognitive Core -> Parametric Control -> Actions
```

Componentes conceptuales:

- Ingestion Layer
- Messaging Layer
- Cognitive Core
- Parametric Control Engine
- Digital Twin Engine
- Control Layer
- API / UI Layer

## Estado actual del repositorio

El repo esta en una reorganizacion incremental.

Hoy conviven:

- runtime Python para ingesta, MQTT, storage, procesos IoT y migraciones;
- API Python historica;
- `core_backend` Python en transicion;
- backend/UI Next.js para el dominio operacional;
- modulo de Digital Twin Engine;
- infraestructura local con contenedores;
- documentacion historica, de saneo y de migracion.

## Clasificacion actual

### Oficial

- Runtime Python de ingestión, MQTT, storage, procesamiento y migraciones.
- `apps/topology-next` como implementacion oficial del dominio operacional:
  - projects
  - sectors
  - locations
  - assets
  - topology
  - provisioning
  - canvas/UI

### Transition

- `src/iot_middleware/core_backend`
- `apps/admin-fastapi`

### Legacy

- `src/iot_middleware/api`
- CRUD historico de `apps/admin-fastapi/routers/*` basado en modelos previos

### Experimental

- `apps/monitoring-dashboard`
- `src/iot_middleware/dte`
- ejemplos y demos

## Estructura objetivo

La reorganizacion converge hacia:

```text
apps/
  ingest-python/
  api-python-legacy/
  admin-fastapi/
  topology-next/
  cognitive-core/
  parametric-control-engine/
  dte/

packages/
  shared-contracts/
  shared-docs/

infra/
  containers/
  migrations/
  env/

docs/
  architecture/
  operations/
  migration/
  legacy/
```

## Importante sobre esta etapa

Para preservar el baseline actual, esta primera reorganizacion crea la estructura arquitectonica y la documentacion oficial, pero no mueve todavia el codigo productivo de mayor riesgo.

Por ahora, las rutas efectivas siguen siendo:

- runtime Python: `src/iot_middleware/*`
- API Python legacy: `src/iot_middleware/api/*`
- admin: `apps/admin-fastapi/*`
- compatibilidad temporal: `containers/admin -> ../apps/admin-fastapi`
- dashboard: `apps/monitoring-dashboard/*`
- compatibilidad temporal: `containers/dashboard -> ../apps/monitoring-dashboard`
- dominio operacional Next: `apps/topology-next/*`
- compatibilidad temporal: `next-backend -> apps/topology-next`
- migraciones: `infra/migrations/alembic/*`
- compatibilidad temporal: `alembic -> infra/migrations/alembic`

## Apps y responsabilidades

### `apps/ingest-python/`

Destino arquitectonico del runtime Python oficial:

- ingestion
- MQTT
- storage
- processing
- backend IoT processes

### `apps/api-python-legacy/`

Destino arquitectonico de la API Python historica que queda en legacy.

### `apps/admin-fastapi/`

Destino arquitectonico del admin actual, que queda en transicion mientras se completa la consolidacion del dominio operacional.

Ubicacion canonica actual del codigo:

- `apps/admin-fastapi/*`

Compatibilidad temporal:

- `containers/admin` queda como symlink hacia `apps/admin-fastapi`

### `apps/monitoring-dashboard/`

Aplicacion experimental de monitoreo en tiempo real.

Ubicacion canonica actual del codigo:

- `apps/monitoring-dashboard/*`

Compatibilidad temporal:

- `containers/dashboard` queda como symlink hacia `apps/monitoring-dashboard`

### `apps/topology-next/`

Destino arquitectonico del backend/UI oficial del dominio operacional.

Ubicacion canonica actual del codigo:

- `apps/topology-next/*`

Compatibilidad temporal:

- `next-backend` queda como symlink hacia `apps/topology-next`

### `apps/cognitive-core/`

Reserva explicita para el futuro nucleo cognitivo del sistema.

### `apps/parametric-control-engine/`

Reserva explicita para el motor de control adaptativo parametrico, diferenciador central del producto.

### `apps/dte/`

Destino arquitectonico del Digital Twin Engine.

## Como ejecutar localmente hoy

### Baseline Python

```bash
./scripts/smoke_core.sh
```

Resultado esperado:

- validacion de sintaxis: OK
- flake8 selectivo: OK
- suite core Python: `17 passed`

### Migraciones Alembic

Ruta canonica:

```bash
alembic -c infra/migrations/alembic.ini upgrade head
```

Compatibilidad temporal mantenida:

```bash
alembic upgrade head
```

### Tests del dominio operacional Next

```bash
cd apps/topology-next
npm test
```

Resultado esperado:

- suite TypeScript: `17 passed`

### Stack local actual

Ruta canonica:

```bash
docker compose -f infra/containers/docker-compose.yaml up -d
```

Las rutas `infra/containers/podman-compose.yaml` y `containers/podman-compose.yaml` quedan solo como alias deprecated de compatibilidad, nunca como comando operativo recomendado.

Servicios definidos actualmente:

- `mosquitto`
- `influxdb`
- `postgresql`
- `api`
- `ingestor`
- `rabbitmq`
- `dashboard`
- `admin`
- `topology-ui`

## Entry points actuales

Canonicos:

- stack local completo: `docker compose -f infra/containers/docker-compose.yaml up -d`
- dominio operacional oficial: `cd apps/topology-next && npm run dev`
- runtime de ingesta Python: `python -m iot_middleware.services.ingestor`
- API Python legacy activa: `uvicorn iot_middleware.api.api:app --host 0.0.0.0 --port 8000`
- admin transicional: `python -m containers.admin.main`
- dashboard experimental: `python -m containers.dashboard.main`
- DTE: `PYTHONPATH=src uvicorn iot_middleware.dte.api.app:app --port 8010`

Transicional / manual solamente:

- `python main.py`

Compatibilidad temporal:

- `cd next-backend && npm run dev`

## Documentacion clave

- Arquitectura: [docs/architecture](/Users/joseluis/dev/iot-middleware%20copia/docs/architecture)
- Migracion: [docs/migration](/Users/joseluis/dev/iot-middleware%20copia/docs/migration)
- Legacy: [docs/legacy](/Users/joseluis/dev/iot-middleware%20copia/docs/legacy)
- Saneo y baseline: [docs/SANEO_BASELINE.md](/Users/joseluis/dev/iot-middleware%20copia/docs/SANEO_BASELINE.md)
- Propuesta de reorganizacion: [docs/PROPUESTA_REORGANIZACION_CHATGPT.md](/Users/joseluis/dev/iot-middleware%20copia/docs/PROPUESTA_REORGANIZACION_CHATGPT.md)

## Decision vigente

- Python queda como runtime IoT oficial.
- Docker Desktop queda como runtime oficial de contenedores para desarrollo local.
- Next.js queda como implementacion oficial del dominio operacional.
- La API Python historica queda como legacy.
- `core_backend` queda en transicion hasta su retiro.
- `main.py` queda como entrypoint transicional y manual, no como ruta operativa preferida.
- `dashboard` queda como experimental.
- El repo debe habilitar explicitamente el futuro `cognitive-core` y `parametric-control-engine`.
