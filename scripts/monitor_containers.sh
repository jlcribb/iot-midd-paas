#!/bin/bash

# Script de Monitoreo para IoT Middleware
# Autor: Sistema de Desarrollo
# Fecha: $(date '+%Y-%m-%d %H:%M:%S')

# Colores para la salida
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Función para imprimir header
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  MONITOREO IOT MIDDLEWARE${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Función para verificar puerto
check_port() {
    local port=$1
    local service=$2
    if nc -z localhost $port 2>/dev/null; then
        echo -e "   ✅ Puerto $port: ${GREEN}ABIERTO${NC}"
        return 0
    else
        echo -e "   ❌ Puerto $port: ${RED}CERRADO${NC}"
        return 1
    fi
}

# Función para verificar health check
check_health() {
    local url=$1
    local service=$2
    local response=$(curl -s $url 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        echo -e "   ✅ Health Check: ${GREEN}OK${NC}"
        return 0
    else
        echo -e "   ❌ Health Check: ${RED}FALLO${NC}"
        return 1
    fi
}

# Función para obtener estado del contenedor
get_container_status() {
    local container=$1
    local status=$(podman inspect $container --format '{{.State.Status}}' 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo $status
    else
        echo "error"
    fi
}

# Función para obtener uptime del contenedor
get_container_uptime() {
    local container=$1
    local uptime=$(podman inspect $container --format '{{.State.StartedAt}}' 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo $uptime
    else
        echo "error"
    fi
}

# Función para verificar logs recientes
check_recent_logs() {
    local container=$1
    local lines=${2:-5}
    echo -e "   📋 Últimos $lines logs:"
    podman logs --tail $lines $container 2>/dev/null | while IFS= read -r line; do
        echo -e "      $line"
    done
}

# Función principal de monitoreo
monitor_containers() {
    print_header
    
    log "Iniciando monitoreo de contenedores..."
    echo ""
    
    # 1. MOSQUITTO
    echo -e "${YELLOW}1. MOSQUITTO (MQTT Broker)${NC}"
    echo -e "   📍 Contenedor: mosquitto"
    echo -e "   🏃 Estado: $(get_container_status mosquitto)"
    echo -e "   ⏰ Iniciado: $(get_container_uptime mosquitto)"
    check_port 1883 "MQTT"
    echo ""
    
    # 2. INFLUXDB
    echo -e "${YELLOW}2. INFLUXDB (Base de Datos)${NC}"
    echo -e "   📍 Contenedor: influxdb"
    echo -e "   🏃 Estado: $(get_container_status influxdb)"
    echo -e "   ⏰ Iniciado: $(get_container_uptime influxdb)"
    check_port 8086 "InfluxDB"
    check_health "http://localhost:8086/health" "InfluxDB"
    echo ""
    
    # 3. API
    echo -e "${YELLOW}3. API (FastAPI)${NC}"
    echo -e "   📍 Contenedor: iotmw-api"
    echo -e "   🏃 Estado: $(get_container_status iotmw-api)"
    echo -e "   ⏰ Iniciado: $(get_container_uptime iotmw-api)"
    check_port 8000 "API"
    check_health "http://localhost:8000/health" "API"
    echo ""
    
    # 4. INGESTOR
    echo -e "${YELLOW}4. INGESTOR${NC}"
    echo -e "   📍 Contenedor: iotmw-ingestor"
    echo -e "   🏃 Estado: $(get_container_status iotmw-ingestor)"
    echo -e "   ⏰ Iniciado: $(get_container_uptime iotmw-ingestor)"
    echo ""
    
    # 5. VERIFICACIÓN DE RED
    echo -e "${YELLOW}5. VERIFICACIÓN DE RED${NC}"
    echo -e "   🌐 Verificando conectividad entre servicios..."
    
    # Verificar que todos los contenedores estén en la misma red
    local network=$(podman inspect mosquitto --format '{{range $net, $config := .NetworkSettings.Networks}}{{$net}}{{end}}' 2>/dev/null)
    if [ -n "$network" ]; then
        echo -e "   ✅ Red compartida: $network"
    else
        echo -e "   ⚠️  No se pudo determinar la red"
    fi
    echo ""
    
    # 6. RESUMEN DE ESTADO
    echo -e "${YELLOW}6. RESUMEN DE ESTADO${NC}"
    local total_containers=4
    local running_containers=0
    
    for container in mosquitto influxdb iotmw-api iotmw-ingestor; do
        if [ "$(get_container_status $container)" = "running" ]; then
            ((running_containers++))
        fi
    done
    
    if [ $running_containers -eq $total_containers ]; then
        echo -e "   🎉 ${GREEN}TODOS LOS SERVICIOS ESTÁN FUNCIONANDO${NC}"
        echo -e "   📊 Contenedores ejecutándose: $running_containers/$total_containers"
    else
        echo -e "   ⚠️  ${YELLOW}ALGUNOS SERVICIOS NO ESTÁN FUNCIONANDO${NC}"
        echo -e "   📊 Contenedores ejecutándose: $running_containers/$total_containers"
    fi
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    log "Monitoreo completado"
}

# Función para generar reporte en archivo
generate_report() {
    local report_file="iot_middleware_status_$(date '+%Y%m%d_%H%M%S').txt"
    
    log "Generando reporte en: $report_file"
    
    # Ejecutar monitoreo y guardar en archivo
    {
        echo "REPORTE DE ESTADO - IOT MIDDLEWARE"
        echo "=================================="
        echo "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Usuario: $(whoami)"
        echo "Host: $(hostname)"
        echo ""
        
        # Ejecutar monitoreo sin colores para el archivo
        podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        
        echo "VERIFICACIÓN DE PUERTOS:"
        echo "------------------------"
        for port in 1883 8086 8000; do
            if nc -z localhost $port 2>/dev/null; then
                echo "Puerto $port: ABIERTO"
            else
                echo "Puerto $port: CERRADO"
            fi
        done
        echo ""
        
        echo "HEALTH CHECKS:"
        echo "---------------"
        echo "InfluxDB: $(curl -s http://localhost:8086/health 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo 'NO RESPONDE')"
        echo "API: $(curl -s http://localhost:8000/health 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo 'NO RESPONDE')"
        echo ""
        
        echo "LOGS RECIENTES:"
        echo "----------------"
        for container in mosquitto influxdb iotmw-api iotmw-ingestor; do
            echo "=== $container ==="
            podman logs --tail 3 $container 2>/dev/null
            echo ""
        done
        
    } > "$report_file"
    
    echo -e "${GREEN}✅ Reporte generado: $report_file${NC}"
    echo -e "${BLUE}📁 Ubicación: $(pwd)/$report_file${NC}"
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  -m, --monitor    Monitorear contenedores (por defecto)"
    echo "  -r, --report     Generar reporte en archivo"
    echo "  -h, --help       Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0               # Monitoreo en pantalla"
    echo "  $0 -r            # Generar reporte en archivo"
    echo "  $0 --monitor     # Monitoreo explícito"
}

# Función principal
main() {
    case "${1:-monitor}" in
        -m|--monitor|monitor)
            monitor_containers
            ;;
        -r|--report)
            generate_report
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"
