# MIDD IOT - PROMPT 017 - Informe autocontenido para ChatGPT

## 1. Resumen de la tarea

Se ejecutó el gate técnico de compatibilidad de `sharp` y de reproducibilidad E2E exclusivamente sobre el repositorio oficial `/Users/joseluis/dev/iot-midd-paas-clean`, sin tocar el repositorio preservado. El objetivo fue determinar si el override `sharp@0.35.3` es aceptable de forma temporal, validar su comportamiento en Apple Silicon y Linux amd64, reconstruir un entorno Python reproducible en el clon limpio y ejecutar el smoke E2E real desde ese clon.

Resultado general:

- decisión técnica final: `READY_FOR_LOCAL_CONTROLLED_MERGE_REHEARSAL_WITH_WARNINGS`
- decisión sobre Sharp: `SHARP_OVERRIDE_ACCEPTABLE_TEMPORARILY`
- clasificación del smoke: `SMOKE_E2E_PASS_CLEAN_REPOSITORY`

## 2. Estado inicial verificado

- repositorio oficial activo: `/Users/joseluis/dev/iot-midd-paas-clean`
- rama activa: `chore/topology-next-major-upgrade`
- `HEAD`: `41bd4ab61fbce3311e86937619e51d3a61164b4b`
- `main`: `9937d2ad5d93c9e96c7a7632909a1047ea9f8311`
- `origin/main`: `6ababdbe2fb9c7ff35c1afe769b48ecea6f133ff`
- sin archivos staged
- sin tags nuevos
- el único residuo previo siguió excluido:
  - `docs/informe_intervencion_codex_chatgpt_2026-07-27.md`

## 3. Archivos creados

- `docs/releases/prompt017_sharp_clean_repo_gate_report_2026-07-28.md`

## 4. Archivos modificados

- `docs/releases/topology_next_major_upgrade_readiness.md`

## 5. Archivos eliminados

- ninguno

## 6. Implementación realizada

No se aplicaron cambios al código productivo. La intervención quedó limitada a:

- verificación Git completa del clon limpio;
- inventario real de uso de imágenes en `apps/topology-next`;
- reinstalación del árbol final con `npm ci`;
- análisis del árbol npm de `sharp`, `@img/sharp-wasm32` y `@emnapi/runtime`;
- prueba funcional directa de `sharp` en memoria;
- evaluación aislada de alternativas B, C y D bajo `/tmp`;
- validación emulada Linux amd64 con Docker Desktop y `node:22-bullseye`;
- creación del entorno Python canónico `venv/` mediante `./setup_venv.sh`;
- reejecución real del smoke E2E desde el clon limpio;
- actualización documental obligatoria;
- generación de este informe autocontenido.

## 7. Inventario de uso real de imágenes

Datos observados en el repositorio:

- sin imports de `next/image`;
- sin `<Image`;
- sin imports o `require('sharp')`;
- sin `images` en `next.config.mjs`;
- sin `loader`;
- sin `unoptimized`;
- sin referencias a `/_next/image`;
- sin assets de imagen dentro de `apps/topology-next`;
- `next.config.mjs` no define `output: 'standalone'` ni export estático.

Clasificación:

- `SHARP_OPTIONAL_CURRENTLY_UNUSED`
- `NEXT_IMAGE_RUNTIME_NOT_EXERCISED_NO_CURRENT_USAGE`

Interpretación:

- la aplicación actual no ejercita el pipeline oficial de optimización de imágenes de Next.js;
- el riesgo del override de `sharp` hoy no proviene de una ruta funcional usada por UI o API;
- el gate debía resolverse igual porque `next@16.2.12` publica `sharp` como opcional oficial.

## 8. Análisis del árbol de Sharp

Árbol definitivo observado en `apps/topology-next`:

- `npm ci`: PASS
- `npm audit --json`: `critical=0`, `high=0`, `moderate=0`, `low=0`
- `npm ls sharp`: `next@16.2.12 -> sharp@0.35.3 overridden`
- `npm explain sharp`: `sharp@"0.35.3" (was "^0.34.5") from next@16.2.12`
- `npm ls @img/sharp-wasm32`: `extraneous`
- `npm explain @img/sharp-wasm32`: paquete WASM materializado en `node_modules`
- `npm ls @emnapi/runtime`: `extraneous`, requerido por `@img/sharp-wasm32`
- `npm ls --json`: `problems` solo con `@img/sharp-wasm32` y `@emnapi/runtime`
- `npm ls --all`: sin `invalid`; solo opcionales omitidos por plataforma
- `npm ls postcss`: `8.5.24 overridden` en `next` y dedupe en `vite`

Datos observados en npm:

- `next@16.2.12` publica `optionalDependencies.sharp = ^0.34.5`
- `sharp@0.35.3` publica paquetes opcionales por plataforma `@img/sharp-*` y `@img/sharp-libvips-*`
- `sharp@0.35.3` publica `engines.node >=20.9.0`

Datos observados localmente:

- host: `darwin arm64`
- Node: `v22.14.0`
- npm: `10.9.2`
- `sharp@0.35.3` instalado no satisface semver `^0.34.5`

Inferencia técnica:

- el warning remanente es de consistencia semver/árbol npm, no de seguridad ni de falla nativa comprobada;
- los `extraneous` quedan acotados a la rama WASM opcional de Sharp y a su runtime `@emnapi`;
- no se detectó `invalid` ni duplicación funcional bloqueante en el árbol definitivo.

## 9. Prueba funcional directa de Sharp

Prueba ejecutada:

- importación de `sharp`;
- creación de imagen mínima RGBA en memoria;
- `resize(1,1)`;
- salida PNG en memoria;
- validación de bytes no vacíos.

Resultado Apple Silicon:

- `sharp=0.35.3`
- `vips=8.18.3`
- `platform=darwin`
- `arch=arm64`
- salida no vacía: `91` bytes
- clasificación: PASS

## 10. Alternativas evaluadas

### Alternativa A - Estado actual

Estado:

- `next@16.2.12`
- override `postcss@8.5.24`
- override `sharp@0.35.3`

Resultado:

- audit en cero
- `npm test`: PASS (`72 passed`)
- `npm run typecheck`: PASS
- `npm run build`: PASS
- Sharp nativo: PASS
- smoke E2E desde clon limpio: PASS

### Alternativa B - Override específico bajo `next`

Entorno temporal:

- `/tmp/midd-iot-prompt017-altb.1iXns0`

Cambio:

```json
"overrides": {
  "next": {
    "postcss": "8.5.24",
    "sharp": "0.35.3"
  }
}
```

Resultado:

- instalación: PASS
- audit: `0 vulnerabilities`
- `npm test`: PASS
- `npm run typecheck`: PASS
- `npm run build`: PASS
- Sharp nativo: PASS
- persisten `@img/sharp-wasm32` y `@emnapi/runtime` como `extraneous`
- no aporta mejora respecto del estado actual

Conclusión:

- descartada como reemplazo del estado actual

### Alternativa C - `npm ci --omit=optional`

Entorno temporal:

- `/tmp/midd-iot-prompt017-altc.t5AMcb`

Resultado:

- instalación: PASS (`129` paquetes)
- audit: `0 vulnerabilities`
- `sharp` desaparece del árbol
- `require('sharp')`: `MODULE_NOT_FOUND`
- `npm test`: FAIL por falta de `@rollup/rollup-darwin-arm64`
- `npm run build`: FAIL
  - Next solo carga bindings WASM
  - Turbopack exige bindings nativos `@next/swc-darwin-arm64`

Conclusión:

- alternativa rechazada
- no es segura ni reproducible para este frontend

### Alternativa D - Sharp como dependencia raíz explícita

Entorno temporal:

- `/tmp/midd-iot-prompt017-altd.ld2sAv`

Cambio:

```json
"dependencies": {
  "sharp": "0.35.3"
}
```

Resultado:

- instalación: PASS
- audit: `0 vulnerabilities`
- `npm test`: PASS
- `npm run typecheck`: PASS
- `npm run build`: PASS
- Sharp nativo: PASS
- `npm ls sharp` muestra `next -> sharp@0.35.3 deduped` y `root -> sharp@0.35.3 overridden`
- persisten `extraneous`
- el desacople semver con `^0.34.5` continúa

Conclusión:

- no mejora materialmente A/E

### Alternativa E - Permanecer con el estado actual

Conclusión:

- elegida como estado definitivo
- sigue siendo la única combinación que mantiene seguridad en cero y validación funcional completa sin degradar el toolchain

## 11. Decisión sobre Sharp

Clasificación exacta:

- `SHARP_OVERRIDE_ACCEPTABLE_TEMPORARILY`

Motivos:

- seguridad final en cero;
- uso real actual de `next/image`: inexistente;
- prueba nativa PASS en Apple Silicon;
- prueba nativa PASS en Linux amd64;
- frontend en verde;
- smoke E2E en PASS desde el clon limpio;
- ninguna alternativa reduce el warning residual sin introducir un costo mayor.

Deuda pendiente:

- `sharp@0.35.3` sigue fuera del rango publicado por `next@16.2.12`;
- `npm ls --json` conserva `extraneous` opcionales explicados;
- el override debe revisarse cuando Next publique una dependencia segura y consistente.

## 12. Validación Linux amd64

Datos del experimento:

- copia temporal: `/tmp/midd-iot-prompt017-alta.HPf7LD`
- imagen: `node:22-bullseye`
- plataforma: `linux/amd64`
- host Docker: `Docker Desktop` sobre `aarch64`
- modo: emulado

Resultado:

- `npm ci`: PASS
- audit: `0 vulnerabilities`
- `npm ls sharp`: PASS
- Sharp nativo: PASS
  - `platform=linux`
  - `arch=x64`
  - `sharp=0.35.3`
  - `vips=8.18.3`
- `npm test`: PASS (`72 passed`)
- `npm run typecheck`: PASS
- `npm run build`: PASS

Conclusión:

- la combinación actual se comporta correctamente también en Linux amd64 emulado

## 13. Entorno Python reproducible

Mecanismo oficial detectado:

- `venv/` local e ignorado;
- `requirements.txt` como base;
- `tests/requirements-test.txt` para pruebas;
- `./setup_venv.sh` como bootstrap explícito del repo.

Acción realizada:

- ejecución de `./setup_venv.sh` en el clon limpio

Resultado:

- `venv` creado correctamente;
- Python: `3.12.0`;
- `sqlalchemy` importable;
- `paho-mqtt` importable;
- el clon limpio quedó apto para ejecutar los scripts Python oficiales.

Diagnóstico del fallo heredado del Prompt 016:

- clasificación principal: `PYTHON_ENV_NOT_CREATED`
- causa concreta:
  - `scripts/smoke_control_engine_end_to_end.sh` intenta usar `venv/bin/python`;
  - al no existir `venv`, hace fallback a `python3`;
  - el `python3` del host no tenía `sqlalchemy`, de ahí el `ModuleNotFoundError`.

## 14. Smoke E2E desde el clon limpio

Ejecución:

```bash
PYTHONDONTWRITEBYTECODE=1 ./scripts/smoke_control_engine_end_to_end.sh
```

Resultado:

- clasificación exacta: `SMOKE_E2E_PASS_CLEAN_REPOSITORY`
- `overall=PASS`
- `exit_code=0`
- `contract-level`: PASS
- `component-level`: PASS
- `broker-level`: PASS
- `database-level`: PASS
- `full E2E`: PASS

Hallazgo clave:

- el problema previo no era de aplicación ni de contratos del worker;
- era exclusivamente la ausencia del entorno Python reproducible en el clon limpio.

## 15. Decisiones técnicas

- mantener el override actual de `sharp` como medida temporal y documentada;
- no adoptar scoped override porque no mejora el árbol;
- no adoptar `--omit=optional` porque rompe `rollup` y `next-swc`;
- no agregar `sharp` como dependencia raíz porque no elimina el warning semver ni los `extraneous`;
- usar `./setup_venv.sh` como mecanismo canónico para reproducir el entorno Python del smoke;
- no tocar código productivo porque la evidencia no justificó cambios funcionales.

## 16. Pruebas ejecutadas y resultados

Frontend definitivo:

- `npm ci`: PASS
- `npm audit --json`: PASS, `0/0/0/0`
- `npm ls sharp`: PASS
- `npm explain sharp`: PASS
- `npm ls postcss`: PASS
- `npm ls --all`: PASS, sin `invalid`
- prueba nativa de Sharp en Apple Silicon: PASS
- `npm test`: PASS (`72 passed`)
- `npm run typecheck`: PASS
- `npm run build`: PASS

Alternativas temporales:

- B: instalación PASS, tests PASS, typecheck PASS, build PASS, sin mejora estructural
- C: instalación PASS, tests FAIL, build FAIL, alternativa rechazada
- D: instalación PASS, tests PASS, typecheck PASS, build PASS, sin mejora estructural

Linux amd64 en contenedor:

- `npm ci`: PASS
- Sharp nativo: PASS
- `npm test`: PASS (`72 passed`)
- `npm run typecheck`: PASS
- `npm run build`: PASS

Backend y runtime desde clon limpio:

- tests focalizados:
  - `tests/unit/test_services/test_ingestor_control_events.py`
  - `tests/unit/test_services/test_control_engine_worker.py`
  - `tests/unit/test_storage/test_db_handler_factory.py`
  - resultado: `18 passed`
- `apps/parametric-control-engine/tests`
  - resultado: `35 passed`
- `docker compose -f infra/containers/docker-compose.yaml config`
  - resultado: PASS
- `./scripts/smoke_control_engine_end_to_end.sh`
  - resultado: PASS completo

## 17. Pruebas no ejecutadas y motivo

- validación visual desktop/tablet/mobile no fue reejecutada en este prompt;
- validación interactiva de `/control` en navegador no fue reejecutada en este prompt.

Motivo:

- el `HEAD` funcional no cambió respecto de la revisión visual previa;
- el alcance de Prompt 017 estaba centrado en `sharp`, reproducibilidad del árbol y smoke E2E desde clon limpio;
- no hubo cambios productivos en frontend que justificaran repetir esa batería visual completa.

## 18. Riesgos o deuda pendiente

- `next@16.2.12` sigue publicando `sharp@^0.34.5`, por lo que `0.35.3` queda fuera de rango semver;
- `npm ls --json` mantiene `@img/sharp-wasm32` y `@emnapi/runtime` como `extraneous`;
- mientras no exista una versión de `next` que absorba una versión segura y consistente de `sharp`, el override debe mantenerse documentado y bajo revisión.

## 19. Estado final

- seguridad: en verde
- frontend: en verde
- backend focalizado: en verde
- engine: en verde
- compose: en verde
- smoke real desde clon limpio: en verde
- consistencia del árbol npm: usable con warning documentado, no bloqueante

Decisión exacta:

- `READY_FOR_LOCAL_CONTROLLED_MERGE_REHEARSAL_WITH_WARNINGS`

## 20. Próximo paso recomendado

Realizar un ensayo de integración local controlado sin merge ni push, manteniendo el estado actual del override de `sharp`, y dejar abierto un seguimiento explícito para retirar el override cuando Next publique una dependencia de `sharp` segura y consistente sin `extraneous`.

## 21. Referencias oficiales consultadas

Documentación oficial:

- Next.js `next/image` y self-hosting: <https://nextjs.org/docs/pages/api-reference/components/image>
- Next.js error `sharp-missing-in-production`: <https://nextjs.org/docs/messages/sharp-missing-in-production>
- Sharp install docs: <https://sharp.pixelplumbing.com/install/>

Metadatos npm consultados:

- `npm view next@16.2.12 optionalDependencies --json`
- `npm view sharp@0.35.3 optionalDependencies --json`
- `npm view sharp@0.35.3 engines --json`
