# Sistema de Monitoreo en Tiempo Real - IoT Middleware

## 🎯 Descripción

El sistema de monitoreo en tiempo real utiliza **RabbitMQ** para comunicación asíncrona entre microservicios y proporciona un **dashboard web** que muestra métricas y eventos en tiempo real mediante WebSockets.

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Servicios IoT  │───▶│  Monitoring     │───▶│   RabbitMQ      │
│  Middleware     │    │  Service        │    │   Exchange      │
│                 │    │                 │    │                 │
│ • Ingestor      │    │ • Recopila      │    │ • Publica       │
│ • Procesador    │    │   métricas      │    │   eventos       │
│ • Almacenamiento│    │ • Publica       │    │ • Enruta        │
│ • Multiprotocolo│    │   eventos       │    │   mensajes      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Dashboard      │
                                                │  WebSocket      │
                                                │                 │
                                                │ • Consume       │
                                                │   eventos       │
                                                │ • Muestra       │
                                                │   métricas      │
                                                └─────────────────┘
```

## 🚀 Características

### ✅ Comunicación Asíncrona
- **RabbitMQ** como broker de mensajes
- Publicación/consumo de eventos en tiempo real
- Exchange tipo `topic` para enrutamiento flexible
- Mensajes persistentes y confiables

### ✅ Dashboard en Tiempo Real
- **WebSocket** para actualizaciones instantáneas
- Visualización de métricas del sistema
- Eventos en tiempo real
- Interfaz web moderna y responsive

### ✅ Métricas Monitoreadas
- Mensajes procesados/fallidos
- Operaciones de base de datos
- Protocolos activos
- Dispositivos activos
- Uptime del sistema
- Estado de servicios

## 📋 Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar RabbitMQ

Agrega la configuración de RabbitMQ a tu `config.yaml`:

```yaml
rabbitmq:
  host: "localhost"
  port: 5672
  username: "guest"
  password: "guest"
  virtual_host: "/"
  exchange: "iot_middleware"
  queue_prefix: "iot"
  heartbeat: 600
  connection_attempts: 3
  retry_delay: 5
  enable_monitoring: true
```

### 3. Iniciar RabbitMQ

Con Docker/Podman:

```bash
podman run -d --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management
```

O instalar localmente:

```bash
# Ubuntu/Debian
sudo apt-get install rabbitmq-server

# macOS
brew install rabbitmq
```

## 🎮 Uso

### 1. Iniciar el Sistema

```bash
python main.py
```

`main.py` se conserva para uso manual/transicional. La ruta operativa preferida para stack local hoy es:

```bash
podman compose -f infra/containers/podman-compose.yaml up -d
```

Si se usa `main.py`, el sistema iniciará automáticamente:
- ✅ Servicio de ingesta
- ✅ Servicio de monitoreo
- ✅ API REST
- ✅ Dashboard WebSocket

### 2. Acceder al Dashboard

Abre tu navegador en:

```
http://localhost:8000/dashboard/
```

El dashboard mostrará:
- **Métricas en tiempo real**: Mensajes procesados, errores, operaciones BD, etc.
- **Eventos en tiempo real**: Lista de eventos del sistema
- **Estado de conexión**: Indicador de conexión WebSocket

### 3. Endpoints Disponibles

#### Dashboard Web
```
GET /dashboard/
```
Página HTML del dashboard de monitoreo

#### WebSocket
```
WS /dashboard/ws
```
Conexión WebSocket para recibir eventos en tiempo real

#### Health Check
```
GET /dashboard/health
```
Verifica el estado del dashboard y RabbitMQ

## 📊 Tipos de Eventos

El sistema publica los siguientes tipos de eventos:

### 1. Métricas (METRIC)
```json
{
  "event_type": "metric",
  "service": "monitoring",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "metric": "system.messages_processed",
    "value": 1250
  },
  "severity": "info"
}
```

### 2. Estado (STATUS)
```json
{
  "event_type": "status",
  "service": "ingestor",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "status": "online",
    "details": {
      "messages_processed": 1250,
      "active_protocols": 7
    }
  },
  "severity": "info"
}
```

### 3. Alertas (ALERT)
```json
{
  "event_type": "alert",
  "service": "database",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "message": "Alta tasa de errores en base de datos",
    "error_count": 15
  },
  "severity": "warning"
}
```

### 4. Datos (DATA)
```json
{
  "event_type": "data",
  "service": "ingestor",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "canal_id": "uuid-canal",
    "valor": 25.5,
    "tipo": "temperature"
  },
  "severity": "info"
}
```

## 🔧 Integración con Servicios

### Publicar Métricas desde un Servicio

```python
from iot_middleware.services.monitoring_service import MonitoringService
from iot_middleware.config import RabbitMQConfig

# Crear servicio de monitoreo
monitoring = MonitoringService(rabbitmq_config)

# Publicar métrica
monitoring.publish_metric(
    metric_name="custom.metric",
    value=42,
    service="mi_servicio"
)

# Publicar estado
monitoring.publish_status(
    service="mi_servicio",
    status="online",
    details={"version": "1.0.0"}
)

# Publicar alerta
monitoring.publish_alert(
    service="mi_servicio",
    message="Algo importante ocurrió",
    severity="warning"
)
```

## 🎨 Personalización del Dashboard

El dashboard está en `src/iot_middleware/api/routers/dashboard_router.py`. Puedes personalizar:

- **Métricas mostradas**: Modifica el HTML en `dashboard_page()`
- **Estilos CSS**: Edita los estilos en el HTML
- **Lógica JavaScript**: Modifica el script en el HTML

## 🐛 Troubleshooting

### RabbitMQ no se conecta

1. Verifica que RabbitMQ esté ejecutándose:
```bash
podman ps | grep rabbitmq
# o
sudo systemctl status rabbitmq-server
```

2. Verifica las credenciales en `config.yaml`

3. Verifica que el puerto 5672 esté abierto

### Dashboard no muestra datos

1. Verifica que el servicio de monitoreo esté iniciado:
```bash
# En los logs deberías ver:
# ✅ Servicio de monitoreo inicializado exitosamente
```

2. Verifica la conexión WebSocket en la consola del navegador

3. Verifica el endpoint de health:
```bash
curl http://localhost:8000/dashboard/health
```

### Eventos no llegan al dashboard

1. Verifica que RabbitMQ esté conectado:
```bash
# En los logs:
# ✅ Conectado a RabbitMQ exitosamente
```

2. Verifica que el consumidor esté activo:
```bash
# En los logs:
# 🔄 Consumidor RabbitMQ iniciado
```

3. Verifica las conexiones WebSocket activas:
```bash
curl http://localhost:8000/dashboard/health
# Debería mostrar "active_connections" > 0
```

## 📈 Monitoreo Avanzado

### Acceder a la Consola de RabbitMQ

```
http://localhost:15672
```

Usuario/contraseña por defecto: `guest/guest`

### Ver Colas y Mensajes

En la consola de RabbitMQ puedes:
- Ver todas las colas creadas
- Inspeccionar mensajes
- Ver estadísticas de throughput
- Monitorear conexiones

## 🔐 Seguridad

Para producción, considera:

1. **Cambiar credenciales por defecto** de RabbitMQ
2. **Habilitar TLS** para conexiones seguras
3. **Configurar usuarios y permisos** en RabbitMQ
4. **Limitar acceso** al dashboard con autenticación
5. **Usar VPN o red privada** para RabbitMQ

## 🚀 Próximos Pasos

- [ ] Agregar gráficos históricos
- [ ] Implementar alertas configurables
- [ ] Agregar exportación de métricas
- [ ] Integrar con Prometheus/Grafana
- [ ] Agregar autenticación al dashboard

---

**¡El sistema de monitoreo está listo para usar!** 🎉

Para más información, consulta la documentación principal del proyecto.
