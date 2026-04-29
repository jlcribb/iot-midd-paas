#!/usr/bin/env bash
#
# Wrapper legacy de compatibilidad.
# La ruta operativa oficial es scripts/docker-stack.sh
#
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
exec "$SCRIPT_DIR/docker-stack.sh" "$@"
