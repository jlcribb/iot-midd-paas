#!/bin/bash

# Script Principal de Gestión - IoT Middleware
# Autor: Sistema de Desarrollo
# Fecha: $(date '+%Y-%m-%d %H:%M:%S')

# Colores para la salida
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Función para imprimir con timestamp
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Función para imprimir header
print_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  GESTOR IOT MIDDLEWARE${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

# Función para mostrar menú principal
show_menu() {
    print_header
    echo -e "${YELLOW}Selecciona una opción:${NC}"
    echo ""
    echo -e "${GREEN}1.${NC} 📊 Monitorear estado de contenedores"
    echo -e "${GREEN}2.${NC} 📋 Generar reporte de estado"
    echo -e "${GREEN}3.${NC} 📖 Generar documentación del desarrollo"
    echo -e "${GREEN}4.${NC} 🚀 Levantar servicios"
    echo -e "${GREEN}5.${NC} 🛑 Detener servicios"
    echo -e "${GREEN}6.${NC} 🔄 Reiniciar servicios"
    echo -e "${GREEN}7.${NC} 📝 Ver logs de un contenedor"
    echo -e "${GREEN}8.${NC} 🌐 Verificar conectividad"
    echo -e "${GREEN}9.${NC} 📊 Estado del sistema"
    echo -e "${GREEN}0.${NC} ❌ Salir"
    echo ""
}

# Función para monitorear contenedores
monitor_containers() {
    log "Ejecutando monitoreo de contenedores..."
    echo ""
    ../scripts/monitor_containers.sh
}

# Función para generar reporte
generate_report() {
    log "Generando reporte de estado..."
    echo ""
    ../scripts/monitor_containers.sh -r
}

# Función para generar documentación
generate_documentation() {
    log "Generando documentación del desarrollo..."
    echo ""
    ../scripts/document_development.sh
}

# Función para levantar servicios
start_services() {
    log "Levantando servicios..."
    echo ""
    if podman-compose up -d; then
        echo -e "${GREEN}✅ Servicios levantados correctamente${NC}"
        echo ""
        echo "Esperando 10 segundos para que los servicios se inicialicen..."
        sleep 10
        echo ""
        echo "Estado actual de los contenedores:"
        podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        echo -e "${RED}❌ Error al levantar los servicios${NC}"
    fi
}

# Función para detener servicios
stop_services() {
    log "Deteniendo servicios..."
    echo ""
    if podman-compose down; then
        echo -e "${GREEN}✅ Servicios detenidos correctamente${NC}"
    else
        echo -e "${RED}❌ Error al detener los servicios${NC}"
    fi
}

# Función para reiniciar servicios
restart_services() {
    log "Reiniciando servicios..."
    echo ""
    stop_services
    echo ""
    start_services
}

# Función para ver logs de un contenedor
view_logs() {
    echo ""
    echo -e "${YELLOW}Contenedores disponibles:${NC}"
    podman ps --format "{{.Names}}" | nl
    echo ""
    read -p "Selecciona el número del contenedor: " container_num
    
    local containers=($(podman ps --format "{{.Names}}"))
    if [ $container_num -ge 1 ] && [ $container_num -le ${#containers[@]} ]; then
        local container=${containers[$((container_num-1))]}
        echo ""
        echo -e "${YELLOW}Mostrando logs de: $container${NC}"
        echo ""
        podman logs -f "$container"
    else
        echo -e "${RED}❌ Número de contenedor inválido${NC}"
    fi
}

# Función para verificar conectividad
check_connectivity() {
    log "Verificando conectividad de servicios..."
    echo ""
    
    echo -e "${YELLOW}Verificando puertos:${NC}"
    for port in 1883 5432 8086 8000; do
        local service=""
        case $port in
            1883) service="MQTT (Mosquitto)" ;;
            5432) service="PostgreSQL" ;;
            8086) service="InfluxDB" ;;
            8000) service="API (FastAPI)" ;;
        esac
        
        if nc -z localhost $port 2>/dev/null; then
            echo -e "   ✅ Puerto $port ($service): ${GREEN}ABIERTO${NC}"
        else
            echo -e "   ❌ Puerto $port ($service): ${RED}CERRADO${NC}"
        fi
    done
    
    echo ""
    echo -e "${YELLOW}Verificando health checks:${NC}"
    
    # InfluxDB
    local influx_health=$(curl -s http://localhost:8086/health 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$influx_health" ]; then
        local status=$(echo "$influx_health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        echo -e "   ✅ InfluxDB: ${GREEN}$status${NC}"
    else
        echo -e "   ❌ InfluxDB: ${RED}No responde${NC}"
    fi
    
    # API
    local api_health=$(curl -s http://localhost:8000/health 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$api_health" ]; then
        local status=$(echo "$api_health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        echo -e "   ✅ API: ${GREEN}$status${NC}"
    else
        echo -e "   ❌ API: ${RED}No responde${NC}"
    fi
}

# Función para mostrar estado del sistema
show_system_status() {
    log "Mostrando estado del sistema..."
    echo ""
    
    echo -e "${YELLOW}Información del Sistema:${NC}"
    echo "   OS: $(uname -s) $(uname -r)"
    echo "   Arquitectura: $(uname -m)"
    echo "   Usuario: $(whoami)"
    echo "   Host: $(hostname)"
    echo ""
    
    echo -e "${YELLOW}Uso de Recursos:${NC}"
    echo "   Espacio en disco:"
    df -h . | head -2
    echo ""
    
    echo -e "${YELLOW}Red:${NC}"
    echo "   IP local: $(hostname -I 2>/dev/null || echo 'No disponible')"
    echo ""
    
    echo -e "${YELLOW}Podman:${NC}"
    echo "   Versión: $(podman --version)"
    echo "   Contenedores ejecutándose: $(podman ps -q | wc -l)"
    echo "   Imágenes disponibles: $(podman images -q | wc -l)"
}

# Función para procesar opción del menú
process_option() {
    local option=$1
    
    case $option in
        1)
            monitor_containers
            ;;
        2)
            generate_report
            ;;
        3)
            generate_documentation
            ;;
        4)
            start_services
            ;;
        5)
            stop_services
            ;;
        6)
            restart_services
            ;;
        7)
            view_logs
            ;;
        8)
            check_connectivity
            ;;
        9)
            show_system_status
            ;;
        0)
            echo ""
            echo -e "${GREEN}👋 ¡Hasta luego!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Opción inválida. Por favor selecciona una opción válida.${NC}"
            ;;
    esac
}

# Función principal
main() {
    # Verificar si estamos en el directorio correcto
    if [ ! -f "podman-compose.yaml" ]; then
        echo -e "${RED}❌ Error: Este script debe ejecutarse desde el directorio 'containers'${NC}"
        echo "Por favor, navega al directorio 'containers' y ejecuta el script desde ahí."
        exit 1
    fi
    
    # Verificar si podman-compose está disponible
    if ! command -v podman-compose &> /dev/null; then
        echo -e "${RED}❌ Error: podman-compose no está instalado${NC}"
        echo "Por favor, instala podman-compose primero:"
        echo "pip3 install podman-compose"
        exit 1
    fi
    
    # Bucle principal del menú
    while true; do
        show_menu
        read -p "Opción: " choice
        
        if [[ $choice =~ ^[0-9]+$ ]]; then
            process_option $choice
        else
            echo -e "${RED}❌ Por favor ingresa un número válido.${NC}"
        fi
        
        echo ""
        read -p "Presiona Enter para continuar..."
        echo ""
    done
}

# Ejecutar función principal
main "$@"
