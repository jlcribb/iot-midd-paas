# infra/migrations

Ubicacion canonica de Alembic y migraciones del sistema.

Contenido actual:

- `infra/migrations/alembic/`
- `infra/migrations/alembic.ini`

Compatibilidad temporal:

- `alembic -> infra/migrations/alembic`
- `alembic.ini -> infra/migrations/alembic.ini`

Comando canonico:

```bash
alembic -c infra/migrations/alembic.ini upgrade head
```

Comando legacy aun soportado:

```bash
alembic upgrade head
```
