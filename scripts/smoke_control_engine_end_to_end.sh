#!/usr/bin/env bash
set -euo pipefail

# This smoke deliberately reconfigures only the two affected consumers with
# per-run output routes. MQTT input remains the canonical telemetry.events
# channel, while recommendations and integration audit never reach legacy
# control.recommendations/control.audit queues.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/infra/containers/docker-compose.yaml"
RUN_SUFFIX="$(date +%s)-$$"
# Python dependencies are preprovisioned in the Compose images. Readiness must
# still mean that the service process has started with its Python runtime, not
# merely that Docker reports a running container.
STARTUP_TIMEOUT_SECONDS="${CONTROL_SMOKE_STARTUP_TIMEOUT_SECONDS:-300}"

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

python_runtime_importable() {
  local service_name="$1"
  local module_name="$2"

  docker exec "$service_name" sh -lc "PYTHONPATH=/app/src:/app/apps/parametric-control-engine/src python -c 'import paho.mqtt.client; import ${module_name}'" >/dev/null 2>&1
}

service_runtime_ready() {
  local service_name="$1"
  local module_name="$2"
  local startup_marker="$3"
  local service_state

  service_state="$(docker inspect --format '{{.State.Status}}' "$service_name" 2>/dev/null || true)"
  case "$service_state" in
    running)
      ;;
    exited|dead|removing)
      echo "[SMOKE] SERVICE_EXITED service=${service_name} state=${service_state}" >&2
      docker logs --tail 80 "$service_name" >&2 || true
      return 1
      ;;
    *)
      return 2
      ;;
  esac

  if ! python_runtime_importable "$service_name" "$module_name"; then
    return 2
  fi
  if ! docker logs --tail 100 "$service_name" 2>&1 | grep -Fq "$startup_marker"; then
    return 2
  fi
  return 0
}

wait_for_service_runtime() {
  local service_name="$1"
  local module_name="$2"
  local startup_marker="$3"
  local probe_status

  while (( $(date +%s) < STARTUP_DEADLINE_EPOCH )); do
    if service_runtime_ready "$service_name" "$module_name" "$startup_marker"; then
      echo "[SMOKE] RUNTIME_READY service=${service_name}" >&2
      return 0
    else
      probe_status=$?
    fi
    if [[ "$probe_status" -eq 1 ]]; then
      return 1
    fi
    sleep 1
  done

  if docker logs --tail 120 "$service_name" 2>&1 | grep -Fq 'Successfully installed'; then
    if python_runtime_importable "$service_name" "$module_name"; then
      echo "[SMOKE] SERVICE_STARTUP_FAILURE_AFTER_PROVISIONING service=${service_name}" >&2
    else
      echo "[SMOKE] RUNTIME_IMPORT_FAILURE_AFTER_PROVISIONING service=${service_name}" >&2
    fi
  else
    echo "[SMOKE] PROVISIONING_TIMEOUT service=${service_name} timeout_seconds=${STARTUP_TIMEOUT_SECONDS}" >&2
  fi
  docker logs --tail 120 "$service_name" >&2 || true
  return 1
}

export CONTROL_WORKER_RECOMMENDATION_QUEUE="$SMOKE_RECOMMENDATION_QUEUE"
export CONTROL_WORKER_AUDIT_QUEUE="$SMOKE_AUDIT_QUEUE"
export SIMULATED_ACTUATION_RECOMMENDATION_QUEUE="$SMOKE_SIMULATED_QUEUE"
export SIMULATED_ACTUATION_RECOMMENDATION_ROUTING_KEY="$SMOKE_SIMULATED_QUEUE"

echo "[SMOKE] Recreating isolated worker routes"
docker compose -f "$COMPOSE_FILE" up -d --force-recreate control-engine-worker simulated-actuation-consumer >/dev/null

STARTUP_DEADLINE_EPOCH=$(($(date +%s) + STARTUP_TIMEOUT_SECONDS))
wait_for_service_runtime \
  control-engine-worker \
  iot_middleware.services.control_engine_worker \
  'Control Engine Worker started'
wait_for_service_runtime \
  simulated-actuation-consumer \
  iot_middleware.services.simulated_actuation_consumer \
  'Simulated Actuation Consumer started'

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
