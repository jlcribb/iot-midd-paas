# Propuesta De Reorganizacion Del Sistema

Fecha de relevamiento: 2026-04-20

## Objetivo

Definir una reorganizacion realista del repo para convertirlo en una base mantenible, con una sola arquitectura oficial por dominio, menor acoplamiento entre componentes y una ruta clara de migracion.

Este documento esta pensado para:

- alinear al equipo sobre el estado actual;
- decidir que queda como nucleo oficial;
- ordenar el trabajo posterior en ChatGPT sin perder contexto tecnico.

## Resumen Ejecutivo

El sistema no esta roto, pero tampoco esta consolidado como una sola plataforma.

Hoy conviven:

- un backend Python historico para ingesta, MQTT, storage y orquestacion;
- una API Python legacy para consulta de datos;
- un core backend Python mas limpio para dominio operativo;
- un backend moderno en Next.js/TypeScript con APIs propias y UI topologica;
- un modulo independiente de Digital Twin Engine.

La principal deuda no es funcional sino arquitectonica: hay duplicacion de dominio, legado mezclado con codigo nuevo, documentacion dispersa y una estructura de repo que ya no refleja una sola fuente de verdad.

## Estado Actual Verificado

Verificado localmente el 2026-04-20:

- `./scripts/smoke_core.sh`: OK
- suite core Python: `17 passed`
- `npm test` en `next-backend`: OK
- suite TypeScript: `17 passed`

Componentes relevantes identificados:

- Orquestador principal Python: [main.py](/Users/joseluis/dev/iot-middleware%20copia/main.py)
- API Python legacy: [src/iot_middleware/api/api.py](/Users/joseluis/dev/iot-middleware%20copia/src/iot_middleware/api/api.py)
- Core backend Python: [src/iot_middleware/core_backend](/Users/joseluis/dev/iot-middleware%20copia/src/iot_middleware/core_backend)
- Admin FastAPI: [containers/admin/main.py](/Users/joseluis/dev/iot-middleware%20copia/containers/admin/main.py)
- Backend/UI Next.js: [next-backend](/Users/joseluis/dev/iot-middleware%20copia/next-backend)
- DTE: [src/iot_middleware/dte](/Users/joseluis/dev/iot-middleware%20copia/src/iot_middleware/dte)
- Migraciones: [infra/migrations/alembic/versions](/Users/joseluis/dev/iot-middleware%20copia/infra/migrations/alembic/versions)
- Infra local: [containers/podman-compose.yaml](/Users/joseluis/dev/iot-middleware%20copia/containers/podman-compose.yaml)

## Diagnostico

### Lo que ya esta bien encaminado

- La ingesta, conectividad MQTT, storage y bootstrap de infraestructura siguen naturalmente alineados con Python.
- El dominio operativo moderno (`projects`, `sectors`, `locations`, `assets`, `topology_links`) ya existe con buenas bases tanto en Python como en TypeScript.
- Hay suites de tests chicas pero utiles para proteger contratos minimos.
- Alembic ya expresa una evolucion de esquema mas ordenada que la inicial.

### Lo que esta mezclado

- El mismo dominio operativo esta duplicado en:
  - `src/iot_middleware/core_backend`
  - `next-backend/src/lib`
- La API Python legacy y el core nuevo no representan exactamente la misma capa.
- `db_handler.py` todavia mezcla bootstrap legado y runtime nuevo.
- `containers/` contiene apps que en la practica funcionan como aplicaciones separadas.
- La documentacion raiz mezcla estado historico, saneo, demostracion y operacion.

### Lo que hoy genera mas costo

- No hay una sola fuente de verdad para el dominio operativo.
- El repo tiene demasiados entrypoints.
- El legado no esta aislado fisicamente.
- Configuracion, infra, apps y documentacion estan acopladas en la misma raiz.
- El worktree esta muy cargado de artefactos y cambios no consolidados.

## Problema Arquitectonico Principal

El problema principal no es "falta de codigo", sino "falta de decision".

Hay que decidir cual es la implementacion oficial para el dominio:

- `projects`
- `sectors`
- `locations`
- `assets`
- `topology_links`
- provisioning asociado

Mientras esa decision no se tome, cualquier mejora nueva aumenta deuda.

## Decision Recomendada

### Mantener como nucleo oficial

- Python para:
  - ingesta;
  - MQTT;
  - integracion con storage;
  - migraciones Alembic;
  - procesos de backend IoT;
  - eventual DTE.

- `next-backend` para:
  - API moderna del dominio operativo;
  - canvas topologico;
  - capa de servicios/repositorios del dominio UI-driven.

### Pasar a transicion controlada

- `src/iot_middleware/core_backend` debe quedar como capa temporal o retirarse del runtime principal una vez migrado el dominio al backend TypeScript.
- `src/iot_middleware/api/api.py` debe quedar marcado como legacy si su rol real pasa a ser solo consulta historica o compatibilidad.

### Aislar del runtime principal

- tablas y rutas legacy tipo `sensor_data/devices/sensors`;
- demos antiguas;
- codigo multiprotocolo retirado pero aun presente como residuo documental;
- scripts y docs de experimentacion que no formen parte del flujo oficial.

## Arquitectura Objetivo

Se recomienda reorganizar el repo por aplicaciones y responsabilidades.

```text
apps/
  ingest-python/
  api-python-legacy/
  admin-fastapi/
  topology-next/
  dte/

packages/
  shared-docs/
  shared-contracts/

infra/
  containers/
  migrations/
  env/

docs/
  architecture/
  operations/
  migration/
```

### Equivalencia con el repo actual

- `main.py` + `src/iot_middleware/services/*` -> `apps/ingest-python/`
- `src/iot_middleware/api/*` -> `apps/api-python-legacy/`
- `containers/admin/*` + posible remanente del core Python -> `apps/admin-fastapi/`
- `next-backend/*` -> `apps/topology-next/`
- `src/iot_middleware/dte/*` -> `apps/dte/`
- `containers/podman-compose.yaml` + init infra -> `infra/containers/`
- `alembic/*` -> `infra/migrations/alembic/`
- `alembic.ini` -> `infra/migrations/alembic.ini`

## Principios De Reorganizacion

- Una sola implementacion oficial por dominio.
- El legado no compite con el runtime principal.
- La infraestructura se separa de las aplicaciones.
- La documentacion principal describe solo el flujo vigente.
- La reorganizacion no debe romper el baseline ya verificado.

## Fases Propuestas

## Fase 1 - Decisiones y congelamiento

Objetivo: dejar de expandir el caos.

Acciones:

- declarar oficialmente que el dominio operativo vive en `next-backend`;
- congelar nuevos cambios funcionales sobre `core_backend` salvo fixes de transicion;
- marcar la API Python actual como `legacy` si corresponde;
- definir entrypoints oficiales para desarrollo local.

Entregables:

- ADR corta de arquitectura;
- tabla "oficial / legacy / transicion / experimental";
- README principal reescrito.

## Fase 2 - Separacion fisica del repo

Objetivo: hacer visible la arquitectura real.

Acciones:

- mover `next-backend` a `apps/topology-next`;
- mover `containers/admin` a `apps/admin-fastapi`;
- mover `src/iot_middleware/dte` a `apps/dte`;
- mover Alembic y compose a `infra/`;
- agrupar scripts operativos por aplicacion o por infra.

Entregables:

- estructura de carpetas nueva;
- imports y comandos actualizados;
- compose y docs apuntando a rutas nuevas.

## Fase 3 - Corte de duplicacion de dominio

Objetivo: evitar mantener dos backends para lo mismo.

Acciones:

- inventariar todo lo que `core_backend` y `next-backend` hacen en comun;
- migrar contratos faltantes al backend TypeScript;
- retirar `core_backend` del runtime activo cuando el dominio ya este completo;
- definir si `admin-fastapi` consume al backend oficial o si queda solo para operacion interna.

Entregables:

- matriz endpoint por endpoint;
- backlog de migracion de contratos;
- fecha de retiro del backend duplicado.

## Fase 4 - Aislamiento del legado

Objetivo: que el legado deje de contaminar el camino principal.

Acciones:

- encapsular `api/api.py` como legacy o compatibilidad;
- separar `db_handler` entre runtime oficial y bootstrap legado;
- retirar rutas, docs y ejemplos obsoletos del README principal;
- mover experimentos, demos y scripts viejos a `legacy/` o `archive/`.

Entregables:

- runtime principal sin tablas o contratos legacy mezclados;
- carpeta `legacy/` o equivalente;
- docs historicas fuera del flujo principal.

## Fase 5 - Contratos y operacion

Objetivo: dejar una base sostenible.

Acciones:

- centralizar variables de entorno por app;
- definir comandos canonicos por aplicacion;
- agregar tests de integracion con PostgreSQL real para el backend oficial;
- dejar un smoke general del sistema.

Entregables:

- `.env.example` por app;
- guia de arranque local real;
- pipeline minima de validacion.

## Riesgos A Vigilar

- mover carpetas sin una matriz de imports puede romper tooling.
- retirar `core_backend` antes de completar equivalencias puede dejar huecos funcionales.
- mantener dos APIs publicas del mismo dominio prolonga la deuda.
- reorganizar sin limpiar docs genera aun mas confusion.
- mezclar reorganizacion con nuevas features es la forma mas rapida de estancarse.

## Criterios De Exito

La reorganizacion se considerara exitosa cuando:

- exista una sola implementacion oficial del dominio operativo;
- el arranque local quede documentado con pocos comandos claros;
- el legado quede aislado del runtime principal;
- la estructura del repo refleje responsabilidades reales;
- los smoke tests y suites minimas sigan pasando;
- un desarrollador nuevo entienda en minutos donde vive cada cosa.

## Tabla De Decisiones A Cerrar

### Decision 1

El backend oficial de `projects/sectors/assets/topology` sera:

- opcion recomendada: `next-backend`
- opcion alternativa: `core_backend` Python

### Decision 2

El admin FastAPI sera:

- UI interna temporal;
- BFF de operacion;
- app legacy a retirar.

### Decision 3

La API Python actual sera:

- legacy de consulta historica;
- wrapper temporal;
- parte del runtime oficial.

### Decision 4

El DTE sera:

- app separada;
- modulo opcional del mismo producto;
- linea experimental no integrada por ahora.

## Primer Backlog Ejecutivo

1. Reescribir el `README.md` para reflejar arquitectura real y estado actual.
2. Crear una ADR corta con la decision de backend oficial por dominio.
3. Inventariar superposicion entre `core_backend` y `next-backend`.
4. Diseñar la nueva estructura `apps/`, `infra/`, `docs/`.
5. Ejecutar la mudanza fisica minima sin cambiar comportamiento.
6. Aislar legacy y actualizar comandos de desarrollo.

## Prompt Base Para Trabajar En ChatGPT

```text
Estoy reorganizando un monorepo IoT que hoy mezcla varias lineas arquitectonicas.

Estado actual:
- Python sigue siendo el nucleo natural para ingesta, MQTT, storage, Alembic y procesos IoT.
- Existe una API Python legacy para consulta de datos.
- Existe un core backend Python con dominio operativo (projects, sectors, locations, assets, topology_links).
- Existe un next-backend en TypeScript/Next.js con APIs propias, servicios, repositorios, provisioning y canvas topologico.
- Tambien existe un modulo separado de Digital Twin Engine.

Verificaciones ya hechas el 2026-04-20:
- ./scripts/smoke_core.sh -> OK, 17 tests Python passed
- npm test en next-backend -> OK, 17 tests passed

Problema principal:
- El dominio operativo esta duplicado entre core_backend Python y next-backend TypeScript.
- Hay legado mezclado con runtime nuevo.
- La estructura del repo no refleja responsabilidades reales.

Decision recomendada:
- Mantener Python para ingesta, MQTT, storage, Alembic y backend IoT.
- Consolidar next-backend como implementacion oficial del dominio operativo moderno.
- Pasar core_backend Python a transicion controlada y luego retirarlo del runtime principal.
- Aislar la API Python legacy y las tablas/contratos legacy.

Quiero que me ayudes a:
1. definir la arquitectura objetivo final;
2. diseñar una nueva estructura de carpetas;
3. armar una matriz de migracion componente por componente;
4. identificar riesgos de la mudanza;
5. proponer un plan por fases con criterios de salida;
6. sugerir ADRs y cambios concretos de README/documentacion.

Trabaja con foco en reorganizacion arquitectonica, no en agregar features nuevas.
```

## Cierre

La reorganizacion no deberia empezar moviendo archivos a ciegas.

El primer paso correcto es cerrar la decision de arquitectura oficial por dominio. Despues de eso, la separacion fisica del repo y el aislamiento del legado pasan a ser trabajo mecanico y verificable.
