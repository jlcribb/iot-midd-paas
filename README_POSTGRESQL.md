# IoT Middleware con PostgreSQL - Guía de Configuración

## 📋 Resumen

Este documento describe la configuración y uso de PostgreSQL en el IoT Middleware, incluyendo la instalación, configuración y pruebas de conectividad.

## 🗄️ Arquitectura de Base de Datos

### Base de Datos Híbrida
El IoT Middleware utiliza un enfoque híbrido para el almacenamiento de datos:

- **InfluxDB**: Para datos de series temporales (métricas, lecturas de sensores)
- **PostgreSQL**: Para datos relacionales (dispositivos, sensores, configuraciones, metadatos)

### Ventajas del Enfoque Híbrido
- **InfluxDB**: Optimizado para datos de series temporales con alta velocidad de escritura
- **PostgreSQL**: Excelente para consultas complejas, relaciones y transacciones ACID
- **Flexibilidad**: Permite almacenar tanto datos estructurados como métricas en tiempo real

## 🚀 Instalación y Configuración

### 1. Archivo requirements.txt
```bash
# Framework y utilidades web
fastapi==0.116.1
uvicorn[standard]==0.35.0
pydantic==2.11.7
pydantic-settings==2.3.0

# Cliente MQTT
paho-mqtt==2.1.0

# Base de datos PostgreSQL
sqlalchemy==2.0.35
psycopg2-binary==2.9.9
alembic==1.14.1

# InfluxDB
influxdb-client==1.49.0

# Parser de configuración
PyYAML==6.0.2

# Utilidades y logging
python-dotenv==1.1.1
loguru==0.7.3
tenacity==9.1.2
orjson==3.11.2
```

### 2. Configuración de PostgreSQL
El contenedor PostgreSQL se configura automáticamente con:

- **Imagen**: `postgres:16-alpine`
- **Puerto**: 5432
- **Base de datos**: `iot_middleware`
- **Usuario**: `iot_user`
- **Contraseña**: `iot_password_2024`
- **Esquema**: `iot_schema`

### 3. Archivos de Configuración
- `containers/postgresql/postgresql.conf`: Configuración del servidor
- `containers/postgresql/init.sql`: Script de inicialización de la base de datos

## 🏗️ Estructura de la Base de Datos

### Esquema `iot_schema`

#### Tabla: `devices`
```sql
CREATE TABLE iot_schema.devices (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255),
    type VARCHAR(100),
    location VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### Tabla: `sensors`
```sql
CREATE TABLE iot_schema.sensors (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES iot_schema.devices(id) ON DELETE CASCADE,
    sensor_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255),
    type VARCHAR(100),
    unit VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### Tabla: `metrics`
```sql
CREATE TABLE iot_schema.metrics (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER REFERENCES iot_schema.sensors(id) ON DELETE CASCADE,
    value NUMERIC(10, 4),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);
```

#### Tabla: `configurations`
```sql
CREATE TABLE iot_schema.configurations (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### Tabla: `system_events`
```sql
CREATE TABLE iot_schema.system_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Configuración del Contenedor

### Variables de Entorno
```yaml
postgresql:
  host: "postgresql"
  port: 5432
  database: "iot_middleware"
  username: "iot_user"
  password: "iot_password_2024"
  schema: "iot_schema"
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
  pool_recycle: 3600
```

### Volúmenes
```yaml
volumes:
  - postgresql_data:/var/lib/postgresql/data:Z
  - ./postgresql/postgresql.conf:/etc/postgresql/postgresql.conf:Z
  - ./postgresql/init.sql:/docker-entrypoint-initdb.d/init.sql:Z
```

## 🧪 Pruebas de Conectividad

### 1. Script de Prueba
```bash
# Ejecutar desde el directorio containers
python3 ../scripts/test_postgresql_connection.py
```

### 2. Prueba Manual
```bash
# Conectar directamente a PostgreSQL
podman exec -it postgresql psql -U iot_user -d iot_middleware

# Listar esquemas
\dn

# Listar tablas del esquema iot_schema
\dt iot_schema.*

# Verificar configuraciones
SELECT * FROM iot_schema.configurations;
```

### 3. Verificación de Logs
```bash
# Ver logs de PostgreSQL
podman logs postgresql

# Ver logs en tiempo real
podman logs -f postgresql
```

## 📊 Monitoreo y Mantenimiento

### 1. Estado del Contenedor
```bash
# Verificar estado
podman ps postgresql

# Ver información detallada
podman inspect postgresql

# Ver estadísticas de uso
podman stats postgresql
```

### 2. Backup y Restauración
```bash
# Backup de la base de datos
podman exec postgresql pg_dump -U iot_user iot_middleware > backup.sql

# Restaurar desde backup
podman exec -i postgresql psql -U iot_user iot_middleware < backup.sql
```

### 3. Limpieza de Datos
```sql
-- Limpiar métricas antiguas (más de 30 días)
DELETE FROM iot_schema.metrics 
WHERE timestamp < NOW() - INTERVAL '30 days';

-- Limpiar eventos del sistema antiguos
DELETE FROM iot_schema.system_events 
WHERE created_at < NOW() - INTERVAL '7 days';
```

## 🔒 Seguridad

### 1. Usuarios y Permisos
- **Usuario de aplicación**: `iot_user` con privilegios limitados
- **Esquema aislado**: `iot_schema` para separar datos de la aplicación
- **Privilegios mínimos**: Solo acceso a las tablas necesarias

### 2. Configuración de Red
- **Puerto interno**: 5432 solo accesible desde la red de contenedores
- **Autenticación**: Contraseña segura para el usuario de aplicación
- **SSL**: Configurable según necesidades de producción

## 🚨 Solución de Problemas

### Error: "Connection refused"
```bash
# Verificar que el contenedor esté ejecutándose
podman ps postgresql

# Verificar logs
podman logs postgresql

# Reiniciar el contenedor
podman restart postgresql
```

### Error: "Authentication failed"
```bash
# Verificar credenciales en la configuración
# Verificar que el usuario exista en la base de datos
podman exec -it postgresql psql -U postgres -c "\du"
```

### Error: "Database does not exist"
```bash
# Verificar que el script de inicialización se ejecutó
podman logs postgresql | grep "database system is ready"

# Ejecutar script de inicialización manualmente
podman exec -i postgresql psql -U postgres < init.sql
```

## 📈 Rendimiento

### 1. Configuración de Memoria
```conf
# postgresql.conf
shared_buffers = 128MB
effective_cache_size = 512MB
work_mem = 4MB
maintenance_work_mem = 64MB
```

### 2. Índices Recomendados
```sql
-- Índices para consultas frecuentes
CREATE INDEX idx_metrics_timestamp ON iot_schema.metrics(timestamp);
CREATE INDEX idx_devices_device_id ON iot_schema.devices(device_id);
CREATE INDEX idx_sensors_sensor_id ON iot_schema.sensors(sensor_id);
```

### 3. Monitoreo de Rendimiento
```sql
-- Consultas lentas
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Uso de índices
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes;
```

## 🔄 Migraciones y Actualizaciones

### 1. Usando Alembic
```bash
# Instalar Alembic
pip install alembic

# Inicializar
alembic init alembic

# Crear migración
alembic revision --autogenerate -m "Add new table"

# Aplicar migración
alembic upgrade head
```

### 2. Scripts SQL Personalizados
```bash
# Ejecutar script de migración
podman exec -i postgresql psql -U iot_user -d iot_middleware < migration.sql
```

## 📚 Referencias

- [Documentación oficial de PostgreSQL](https://www.postgresql.org/docs/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [psycopg2 Driver](https://www.psycopg.org/docs/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)

## 🤝 Contribución

Para reportar problemas o sugerir mejoras:

1. Verificar que el problema no esté documentado aquí
2. Revisar logs del contenedor PostgreSQL
3. Probar conectividad con el script de prueba
4. Crear un issue con detalles del problema

---

**Nota**: Esta configuración está optimizada para desarrollo. Para producción, considera ajustar la configuración de seguridad, rendimiento y backup según tus necesidades específicas.
