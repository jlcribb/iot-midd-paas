# Control Engine Post-RC1 Baseline Manifest

Fecha de emision: 2026-07-27
Estado de decision: READY_FOR_BASELINE_CUT_WITH_WARNINGS
Commit base inspeccionado: `f29200f6d9f54926fae36e40e6f78dd52a72eea6`
Branch inspeccionada: `main`

## 1. Objetivo del corte

Definir un corte versionable y separable del trabajo post `control-engine-mvp-rc1`, limitado al flujo E2E oficial de control parametrico:

`Telemetry Event -> ControlEvaluationRequest -> Policy Selection -> Evaluation -> Recommendation -> Publishable Envelope -> Audit Envelope`

El corte propuesto incluye solamente codigo, pruebas, scripts, configuracion y documentacion directamente vinculados con:

- C4 Control Parametrico
- C5 Politicas
- C6 Auditoria
- C7 Dashboard minimo operativo

## 2. Veredicto

El baseline puede cortarse si se respeta exactamente el perimetro de archivos de este manifiesto y se dejan afuera los cambios ajenos y los artefactos generados.

No se detectaron bloqueos funcionales en:

- worker Python de control;
- emision y persistencia de auditoria;
- smoke end-to-end real;
- endpoints `/api/control/*`;
- dashboard visual `/control`;
- stack oficial `docker compose`.

## 3. Archivos propuestos para el baseline

### 3.1 Codigo y configuracion funcional

- `.gitignore`
- `README.md`
- `infra/containers/docker-compose.yaml`
- `src/iot_middleware/services/control_runtime_contract.py`
- `src/iot_middleware/services/control_engine_worker.py`
- `src/iot_middleware/services/ingestor.py`
- `src/iot_middleware/storage/db_handler.py`

### 3.2 Scripts operativos y smoke

- `scripts/README.md`
- `scripts/docker-stack.sh`
- `scripts/smoke_control_engine_end_to_end.py`
- `scripts/smoke_control_engine_end_to_end.sh`

### 3.3 Pruebas

- `tests/unit/test_services/test_control_engine_worker.py`
- `tests/unit/test_services/test_ingestor_control_events.py`
- `tests/unit/test_storage/test_db_handler_factory.py`

### 3.4 Documentacion y contratos

- `docs/contracts/control_event_contract.md`
- `docs/contracts/control_policy_contract.md`
- `docs/contracts/control_audit_contract.md`
- `docs/operations/control_dashboard.md`
- `docs/operations/control_engine_worker.md`
- `docs/releases/control_engine_post_rc1_baseline_readiness_2026-07-27.md`
- `docs/releases/control_engine_post_rc1_baseline_manifest.md`

### 3.5 Evidencia versionable del corte

- `reports/releases/control_engine_post_rc1_baseline_evidence.json`

## 4. Archivos explicitamente excluidos del baseline

### 4.1 Cambios ajenos al baseline de control parametrico

- `apps/topology-next/next.config.mjs`
- `apps/topology-next/tsconfig.json`
- `apps/topology-next/src/app/globals.css`
- `apps/topology-next/src/components/topology/api.ts`
- `apps/topology-next/src/components/topology/topology-palette.tsx`
- `apps/topology-next/src/components/topology/topology-sidebar.tsx`
- `apps/topology-next/src/components/topology/topology-toolbar.tsx`
- `apps/topology-next/src/components/topology/topology-workspace.tsx`
- `apps/topology-next/src/components/topology/types.ts`
- `apps/topology-next/src/lib/dto/project.dto.ts`
- `apps/topology-next/src/lib/repositories/project.repository.ts`
- `apps/topology-next/src/lib/validators/project.schemas.ts`
- `apps/topology-next/tests/unit/control-policy.service.test.ts`
- `apps/topology-next/tests/unit/project.service.test.ts`
- `apps/topology-next/tests/unit/provisioning.service.test.ts`
- `apps/topology-next/tests/unit/sector.service.test.ts`
- `apps/topology-next/tests/unit/topology.service.test.ts`
- `apps/topology-next/tests/unit/project.repository.test.ts`
- `apps/topology-next/tests/unit/project.validators.test.ts`

### 4.2 Artefactos generados no versionables o deuda historica

- `apps/topology-next/.next/**`
- `apps/topology-next/.next-docker/**`
- `apps/topology-next/node_modules/.vite/vitest/results.json`
- `apps/topology-next/tsconfig.typecheck.tsbuildinfo`
- `apps/topology-next/tsconfig.tsbuildinfo`
- `src/iot_middleware/services/__pycache__/**`
- `src/iot_middleware/storage/__pycache__/**`
- `tests/__pycache__/**`
- `ingesta_service.log`

### 4.3 Archivos dudosos que no deben entrar al baseline sin trazabilidad

- `topology-workspace-home.png`
- `topology-workspace-mobile-top.png`
- `topology-workspace-mobile.png`

## 5. Clasificacion del worktree

### 5.1 Grupo A - incluir en commit baseline

Los archivos listados en la seccion 3.

### 5.2 Grupo B - excluir por cambio ajeno

Los archivos listados en la seccion 4.1.

### 5.3 Grupo C - excluir por artefacto generado

Los archivos listados en la seccion 4.2.

### 5.4 Grupo D - preservar pero no stagear por origen incierto

Los archivos listados en la seccion 4.3.

## 6. Trazabilidad reconstruida por prompt

### 6.1 Prompt 001 - consolidacion E2E

Atribucion alta:

- `.gitignore`
- `README.md`
- `docs/contracts/control_event_contract.md`
- `docs/contracts/control_policy_contract.md`
- `docs/operations/control_dashboard.md`
- `docs/operations/control_engine_worker.md`
- `infra/containers/docker-compose.yaml`
- `scripts/README.md`
- `scripts/docker-stack.sh`
- `scripts/smoke_control_engine_end_to_end.py`
- `scripts/smoke_control_engine_end_to_end.sh`
- `src/iot_middleware/services/control_runtime_contract.py`
- `src/iot_middleware/services/control_engine_worker.py`
- `src/iot_middleware/services/ingestor.py`
- `tests/unit/test_services/test_control_engine_worker.py`
- `tests/unit/test_services/test_ingestor_control_events.py`

### 6.2 Prompt 002 - validacion E2E real con Docker

No se detecto en el repositorio un archivo final independiente generado por ese prompt. La evidencia funcional se reconstruyo mediante:

- smoke E2E real reejecutado;
- estado actual del stack Docker;
- endpoints `/api/control/*`;
- dashboard `/control`;
- documentacion y scripts existentes.

### 6.3 Prompt 003 - cierre de consistencia de auditoria

Atribucion alta:

- `docs/contracts/control_audit_contract.md`
- `src/iot_middleware/storage/db_handler.py`
- `tests/unit/test_storage/test_db_handler_factory.py`
- `docs/releases/control_engine_post_rc1_baseline_readiness_2026-07-27.md`

Atribucion probable compartida con Prompt 001 o Prompt 003:

- `src/iot_middleware/services/control_engine_worker.py`
- `src/iot_middleware/services/ingestor.py`
- `docs/operations/control_engine_worker.md`
- `scripts/smoke_control_engine_end_to_end.py`

### 6.4 Origen incierto y no baseline

- cambios de `apps/topology-next` listados en 4.1;
- imagenes `topology-workspace-*.png`;
- artefactos generados historicamente trackeados.

## 7. Validaciones ejecutadas

### 7.1 Python y backend

- `./venv/bin/pytest tests/unit/test_services/test_control_engine_worker.py -q` -> `10 passed`
- `./venv/bin/pytest tests/unit/test_services/test_ingestor_control_events.py tests/unit/test_services/test_control_engine_worker.py tests/unit/test_storage/test_db_handler_factory.py -q` -> `18 passed`
- `./scripts/smoke_core.sh` -> `19 passed`

### 7.2 Front oficial del engine

- `PYTHONPATH=apps/parametric-control-engine/src ./venv/bin/pytest apps/parametric-control-engine/tests -q` -> `35 passed`

### 7.3 Topology Next

- `npm test` -> `18 files passed`, `65 passed`
- `npm run typecheck` -> `PASS`
- `npm run build` -> `PASS`
- `lint` no ejecutado porque `apps/topology-next/package.json` no define script `lint`

### 7.4 Smoke E2E real de control parametrico

- `./scripts/smoke_control_engine_end_to_end.sh` -> `PASS`
- `run_id`: `db572934ac9049cb942793d08235b750`
- `event_id`: `evt-full-e2e-db572934ac9049cb942793d08235b750`
- `audit_row_id`: `163`

Chequeos aprobados:

- `contract-level`
- `component-level`
- `broker-level`
- `database-level`
- `full E2E`
- `audit_publish`
- `audit_persistence_attempt`
- `audit_database_row`
- `audit_metadata_consistency`

### 7.5 Validacion SQL de auditoria persistida

Consulta directa a PostgreSQL validada sobre el evento mas reciente:

- `accion = CONTROL_RECOMMENDATION_EMITTED`
- `entidad = control_engine_worker`
- `status = processed`
- `audit_publish_status = published`
- `audit_persistence_status = persisted`
- `embedded_row_id = 163`

## 8. Validacion de APIs oficiales

- `GET http://127.0.0.1:3000/api/control/access` -> `200 OK`
- `GET http://127.0.0.1:3000/api/control/status` -> `200 OK`
- `GET http://127.0.0.1:3000/api/control/recommendations?projectId=00000000-0000-0000-0000-000000000001&limit=5` -> `200 OK`
- `GET http://127.0.0.1:3000/api/control/audit?projectId=00000000-0000-0000-0000-000000000001&limit=5` -> `200 OK`
- `GET http://127.0.0.1:3000/api/control/recommendations?limit=3` -> `200 OK`
- `GET http://127.0.0.1:3000/api/control/audit?limit=3` -> `200 OK`

## 9. Validacion visual-operativa de `/control`

Validacion realizada con navegador real en `http://127.0.0.1:3000/control`.

Confirmado visualmente:

- el dashboard carga;
- el actor visible es `local-control-admin`;
- el rol visible es `admin`;
- el scope visible es `all-projects`;
- la vista es read-only;
- existen datos en tablas de recomendaciones y auditoria;
- el evento E2E mas reciente aparece reflejado en la UI;
- no se observaron errores ni warnings de consola del dashboard evaluado.

Capturas locales no versionables:

- `/private/tmp/midd-iot-release-readiness-2026-07-27/control-dashboard-desktop-loaded.png`
- `/private/tmp/midd-iot-release-readiness-2026-07-27/control-dashboard-mobile-loaded.png`
- `/private/tmp/midd-iot-release-readiness-2026-07-27/control-dashboard-tables.png`

## 10. Estado del stack Docker oficial

### 10.1 Validacion de runtime

- `docker version` -> cliente `29.4.1`, servidor `29.4.1`, Docker Desktop `4.71.0`
- `docker compose version` -> `v5.1.3`
- `docker compose -f infra/containers/docker-compose.yaml config` -> valido

### 10.2 Servicios relevantes observados en ejecucion

- `control-engine-worker`
- `ingestor`
- `postgresql`
- `rabbitmq`
- `mosquitto`
- `topology-ui`

## 11. Warnings aceptados

- La imagen `docker.io/postgis/postgis:16-3.4` resolvio como `linux/amd64` en host `darwin/arm64`. No bloqueo el smoke ni la operacion, pero sigue siendo deuda de portabilidad local.
- Existen artefactos generados historicamente trackeados en git desde el commit `e89cd5e4` y al menos un `.pyc` trackeado desde `3bb123c9`.
- El worktree contiene cambios ajenos en `apps/topology-next` que no deben mezclarse con el baseline de control.
- En logs de PostgreSQL quedaron errores historicos de otras areas funcionales. No bloquearon `/control` ni el E2E de control parametrico, pero deben limpiarse antes de un release mas amplio.
- `npm run build` reporto `Dynamic server usage` en rutas `/api/control/*`; la condicion es esperada para rutas dinamicas y no fue bloqueante en esta validacion.

## 12. Riesgos si se corta mal el baseline

- mezclar el baseline con cambios ajenos de topologia o proyectos;
- arrastrar artefactos generados al commit;
- incorporar imagenes dudosas sin trazabilidad;
- perder la capacidad de auditar exactamente que parte del worktree corresponde al flujo oficial de control.

## 13. Plan exacto de staging recomendado

### 13.1 Revision previa obligatoria

Ejecutar revision manual por archivo antes de stagear:

```bash
git diff -- .gitignore README.md infra/containers/docker-compose.yaml \
  src/iot_middleware/services/control_runtime_contract.py \
  src/iot_middleware/services/control_engine_worker.py \
  src/iot_middleware/services/ingestor.py \
  src/iot_middleware/storage/db_handler.py \
  scripts/README.md scripts/docker-stack.sh \
  scripts/smoke_control_engine_end_to_end.py \
  scripts/smoke_control_engine_end_to_end.sh \
  tests/unit/test_services/test_control_engine_worker.py \
  tests/unit/test_services/test_ingestor_control_events.py \
  tests/unit/test_storage/test_db_handler_factory.py \
  docs/contracts/control_event_contract.md \
  docs/contracts/control_policy_contract.md \
  docs/contracts/control_audit_contract.md \
  docs/operations/control_dashboard.md \
  docs/operations/control_engine_worker.md \
  docs/releases/control_engine_post_rc1_baseline_readiness_2026-07-27.md \
  docs/releases/control_engine_post_rc1_baseline_manifest.md \
  reports/releases/control_engine_post_rc1_baseline_evidence.json
```

### 13.2 Staging por grupo

Codigo y configuracion:

```bash
git add .gitignore README.md infra/containers/docker-compose.yaml \
  src/iot_middleware/services/control_runtime_contract.py \
  src/iot_middleware/services/control_engine_worker.py \
  src/iot_middleware/services/ingestor.py \
  src/iot_middleware/storage/db_handler.py
```

Scripts:

```bash
git add scripts/README.md scripts/docker-stack.sh \
  scripts/smoke_control_engine_end_to_end.py \
  scripts/smoke_control_engine_end_to_end.sh
```

Pruebas:

```bash
git add tests/unit/test_services/test_control_engine_worker.py \
  tests/unit/test_services/test_ingestor_control_events.py \
  tests/unit/test_storage/test_db_handler_factory.py
```

Documentacion:

```bash
git add docs/contracts/control_event_contract.md \
  docs/contracts/control_policy_contract.md \
  docs/contracts/control_audit_contract.md \
  docs/operations/control_dashboard.md \
  docs/operations/control_engine_worker.md \
  docs/releases/control_engine_post_rc1_baseline_readiness_2026-07-27.md \
  docs/releases/control_engine_post_rc1_baseline_manifest.md
```

Evidencia:

```bash
git add reports/releases/control_engine_post_rc1_baseline_evidence.json
```

### 13.3 Verificacion final de staging

```bash
git diff --cached --name-only
git status --short
```

## 14. Commit y tag sugeridos

Commit sugerido:

```text
freeze: control engine post-RC1 baseline
```

Tag sugerido:

```text
control-engine-mvp-rc1.1
```

Nombre sugerido para release interna:

```text
Control Engine Post-RC1 Baseline
```

## 15. Comandos de corte recomendados y no ejecutados

```bash
git commit -m "freeze: control engine post-RC1 baseline"
git tag -a control-engine-mvp-rc1.1 -m "Control Engine Post-RC1 Baseline"
git push origin main --follow-tags
```

Estos comandos quedan documentados solamente como siguiente paso. No fueron ejecutados en esta intervencion.

