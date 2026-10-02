# GDSS-001 — Implementación declarativa

Capacidad A1 / C6. Estado vigente y evidencia: [informe final](GDSS-001-FINAL-REPORT.md).
Baseline, decisiones P1–P4 y reconciliación: [STEP 0 R1](GDSS-001-RECONCILIATION.md).
GDSS-001 es una fundación para capacidades futuras; no es un Digital Twin runtime.

## Superficie servidor

Código: `apps/topology-next/src/lib/gdss/core.ts` y `service.ts`.
Operaciones públicas: createModelIdentity, createDraftVersion, updateDraft, transition,
createSuccessor, getModel, getVersion y listVersions.
Se entrega servicio TypeScript de servidor; esta fase no agrega UI ni rutas HTTP.
Los consumidores servidor deben resolver el actor desde la sesión OAuth existente, nunca
desde un payload de usuario. Se reutilizan scope y roles por proyecto del sistema.

Viewer: lectura. Operator: crear, editar DRAFT, validar, promover a EXPERIMENTAL y crear sucesor.
Admin: además aprobar, publicar y deprecar. Se rechaza dev_fallback.
Crear no concede por sí solo publicación. No se introduce autenticación paralela.

## Contratos y almacenamiento

SystemModelIdentity conserva identidad lógica y proyecto. SystemModelVersion gobierna contenido,
lifecycle y versión. Component, Variable, Parameter, Formula, Constraint y Boundary son contratos
diferenciados que comparten una tabla de artefactos con discriminador y FK a versión.
getVersion materializa model_version_id en cada hijo; las ediciones reciben contenido para una
versión explícita y no admiten otra pertenencia dentro del payload.

El documento JSONB y sus proyecciones relacionales cambian atómicamente mediante trigger.
Las proyecciones no admiten DML directo. Referencias entre hijos usan claves compuestas
(model_version_id, symbol), impidiendo cruces entre versiones.
Cada hijo y versión conserva uno o más registros de procedencia con FK real. La agregación
mantiene fuentes heterogéneas; LITERATURE exige source_reference y no se resuelve externamente.

UnitDefinition tiene clave conceptual y revisión inmutable, symbol/name/scale/offset/
canonical_unit y firma dimensional de siete exponentes SI enteros. DimensionDefinition es
esa firma, incluida en snapshots y unidades inmutables. No hay catálogo mutable de dimensiones.
Corregir una definición requiere revisión nueva; las versiones guardan la referencia exacta.
Se valida compatibilidad declarativa: °C/K comparten dimensión; no se convierten fórmulas.

## Lifecycle, hash y auditoría

DRAFT → VALIDATED → EXPERIMENTAL → APPROVED → PUBLISHED → DEPRECATED.
Sólo DRAFT admite cambios. Desde VALIDATED se congela contenido, incluida procedencia,
catálogo referenciado y restricciones. Corregir requiere sucesor DRAFT con hijos propios.
El contenido del predecesor permanece intacto.

VALIDATED sólo acredita estructura y gobernanza de esta fase.
PUBLISHED ≠ SCIENTIFICALLY_TRUE; PUBLISHED ≠ CONTROL_READY; PUBLISHED ≠ ACTUATION_AUTHORIZED.

Canonicalización: claves de objetos ordenadas; colecciones children/units/provenance y conjuntos
de referencias sin orden incidental. formula.input_refs es un conjunto de dependencias;
metadata/validity y demás arrays semánticos conservan orden. expression_source es texto opaco.
No hay eval, exec, parser matemático ni ejecutor. computational_role y epistemic_kind son
independientes; MEASURED no es un enum adicional.

SHA-256 comprende contenido gobernado; excluye UUID/timestamps/lifecycle/eventos/predecesor.
Referencias por claves locales estables. Las transiciones posteriores conservan el hash.
Validación, congelamiento, transición, evento GDSS y auditoría iot_schema.auditoria se ejecutan
en la misma transacción. SQL verifica el hash contra la representación almacenada y su
equivalencia JSONB con el contenido; un constraint diferido exige evento al cerrar transacción.
Eventos append-only y UNIQUE(version,to_status) impiden duplicación.

## Migraciones y pruebas

0039 introduce las ocho tablas GDSS y controles de integridad.
0040 refuerza procedencia/declaraciones dimensionales ante SQL directo.
Ambas extienden 0038; no se reescribieron migraciones anteriores.

Desde apps/topology-next:
```bash
GDSS_DB_TEST=1 npm test -- tests/unit/gdss.test.ts tests/integration/gdss.persistence.test.ts
npm run typecheck
```

Las pruebas GDSS usan proyectos en transacciones con rollback y savepoints. Los dos fixtures
de dominio usan el mismo servicio. Las pruebas verifican categorías, hash, lifecycle,
inmutabilidad, FK, procedencia, permisos, fallos inyectados, imports y superficie pública.
Las reservas 07/08/13/15/17/20 permanecen documentales, sin implementaciones ficticias.

La suite E2E completa del repositorio requiere la red Docker y el runner existente; véanse
comandos y resultados en el informe. Ese runner no es dependencia del núcleo GDSS.

## Fronteras

Sin simulación, DTE, Control Engine, MQTT, telemetría acoplada, recomendaciones o actuación.
Los imports compartidos control-access/ControlActor son infraestructura de identidad/scope,
no lógica del motor paramétrico. No se toca first_order.py ni se usa como motor GDSS.
