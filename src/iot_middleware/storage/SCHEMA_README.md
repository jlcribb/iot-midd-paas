# Estructura de Datos PostgreSQL - IoT Middleware

## 📋 Descripción General

Esta documentación describe la estructura completa de base de datos PostgreSQL implementada para el sistema IoT Middleware. La estructura está diseñada para manejar de manera eficiente y escalable todos los aspectos de un sistema IoT empresarial.

## 🏗️ Arquitectura de la Base de Datos

### Esquema Principal
- **Nombre del esquema**: `iot_schema`
- **Extensiones requeridas**: `uuid-ossp`, `pgcrypto`
- **Extensiones opcionales**: `postgis` (para geo-localización)

### Características Principales
- ✅ **Normalización completa**: Estructura relacional optimizada
- 🔄 **Auditoría automática**: Tracking de todos los cambios
- 📊 **Particionamiento temporal**: Para registros de datos históricos
- 🗺️ **Geo-localización**: Coordenadas GPS para unidades y dispositivos
- 🔐 **Seguridad avanzada**: RLS (Row Level Security) y encriptación
- 📈 **Performance optimizada**: Índices estratégicos y vistas materializadas

## 🗄️ Entidades Principales

### 1. CLIENTES (`iot_schema.clientes`)
**Propósito**: Organizaciones o personas que utilizan el sistema

**Campos principales**:
- `id`: UUID único del cliente
- `nombre`: Nombre de la organización
- `sector` / `industria`: Clasificación del cliente
- `contacto_principal`: JSONB con información del contacto principal
- `contactos_adicionales`: Array JSONB de contactos secundarios
- `direccion`: JSONB con información de ubicación
- `configuracion`: Configuraciones específicas del cliente

**Ejemplo de uso**:
```sql
INSERT INTO iot_schema.clientes (nombre, sector, contacto_principal)
VALUES (
    'Industrias Tecnológicas S.A.',
    'Tecnología',
    '{"nombre": "Ana Martínez", "email": "ana@indutech.com", "telefono": "+34 91 123 4567"}'
);
```

### 2. PROYECTOS (`iot_schema.proyectos`)
**Propósito**: Proyectos asociados a clientes

**Campos principales**:
- `id`: UUID único del proyecto
- `cliente_id`: Referencia al cliente
- `nombre` / `descripcion`: Información del proyecto
- `estado`: Enum ('planificado', 'activo', 'pausado', 'cerrado', 'cancelado')
- `fecha_inicio` / `fecha_fin`: Cronograma del proyecto
- `presupuesto` / `prioridad`: Información de gestión
- `configuracion`: Configuraciones específicas del proyecto

**Relaciones**:
- Pertenece a un **CLIENTE**
- Tiene múltiples **UNIDADES_PROYECTO**
- Tiene múltiples **DISPOSITIVOS_PROYECTO**

### 3. UNIDADES_PROYECTO (`iot_schema.unidades_proyecto`)
**Propósito**: Subdivisiones físicas y lógicas de proyectos

**Campos principales**:
- `id`: UUID único de la unidad
- `proyecto_id`: Referencia al proyecto
- `nombre` / `descripcion`: Información de la unidad
- `ubicacion`: Descripción textual de la ubicación
- `responsable`: Persona responsable de la unidad
- `lat` / `lon`: Coordenadas GPS (opcional)
- `configuracion`: Configuraciones específicas de la unidad

**Casos de uso**:
- Edificios, pisos, salas
- Áreas geográficas
- Divisiones organizacionales

### 4. DISPOSITIVOS (`iot_schema.dispositivos`)
**Propósito**: Catálogo de dispositivos IoT

**Campos principales**:
- `id`: UUID único del dispositivo
- `tipo`: Categoría del dispositivo (sensor, actuador, gateway, etc.)
- `fabricante` / `modelo`: Información del fabricante
- `identificador_unico`: MAC, Serial, UUID del equipo
- `protocolo`: Protocolo de comunicación (MQTT, BLE, HTTP, RF, etc.)
- `vida_util_meses`: Tiempo estimado de vida útil
- `especificaciones_tecnicas`: JSONB con datasheet completo
- `configuracion_protocolo`: Configuraciones específicas del protocolo

**Tipos de dispositivos soportados**:
- **Sensores**: Temperatura, humedad, presión, etc.
- **Actuadores**: Relés, motores, válvulas, etc.
- **Gateways**: Raspberry Pi, ESP32, etc.
- **Dispositivos de campo**: PLCs, RTUs, etc.

### 5. DISPOSITIVOS_PROYECTO (`iot_schema.dispositivos_proyecto`)
**Propósito**: Asignación de dispositivos a proyectos específicos

**Campos principales**:
- `id`: UUID único de la asignación
- `proyecto_id`: Referencia al proyecto
- `dispositivo_id`: Referencia al dispositivo
- `unidad_id`: Referencia a la unidad (opcional)
- `nombre_personalizado`: Nombre específico en el proyecto
- `fecha_instalacion` / `fecha_retiro`: Ciclo de vida del dispositivo
- `estado`: Estado actual del dispositivo
- `ubicacion_fisica`: Ubicación específica dentro de la unidad
- `responsable`: Persona responsable del dispositivo

**Ventajas**:
- Un dispositivo puede estar en múltiples proyectos
- Gestión independiente del ciclo de vida por proyecto
- Trazabilidad completa de ubicaciones

### 6. CANALES (`iot_schema.canales`)
**Propósito**: Sensores o canales de datos de dispositivos

**Campos principales**:
- `id`: UUID único del canal
- `dispositivo_id`: Referencia al dispositivo
- `nombre` / `etiqueta`: Identificación del canal
- `unidad_medida`: Unidad de medida (°C, %RH, hPa, etc.)
- `tipo`: Tipo de dato ('int', 'float', 'bool', 'string', 'json', 'binary', 'timestamp')
- `rango_min` / `rango_max`: Rango esperado de valores
- `precision_valor`: Número de decimales
- `frecuencia_muestreo`: Frecuencia en segundos
- `umbral_alto` / `umbral_bajo`: Umbrales para alarmas
- `metadatos`: JSONB con información adicional (topic MQTT, QoS, etc.)

**Ejemplo de canal de temperatura**:
```sql
INSERT INTO iot_schema.canales (
    dispositivo_id, nombre, etiqueta, unidad_medida, tipo,
    rango_min, rango_max, frecuencia_muestreo
) VALUES (
    'uuid-dispositivo', 'temperature', 'Temperatura Ambiente', '°C', 'float',
    -40.0, 125.0, 60
);
```

### 7. REGISTROS_DATOS (`iot_schema.registros_datos`)
**Propósito**: Datos capturados por los canales (particionado por tiempo)

**Campos principales**:
- `id`: ID secuencial único
- `canal_id`: Referencia al canal
- `ts`: Timestamp de la medición
- `valor_num` / `valor_int` / `valor_bool` / `valor_text` / `valor_json`: Valor según tipo
- `calidad`: Calidad del dato (OK, GOOD, UNCERTAIN, BAD, etc.)
- `calidad_porcentaje`: Porcentaje de calidad (0-100)
- `metadata`: JSONB con información adicional (QoS, IP, RSSI, etc.)
- `procesado` / `validado`: Estados del procesamiento

**Particionamiento**:
- **Estrategia**: Particionamiento por rango de tiempo (mensual)
- **Ventajas**: Consultas históricas rápidas, mantenimiento eficiente
- **Ejemplo**: `registros_datos_2025_08` para agosto 2025

### 8. EVENTOS_ALARMAS (`iot_schema.eventos_alarmas`)
**Propósito**: Eventos y alarmas del sistema

**Campos principales**:
- `id`: UUID único del evento
- `proyecto_id`: Referencia al proyecto
- `canal_id` / `unidad_id` / `dispositivo_id`: Referencias opcionales
- `ts`: Timestamp del evento
- `severidad`: Nivel de severidad ('info', 'warning', 'error', 'critical', 'fatal')
- `titulo` / `descripcion`: Información del evento
- `detalles`: JSONB con valores que dispararon el evento
- `estado`: Estado del evento ('activa', 'reconocida', 'resuelta', 'cerrada')
- `reconocida_por` / `resuelta_por`: Usuarios que gestionan el evento

### 9. USUARIOS (`iot_schema.usuarios`)
**Propósito**: Cuentas de usuario del sistema

**Campos principales**:
- `id`: UUID único del usuario
- `email`: Email único del usuario
- `nombre` / `apellido`: Información personal
- `password_hash`: Hash de la contraseña (encriptada)
- `rol`: Rol del sistema ('admin', 'tecnico', 'cliente', 'lectura', 'supervisor')
- `activo`: Estado de la cuenta
- `configuracion`: JSONB con preferencias del usuario

### 10. USUARIOS_SCOPE (`iot_schema.usuarios_scope`)
**Propósito**: Alcance de usuarios en clientes/proyectos

**Campos principales**:
- `id`: UUID único del scope
- `usuario_id`: Referencia al usuario
- `cliente_id` / `proyecto_id`: Referencias opcionales
- `permisos`: JSONB con permisos específicos en este scope
- `activo`: Estado del scope

**Casos de uso**:
- Usuario con acceso solo a un cliente específico
- Usuario con acceso solo a un proyecto específico
- Usuario con acceso global a todos los clientes/proyectos

### 11. CONFIG_MIDDLEWARE (`iot_schema.config_middleware`)
**Propósito**: Configuraciones del middleware IoT

**Campos principales**:
- `id`: UUID único de la configuración
- `clave`: Clave de la configuración
- `valor`: JSONB con el valor de la configuración
- `descripcion`: Descripción de la configuración
- `categoria`: Agrupación de configuraciones
- `version`: Versión de la configuración
- `sensible`: Si la configuración contiene información sensible
- `vigente`: Si la configuración está activa

**Ejemplos de configuraciones**:
```json
{
  "frecuencias_muestreo": {
    "temperatura": 60,
    "humedad": 60,
    "presion": 300
  },
  "umbrales_alarmas": {
    "temperatura_alta": 30.0,
    "temperatura_baja": 15.0,
    "humedad_alta": 80.0
  }
}
```

### 12. AUDITORIA (`iot_schema.auditoria`)
**Propósito**: Registro de cambios para auditoría

**Campos principales**:
- `id`: ID secuencial único
- `usuario_id`: Usuario que realizó el cambio
- `entidad`: Nombre de la tabla modificada
- `entidad_id`: ID del registro modificado
- `accion`: Tipo de acción ('INSERT', 'UPDATE', 'DELETE')
- `cambios`: JSONB con diff de los cambios
- `ip_origen` / `user_agent`: Información del cliente
- `ts`: Timestamp del cambio

## 🔧 Funcionalidades Avanzadas

### Particionamiento Temporal
```sql
-- Crear partición mensual
SELECT iot_schema.crear_particion_mensual('2025-08-15');

-- Limpiar particiones antiguas (mantener 12 meses)
SELECT iot_schema.limpiar_particiones_antiguas(12);
```

### Vistas Útiles
- **`v_resumen_proyectos`**: Resumen completo de proyectos con estadísticas
- **`v_resumen_dispositivos`**: Resumen de dispositivos por proyecto y unidad

### Triggers de Auditoría
- **Auditoría automática**: Todos los cambios se registran automáticamente
- **Timestamps automáticos**: Campos `actualizado_en` se actualizan automáticamente

### Seguridad (RLS)
- **Configuraciones sensibles**: Solo admins pueden ver configuraciones marcadas como sensibles
- **Auditoría**: Solo admins pueden ver la tabla de auditoría completa

## 📊 Índices y Performance

### Índices Principales
```sql
-- Índices básicos para consultas frecuentes
CREATE INDEX idx_proyectos_cliente ON iot_schema.proyectos(cliente_id);
CREATE INDEX idx_dispositivos_tipo ON iot_schema.dispositivos(tipo);
CREATE INDEX idx_canales_dispositivo ON iot_schema.canales(dispositivo_id);

-- Índices para registros de datos (particionados)
CREATE INDEX idx_reg_datos_canal_ts ON iot_schema.registros_datos(canal_id, ts);
CREATE INDEX idx_reg_datos_ts ON iot_schema.registros_datos(ts);

-- Índices JSONB para búsquedas avanzadas
CREATE INDEX idx_reg_metadata ON iot_schema.registros_datos USING GIN (metadata);
CREATE INDEX idx_canales_metadatos ON iot_schema.canales USING GIN (metadatos);
```

### Optimizaciones de Performance
- **Particionamiento**: Consultas históricas rápidas
- **Índices estratégicos**: Para consultas más frecuentes
- **Vistas materializadas**: Para reportes complejos
- **Pool de conexiones**: Configuración optimizada

## 🚀 Uso Práctico

### Aplicar el Esquema
```bash
# Aplicar esquema completo
python3 scripts/apply_schema.py

# Verificar creación
python3 examples/schema_usage_example.py
```

### Ejemplos de Consultas
```sql
-- Obtener datos de temperatura de las últimas 24 horas
SELECT 
    rd.ts,
    rd.valor_num,
    c.etiqueta,
    c.unidad_medida,
    d.identificador_unico
FROM iot_schema.registros_datos rd
JOIN iot_schema.canales c ON rd.canal_id = c.id
JOIN iot_schema.dispositivos d ON c.dispositivo_id = d.id
WHERE c.nombre = 'temperature'
  AND rd.ts >= NOW() - INTERVAL '24 hours'
ORDER BY rd.ts DESC;

-- Resumen de dispositivos por proyecto
SELECT 
    p.nombre as proyecto,
    COUNT(dp.id) as total_dispositivos,
    COUNT(CASE WHEN dp.estado = 'activo' THEN 1 END) as dispositivos_activos
FROM iot_schema.proyectos p
LEFT JOIN iot_schema.dispositivos_proyecto dp ON p.id = dp.proyecto_id
GROUP BY p.id, p.nombre;
```

## 🔮 Próximos Pasos

### Funcionalidades Planificadas
- [ ] **Migración automática**: Scripts para actualizar esquemas existentes
- [ ] **Backup automático**: Políticas de backup y recuperación
- [ ] **Monitoreo de performance**: Métricas de consultas y índices
- [ ] **Compresión de datos**: Para particiones históricas
- [ ] **Replicación**: Para alta disponibilidad

### Integración
- [ ] **Con MQTT**: Inserción automática de mensajes recibidos
- [ ] **Con procesamiento**: Validación y normalización de datos
- [ ] **Con API REST**: Endpoints para gestión de entidades
- [ ] **Con dashboards**: Vistas optimizadas para visualización

---

**Nota**: Esta estructura de datos está diseñada para ser escalable y mantenible. Para implementaciones en producción, se recomienda revisar y ajustar los índices según los patrones de consulta específicos de cada instalación.
