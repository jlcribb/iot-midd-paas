# 📊 Estructura de Bases de Datos - IoT Middleware

## 🗄️ PostgreSQL

### Esquema: `iot_schema`

El sistema utiliza PostgreSQL para almacenar datos relacionales, metadatos y configuraciones. Todas las tablas están en el esquema `iot_schema`.

### Tablas Principales

#### 1. **`clientes`** 
Organizaciones o personas que utilizan el sistema.

**Campos principales:**
- `id` (UUID) - Identificador único
- `nombre` (TEXT) - Nombre de la organización
- `sector`, `industria` (TEXT) - Clasificación
- `contacto_principal` (JSONB) - Información del contacto principal
- `contactos_adicionales` (JSONB) - Array de contactos secundarios
- `direccion` (JSONB) - Información de ubicación
- `configuracion` (JSONB) - Configuraciones específicas
- `activo` (BOOLEAN) - Estado activo/inactivo
- `creado_en`, `actualizado_en` (TIMESTAMPTZ) - Timestamps de auditoría

#### 2. **`proyectos`**
Proyectos asociados a clientes.

**Campos principales:**
- `id` (UUID) - Identificador único
- `cliente_id` (UUID) - Referencia a `clientes.id`
- `nombre` (TEXT) - Nombre del proyecto
- `descripcion` (TEXT) - Descripción del proyecto
- `estado` (estado_proyecto ENUM) - 'planificado', 'activo', 'pausado', 'cerrado', 'cancelado'
- `fecha_inicio`, `fecha_fin` (DATE) - Fechas del proyecto
- `presupuesto` (DECIMAL) - Presupuesto asignado
- `prioridad` (SMALLINT) - 1=baja, 2=media, 3=alta, 4=crítica
- `configuracion` (JSONB) - Configuraciones específicas
- `activo` (BOOLEAN) - Estado activo/inactivo

#### 3. **`unidades_proyecto`**
Subdivisiones físicas y lógicas de proyectos.

**Campos principales:**
- `id` (UUID) - Identificador único
- `proyecto_id` (UUID) - Referencia a `proyectos.id`
- `nombre` (TEXT) - Nombre de la unidad
- `descripcion` (TEXT) - Descripción
- `ubicacion` (TEXT) - Ubicación física
- `responsable`, `responsable_email`, `responsable_telefono` (TEXT)
- `lat`, `lon` (DOUBLE PRECISION) - Coordenadas GPS
- `configuracion` (JSONB) - Configuraciones específicas
- `activo` (BOOLEAN) - Estado activo/inactivo

#### 4. **`sesiones`**
Períodos de recolección de datos.

**Campos principales:**
- `id` (UUID) - Identificador único
- `unidad_id` (UUID) - Referencia a `unidades_proyecto.id`
- `nombre` (TEXT) - Nombre de la sesión
- `descripcion` (TEXT) - Descripción
- `inicio`, `fin` (TIMESTAMPTZ) - Rango temporal de la sesión
- `estado` (TEXT) - 'activa', 'pausada', 'finalizada', 'cancelada'
- `observaciones` (TEXT) - Notas adicionales
- `configuracion` (JSONB) - Configuraciones de la sesión
- `metadata` (JSONB) - Datos adicionales

#### 5. **`dispositivos`**
Catálogo de dispositivos IoT.

**Campos principales:**
- `id` (UUID) - Identificador único
- `tipo` (TEXT) - Tipo de dispositivo (sensor, actuador, gateway, etc.)
- `fabricante` (TEXT) - Fabricante del dispositivo
- `modelo` (TEXT) - Modelo del dispositivo
- `identificador_unico` (TEXT UNIQUE) - MAC/Serial/UUID del equipo
- `protocolo` (protocolo_comunicacion ENUM) - 'MQTT', 'BLE', 'HTTP', 'RF', 'LoRa', 'Modbus', 'OPC_UA', 'Otro'
- `vida_util_meses` (INTEGER) - Vida útil estimada
- `especificaciones_tecnicas` (JSONB) - Datasheets y especificaciones
- `configuracion_protocolo` (JSONB) - Configuraciones del protocolo
- `firmware_version`, `hardware_version` (TEXT)
- `certificaciones` (JSONB) - Lista de certificaciones
- `activo` (BOOLEAN) - Estado activo/inactivo

#### 6. **`dispositivos_proyecto`**
Asignación de dispositivos a proyectos específicos.

**Campos principales:**
- `id` (UUID) - Identificador único
- `proyecto_id` (UUID) - Referencia a `proyectos.id`
- `dispositivo_id` (UUID) - Referencia a `dispositivos.id`
- `unidad_id` (UUID) - Referencia a `unidades_proyecto.id` (opcional)
- `nombre_personalizado` (TEXT) - Nombre específico en el proyecto
- `descripcion` (TEXT) - Descripción
- `fecha_instalacion`, `fecha_retiro` (DATE) - Ciclo de vida
- `estado` (estado_dispositivo ENUM) - 'activo', 'inactivo', 'mantenimiento', 'error', 'desconectado'
- `configuracion` (JSONB) - Configuraciones específicas
- `ubicacion_fisica` (TEXT) - Ubicación dentro de la unidad
- `responsable`, `responsable_email`, `responsable_telefono` (TEXT)
- `metadata` (JSONB) - Datos adicionales
- **UNIQUE** (`proyecto_id`, `dispositivo_id`)

#### 7. **`canales`**
Sensores o canales de datos de dispositivos.

**Campos principales:**
- `id` (UUID) - Identificador único
- `dispositivo_id` (UUID) - Referencia a `dispositivos.id`
- `nombre` (TEXT) - Nombre del canal (ej. "temperatura")
- `etiqueta` (TEXT) - Label amigable
- `descripcion` (TEXT) - Descripción
- `unidad_medida` (TEXT) - Unidad (ej. "°C", "ppm", "pH")
- `tipo` (tipo_dato ENUM) - 'int', 'float', 'bool', 'string', 'json', 'binary', 'timestamp'
- `rango_min`, `rango_max` (DOUBLE PRECISION) - Rango esperado
- `precision_valor` (INTEGER) - Número de decimales
- `frecuencia_muestreo` (INTEGER) - Frecuencia en segundos
- `umbral_alto`, `umbral_bajo` (DOUBLE PRECISION) - Umbrales de alarma
- `metadatos` (JSONB) - Información adicional (topic MQTT, QoS, etc.)
- `configuracion` (JSONB) - Configuraciones específicas
- `activo` (BOOLEAN) - Estado activo/inactivo
- **UNIQUE** (`dispositivo_id`, `nombre`)

#### 8. **`registros_datos`** ⚠️ **PARTICIONADA**
Datos capturados por los canales. **Tabla particionada por tiempo (mensual)**.

**Campos principales:**
- `id` (BIGSERIAL) - ID secuencial
- `canal_id` (UUID) - Referencia a `canales.id`
- `ts` (TIMESTAMPTZ) - Timestamp de la medición
- `valor_num` (DOUBLE PRECISION) - Valor numérico (float)
- `valor_int` (BIGINT) - Valor entero
- `valor_bool` (BOOLEAN) - Valor booleano
- `valor_text` (TEXT) - Valor de texto
- `valor_json` (JSONB) - Valor JSON
- `calidad` (calidad_dato ENUM) - 'OK', 'GOOD', 'UNCERTAIN', 'BAD', 'SUSPECTO', 'MALO'
- `calidad_porcentaje` (INTEGER) - Porcentaje de calidad (0-100)
- `metadata` (JSONB) - Metadatos adicionales (qos, ip, device_status, rssi, etc.)
- `procesado` (BOOLEAN) - Si el dato ya fue procesado
- `validado` (BOOLEAN) - Si el dato pasó validación
- **PRIMARY KEY** (`id`, `ts`)
- **PARTITION BY RANGE (ts)** - Particiones mensuales automáticas

**Particiones:**
- Se crean automáticamente por mes (ej: `registros_datos_2025_01`, `registros_datos_2025_02`)
- Función: `iot_schema.crear_particion_mensual(fecha DATE)`
- Función de limpieza: `iot_schema.limpiar_particiones_antiguas(meses_retener INTEGER)`

#### 9. **`eventos_alarmas`**
Eventos y alarmas del sistema.

**Campos principales:**
- `id` (UUID) - Identificador único
- `proyecto_id` (UUID) - Referencia a `proyectos.id`
- `canal_id` (UUID) - Referencia a `canales.id` (opcional)
- `unidad_id` (UUID) - Referencia a `unidades_proyecto.id` (opcional)
- `dispositivo_id` (UUID) - Referencia a `dispositivos.id` (opcional)
- `ts` (TIMESTAMPTZ) - Timestamp del evento
- `severidad` (severidad_evento ENUM) - 'info', 'warning', 'error', 'critical', 'fatal'
- `codigo` (TEXT) - Código estándar/OPC UA (opcional)
- `titulo` (TEXT) - Título del evento
- `descripcion` (TEXT) - Descripción detallada
- `detalles` (JSONB) - Valores que dispararon el evento
- `estado` (TEXT) - 'activa', 'reconocida', 'resuelta', 'cerrada'
- `reconocida_por`, `reconocida_en` - Reconocimiento del evento
- `resuelta_por`, `resuelta_en` - Resolución del evento
- `comentarios` (TEXT) - Comentarios adicionales
- `metadata` (JSONB) - Datos adicionales

#### 10. **`usuarios`**
Usuarios del sistema con roles y permisos.

**Campos principales:**
- `id` (UUID) - Identificador único
- `email` (CITEXT UNIQUE) - Email del usuario (case-insensitive)
- `nombre`, `apellido` (TEXT) - Nombre completo
- `password_hash` (TEXT) - Hash de la contraseña
- `rol` (rol_sistema ENUM) - 'admin', 'tecnico', 'cliente', 'lectura', 'supervisor'
- `activo` (BOOLEAN) - Estado activo/inactivo
- `ultimo_login` (TIMESTAMPTZ) - Último inicio de sesión
- `configuracion` (JSONB) - Preferencias del usuario
- `metadata` (JSONB) - Datos adicionales

#### 11. **`usuarios_scope`**
Alcance de usuarios en clientes/proyectos (scoping).

**Campos principales:**
- `id` (UUID) - Identificador único
- `usuario_id` (UUID) - Referencia a `usuarios.id`
- `cliente_id` (UUID) - Referencia a `clientes.id` (opcional)
- `proyecto_id` (UUID) - Referencia a `proyectos.id` (opcional)
- `permisos` (JSONB) - Permisos específicos en este scope
- `activo` (BOOLEAN) - Estado activo/inactivo
- **UNIQUE** (`usuario_id`, `cliente_id`, `proyecto_id`)

#### 12. **`config_middleware`**
Configuraciones del middleware IoT (versionadas).

**Campos principales:**
- `id` (UUID) - Identificador único
- `clave` (TEXT) - Clave de la configuración
- `valor` (JSONB) - Valor de la configuración (frecuencias, umbrales, reglas)
- `descripcion` (TEXT) - Descripción
- `categoria` (TEXT) - Agrupación de configuraciones
- `version` (INTEGER) - Versión de la configuración
- `sensible` (BOOLEAN) - Si contiene información sensible (se cifra)
- `vigente` (BOOLEAN) - Si está vigente
- `activo` (BOOLEAN) - Estado activo/inactivo
- `creado_por`, `actualizado_por` (UUID) - Referencias a `usuarios.id`

#### 13. **`auditoria`**
Registro de cambios para auditoría.

**Campos principales:**
- `id` (BIGSERIAL) - ID secuencial
- `usuario_id` (UUID) - Referencia a `usuarios.id` (opcional)
- `entidad` (TEXT) - Nombre de la entidad (ej. 'config_middleware', 'eventos_alarmas', 'canales')
- `entidad_id` (UUID) - ID de la entidad afectada
- `accion` (TEXT) - 'INSERT', 'UPDATE', 'DELETE'
- `cambios` (JSONB) - Diff o snapshot: `{antes: {}, despues: {}}`
- `ip_origen` (INET) - IP de origen
- `user_agent` (TEXT) - User agent del cliente
- `contexto` (JSONB) - Información adicional del contexto
- `ts` (TIMESTAMPTZ) - Timestamp del cambio

### Tipos ENUM Personalizados

- **`estado_proyecto`**: 'planificado', 'activo', 'pausado', 'cerrado', 'cancelado'
- **`protocolo_comunicacion`**: 'MQTT', 'BLE', 'HTTP', 'RF', 'LoRa', 'Modbus', 'OPC_UA', 'Otro'
- **`tipo_dato`**: 'int', 'float', 'bool', 'string', 'json', 'binary', 'timestamp'
- **`rol_sistema`**: 'admin', 'tecnico', 'cliente', 'lectura', 'supervisor'
- **`calidad_dato`**: 'OK', 'GOOD', 'UNCERTAIN', 'BAD', 'SUSPECTO', 'MALO'
- **`severidad_evento`**: 'info', 'warning', 'error', 'critical', 'fatal'
- **`estado_dispositivo`**: 'activo', 'inactivo', 'mantenimiento', 'error', 'desconectado'

### Vistas Útiles

- **`v_resumen_proyectos`**: Resumen de proyectos con estadísticas
- **`v_resumen_dispositivos`**: Resumen de dispositivos con estadísticas

### Funciones y Triggers

- **`fn_auditar_cambios()`**: Función genérica de auditoría
- **`fn_actualizar_timestamp()`**: Actualización automática de timestamps
- **`crear_particion_mensual(fecha DATE)`**: Crear particiones mensuales para `registros_datos`
- **`limpiar_particiones_antiguas(meses_retener INTEGER)`**: Limpiar particiones antiguas

---

## 📈 InfluxDB

### Bucket Principal

**Nombre del bucket:** `iot` (configurable en `config.yaml`)

**Configuración:**
- **Retention Policy**: 30 días (configurable)
- **Organización**: `my-org` (configurable)
- **Token**: Requerido para autenticación

### Measurement (Tabla de Series Temporales)

#### **`sensor_data`**

Esta es la única measurement utilizada en InfluxDB. Almacena todos los datos de sensores como series temporales.

**Estructura de Puntos:**

```python
Point("sensor_data")
    .tag("device_id", "sensor_001")           # Tag: Identificador del dispositivo
    .tag("sensor_type", "temperature")        # Tag: Tipo de sensor
    .tag("topic", "iot/sensor_001/temperature") # Tag: Tópico MQTT
    .field("value", 24.5)                     # Field: Valor principal
    .field("unit", "celsius")                 # Field: Unidad de medida
    .time(timestamp)                          # Timestamp de la medición
```

**Tags (Índices para consultas):**
- `device_id` - Identificador único del dispositivo
- `sensor_type` - Tipo de sensor (temperature, humidity, pressure, etc.)
- `topic` - Tópico MQTT de origen

**Fields (Valores medidos):**
- `value` - Valor principal de la medición (obligatorio)
- `unit` - Unidad de medida (opcional)
- Cualquier otro campo adicional del `data_dict` que no esté en los tags

**Ejemplo de Datos:**

```
measurement: sensor_data
tags: {device_id: "sensor_001", sensor_type: "temperature", topic: "iot/sensor_001/temperature"}
fields: {value: 24.5, unit: "celsius"}
time: 2025-01-05T20:00:00Z
```

### Consultas Típicas

**Obtener últimos 10 valores de temperatura:**
```flux
from(bucket: "iot")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  |> filter(fn: (r) => r["sensor_type"] == "temperature")
  |> limit(n: 10)
```

**Promedio de temperatura por hora:**
```flux
from(bucket: "iot")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  |> filter(fn: (r) => r["sensor_type"] == "temperature")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
```

---

## 🔄 Resumen de Uso

### PostgreSQL (`iot_schema`)
- **Metadatos**: Clientes, Proyectos, Unidades, Dispositivos, Canales
- **Configuración**: Usuarios, Permisos, Configuraciones del middleware
- **Datos Relacionales**: Asignaciones, Sesiones, Eventos/Alarmas
- **Auditoría**: Registro completo de cambios
- **Datos Particionados**: `registros_datos` (particionada mensualmente)

### InfluxDB (`iot` bucket)
- **Series Temporales**: Todos los datos de sensores en `sensor_data`
- **Optimizado para**: Consultas temporales, agregaciones, métricas
- **Retención**: 30 días (configurable)

---

## 📝 Notas Importantes

1. **Particionamiento**: La tabla `registros_datos` está particionada mensualmente para optimizar el rendimiento en consultas históricas.

2. **Índices**: PostgreSQL tiene índices optimizados en campos clave (timestamps, foreign keys, campos JSONB con GIN).

3. **Seguridad**: RLS (Row Level Security) habilitado en tablas sensibles (`config_middleware`, `auditoria`).

4. **Auditoría Automática**: Triggers automáticos registran todos los cambios en tablas principales.

5. **Flexibilidad**: Campos JSONB permiten almacenar información adicional sin modificar el esquema.

6. **InfluxDB**: Solo almacena datos de series temporales. Todos los metadatos están en PostgreSQL.
