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
2. fallback local/dev si `CONTROL_RBAC_ALLOW_DEV_FALLBACK=true` y no estamos en producción.

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

En esta fase el actor autenticado se considera `all_projects=true`, porque
todavía no existe una tabla local de memberships por proyecto dentro de
`topology-next`.

El scope granular por proyecto queda pendiente para una fase posterior.
El fallback local/dev conserva el scope por `x-control-project-ids` /
`control_project_ids`.

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
