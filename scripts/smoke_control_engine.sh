#!/usr/bin/env bash
set -euo pipefail

export REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$REPO_ROOT/src:$REPO_ROOT/apps/parametric-control-engine/src:${PYTHONPATH:-}"
export CONTROL_WORKER_PUBLISH_MODE="${CONTROL_WORKER_PUBLISH_MODE:-stdout}"
export CONTROL_WORKER_FORCE_ENABLED="${CONTROL_WORKER_FORCE_ENABLED:-true}"
export CONTROL_WORKER_ALLOW_INMEMORY_POLICY_FALLBACK="${CONTROL_WORKER_ALLOW_INMEMORY_POLICY_FALLBACK:-true}"
export DB_HOST="${DB_HOST:-localhost}"
export DB_PORT="${DB_PORT:-5432}"
export DB_NAME="${DB_NAME:-iot_middleware}"
export DB_USER="${DB_USER:-iot_user}"
export DB_PASSWORD="${DB_PASSWORD:-iot_password_2024}"

PYTHON_BIN="${PYTHON_BIN:-$REPO_ROOT/venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

echo "[SMOKE] Running control engine worker direct smoke test"
"$PYTHON_BIN" "$REPO_ROOT/scripts/publish_test_control_event.py"
