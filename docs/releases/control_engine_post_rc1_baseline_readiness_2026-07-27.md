# Informe de intervención y baseline readiness post-RC1

## 1. Resumen de la tarea

Se cerró la inconsistencia observable entre la persistencia real de auditoría y la metadata `audit_persistence` del `audit envelope`, se saneó de forma controlada una parte segura del worktree generado, se revalidó el flujo E2E oficial con Docker Compose y se dejó una baseline técnica documentada para una siguiente formalización post-RC1.

Estado final de esta intervención:

`COMPLETED_AUDIT_CONSISTENCY_AND_BASELINE_READINESS_WITH_WARNINGS`

## 2. Contextos definidos y restricciones aplicadas

- Capacidad foco: `C6 Auditoría`, con soporte directo a estabilidad operativa de `C4 Control Paramétrico`.
- Flujo canónico preservado:

```text
Telemetry Event
  -> ControlEvaluationRequest
  -> Policy Selection
  -> Evaluation
  -> Recommendation
  -> Publishable Envelope
  -> Audit Envelope
```

- Flujo operativo validado:

```text
MQTT
  -> Python ingestor
  -> RabbitMQ telemetry.events
  -> control_engine_worker
  -> public.projects.parametric_control_enabled
  -> public.project_control_policies
  -> apps/parametric-control-engine
  -> RabbitMQ control.recommendations
  -> RabbitMQ control.audit
  -> iot_schema.auditoria
  -> apps/topology-next /api/control/*
  -> /control
```

- Runtime local oficial respetado: `Docker Desktop` + `docker compose`.
- No se introdujeron flujos paralelos, nuevas tablas, migraciones, IA, Cognitive Core, actuación automática ni cambios de infraestructura.
- Se preservó la naturaleza `best-effort` de la auditoría. No se agregó semántica `exactly-once`, outbox, saga ni transacciones distribuidas.

## 3. Estado recibido y contraste realizado

Antes de modificar, se contrastó el estado con:

- `AGENTS.md`
- `README.md`
- `docs/contracts/control_audit_contract.md`
- `docs/contracts/control_event_contract.md`
- `docs/contracts/control_policy_contract.md`
- `docs/operations/control_engine_worker.md`
- `docs/operations/control_dashboard.md`
- `docs/operations/control_observability.md`
- `docs/releases/control_engine_mvp_rc1.md`
- `scripts/README.md`
- `scripts/smoke_control_engine_end_to_end.py`
- `src/iot_middleware/services/control_engine_worker.py`
- `src/iot_middleware/services/control_runtime_contract.py`
- `src/iot_middleware/services/ingestor.py`
- `src/iot_middleware/storage/db_handler.py`
- `apps/topology-next/src/app/api/control/audit/route.ts`
- `apps/topology-next/src/lib/repositories/control-observability.repository.ts`
- `tests/unit/test_services/test_control_engine_worker.py`
- `tests/unit/test_services/test_ingestor_control_events.py`
- `tests/unit/test_storage/test_db_handler_factory.py`

Observación de contexto:

- el repositorio contiene `docs/informe_intervencion_codex_chatgpt_2026-07-27.md` como informe previo;
- no se encontró un archivo separado y explícito de cierre de `PROMPT 002`, por lo que el estado recibido se reconstruyó contrastando prompt, código, tests, logs, base y stack activo.

Inspecciones operativas mínimas realizadas:

- `git status --short`
- `git diff --stat`
- `git diff` focalizado sobre worker, contrato runtime, persistencia, smoke y tests afectados
- `git log -1 --oneline`
- `docker version`
- `docker compose version`
- `docker compose -f infra/containers/docker-compose.yaml ps`

Hallazgo base confirmado:

- el `audit envelope` publicado podía reflejar `pending_best_effort` de forma honesta;
- la fila persistida en `iot_schema.auditoria` podía conservar ese mismo estado aunque la inserción ya hubiera sido exitosa;
- la inconsistencia no estaba en la persistencia real, sino en el momento y la forma de consolidar `audit_persistence` dentro del payload almacenado.

## 4. Diagnóstico técnico

Orden operativo encontrado en el worker:

1. construir `audit envelope`;
2. publicar `control.audit`;
3. persistir auditoría;
4. mutar metadata en memoria después de la persistencia.

Problema:

- la representación publicada y la representación persistida compartían el mismo payload base;
- el resultado final de persistencia se conocía demasiado tarde respecto del contenido ya serializado para la fila;
- por eso podía quedar `audit_persistence.status = pending_best_effort` dentro de una fila ya insertada.

## 5. Decisión técnica adoptada

Se eligió una solución mínima híbrida, compatible con el diseño actual:

- el envelope base nace con `not_attempted`;
- antes de publicar auditoría se marca `pending_best_effort`, que es el estado honesto para el mensaje emitido a RabbitMQ;
- la persistencia devuelve un resultado estructurado;
- durante la persistencia en PostgreSQL se hace `flush()` para obtener evidencia real de inserción;
- antes del `commit`, se reescribe la metadata `audit_persistence` de la fila con el resultado confirmado;
- el proceso devuelve una copia final con `persisted` o `failed`, sin afirmar garantías transaccionales globales.

Razón de elección:

- evita una segunda actualización SQL posterior;
- mantiene honestidad semántica en el mensaje publicado;
- permite que la fila almacenada refleje el resultado real de su persistencia;
- no cambia esquema;
- no rompe `/api/control/audit`.

## 6. Estados de persistencia resultantes

- `not_attempted`: el envelope base aún no intentó persistir.
- `pending_best_effort`: el audit ya fue construido/publicado, pero todavía no hay confirmación definitiva de base.
- `persisted`: existe evidencia real de inserción exitosa y la fila almacenada queda actualizada con esa metadata.
- `failed`: se intentó persistir y la operación falló; el resultado queda estructurado y observable.

Metadata consolidada cuando corresponde:

- `attempted`
- `attempted_at`
- `completed_at`
- `backend`
- `store`
- `table`
- `action`
- `row_id`
- `rows_affected`
- `error` sanitizado solo ante fallo

## 7. Implementación realizada

- `src/iot_middleware/services/control_runtime_contract.py`
  - se formalizaron constantes para los estados `not_attempted`, `pending_best_effort`, `persisted` y `failed`.

- `src/iot_middleware/services/control_engine_worker.py`
  - se incorporó la construcción explícita de metadata de persistencia;
  - el envelope base arranca en `not_attempted`;
  - antes de publicar `control.audit`, la persistencia se marca como `pending_best_effort`;
  - `_persist_audit_envelope()` pasó a trabajar con un resultado estructurado, no solo booleano;
  - se mantuvo la publicación de auditoría separada de la confirmación de base.

- `src/iot_middleware/storage/db_handler.py`
  - `persist_control_audit_record()` pasó a devolver metadata estructurada;
  - se hace `flush()` para obtener `row_id`;
  - la fila ORM se actualiza con `audit_persistence.status = persisted` antes del `commit`;
  - ante error, se devuelve `failed` con metadata observable.

- `src/iot_middleware/services/ingestor.py`
  - se agregó recreación del cliente RabbitMQ ante publicación fallida o conexión vieja, para estabilizar el E2E real.

- `scripts/smoke_control_engine_end_to_end.py`
  - se añadieron verificaciones explícitas de:
    - `audit_publish`
    - `audit_persistence_attempt`
    - `audit_database_row`
    - `audit_metadata_consistency`
  - el nivel `full E2E` ahora falla si la metadata persistida no coincide con la fila observada.

- documentación
  - `docs/contracts/control_audit_contract.md`
  - `docs/operations/control_engine_worker.md`
  - `scripts/README.md`
  - se actualizó la semántica de estados y el ciclo real del envelope.

- pruebas unitarias
  - se cubrió el estado inicial `not_attempted`;
  - se verificó que el audit publicado salga en `pending_best_effort`;
  - se verificó la transición estructurada a `persisted` o `failed`;
  - se cubrió el retry del ingestor frente a fallo de RabbitMQ.

## 8. Archivos creados

- `docs/releases/control_engine_post_rc1_baseline_readiness_2026-07-27.md`

## 9. Archivos modificados

- `docs/contracts/control_audit_contract.md`
- `docs/operations/control_engine_worker.md`
- `scripts/README.md`
- `scripts/smoke_control_engine_end_to_end.py`
- `src/iot_middleware/services/control_engine_worker.py`
- `src/iot_middleware/services/control_runtime_contract.py`
- `src/iot_middleware/services/ingestor.py`
- `src/iot_middleware/storage/db_handler.py`
- `tests/unit/test_services/test_control_engine_worker.py`
- `tests/unit/test_services/test_ingestor_control_events.py`
- `tests/unit/test_storage/test_db_handler_factory.py`

## 10. Archivos eliminados

No se eliminaron archivos versionados.

Sí se saneó una parte segura de artefactos no versionados y reproducibles del worktree:

- `.playwright-mcp/`
- `.pytest_cache/`
- `tests/.pytest_cache/`
- `scripts/__pycache__/`
- `apps/parametric-control-engine/tests/__pycache__/`
- `tests/unit/test_services/__pycache__/`
- `tests/unit/test_storage/__pycache__/`
- varios `.DS_Store`

Se conservaron artefactos dudosos o cambios ajenos al alcance:

- `topology-workspace-home.png`
- `topology-workspace-mobile-top.png`
- `topology-workspace-mobile.png`
- cambios preexistentes en `apps/topology-next`
- artefactos versionados históricos como `.next`, `results.json`, `tsbuildinfo`, `ingesta_service.log`, `*.pyc` ya presentes en Git

## 11. Pruebas ejecutadas y resultados

### Validación Python

- `./venv/bin/pytest tests/unit/test_services/test_control_engine_worker.py -q`
  - resultado: `10 passed`

- `./venv/bin/pytest tests/unit/test_services/test_ingestor_control_events.py tests/unit/test_services/test_control_engine_worker.py tests/unit/test_storage/test_db_handler_factory.py -q`
  - resultado: `18 passed`

- `PYTHONPATH=apps/parametric-control-engine/src ./venv/bin/pytest apps/parametric-control-engine/tests -q`
  - resultado: `35 passed`

### Smoke local

- `./scripts/smoke_core.sh`
  - resultado: `19 passed`

- `./scripts/smoke_control_engine_end_to_end.sh`
  - resultado final: `overall=PASS`
  - `run_id`: `f855488a0ed040bdaf2c9782ef848c3b`
  - niveles:
    - `contract-level: PASS`
    - `component-level: PASS`
    - `broker-level: PASS`
    - `database-level: PASS`
    - `full E2E: PASS`

### Verificación operativa del stack

- `docker version`
  - cliente: `29.4.1`
  - server: `Docker Desktop 4.71.0`, engine `29.4.1`

- `docker compose version`
  - resultado: `v5.1.3`

- `docker compose -f infra/containers/docker-compose.yaml ps`
  - resultado: stack operativo, incluyendo `ingestor`, `control-engine-worker`, `rabbitmq`, `postgresql`, `mosquitto` y `topology-ui`

### Verificación de endpoints operativos

- `GET /api/control/status`
  - `200 OK`

- `GET /api/control/recommendations?projectId=00000000-0000-0000-0000-000000000001&limit=3`
  - `200 OK`
  - incluye `evt-full-e2e-f855488a0ed040bdaf2c9782ef848c3b`

- `GET /api/control/audit?projectId=00000000-0000-0000-0000-000000000001&limit=3`
  - `200 OK`
  - fila real observada: `id=158`
  - `audit_persistence.status = persisted`
  - `row_id = 158`

### Verificación de frontend operacional

- `cd apps/topology-next && npm test`
  - resultado: `65 passed`

- `cd apps/topology-next && npm run typecheck`
  - resultado: `passed`

- `cd apps/topology-next && npm run build`
  - resultado: `passed` con warnings conocidos de `Dynamic server usage` en rutas `/api/control/*`

## 12. Pruebas no ejecutadas y motivo

- no se ejecutó una validación visual manual exhaustiva del dashboard `/control`;
  - motivo: el alcance de esta intervención fue consistencia de auditoría y readiness técnica, no QA visual completa.

- no se ejecutaron pruebas de larga duración, restart loops o endurance del broker;
  - motivo: fuera de alcance para una corrección mínima post-RC1.

- no se generó commit, tag o release formal;
  - motivo: el prompt pidió explícitamente no hacerlo todavía.

## 13. Riesgos y deuda pendiente

- la auditoría sigue siendo `best-effort`;
  - no existe atomicidad entre RabbitMQ y PostgreSQL.

- el worktree sigue sucio por cambios previos y por artefactos versionados históricos fuera de alcance.

- persisten warnings de `Dynamic server usage` en `apps/topology-next`, no bloqueantes para esta baseline.

- falta una revisión visual/manual final del dashboard `/control`.

- la baseline formal posterior a RC1 todavía no fue materializada como commit/tag/release.

## 14. Estado final

Resultado consolidado:

- la inconsistencia entre inserción real y metadata persistida quedó corregida;
- el audit publicado mantiene honestidad semántica con `pending_best_effort`;
- la fila persistida refleja `persisted` cuando la inserción fue exitosa;
- `/api/control/audit` expone la metadata corregida sin ruptura contractual;
- el flujo oficial `MQTT -> ingestor -> worker -> RabbitMQ -> PostgreSQL -> /api/control/*` quedó revalidado en entorno real Docker Compose.

Evidencia puntual del cierre:

- `event_id`: `evt-full-e2e-f855488a0ed040bdaf2c9782ef848c3b`
- `correlation_id`: `control::evt-full-e2e-f855488a0ed040bdaf2c9782ef848c3b::tank_level`
- `audit_id`: `audit::evt-full-e2e-f855488a0ed040bdaf2c9782ef848c3b::tank_level`
- `audit_row_id`: `158`

Estado final formal:

`COMPLETED_AUDIT_CONSISTENCY_AND_BASELINE_READINESS_WITH_WARNINGS`

## 15. Próximo paso recomendado

Crear la baseline formal post-RC1 en una intervención separada y controlada:

1. sanear o aislar los cambios ajenos al alcance que siguen en el worktree;
2. revisar visualmente `/control` y las rutas `/api/control/*` con criterio release;
3. congelar la evidencia E2E verde;
4. recién entonces crear commit, tag y release de la baseline post-RC1.
