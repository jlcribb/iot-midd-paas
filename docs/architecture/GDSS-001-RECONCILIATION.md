# GDSS-001 — Reconciliación R1 y decisiones STEP 0

Fecha: 2026-10-01. Capacidad A1/C6. BASELINE_RECONCILIATION = PASS.
STEP_0_GATE = PASS. P1–P4 = RESOLVED.

## Evidencia
Checkout autorizado: /Users/joseluis/dev/iot-midd-paas-auth-work.
Branch main; HEAD ceafe7b08d803cb9da739ab6dd45c0adb3aa5f86; git status inicial vacío.
Alembic heads ejecutado con el entorno Python del checkout anterior: 0038 (head).
PostgreSQL: SELECT version_num FROM alembic_version -> 0038.
0038 revisa 0037. Docker inspect iotmw-topology-ui: este checkout -> /app.
El checkout anterior y sus cambios permanecen intactos. Su informe bloqueado se preserva como evidencia histórica, no como estado de esta ejecución.
La herramienta Python se reutiliza sin copiar código ni cambiar migraciones históricas.

## P1 — Provenance
P1_DECISION: tabla de artefactos hijos con discriminador de clase, FK obligatoria a versión y clave local única. Procedencia en registros asociados mediante FK real a versión y FK compuesta opcional a hijo; NULL en hijo significa procedencia propia de la versión.
P1_RATIONALE: un único supertipo gobernado permite integridad referencial real sin entity_type/entity_id polimórfico. Component/Variable/Parameter/Formula/Constraint/Boundary mantienen contratos separados.
P1_SCHEMA_IMPLICATION: claves compuestas (version_id, local_key) en hijos y referencias; cada fila de procedencia conserva fuente y clasificación; la agregación no reemplaza registros.

## P2 — Catálogo
P2_DECISION: definiciones inmutables desde creación con clave conceptual y revisión. Cada versión guarda definiciones exactas en su snapshot gobernado además de referencias de catálogo.
P2_RATIONALE: ni correcciones de catálogo ni sucesores cambian el significado histórico.
P2_SCHEMA_IMPLICATION: UNIQUE(conceptual_key, revision); UPDATE/DELETE prohibidos; firmas SI de siete exponentes enteros (fraccionarios fuera de esta fase); escala finita positiva y offset finito.

## P3 — Canonicalización
P3_DECISION: formula.input_refs es conjunto de dependencias UNORDERED; el orden posicional permanece en expression_source opaco.
P3_CANONICALIZATION_REGISTRY:
- identidad técnica, timestamps, lifecycle, eventos y predecesor: excluidos.
- model description, validity; child symbol, kind, label, description, typed fields; provenance kind/source/description/asserted_by/metadata; unit symbol/name/scale/offset/canonical_unit/dimension: SCALAR u objeto cuyas claves se ordenan.
- model children, provenance records, catalog snapshots: UNORDERED por representación canónica.
- input_refs, constraint refs, boundary included_components: UNORDERED referencias por clave local estable.
- output_ref y unit_ref: REFERENCE por clave semántica local, nunca UUID.
- metadata/validity JSON: objetos con claves ordenadas; arrays conservan orden ORDERED. No se interpreta su contenido.
- computational_role y epistemic_kind: SCALAR independientes.
P3_HASH_IMPLICATION: SHA-256 de JSON estable UTF-8; números finitos; rechazar campos desconocidos. Claves locales únicas entre los seis tipos, copiadas al sucesor.

## P4 — Autorización
P4_DECISION: el servicio Next reutiliza ControlActor, canAccessProject/getControlRoleForProject como infraestructura de identidad/scope (no lógica del motor), y exige OAuth. El core puro no importa auth ni DB.
P4_EXISTING_AUTHORIZATION_MAPPING: viewer sólo lectura; operator crear, editar draft, validar, promover experimental y crear sucesor; admin además aprobar, publicar y deprecar. Los permisos se calculan por proyecto, nunca por rol global cuando hay OAuth.
P4_SEPARATION_OF_AUTHORITY: crear no otorga publicar; no se introduce autenticación paralela. Se rechaza dev_fallback. No se exige persona distinta: el repositorio no establece ese requisito para esta capacidad. El límite de confianza es el servicio servidor con actor resuelto desde sesión.
Evidencia: docs/operations/project_control_governance.md; lib/auth/control-access.ts; lib/auth/control-auth-session.ts; project_control_memberships. OAuth sin membership carece de scope. Se conservan estos mecanismos.

## Límites
GDSS no importa simulation/canonical.ts pese a utilidad semejante: contiene dependencia de otro subsistema. SHA-256 y canonicalización tienen implementación propia mínima.
La nueva migración se determina después de reconciliación: 0039 sobre 0038. Al cierre se aplicó además 0040 para reforzar las declaraciones obligatorias: código y DB quedan en 0040, head único. Véase el [informe final](GDSS-001-FINAL-REPORT.md).
Persistencia public, UUID/TIMESTAMPTZ/JSONB, transacciones con lib/db/tx.ts; eventos propios append-only y auditoría iot_schema.auditoria en misma transacción.
Superficie de esta fase: servicio declarativo servidor, sin UI ni endpoints de ejecución.
