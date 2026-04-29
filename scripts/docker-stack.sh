#!/usr/bin/env bash
#
# Pipeline IoT Middleware — gestión del stack con Docker Compose.
# Uso: desde cualquier directorio, o desde la raíz del repo:
#   ./scripts/docker-stack.sh <comando>
#
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
COMPOSE_FILE="$REPO_ROOT/infra/containers/docker-compose.yaml"
COMPOSE=(docker compose -f "$COMPOSE_FILE")

INFRA_ORDER=(mosquitto influxdb postgresql rabbitmq)
APP_ORDER=(iotmw-api iotmw-ingestor iotmw-dashboard iotmw-admin)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

die() {
  echo -e "${RED}[ERROR]${NC} $*" >&2
  exit 1
}

info() { echo -e "${GREEN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

require_compose_file() {
  [[ -f "$COMPOSE_FILE" ]] || die "No existe $COMPOSE_FILE (¿estás en el clon correcto del repo?)"
}

container_exists() {
  docker container inspect "$1" >/dev/null 2>&1
}

cmd_status() {
  require_compose_file
  echo "=== Contenedores del stack IoT Middleware (Docker) ==="
  printf "%-18s %-12s %-10s %s\n" "NOMBRE" "ESTADO" "SALUD" "PUERTOS"
  echo "----------------------------------------------------------------------------"
  local names=("${INFRA_ORDER[@]}" "${APP_ORDER[@]}")
  local name state health ports
  for name in "${names[@]}"; do
    if ! container_exists "$name"; then
      printf "%-18s %-12s %-10s %s\n" "$name" "no existe" "-" "-"
      continue
    fi
    state=$(docker inspect "$name" --format '{{.State.Status}}' 2>/dev/null || echo "?")
    health=$(docker inspect "$name" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}—{{end}}' 2>/dev/null || echo "—")
    ports=$(docker port "$name" 2>/dev/null | tr '\n' ' ' | sed 's/[[:space:]]*$//')
    [[ -z "$ports" ]] && ports="—"
    printf "%-18s %-12s %-10s %s\n" "$name" "$state" "$health" "$ports"
  done
}

cmd_healthcheck() {
  require_compose_file
  info "Verificando health status de Docker donde esté definido…"
  for name in postgresql; do
    if container_exists "$name"; then
      if docker inspect "$name" --format '{{.Config.Healthcheck}}' 2>/dev/null | grep -q .; then
        local health
        health=$(docker inspect "$name" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null || echo "unknown")
        if [[ "$health" == "healthy" ]]; then
          info "  $name: healthy"
        else
          warn "  $name: health status = $health"
        fi
      fi
    fi
  done
}

cmd_probe() {
  local ok=0 fail=0
  echo "=== Sondas HTTP (constatación rápida) ==="
  probe_url() {
    local url=$1 desc=$2
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$url" || echo "000")
    if [[ "$code" =~ ^2 ]]; then
      echo -e "  ${GREEN}OK${NC}  [$code] $desc → $url"
      ((ok++)) || true
    else
      echo -e "  ${RED}FALLO${NC} [$code] $desc → $url"
      ((fail++)) || true
    fi
  }
  probe_url "http://127.0.0.1:8000/docs" "API (OpenAPI)"
  probe_url "http://127.0.0.1:9000/" "Panel administración"
  probe_url "http://127.0.0.1:8080/health" "Dashboard /health"
  echo "---"
  if [[ $fail -gt 0 ]]; then
    warn "Sondas fallidas: $fail (revisa logs: $0 logs <nombre>)"
    return 1
  fi
  info "Todas las sondas respondieron 2xx ($ok)."
}

cmd_check() {
  cmd_status
  echo ""
  cmd_healthcheck || true
  echo ""
  cmd_probe || true
}

cmd_up() {
  require_compose_file
  cd "$REPO_ROOT"
  info "Levantando stack (docker compose up -d)…"
  "${COMPOSE[@]}" up -d
  info "Esperando a PostgreSQL (hasta ~30s)…"
  local i=0
  while ! docker exec postgresql pg_isready -U iot_user -d iot_middleware &>/dev/null; do
    sleep 1
    i=$((i + 1))
    [[ $i -lt 35 ]] || { warn "PostgreSQL no respondió a tiempo; revisa: docker logs postgresql"; break; }
  done
  cmd_check || true
}

cmd_down() {
  require_compose_file
  cd "$REPO_ROOT"
  info "Parando stack (docker compose stop; contenedores conservados)…"
  "${COMPOSE[@]}" stop
  info "Stack parado."
}

cmd_down_remove() {
  require_compose_file
  cd "$REPO_ROOT"
  warn "Eliminando contenedores del compose (los volúmenes nombrados se conservan salvo -v en down completo)."
  "${COMPOSE[@]}" down
  info "Contenedores eliminados. Volúmenes: docker volume ls"
}

cmd_recreate() {
  require_compose_file
  cd "$REPO_ROOT"
  info "Recreando contenedores (imágenes y volúmenes persistentes se reutilizan)…"
  "${COMPOSE[@]}" up -d --force-recreate
  cmd_check || true
}

cmd_restart() {
  cmd_down
  cmd_up
}

cmd_logs() {
  local svc=${1:-}
  [[ -n "$svc" ]] || die "Uso: $0 logs <nombre_contenedor>  (ej. iotmw-api)"
  docker logs -f --tail 100 "$svc"
}

cmd_start_manual() {
  info "Arranque manual en orden…"
  for c in "${INFRA_ORDER[@]}"; do
    docker start "$c" 2>/dev/null && info "  iniciado: $c" || warn "  $c: no iniciado (¿existe?)"
  done
  sleep 4
  for c in "${APP_ORDER[@]}"; do
    docker start "$c" 2>/dev/null && info "  iniciado: $c" || warn "  $c: no iniciado (¿existe?)"
  done
  cmd_check || true
}

cmd_help() {
  cat <<EOF
IoT Middleware — pipeline Docker

  $0 status       Estado de los 8 contenedores (running/exited, salud, puertos)
  $0 healthcheck  Verifica health status de Docker donde esté definido
  $0 probe        Comprueba API (8000), Admin (9000), Dashboard /health (8080)
  $0 check        status + healthcheck + probe (pipeline de constatación)

  $0 up           Levantar todo (docker compose up -d) + espera Postgres + check
  $0 down         Parar todo (compose stop)
  $0 down-remove  Parar y eliminar contenedores (compose down; conserva volúmenes por defecto)
  $0 recreate     Recrear contenedores (--force-recreate) + check
  $0 restart      down + up

  $0 start-manual Arrancar por nombre (infra → apps) si compose no puede recrear
  $0 logs <nombre>  Tailer de logs (ej. postgresql, iotmw-api)

Compose file: $COMPOSE_FILE
Ejecutar siempre desde el clon del repositorio (el script localiza la raíz solo).
EOF
}

main() {
  command -v docker >/dev/null 2>&1 || die "Docker no está en PATH."
  docker compose version >/dev/null 2>&1 || die "docker compose no está disponible."
  local cmd=${1:-help}
  shift || true
  case "$cmd" in
    status) cmd_status ;;
    healthcheck) cmd_healthcheck ;;
    probe) cmd_probe ;;
    check) cmd_check ;;
    up) cmd_up ;;
    down) cmd_down ;;
    down-remove) cmd_down_remove ;;
    recreate) cmd_recreate ;;
    restart) cmd_restart ;;
    start-manual) cmd_start_manual ;;
    logs) cmd_logs "$@" ;;
    help|-h|--help) cmd_help ;;
    *) die "Comando desconocido: $cmd. Usa: $0 help" ;;
  esac
}

main "$@"
