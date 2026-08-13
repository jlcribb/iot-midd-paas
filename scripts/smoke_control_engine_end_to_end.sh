#!/usr/bin/env bash
set -euo pipefail

# This smoke deliberately reconfigures only the two affected consumers with
# per-run output routes. MQTT input remains the canonical telemetry.events
# channel, while recommendations and integration audit never reach legacy
# control.recommendations/control.audit queues.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/infra/containers/docker-compose.yaml"
RUN_SUFFIX="$(date +%s)-$$"
STARTUP_TIMEOUT_SECONDS="${CONTROL_SMOKE_STARTUP_TIMEOUT_SECONDS:-180}"

SMOKE_RECOMMENDATION_QUEUE="control.recommendations.smoke.${RUN_SUFFIX}"
SMOKE_AUDIT_QUEUE="control.audit.smoke.${RUN_SUFFIX}"
SMOKE_SIMULATED_QUEUE="control.recommendations.simulated.smoke.${RUN_SUFFIX}"

restore_runtime() {
  local exit_code=$?
  set +e
  echo "[SMOKE] Restoring canonical worker routes"
  env \
    -u CONTROL_WORKER_RECOMMENDATION_QUEUE \
    -u CONTROL_WORKER_AUDIT_QUEUE \
    -u SIMULATED_ACTUATION_RECOMMENDATION_QUEUE \
    -u SIMULATED_ACTUATION_RECOMMENDATION_ROUTING_KEY \
    docker compose -f "$COMPOSE_FILE" up -d --force-recreate control-engine-worker simulated-actuation-consumer >/dev/null

  for queue in "$SMOKE_RECOMMENDATION_QUEUE" "$SMOKE_AUDIT_QUEUE" "$SMOKE_SIMULATED_QUEUE"; do
    docker exec rabbitmq rabbitmqctl delete_queue "$queue" >/dev/null 2>&1 || true
  done
  exit "$exit_code"
}
trap restore_runtime EXIT

export CONTROL_WORKER_RECOMMENDATION_QUEUE="$SMOKE_RECOMMENDATION_QUEUE"
export CONTROL_WORKER_AUDIT_QUEUE="$SMOKE_AUDIT_QUEUE"
export SIMULATED_ACTUATION_RECOMMENDATION_QUEUE="$SMOKE_SIMULATED_QUEUE"
export SIMULATED_ACTUATION_RECOMMENDATION_ROUTING_KEY="$SMOKE_SIMULATED_QUEUE"

echo "[SMOKE] Recreating isolated worker routes"
docker compose -f "$COMPOSE_FILE" up -d --force-recreate control-engine-worker simulated-actuation-consumer >/dev/null

for _ in $(seq 1 "$STARTUP_TIMEOUT_SECONDS"); do
  if docker exec control-engine-worker sh -lc 'PYTHONPATH=/app/src:/app/apps/parametric-control-engine/src python -c "import iot_middleware.services.control_engine_worker"' >/dev/null 2>&1 \
    && docker exec simulated-actuation-consumer sh -lc 'PYTHONPATH=/app/src:/app/apps/parametric-control-engine/src python -c "import iot_middleware.services.simulated_actuation_consumer"' >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
docker exec control-engine-worker sh -lc 'PYTHONPATH=/app/src:/app/apps/parametric-control-engine/src python -c "import iot_middleware.services.control_engine_worker"' >/dev/null
docker exec simulated-actuation-consumer sh -lc 'PYTHONPATH=/app/src:/app/apps/parametric-control-engine/src python -c "import iot_middleware.services.simulated_actuation_consumer"' >/dev/null

echo "[SMOKE] Running canonical MQTT -> simulated delivery smoke"
docker exec \
  -e PYTHONPATH=/app/src:/app/apps/parametric-control-engine/src \
  -e RABBITMQ_HOST=rabbitmq \
  -e MQTT_HOST=mosquitto \
  -e CONTROL_SMOKE_RECOMMENDATION_QUEUE="$SMOKE_RECOMMENDATION_QUEUE" \
  -e CONTROL_SMOKE_AUDIT_QUEUE="$SMOKE_AUDIT_QUEUE" \
  -e CONTROL_SMOKE_SIMULATED_QUEUE="$SMOKE_SIMULATED_QUEUE" \
  control-engine-worker \
  python /app/scripts/smoke_control_engine_end_to_end.py
