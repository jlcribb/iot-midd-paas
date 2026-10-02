# GDSS-001 — Informe final para ChatGPT

Fecha de cierre: 2026-10-02.
Mandatos: MIDD-GDSS-P001 y MIDD-GDSS-P001-R1; cierre autorizado por el usuario.
**Estado: COMPLETED_GOVERNED_DECLARATIVE_SYSTEMS_FOUNDATION_WITH_WARNINGS**

La fundación declarativa está implementada, migrada y verificada. La regresión completa
incluye los dos E2E antes fallidos: **301 tests aprobados, 0 fallidos, 0 omitidos, 96 archivos**.
No hubo push ni commit. Las advertencias no bloqueantes se detallan en H.

## A. Baseline y recuperación

| Campo | Intento anterior preservado | Baseline autoritativo R1 |
|---|---|---|
| Checkout | /Users/joseluis/dev/iot-midd-paas | /Users/joseluis/dev/iot-midd-paas-auth-work |
| Branch | main | main |
| HEAD | 1bf4a1ea327723f25c1f9bca0a170aa32ec06a9f | ceafe7b08d803cb9da739ab6dd45c0adb3aa5f86 |
| Alembic inicial del código | 0008 | 0038, un único head |
| Alembic inicial de PostgreSQL | 0038 | 0038 |
| Working tree inicial | Sucio, preservado | Limpio |
| Runtime | No era el checkout montado | Docker monta este checkout en /app |

Se verificaron branch, HEAD, status, migración 0038, cadena única, alembic_version y montajes.
El código autoritativo contiene las capacidades de gobernanza observadas y roles por proyecto.
BASELINE_RECONCILIATION = PASS. STEP_0_GATE = PASS.
No se usó stamp, downgrade, reescritura de migraciones ni merge del checkout anterior.
Su [informe bloqueado](GDSS-001-STEP-0-REPORT.md) se conserva como evidencia histórica.

## B. Decisiones P1–P4

Decisiones y evidencia completas: [reconciliación](GDSS-001-RECONCILIATION.md).

| Decisión | Resultado |
|---|---|
| P1 — Provenance | RESOLVED. Supertipo relacional gdss_artifact con discriminador y pertenencia a versión; procedencia con FK real a versión y FK compuesta a hijo cuando corresponde. Múltiples fuentes preservadas. |
| P2 — Catálogo | RESOLVED. Clave conceptual y revisión inmutable de unidad, firma SI y snapshots por versión. Correcciones requieren nueva revisión. |
| P3 — Canonicalización | RESOLVED. input_refs es conjunto UNORDERED de dependencias; arrays semánticos conservan orden; referencias por claves locales; SHA-256. |
| P4 — Autorización | RESOLVED. OAuth, scope y roles por proyecto existentes. Operator crea/edita/valida/promueve experimental; admin además aprueba/publica/depreca. Crear no concede publicar. |

No fue necesario acoplar GDSS al motor de control, al DTE ni a actuaciones.
Los nombres ControlActor/control-access corresponden a infraestructura compartida de
identidad/scope, no a lógica del parametric-control-engine.

## C. Implementación

| Entregable | Archivo relativo al checkout autoritativo |
|---|---|
| Contratos, validación, dimensiones, canonicalización/hash | apps/topology-next/src/lib/gdss/core.ts |
| Servicio transaccional, RBAC, lifecycle, auditoría, sucesores | apps/topology-next/src/lib/gdss/service.ts |
| Persistencia, FK, inmutabilidad y eventos | infra/migrations/alembic/versions/0039_gdss_foundation.py |
| Refuerzo de declaraciones requeridas en SQL directo | infra/migrations/alembic/versions/0040_gdss_required_declarations.py |
| Fixtures Hydroponic/Thermal | apps/topology-next/tests/fixtures/gdss.ts |
| Pruebas de contratos y fronteras | apps/topology-next/tests/unit/gdss.test.ts |
| Pruebas PostgreSQL y atomicidad | apps/topology-next/tests/integration/gdss.persistence.test.ts |
| Aislamiento del E2E existente para cerrar regresión | apps/topology-next/tests/integration/experiment-batch.e2e.test.ts |

Contratos implementados: SystemModelIdentity, SystemModelVersion, Component, Variable,
Parameter, Formula, Constraint, Boundary, Provenance, UnitDefinition, DimensionDefinition
y LifecycleEvent. No hay versionado/lifecycle independiente de fórmulas.

Superficie entregada: servicio servidor TypeScript con createModelIdentity, createDraftVersion,
updateDraft, transition, createSuccessor, getModel, getVersion y listVersions.
No se agregó UI ni API HTTP: la entrega es la opción service permitida por el mandato.
Un adaptador HTTP futuro deberá obtener el actor desde la sesión, nunca desde el payload.

Las versiones contienen hijos propios. La persistencia materializa model_version_id y FK
compuestas; getVersion expone esa pertenencia. Las fórmulas son texto opaco. Los ejes
computational_role/epistemic_kind son independientes.

DRAFT es el único estado editable. Validación, hash, freeze, transición, evento y auditoría
se ejecutan transaccionalmente. Un constraint diferido impide transición sin evento.
Eventos append-only y unicidad por versión/estado destino impiden duplicación.
El sucesor conserva procedencia y reconstruye referencias sin modificar el original.

Ocho tablas: gdss_identity, gdss_version, gdss_artifact, gdss_reference, gdss_provenance,
gdss_unit_definition, gdss_unit_reference, gdss_lifecycle_event.
Las dimensiones se representan por firmas de siete exponentes SI enteros, incluidas en
definiciones inmutables de unidad y snapshots; no se introdujo catálogo mutable adicional.

Guía de uso y alcance: [implementación](GDSS-001-IMPLEMENTATION.md).

## D. Matriz de invariantes

U = apps/topology-next/tests/unit/gdss.test.ts.
D = apps/topology-next/tests/integration/gdss.persistence.test.ts.
Todos los tests citados forman parte de la corrida final aprobada. PASS está limitado
a GDSS-001; no implica validación científica ni cumplimiento de fases futuras.

| ID | Estado | Evidencia |
|---|---|---|
| GDS-INV-01 | PASS | U: preserves independent computational/epistemic categories |
| GDS-INV-02 | PASS | U: OBSERVED/PREDICTED distintos; MEASURED rechazado como enum |
| GDS-INV-03 | PASS | U: has a closed declarative surface; keeps expressions opaque |
| GDS-INV-04 | PASS | U: esquema/superficie cerrados sin contratos runtime |
| GDS-INV-05 | PASS | U: AST de dependencias/ejecución y superficie sin actuación |
| GDS-INV-06 | PASS | D: persists, freezes, audits and versions, para ambos dominios; sucesores y pertenencia de hijos |
| GDS-INV-07 | STRUCTURALLY_RESERVED | No resultados ni SimulationRun implementados |
| GDS-INV-08 | STRUCTURALLY_RESERVED | No runs; no se afirma reproducibilidad de simulación |
| GDS-INV-09 | PASS — parcial declarativo | U: compares SI signatures; D: rejects SQL documents missing mandatory provenance or dimension semantics; sin álgebra |
| GDS-INV-10 | PASS | U: requires source identity; D: preserves mixed provenance and catalog history |
| GDS-INV-11 | PASS | D: AI_PROPOSED conservado hasta PUBLISHED |
| GDS-INV-12 | PASS | U: superficie cerrada; D: transiciones ilegales/publicación no autorizada rechazadas |
| GDS-INV-13 | STRUCTURALLY_RESERVED | No PhysicalBinding |
| GDS-INV-14 | PASS | D: LITERATURE/EMPIRICAL/AI_PROPOSED permanecen identificables |
| GDS-INV-15 | STRUCTURALLY_RESERVED | No resultados históricos de simulación |
| GDS-INV-16 | PASS | U: AST de vocabulario/imports; ambos fixtures usan el mismo core que no los importa |
| GDS-INV-17 | STRUCTURALLY_RESERVED | Sin runs históricos; D sí verifica inmutabilidad del predecesor actual |
| GDS-INV-18 | PASS | U: COUNTERFACTUAL y OBSERVED separados |
| GDS-INV-19 | PASS | U: does not promote calibrated provenance or confer scientific validity |
| GDS-INV-20 | STRUCTURALLY_RESERVED | Sin DigitalTwin runtime ni binding físico |
| GDS-INV-21 | PASS | U: acreditación científica extra rechazada; D: lifecycle no eleva procedencia |
| GDS-INV-22 | PASS | U: ejes independientes; D/0040: categorías declarativas verificadas también en SQL |

Otras pruebas: fallos de hash, UPDATE, evento y auditoría con rollback; transición sin evento;
hash incorrecto; cambios en contenido congelado; edición directa de proyecciones; FK local;
catálogo inmutable; distinta identidad técnica con igual hash semántico; secuencia semántica
reordenada con hash distinto.

## E. Frontera arquitectónica y verificación separada

| Capacidad/dependencia en GDSS | Resultado |
|---|---|
| Control Engine | NONE |
| DTE | NONE |
| MQTT | NONE |
| Actuación física | NONE |
| Simulación | NONE |
| Telemetry binding | NONE |

Evidencia: allowlist AST de imports de todos los archivos GDSS, ausencia de ejecución dinámica,
esquemas estrictos y lista cerrada de métodos. Los imports del core son node:crypto y zod;
el servicio agrega sólo DB, errores e infraestructura compartida de autorización.

La verificación separada utilizó DML SQL que evita el servicio, comprobación SHA-256 de
PostgreSQL, FK/constraints diferidos e inspección AST. La corrida integral en Docker verificó
además la regresión externa al módulo. Fue ejecutada en esta misma sesión, sin afirmar revisión
por una persona o agente externo. La independencia de los controles respecto del servicio
no equivale a una auditoría organizacional independiente.

PUBLISHED ≠ SCIENTIFICALLY_TRUE.
PUBLISHED ≠ CONTROL_READY.
PUBLISHED ≠ ACTUATION_AUTHORIZED.

## F. Regresión y migraciones

| Verificación | Resultado |
|---|---|
| Baseline Next, antes de código GDSS | 268 PASS, 8 SKIPPED; 87 archivos PASS, 7 SKIPPED |
| Typecheck baseline | PASS |
| Build HEAD inicial aislado con git archive, --webpack | PASS |
| Build implementación Next/Turbopack, salida aislada | PASS |
| Typecheck de cierre, después del arreglo del test | PASS, exit 0 |
| Python tests/unit y parametric-control-engine/tests | 190 PASS |
| Nuevas pruebas GDSS | 25 PASS: 13 unitarias + 12 PostgreSQL |
| Regresión previa de persistencia sin runners | 299 PASS, 2 SKIPPED |
| **Regresión final, todos los runners habilitados** | **301 PASS, 0 FAIL, 0 SKIPPED; 96 archivos PASS; exit 0** |
| Upgrade 0038 → 0039 → 0040 | PASS |
| Alembic head de código y DB, comprobación de cierre | 0040 / 0040, único |
| gdss_version tras pruebas | 0 filas |
| Proyectos llamados M65 isolated E2E tras cierre | 0 filas |
| git diff --check | PASS |

La primera ejecución Python falló en colección por PYTHONPATH incompleto. La correcta,
PYTHONPATH=src:apps/parametric-control-engine/src, pasó 190 pruebas. No hubo cambio de
código Python productivo para resolverlo.

### Resolución de los dos E2E pendientes

- El endpoint /internal/shadow-control-evaluations ya existía en
  src/iot_middleware/services/simulation_replay_api.py. El proceso montado estaba desactualizado.
  Se reinició únicamente simulation-replay-runner; no se añadió endpoint ni lógica.
- experiment-batch.e2e.test.ts usaba un proyecto compartido. El generador podía reutilizar
  candidatos con referencias de otras ejecuciones y su cleanup fallaba por FK.
  Ahora crea proyecto UUID propio con control deshabilitado, reutiliza ese scope en todo el test
  y realiza cleanup en transacción limitado a su proyecto. No se debilitaron aserciones.
- Se ejecutó la suite dentro de Docker, donde el nombre simulation-replay-runner es resoluble.
  No se expuso un puerto ni se añadió un servicio.

Comando final exacto:

```bash
docker exec -w /app/apps/topology-next \
  -e GDSS_DB_TEST=1 -e M6_E2E_DB=1 -e M63A_E2E_DB=1 \
  -e M64_E2E_DB=1 -e M65_E2E_DB=1 -e M65_E2E_RUNNER=1 \
  -e M72_E2E_RUNNER=1 iotmw-topology-ui npm test -- --reporter=dot
```

Salida final abreviada capturada:

```text
Test Files  96 passed (96)
     Tests  301 passed (301)
  Start at  20:46:35
  Duration  26.51s
exit_code: 0
```

El horario es el emitido por el contenedor. Los mensajes de UnauthorizedError/ZodError en
stderr corresponden a tests negativos aprobados; no son fallos de la corrida.

Las migraciones se ejecutaron por el runtime oficial:

```bash
docker exec -e PYTHONPATH=/app/src iotmw-ingestor \
  python -m alembic -c infra/migrations/alembic.ini upgrade head
```

No se modificó ninguna migración 0001..0038. 0040 se agregó después de aplicar 0039 para
reforzar declaraciones obligatorias sin reescribir historia.

## G. Git y artefactos

HEAD inicial y final: ceafe7b08d803cb9da739ab6dd45c0adb3aa5f86.
Branch: main. Commits creados: ninguno. Push: no realizado.
Working tree final: archivos nuevos GDSS sin commit y una modificación acotada del E2E existente.

Archivos atribuibles:
- apps/topology-next/src/lib/gdss/core.ts
- apps/topology-next/src/lib/gdss/service.ts
- apps/topology-next/tests/fixtures/gdss.ts
- apps/topology-next/tests/unit/gdss.test.ts
- apps/topology-next/tests/integration/gdss.persistence.test.ts
- apps/topology-next/tests/integration/experiment-batch.e2e.test.ts
- infra/migrations/alembic/versions/0039_gdss_foundation.py
- infra/migrations/alembic/versions/0040_gdss_required_declarations.py
- docs/architecture/GDSS-001-ADR.md
- docs/architecture/GDSS-001-CONTRACTS.md
- docs/architecture/GDSS-001-PERSISTENCE.md
- docs/architecture/GDSS-001-INVARIANTS.md
- docs/architecture/GDSS-001-IMPLEMENTATION-PLAN.md
- docs/architecture/GDSS-001-OPERATIONAL-PROMPT.md
- docs/architecture/GDSS-001-STEP-0-REPORT.md
- docs/architecture/GDSS-001-RECONCILIATION.md
- docs/architecture/GDSS-001-RECOVERY-PROMPT.md
- docs/architecture/GDSS-001-IMPLEMENTATION.md
- docs/architecture/GDSS-001-FINAL-REPORT.md

El build había agregado inclusiones temporales a tsconfig.json: se retiraron sólo esos cambios.
Su salida fue preservada fuera del checkout en
/private/tmp/gdss-baseline.0vL9Db/verification-build.
La copia del HEAD inicial para comparación también quedó en esa carpeta temporal.

Los documentos finales que no pudieron guardarse por el límite de uso anterior quedaron
guardados durante este cierre. El bloqueo de escritura está resuelto.

## H. Hallazgos remanentes

- BLOCKING: ninguno para el alcance GDSS-001 probado.
- NON_BLOCKING / datos históricos de tests: la base conserva 31 sesiones con created_by
  prefijado m65-e2e- de ejecuciones anteriores en proyectos compartidos. No se puede atribuir
  toda esa población exclusivamente a esta solicitud; no se borró. El nuevo fixture aislado
  y las pruebas GDSS sí quedaron sin residuos. Este dato motiva el estado WITH_WARNINGS.
- NON_BLOCKING / alcance: se entrega servicio servidor sin UI/HTTP; dimensiones enteras y
  compatibilidad declarativa. No se afirma inferencia algebraica ni validación científica.
- PRE_EXISTING, resuelto para verificación: proceso del runner desactualizado y test compartido.
- FUTURE_PHASE: SimulationRun, solver, telemetría, calibración, gemelo vinculado y actuación.

El cierre no requiere push ni commit. No quedan peticiones de implementación, regresión o
documentación pendientes dentro del alcance autorizado.
