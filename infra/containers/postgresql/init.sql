-- Script de inicialización para IoT Middleware
-- Archivo: init.sql

-- Crear usuario específico para la aplicación (si no existe)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'iot_user') THEN
        CREATE USER iot_user WITH PASSWORD 'iot_password_2024';
    END IF;
END
$$;

-- La base de datos iot_middleware ya se crea automáticamente por la variable POSTGRES_DB

-- Otorgar privilegios al usuario
GRANT ALL PRIVILEGES ON DATABASE iot_middleware TO iot_user;

-- Crear esquema para la aplicación
CREATE SCHEMA IF NOT EXISTS iot_schema;

-- Otorgar privilegios en el esquema
GRANT ALL ON SCHEMA iot_schema TO iot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA iot_schema TO iot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA iot_schema TO iot_user;

-- Crear tabla de dispositivos IoT
CREATE TABLE IF NOT EXISTS iot_schema.devices (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255),
    type VARCHAR(100),
    location VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de sensores
CREATE TABLE IF NOT EXISTS iot_schema.sensors (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES iot_schema.devices(id) ON DELETE CASCADE,
    sensor_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255),
    type VARCHAR(100),
    unit VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de métricas (para datos históricos que no van a InfluxDB)
CREATE TABLE IF NOT EXISTS iot_schema.metrics (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER REFERENCES iot_schema.sensors(id) ON DELETE CASCADE,
    value NUMERIC(10, 4),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Crear tabla de configuraciones
CREATE TABLE IF NOT EXISTS iot_schema.configurations (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de eventos del sistema
CREATE TABLE IF NOT EXISTS iot_schema.system_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_devices_device_id ON iot_schema.devices(device_id);
CREATE INDEX IF NOT EXISTS idx_sensors_device_id ON iot_schema.sensors(device_id);
CREATE INDEX IF NOT EXISTS idx_sensors_sensor_id ON iot_schema.sensors(sensor_id);
CREATE INDEX IF NOT EXISTS idx_metrics_sensor_id ON iot_schema.metrics(sensor_id);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON iot_schema.metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_configurations_key ON iot_schema.configurations(key);
CREATE INDEX IF NOT EXISTS idx_system_events_timestamp ON iot_schema.system_events(created_at);

-- Insertar configuraciones por defecto
INSERT INTO iot_schema.configurations (key, value, description) VALUES
    ('mqtt_broker_host', 'mosquitto', 'Host del broker MQTT'),
    ('mqtt_broker_port', '1883', 'Puerto del broker MQTT'),
    ('influxdb_host', 'influxdb', 'Host de InfluxDB'),
    ('influxdb_port', '8086', 'Puerto de InfluxDB'),
    ('influxdb_token', 'dev-token', 'Token de autenticación de InfluxDB'),
    ('influxdb_org', 'my-org', 'Organización de InfluxDB'),
    ('influxdb_bucket', 'iot', 'Bucket de InfluxDB'),
    ('postgresql_host', 'postgresql', 'Host de PostgreSQL'),
    ('postgresql_port', '5432', 'Puerto de PostgreSQL'),
    ('postgresql_database', 'iot_middleware', 'Base de datos de PostgreSQL'),
    ('postgresql_user', 'iot_user', 'Usuario de PostgreSQL'),
    ('api_host', '0.0.0.0', 'Host de la API'),
    ('api_port', '8000', 'Puerto de la API'),
    ('log_level', 'INFO', 'Nivel de logging'),
    ('data_retention_days', '30', 'Días de retención de datos históricos')
ON CONFLICT (key) DO NOTHING;

-- Crear función para actualizar timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Crear triggers para actualizar timestamps
CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON iot_schema.devices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_configurations_updated_at BEFORE UPDATE ON iot_schema.configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Otorgar todos los privilegios al usuario
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA iot_schema TO iot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA iot_schema TO iot_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA iot_schema TO iot_user;

-- Comentarios sobre las tablas
COMMENT ON TABLE iot_schema.devices IS 'Dispositivos IoT registrados en el sistema';
COMMENT ON TABLE iot_schema.sensors IS 'Sensores asociados a dispositivos IoT';
COMMENT ON TABLE iot_schema.metrics IS 'Métricas históricas de sensores (backup de InfluxDB)';
COMMENT ON TABLE iot_schema.configurations IS 'Configuraciones del sistema IoT Middleware';
COMMENT ON TABLE iot_schema.system_events IS 'Eventos del sistema para auditoría y debugging';

-- Mostrar resumen de la inicialización
SELECT 'Base de datos iot_middleware inicializada correctamente' as status;
SELECT 'Usuario iot_user creado con privilegios completos' as user_status;
SELECT 'Esquema iot_schema creado con tablas básicas' as schema_status;
