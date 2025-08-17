# Módulo de Almacenamiento - IoT Middleware

## 📋 Descripción

El módulo de almacenamiento proporciona funcionalidades completas para la persistencia de datos IoT en diferentes tipos de bases de datos. Soporta PostgreSQL para datos relacionales e InfluxDB para series temporales, con manejo robusto de conexiones, reconexión automática y funciones de inserción optimizadas.

## 🚀 Características Principales

- ✅ **Soporte Multi-Base de Datos**: PostgreSQL e InfluxDB
- 🔄 **Reconexión Automática**: Manejo robusto de fallos de conexión
- 📊 **Métricas en Tiempo Real**: Monitoreo completo de operaciones
- 🏥 **Health Checks**: Verificación de salud de las bases de datos
- 🛡️ **Manejo de Errores**: Gestión robusta de errores y excepciones
- ⚡ **Pool de Conexiones**: Configuración optimizada de conexiones
- 🔧 **Configuración Flexible**: Soporte para configuración híbrida
- 📝 **Logging Detallado**: Registro completo de operaciones

## 🏗️ Arquitectura

### Clases Principales

#### `DatabaseHandler`
Manejador principal que coordina múltiples bases de datos:

- **Detección Automática**: Determina qué bases de datos usar según configuración
- **Enrutamiento Inteligente**: Dirige datos a las bases de datos apropiadas
- **Health Monitoring**: Monitoreo de salud de todas las conexiones
- **Métricas Consolidadas**: Estadísticas unificadas de todas las operaciones

#### `PostgreSQLHandler`
Manejador específico para PostgreSQL usando SQLAlchemy:

- **Pool de Conexiones**: Gestión eficiente de conexiones
- **Creación Automática de Tablas**: Estructura de base de datos automática
- **Reconexión en Background**: Recuperación automática de conexiones perdidas
- **Transacciones Seguras**: Manejo seguro de operaciones de base de datos

#### `InfluxDBHandler`
Manejador específico para InfluxDB:

- **Cliente Optimizado**: Uso eficiente del cliente oficial de InfluxDB
- **Puntos de Datos**: Estructuración automática de datos para series temporales
- **Tags y Campos**: Organización inteligente de metadatos
- **Health Checks**: Verificación de salud del servidor InfluxDB

## 📖 Uso Básico

### 1. Función Simple insert_sensor_data
```python
from iot_middleware.storage import insert_sensor_data

# Datos del sensor
sensor_data = {
    "topic": "iot/sensor_001/temperature",
    "device_id": "sensor_001",
    "sensor_type": "temperature",
    "value": 24.5,
    "unit": "celsius",
    "timestamp": "2025-08-14T00:00:00Z"
}

# Insertar datos
success = insert_sensor_data(sensor_data)
if success:
    print("✅ Datos insertados exitosamente")
```

### 2. Manejador Avanzado
```python
from iot_middleware.storage import create_database_handler
from iot_middleware.config import load_config

# Cargar configuración
config = load_config()

# Crear manejador
handler = create_database_handler(
    config.postgresql,
    config.influxdb,
    config.storage
)

# Insertar datos
success = handler.insert_sensor_data(sensor_data)

# Verificar estado de conexiones
status = handler.get_connection_status()
print(f"Estado: {status}")

# Health check
health = handler.health_check()
print(f"Salud: {health['status']}")

# Cerrar conexiones
handler.close()
```

## 🔧 Configuración

### Estructura de Configuración
```yaml
# PostgreSQL
postgresql:
  host: "localhost"
  port: 5432
  database: "iot_middleware"
  username: "iot_user"
  password: "iot_password"
  db_schema: "iot_schema"
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
  pool_recycle: 3600

# InfluxDB
influxdb:
  url: "http://localhost:8086"
  token: "dev-token"
  org: "my-org"
  bucket: "iot"
  retention_policy: "30d"
  batch_size: 1000
  flush_interval: 10

# Almacenamiento
storage:
  timeseries:
    provider: "influxdb"
    retention_days: 30
  
  relational:
    provider: "postgresql"
    backup_enabled: true
  
  metadata:
    provider: "postgresql"
    cache_enabled: true
```

## 🗄️ Tipos de Base de Datos

### DatabaseType.POSTGRESQL
- **Uso**: Datos relacionales, metadatos, configuración
- **Ventajas**: ACID, consultas complejas, integridad referencial
- **Casos de Uso**: Dispositivos, sensores, usuarios, configuración

### DatabaseType.INFLUXDB
- **Uso**: Series temporales, métricas, datos de sensores
- **Ventajas**: Optimizado para tiempo, compresión eficiente, consultas de agregación
- **Casos de Uso**: Lecturas de sensores, métricas de sistema, monitoreo

### DatabaseType.HYBRID
- **Uso**: Combinación de ambas bases de datos
- **Ventajas**: Mejor de ambos mundos, flexibilidad total
- **Casos de Uso**: Sistemas complejos con diferentes tipos de datos

## 📊 Estructura de Tablas

### Tabla sensor_data (PostgreSQL)
```sql
CREATE TABLE iot_schema.sensor_data (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    device_id VARCHAR(100),
    sensor_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Índices Optimizados
```sql
-- Índice por timestamp para consultas temporales
CREATE INDEX idx_sensor_data_timestamp ON iot_schema.sensor_data (timestamp);

-- Índice por device_id para consultas por dispositivo
CREATE INDEX idx_sensor_data_device_id ON iot_schema.sensor_data (device_id);

-- Índice por sensor_type para consultas por tipo
CREATE INDEX idx_sensor_data_sensor_type ON iot_schema.sensor_data (sensor_type);
```

### Estructura de Puntos (InfluxDB)
```python
# Punto de ejemplo
Point("sensor_data")
    .tag("device_id", "sensor_001")
    .tag("sensor_type", "temperature")
    .tag("topic", "iot/sensor_001/temperature")
    .field("value", 24.5)
    .field("unit", "celsius")
    .time(timestamp)
```

## 🧪 Pruebas

### Ejecutar Pruebas
```bash
# Desde el directorio raíz
python3 scripts/test_db_handler.py

# O desde el directorio containers
python3 ../scripts/test_db_handler.py
```

### Ejecutar Ejemplos
```bash
# Desde el directorio raíz
python3 examples/database_usage_example.py

# O desde el directorio containers
python3 ../examples/database_usage_example.py
```

## 📈 Métricas y Monitoreo

### Métricas Disponibles
```python
# Obtener métricas
metrics = handler.get_metrics()

# Para cada base de datos:
{
    "total_operations": 150,
    "successful_operations": 148,
    "failed_operations": 2,
    "last_operation": "2025-08-14T00:00:00Z",
    "connection_attempts": 1,
    "last_connection": "2025-08-14T00:00:00Z",
    "uptime_seconds": 3600
}
```

### Health Check
```python
# Verificar salud
health = handler.health_check()

# Resultado:
{
    "status": "healthy",  # healthy, degraded, unhealthy
    "timestamp": "2025-08-14T00:00:00Z",
    "databases": {
        "postgresql": {
            "status": "connected",
            "connected": True,
            "metrics": {...}
        },
        "influxdb": {
            "status": "connected",
            "connected": True,
            "metrics": {...}
        }
    }
}
```

## 🔄 Reconexión Automática

### Mecanismo de Reconexión
```python
# PostgreSQL: Reconexión en background
if connection_status == ConnectionStatus.ERROR:
    # Iniciar thread de reconexión
    start_reconnect_monitor()
    
    # Reintentos automáticos cada 30 segundos
    while not stop_reconnect.is_set():
        if reconnect():
            break
        time.sleep(30)
```

### Estados de Conexión
- **DISCONNECTED**: Sin conexión activa
- **CONNECTING**: Intentando conectar
- **CONNECTED**: Conexión establecida
- **ERROR**: Error de conexión
- **RECONNECTING**: Intentando reconectar

## 🛡️ Manejo de Errores

### Tipos de Errores Manejados
- **Errores de Conexión**: Timeouts, conexiones perdidas
- **Errores de Autenticación**: Credenciales inválidas
- **Errores de Base de Datos**: Restricciones, sintaxis SQL
- **Errores de Red**: Problemas de conectividad

### Estrategias de Recuperación
```python
try:
    success = handler.insert_sensor_data(data)
except ConnectionError:
    # Marcar como error de conexión
    handler.connection_status = ConnectionStatus.ERROR
    
    # Iniciar reconexión automática
    handler.start_reconnect_monitor()
    
    # Retornar fallo para manejo en nivel superior
    return False
```

## 📚 Ejemplos de Uso

### 1. Inserción de Datos de Sensor
```python
def store_sensor_reading(device_id, sensor_type, value, unit):
    """Almacenar lectura de sensor"""
    sensor_data = {
        "topic": f"iot/{device_id}/{sensor_type}",
        "device_id": device_id,
        "sensor_type": sensor_type,
        "value": value,
        "unit": unit,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return handler.insert_sensor_data(sensor_data)
```

### 2. Monitoreo de Salud
```python
def monitor_database_health():
    """Monitorear salud de las bases de datos"""
    health = handler.health_check()
    
    if health['status'] == 'unhealthy':
        # Alertar al sistema de monitoreo
        send_alert("Bases de datos no saludables")
    
    return health
```

### 3. Inserción en Lote
```python
def store_batch_data(sensor_readings):
    """Almacenar múltiples lecturas de sensores"""
    successful_inserts = 0
    
    for reading in sensor_readings:
        if handler.insert_sensor_data(reading):
            successful_inserts += 1
    
    return successful_inserts, len(sensor_readings)
```

## 🔧 Personalización

### Esquemas Personalizados
```python
# Crear esquema personalizado en PostgreSQL
def create_custom_schema(handler, schema_name):
    with handler.postgresql_handler.get_session() as session:
        session.execute(text(f"""
            CREATE SCHEMA IF NOT EXISTS {schema_name};
            
            CREATE TABLE IF NOT EXISTS {schema_name}.custom_data (
                id SERIAL PRIMARY KEY,
                data JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
```

### Normalizadores Personalizados
```python
# Normalizar datos antes de inserción
def normalize_sensor_data(raw_data):
    """Normalizar datos de sensor antes de almacenar"""
    normalized = {
        "topic": raw_data.get("topic", "unknown"),
        "device_id": raw_data.get("device_id", "unknown"),
        "sensor_type": raw_data.get("sensor_type", "unknown"),
        "value": float(raw_data.get("value", 0)),
        "timestamp": raw_data.get("timestamp") or datetime.now(timezone.utc).isoformat()
    }
    
    return normalized
```

## 📚 Dependencias

### PostgreSQL
```bash
pip install sqlalchemy psycopg2-binary
```

### InfluxDB
```bash
pip install influxdb-client
```

### Opcionales
```bash
pip install asyncpg  # Para PostgreSQL asíncrono
pip install aioinflux  # Para InfluxDB asíncrono
```

## 🤝 Contribución

Para contribuir al módulo de almacenamiento:

1. Mantener compatibilidad con versiones anteriores
2. Agregar pruebas para nuevas funcionalidades
3. Documentar cambios en este README
4. Seguir las convenciones de código existentes
5. Probar con diferentes versiones de bases de datos

## 📞 Soporte

Para problemas o preguntas:

1. Revisar este README
2. Ejecutar las pruebas incluidas
3. Verificar la configuración de conexión
4. Revisar los logs de conexión
5. Verificar que las bases de datos estén ejecutándose

## 🚀 Próximos Pasos

### Funcionalidades Planificadas
- [ ] Soporte para bases de datos NoSQL adicionales (MongoDB, Cassandra)
- [ ] Modo asíncrono para mejor rendimiento
- [ ] Cache de consultas para PostgreSQL
- [ ] Compresión automática de datos en InfluxDB
- [ ] Backup automático de datos
- [ ] Migración de esquemas

### Integración
- [ ] Con el módulo MQTT para inserción automática
- [ ] Con el procesador de datos para validación
- [ ] Con la API REST para consultas
- [ ] Con el sistema de alertas para monitoreo

---

**Nota**: Este módulo está diseñado para ser robusto y fácil de usar en entornos de producción. Si encuentras algún problema, por favor reporta el issue con detalles del error y tu configuración.
