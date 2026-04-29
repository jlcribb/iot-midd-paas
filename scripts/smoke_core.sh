#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ ! -x "./venv/bin/python" || ! -x "./venv/bin/pytest" ]]; then
  echo "ERROR: no se encontro entorno virtual en ./venv (python/pytest)."
  echo "Sugerencia: ejecutar ./setup_venv.sh"
  exit 1
fi

echo "[1/3] Validacion rapida de sintaxis"
PYTHONPYCACHEPREFIX=/tmp/pycache ./venv/bin/python -m py_compile \
  src/iot_middleware/config/config_loader.py \
  src/iot_middleware/models/base.py \
  src/iot_middleware/storage/db_handler.py \
  src/iot_middleware/api/api.py \
  src/iot_middleware/api/routers/auth_router.py \
  src/iot_middleware/api/routers/data_router.py \
  src/iot_middleware/api/routers/events_router.py \
  src/iot_middleware/api/routers/projects_router.py

echo "[2/3] Contratos estaticos minimos (imports no usados / nombres no definidos)"
./venv/bin/flake8 --select=F401,F821 \
  src/iot_middleware/config/config_loader.py \
  src/iot_middleware/models/base.py \
  src/iot_middleware/storage/db_handler.py \
  src/iot_middleware/api/api.py \
  src/iot_middleware/api/models/common_models.py \
  src/iot_middleware/api/models/auth_models.py \
  src/iot_middleware/api/models/data_models.py

echo "[3/3] Suite core de saneamiento"
./venv/bin/pytest -q \
  tests/unit/test_storage/test_schema_bootstrap_mode.py \
  tests/unit/test_storage/test_db_handler_factory.py \
  tests/unit/test_auth/test_auth_scope_contract.py \
  tests/unit/test_auth/test_scope_and_permissions.py \
  tests/unit/test_api/test_router_contract_helpers.py

echo "OK: smoke core completado"
