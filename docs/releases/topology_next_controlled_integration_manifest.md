# Topology Next Controlled Integration Manifest

## Identificacion

- repositorio: `/Users/joseluis/dev/iot-midd-paas-clean`
- rama fuente: `chore/topology-next-major-upgrade`
- rama destino futura: `main`
- HEAD fuente antes del commit documental del Prompt 019: `c80c18b08bce147fcd9ef26db9ad63583e561c29`
- HEAD fuente final informado externamente: consultar el commit local que incorpore este manifiesto y el cierre documental del Prompt 019
- `main`: `9937d2ad5d93c9e96c7a7632909a1047ea9f8311`
- `origin/main`: `6ababdbe2fb9c7ff35c1afe769b48ecea6f133ff`
- merge base: `9937d2ad5d93c9e96c7a7632909a1047ea9f8311`

## Tipo de integracion esperada

- modalidad esperada: `fast-forward`
- merge commit: no esperado
- resolucion de conflictos: no esperada
- historia esperada:
  - `main@9937d2a`
  - `3d16d9b` `chore(topology): upgrade Next.js security baseline`
  - `41bd4ab` `docs(topology): finalize Next.js upgrade review`
  - `c80c18b` `docs(topology): record local Next.js merge rehearsal`
  - `HEAD final de Prompt 019` informado externamente
- commits incluidos:
  - funcionales: `3d16d9b`
  - documentales: `41bd4ab`, `c80c18b` y el cierre de Prompt 019

## Precondiciones

- worktree limpio
- rama activa correcta
- hashes coincidentes con este manifiesto
- `main` sin movimientos inesperados
- `origin/main` sin movimientos inesperados
- rama de upgrade no publicada o publicacion explicitamente autorizada
- documentacion cerrada
- `npm audit` en cero `critical/high`
- tests frontend en verde
- typecheck en verde
- build en verde
- Compose config en verde
- smoke heredado en verde

## Comandos propuestos

Estos comandos quedan documentados de forma conceptual. No estan autorizados por el Prompt 019 y no fueron ejecutados en esta fase.

```bash
cd /Users/joseluis/dev/iot-midd-paas-clean
git switch main
git merge --ff-only chore/topology-next-major-upgrade
```

Aclaraciones:

- requieren autorizacion posterior explicita
- no incluyen `push`
- no incluyen `tag`
- no incluyen `release`
- no autorizan publicacion de la rama

## Validaciones postintegracion futuras

- Git:
  - `git status --short --branch`
  - `git log --oneline --decorate -5`
  - `git diff --check origin/main...HEAD`
- npm audit:
  - `cd apps/topology-next && npm audit --json`
- tests:
  - `cd apps/topology-next && npm test`
- typecheck:
  - `cd apps/topology-next && npm run typecheck`
- build:
  - `cd apps/topology-next && npm run build`
- auth:
  - verificar `/control`, redirect a `/login` y preservacion de `callbackUrl`
- feature flag:
  - verificar `parametric_control_enabled` en persistencia, validacion y UI
- visual:
  - desktop, tablet y movil
- Python:
  - verificar `./setup_venv.sh` o entorno equivalente antes de scripts Python
- engine:
  - `apps/parametric-control-engine/tests`
- Compose:
  - `docker compose -f infra/containers/docker-compose.yaml config`
- smoke:
  - `PYTHONDONTWRITEBYTECODE=1 ./scripts/smoke_control_engine_end_to_end.sh`

## Rollback futuro

Preservar conceptualmente el commit previo de `main` antes de autorizar la integracion. Si en una fase posterior se ejecuta el fast-forward y se necesita volver atras, el rollback debera apoyarse en el hash anterior de `main` registrado antes del merge, sin crear tags en esta etapa y sin ejecutar aqui ningun reset o rollback.

## Riesgos

- override temporal de `sharp@0.35.3` fuera del rango `^0.34.5` declarado por `next@16.2.12`
- override de `postcss@8.5.24`
- OAuth real pendiente de validacion con providers configurados
- dependencia del entorno local para reproducibilidad de Python, contenedores y smoke

## Decision

- integracion tecnicamente preparada
- ejecucion pendiente de autorizacion expresa
- clasificacion operativa propuesta: `READY_FOR_EXPLICIT_LOCAL_FAST_FORWARD_AUTHORIZATION_WITH_WARNINGS`

## Estado posterior a Prompt 020

- nota:
  - las secciones anteriores conservan el estado histórico documentado hasta Prompt 019; este bloque agrega exclusivamente el cierre ejecutado en Prompt 020 sin reescribir precondiciones ni comandos históricos
- integracion local ejecutada:
  - sí
- rama integrada localmente:
  - `main`
- HEAD de `main` inmediatamente después del fast-forward:
  - `f03ec4a2052f2eb855fa466f490b06c4f6fe2689`
- push pendiente:
  - sí
- publicacion pendiente:
  - sí
- tag pendiente:
  - sí
- release pendiente:
  - sí
- validacion postintegracion realizada:
  - sí
- resultado operativo:
  - integración local retenida con warnings conocidos, sin autorización de publicación

## Estado posterior a Prompt 021

- gate visual postintegracion:
  - cerrado
- commit exacto de Prompt 020:
  - `2851fcbbadedc5d6538af6a1d437572ed4629516`
- HEAD de `main` al iniciar Prompt 021:
  - `2851fcbbadedc5d6538af6a1d437572ed4629516`
- HEAD final de `main` tras el cierre documental de Prompt 021:
  - el commit local de cierre documental de Prompt 021 en `main`; su hash exacto se registra en la evidencia Git final de la sesión y no se incrusta aquí para evitar autorreferencia del propio commit
- publicacion autorizada:
  - no
- push autorizado:
  - no
- precondiciones restantes:
  - decisión humana explícita de publicación
  - validación OAuth real en entorno con providers, si se requiere antes de publicar
- autorización siguiente necesaria:
  - autorización humana explícita para publicar `main` de forma controlada
- resultado operativo:
  - `main` queda listo solo para una autorización posterior de publicación, con warnings heredados y sin cambios productivos adicionales
