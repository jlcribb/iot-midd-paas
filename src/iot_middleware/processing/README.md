# Módulo de Procesamiento - IoT Middleware

## 📋 Descripción

El módulo de procesamiento proporciona funcionalidades completas para el procesamiento y normalización de datos IoT recibidos por MQTT. Incluye validación de esquemas, normalización automática de unidades, y preparación de datos para inserción en base de datos.

## 🚀 Características Principales

- ✅ **Validación de Esquemas**: Validación robusta según esquemas definidos en config.yaml
- 🔄 **Normalización Automática**: Conversión automática de unidades (Fahrenheit a Celsius, etc.)
- ⏰ **Timestamp Automático**: Agregado automático de timestamp si no está presente
- 🎯 **Detección Inteligente**: Detección automática del tipo de mensaje y esquema
- 🔧 **Niveles de Validación**: Múltiples niveles (STRICT, NORMAL, LENIENT)
- 📊 **Metadatos de Procesamiento**: Información completa del procesamiento
- 🛡️ **Manejo de Errores**: Manejo robusto de errores y mensajes inválidos
- 📈 **Estadísticas**: Monitoreo completo del procesamiento

## 🏗️ Arquitectura

### Clases Principales

#### `DataProcessor`
Procesador principal que coordina la validación, normalización y preparación de datos:

- **Validación**: Valida mensajes contra esquemas predefinidos
- **Normalización**: Aplica normalizadores específicos por tipo de dato
- **Metadatos**: Agrega información de procesamiento
- **Estadísticas**: Mantiene estadísticas de procesamiento

#### `DataNormalizer`
Normalizador de datos que convierte unidades y aplica límites:

- **Temperatura**: Fahrenheit/Kelvin → Celsius
- **Humedad**: Decimal/PPM → Porcentaje
- **Presión**: Pa/Bar/Atm → hPa
- **Límites**: Aplica límites de configuración

#### `MessageSchema`
Define la estructura y validación de mensajes:

- **Campos**: Lista de campos con tipos y restricciones
- **Validación**: Reglas de validación por campo
- **Requeridos/Opcionales**: Clasificación automática de campos

#### `FieldSchema`
Define la validación de un campo individual:

- **Tipo de Dato**: STRING, INTEGER, FLOAT, BOOLEAN, TIMESTAMP, JSON, ARRAY
- **Restricciones**: Valores mínimos/máximos, patrones regex, valores permitidos
- **Valores por Defecto**: Valores por defecto para campos opcionales

## 📖 Uso Básico

### 1. Función Simple process_message
```python
from iot_middleware.processing import process_message

# Mensaje simple
message = {
    "device_id": "sensor_001",
    "sensor_type": "temperature",
    "value": 75.2,
    "unit": "fahrenheit"
}

# Procesar mensaje
result = process_message(message)
print(f"Temperatura normalizada: {result['value']} {result['unit']}")
```

### 2. Procesador Avanzado
```python
from iot_middleware.processing import create_data_processor
from iot_middleware.config import load_config

# Cargar configuración
config = load_config()

# Crear procesador
processor = create_data_processor(config.processing, config.normalizers)

# Procesar mensaje
result = processor.process_message(message, validation_level=ValidationLevel.NORMAL)
```

## 🔧 Configuración

### Estructura de Configuración
```yaml
processing:
  batch_size: 100
  max_workers: 4
  timeout: 30
  retry_attempts: 3
  retry_delay: 5

normalizers:
  temperature:
    unit: "celsius"
    min_value: -50
    max_value: 100
  humidity:
    unit: "percentage"
    min_value: 0
    max_value: 100
  pressure:
    unit: "hpa"
    min_value: 800
    max_value: 1200
```

## 🧪 Pruebas

### Ejecutar Pruebas
```bash
# Desde el directorio raíz
python3 scripts/test_data_processor.py

# O desde el directorio containers
python3 ../scripts/test_data_processor.py
```

## 📚 Ejemplos de Uso

### Ejecutar Ejemplos
```bash
# Desde el directorio raíz
python3 examples/data_processing_example.py

# O desde el directorio containers
python3 ../examples/data_processing_example.py
```

## 🔄 Niveles de Validación

### ValidationLevel.STRICT
- Rechaza mensajes que no cumplan exactamente el esquema
- Lanza excepciones para errores de validación
- Ideal para entornos de producción críticos

### ValidationLevel.NORMAL
- Normaliza y corrige cuando es posible
- Usa valores por defecto para campos opcionales
- Balance entre robustez y flexibilidad

### ValidationLevel.LENIENT
- Acepta casi cualquier mensaje
- Solo normaliza datos básicos
- Ideal para desarrollo y testing

## 📊 Esquemas Predefinidos

### sensor_data
Para datos de sensores IoT:
- **device_id**: ID del dispositivo (requerido)
- **sensor_type**: Tipo de sensor (requerido)
- **value**: Valor del sensor (requerido)
- **unit**: Unidad de medida (opcional)
- **timestamp**: Timestamp de la medición (opcional)

### device_status
Para estado de dispositivos:
- **device_id**: ID del dispositivo (requerido)
- **status**: Estado del dispositivo (requerido)
- **timestamp**: Timestamp del estado (opcional)

### alert
Para alertas del sistema:
- **alert_type**: Tipo de alerta (requerido)
- **device_id**: ID del dispositivo (requerido)
- **severity**: Severidad de la alerta (requerido)
- **message**: Mensaje de la alerta (requerido)

## 🔄 Normalización de Datos

### Temperatura
- **Fahrenheit → Celsius**: `(°F - 32) × 5/9`
- **Kelvin → Celsius**: `K - 273.15`
- **Límites**: Aplica límites de configuración
- **Precisión**: Redondea a 2 decimales

### Humedad
- **Decimal → Porcentaje**: `× 100`
- **PPM → Porcentaje**: `÷ 10000`
- **Límites**: Aplica límites de configuración
- **Precisión**: Redondea a 1 decimal

### Presión
- **Pa → hPa**: `÷ 100`
- **Bar → hPa**: `× 1000`
- **Atm → hPa**: `× 1013.25`
- **Límites**: Aplica límites de configuración
- **Precisión**: Redondea a 1 decimal

## 📈 Metadatos de Procesamiento

### Información Automática
- **processing_timestamp**: Timestamp del procesamiento
- **schema_used**: Esquema utilizado
- **schema_version**: Versión del esquema
- **processing_version**: Versión del procesador
- **timestamp_added**: Si se agregó timestamp automáticamente

### Información de Normalización
- **original_value**: Valor original antes de normalización
- **original_unit**: Unidad original
- **normalized**: Si se aplicó normalización
- **error**: Información de error si falló la normalización

## 🚨 Manejo de Errores

### Respuesta de Error
```python
{
    "error": True,
    "error_message": "Descripción del error",
    "original_payload": {...},
    "processing_timestamp": "2025-08-14T00:00:00Z",
    "timestamp": "2025-08-14T00:00:00Z"
}
```

## 📊 Estadísticas de Procesamiento

### Métricas Disponibles
- **messages_processed**: Total de mensajes procesados
- **messages_validated**: Mensajes validados exitosamente
- **messages_normalized**: Mensajes normalizados exitosamente
- **errors**: Número de errores encontrados
- **last_processed**: Timestamp del último procesamiento

## 🎯 Casos de Uso

### 1. Gateway IoT
```python
def process_sensor_data(payload):
    """Procesar datos de sensores IoT"""
    try:
        result = process_message(payload)
        
        if "error" in result and result["error"]:
            # Manejar error
            log_error(result['error_message'])
            return None
        
        # Datos normalizados listos para base de datos
        return result
        
    except Exception as e:
        log_error(f"Error inesperado: {e}")
        return None
```

### 2. Sistema de Monitoreo
```python
def monitor_data_quality(payload):
    """Monitorear calidad de datos"""
    processor = create_data_processor(config.processing, config.normalizers)
    
    # Procesar con validación estricta
    result = processor.process_message(
        payload, 
        validation_level=ValidationLevel.STRICT
    )
    
    # Analizar calidad
    if result.get('normalized'):
        print(f"Datos normalizados: {result['value']} {result['unit']}")
    
    return result
```

## 🔧 Personalización

### Esquemas Personalizados
```python
# Crear esquema para sensores de calidad del aire
air_quality_schema = MessageSchema(
    name="air_quality",
    description="Datos de calidad del aire",
    fields=[
        FieldSchema("device_id", DataType.STRING, required=True),
        FieldSchema("pm25", DataType.FLOAT, required=True, min_value=0, max_value=500),
        FieldSchema("pm10", DataType.FLOAT, required=True, min_value=0, max_value=1000),
        FieldSchema("co2", DataType.FLOAT, required=False, min_value=300, max_value=5000),
        FieldSchema("timestamp", DataType.TIMESTAMP, required=False)
    ]
)

# Agregar al procesador
processor.add_custom_schema("air_quality", air_quality_schema)
```

## 📚 Dependencias

- **iot_middleware.config**: Sistema de configuración
- **json**: Manejo de payloads JSON
- **datetime**: Manejo de timestamps
- **logging**: Sistema de logging integrado
- **re**: Validación de patrones regex
- **decimal**: Precisión numérica

## 🤝 Contribución

Para contribuir al módulo de procesamiento:

1. Mantener compatibilidad con versiones anteriores
2. Agregar pruebas para nuevas funcionalidades
3. Documentar cambios en este README
4. Seguir las convenciones de código existentes

## 📞 Soporte

Para problemas o preguntas:

1. Revisar este README
2. Ejecutar las pruebas incluidas
3. Verificar la configuración
4. Revisar los logs de procesamiento

## 🚀 Próximos Pasos

### Funcionalidades Planificadas
- [ ] Soporte para más tipos de datos
- [ ] Normalizadores personalizables
- [ ] Validación de esquemas dinámicos
- [ ] Cache de esquemas para rendimiento
- [ ] Métricas de rendimiento avanzadas

### Integración
- [ ] Con el módulo MQTT
- [ ] Con el sistema de almacenamiento
- [ ] Con la API REST
- [ ] Con el sistema de alertas

---

**Nota**: Este módulo está diseñado para ser robusto y fácil de usar en entornos de producción. Si encuentras algún problema, por favor reporta el issue con detalles del error y tu configuración.
