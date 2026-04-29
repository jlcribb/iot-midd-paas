# Servicio de Ingesta MQTT - IoT Middleware

## Descripción

El servicio de ingesta MQTT es un componente central del IoT Middleware que se encarga de recibir, procesar y almacenar datos de dispositivos IoT a través del protocolo MQTT. Este servicio implementa un pipeline completo de ingesta de datos con capacidades de validación, transformación y almacenamiento.

## Características Principales

### 🔌 Conectividad MQTT
- **Suscripción automática** a tópicos configurados
- **Reconexión automática** con backoff exponencial
- **Soporte para QoS** (0, 1, 2) configurable
- **Autenticación** con usuario/contraseña y TLS
- **Keepalive** configurable para mantener conexiones estables

### 📊 Procesamiento de Datos
- **Parseo inteligente** de payloads (JSON, string, binario)
- **Mapeo de tópicos** a entidades del sistema (proyecto/unidad/dispositivo/canal)
- **Validación de datos** por tipo y rangos configurados
- **Normalización** de datos según esquemas predefinidos
- **Transformación** de formatos y unidades

### 🗄️ Almacenamiento
- **Inserción en lote** para optimizar rendimiento
- **Soporte multi-base de datos** (PostgreSQL, InfluxDB, híbrido)
- **Pool de conexiones** configurable
- **Transacciones** para consistencia de datos
- **Particionamiento** automático por fecha

### 🚨 Sistema de Alarmas
- **Umbrales configurables** por canal y tipo de dato
- **Múltiples niveles de severidad** (INFO, ADVERTENCIA, CRÍTICO)
- **Detección automática** de condiciones anómalas
- **Notificaciones** configurables
- **Historial de alarmas** persistente

### 📈 Monitoreo y Métricas
- **Métricas en tiempo real** de rendimiento
- **Logging estructurado** con diferentes niveles
- **Health checks** automáticos
- **Alertas de rendimiento** configurables
- **Dashboard de métricas** integrado

### 🚀 Rendimiento y Escalabilidad
- **Procesamiento asíncrono** con workers múltiples
- **Cola de mensajes** con backpressure configurable
- **Procesamiento en lote** optimizado
- **Balanceo de carga** automático
- **Escalado horizontal** soportado

## Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Dispositivos  │    │   Broker MQTT    │    │  Servicio de    │
│      IoT        │───▶│   (Mosquitto)    │───▶│   Ingesta       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Base de       │    │   Sistema de     │    │   API REST      │
│   Datos         │◀───│   Alarmas        │◀───│   (Métricas)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Instalación

### Requisitos Previos
- Python 3.8+
- PostgreSQL 12+ o InfluxDB 2.0+
- Broker MQTT (Mosquitto recomendado)
- Docker/Podman (opcional)

### Instalación de Dependencias
```bash
pip install -r requirements.txt
```

### Configuración de Base de Datos
```bash
# PostgreSQL
createdb iot_middleware
psql -d iot_middleware -f src/iot_middleware/storage/schema.sql

# InfluxDB
influx bucket create -n iot_data -r 30d
```

## Configuración

### Archivo de Configuración Principal
El servicio se configura a través de un archivo YAML que define todos los parámetros:

```yaml
# config_ingesta.yaml
mqtt:
  broker:
    host: "localhost"
    port: 1883
    username: "iot_user"
    password: "iot_password"
    tls_enabled: false
  
  topics:
    subscribe:
      - "iot/+/+/+/+/+"  # Patrón estándar
      - "sensors/+/+/+"   # Patrón personalizado
    
    publish:
      - "iot/status/ingesta"
      - "iot/alarms/+"

storage:
  type: "postgresql"
  postgresql:
    host: "localhost"
    port: 5432
    database: "iot_middleware"
    username: "iot_user"
    password: "iot_password"

ingesta:
  max_queue_size: 1000
  batch_size: 100
  max_workers: 4
  validation_enabled: true
```

### Configuración de Tópicos

#### Patrón Estándar
```
iot/{proyecto_id}/{unidad_id}/{dispositivo_id}/{canal_id}
```

#### Patrones Personalizados
```yaml
topic_mapping:
  "^sensors/(?P<tipo>[^/]+)/(?P<ubicacion>[^/]+)/(?P<id>[^/]+)$":
    proyecto_id: "sensors_project"
    unidad_id: "tipo"
    dispositivo_id: "ubicacion"
    canal_id: "id"
```

### Configuración de Umbrales de Alarma
```yaml
alarm_thresholds:
  "canal_temperatura_001":
    - tipo: "max"
      valor: 80
      severidad: "ADVERTENCIA"
      mensaje: "Temperatura alta detectada"
    
    - tipo: "min"
      valor: 0
      severidad: "CRITICO"
      mensaje: "Temperatura crítica baja"
```

## Uso

### Ejecución del Servicio
```bash
# Ejecución directa
python -m iot_middleware.services.ingestor config_ingesta.yaml

# Con logging detallado
python -m iot_middleware.services.ingestor config_ingesta.yaml --log-level DEBUG

# Como servicio del sistema
sudo systemctl start iot-ingesta
```

### Ejecución con Docker/Podman
```bash
# Construir imagen
podman build -t iot-ingesta .

# Ejecutar contenedor
podman run -d \
  --name iot-ingesta \
  -v ./config:/app/config \
  -v ./logs:/app/logs \
  iot-ingesta
```

### Scripts de Prueba
```bash
# Ejecutar ejemplos
python examples/ingesta_example.py

# Simular publicación de mensajes
python examples/mqtt_publisher_test.py comprehensive 300

# Probar tipos específicos
python examples/mqtt_publisher_test.py temperature 60
```

## API y Monitoreo

### Endpoints de Estado
```bash
# Estado del servicio
curl http://localhost:8080/health

# Métricas en tiempo real
curl http://localhost:8080/metrics

# Estado de conexión MQTT
curl http://localhost:8080/mqtt/status
```

### Logs y Debugging
```bash
# Ver logs en tiempo real
tail -f logs/ingesta_service.log

# Filtrar por nivel
grep "ERROR" logs/ingesta_service.log

# Buscar mensajes específicos
grep "canal_temperatura" logs/ingesta_service.log
```

## Desarrollo y Testing

### Estructura del Proyecto
```
src/iot_middleware/services/
├── ingestor.py              # Servicio principal
├── __init__.py
└── tests/                   # Tests unitarios

examples/
├── config_ingesta.yaml      # Configuración de ejemplo
├── ingesta_example.py       # Ejemplos de uso
└── mqtt_publisher_test.py   # Simulador de mensajes
```

### Ejecutar Tests
```bash
# Tests unitarios
python -m pytest tests/services/test_ingestor.py

# Tests de integración
python -m pytest tests/integration/test_ingesta_mqtt.py

# Cobertura de código
python -m pytest --cov=iot_middleware.services.ingestor
```

### Desarrollo Local
```bash
# Instalar en modo desarrollo
pip install -e .

# Ejecutar con hot reload
python -m watchdog.watchmedo auto-restart \
  --pattern="*.py" \
  --recursive \
  --directory="src/" \
  -- python -m iot_middleware.services.ingestor
```

## Monitoreo y Alertas

### Métricas Clave (KPIs)
- **Throughput**: Mensajes por segundo
- **Latencia**: Tiempo de procesamiento promedio
- **Tasa de error**: Porcentaje de mensajes fallidos
- **Utilización de cola**: Porcentaje de uso de la cola de mensajes
- **Uptime**: Tiempo de funcionamiento continuo

### Alertas Automáticas
- **Alta utilización de cola** (>80%)
- **Tasa de error elevada** (>5%)
- **Conexión MQTT perdida**
- **Errores de base de datos**
- **Memoria crítica** (>90%)

### Dashboards
- **Grafana**: Métricas en tiempo real
- **Prometheus**: Recopilación de métricas
- **Kibana**: Análisis de logs
- **Custom**: Dashboard personalizado

## Troubleshooting

### Problemas Comunes

#### Conexión MQTT Fallida
```bash
# Verificar broker
mosquitto_pub -h localhost -t test -m "hello"

# Verificar configuración
python -c "from iot_middleware.config import load_config; print(load_config())"
```

#### Errores de Base de Datos
```bash
# Verificar conexión PostgreSQL
psql -h localhost -U iot_user -d iot_middleware -c "SELECT 1"

# Verificar esquema
psql -h localhost -U iot_user -d iot_middleware -c "\dt iot_schema.*"
```

#### Cola de Mensajes Llena
```bash
# Ajustar configuración
ingesta:
  max_queue_size: 2000      # Aumentar tamaño
  max_workers: 8            # Más workers
  batch_timeout: 2.0        # Reducir timeout
```

### Logs de Debug
```bash
# Habilitar logging detallado
export LOG_LEVEL=DEBUG

# Ver logs de MQTT
grep "MQTT" logs/ingesta_service.log

# Ver logs de validación
grep "validation" logs/ingesta_service.log
```

## Escalabilidad

### Escalado Vertical
- **Aumentar workers**: `max_workers: 8`
- **Tamaño de cola**: `max_queue_size: 5000`
- **Pool de conexiones**: `pool_size: 20`

### Escalado Horizontal
- **Múltiples instancias** del servicio
- **Load balancer** para distribución de carga
- **Base de datos compartida** o replicada
- **Cola de mensajes distribuida** (Redis, RabbitMQ)

### Configuración de Producción
```yaml
ingesta:
  max_queue_size: 10000
  batch_size: 500
  max_workers: 16
  batch_timeout: 1.0
  
storage:
  postgresql:
    pool_size: 50
    max_overflow: 100
    pool_timeout: 10
```

## Seguridad

### Autenticación MQTT
- **Usuario/contraseña** para acceso básico
- **Certificados TLS** para conexiones seguras
- **ACLs** para control de acceso por tópico

### Seguridad de Base de Datos
- **Conexiones encriptadas** (SSL/TLS)
- **Usuarios con permisos mínimos**
- **Auditoría de accesos**

### Validación de Datos
- **Sanitización** de payloads
- **Validación de esquemas** estricta
- **Rate limiting** por dispositivo

## Contribución

### Guías de Desarrollo
1. **Fork** del repositorio
2. **Crear branch** para feature: `git checkout -b feature/nueva-funcionalidad`
3. **Commit** cambios: `git commit -am 'Agregar nueva funcionalidad'`
4. **Push** al branch: `git push origin feature/nueva-funcionalidad`
5. **Crear Pull Request**

### Estándares de Código
- **PEP 8** para estilo de Python
- **Type hints** para todas las funciones
- **Docstrings** completos
- **Tests** para nueva funcionalidad
- **Logging** estructurado

### Reportar Issues
- **Bug reports** con pasos de reproducción
- **Feature requests** con casos de uso
- **Documentación** de mejoras
- **Ejemplos** de configuración

## Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

### Canales de Soporte
- **Issues de GitHub**: Para bugs y feature requests
- **Discussions**: Para preguntas y discusiones
- **Wiki**: Documentación adicional
- **Email**: soporte@iot-middleware.com

### Comunidad
- **Slack**: #iot-middleware
- **Discord**: Servidor oficial
- **Meetups**: Eventos locales
- **Conferencias**: Presentaciones técnicas

---

**Nota**: Este servicio es parte del ecosistema IoT Middleware. Para más información sobre otros componentes, consulta la [documentación principal](README.md).
