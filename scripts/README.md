# Scripts de Gestión y Monitoreo - IoT Middleware

Este directorio contiene scripts para gestionar, monitorear y documentar el estado del IoT Middleware.

## 📁 Scripts Disponibles

### 1. `iot_middleware_manager.sh` - Gestor Principal
Script principal con menú interactivo que combina todas las funcionalidades.

**Uso:**
```bash
./scripts/iot_middleware_manager.sh
```

**Funcionalidades:**
- 📊 Monitorear estado de contenedores
- 📋 Generar reporte de estado
- 📖 Generar documentación del desarrollo
- 🚀 Levantar servicios
- 🛑 Detener servicios
- 🔄 Reiniciar servicios
- 📝 Ver logs de contenedores
- 🌐 Verificar conectividad
- 📊 Estado del sistema

### 2. `monitor_containers.sh` - Monitoreo de Contenedores
Script especializado para monitorear el estado de todos los contenedores.

**Uso:**
```bash
# Monitoreo en pantalla
../scripts/monitor_containers.sh

# Generar reporte en archivo
../scripts/monitor_containers.sh -r

# Mostrar ayuda
../scripts/monitor_containers.sh -h
```

**Características:**
- ✅ Verificación de estado de contenedores
- 🌐 Verificación de puertos abiertos
- 🏥 Health checks de servicios
- 📊 Resumen de estado general
- 🎨 Salida con colores y emojis

### 3. `document_development.sh` - Documentación del Desarrollo
Script para generar documentación automática del estado del desarrollo.

**Uso:**
```bash
# Generar documentación
../scripts/document_development.sh

# Mostrar ayuda
../scripts/document_development.sh -h
```

**Características:**
- 📖 Genera documentación en Markdown
- 📊 Incluye métricas del sistema
- 🔍 Logs recientes de contenedores
- 📋 Estado de la infraestructura
- 🚀 Próximos pasos recomendados

## 🚀 Instalación y Configuración

### Prerrequisitos
- Docker Desktop instalado y funcionando
- `docker compose` disponible
- Bash shell
- Comandos: `curl`, `nc` (netcat)

### Verificar Docker Compose
```bash
docker --version
docker compose version
```

### Permisos de Ejecución
```bash
chmod +x scripts/*.sh
```

## 📋 Uso Rápido

### Monitoreo Básico
```bash
# Ejecutar gestor principal desde la raíz del repo
./scripts/iot_middleware_manager.sh

# O ejecutar monitoreo directo
./scripts/monitor_containers.sh
```

### Generar Documentación
```bash
# Generar documentación del desarrollo
./scripts/document_development.sh

# Generar reporte de estado
./scripts/monitor_containers.sh -r
```

### Stack oficial
```bash
docker compose -f infra/containers/docker-compose.yaml up -d
./scripts/docker-stack.sh check
```

### Smokes de Control Paramétrico
```bash
# Smoke directo del worker (debug local, con fallback permitido)
./scripts/smoke_control_engine.sh

# Smoke RabbitMQ del worker (enabled + disabled, sin MQTT)
./scripts/smoke_control_engine_rabbitmq.sh

# Smoke oficial de consolidación del canal MQTT -> runtime -> observabilidad
./scripts/smoke_control_engine_end_to_end.sh
```

Ese smoke está pensado para ejecutarse desde la máquina host, con el stack
canónico publicado por Docker Compose. Si no se definieron overrides manuales,
resuelve por defecto:

- PostgreSQL: `localhost:5432`
- RabbitMQ: `localhost:5672`
- MQTT: `localhost:1883`
- observabilidad Next.js: `http://127.0.0.1:3000`

El smoke E2E distingue estos niveles:

- `contract-level`
- `component-level`
- `broker-level`
- `database-level`
- `full E2E`

Y separa además la evidencia de auditoría en:

- `audit_publish`
- `audit_persistence_attempt`
- `audit_database_row`
- `audit_metadata_consistency`

Y usa estos códigos de salida:

- `0`: PASS completo
- `1`: FAIL
- `2`: WARN/SKIP sin fallo duro

`./scripts/podman-stack.sh` queda únicamente como wrapper deprecated de compatibilidad.

## 📊 Salidas Generadas

### Archivos de Reporte
- **Estado:** `iot_middleware_status_YYYYMMDD_HHMMSS.txt`
- **Documentación:** `development_log_YYYYMMDD_HHMMSS.md`

### Ubicación de Archivos
Los archivos se generan en el directorio desde donde se ejecuta el script.

## 🔧 Personalización

### Modificar Puertos
Edita los scripts para cambiar los puertos monitoreados:
```bash
# En monitor_containers.sh y otros scripts
for port in 1883 8086 8000; do
    # ... código de verificación
done
```

### Agregar Nuevos Servicios
Para agregar nuevos servicios, modifica las funciones de monitoreo:
```bash
# Agregar nuevo contenedor
echo -e "${YELLOW}5. NUEVO_SERVICIO${NC}"
echo -e "   📍 Contenedor: nuevo-servicio"
echo -e "   🏃 Estado: $(get_container_status nuevo-servicio)"
```

## 📝 Logs y Debugging

### Ver Logs de Contenedores
```bash
# Ver logs en tiempo real
docker logs -f [nombre_contenedor]

# Ver últimos N logs
docker logs --tail 10 [nombre_contenedor]
```

### Verificar Estado de Docker
```bash
# Listar contenedores
docker ps

# Ver información detallada
docker inspect [nombre_contenedor]

# Ver espacio usado por imágenes y contenedores
docker system df
```

## 🚨 Solución de Problemas

### Error: "`docker compose` no está disponible"
```bash
docker --version
docker compose version
```

### Error: "Este script debe ejecutarse desde el directorio 'containers'"
```bash
cd containers
../scripts/iot_middleware_manager.sh
```

### Error: "Puerto X está cerrado"
1. Verificar que el contenedor esté ejecutándose
2. Verificar logs del contenedor
3. Verificar configuración de puertos en `docker-compose.yaml`

### Contenedor no inicia
```bash
# Ver logs del contenedor
docker logs [nombre_contenedor]

# Reiniciar el contenedor
docker restart [nombre_contenedor]

# Verificar recursos del sistema
docker system df
```

## 📚 Ejemplos de Uso

### Ejemplo 1: Monitoreo Diario
```bash
# Crear script cron para monitoreo automático
echo "0 9 * * * cd /path/to/iot-middleware/containers && ../scripts/monitor_containers.sh -r" | crontab -
```

### Ejemplo 2: Documentación Automática
```bash
# Generar documentación antes de commits
../scripts/document_development.sh
git add development_log_*.md
git commit -m "Actualizar documentación del desarrollo"
```

### Ejemplo 3: Verificación Rápida
```bash
# Verificar solo conectividad
../scripts/iot_middleware_manager.sh
# Seleccionar opción 8
```

## 🔄 Mantenimiento

### Actualizar Scripts
Los scripts se actualizan automáticamente con cada ejecución, incluyendo:
- Timestamps actualizados
- Estado actual de contenedores
- Logs recientes
- Métricas del sistema

### Limpieza de Archivos
Los archivos generados incluyen timestamp, por lo que puedes:
- Mantener historial completo
- Eliminar archivos antiguos manualmente
- Configurar limpieza automática con cron

## 📞 Soporte

Para problemas o mejoras:
1. Revisar logs de contenedores
2. Verificar estado del sistema
3. Consultar documentación generada
4. Revisar configuración de `docker-compose.yaml`

---

**Nota:** Todos los scripts están diseñados para ejecutarse desde el directorio `containers` del proyecto IoT Middleware.
