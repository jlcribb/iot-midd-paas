# 🚀 Script Gestor IoT Middleware

Script principal para gestionar y levantar todos los servicios del IoT Middleware.

## 📋 Descripción

El script `iot_middleware_manager.sh` proporciona una interfaz interactiva para gestionar todos los servicios del middleware, incluyendo:

- ✅ Levantar servicios (contenedores)
- ✅ Detener servicios
- ✅ Reiniciar servicios
- ✅ Monitorear contenedores
- ✅ Ver logs de contenedores
- ✅ Verificar conectividad
- ✅ Ver estado del sistema

## 🚀 Uso Rápido

### Ejecutar el script

Desde cualquier directorio del proyecto:

```bash
./scripts/iot_middleware_manager.sh
```

O con ruta completa:

```bash
bash scripts/iot_middleware_manager.sh
```

### Levantar todos los servicios (opción rápida)

Si solo quieres levantar los servicios sin el menú interactivo:

```bash
docker compose -f infra/containers/docker-compose.yaml up -d
```

O usando el script desde cualquier lugar:

```bash
# Opción 4 del menú: Levantar servicios
./scripts/iot_middleware_manager.sh
# Luego selecciona la opción 4
```

## 📋 Opciones del Menú

El script muestra un menú interactivo con las siguientes opciones:

1. **📊 Monitorear estado de contenedores**
   - Muestra el estado actual de todos los contenedores

2. **📋 Generar reporte de estado**
   - Genera un reporte detallado del estado del sistema

3. **📖 Generar documentación del desarrollo**
   - Genera documentación del desarrollo

4. **🚀 Levantar servicios**
   - Inicia todos los servicios usando `docker compose up -d`
   - Espera 10 segundos para la inicialización
   - Muestra el estado de los contenedores

5. **🛑 Detener servicios**
   - Detiene todos los servicios usando `docker compose down`

6. **🔄 Reiniciar servicios**
   - Detiene y reinicia todos los servicios

7. **📝 Ver logs de un contenedor**
   - Muestra una lista de contenedores disponibles
   - Permite seleccionar uno para ver sus logs en tiempo real

8. **🌐 Verificar conectividad**
   - Verifica que los puertos estén abiertos:
     - 1883 (MQTT Mosquitto)
     - 5432 (PostgreSQL)
     - 8086 (InfluxDB)
     - 8000 (API FastAPI)
   - Verifica health checks de servicios

9. **📊 Estado del sistema**
   - Muestra información del sistema operativo
   - Muestra uso de recursos (espacio en disco)
   - Muestra información de red
   - Muestra información de Docker

0. **❌ Salir**
   - Sale del script

## 🔧 Requisitos

- **Docker Desktop** instalado y configurado
- **docker compose** disponible
- Acceso al repositorio con `infra/containers/docker-compose.yaml`

## 🎯 Ejemplo de Uso

```bash
# 1. Ejecutar el script
./scripts/iot_middleware_manager.sh

# 2. El menú aparecerá:
# ========================================
#   GESTOR IOT MIDDLEWARE
# ========================================
#
# Selecciona una opción:
#
# 1. 📊 Monitorear estado de contenedores
# 2. 📋 Generar reporte de estado
# 3. 📖 Generar documentación del desarrollo
# 4. 🚀 Levantar servicios
# 5. 🛑 Detener servicios
# 6. 🔄 Reiniciar servicios
# 7. 📝 Ver logs de un contenedor
# 8. 🌐 Verificar conectividad
# 9. 📊 Estado del sistema
# 0. ❌ Salir
#
# Opción: 4

# 3. El script levantará todos los servicios
# 4. Mostrará el estado de los contenedores
```

## 🐛 Solución de Problemas

### Error: "`docker compose` no está disponible"

**Solución:**
```bash
# Verificar que Docker esté instalado
docker --version
docker compose version
```

### Error: "No se encontró un archivo docker-compose válido"

**Solución:**
El script usa únicamente la ruta canónica `infra/containers/docker-compose.yaml`. Si aún aparece:

```bash
# Ejecutar desde el directorio raíz del proyecto
cd /ruta/al/iot-middleware
./scripts/iot_middleware_manager.sh
```

### Los servicios no se levantan

**Verificar:**
1. Que Docker Desktop esté corriendo:
   ```bash
   docker ps
   ```

2. Que el archivo `infra/containers/docker-compose.yaml` exista

3. Que no haya puertos ocupados:
   ```bash
   # Verificar puertos
   lsof -i :1883  # MQTT
   lsof -i :5432  # PostgreSQL
   lsof -i :8086  # InfluxDB
   lsof -i :8000  # API
   ```

## 📝 Notas

- El script funciona desde cualquier directorio del proyecto
- Usa `docker compose` como estándar operativo
- Prefiere la infraestructura canónica en `infra/containers/`
- El admin transicional vive en `apps/admin-fastapi/`
- El dashboard experimental vive en `apps/monitoring-dashboard/`
- Los servicios se levantan en segundo plano (modo detached: `-d`)
- Los logs se muestran en tiempo real cuando se selecciona la opción 7

## 🔗 Enlaces Relacionados

- [Guía de Inicio Rápido](../docs/legacy/GUIA_INICIO_RAPIDO.md)
- [Documentación legacy del repo embebido de containers](../docs/legacy/containers/README.md)
- [README Principal](../README.md)

¡Listo! 🚀
