# GDSS-001 — Step 0 evidence / 2026-10-01

Status: `BLOCKED_BY_ARCHITECTURAL_CONTRADICTION`

El mandato MIDD-GDSS-P001 fue recibido para ejecución. El plan v0.1 queda aprobado según su baseline explícito. La puerta STEP 0 no pasa: el checkout asignado y el runtime local corresponden a baselines diferentes de persistencia y autorización. Esto no refuta el diseño GDSS; impide elegir silenciosamente cuál gobernanza existente debe preservar la implementación.

## A. Baseline y evidencia

| Evidencia | Resultado |
|---|---|
| Workspace asignado | `/Users/joseluis/dev/iot-midd-paas` |
| Branch | `main` |
| HEAD inicial y final | `1bf4a1ea327723f25c1f9bca0a170aa32ec06a9f` |
| `./venv/bin/alembic -c infra/migrations/alembic.ini heads` | `0008 (head)` |
| `SELECT version_num FROM alembic_version` en contenedor `postgresql`, DB `iot_middleware` | `0038` |
| Montaje de `iotmw-topology-ui` y `control-engine-worker` obtenido con `docker inspect` | `/Users/joseluis/dev/iot-midd-paas-auth-work -> /app` |
| HEAD de ese otro checkout, inspección sólo lectura | `ceafe7b08d803cb9da739ab6dd45c0adb3aa5f86`, branch `main` |
| Migración 0038 del otro checkout | `revision = "0038"`, `down_revision = "0037"` |

El workspace asignado sólo tiene ramas locales/remotas `main` y `origin/main`; su historial local de migraciones no contiene la cadena desplegada posterior a 0008. No se ejecutó fetch ni se cambió de checkout.

La base contiene, entre otras, `control_governed_deployment_authorizations`, `control_governed_physical_actuation_authorizations`, `control_governed_control_loop_enablement_authorizations` y `control_simulation_runs`. Sus implementaciones no están en este checkout. El otro checkout contiene contratos y validadores de esas capacidades. Además su `control-access.ts` incorpora `getControlRoleForProject` y `actor.project_roles`; el archivo equivalente aquí no los contiene. P4 no puede cerrarse contra la gobernanza desplegada usando sólo el baseline asignado.

El working tree ya estaba sucio: cambios de UI/topología, DTO/repositorio/validadores de proyecto, tests, configuración Next/TypeScript, artefactos `.next`, cachés, logs, documentos y capturas. Se preservaron. No se hicieron commits, push, checkout, merge, stamp, downgrade ni escrituras en PostgreSQL.

## B. Reconocimiento y P1–P4

Convenciones verificadas en el workspace:

- Alembic usa SQL PostgreSQL mediante `op.execute`; migraciones 0007 y 0008 forman parte de una cadena única. UUID, JSONB y TIMESTAMPTZ aparecen en las tablas operacionales.
- Runtime Python mantiene modelos SQLAlchemy en `src/iot_middleware/models`; Next usa `pg`, repositorios y servicios, con Zod y rutas API. `src/lib/db/tx.ts` implementa BEGIN/COMMIT/ROLLBACK sobre una conexión.
- Auditoría operacional: `control-policy-audit.repository.ts` recibe `SqlExecutor` y escribe en `iot_schema.auditoria`; ese patrón permite compartir transacción.
- Autenticación: NextAuth Google/GitHub, sesiones JWT y `control-auth-session.ts`. Autorización local: viewer/operator/admin y scope de proyectos. El runtime montado tiene mecanismos adicionales por proyecto que deben revisarse en el baseline elegido.
- Tests Next: Vitest `tests/**/*.test.ts`; Python: pytest, suite core mediante `scripts/smoke_core.sh`.
- `stableJsonStringify` existe en `control-policy-governance.ts`: ordena claves de objetos y conserva arrays. No se reutilizará importando lógica de control en GDSS. La búsqueda de `createHash`/`sha256` en fuentes inspeccionadas no encontró una utilidad compartida de hashing.
- Fronteras inspeccionadas: migración 0007, `src/iot_middleware/services/control_engine_worker.py`, benchmark `apps/parametric-control-engine/src/parametric_control_engine/simulation/first_order.py`, DTE experimental bajo `src/iot_middleware/dte`. DTE admite modos SIMULATION/HYBRID/REAL e infraestructura MQTT. Las nuevas tablas de actuación existen en la base pero su código corresponde al otro checkout.

| Decisión | Propuesta de reconocimiento | Estado |
|---|---|---|
| P1 | Relaciones explícitas por entidad propietaria y FK reales para registros de procedencia múltiples; evitar owner polimórfico sin FK. El esquema concreto depende del baseline confirmado. | Pendiente; no migración |
| P2 | Clave conceptual más revisión inmutable de unidad/dimensión; referencia exacta desde cada versión. | Pendiente de especificación persistente |
| P3 | `formula.input_refs` como conjunto de dependencias UNORDERED; expresión opaca SCALAR; referencias mediante claves locales estables. Listas con significado posicional conservan orden. Falta el registro completo por campo. | Pendiente; no hashing |
| P4 | Reutilizar la sesión y autorización existentes; creación nunca confiere publicación. El mapeo final requiere escoger el baseline con su gobernanza por proyecto. | Bloqueado por divergencia |

`STEP_0_GATE = BLOCKED`. Las propuestas P1–P3 no se presentan como decisiones aprobadas ni resueltas. Ninguna requiere acoplar GDSS a control, DTE o actuación.

## C. Implementación y límites

No se escribió código productivo, migración, servicio, API, fixtures ni tests GDSS. No hay capacidad GDSS de control, DTE, MQTT, actuación, simulación ni binding de telemetría añadida. La ausencia de implementación no demuestra el cumplimiento funcional de GDSS.

Se guardó el prompt operacional y este informe; se sincronizaron los estados documentales del plan y arquitectura con el mandato recibido.

## D. Invariantes

| ID | Estado | Evidencia |
|---|---|---|
| GDS-INV-01 | NOT_TESTED | No implementación GDSS |
| GDS-INV-02 | NOT_TESTED | No implementación GDSS |
| GDS-INV-03 | NOT_TESTED | No implementación GDSS |
| GDS-INV-04 | NOT_TESTED | No implementación GDSS |
| GDS-INV-05 | NOT_TESTED | No implementación GDSS |
| GDS-INV-06 | NOT_TESTED | No implementación GDSS |
| GDS-INV-07 | STRUCTURALLY_RESERVED | Architecture v0.2 INVARIANTS |
| GDS-INV-08 | STRUCTURALLY_RESERVED | Architecture v0.2 INVARIANTS |
| GDS-INV-09 | NOT_TESTED | No implementación GDSS |
| GDS-INV-10 | NOT_TESTED | No implementación GDSS |
| GDS-INV-11 | NOT_TESTED | No implementación GDSS |
| GDS-INV-12 | NOT_TESTED | No implementación GDSS |
| GDS-INV-13 | STRUCTURALLY_RESERVED | Architecture v0.2 INVARIANTS |
| GDS-INV-14 | NOT_TESTED | No implementación GDSS |
| GDS-INV-15 | STRUCTURALLY_RESERVED | Architecture v0.2 INVARIANTS |
| GDS-INV-16 | NOT_TESTED | No implementación GDSS |
| GDS-INV-17 | STRUCTURALLY_RESERVED | Architecture v0.2 INVARIANTS |
| GDS-INV-18 | NOT_TESTED | No implementación GDSS |
| GDS-INV-19 | NOT_TESTED | No implementación GDSS |
| GDS-INV-20 | STRUCTURALLY_RESERVED | Architecture v0.2 INVARIANTS |
| GDS-INV-21 | NOT_TESTED | No implementación GDSS |
| GDS-INV-22 | NOT_TESTED | No implementación GDSS |

## E. Comprobaciones ejecutadas

| Comando | Resultado inicial |
|---|---|
| `npm test -- --reporter=dot` en topology-next | 18 archivos, 65 tests PASS; 0 failed, 0 skipped |
| `npm run typecheck` en topology-next | PASS, exit 0 |
| `./scripts/smoke_core.sh` | Sintaxis y flake8 PASS; 19 tests PASS, 0 failed, 0 skipped |
| Alembic heads | Head del código 0008 |
| Consulta read-only de alembic_version | Base desplegada 0038 |
| Build completo / integración / upgrade / regresión posterior | NOT_TESTED; gate detenido antes de implementación |

Las pruebas pueden actualizar cachés Vitest/TypeScript y Python; varias ya estaban modificadas al inicio. No se atribuye ese churn a implementación GDSS. No se afirma baseline completo verde ni cierre del proyecto.

## F. Hallazgos y recuperación

- BLOCKING / PRE_EXISTING: baseline asignado 0008 frente a runtime/base 0038, con diferencias de autorización. Es necesario confirmar el checkout y la base objetivo antes de migrar o integrar RBAC.
- FUTURE_PHASE: simulación, observación acoplada y actuación permanecen fuera de alcance.

Alternativas: continuar en el checkout `iot-midd-paas-auth-work` que corresponde al runtime, trasladando únicamente los documentos GDSS después de revisar sus instrucciones; o mantener este checkout con una base aislada y baseline expresamente elegido. No se realiza ninguna de esas acciones sin resolver el destino, pues cambia qué gobernanza existente debe respetarse. No se debe usar `stamp` ni modificar 0038 para ocultar la divergencia.
