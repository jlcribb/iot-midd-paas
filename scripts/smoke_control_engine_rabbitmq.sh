#!/usr/bin/env bash
set -euo pipefail

export REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$REPO_ROOT/src:$REPO_ROOT/apps/parametric-control-engine/src:${PYTHONPATH:-}"

PYTHON_BIN="${PYTHON_BIN:-$REPO_ROOT/venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

echo "[SMOKE] Running control engine worker RabbitMQ smoke test"
"$PYTHON_BIN" "$REPO_ROOT/scripts/smoke_control_engine_rabbitmq.py"
