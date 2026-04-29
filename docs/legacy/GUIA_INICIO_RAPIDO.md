# 🚀 Guía de Inicio Rápido - IoT Middleware

## 📋 Prerrequisitos

Antes de iniciar el sistema, asegúrate de tener:

1. **Python 3.9+** instalado
2. **Podman** o **Docker** instalado (para servicios externos)
3. **Entorno virtual** creado y activado

## 🔧 Paso 1: Instalar Dependencias

```bash
# Activar entorno virtual (si no está activo)
source venv/bin/activate

# Instalar todas las dependencias
pip install -r requirements.txt
```

## 🐳 Paso 2: Levantar Servicios Externos

El sistema necesita los siguientes servicios:

- **MQTT Broker** (Mosquitto)
- **PostgreSQL** (Base de datos relacional)
- **InfluxDB** (Base de datos de series temporales)
- **RabbitMQ** (Comunicación asíncrona - opcional para monitoreo)

### Opción A: Usar Podman Compose (Recomendado)

```bash
# Desde el directorio raíz del proyecto
cd containers

# Iniciar todos los servicios
podman-compose up -d

# Verificar que todos los servicios estén corriendo
podman-compose ps
```

### Opción B: Iniciar Servicios Manualmente

Si prefieres iniciar los servicios manualmente, necesitarás:

1. **Mosquitto MQTT** en `localhost:1883`
2. **PostgreSQL** en `localhost:5432`
3. **InfluxDB** en `localhost:8086`
4. **RabbitMQ** en `localhost:5672` (opcional)

## ⚙️ Paso 3: Configurar Variables de Entorno

Verifica que `config.yaml` tenga las configuraciones correctas para tus servicios:

```yaml
mqtt:
  broker:
    host: "localhost"
    port: 1883

postgresql:
  host: "localhost"
  port: 5432
  database: "iot_middleware"
  username: "iot_user"
  password: "iot_password"

influxdb:
  url: "http://localhost:8086"
  token: "your_influxdb_token"
  org: "iot_org"
  bucket: "iot_data"

rabbitmq:
  host: "localhost"
  port: 5672
  username: "guest"
  password: "guest"
```

## 🚀 Paso 4: Iniciar el Middleware

### Opción A: Script Principal (Solo transición/manual)

```bash
# Desde el directorio raíz
python main.py
```

Este script se conserva para flujos manuales y de transición. Iniciará:
- ✅ Cliente MQTT para ingesta
- ✅ API REST en puerto 8000
- ✅ Servicio de monitoreo (si RabbitMQ está disponible)
- ✅ Servicios de auditoría

### Opción B: Rutas canónicas actuales

```bash
# Stack local completo
podman compose -f infra/containers/podman-compose.yaml up -d

# Dominio operacional oficial
cd apps/topology-next && npm run dev

# Runtime de ingesta Python
python -m iot_middleware.services.ingestor
```

### Opción C: Iniciar Componentes Individualmente

```bash
# Terminal 1: API REST
uvicorn iot_middleware.api.api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Servicio de Ingesta
python -m iot_middleware.services.ingestor

# Terminal 3: Dashboard (opcional)
python -m containers.dashboard.main
```

## 🧪 Paso 5: Verificar que Todo Funciona

### 1. Verificar API REST

```bash
# Health check
curl http://localhost:8000/health

# Documentación interactiva
open http://localhost:8000/docs
```

### 2. Verificar Dashboard (si está corriendo)

```bash
open http://localhost:8080
```

### 3. Enviar un Mensaje MQTT de Prueba

```bash
# Instalar mosquitto-clients si no lo tienes
# macOS: brew install mosquitto

# Publicar un mensaje de prueba
mosquitto_pub -h localhost -p 1883 -t "iot/test/proyecto/unidad/dispositivo/canal" -m '{"valor": 25.5, "timestamp": "2025-01-05T20:00:00Z"}'
```

### 4. Verificar que el Mensaje se Procesó

```bash
# Consultar datos a través de la API
curl http://localhost:8000/data?limit=10
```

## 📊 Paso 6: Monitoreo y Logs

### Ver Logs del Sistema

```bash
# Logs del script principal
tail -f iot_middleware.log

# Logs de contenedores (si usas Podman)
podman-compose -f containers/podman-compose.yaml logs -f
```

### Verificar Estado de Servicios

```bash
# Ver estado de todos los servicios
python scripts/verify_system.py

# Ver contenedores corriendo
podman ps
```

## 🎯 Pruebas Recomendadas

### 1. Prueba de Ingesta MQTT

```bash
# Publicar varios mensajes de prueba
for i in {1..10}; do
  mosquitto_pub -h localhost -p 1883 \
    -t "iot/test/proyecto/unidad/dispositivo/temperatura" \
    -m "{\"valor\": $((20 + i)), \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
  sleep 1
done
```

### 2. Prueba de API REST

```bash
# Obtener proyectos
curl http://localhost:8000/proyectos

# Obtener datos
curl http://localhost:8000/data?limit=5

# Obtener eventos
curl http://localhost:8000/eventos?limit=5
```

### 3. Prueba del Dashboard

1. Abre `http://localhost:8080` en tu navegador
2. Deberías ver:
   - ✅ Métricas en tiempo real
   - ✅ Eventos del sistema
   - ✅ Estado de conexión WebSocket

## 🐛 Troubleshooting

### El middleware no inicia

1. **Verificar que los servicios externos estén corriendo:**
   ```bash
   # Verificar MQTT
   mosquitto_sub -h localhost -p 1883 -t "#" -v
   
   # Verificar PostgreSQL
   psql -h localhost -U iot_user -d iot_middleware
   
   # Verificar InfluxDB
   curl http://localhost:8086/health
   
   # Verificar RabbitMQ
   curl http://localhost:15672/api/overview -u guest:guest
   ```

2. **Verificar configuración:**
   ```bash
   python scripts/verify_system.py
   ```

3. **Ver logs de errores:**
   ```bash
   tail -f iot_middleware.log
   ```

### La API no responde

1. Verificar que el puerto 8000 no esté en uso:
   ```bash
   lsof -i :8000
   ```

2. Verificar logs de uvicorn:
   ```bash
   # Si iniciaste con uvicorn directamente, los logs aparecen en consola
   ```

### No llegan datos MQTT

1. Verificar conexión MQTT:
   ```bash
   mosquitto_sub -h localhost -p 1883 -t "#" -v
   ```

2. Verificar que el cliente MQTT esté suscrito a los tópicos correctos en `config.yaml`

3. Verificar logs del servicio de ingesta

## 📝 Próximos Pasos

Una vez que el sistema esté funcionando:

1. ✅ **Configurar autenticación**: Habilitar JWT en `config.yaml`
2. ✅ **Configurar base de datos**: Ejecutar migraciones de Alembic
3. ✅ **Configurar InfluxDB**: Crear organización y bucket
4. ✅ **Personalizar configuración**: Ajustar parámetros según necesidades
5. ✅ **Agregar dispositivos**: Crear proyectos, unidades y dispositivos
6. ✅ **Monitorear métricas**: Usar el dashboard para monitoreo en tiempo real

## 🔗 Enlaces Útiles

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Dashboard**: http://localhost:8080
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

---

**¡El sistema está listo para usar!** 🎉
