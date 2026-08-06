# Topology Next Major Upgrade Readiness

## 1. Contexto

- Prompt ejecutado: `MIDD IOT — PROMPT 015`
- Fecha: `2026-07-28`
- Repositorio evaluado: `/Users/joseluis/dev/iot-midd-paas-clean`
- Rama de trabajo: `chore/topology-next-major-upgrade`
- Commit base: `9937d2ad5d93c9e96c7a7632909a1047ea9f8311`
- Objetivo: eliminar los advisories `critical` y `high` restantes de `apps/topology-next` sin romper App Router, auth, `/control`, `/api/control/*`, feature flag `parametric_control_enabled`, build ni flujo E2E.
- Referencias oficiales usadas:
  - [Next.js 15 upgrade guide](https://nextjs.org/docs/app/guides/upgrading/version-15)
  - [Next.js 16 upgrade guide](https://nextjs.org/docs/app/guides/upgrading/version-16)
  - [Next.js async dynamic APIs](https://nextjs.org/docs/messages/sync-dynamic-apis)
  - [next-auth package metadata](https://www.npmjs.com/package/next-auth)

## 2. Estado inicial

- `main` local en `9937d2ad5d93c9e96c7a7632909a1047ea9f8311`
- `origin/main` en `6ababdbe2fb9c7ff35c1afe769b48ecea6f133ff`
- `main` local ahead de `origin/main` por `1` commit
- residuo excluido del alcance: `docs/informe_intervencion_codex_chatgpt_2026-07-27.md`
- baseline de `apps/topology-next`:
  - Node `v22.14.0`
  - npm `10.9.2`
  - `next` `14.2.13`
  - `next-auth` `4.24.15`
  - `react` / `react-dom` `18.3.1`
  - `typescript` `5.7.3`
  - `vite` `6.4.3`
  - `vitest` `3.2.6`

## 3. Advisories pendientes

- baseline `npm audit` guardada en `/tmp/midd-iot-prompt015-audit-before.json`
- resultado baseline:
  - `critical = 1`
  - `high = 1`
  - `moderate = 0`
  - `low = 0`
- advisories remanentes antes del upgrade:
  - `next` con severidad `critical`
  - `postcss` con severidad `high`

## 4. Versiones evaluadas

- Fase A:
  - se verificó que el major `14` no tenía una ruta local confirmada que dejara `critical = 0` y `high = 0`
  - no se consolidó upgrade menor adicional de `14`
- Fase B:
  - versión evaluada: `15.5.21`
  - compatibilidad de peer: aceptable con `react 18` y `next-auth 4.24.15`
  - resultado: build falló por incompatibilidad de firmas de route handlers con `params` sin migrar a API async
  - audit intermedio empeoró a `high = 3`, `moderate = 1`
  - decisión: revertido por no cumplir build ni seguridad
- Fase C:
  - versión evaluada: `16.2.12`
  - compatibilidad de peer: aceptable con `react 18.3.1` y `next-auth 4.24.15`
  - requisito principal: migración mecánica de `params` y `searchParams` a APIs async
  - resultado inicial: tests, typecheck y build compatibles, pero persistían advisories por `postcss 8.4.31` y `sharp 0.34.5`
  - remediación final: `overrides` selectivos para `postcss 8.5.24` y `sharp 0.35.3`

## 5. Intentos realizados

### Intento 1

- versión: `next@15.5.21`
- comando: `npm install next@15.5.21`
- archivos tocados: `package.json`, `package-lock.json`, `next-env.d.ts`
- tests: PASS
- typecheck: PASS
- build: FAIL
- motivo: firmas de route handlers incompatibles con el segundo argumento exigido por Next 15+
- acción: reversión completa del intento

### Intento 2

- versión: `next@16.2.12`
- comando: `npm install next@16.2.12`
- cambio mecánico aplicado:
  - `params` de route handlers convertidos a `Promise<...>` con `await params`
  - `searchParams` de `/login` convertido a `Promise<...>` con resolución async
- tests: PASS
- typecheck: PASS
- build: PASS
- audit: todavía con vulnerabilidades `high`
- acción: se conservó como base del candidato

### Intento 3

- versión: `next@16.2.12` con overrides
- comandos:
  - `npm install next@16.2.12`
  - actualización controlada de `package.json` con:
    - `postcss: 8.5.24`
    - `sharp: 0.35.3`
  - `npm install`
- tests: PASS
- typecheck: PASS
- build: PASS
- audit: `critical = 0`, `high = 0`
- acción: candidato final conservado

## 6. Versión elegida o motivo de bloqueo

- versión elegida: `next@16.2.12`
- React mantenido: `18.3.1`
- React DOM mantenido: `18.3.1`
- NextAuth mantenido: `4.24.15`
- motivo:
  - fue la mínima ruta mayor comprobada localmente que permitió conservar compatibilidad funcional y cerrar completamente `npm audit`
  - la ruta `15.x` requería la misma migración async y además no resolvía seguridad

## 7. Cambios de Next.js

- dependencia `next` actualizada de `14.2.13` a `^16.2.12`
- build final verificado con `Next.js 16.2.12 (Turbopack)`
- desaparecieron los warnings previos de `DYNAMIC_SERVER_USAGE` durante build
- no fue necesario introducir `proxy.ts`
- no fue necesario tocar `next.config.mjs`

## 8. Cambios de React

- `react` mantenido en `18.3.1`
- `react-dom` mantenido en `18.3.1`
- no se requirió salto a React 19
- no hubo cambios de componentes client/server por compatibilidad de React

## 9. Cambios de TypeScript

- `typescript` se mantuvo en `5.7.3`
- `apps/topology-next/tsconfig.json` quedó ajustado por compatibilidad con Next 16:
  - `jsx: "react-jsx"`
  - inclusión de `.next/dev/types/**/*.ts`
- no se modificó `tsconfig.typecheck.json`

## 10. Cambios de NextAuth

- `next-auth` se mantuvo en `4.24.15`
- peer dependencies verificadas localmente:
  - soporta `next` `^15 || ^16`
  - soporta `react` `^18`
- `/api/auth/[...nextauth]` continuó en el árbol de rutas final de producción
- navegación a `/control` redirigió correctamente a `/login?callbackUrl=%2Fcontrol` bajo entorno sin providers OAuth configurados
- no se requirió migración a Auth.js / NextAuth 5

## 11. Middleware

- no existe `middleware.ts` ni `proxy.ts` en `apps/topology-next`
- no se agregó middleware nuevo
- la protección observada depende de `next-auth` y lógica de sesión existente

## 12. Route handlers

- se adaptaron mecánicamente a API async de Next 15/16 los handlers con `params` en:
  - `src/app/api/assets/[id]/children/route.ts`
  - `src/app/api/assets/[id]/devices/route.ts`
  - `src/app/api/assets/[id]/route.ts`
  - `src/app/api/assets/[id]/tree/route.ts`
  - `src/app/api/control/policies/[id]/route.ts`
  - `src/app/api/locations/[id]/route.ts`
  - `src/app/api/projects/[projectId]/assets/offline/route.ts`
  - `src/app/api/projects/[projectId]/assets/route.ts`
  - `src/app/api/projects/[projectId]/route.ts`
  - `src/app/api/projects/[projectId]/sectors/route.ts`
  - `src/app/api/projects/[projectId]/topology/route.ts`
  - `src/app/api/projects/[projectId]/topology/views/route.ts`
  - `src/app/api/sectors/[sectorId]/assets/route.ts`
  - `src/app/api/sectors/[sectorId]/route.ts`
  - `src/app/api/topology-links/[id]/route.ts`
  - `src/app/api/topology-views/[id]/layout/route.ts`
  - `src/app/api/topology-views/[id]/route.ts`
- patrón aplicado:
  - `params: { ... }` -> `params: Promise<{ ... }>`
  - `params.id` / `params.projectId` -> `const { ... } = await params`
- no se alteró lógica de negocio, autorización, queries ni payloads

## 13. APIs dinámicas

- `headers()` ya estaba usado de forma async en `src/lib/auth/control-auth-session.ts`
- `/login` se adaptó a `searchParams` async:
  - `searchParams?: Promise<{ callbackUrl?: string; error?: string }>`
  - resolución local `const resolvedSearchParams = (await searchParams) ?? {}`
- no hubo cambios en `cookies()` ni `draftMode()`
- no se introdujeron cambios de caching ni runtime `edge`

## 14. Configuración

- `apps/topology-next/package.json`
  - `next` actualizado a `^16.2.12`
  - `overrides` agregados:
    - `postcss: 8.5.24`
    - `sharp: 0.35.3`
- `apps/topology-next/package-lock.json`
  - regenerado por `npm install`
- `apps/topology-next/tsconfig.json`
  - ajustes de compatibilidad de Next 16 ya indicados
- `apps/topology-next/next.config.mjs`
  - sin cambios
- `apps/topology-next/vitest.config.ts`
  - sin cambios

## 15. Tests

- frontend:
  - `npm test`
  - resultado final: `72 passed` en `18` archivos
- autenticación:
  - `tests/unit/control-auth-session.test.ts`: PASS
  - `tests/unit/control-access.test.ts`: PASS
- feature flag:
  - `tests/unit/project.repository.test.ts`: PASS
  - `tests/unit/project.validators.test.ts`: PASS
  - `tests/unit/project.service.test.ts`: PASS

## 16. Build

- `npm run build`
- resultado final: PASS
- verificado fuera del sandbox por un `EPERM` del entorno al escribir `.next/trace`
- rutas críticas presentes en salida final:
  - `/api/auth/[...nextauth]`
  - `/api/control/access`
  - `/api/control/audit`
  - `/api/control/recommendations`
  - `/api/control/status`
  - `/control`
  - `/control/policies`
  - `/login`

## 17. Typecheck

- `npm run typecheck`
- resultado final: PASS
- verificado fuera del sandbox por un `EPERM` del entorno al escribir `tsconfig.typecheck.tsbuildinfo`

## 18. Auth

- comportamiento observado:
  - `/control` protegido y redirigiendo a `/login`
  - `callbackUrl` preservado
  - página `/login` renderizada sin errores de runtime
  - providers visibles pero deshabilitados por ausencia de `AUTH_GOOGLE_*` y `AUTH_GITHUB_*` en el entorno local
- conclusión:
  - auth compatible
  - validación completa de login OAuth real queda para entorno con providers configurados

## 19. Feature flag

- validación funcional preservada por tests de repository, validators y service
- el toggle `Control Paramétrico habilitado` siguió visible en el workspace
- no hubo cambios de contrato ni persistencia asociados a `parametric_control_enabled`

## 20. Validación visual

- servidor local aislado:
  - `npm run dev -- --hostname 127.0.0.1 --port 3101`
- viewports validados:
  - desktop `1440 x 900`
  - tablet `1024 x 768`
  - móvil `390 x 844`
- capturas fuera del repositorio:
  - `/private/tmp/midd-iot-prompt015-workspace-desktop.png`
  - `/private/tmp/midd-iot-prompt015-control-desktop.png`
  - `/private/tmp/midd-iot-prompt015-workspace-tablet.png`
  - `/private/tmp/midd-iot-prompt015-workspace-mobile.png`
  - `/private/tmp/midd-iot-prompt015-login-mobile.png`
- comprobaciones:
  - workspace carga en desktop, tablet y móvil
  - sidebar, toolbar, palette e inspector continúan presentes
  - `/control` redirige a `/login` sin crash
  - consola sin `warn` ni `error` nuevos
  - sin overflow horizontal:
    - móvil `scrollWidth = 390`
    - tablet `scrollWidth = 1024`

## 21. Audit antes/después

- antes:
  - archivo: `/tmp/midd-iot-prompt015-audit-before.json`
  - `critical = 1`
  - `high = 1`
  - `moderate = 0`
  - `low = 0`
- después:
  - archivo: `/tmp/midd-iot-prompt015-audit-after.json`
  - `critical = 0`
  - `high = 0`
  - `moderate = 0`
  - `low = 0`
- diferencia:
  - se eliminaron todas las vulnerabilidades remanentes de severidad alta y crítica

## 22. Regresiones

- no se detectaron regresiones en:
  - tests frontend
  - typecheck
  - build
  - protección de `/control`
  - visibilidad del toggle de `parametric_control_enabled`
  - estructura principal del workspace
- no se detectaron errores de consola durante la validación visual

## 23. Deuda

- el cierre de advisories depende de `overrides` de `postcss` y `sharp`, no de una versión upstream de Next 16 que ya incorpore esos fixes por sí sola
- persisten dependencias desactualizadas sin impacto bloqueante según `npm outdated`:
  - `react`, `react-dom`, `@types/*`, `vite`, `vitest`, `typescript`, `zod`, `zustand`, `pg`, `@xyflow/react`
- la validación OAuth real no se pudo completar por falta de providers configurados en local

## 24. Riesgos

- riesgo principal: los `overrides` fuerzan paquetes transitivos (`postcss`, `sharp`) por encima de la selección original del árbol de Next; hoy pasan tests y build, pero deben observarse en validación humana y smoke de UI post-merge
- el build y typecheck requieren ejecución fuera del sandbox de Codex por restricciones de escritura del entorno, aunque el código resultó compatible
- el smoke E2E obligatorio se ejecutó sobre el runtime original, no sobre este clon, por instrucción explícita de aislamiento
- deuda estructural heredada, no introducida por este prompt:
  - auditoría runtime sigue siendo best-effort
  - no existe atomicidad RabbitMQ/PostgreSQL en la publicación/persistencia
  - warning operativo recurrente de revisar compatibilidad de PostGIS/containers según plataforma sigue fuera del alcance de este upgrade

## 25. Readiness

- estado: `READY_FOR_NEXT_MAJOR_UPGRADE_COMMIT_WITH_WARNINGS`
- justificación:
  - `critical = 0`
  - `high = 0`
  - tests, typecheck, build, visual, Python, engine, Compose y smoke quedaron en PASS
  - quedan warnings no bloqueantes por uso de `overrides` selectivos y por ausencia de providers OAuth para prueba real de login

## 26. Próximo paso

- siguiente intervención recomendada: revisar y publicar el upgrade mediante validación humana final del branch `chore/topology-next-major-upgrade`, con foco en smoke UI post-merge y observación de los `overrides` de `postcss`/`sharp`.

## 27. Addendum Prompt 016

- Prompt ejecutado: `MIDD IOT — PROMPT 016`
- Fecha de revisión: `2026-07-28`
- Commit revisado: `3d16d9bc5420d641320ac4215cf821df33d7f20c`
- Alcance: revisión técnica final del upgrade mayor, análisis de overrides, repetición de validaciones críticas y recomendación controlada de integración
- Resultado: no se detectaron cambios funcionales accidentales en el diff del Prompt 015

## 28. Revisión del diff del upgrade

- `package.json`
  - cambio: `next` a `16.2.12` y `overrides` de `postcss`/`sharp`
  - conclusión: cambio alineado al objetivo de seguridad; sin expansión funcional
- `tsconfig.json`
  - cambio: `jsx: react-jsx` y agregado `.next/dev/types/**/*.ts`
  - conclusión: ajuste de compatibilidad mecánica de Next 16
- `src/app/login/page.tsx`
  - cambio: `searchParams` convertido a async con preservación de `callbackUrl` y `error`
  - conclusión: cambio mecánico, sin alteración funcional
- `src/app/api/**/[param]/route.ts`
  - cambio: `params` convertido a `Promise<...>` y consumo vía `await params`
  - conclusión: cambio mecánico, sin cambios de códigos HTTP, validadores, servicios ni autorización
- `docs/releases/topology_next_major_upgrade_readiness.md`
  - cambio: documentación de Prompt 015 y esta revisión final
  - conclusión: trazabilidad técnica necesaria

## 29. Revisión final de overrides

### `postcss`

- versión forzada: `8.5.24`
- origen upstream observado: `next@16.2.12` declara `postcss: 8.4.31`
- sin override: quedan dos instancias:
  - `next -> postcss@8.4.31`
  - `vite -> postcss@8.5.24`
- advisory reintroducido sin override:
  - `GHSA-6g55-p6wh-862q`
  - `GHSA-r28c-9q8g-f849`
  - adicional moderado `GHSA-qx2v-qp2m-jg93`
- severidad observada sin override: `high`
- compatibilidad semver con la declaración de `next`: no satisface el pin exacto `8.4.31`
- comportamiento observado con override: tests, typecheck y build siguen en PASS
- decisión: mantener como override temporal por seguridad
- criterio futuro de retiro: una versión de `next` que ya no dependa de `postcss <=8.5.17`

### `sharp`

- versión forzada: `0.35.3`
- origen upstream observado: `next@16.2.12` declara `optionalDependencies.sharp = ^0.34.5`
- sin override: `next -> sharp@0.34.5`
- advisory reintroducido sin override:
  - `GHSA-f88m-g3jw-g9cj`
- severidad observada sin override: `high`
- compatibilidad semver con la declaración de `next`: `0.35.3` no satisface `^0.34.5`
- comportamiento observado con override:
  - audit `0/0`
  - tests, typecheck y build PASS
  - `npm ls --json` reporta `extraneous` explicados:
    - `@img/sharp-wasm32@0.35.3`
    - `@emnapi/runtime@1.11.3`
- explicación del warning:
  - `@emnapi/runtime` entra vía `@img/sharp-wasm32`
  - `@img/sharp-wasm32` no figura en el lockfile definitivo, pero queda materializado por la instalación de `sharp@0.35.3`
- riesgo: warning real de consistencia del árbol, no bloqueo funcional comprobado
- decisión: mantener como override temporal por seguridad, con revisión humana obligatoria
- criterio futuro de retiro: una versión de `next` que declare un rango de `sharp` no vulnerable y reinstale sin `extraneous`

## 30. Experimento controlado sin overrides

- entorno: `/tmp/midd-iot-prompt016-topology-next-no-overrides`
- método:
  - copia aislada del frontend
  - remoción de `overrides`
  - fijación de versiones raíz al mismo baseline instalado
  - reinstalación limpia y validación
- resultado del árbol sin overrides:
  - `next -> postcss@8.4.31`
  - `next -> sharp@0.34.5`
  - `npm ls --json`: sin `problems`
- audit sin overrides:
  - `critical = 0`
  - `high = 3`
  - `moderate = 1`
  - `low = 0`
- advisories reintroducidos:
  - `postcss` por debajo de `8.5.18`
  - `sharp` por debajo de `0.35.0`
  - `next-auth` moderado por efecto de `next`
- validaciones sin overrides:
  - `npm test`: PASS (`72 passed`)
  - `npm run typecheck`: PASS
  - `npm run build`: PASS
- clasificación del experimento:
  - `OVERRIDES_REQUIRED_FOR_SECURITY`

## 31. Revalidación final del árbol definitivo

- comando de reinstalación: `npm ci`
- audit definitivo:
  - archivo: `/tmp/midd-iot-prompt016-audit-final.json`
  - `critical = 0`
  - `high = 0`
  - `moderate = 0`
  - `low = 0`
- validaciones frontend:
  - `npm test`: PASS (`72 passed`)
  - `npm run typecheck`: PASS
  - `npm run build`: PASS
- validaciones backend:
  - Python focalizado: `18 passed`
  - `apps/parametric-control-engine`: `35 passed`
  - `docker compose -f infra/containers/docker-compose.yaml config`: PASS
- validación visual mínima:
  - home carga en `3101`
  - `/control` redirige a `/login?callbackUrl=%2Fcontrol`
  - sin errores de consola del navegador
  - sin overflow horizontal en `1024` y `390`
- smoke E2E:
  - intento ejecutado desde el clon limpio
  - resultado: `NOT_RUN_REPOSITORY_PRESERVATION`
  - motivo: el clon limpio no dispone del entorno Python local requerido por el script y falla en `ModuleNotFoundError: sqlalchemy`
- decisión técnica de integración:
  - `READY_FOR_CONTROLLED_INTEGRATION_REVIEW_WITH_WARNINGS`
- justificación:
  - el árbol definitivo cumple seguridad y compatibilidad funcional
  - el override de `sharp` queda con warning por rango semver no satisfecho y `extraneous` opcionales explicados

## 32. Prompt 017 - Gate de compatibilidad de Sharp y reproducibilidad E2E

### Contexto del gate

- fecha: `2026-07-28`
- repositorio oficial validado: `/Users/joseluis/dev/iot-midd-paas-clean`
- rama validada: `chore/topology-next-major-upgrade`
- `HEAD`: `41bd4ab61fbce3311e86937619e51d3a61164b4b`
- `main`: `9937d2ad5d93c9e96c7a7632909a1047ea9f8311`
- `origin/main`: `6ababdbe2fb9c7ff35c1afe769b48ecea6f133ff`
- sin archivos staged
- sin tags nuevos
- residuo conocido aún excluido:
  - `docs/informe_intervencion_codex_chatgpt_2026-07-27.md`

### Inventario de uso real de imágenes

Hallazgos observados en el repositorio:

- `rg "from ['\"]next/image['\"]" apps/topology-next` -> sin coincidencias
- `rg "require\\(['\"]sharp['\"]\\)" apps/topology-next` -> sin coincidencias
- `rg "from ['\"]sharp['\"]" apps/topology-next` -> sin coincidencias
- `rg "<Image" apps/topology-next/src` -> sin coincidencias
- `rg "unoptimized" apps/topology-next` -> sin coincidencias
- `rg "_next/image" apps/topology-next` -> sin coincidencias
- `rg "images:" apps/topology-next` -> sin coincidencias
- `rg "loader:" apps/topology-next` -> sin coincidencias
- `rg "output:" apps/topology-next/next.config.mjs apps/topology-next` -> sin coincidencias
- `apps/topology-next/next.config.mjs` solo define `reactStrictMode` y `distDir`
- no se encontraron assets `.png/.jpg/.jpeg/.webp/.gif/.svg` dentro de `apps/topology-next`

Clasificación:

- `SHARP_OPTIONAL_CURRENTLY_UNUSED`
- `NEXT_IMAGE_RUNTIME_NOT_EXERCISED_NO_CURRENT_USAGE`

Justificación:

- la aplicación no consume `next/image`
- no existe loader custom ni configuración `images`
- no hay evidencia de rutas `/_next/image`
- no hay imágenes locales o remotas sometidas hoy al pipeline oficial de optimización

### Árbol de Sharp observado

Estado definitivo revalidado en `apps/topology-next`:

- `npm ci` -> PASS
- `npm audit --json` -> `critical=0`, `high=0`, `moderate=0`, `low=0`
- `npm ls sharp`:
  - `next@16.2.12 -> sharp@0.35.3 overridden`
- `npm explain sharp`:
  - `sharp@"0.35.3" (was "^0.34.5") from next@16.2.12`
- `npm ls postcss`:
  - `next@16.2.12 -> postcss@8.5.24 overridden`
  - `vite@6.4.3 -> postcss@8.5.24 deduped`
- `npm ls --json`:
  - `problems` contiene solo:
    - `extraneous: @img/sharp-wasm32@0.35.3`
    - `extraneous: @emnapi/runtime@1.11.3`
- `npm ls --all`:
  - sin `invalid`
  - solo `UNMET OPTIONAL DEPENDENCY` esperables por plataforma

Metadatos observados:

- `process.platform process.arch`: `darwin arm64`
- `next@16.2.12` publicado en npm declara `optionalDependencies.sharp = ^0.34.5`
- `sharp@0.35.3` publicado en npm declara paquetes opcionales por plataforma `@img/sharp-*` y `@img/sharp-libvips-*`
- `sharp@0.35.3` publicado en npm declara `engines.node >=20.9.0`

Interpretación técnica:

- el árbol queda seguro y funcional
- el warning persistente no es de vulnerabilidad sino de consistencia semver
- los `extraneous` observados quedan acotados al paquete WASM de Sharp y a `@emnapi/runtime`

### Prueba directa de Sharp

Prueba nativa ejecutada en memoria:

- creación de imagen RGBA mínima
- `resize`
- salida PNG en memoria
- validación de bytes no vacíos

Resultado Apple Silicon:

- `sharp=0.35.3`
- `vips=8.18.3`
- `platform=darwin`
- `arch=arm64`
- salida: `91` bytes
- clasificación: PASS

### Alternativas evaluadas

#### Alternativa A - Estado actual

- `next@16.2.12`
- override `postcss@8.5.24`
- override `sharp@0.35.3`

Resultado:

- audit en cero
- `npm test`: PASS (`72 passed`)
- `npm run typecheck`: PASS
- `npm run build`: PASS
- prueba nativa de Sharp: PASS
- smoke E2E desde clon limpio: PASS

#### Alternativa B - Override específico bajo `next`

Entorno:

- `/tmp/midd-iot-prompt017-altb.1iXns0`

Cambio:

- `overrides.next.postcss = 8.5.24`
- `overrides.next.sharp = 0.35.3`

Resultado:

- instalación: PASS
- audit: `0 vulnerabilities`
- tests: PASS (`72 passed`)
- typecheck: PASS
- build: PASS
- Sharp nativo: PASS
- warning persistente:
  - `@img/sharp-wasm32 extraneous`
  - `@emnapi/runtime extraneous`
- mejora frente al estado actual: ninguna

Conclusión:

- no justifica reemplazar el estado actual

#### Alternativa C - `npm ci --omit=optional`

Entorno:

- `/tmp/midd-iot-prompt017-altc.t5AMcb`

Resultado:

- instalación: PASS (`129` paquetes)
- audit: `0 vulnerabilities`
- `npm ls sharp`: vacío
- `require('sharp')`: `MODULE_NOT_FOUND`
- tests: FAIL
  - falta `@rollup/rollup-darwin-arm64`
- build: FAIL
  - Next cae a bindings WASM y Turbopack informa falta de bindings nativos `@next/swc-darwin-arm64`

Conclusión:

- `SHARP_CAN_BE_OMITTED_SAFELY` rechazado
- omitir opcionales rompe toolchain nativo del frontend

#### Alternativa D - Sharp como dependencia raíz explícita

Entorno:

- `/tmp/midd-iot-prompt017-altd.ld2sAv`

Cambio:

- agregado `dependencies.sharp = 0.35.3`

Resultado:

- instalación: PASS
- audit: `0 vulnerabilities`
- tests: PASS (`72 passed`)
- typecheck: PASS
- build: PASS
- Sharp nativo: PASS
- `npm ls sharp`:
  - `next -> sharp@0.35.3 deduped`
  - `root -> sharp@0.35.3 overridden`
- warning persistente:
  - `@img/sharp-wasm32 extraneous`
  - `@emnapi/runtime extraneous`
- el desacople semver con `^0.34.5` permanece

Conclusión:

- no aporta una mejora suficiente sobre A/E

### Decisión sobre Sharp

Clasificación exacta:

- `SHARP_OVERRIDE_ACCEPTABLE_TEMPORARILY`

Justificación:

- seguridad en cero
- no existe uso real actual de `next/image`
- Sharp fue validado funcionalmente en Apple Silicon y Linux amd64
- build, tests y typecheck permanecen en PASS
- las alternativas B y D no mejoran materialmente la consistencia
- la alternativa C rompe el toolchain nativo

Deuda explícita:

- `0.35.3` sigue fuera del rango `^0.34.5` publicado por `next@16.2.12`
- `npm ls --json` mantiene `extraneous` opcionales explicados

Criterio de retiro del override:

- adoptar una versión de `next` que publique un rango de `sharp` no vulnerable y consistente con una instalación limpia sin `extraneous`

### Validación Linux amd64

Entorno:

- copia temporal: `/tmp/midd-iot-prompt017-alta.HPf7LD`
- imagen: `node:22-bullseye`
- modo: emulación `--platform=linux/amd64` sobre Docker Desktop `aarch64`

Resultado:

- `npm ci`: PASS
- audit: `0 vulnerabilities`
- `npm ls sharp`: `next -> sharp@0.35.3 overridden`
- Sharp nativo: PASS
  - `platform=linux`
  - `arch=x64`
  - `sharp=0.35.3`
  - `vips=8.18.3`
- `npm test`: PASS (`72 passed`)
- `npm run typecheck`: PASS
- `npm run build`: PASS

Clasificación:

- Linux amd64 validado satisfactoriamente

### Entorno Python reproducible

Mecanismo oficial observado:

- `venv/` local e ignorado
- dependencias base en `requirements.txt`
- dependencias de testing en `tests/requirements-test.txt`
- script canónico del repo: `./setup_venv.sh`

Acción ejecutada:

- `./setup_venv.sh` en el clon limpio

Resultado:

- `venv` creado en el clon limpio
- Python: `3.12.0`
- imports críticos verificados:
  - `sqlalchemy 2.0.35`
  - `paho-mqtt` import PASS

Causa del fallo heredado del Prompt 016:

- clasificación principal: `PYTHON_ENV_NOT_CREATED`
- detalle:
  - el script `scripts/smoke_control_engine_end_to_end.sh` intenta `venv/bin/python`
  - al no existir `venv`, cae a `python3`
  - el `python3` del host no tenía `sqlalchemy`

### Smoke E2E desde el clon limpio

Preflight observado:

- `postgresql`, `rabbitmq`, `mosquitto` y `topology-ui` accesibles por puertos canónicos
- `/api/control/status` responde `200 OK`

Ejecución:

- `PYTHONDONTWRITEBYTECODE=1 ./scripts/smoke_control_engine_end_to_end.sh`

Resultado:

- clasificación exacta: `SMOKE_E2E_PASS_CLEAN_REPOSITORY`
- `overall=PASS`
- `exit_code=0`
- `contract-level`: PASS
- `component-level`: PASS
- `broker-level`: PASS
- `database-level`: PASS
- `full E2E`: PASS

### Validaciones finales consolidadas

- frontend:
  - `npm test`: PASS (`72 passed`)
  - `npm run typecheck`: PASS
  - `npm run build`: PASS
- backend focalizado:
  - `18 passed`
- parametric-control-engine:
  - `35 passed`
- Docker Compose:
  - `docker compose -f infra/containers/docker-compose.yaml config`: PASS
- smoke real:
  - `SMOKE_E2E_PASS_CLEAN_REPOSITORY`

### Riesgos y deuda

- warning semver documentado entre `next@16.2.12` y `sharp@0.35.3`
- `extraneous` opcionales de Sharp aún visibles en `npm ls --json`
- validación visual desktop/tablet/mobile no fue reejecutada en este prompt porque el alcance se concentró en compatibilidad de Sharp y reproducibilidad E2E sobre el mismo `HEAD` ya revisado en Prompt 016

### Decisión de integración

Decisión exacta:

- `READY_FOR_LOCAL_CONTROLLED_MERGE_REHEARSAL_WITH_WARNINGS`

Justificación:

- audit final en cero
- frontend, backend, engine, compose y smoke real en PASS
- Sharp probado en Apple Silicon y Linux amd64
- persiste un warning documentado, pero no se observó inconsistencia bloqueante ni regresión funcional

## 33. Prompt 018 - Ensayo local controlado de integración de Next.js

### Resultado del ensayo

- relación entre ramas:
  - merge base `9937d2ad5d93c9e96c7a7632909a1047ea9f8311`
  - `main` sin commits exclusivos
  - `chore/topology-next-major-upgrade` con `2` commits exclusivos
- clasificación previa:
  - `FAST_FORWARD_CANDIDATE`
- método:
  - worktree temporal en `/tmp/midd-iot-prompt018-merge-rehearsal.W7UoPI`
  - rama temporal segura `rehearsal-prompt018-next-upgrade`
  - integración mediante `git merge --ff-only`
- resultado:
  - fast-forward limpio
  - sin conflictos
  - sin merge commit
  - sin diferencias de contenido respecto de `chore/topology-next-major-upgrade`

### Clasificación de historia

- `HISTORY_CLEAN_FAST_FORWARD`

Motivos:

- trazabilidad clara entre el commit funcional `3d16d9b` y el documental `41bd4ab`
- no fue necesario commit temporal
- no se detectó pérdida de commits ni cambios paralelos inesperados

### Validaciones ejecutadas sobre el resultado integrado

- frontend:
  - `npm ci`: PASS
  - `npm audit --json`: `0` critical, `0` high, `0` moderate, `0` low
  - `npm test`: PASS (`72 passed`)
  - `npm run typecheck`: PASS
  - `npm run build`: PASS
- Sharp:
  - importación y transformación nativa PASS
  - `sharp 0.35.3`
  - `vips 8.18.3`
  - `darwin arm64`
- auth y feature flag:
  - `NextAuth 4.24.15` preservado
  - estrategia `jwt` preservada
  - `/control` protegido con redirect a `/login?callbackUrl=%2Fcontrol`
  - `parametric_control_enabled` preservado en persistencia, validación y UI
- visual:
  - desktop, tablet y móvil PASS
  - sin overflow horizontal
  - sin errores de consola del navegador
- Python y backend:
  - `./setup_venv.sh`: PASS
  - tests focalizados: `18 passed`
  - `apps/parametric-control-engine/tests`: `35 passed`
- plataforma:
  - `docker compose -f infra/containers/docker-compose.yaml config`: PASS
  - smoke real: `SMOKE_E2E_PASS_MERGE_REHEARSAL`

### Warnings

- se mantiene la deuda conocida:
  - override temporal `sharp@0.35.3` fuera del rango `^0.34.5` declarado por `next@16.2.12`
  - `@img/sharp-wasm32` y `@emnapi/runtime` continúan como `extraneous` opcionales explicados
- en la validación visual local aparecieron warnings de `next-auth` por `NEXTAUTH_URL` y `NO_SECRET` ausentes en el entorno dev del ensayo; no implicaron bypass ni regresión funcional

### Readiness final

- decisión técnica exacta:
  - `READY_FOR_CONTROLLED_LOCAL_INTEGRATION_WITH_WARNINGS`
- estado exacto del ensayo:
  - `COMPLETED_LOCAL_MERGE_REHEARSAL_WITH_WARNINGS`
- interpretación:
  - la integración local futura puede planificarse sin esperar más validaciones técnicas de este mismo alcance, pero manteniendo explícita la deuda temporal de Sharp y sin asumir que este ensayo autoriza merge oficial, push, tag o release por sí solo

## 34. Prompt 019 - Cierre documental y paquete controlado de integración

### Estado documental inicial

- `docs/releases/prompt017_sharp_clean_repo_gate_report_2026-07-28.md` existía en working tree pero seguía untracked
- `docs/releases/prompt018_local_merge_rehearsal_report_2026-07-28.md` ya estaba tracked mediante `c80c18b`
- `docs/releases/topology_next_major_upgrade_readiness.md` ya incluía Prompt 017 y Prompt 018
- persistía el residuo excluido:
  - `docs/informe_intervencion_codex_chatgpt_2026-07-27.md`

### Inconsistencias encontradas

- el informe de Prompt 018 todavía declaraba campos pendientes o autorreferenciales:
  - `ver respuesta final de la sesión`
  - `pendiente de registrar`
  - `pendiente del commit documental`
- el estado Git real ya no coincidía con esos placeholders porque el cierre documental de Prompt 018 sí había sido committeado en `c80c18b`
- `prompt017` seguía fuera del índice y de la historia pese a ser parte de la trazabilidad oficial

### Documentos incorporados

- `docs/releases/prompt017_sharp_clean_repo_gate_report_2026-07-28.md`
- `docs/releases/prompt018_local_merge_rehearsal_report_2026-07-28.md`
- `docs/releases/topology_next_major_upgrade_readiness.md`
- `docs/releases/topology_next_controlled_integration_manifest.md`

### Correcciones realizadas

- normalización del informe de Prompt 018 con el commit real `c80c18b08bce147fcd9ef26db9ad63583e561c29`
- cierre de los campos pendientes de commit, staged y worktree final del Prompt 018
- creación del manifiesto declarativo de integración futura sin ejecutar el fast-forward
- consolidación de Prompt 019 en este readiness

### Commit padre de la fase

- `c80c18b08bce147fcd9ef26db9ad63583e561c29`

### Estado final de trazabilidad

- trazabilidad 015 -> 016 -> 017 -> 018 -> 019 consolidada
- sin cambios productivos
- sin secretos ni credenciales detectadas en los documentos revisados
- con deuda explícita preservada sobre `sharp`, `postcss` y validación OAuth real

### Relación con `main`

- merge base estable en `9937d2ad5d93c9e96c7a7632909a1047ea9f8311`
- `main` sin commits exclusivos respecto del branch de upgrade
- fast-forward sigue siendo la expectativa técnica

### Relación con `origin/main`

- `origin/main` permanece en `6ababdbe2fb9c7ff35c1afe769b48ecea6f133ff`
- la rama de upgrade continúa local y sin publicación

### Decisión final

- clasificación documental:
  - `DOCUMENTATION_TRACEABILITY_COMPLETE_WITH_WARNINGS`
- decisión técnica:
  - `READY_FOR_EXPLICIT_LOCAL_FAST_FORWARD_AUTHORIZATION_WITH_WARNINGS`

### Prohibición de publicación

- Prompt 019 no autoriza merge real, push, tag, release ni publicación de rama

### Próximo paso recomendado

- solicitar una autorización explícita posterior si se desea ejecutar el fast-forward local documentado en el manifiesto

## 35. Prompt 020 - Integración local fast-forward controlada

### Estado previo

- `main` en `9937d2ad5d93c9e96c7a7632909a1047ea9f8311`
- rama fuente `chore/topology-next-major-upgrade` en `f03ec4a2052f2eb855fa466f490b06c4f6fe2689`
- merge base igual a `main`
- `0` commits exclusivos de `main`
- `4` commits exclusivos de la rama fuente
- fast-forward validado como posible y sin conflictos

### Autorización

- Prompt 020 constituyó la autorización explícita requerida por el manifiesto para ejecutar:
  - `git switch main`
  - `git merge --ff-only chore/topology-next-major-upgrade`

### Fast-forward

- resultado del merge:
  - PASS
  - sin conflictos
  - sin merge commit
- `main` alcanzó:
  - `f03ec4a2052f2eb855fa466f490b06c4f6fe2689`
- después del merge:
  - `main` y `chore/topology-next-major-upgrade` quedaron idénticos

### Resultado

- clasificación del merge:
  - `LOCAL_FAST_FORWARD_PASS`
- clasificación del smoke sobre `main`:
  - `SMOKE_E2E_PASS_INTEGRATED_MAIN`
- clasificación Git final esperada tras el commit documental:
  - `INTEGRATED_MAIN_CLEAN_WITH_DOCUMENTATION_COMMIT`

### Validaciones postintegración

- frontend:
  - `npm ci`: PASS
  - `npm audit --json`: `0` critical, `0` high, `0` moderate, `0` low
  - `npm test`: PASS (`72 passed`)
  - `npm run typecheck`: PASS
  - `npm run build`: PASS
- Sharp:
  - importación y transformación nativa PASS
  - `sharp 0.35.3`
  - `vips 8.18.3`
  - `darwin arm64`
- auth y feature flag:
  - `NextAuth 4.24.15` preservado
  - estrategia `jwt` preservada
  - `/control` protegido y redirigiendo a `/login?callbackUrl=%2Fcontrol`
  - `parametric_control_enabled` preservado
- backend y plataforma:
  - `18 passed`
  - `35 passed`
  - `docker compose -f infra/containers/docker-compose.yaml config`: PASS
  - smoke E2E real en `main`: PASS

### Warnings

- override temporal `sharp@0.35.3`
- override temporal `postcss@8.5.24`
- OAuth real no ejecutado
- warnings locales de NextAuth en el entorno dev
- validación visual postintegración directa ejecutada en desktop y redirect auth; tablet/móvil quedaron sin rerun independiente, aunque no hubo delta de contenido respecto del hash ya validado en Prompt 018

### Estado final de `main`

- `main` quedó retenido localmente con la integración aplicada
- `origin/main` continuó intacto en `6ababdbe2fb9c7ff35c1afe769b48ecea6f133ff`
- la rama fuente siguió preservada en `f03ec4a2052f2eb855fa466f490b06c4f6fe2689`

### Prohibición de push

- esta fase no autoriza push, publicación, tag ni release

### Próximo paso

- realizar una revisión humana final y decidir si se autoriza la publicación controlada de `main`, manteniendo mientras tanto la integración solo en estado local

## 36. Prompt 021 - Cierre del gate visual postintegración

### Criterio parcial heredado

- Prompt 020 había dejado un único criterio parcial:
  - rerun visual directo independiente en `tablet` y `móvil`
  - identificación concluyente del toggle `parametric_control_enabled`

### Validaciones ejecutadas

- Git:
  - identificación del commit exacto de Prompt 020:
    - `2851fcbbadedc5d6538af6a1d437572ed4629516`
  - confirmación de historia limpia postintegración:
    - rama de upgrade intacta en `f03ec4a2052f2eb855fa466f490b06c4f6fe2689`
    - `main` con un commit documental exclusivo al inicio de Prompt 021
- preflight técnico sobre `main`:
  - `npm ci`: PASS
  - `npm audit --json`: `0` critical, `0` high, `0` moderate, `0` low
  - `npm test`: PASS (`72 passed`)
  - `npm run typecheck`: PASS
  - `npm run build`: PASS
  - `docker compose -f infra/containers/docker-compose.yaml config`: PASS
- visual directo:
  - desktop `1440 x 900`: PASS
  - tablet `1024 x 768`: PASS
  - móvil `390 x 844`: PASS
- auth:
  - `/control` redirige a `/login?callbackUrl=%2Fcontrol`
  - `/api/control/access` devuelve `401` sin sesión
  - providers visibles y deshabilitados al no haber credenciales OAuth configuradas
- feature flag:
  - toggle identificado en la tarjeta `Proyecto`
  - estado inicial `false`
  - cambio a `true` con `PATCH 200`
  - restauración a `false` con `PATCH 200`
  - persistencia restaurada al valor original

### Resultados

- clasificación del feature flag:
  - `FEATURE_FLAG_VISUAL_AND_STRUCTURAL_PASS`
- clasificación de auth:
  - `AUTH_REDIRECT_PASS_OAUTH_NOT_RUN`
- clasificación documental:
  - `POST_INTEGRATION_VISUAL_TRACEABILITY_COMPLETE_WITH_WARNINGS`
- clasificación Git final esperada tras el commit documental:
  - `MAIN_READY_LOCAL_ONLY_WITH_WARNINGS`

### Estado final

- el gate visual postintegración quedó cerrado
- `main` local quedó retenido con:
  - upgrade integrado
  - cierre documental de Prompt 020
  - readiness listo para una eventual autorización humana de publicación
- `origin/main` continuó intacto en `6ababdbe2fb9c7ff35c1afe769b48ecea6f133ff`

### Warnings

- override temporal `sharp@0.35.3`
- override temporal `postcss@8.5.24`
- warnings locales de `NEXTAUTH_URL` y `NO_SECRET` en entorno dev
- OAuth real no ejecutado con providers configurados

### Readiness para publicación

- decisión técnica:
  - `READY_FOR_EXPLICIT_PUBLICATION_AUTHORIZATION_WITH_WARNINGS`
- alcance:
  - no autoriza push
  - no autoriza tag
  - no autoriza release
  - solo declara que `main` local queda listo para una autorización humana posterior

### Próximo paso

- solicitar una autorización humana explícita si se desea publicar `main` de forma controlada

## 37. Prompt 022 - Publicación controlada de `main`

### Autorización

- Prompt 022 constituyó la autorización explícita para:
  - `git fetch --prune origin`
  - `git push --dry-run origin main:main`
  - `git push origin main:main`
  - validación post-push
  - documentación local posterior
  - segundo push exclusivo para el commit documental de esta fase

### Precondiciones

- `main` en `8036bf79b49314cfef490f2cf107ff72f96747be`
- `origin/main` en `6ababdbe2fb9c7ff35c1afe769b48ecea6f133ff`
- rama de upgrade preservada en `f03ec4a2052f2eb855fa466f490b06c4f6fe2689`
- historia local íntegra y lineal
- worktree limpio salvo el residual excluido
- validaciones críticas heredadas en PASS

### Fetch y remoto

- `git fetch --prune origin`: PASS
- `origin/main` no avanzó
- `origin/main` siguió siendo ancestro de `main`
- divergencia previa:
  - remoto `0`
  - local `7`
- clasificación remota:
  - `REMOTE_FAST_FORWARD_SAFE`

### Dry-run y push principal

- `git push --dry-run origin main:main`: PASS
- rango anunciado:
  - `6ababdb..8036bf7`
- `git push origin main:main`: PASS
- hash publicado principal:
  - `8036bf79b49314cfef490f2cf107ff72f96747be`

### Verificación post-push

- `git fetch origin`: PASS
- `git rev-parse main` = `git rev-parse origin/main`
- `git ls-remote --heads origin refs/heads/main` confirmó el mismo hash
- divergencia:
  - `0 0`

### Validación post-push

- `npm audit --json`: `0` critical, `0` high, `0` moderate, `0` low
- `npm test`: PASS (`72 passed`)
- `npm run typecheck`: PASS
- `npm run build`: PASS
- `docker compose -f infra/containers/docker-compose.yaml config`: PASS

### Warnings

- override temporal `sharp@0.35.3`
- override temporal `postcss@8.5.24`
- OAuth real no ejecutado
- warnings locales `NEXTAUTH_URL` y `NO_SECRET`

### Estado final

- `main` quedó publicado en `origin/main`
- el commit documental de Prompt 022 deja trazabilidad adicional local antes de su publicación
- sin force push
- sin tag
- sin release

### Próximo paso

- evaluar una autorización humana posterior para crear un tag de release sobre `origin/main`, sin ejecutarlo en esta fase

## 38. Prompt 023 - Cierre verificable de publicación y readiness para tag

### Verificación Git

- commit documental exacto de Prompt 022:
  - `46ee3157370d3e0975cec80e3d5d625325754fff`
- padre del commit documental:
  - `8036bf79b49314cfef490f2cf107ff72f96747be`
- contenido del commit documental:
  - `docs/releases/prompt022_controlled_main_publication_report_2026-07-29.md`
  - `docs/releases/topology_next_major_upgrade_readiness.md`
  - `docs/releases/topology_next_controlled_integration_manifest.md`
- ramas que contienen el commit:
  - local `main`
  - remoto `origin/main`
- fetch de verificación:
  - `git fetch --prune origin`: PASS
- hash remoto tras fetch:
  - `origin/main = 46ee3157370d3e0975cec80e3d5d625325754fff`
- `ls-remote`:
  - `46ee3157370d3e0975cec80e3d5d625325754fff refs/heads/main`
- divergencia:
  - `origin/main...main = 0 0`
- árbol de decisión aplicado:
  - `PROMPT022_SECOND_PUSH_ALREADY_COMPLETE`

### Validaciones mínimas reejecutadas en Prompt 023

- `npm audit --json`:
  - `critical=0`
  - `high=0`
  - `moderate=0`
  - `low=0`
- `npm test`:
  - PASS
  - `72 passed`
- `npm run typecheck`:
  - PASS
- `npm run build`:
  - PASS
  - `Next.js 16.2.12 (Turbopack)`
- `docker compose -f infra/containers/docker-compose.yaml config`:
  - PASS

### Baseline remota

- archivo de baseline:
  - `docs/releases/topology_next_remote_baseline_after_prompt022.md`
- baseline remota estable:
  - sí
- hash remoto estable:
  - `46ee3157370d3e0975cec80e3d5d625325754fff`
- merge commits nuevos:
  - ninguno
- rama de upgrade publicada:
  - no

### Readiness para tag

- decisión:
  - `READY_FOR_EXPLICIT_TAG_AUTHORIZATION_WITH_WARNINGS`
- fundamentos:
  - publicación de Prompt 022 completamente reconciliada
  - baseline remota verificable creada
  - validaciones mínimas de Prompt 023 en verde
  - no hubo regresiones productivas entre Prompt 022 y Prompt 023
- warnings vigentes:
  - override temporal `sharp@0.35.3`
  - override temporal `postcss@8.5.24`
  - OAuth real pendiente con providers configurados
  - warnings locales de `NEXTAUTH_URL` y `NO_SECRET`
- no autorizado en esta fase:
  - crear tag
  - crear release
  - publicar el commit documental de Prompt 023

### Estado final

- `origin/main` queda fijado como baseline remota en `46ee3157370d3e0975cec80e3d5d625325754fff`
- `main` local queda reservado para un único commit documental adicional de Prompt 023
- la publicación funcional queda cerrada y la siguiente decisión humana ya no es de publicación técnica de Prompt 022, sino de publicación documental de Prompt 023 y/o autorización explícita de tag

## 39. Prompt 024 - Publicación del cierre Prompt 023 y tag RC

### Publicación de Prompt 023

- commit documental de Prompt 023:
  - `a231887f332265a4773cfb0d574de268f43f2bdf`
- padre:
  - `46ee3157370d3e0975cec80e3d5d625325754fff`
- `git fetch --prune origin`:
  - PASS
- `origin/main` previo:
  - `46ee3157370d3e0975cec80e3d5d625325754fff`
- dry-run de `main`:
  - PASS
  - `46ee315..a231887`
- `git push origin main:main`:
  - PASS
- sincronización post-push:
  - `main = origin/main = a231887f332265a4773cfb0d574de268f43f2bdf`
  - divergencia `0 0`
  - `ls-remote` coincidente

### Convención de tag

- tags existentes previos:
  - `control-engine-mvp-rc1.1`
- convención explícita documentada en repositorio:
  - no se encontró una convención formal adicional
- nombre recomendado por Prompt 024:
  - `topology-next-next16-security-rc1`
- adaptación:
  - no fue necesaria
- disponibilidad:
  - libre local y remotamente al momento de crear el tag

### Validaciones mínimas reejecutadas en Prompt 024

- `npm audit --json`:
  - `critical=0`
  - `high=0`
  - `moderate=0`
  - `low=0`
- `npm test`:
  - PASS
  - `72 passed`
- `npm run typecheck`:
  - PASS
- `npm run build`:
  - PASS
  - `Next.js 16.2.12 (Turbopack)`
- `docker compose -f infra/containers/docker-compose.yaml config`:
  - PASS

### Tag release candidate

- tag creado:
  - `topology-next-next16-security-rc1`
- tipo:
  - anotado
- objeto tag:
  - `6f65fd4d5a1ca716fc2ffe25ee23889f71f980ea`
- commit target:
  - `a231887f332265a4773cfb0d574de268f43f2bdf`
- `git push origin refs/tags/topology-next-next16-security-rc1`:
  - PASS
- verificación remota:
  - `refs/tags/topology-next-next16-security-rc1 = 6f65fd4d5a1ca716fc2ffe25ee23889f71f980ea`
  - `refs/tags/topology-next-next16-security-rc1^{} = a231887f332265a4773cfb0d574de268f43f2bdf`
- baseline etiquetada:
  - `docs/releases/topology_next_tagged_baseline_after_prompt024.md`

### Readiness para release

- decisión:
  - `READY_FOR_EXPLICIT_RELEASE_AUTHORIZATION_WITH_WARNINGS`
- fundamentos:
  - Prompt 023 ya quedó publicado y sincronizado
  - el tag RC ya existe local y remoto
  - las validaciones mínimas volvieron a pasar sobre el commit etiquetado
  - la baseline etiquetada ya quedó documentada
- warnings vigentes:
  - override temporal `sharp@0.35.3`
  - override temporal `postcss@8.5.24`
  - OAuth real pendiente con providers configurados
  - warnings locales de `NEXTAUTH_URL` y `NO_SECRET`
- no autorizado en esta fase:
  - crear GitHub Release
  - publicar artefactos
  - mover el tag para incluir la documentación de Prompt 024

### Estado final

- `origin/main` queda sincronizado en `a231887f332265a4773cfb0d574de268f43f2bdf`
- `topology-next-next16-security-rc1` fija esa baseline publicada como release candidate
- la siguiente decisión humana ya no es de publicación ni de tagging, sino de autorización explícita de release

## Prompt 029 - Clon operativo writable

- bloqueo resuelto:
  - `BLOCKED_REPOSITORY_WRITE_ACCESS`
- clon fuente preservado:
  - `/Users/joseluis/dev/iot-midd-paas-clean`
- nueva ruta operativa para las siguientes fases:
  - `/Users/joseluis/dev/iot-midd-paas-auth-work`
- baseline local retenida en el nuevo clon:
  - `main = 55e2af58e71896770ad65e008656fcfa3c2d0342`
  - `origin/main = a231887f332265a4773cfb0d574de268f43f2bdf`
  - divergencia `0 1` antes del cierre documental de Prompt 029
- historia preservada:
  - commit local pendiente de Prompt 024
  - rama `chore/topology-next-major-upgrade`
  - tag `topology-next-next16-security-rc1`
- seguridad operativa:
  - sin copia de `.env.local`
  - sin copia de `.next`
  - sin copia de `node_modules`
  - sin copia del residual `docs/informe_intervencion_codex_chatgpt_2026-07-27.md`
- siguiente fase habilitada:
  - reanudar Prompt 028 exclusivamente en `/Users/joseluis/dev/iot-midd-paas-auth-work`

## Prompt 030 - Preparacion OAuth en clon writable

- estado:
  - completado en `/Users/joseluis/dev/iot-midd-paas-auth-work`
- `.env.local`:
  - ignorado y creado solo como archivo local
- `.env.local.example`:
  - creado y trackeado
- helper OAuth:
  - agregado para placeholders, parcialidad y prioridad `NEXTAUTH_*`
- GitHub:
  - listo para credenciales reales
- Google:
  - listo para credenciales reales
- validaciones:
  - `npm audit --json`: `0/0/0/0`
  - `npm test`: `83 passed`
  - `npm run typecheck`: PASS
  - `npm run build`: PASS
  - smoke local: `/login 200`, `/control 307`, `/api/control/access 401`
- OAuth real:
  - pendiente por decisión humana y credenciales reales
