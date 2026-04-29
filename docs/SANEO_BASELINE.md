# Baseline De Saneo (Core)

Este baseline fija una verificacion minima reproducible para el nucleo saneado.

## Comandos canonicos

Desde la raiz del repo:

```bash
./scripts/smoke_core.sh
```

Comando directo de suite core:

```bash
./venv/bin/pytest -q \
  tests/unit/test_storage/test_schema_bootstrap_mode.py \
  tests/unit/test_storage/test_db_handler_factory.py \
  tests/unit/test_auth/test_auth_scope_contract.py \
  tests/unit/test_auth/test_scope_and_permissions.py \
  tests/unit/test_api/test_router_contract_helpers.py
```

## Resultado esperado

- Validacion de sintaxis: OK.
- Flake8 selectivo (`F401,F821`) en modulos core saneados: OK.
- Suite core: `17 passed`.

## Ultima verificacion

- Fecha: 2026-03-25.
- Comando: `./scripts/smoke_core.sh`.
- Resultado: OK (`17 passed` en suite core).

## Warnings conocidos (no bloqueantes de codigo)

- `urllib3 NotOpenSSLWarning` por entorno local con LibreSSL en macOS.
- No afecta la logica del middleware; depende del runtime de Python/SSL del sistema.

## Objetivo cubierto del plan

- SAN-003 Baseline automatizado:
- comando unico de smoke;
- comando unico de suite core;
- registro de warnings conocidos.
