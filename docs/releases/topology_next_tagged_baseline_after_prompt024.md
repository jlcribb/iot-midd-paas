# Topology Next Tagged Baseline After Prompt 024

## Identificacion

- fecha: `2026-07-29`
- repositorio: `/Users/joseluis/dev/iot-midd-paas-clean`
- rama: `main`
- remoto: `origin`
- tag: `topology-next-next16-security-rc1`
- tipo de tag: `annotated`
- objeto tag: `6f65fd4d5a1ca716fc2ffe25ee23889f71f980ea`
- commit target: `a231887f332265a4773cfb0d574de268f43f2bdf`
- `main`: `a231887f332265a4773cfb0d574de268f43f2bdf`
- `origin/main`: `a231887f332265a4773cfb0d574de268f43f2bdf`
- `ls-remote`:
  - `refs/heads/main = a231887f332265a4773cfb0d574de268f43f2bdf`
  - `refs/tags/topology-next-next16-security-rc1 = 6f65fd4d5a1ca716fc2ffe25ee23889f71f980ea`
  - `refs/tags/topology-next-next16-security-rc1^{} = a231887f332265a4773cfb0d574de268f43f2bdf`

## Contenido de la baseline

- Next.js:
  - `16.2.12`
- React:
  - `18.3.1`
- React DOM:
  - `18.3.1`
- NextAuth:
  - `4.24.15`
- TypeScript:
  - `5.7.3`
- Sharp:
  - `0.35.3` por override temporal
- PostCSS:
  - `8.5.24` por override temporal
- feature flag:
  - `parametric_control_enabled` preservado y validado
- auth:
  - redirect a `/login` preservado
  - OAuth real pendiente
- control paramétrico:
  - preservado funcionalmente
  - benchmark, auditoría y flujo E2E heredados sin regresión reportada

## Validaciones

- ejecutadas en Prompt 024:
  - `npm audit --json`: PASS, `0/0/0/0`
  - `npm test`: PASS, `72 passed`
  - `npm run typecheck`: PASS
  - `npm run build`: PASS
  - `docker compose -f infra/containers/docker-compose.yaml config`: PASS
- evidencia heredada:
  - visual desktop/tablet/móvil: PASS
  - feature flag: PASS
  - auth redirect: PASS
  - Sharp host y Linux amd64: PASS
  - Python focalizado: PASS
  - engine: PASS
  - smoke E2E integrado: PASS

## Warnings

- override temporal `sharp@0.35.3`
- override temporal `postcss@8.5.24`
- OAuth real no ejecutado con providers configurados
- warnings locales de `NEXTAUTH_URL` y `NO_SECRET`

## Estado

- tag publicado:
  - sí
- release creada:
  - no
- rama de upgrade publicada:
  - no
- readiness para release:
  - `READY_FOR_EXPLICIT_RELEASE_AUTHORIZATION_WITH_WARNINGS`
- clasificación operativa:
  - baseline etiquetada y verificable
