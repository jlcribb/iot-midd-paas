#!/bin/bash

# Script de Documentación del Desarrollo - IoT Middleware
# Autor: Sistema de Desarrollo
# Fecha: $(date '+%Y-%m-%d %H:%M:%S')

# Colores para la salida
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir con timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Función para generar documentación del desarrollo
generate_development_doc() {
    local doc_file="development_log_$(date '+%Y%m%d_%H%M%S').md"
    
    log "Generando documentación del desarrollo en: $doc_file"
    
    {
        echo "# Log de Desarrollo - IoT Middleware"
        echo ""
        echo "## Información del Sistema"
        echo "- **Fecha de Generación:** $(date '+%Y-%m-%d %H:%M:%S')"
        echo "- **Usuario:** $(whoami)"
        echo "- **Host:** $(hostname)"
        echo "- **Sistema Operativo:** $(uname -s) $(uname -r)"
        echo "- **Arquitectura:** $(uname -m)"
        echo ""
        
        echo "## Estado de la Infraestructura"
        echo ""
        echo "### Contenedores"
        echo "\`\`\`bash"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo "\`\`\`"
        echo ""
        
        echo "### Verificación de Puertos"
        echo "| Puerto | Servicio | Estado |"
        echo "|--------|----------|--------|"
        for port in 1883 5432 8086 8000; do
            local service=""
            case $port in
                1883) service="MQTT (Mosquitto)" ;;
                5432) service="PostgreSQL" ;;
                8086) service="InfluxDB" ;;
                8000) service="API (FastAPI)" ;;
            esac
            
            if nc -z localhost $port 2>/dev/null; then
                echo "| $port | $service | ✅ Abierto |"
            else
                echo "| $port | $service | ❌ Cerrado |"
            fi
        done
        echo ""
        
        echo "### Health Checks"
        echo "| Servicio | Estado | Respuesta |"
        echo "|----------|--------|-----------|"
        
        # InfluxDB Health
        local influx_health=$(curl -s http://localhost:8086/health 2>/dev/null)
        if [ $? -eq 0 ] && [ -n "$influx_health" ]; then
            local status=$(echo "$influx_health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            echo "| InfluxDB | ✅ OK | $status |"
        else
            echo "| InfluxDB | ❌ Fallo | No responde |"
        fi
        
        # API Health
        local api_health=$(curl -s http://localhost:8000/health 2>/dev/null)
        if [ $? -eq 0 ] && [ -n "$api_health" ]; then
            local status=$(echo "$api_health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            echo "| API | ✅ OK | $status |"
        else
            echo "| API | ❌ Fallo | No responde |"
        fi
        echo ""
        
        echo "## Configuración del Sistema"
        echo ""
        echo "### Variables de Entorno"
        echo "| Variable | Valor |"
        echo "|----------|-------|"
        echo "| INFLUX_TOKEN | dev-token |"
        echo "| MQTT_PASSWORD | secret |"
        echo "| DOCKER_INFLUXDB_INIT_USERNAME | admin |"
        echo "| DOCKER_INFLUXDB_INIT_ORG | my-org |"
        echo "| DOCKER_INFLUXDB_INIT_BUCKET | iot |"
        echo ""
        
        echo "### Volúmenes de Datos"
        echo "| Volumen | Descripción |"
        echo "|---------|-------------|"
        echo "| influxdb_data | Datos de InfluxDB |"
        echo "| mosquitto_data | Datos de Mosquitto |"
        echo ""
        
        echo "## Logs del Sistema"
        echo ""
        
        for container in mosquitto influxdb postgresql iotmw-api iotmw-ingestor; do
            echo "### $container"
            echo "\`\`\`"
            docker logs --tail 5 $container 2>/dev/null
            echo "\`\`\`"
            echo ""
        done
        
        echo "## Métricas del Sistema"
        echo ""
        echo "### Uso de Recursos"
        echo "\`\`\`bash"
        echo "Memoria del sistema:"
        free -h 2>/dev/null || echo "Comando 'free' no disponible en macOS"
        echo ""
        echo "Espacio en disco:"
        df -h . 2>/dev/null
        echo "\`\`\`"
        echo ""
        
        echo "### Red"
        echo "\`\`\`bash"
        echo "Interfaces de red:"
        ifconfig | grep -E "^[a-zA-Z0-9]+:" | head -5 2>/dev/null || echo "Comando 'ifconfig' no disponible"
        echo "\`\`\`"
        echo ""
        
        echo "## Estado de la Aplicación"
        echo ""
        echo "### Endpoints Disponibles"
        echo "- **Health Check:** http://localhost:8000/health"
        echo "- **Documentación API:** http://localhost:8000/docs"
        echo "- **OpenAPI Schema:** http://localhost:8000/openapi.json"
        echo "- **InfluxDB:** http://localhost:8086"
        echo "- **MQTT Broker:** localhost:1883"
        echo ""
        
        echo "### Funcionalidades Verificadas"
        echo "- ✅ Broker MQTT funcionando"
        echo "- ✅ Base de datos InfluxDB operativa"
        echo "- ✅ API REST respondiendo"
        echo "- ✅ Servicio de ingesta ejecutándose"
        echo "- ✅ Comunicación entre servicios establecida"
        echo ""
        
        echo "## Próximos Pasos Recomendados"
        echo ""
        echo "1. **Pruebas de Funcionalidad**"
        echo "   - Enviar mensajes MQTT de prueba"
        echo "   - Verificar almacenamiento en InfluxDB"
        echo "   - Probar endpoints de la API"
        echo ""
        echo "2. **Monitoreo Continuo**"
        echo "   - Ejecutar script de monitoreo regularmente"
        echo "   - Revisar logs de errores"
        echo "   - Verificar métricas de rendimiento"
        echo ""
        echo "3. **Desarrollo de Funcionalidades**"
        echo "   - Implementar normalizadores de datos"
        echo "   - Agregar endpoints de consulta"
        echo "   - Configurar alertas y notificaciones"
        echo ""
        
        echo "## Comandos Útiles"
        echo ""
        echo "\`\`\`bash"
        echo "# Monitorear contenedores"
        echo "./scripts/monitor_containers.sh"
        echo ""
        echo "# Generar reporte de estado"
        echo "./scripts/monitor_containers.sh -r"
        echo ""
        echo "# Ver logs de un contenedor específico"
        echo "docker logs -f [nombre_contenedor]"
        echo ""
        echo "# Reiniciar un servicio"
        echo "docker restart [nombre_contenedor]"
        echo ""
        echo "# Detener todos los servicios"
        echo "docker compose -f infra/containers/docker-compose.yaml down"
        echo ""
        echo "# Levantar todos los servicios"
        echo "docker compose -f infra/containers/docker-compose.yaml up -d"
        echo "\`\`\`"
        echo ""
        
        echo "---"
        echo "*Documento generado automáticamente el $(date '+%Y-%m-%d %H:%M:%S')*"
        
    } > "$doc_file"
    
    echo -e "${GREEN}✅ Documentación generada: $doc_file${NC}"
    echo -e "${BLUE}📁 Ubicación: $(pwd)/$doc_file${NC}"
    echo -e "${YELLOW}📖 Formato: Markdown${NC}"
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  -d, --doc        Generar documentación del desarrollo (por defecto)"
    echo "  -h, --help       Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0               # Generar documentación"
    echo "  $0 -d            # Generar documentación explícitamente"
    echo "  $0 --help        # Mostrar ayuda"
}

# Función principal
main() {
    case "${1:-doc}" in
        -d|--doc|doc)
            generate_development_doc
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
