"""
Procesador y Normalizador de Datos - IoT Middleware
==================================================

Este módulo implementa el procesamiento y normalización de mensajes MQTT
recibidos, incluyendo validación de esquemas, normalización de datos
y preparación para inserción en base de datos.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from decimal import Decimal, InvalidOperation

# Importar configuración
try:
    from ..config import ProcessingConfig, NormalizerConfig
except ImportError:
    # Fallback para importación directa
    from iot_middleware.config import ProcessingConfig, NormalizerConfig

# Configurar logging
logger = logging.getLogger(__name__)


class DataType(Enum):
    """Tipos de datos soportados"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    JSON = "json"
    ARRAY = "array"


class ValidationLevel(Enum):
    """Niveles de validación"""
    STRICT = "strict"      # Rechaza mensajes que no cumplan exactamente
    NORMAL = "normal"      # Normaliza y corrige cuando es posible
    LENIENT = "lenient"    # Acepta casi cualquier cosa, solo normaliza básico


@dataclass
class FieldSchema:
    """Esquema de un campo de datos"""
    name: str
    data_type: DataType
    required: bool = True
    default: Any = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None  # Regex pattern para strings
    allowed_values: Optional[List[Any]] = None
    description: str = ""
    
    def validate(self, value: Any) -> Tuple[bool, Any, Optional[str]]:
        """
        Validar un valor según el esquema
        
        Returns:
            (is_valid, normalized_value, error_message)
        """
        # Si el campo no es requerido y el valor es None, usar default
        if not self.required and value is None:
            return True, self.default, None
        
        # Si el campo es requerido y el valor es None, error
        if self.required and value is None:
            return False, None, f"Campo '{self.name}' es requerido"
        
        try:
            # Convertir y validar según el tipo
            normalized_value = self._normalize_value(value)
            
            # Validaciones adicionales
            if not self._validate_constraints(normalized_value):
                return False, None, f"Valor '{normalized_value}' no cumple las restricciones del campo '{self.name}'"
            
            return True, normalized_value, None
            
        except Exception as e:
            return False, None, f"Error validando campo '{self.name}': {str(e)}"
    
    def _normalize_value(self, value: Any) -> Any:
        """Normalizar valor según el tipo de datos"""
        if self.data_type == DataType.STRING:
            return str(value) if value is not None else ""
        
        elif self.data_type == DataType.INTEGER:
            if isinstance(value, str):
                # Intentar convertir string a entero
                return int(float(value))  # Usar float primero para manejar "23.0"
            elif isinstance(value, (int, float)):
                return int(value)
            else:
                raise ValueError(f"No se puede convertir '{value}' a entero")
        
        elif self.data_type == DataType.FLOAT:
            if isinstance(value, str):
                return float(value)
            elif isinstance(value, (int, float)):
                return float(value)
            else:
                raise ValueError(f"No se puede convertir '{value}' a float")
        
        elif self.data_type == DataType.BOOLEAN:
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                lower_val = value.lower()
                if lower_val in ('true', '1', 'yes', 'on'):
                    return True
                elif lower_val in ('false', '0', 'no', 'off'):
                    return False
                else:
                    raise ValueError(f"No se puede convertir '{value}' a booleano")
            elif isinstance(value, (int, float)):
                return bool(value)
            else:
                raise ValueError(f"No se puede convertir '{value}' a booleano")
        
        elif self.data_type == DataType.TIMESTAMP:
            if isinstance(value, datetime):
                return value
            elif isinstance(value, str):
                # Intentar parsear diferentes formatos de timestamp
                return self._parse_timestamp(value)
            elif isinstance(value, (int, float)):
                # Asumir timestamp Unix
                return datetime.fromtimestamp(value, tz=timezone.utc)
            else:
                raise ValueError(f"No se puede convertir '{value}' a timestamp")
        
        elif self.data_type == DataType.JSON:
            if isinstance(value, dict):
                return value
            elif isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    raise ValueError(f"String '{value}' no es JSON válido")
            else:
                raise ValueError(f"No se puede convertir '{value}' a JSON")
        
        elif self.data_type == DataType.ARRAY:
            if isinstance(value, list):
                return value
            elif isinstance(value, str):
                # Intentar parsear como JSON array
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return parsed
                    else:
                        raise ValueError(f"JSON '{value}' no es un array")
                except json.JSONDecodeError:
                    # Intentar split por comas
                    return [item.strip() for item in value.split(',') if item.strip()]
            else:
                raise ValueError(f"No se puede convertir '{value}' a array")
        
        else:
            return value
    
    def _parse_timestamp(self, value: str) -> datetime:
        """Parsear diferentes formatos de timestamp"""
        # Lista de formatos comunes
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f",      # ISO con microsegundos
            "%Y-%m-%dT%H:%M:%S",          # ISO sin microsegundos
            "%Y-%m-%d %H:%M:%S.%f",      # Formato estándar con microsegundos
            "%Y-%m-%d %H:%M:%S",          # Formato estándar
            "%Y-%m-%d",                   # Solo fecha
            "%d/%m/%Y %H:%M:%S",          # Formato europeo
            "%m/%d/%Y %H:%M:%S",          # Formato americano
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        
        # Si ningún formato funciona, intentar parse automático
        try:
            from dateutil import parser
            return parser.parse(value).replace(tzinfo=timezone.utc)
        except ImportError:
            pass
        
        raise ValueError(f"No se pudo parsear timestamp: {value}")
    
    def _validate_constraints(self, value: Any) -> bool:
        """Validar restricciones del campo"""
        # Validar rango numérico
        if self.data_type in (DataType.INTEGER, DataType.FLOAT):
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        
        # Validar patrón regex
        if self.pattern and isinstance(value, str):
            if not re.match(self.pattern, value):
                return False
        
        # Validar valores permitidos
        if self.allowed_values is not None:
            if value not in self.allowed_values:
                return False
        
        return True


@dataclass
class MessageSchema:
    """Esquema completo de un mensaje"""
    name: str
    fields: List[FieldSchema]
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    description: str = ""
    
    def __post_init__(self):
        """Inicializar campos requeridos y opcionales"""
        if not self.required_fields and not self.optional_fields:
            self.required_fields = [field.name for field in self.fields if field.required]
            self.optional_fields = [field.name for field in self.fields if not field.required]


class DataNormalizer:
    """Normalizador de datos según configuración"""
    
    def __init__(self, config: NormalizerConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def normalize_temperature(self, value: Any, unit: str = "celsius") -> Dict[str, Any]:
        """Normalizar datos de temperatura"""
        try:
            # Convertir a float
            temp_value = float(value)
            
            # Normalizar a Celsius
            if unit.lower() in ("fahrenheit", "f"):
                temp_value = (temp_value - 32) * 5/9
                unit = "celsius"
            elif unit.lower() in ("kelvin", "k"):
                temp_value = temp_value - 273.15
                unit = "celsius"
            
            # Aplicar límites de configuración
            temp_config = self.config.temperature
            if temp_config.get('min_value') is not None and temp_value < temp_config['min_value']:
                temp_value = temp_config['min_value']
                self.logger.warning(f"Temperatura {value} está por debajo del mínimo, normalizada a {temp_value}")
            
            if temp_config.get('max_value') is not None and temp_value > temp_config['max_value']:
                temp_value = temp_config['max_value']
                self.logger.warning(f"Temperatura {value} está por encima del máximo, normalizada a {temp_value}")
            
            return {
                "value": round(temp_value, 2),
                "unit": "celsius",
                "original_value": value,
                "original_unit": unit,
                "normalized": True
            }
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error normalizando temperatura {value}: {e}")
            return {
                "value": None,
                "unit": "celsius",
                "error": str(e),
                "normalized": False
            }
    
    def normalize_humidity(self, value: Any, unit: str = "percentage") -> Dict[str, Any]:
        """Normalizar datos de humedad"""
        try:
            # Convertir a float
            hum_value = float(value)
            
            # Normalizar a porcentaje
            if unit.lower() in ("decimal", "ratio"):
                hum_value = hum_value * 100
                unit = "percentage"
            elif unit.lower() in ("ppm", "parts_per_million"):
                hum_value = hum_value / 10000
                unit = "percentage"
            
            # Aplicar límites
            hum_config = self.config.humidity
            if hum_config.get('min_value') is not None and hum_value < hum_config['min_value']:
                hum_value = hum_config['min_value']
            
            if hum_config.get('max_value') is not None and hum_value > hum_config['max_value']:
                hum_value = hum_config['max_value']
            
            return {
                "value": round(hum_value, 1),
                "unit": "percentage",
                "original_value": value,
                "original_unit": unit,
                "normalized": True
            }
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error normalizando humedad {value}: {e}")
            return {
                "value": None,
                "unit": "percentage",
                "error": str(e),
                "normalized": False
            }
    
    def normalize_pressure(self, value: Any, unit: str = "hpa") -> Dict[str, Any]:
        """Normalizar datos de presión"""
        try:
            # Convertir a float
            press_value = float(value)
            
            # Normalizar a hPa
            if unit.lower() in ("pa", "pascal"):
                press_value = press_value / 100
                unit = "hpa"
            elif unit.lower() in ("kpa", "kilopascal"):
                press_value = press_value * 10
                unit = "hpa"
            elif unit.lower() in ("bar"):
                press_value = press_value * 1000
                unit = "hpa"
            elif unit.lower() in ("atm", "atmosphere"):
                press_value = press_value * 1013.25
                unit = "hpa"
            
            # Aplicar límites
            press_config = self.config.pressure
            if press_config.get('min_value') is not None and press_value < press_config['min_value']:
                press_value = press_config['min_value']
            
            if press_config.get('max_value') is not None and press_value > press_config['max_value']:
                press_value = press_config['max_value']
            
            return {
                "value": round(press_value, 1),
                "unit": "hpa",
                "original_value": value,
                "original_unit": unit,
                "normalized": True
            }
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error normalizando presión {value}: {e}")
            return {
                "value": None,
                "unit": "hpa",
                "error": str(e),
                "normalized": False
            }


class DataProcessor:
    """Procesador principal de datos IoT"""
    
    def __init__(self, processing_config: ProcessingConfig, normalizer_config: NormalizerConfig):
        self.config = processing_config
        self.normalizer = DataNormalizer(normalizer_config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Esquemas predefinidos para tipos comunes de mensajes
        self.schemas = self._create_default_schemas()
        
        # Estadísticas de procesamiento
        self.stats = {
            "messages_processed": 0,
            "messages_validated": 0,
            "messages_normalized": 0,
            "errors": 0,
            "last_processed": None
        }
    
    def _create_default_schemas(self) -> Dict[str, MessageSchema]:
        """Crear esquemas por defecto para tipos comunes de mensajes"""
        schemas = {}
        
        # Esquema para datos de sensor
        sensor_data_schema = MessageSchema(
            name="sensor_data",
            description="Datos de sensores IoT",
            fields=[
                FieldSchema("device_id", DataType.STRING, required=True, description="ID del dispositivo"),
                FieldSchema("sensor_type", DataType.STRING, required=True, description="Tipo de sensor"),
                FieldSchema("value", DataType.FLOAT, required=True, description="Valor del sensor"),
                FieldSchema("unit", DataType.STRING, required=False, default="", description="Unidad de medida"),
                FieldSchema("timestamp", DataType.TIMESTAMP, required=False, description="Timestamp de la medición"),
                FieldSchema("location", DataType.STRING, required=False, description="Ubicación del sensor"),
                FieldSchema("battery", DataType.FLOAT, required=False, min_value=0, max_value=100, description="Nivel de batería"),
                FieldSchema("signal_strength", DataType.FLOAT, required=False, min_value=-100, max_value=0, description="Fuerza de señal"),
                FieldSchema("metadata", DataType.JSON, required=False, description="Metadatos adicionales")
            ]
        )
        schemas["sensor_data"] = sensor_data_schema
        
        # Esquema para estado del dispositivo
        device_status_schema = MessageSchema(
            name="device_status",
            description="Estado de dispositivos IoT",
            fields=[
                FieldSchema("device_id", DataType.STRING, required=True, description="ID del dispositivo"),
                FieldSchema("status", DataType.STRING, required=True, allowed_values=["online", "offline", "error", "maintenance"], description="Estado del dispositivo"),
                FieldSchema("timestamp", DataType.TIMESTAMP, required=False, description="Timestamp del estado"),
                FieldSchema("battery", DataType.FLOAT, required=False, min_value=0, max_value=100, description="Nivel de batería"),
                FieldSchema("temperature", DataType.FLOAT, required=False, min_value=-50, max_value=100, description="Temperatura del dispositivo"),
                FieldSchema("uptime", DataType.INTEGER, required=False, min_value=0, description="Tiempo de actividad en segundos"),
                FieldSchema("error_code", DataType.STRING, required=False, description="Código de error si aplica"),
                FieldSchema("metadata", DataType.JSON, required=False, description="Metadatos adicionales")
            ]
        )
        schemas["device_status"] = device_status_schema
        
        # Esquema para alertas
        alert_schema = MessageSchema(
            name="alert",
            description="Alertas del sistema IoT",
            fields=[
                FieldSchema("alert_type", DataType.STRING, required=True, description="Tipo de alerta"),
                FieldSchema("device_id", DataType.STRING, required=True, description="ID del dispositivo"),
                FieldSchema("severity", DataType.STRING, required=True, allowed_values=["info", "warning", "error", "critical"], description="Severidad de la alerta"),
                FieldSchema("message", DataType.STRING, required=True, description="Mensaje de la alerta"),
                FieldSchema("timestamp", DataType.TIMESTAMP, required=False, description="Timestamp de la alerta"),
                FieldSchema("value", DataType.FLOAT, required=False, description="Valor que disparó la alerta"),
                FieldSchema("threshold", DataType.FLOAT, required=False, description="Umbral de la alerta"),
                FieldSchema("metadata", DataType.JSON, required=False, description="Metadatos adicionales")
            ]
        )
        schemas["alert"] = alert_schema
        
        return schemas
    
    def process_message(self, payload: Dict[str, Any], schema_name: Optional[str] = None, 
                       validation_level: ValidationLevel = ValidationLevel.NORMAL) -> Dict[str, Any]:
        """
        Procesar y normalizar un mensaje MQTT
        
        Args:
            payload: Datos del mensaje a procesar
            schema_name: Nombre del esquema a usar (opcional)
            validation_level: Nivel de validación a aplicar
        
        Returns:
            Diccionario normalizado listo para inserción en base de datos
        """
        try:
            self.stats["messages_processed"] += 1
            self.stats["last_processed"] = datetime.now()
            
            self.logger.info(f"Procesando mensaje #{self.stats['messages_processed']}")
            
            # Determinar esquema a usar
            schema = self._determine_schema(payload, schema_name)
            if not schema:
                raise ValueError(f"No se pudo determinar el esquema para el mensaje")
            
            # Validar y normalizar según el esquema
            validated_data = self._validate_against_schema(payload, schema, validation_level)
            
            # Normalizar datos específicos
            normalized_data = self._normalize_specific_fields(validated_data)
            
            # Agregar metadatos de procesamiento
            final_data = self._add_processing_metadata(normalized_data, schema)
            
            self.stats["messages_validated"] += 1
            self.stats["messages_normalized"] += 1
            
            self.logger.info(f"Mensaje procesado exitosamente usando esquema '{schema.name}'")
            return final_data
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Error procesando mensaje: {e}")
            
            # Retornar datos de error según el nivel de validación
            if validation_level == ValidationLevel.STRICT:
                raise
            else:
                return self._create_error_response(payload, str(e))
    
    def _determine_schema(self, payload: Dict[str, Any], schema_name: Optional[str] = None) -> Optional[MessageSchema]:
        """Determinar qué esquema usar para el mensaje"""
        # Si se especifica un esquema, usarlo
        if schema_name and schema_name in self.schemas:
            return self.schemas[schema_name]
        
        # Intentar determinar automáticamente basado en el contenido
        if "sensor_type" in payload and "value" in payload:
            return self.schemas.get("sensor_data")
        elif "status" in payload and "device_id" in payload:
            return self.schemas.get("device_status")
        elif "alert_type" in payload and "severity" in payload:
            return self.schemas.get("alert")
        
        # Si no se puede determinar, usar el esquema más genérico
        return self.schemas.get("sensor_data")
    
    def _validate_against_schema(self, payload: Dict[str, Any], schema: MessageSchema, 
                                validation_level: ValidationLevel) -> Dict[str, Any]:
        """Validar payload contra el esquema especificado"""
        validated_data = {}
        errors = []
        
        # Procesar cada campo del esquema
        for field_schema in schema.fields:
            field_name = field_schema.name
            field_value = payload.get(field_name)
            
            # Validar campo
            is_valid, normalized_value, error_msg = field_schema.validate(field_value)
            
            if is_valid:
                validated_data[field_name] = normalized_value
            else:
                if validation_level == ValidationLevel.STRICT:
                    errors.append(f"Campo '{field_name}': {error_msg}")
                elif validation_level == ValidationLevel.NORMAL:
                    # Usar valor por defecto si está disponible
                    if field_schema.default is not None:
                        validated_data[field_name] = field_schema.default
                        self.logger.warning(f"Campo '{field_name}' inválido, usando valor por defecto: {field_schema.default}")
                    else:
                        errors.append(f"Campo '{field_name}': {error_msg}")
                else:  # LENIENT
                    # Intentar usar el valor original o un valor por defecto
                    validated_data[field_name] = field_value if field_value is not None else field_schema.default
                    if error_msg:
                        self.logger.warning(f"Campo '{field_name}' con advertencia: {error_msg}")
        
        # Agregar campos adicionales del payload que no están en el esquema
        if validation_level != ValidationLevel.STRICT:
            for key, value in payload.items():
                if key not in validated_data:
                    validated_data[key] = value
        
        # Si hay errores críticos, lanzar excepción
        if errors and validation_level == ValidationLevel.STRICT:
            raise ValueError(f"Errores de validación: {'; '.join(errors)}")
        
        return validated_data
    
    def _normalize_specific_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizar campos específicos según su tipo"""
        normalized_data = data.copy()
        
        # Normalizar temperatura
        if "sensor_type" in data and data["sensor_type"] == "temperature" and "value" in data:
            unit = data.get("unit", "celsius")
            normalized_temp = self.normalizer.normalize_temperature(data["value"], unit)
            if normalized_temp["normalized"]:
                normalized_data.update(normalized_temp)
        
        # Normalizar humedad
        elif "sensor_type" in data and data["sensor_type"] == "humidity" and "value" in data:
            unit = data.get("unit", "percentage")
            normalized_hum = self.normalizer.normalize_humidity(data["value"], unit)
            if normalized_hum["normalized"]:
                normalized_data.update(normalized_hum)
        
        # Normalizar presión
        elif "sensor_type" in data and data["sensor_type"] == "pressure" and "value" in data:
            unit = data.get("unit", "hpa")
            normalized_press = self.normalizer.normalize_pressure(data["value"], unit)
            if normalized_press["normalized"]:
                normalized_data.update(normalized_press)
        
        return normalized_data
    
    def _add_processing_metadata(self, data: Dict[str, Any], schema: MessageSchema) -> Dict[str, Any]:
        """Agregar metadatos de procesamiento"""
        metadata = {
            "processing_timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_used": schema.name,
            "schema_version": "1.0",
            "processing_version": "1.0"
        }
        
        # Agregar timestamp si no existe
        if "timestamp" not in data or data["timestamp"] is None:
            data["timestamp"] = datetime.now(timezone.utc).isoformat()
            metadata["timestamp_added"] = True
        
        # Agregar metadatos al mensaje
        if "metadata" in data and isinstance(data["metadata"], dict):
            data["metadata"].update(metadata)
        else:
            data["metadata"] = metadata
        
        return data
    
    def _create_error_response(self, original_payload: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """Crear respuesta de error para mensajes que fallaron"""
        return {
            "error": True,
            "error_message": error_message,
            "original_payload": original_payload,
            "processing_timestamp": datetime.now(timezone.utc).isoformat(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def add_custom_schema(self, name: str, schema: MessageSchema):
        """Agregar un esquema personalizado"""
        self.schemas[name] = schema
        self.logger.info(f"Esquema personalizado '{name}' agregado")
    
    def get_schema(self, name: str) -> Optional[MessageSchema]:
        """Obtener un esquema por nombre"""
        return self.schemas.get(name)
    
    def list_schemas(self) -> List[str]:
        """Listar todos los esquemas disponibles"""
        return list(self.schemas.keys())
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de procesamiento"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reiniciar estadísticas de procesamiento"""
        self.stats = {
            "messages_processed": 0,
            "messages_validated": 0,
            "messages_normalized": 0,
            "errors": 0,
            "last_processed": None
        }
        self.logger.info("Estadísticas de procesamiento reiniciadas")

# Función de conveniencia para crear procesador
def create_data_processor(processing_config: ProcessingConfig, normalizer_config: NormalizerConfig) -> DataProcessor:
    """
    Crear una instancia del procesador de datos
    
    Args:
        processing_config: Configuración de procesamiento
        normalizer_config: Configuración de normalizadores
    
    Returns:
        Instancia del procesador de datos
    """
    return DataProcessor(processing_config, normalizer_config)


# Función principal process_message para compatibilidad
def process_message(payload: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Función principal para procesar mensajes (compatibilidad con código existente)
    
    Args:
        payload: Datos del mensaje a procesar
        **kwargs: Argumentos adicionales (schema_name, validation_level, etc.)
    
    Returns:
        Diccionario normalizado listo para inserción en base de datos
    """
    # Crear configuración por defecto si no se proporciona
    try:
        from ..config import ProcessingConfig, NormalizerConfig
    except ImportError:
        # Fallback para importación directa
        from iot_middleware.config import ProcessingConfig, NormalizerConfig
    
    default_processing_config = ProcessingConfig()
    default_normalizer_config = NormalizerConfig()
    
    # Crear procesador
    processor = create_data_processor(default_processing_config, default_normalizer_config)
    
    # Procesar mensaje
    return processor.process_message(payload, **kwargs)


# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Crear configuración por defecto
        from iot_middleware.config import ProcessingConfig, NormalizerConfig
        
        processing_config = ProcessingConfig()
        normalizer_config = NormalizerConfig()
        
        # Crear procesador
        processor = create_data_processor(processing_config, normalizer_config)
        
        # Mensaje de ejemplo
        test_message = {
            "device_id": "sensor_001",
            "sensor_type": "temperature",
            "value": 75.2,
            "unit": "fahrenheit",
            "location": "sala_principal"
        }
        
        print("🧪 Probando procesamiento de mensaje...")
        print(f"📨 Mensaje original: {test_message}")
        
        # Procesar mensaje
        result = processor.process_message(test_message)
        
        print(f"✅ Mensaje procesado:")
        print(f"   📊 Resultado: {json.dumps(result, indent=2, default=str)}")
        
        # Mostrar estadísticas
        stats = processor.get_processing_stats()
        print(f"\n📈 Estadísticas de procesamiento:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
