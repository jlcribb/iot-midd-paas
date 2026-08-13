# Control OAuth & Session Layer

## Objetivo

Agregar autenticación real sobre `apps/topology-next` para que el RBAC
operacional existente se alimente de un actor autenticado y no dependa
principalmente del fallback `x-control-*`.

OAuth autentica quién es el usuario.
RBAC decide qué puede hacer.
Auditoría registra qué hizo.
El worker sigue independiente.

## Stack

- `next-auth` sobre App Router
- sesión `jwt`
- providers iniciales:
  - Google
  - GitHub

La ruta `GET /api/auth/session` queda provista por NextAuth dentro de
`/api/auth/[...nextauth]`.

## Variables de entorno

- `AUTH_SECRET`
- `AUTH_URL`
- `AUTH_GOOGLE_ID`
- `AUTH_GOOGLE_SECRET`
- `AUTH_GITHUB_ID`
- `AUTH_GITHUB_SECRET`
- `CONTROL_AUTH_ADMIN_EMAILS`
- `CONTROL_AUTH_OPERATOR_EMAILS`
- `CONTROL_AUTH_VIEWER_EMAILS`
- `CONTROL_RBAC_ALLOW_DEV_FALLBACK`

Compatibilidad:

- `AUTH_SECRET` se usa como secreto principal;
- `AUTH_URL` se proyecta a `NEXTAUTH_URL` para compatibilidad con `next-auth` v4.

## Login y logout

- página de login: `/login`
- logout operativo: botón de cierre de sesión en `/control` y `/control/policies`
- página auxiliar: `/logout`

Si un usuario no autenticado intenta entrar a `/control` o
`/control/policies`, la app lo redirige a `/login` con `callbackUrl`.

## Resolución del actor

Prioridad:

1. sesión OAuth válida;
2. fallback local/dev **solamente** si `CONTROL_RBAC_ALLOW_DEV_FALLBACK=true`
   fue configurado de forma explícita y no estamos en producción.

El fallback queda deshabilitado por defecto, incluso bajo `NODE_ENV=development`.
El modo development no constituye una frontera de confianza. Cuando se habilita,
el fallback puede conceder capacidades amplias mediante `x-control-*` y debe
tratarse como una conveniencia insegura: no es válido para validación gobernada,
candidatos RC ni producción.

El helper principal es `resolveAuthenticatedControlActor()` y mapea:

- `session.user.email`
- `session.user.name`
- `session.user.image`
- `provider`
- `providerAccountId`

hacia un actor operacional con:

- `actor_id`
- `user_id`
- `username`
- `display_name`
- `email`
- `role`
- `auth_source`

## Roles

La asignación inicial de rol se resuelve por email:

- `CONTROL_AUTH_ADMIN_EMAILS`
- `CONTROL_AUTH_OPERATOR_EMAILS`
- `CONTROL_AUTH_VIEWER_EMAILS`

Precedencia:

1. `admin`
2. `operator`
3. `viewer`

Si un usuario está autenticado pero no aparece en ninguna lista, queda como
`viewer`.

## Scope

Las sesiones OAuth se resuelven mediante memberships persistidos por proyecto.
Siempre tienen `all_projects=false`: sin membership el scope queda vacío, y
una membership concede exclusivamente el proyecto y rol asociados. El fallback
local/dev, cuando fue habilitado de forma explícita, conserva el scope indicado
por `x-control-project-ids` / `control_project_ids`.

## Matriz de configuración

| Entorno | `CONTROL_RBAC_ALLOW_DEV_FALLBACK` | Uso permitido |
| --- | --- | --- |
| Development convenience inseguro | `true` explícito | Debug local controlado; nunca RC/release. |
| Development gobernado / validación RC | `false` | OAuth + memberships persistidos. |
| Producción | `false` obligatorio | OAuth + memberships persistidos. |

## Protección de endpoints

Se protege la superficie:

- `/api/control/access`
- `/api/control/status`
- `/api/control/recommendations`
- `/api/control/audit`
- `/api/control/policies`
- `/api/control/policies/[id]`
- `/api/control/policies/preview`

Comportamiento:

- sin sesión y sin fallback dev: `401`
- autenticado con rol insuficiente: `403`

## Token interno para route handlers

No se expone ningún secreto al cliente.

Los route handlers verifican la sesión JWT firmada por NextAuth usando
`getServerSession(authOptions)`. Ese JWT de sesión actúa como token interno del
backend para `apps/topology-next`.

## Restricciones mantenidas

Esta fase no modifica:

- `control_engine_worker`
- evaluators
- ingestor
- `core_backend`
- `admin-fastapi`
- lógica de control
