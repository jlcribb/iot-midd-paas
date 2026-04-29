# Backend Integrity Review (midd IoT)

## 1) Flujo completo implementado

Flujo operativo cubierto con services + route handlers + validación Zod:

1. `POST /api/projects` crea proyecto.
2. `POST /api/locations` crea ubicación opcional.
3. `POST /api/sectors` crea sector dentro de proyecto.
4. `POST /api/locations` crea ubicación opcional para nodo.
5. `POST /api/assets` crea nodo programable (`asset_type=programmable_node`).
6. `POST /api/assets` crea sensor/actuador con `parent_asset_id`.
7. `POST /api/topology-links` crea relaciones topológicas.
8. `GET /api/assets/:id/tree` consulta árbol jerárquico.
9. `GET /api/projects/:projectId/topology` consulta topología del proyecto.
10. `GET /api/projects/:projectId/assets/offline` consulta activos offline.
11. `PATCH` en entidades aplica updates parciales con reglas de integridad.

Adicional:

- `POST /api/provisioning/bootstrap-node-with-devices` implementa alta compuesta transaccional:
  - sector (nuevo o existente),
  - location opcional,
  - nodo,
  - hijos sensor/actuador,
  - links mínimos (`contains`, `reads`, `controls`).

## 2) Validaciones estructurales (Zod)

- `create/update` schemas para `projects`, `sectors`, `locations`, `assets`, `topology-links`.
- updates parciales con rechazo de payload vacío.
- UUID, enums, rangos y coherencia lat/lon.
- fuente/target único en links topológicos.
- schema compuesto `bootstrapNodeWithDevicesSchema`.

## 3) Validaciones de negocio (services)

- `ProjectService`: nombre requerido, estado válido.
- `SectorService`:
  - proyecto existente,
  - `location_id` válido,
  - nombre único por proyecto,
  - código único por proyecto.
- `AssetService`:
  - proyecto/sector existentes y coherentes,
  - `location_id` válido,
  - `subtype` y `name` requeridos,
  - padre existente, mismo proyecto/sector, no autorreferencia,
  - restricción de tipos:
    - contenedores permitidos: `programmable_node|gateway|relay_module|power_unit`,
    - tipos no permitidos como hijo: `programmable_node|gateway|power_unit`,
  - normalización MAC,
  - duplicados por `code`, `serial_number`, `mac_address`,
  - bloqueo de cambios de sector con hijos o con links topológicos de sector.
- `TopologyService`:
  - proyecto existente,
  - source/target válidos y dentro del mismo proyecto,
  - rechazo de self-link inválido,
  - rechazo de duplicado exacto.

## 4) Integridad reforzada y transacciones

Transacciones implementadas:

- `ProvisioningService.bootstrapNodeWithDevices` (alta compuesta).
- `SectorService.softDelete` (baja lógica sector + assets + topology).
- `AssetService.deleteSafe` (baja lógica en cascada sobre subárbol + topology).
- `ProjectService.update` cuando archiva proyecto (desactivación relacionada).

Manejo de errores uniforme:

- `400` validación estructural/negocio.
- `404` entidad inexistente.
- `409` conflicto de integridad/duplicados.
- `500` error interno.

## 5) Huecos detectados en schema base y mejoras propuestas

Sin modificar `001_core_schema.sql`, se proponen migraciones separadas:

- `migrations/005_enforce_assets_sector_project_consistency.sql`
  - agrega trigger para garantizar que `assets.sector_id` pertenezca al mismo `project_id`.
- `migrations/006_prevent_assets_parent_cycles.sql`
  - agrega trigger para bloquear ciclos jerárquicos por `parent_asset_id`.

Riesgos que persisten (siguiente iteración):

- falta endpoint dedicado para “reasignación estructural” (move seguro de subárbol + recomposición de topology en una sola operación).
- falta estrategia explícita de versionado de topología (auditoría histórica de cambios complejos).
- tests actuales son unitarios; falta suite de integración contra PostgreSQL real con fixtures SQL.

## 6) Checklist de cobertura

- [x] creación de proyecto
- [x] creación de sector
- [x] creación de location
- [x] creación de nodo programable
- [x] creación de sensor
- [x] creación de actuador
- [x] vínculo padre-hijo
- [x] vínculo topológico
- [x] consulta de hijos
- [x] consulta de árbol
- [x] consulta de topología
- [x] consulta de offline assets
- [x] transacciones compuestas
- [x] validación de integridad en services
- [x] manejo uniforme de errores HTTP
- [x] tests mínimos solicitados (14 casos)

## 7) Auto-revisión final

### Qué quedó cubierto

- arquitectura por capas (`db`, `repositories`, `services`, `validators`, `api handlers`, `errors`, `tests`).
- separación explícita entre jerarquía (`parent_asset_id`) y topología (`topology_links`).
- flujo completo de alta/vinculación/consulta con endpoint compuesto transaccional.

### Reglas de integridad reforzadas

- coherencia proyecto-sector-asset.
- restricciones de tipo padre/hijo.
- prevención de duplicados de negocio.
- control de cambios estructurales con riesgo de inconsistencia.

### Riesgos remanentes

- ausencia de pruebas E2E con DB real y datos de borde.
- ausencia de política de permisos/autorización (fuera de alcance de esta iteración).

### Migraciones sugeridas

- `005_enforce_assets_sector_project_consistency.sql`
- `006_prevent_assets_parent_cycles.sql`

### Próxima iteración recomendada

- agregar pruebas de integración con PostgreSQL real (containers/CI).
- crear endpoint transaccional de “move subtree + reconcile topology”.
- agregar observabilidad (tracing + métricas por endpoint y transacción).
