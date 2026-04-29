# Backend Core Midd IoT - Revisión Integral

## 1) Flujo completo implementado

El backend core ahora expone un flujo end-to-end sobre `public` (`projects`, `sectors`, `locations`, `assets`, `topology_links`) con capa por responsabilidades.

Estado actual de exposicion:

- superficie transicional: `/api/transition/core-backend/*`
- ya no forma parte de la superficie normal `/api/*` del admin

- Validación estructural (`schemas.py`, Pydantic).
- Repositorios SQL (`repositories.py`).
- Reglas de negocio (`services.py`).
- API REST (`router.py`) integrada en `apps/admin-fastapi/main.py` bajo `/api/transition/core-backend/*`.

Flujo operativo cubierto:

1. Crear proyecto: `POST /api/transition/core-backend/projects`
2. Crear location opcional de sector: `POST /api/transition/core-backend/locations`
3. Crear sector: `POST /api/transition/core-backend/sectors`
4. Crear location opcional de nodo: `POST /api/transition/core-backend/locations`
5. Crear nodo programable: `POST /api/transition/core-backend/assets` (`asset_type=programmable_node`)
6. Crear sensor/actuador hijo con `parent_asset_id`: `POST /api/transition/core-backend/assets`
7. Crear topología:
   - `POST /api/transition/core-backend/topology-links` (`contains`, `reads`, `controls`, etc.)
8. Consultar árbol y topología:
   - `GET /api/transition/core-backend/assets/{id}/tree`
   - `GET /api/transition/core-backend/projects/{projectId}/topology`
9. Consultar offline:
   - `GET /api/transition/core-backend/projects/{projectId}/assets/offline?offline_minutes=15`
10. Editar entidades:
    - `PATCH /api/transition/core-backend/projects/{id}`
    - `PATCH /api/transition/core-backend/sectors/{id}`
    - `PATCH /api/transition/core-backend/locations/{id}`
    - `PATCH /api/transition/core-backend/assets/{id}`
    - `PATCH /api/transition/core-backend/topology-links/{id}`

Además se implementó provisioning transaccional:

- `POST /api/transition/core-backend/projects/{projectId}/provisioning/node-bundle`
  - Crea nodo + hijos + links topológicos en una sola transacción.

## 2) Validaciones de negocio aplicadas

### Projects
- `name` obligatorio no vacío.
- `status` restringido al enum del DDL.

### Sectors
- Proyecto debe existir.
- `location_id` debe existir si se informa.
- No duplicar `name` en el mismo proyecto.
- No duplicar `code` en el mismo proyecto (si aplica).
- Soft delete seguro (`DELETE /api/transition/core-backend/sectors/{id}`): marca sector inactivo + desactiva assets + links asociados.

### Locations
- `name` obligatorio.
- `latitude/longitude` en par.
- `metadata` debe ser objeto JSON.

### Assets
- Proyecto y sector deben existir y ser coherentes.
- `parent_asset_id`:
  - debe existir,
  - mismo proyecto y sector,
  - tipo de padre permitido,
  - evita autorreferencia.
- Normalización MAC (`trim + lower`).
- `metadata` debe ser objeto JSON.
- Soft delete seguro (`DELETE /api/transition/core-backend/assets/{id}`):
  - retira nodo raíz y desactiva descendencia en transacción,
  - desactiva links topológicos relacionados.

### Topology links
- Exactamente una fuente y un destino (asset/sector).
- Validación de pertenencia al mismo proyecto.
- Evita self-link inválido.
- Prevención de duplicados semánticos exactos.
- `relation_type` y `status` validados contra enums.

## 3) Integridad, transacciones y manejo de errores

Operaciones transaccionales implementadas a nivel servicio (una sesión DB por operación):

- Provisioning compuesto (`node-bundle`).
- Soft delete de sector (sector + assets + topology).
- Soft delete de asset/subtree + desactivación de links.
- Updates estructurales con validación previa.

Manejo de errores:

- `400`: payload inválido / regla de validación (`validation_error`).
- `404`: entidad inexistente (`not_found`).
- `409`: conflicto de integridad/duplicado (`integrity_conflict`).
- `500`: error interno.

Se mapearon errores de SQLAlchemy/PostgreSQL a errores de dominio (`errors.py`) y se normalizó el `RequestValidationError` de FastAPI a `400` en `apps/admin-fastapi/main.py`.

## 4) Huecos detectados y mejoras realizadas

Hueco detectado:
- El DDL base no tenía bandera explícita de actividad para `sectors` y `locations`, lo que complica borrado lógico consistente y filtros eficientes.
- En la primera iteración de soft-delete, podían quedar links topológicos activos entre assets de un sector inactivado.
- Archivar proyecto no estaba desactivando automáticamente todo su alcance operativo (sectors/assets/links).
- En provisioning transaccional (`node-bundle`), faltaban defaults explícitos de columnas opcionales para inserts internos.

Mejora implementada como migración separada:
- `alembic/versions/0006_add_is_active_flags.py`
  - agrega `is_active boolean` en `sectors` y `locations`,
  - backfill desde `metadata.is_active`,
  - índices `ix_sectors_is_active` y `ix_locations_is_active`.

No se modificó el DDL base (`001_core_schema.sql` / `0004_core_schema_public.py`), se extendió por migración incremental.

Correcciones aplicadas en capa de servicios/repositorios:
- Soft-delete de sector ahora inactiva también links que referencian assets del sector.
- Soft-delete de asset ahora inactiva links de todo el subárbol, no solo del nodo raíz.
- `status=archived` en proyecto desactiva sectors, assets y topology links del proyecto.
- Repositorios `create` para assets/topology completan valores opcionales para evitar fallas de bind.

## 5) Checklist final de integridad

- [x] Creación de proyecto
- [x] Creación de sector
- [x] Creación de nodo programable
- [x] Creación de sensor/actuador
- [x] Relación padre-hijo (`parent_asset_id`)
- [x] Relación topológica (`topology_links`)
- [x] Consulta de árbol (`/assets/{id}/tree`)
- [x] Consulta de topología (`/projects/{id}/topology`)
- [x] Consulta de offline assets
- [x] Consistencia proyecto/sector/asset/link en servicios y DB

## 6) Próxima iteración recomendada

1. Tests de integración contra PostgreSQL real para constraints/triggers del DDL.
2. Endpoint de reasignación estructural explícita (mover asset entre sectores con reconfirmación de topología).
3. Auditoría de cambios core en tabla de eventos de dominio.
4. Paginación y filtros avanzados en listados de assets/topología.
