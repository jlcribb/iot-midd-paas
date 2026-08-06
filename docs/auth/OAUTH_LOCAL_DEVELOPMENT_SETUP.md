# OAuth Local Development Setup

## Objetivo

Configurar la autenticacion OAuth local de `apps/topology-next` sin exponer secretos y sin mezclar este flujo con la autenticacion de GitHub CLI.

## OAuth de la aplicacion vs GitHub CLI

- OAuth de la aplicacion:
  - login de usuarios finales en Midd IoT
  - usa `AUTH_GITHUB_*`, `AUTH_GOOGLE_*`, `NEXTAUTH_URL` y `NEXTAUTH_SECRET`
- GitHub CLI:
  - usa `gh auth login`
  - no reutiliza la OAuth App de Midd IoT
  - no usa las callbacks de NextAuth

## Archivos

- archivo local ignorado:
  - `apps/topology-next/.env.local`
- archivo de ejemplo trackeado:
  - `apps/topology-next/.env.local.example`

## Convencion de variables

Providers OAuth:

```env
AUTH_GITHUB_ID=
AUTH_GITHUB_SECRET=
AUTH_GOOGLE_ID=
AUTH_GOOGLE_SECRET=
```

NextAuth canónico:

```env
NEXTAUTH_URL=
NEXTAUTH_SECRET=
```

Compatibilidad heredada:

```env
AUTH_URL=
AUTH_SECRET=
```

Prioridad efectiva:

- `NEXTAUTH_URL ?? AUTH_URL`
- `NEXTAUTH_SECRET ?? AUTH_SECRET`

## `.env.local`

Base local recomendada:

```env
NEXTAUTH_URL=http://127.0.0.1:3000
NEXTAUTH_SECRET=REPLACE_WITH_A_RANDOM_LOCAL_SECRET

AUTH_GITHUB_ID=REPLACE_WITH_GITHUB_CLIENT_ID
AUTH_GITHUB_SECRET=REPLACE_WITH_GITHUB_CLIENT_SECRET

AUTH_GOOGLE_ID=REPLACE_WITH_GOOGLE_CLIENT_ID
AUTH_GOOGLE_SECRET=REPLACE_WITH_GOOGLE_CLIENT_SECRET
```

## GitHub OAuth App

Configurar:

- Homepage URL:
  - `http://127.0.0.1:3000/`
- Authorization callback URL:
  - `http://127.0.0.1:3000/api/auth/callback/github`

Variables:

- `AUTH_GITHUB_ID`
- `AUTH_GITHUB_SECRET`

## Google OAuth Web Client

Configurar:

- Authorized JavaScript origin:
  - `http://127.0.0.1:3000`
- Authorized redirect URI:
  - `http://127.0.0.1:3000/api/auth/callback/google`

Variables:

- `AUTH_GOOGLE_ID`
- `AUTH_GOOGLE_SECRET`

## NEXTAUTH_SECRET

Generar localmente:

```bash
openssl rand -base64 32
```

Usarlo solo en `apps/topology-next/.env.local`.

## Reinicio del servidor

Después de cambiar credenciales o secretos:

1. detener el servidor local;
2. volver a ejecutar `npm run dev -- --hostname 127.0.0.1 --port 3000`.

## Seguridad

- no guardar secretos en Git
- no compartir capturas con valores
- no copiar secretos a reportes
- rotar secretos si hubo exposición accidental
- mantener `.env.local` solo como archivo local ignorado
