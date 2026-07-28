# Topology Workspace Parametric Control Migration Readiness

## 1. Resumen de la tarea

Se realizó una revisión humana asistida y consolidación local de la migración del workspace de `apps/topology-next` para incorporar control paramétrico por proyecto dentro del flujo oficial, sin tocar el repositorio original salvo lectura y smoke E2E. El foco quedó restringido a la capa oficial `apps/topology-next` + contratos DTO/validator/repository ya existentes, validando el feature flag `parametric_control_enabled`, la experiencia visual-operativa del workspace y el estado de release-readiness antes de un único commit local.

Estado final de esta intervención:

`COMPLETED_TOPOLOGY_MIGRATION_REVIEW_AND_COMMIT_WITH_WARNINGS`

Readiness final:

`READY_FOR_TOPOLOGY_MIGRATION_COMMIT_WITH_WARNINGS`

## 2. Contextos definidos

- Contexto arquitectónico aplicado:
  - `Python` sigue siendo el runtime oficial IoT.
  - `apps/topology-next` sigue siendo el backend/UI oficial del dominio operacional.
  - `apps/parametric-control-engine` sigue siendo el motor oficial.
  - no se crearon rutas, servicios ni contratos paralelos.
- Capacidades reforzadas:
  - `C4 Control Paramétrico`
  - `C6 Auditoría`
  - `C7 Dashboard`
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

- Repositorios usados:
  - original solo lectura + smoke: `/Users/joseluis/dev/iot-midd-paas`
  - clon limpio de trabajo: `/Users/joseluis/dev/iot-midd-paas-clean`

## 3. Estado de avance

- Migración de UI/workspace existente: consolidada en el clon limpio.
- Toggle por proyecto `parametric_control_enabled`: validado visualmente y por persistencia tras recarga.
- DTO/repository/validators del proyecto: alineados con el feature flag.
- Cobertura puntual para `false/undefined`: reforzada.
- Build, typecheck y suite frontend: en verde.
- Smoke E2E oficial del runtime Python: en verde sobre el repo original.
- Readiness documentado: completo.

## 4. Archivos creados

- `docs/releases/topology_workspace_parametric_control_migration_readiness.md`

## 5. Archivos modificados

- `apps/topology-next/next.config.mjs`
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

## 6. Archivos eliminados

No se eliminaron archivos versionados.

## 7. Implementación realizada

- Se mantuvo el campo oficial `parametric_control_enabled` como único feature flag por proyecto en DTO, validators, repositorio y consumo UI.
- En `topology-workspace.tsx` se dejó el toggle del proyecto conectado al `PATCH` oficial de proyecto y se corrigió la actualización del store para reutilizar el estado más reciente y reemplazar el proyecto con la respuesta completa del backend.
- En `topology-sidebar.tsx` se dejó visible el control del feature flag dentro del panel de proyecto, con `disabled` durante actualización y una nota explícita de estado transitorio.
- Se reforzó la cobertura unitaria del repositorio para validar:
  - mapeo por defecto a `false` cuando la columna no está presente;
  - preservación de `false` explícito;
  - omisión correcta del campo cuando no se envía.
- Se reforzó la cobertura unitaria de validadores para validar:
  - default `false` en create;
  - aceptación de `true` y `false` en update;
  - rechazo de valores no booleanos;
  - rechazo de payload vacío en update.
- Se validó el workspace en desktop, tablet y mobile sobre build productivo local.

## 8. Decisiones técnicas

- No se tocó `topology-store.ts` para evitar abrir cambios fuera del perímetro permitido; el ajuste de consistencia del toggle se resolvió desde `topology-workspace.tsx` con `useTopologyStore.getState().projects`.
- No se introdujeron nuevos endpoints ni nuevos contratos; el toggle usa el `updateProject(...)` oficial.
- No se hicieron cambios en runtime Python ni en Compose como parte de esta migración del workspace.
- El readiness queda “con warnings” por deuda de dependencias frontend reportada por `npm audit`, no por fallas funcionales del feature flag.

## 9. Pruebas ejecutadas y resultados

- Python focalizado:
  - `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=apps/parametric-control-engine/src /Users/joseluis/dev/iot-midd-paas/venv/bin/pytest -p no:cacheprovider tests/unit/test_services/test_ingestor_control_events.py tests/unit/test_services/test_control_engine_worker.py tests/unit/test_storage/test_db_handler_factory.py -q`
  - resultado: `18 passed in 0.51s`
- Parametric control engine:
  - `/Users/joseluis/dev/iot-midd-paas/venv/bin/pytest -p no:cacheprovider apps/parametric-control-engine/tests -q`
  - resultado: `35 passed in 0.29s`
- Frontend unit tests:
  - `npm test`
  - resultado: `18` archivos, `72 passed`
- Typecheck:
  - `npm run typecheck`
  - resultado: éxito
- Build productivo:
  - `npm run build`
  - resultado: éxito
  - observación: persistieron warnings esperados `DYNAMIC_SERVER_USAGE` en `/api/control/access`, `/api/control/audit`, `/api/control/recommendations` y `/api/control/status`, sin bloquear build
- Docker Compose oficial:
  - `docker compose -f infra/containers/docker-compose.yaml config`
  - resultado: éxito
- Smoke E2E oficial sobre el repo original:
  - `./scripts/smoke_control_engine_end_to_end.sh`
  - resultado: `PASS`
  - `run_id`: `c0d437ac54b347a5a366f9d6f1565f56`
  - `audit_row_id`: `193`
- Validación visual-operativa asistida:
  - URL: `http://127.0.0.1:3001/?projectId=00000000-0000-0000-0000-0000000000b5`
  - desktop: parte en `Control disabled`
  - toggle a enabled: persiste tras recarga
  - toggle a disabled: persiste tras recarga
  - mobile: sigue visible el control del proyecto y el estado `Control disabled`
  - consola in-app: `0` logs de error en desktop, enabled y disabled
  - evidencia local:
    - `/private/tmp/midd-iot-prompt012-visual-evidence/workspace-desktop.png`
    - `/private/tmp/midd-iot-prompt012-visual-evidence/control-toggle-enabled.png`
    - `/private/tmp/midd-iot-prompt012-visual-evidence/workspace-tablet.png`
    - `/private/tmp/midd-iot-prompt012-visual-evidence/control-toggle-disabled.png`
    - `/private/tmp/midd-iot-prompt012-visual-evidence/workspace-mobile.png`
- Auditoría de dependencias:
  - `npm audit --json`
  - resultado: `9` vulnerabilidades reportadas
  - severidad: `3 critical`, `2 high`, `4 moderate`
  - directas relevantes: `next`, `next-auth`, `vitest`
  - transitive relevantes: `postcss`, `vite`, `vite-node`, `esbuild`, `uuid`, `@vitest/mocker`

## 10. Pruebas no ejecutadas y motivo

- No se exportó HAR ni traza formal de red desde el navegador interno.
- Motivo: la capability disponible en el browser in-app permitió validación visual y consola, pero no expuso una captura de red estable para este entorno.

## 11. Riesgos o deuda pendiente

- `npm audit` sigue marcando deuda importante de dependencias:
  - `next@14.2.13` queda afectado por advisories con fix disponible en ramas más nuevas;
  - `next-auth` tiene advisories `high/critical`;
  - `vitest@2.1.8` arrastra vulnerabilidades críticas de tooling.
- Las correcciones sugeridas por `npm audit` implican upgrades potencialmente mayores:
  - `next -> 16.2.12`
  - `vitest -> 4.1.10`
- La nota transitoria `Actualizando feature flag del proyecto...` quedó implementada, pero no fue observable en captura porque la respuesta local del `PATCH` fue demasiado rápida.
- El clon limpio conserva archivos no stageados ajenos a este corte:
  - `docs/informe_intervencion_codex_chatgpt_2026-07-27.md`

## 12. Estado final

- Repositorio original:
  - sin modificaciones de esta intervención fuera de lectura y ejecución del smoke oficial
- Clon limpio:
  - listo para commit local selectivo de la migración del workspace
- Clasificación final:
  - `COMPLETED_TOPOLOGY_MIGRATION_REVIEW_AND_COMMIT_WITH_WARNINGS`
- Readiness:
  - `READY_FOR_TOPOLOGY_MIGRATION_COMMIT_WITH_WARNINGS`

## 13. Próximos pasos sugeridos

1. Crear el commit local selectivo `feat(topology): integrate project parametric control workspace`.
2. Abrir una intervención separada para saneamiento de dependencias frontend, sin mezclarla con esta migración funcional.
3. Si se requiere release productivo del frontend, tratar `npm audit` como deuda prioritaria antes de promover a un corte final.

## 14. Próximo paso recomendado

Ejecutar el commit local selectivo de esta migración y dejar un ticket aparte para actualización controlada de `next`, `next-auth` y `vitest`.
