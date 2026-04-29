# Topology Canvas Review (midd IoT)

## 1. Decisiones de arquitectura UI

- Se implementó un **workspace visual** en la página principal con 3 paneles:
  - izquierda: navegación, búsqueda, filtros y paleta de creación,
  - centro: canvas interactivo,
  - derecha: inspector contextual.
- Estado UI centralizado con **Zustand** (`topology-store`) para evitar un componente monolítico y facilitar evolución.
- Composición modular en `src/components/topology/*`.

## 2. Librería elegida

Se eligió **React Flow (@xyflow/react)** porque ofrece de forma nativa:

- drag & drop de nodos,
- pan/zoom,
- selección de nodos y edges,
- creación visual de conexiones (`onConnect`),
- nodos y edges personalizados,
- minimapa y controles de navegación,
- integración natural con React/TypeScript.

Es una base robusta para pasar de CRUD a editor operativo.

## 3. Jerarquía vs topología (separación explícita)

- **Jerarquía física/operativa** (`assets.parent_asset_id`):
  - se representa como edges tipo `hierarchy`, estilo punteado y etiqueta `parent`.
- **Topología explícita** (`topology_links`):
  - se representa como edges `topologyEdge`, con relación visible (`reads`, `controls`, etc.).

La UI no mezcla ambos conceptos; los renderiza como capas distintas dentro del mismo canvas.

## 4. Persistencia de layout

Se implementó persistencia formal con migraciones separadas:

- `migrations/007_topology_views.sql`
- `migrations/008_topology_node_layouts.sql`
- `migrations/009_topology_link_layouts.sql`

Nuevos endpoints:

- `GET/POST /api/projects/:projectId/topology/views`
- `GET/PATCH /api/topology-views/:id`
- `GET/PUT /api/topology-views/:id/layout`

El layout queda estable entre recargas por vista (`logical`, `physical`, `geographic`).

## 5. Interacciones listas

- selección de nodo y enlace,
- mover nodos y guardar layout,
- crear sector,
- crear nodo programable,
- crear sensor/actuador hijo de nodo,
- conectar visualmente nodos/sectores para crear `topology_links`,
- editar y eliminar (lógico) desde inspector,
- auto layout semántico inicial (sector -> nodo -> dispositivos),
- centrar canvas, validar inconsistencias, filtros por tipo/estado.

## 6. Validación visual e inconsistencias

Se señalan visualmente:

- sector vacío,
- sensor/actuador sin `parent_asset_id`,
- nodo programable sin dispositivos,
- estados operativos críticos (`offline`, `fault`, `maintenance`),
- links topológicos con referencias inválidas.

## 7. Riesgos y siguientes mejoras

- Mejorar UX de creación de links con modal formal de `relation_type` (hoy usa prompt).
- Agregar selección múltiple y edición batch.
- Completar vista geográfica con geolocalización real y capas GIS.
- Añadir tests E2E de interacción canvas + persistencia de layout.
- Agregar políticas de permisos por modo (operación/diseño) a nivel backend.
