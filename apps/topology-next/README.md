# topology-next

Backend/UI oficial del dominio operacional de Midd IOT.

Responsabilidades:

- projects
- sectors
- locations
- assets
- topology
- provisioning
- topology views
- canvas/UI

## Estado

Clasificacion actual: `official`

## Nota de compatibilidad

La ubicacion canonica del codigo es:

- `apps/topology-next/`

Se mantiene temporalmente:

- `next-backend -> apps/topology-next`

para no romper comandos, tooling y validaciones existentes durante la transicion.

## Autenticacion OAuth local

- copiar `apps/topology-next/.env.local.example` a `apps/topology-next/.env.local`
- completar `NEXTAUTH_URL=http://127.0.0.1:3000`
- generar `NEXTAUTH_SECRET`
- completar las credenciales de GitHub y Google
- reiniciar el servidor local
- no commitear `apps/topology-next/.env.local`
- referencia operativa: `docs/auth/OAUTH_LOCAL_DEVELOPMENT_SETUP.md`
