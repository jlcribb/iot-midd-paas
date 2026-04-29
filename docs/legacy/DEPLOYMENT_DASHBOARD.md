# 🚀 Guía de Deployment del Dashboard

## 📋 Resumen

El dashboard de monitoreo es un servicio independiente que se ejecuta en su propio contenedor, consumiendo eventos de RabbitMQ y mostrándolos en tiempo real mediante WebSocket.

## 🏗️ Arquitectura

```
┌─────────────────┐
│  RabbitMQ       │
│  (Contenedor)   │
└────────┬────────┘
         │
         │ Eventos
         ▼
┌─────────────────┐
│  Dashboard      │
│  (Contenedor)   │───▶ WebSocket ───▶ Navegadores
└─────────────────┘
```

## 🚀 Deployment Rápido

### Opción 1: Con Podman Compose (Recomendado)

```bash
# Desde el directorio raíz del proyecto
cd /Users/joseluis/dev/iot-middleware

# Iniciar todos los servicios (incluyendo dashboard)
podman-compose -f containers/podman-compose.yaml up -d

# Ver logs del dashboard
podman logs -f iotmw-dashboard

# Acceder al dashboard
open http://localhost:8080
```

### Opción 2: Construir y Ejecutar Manualmente

```bash
# Construir imagen del dashboard
podman build -t iot-middleware-dashboard -f containers/dashboard/Dockerfile .

# Ejecutar contenedor
podman run -d \
  --name iotmw-dashboard \
  -p 8080:8080 \
  -e RABBITMQ_HOST=rabbitmq \
  -e RABBITMQ_PORT=5672 \
  -e RABBITMQ_USERNAME=guest \
  -e RABBITMQ_PASSWORD=guest \
  --network podman \
  iot-middleware-dashboard
```

### Opción 3: Desarrollo Local

```bash
# Instalar dependencias
pip install -r containers/dashboard/requirements.txt

# Ejecutar dashboard
python -m containers.dashboard.main

# O usar el script
./containers/dashboard/start.sh
```

## ⚙️ Configuración

### Variables de Entorno

El dashboard se configura mediante variables de entorno:

```bash
# Dashboard
DASHBOARD_PORT=8080
DASHBOARD_HOST=0.0.0.0
DASHBOARD_CONFIG=/app/config.yaml

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/
RABBITMQ_EXCHANGE=iot_middleware
RABBITMQ_QUEUE_PREFIX=iot
```

### Archivo de Configuración

Alternativamente, puedes usar un archivo `config.yaml`:

```yaml
rabbitmq:
  host: "rabbitmq"
  port: 5672
  username: "guest"
  password: "guest"
  virtual_host: "/"
  exchange: "iot_middleware"
  queue_prefix: "iot"
  enable_monitoring: true
```

## 🔍 Verificación

### 1. Verificar que el contenedor esté ejecutándose

```bash
podman ps | grep dashboard
```

Deberías ver:
```
iotmw-dashboard    python:3.12-slim    ...    0.0.0.0:8080->8080/tcp
```

### 2. Verificar health check

```bash
curl http://localhost:8080/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "rabbitmq": {
    "connected": true,
    "host": "rabbitmq",
    "port": 5672
  },
  "active_connections": 0,
  "service": "dashboard"
}
```

### 3. Acceder al dashboard

Abre tu navegador en:
```
http://localhost:8080
```

Deberías ver:
- ✅ Header con título y estado de conexión
- ✅ 6 tarjetas de métricas
- ✅ Panel de eventos en tiempo real

## 🐛 Troubleshooting

### Dashboard no inicia

1. **Verificar logs**:
```bash
podman logs iotmw-dashboard
```

2. **Verificar dependencias**:
```bash
podman exec iotmw-dashboard pip list | grep -E "fastapi|pika|pydantic"
```

3. **Verificar configuración**:
```bash
podman exec iotmw-dashboard env | grep -E "RABBITMQ|DASHBOARD"
```

### No se conecta a RabbitMQ

1. **Verificar que RabbitMQ esté ejecutándose**:
```bash
podman ps | grep rabbitmq
```

2. **Verificar conectividad**:
```bash
podman exec iotmw-dashboard ping -c 3 rabbitmq
```

3. **Verificar credenciales**:
```bash
podman exec iotmw-dashboard env | grep RABBITMQ
```

### WebSocket no funciona

1. **Verificar que el puerto esté expuesto**:
```bash
podman port iotmw-dashboard
```

2. **Verificar firewall**:
```bash
# En macOS
sudo pfctl -s rules | grep 8080
```

3. **Probar conexión WebSocket**:
```bash
# Instalar wscat
npm install -g wscat

# Conectar
wscat -c ws://localhost:8080/ws
```

### No llegan eventos

1. **Verificar que el servicio de monitoreo esté publicando**:
```bash
# Ver logs del servicio de monitoreo
podman logs iotmw-ingestor | grep -i "monitoring\|rabbitmq"
```

2. **Verificar colas en RabbitMQ**:
```bash
# Acceder a la consola de RabbitMQ
open http://localhost:15672
# Usuario: guest, Contraseña: guest
```

3. **Verificar suscripción**:
```bash
# Ver logs del dashboard
podman logs iotmw-dashboard | grep -i "subscribe\|event"
```

## 📊 Monitoreo

### Logs en Tiempo Real

```bash
# Logs del dashboard
podman logs -f iotmw-dashboard

# Logs de RabbitMQ
podman logs -f rabbitmq

# Todos los logs
podman-compose -f containers/podman-compose.yaml logs -f
```

### Métricas del Contenedor

```bash
# Estadísticas de recursos
podman stats iotmw-dashboard

# Información del contenedor
podman inspect iotmw-dashboard
```

## 🔄 Actualización

### Actualizar el Dashboard

```bash
# Detener contenedor
podman stop iotmw-dashboard
podman rm iotmw-dashboard

# Reconstruir imagen
podman build -t iot-middleware-dashboard -f containers/dashboard/Dockerfile .

# Reiniciar
podman-compose -f containers/podman-compose.yaml up -d dashboard
```

### Actualizar Código en Desarrollo

```bash
# El código está montado como volumen, solo reinicia
podman restart iotmw-dashboard
```

## 🔐 Seguridad para Producción

### 1. Cambiar Credenciales

```bash
# Generar contraseña segura
openssl rand -base64 32

# Actualizar en podman-compose.yaml
RABBITMQ_PASSWORD=<password-segura>
```

### 2. Habilitar HTTPS/WSS

```bash
# Agregar certificados SSL
# Configurar reverse proxy (nginx/traefik)
```

### 3. Autenticación

```bash
# Agregar autenticación JWT al WebSocket
# Implementar en dashboard/main.py
```

### 4. Rate Limiting

```bash
# Limitar conexiones por IP
# Implementar en dashboard/main.py
```

## 📈 Escalabilidad

### Múltiples Instancias

```bash
# Ejecutar múltiples instancias del dashboard
podman run -d --name dashboard-1 -p 8080:8080 ...
podman run -d --name dashboard-2 -p 8081:8080 ...
podman run -d --name dashboard-3 -p 8082:8080 ...

# Usar load balancer (nginx/traefik)
```

### High Availability

```bash
# Configurar RabbitMQ en cluster
# Usar múltiples instancias del dashboard
# Implementar health checks y auto-restart
```

## 🎯 Próximos Pasos

- [ ] Agregar autenticación
- [ ] Implementar HTTPS/WSS
- [ ] Agregar gráficos históricos
- [ ] Integrar con Grafana
- [ ] Agregar alertas visuales
- [ ] Implementar rate limiting

---

**¡El dashboard está listo para deployment!** 🚀
