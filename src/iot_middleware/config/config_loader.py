"""
Módulo de Carga de Configuración - IoT Middleware
==================================================

Este módulo se encarga de cargar y validar la configuración del sistema
desde archivos YAML, incluyendo validación de esquemas y valores requeridos.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
try:
    from pydantic import BaseModel, Field, field_validator, ValidationError, ConfigDict
except ImportError:
    # Fallback para versiones anteriores de Pydantic
    from pydantic import BaseModel, Field, field_validator, ValidationError, ConfigDict
import logging

# Configurar logging
logger = logging.getLogger(__name__)


class MQTTConfig(BaseModel):
    """Configuración del broker MQTT"""
    broker: Dict[str, Any] = Field(..., description="Configuración del broker MQTT")
    topics: Dict[str, List[str]] = Field(..., description="Configuración de tópicos")
    qos: int = Field(default=1, ge=0, le=2, description="Calidad de servicio MQTT")
    retain: bool = Field(default=False, description="Retener mensajes MQTT")
    
    @field_validator('broker')
    @classmethod
    def validate_broker(cls, v):
        required_keys = ['host', 'port']
        missing_keys = [key for key in required_keys if key not in v]
        if missing_keys:
            raise ValueError(f"Configuración MQTT incompleta. Faltan: {missing_keys}")
        
        # Validar puerto
        if not isinstance(v.get('port'), int) or v['port'] <= 0:
            raise ValueError("El puerto MQTT debe ser un número entero positivo")
        
        # Validar host
        if not v.get('host'):
            raise ValueError("El host MQTT no puede estar vacío")
        
        return v
    
    @field_validator('topics')
    @classmethod
    def validate_topics(cls, v):
        required_keys = ['subscribe', 'publish']
        missing_keys = [key for key in required_keys if key not in v]
        if missing_keys:
            raise ValueError(f"Configuración de tópicos incompleta. Faltan: {missing_keys}")
        
        # Validar que los tópicos sean listas
        for key, topics in v.items():
            if not isinstance(topics, list):
                raise ValueError(f"Los tópicos {key} deben ser una lista")
            if not topics:
                raise ValueError(f"La lista de tópicos {key} no puede estar vacía")
        
        return v


class InfluxDBConfig(BaseModel):
    """Configuración de InfluxDB"""
    url: str = Field(..., description="URL de conexión a InfluxDB")
    token: str = Field(..., description="Token de autenticación")
    org: str = Field(..., description="Organización de InfluxDB")
    bucket: str = Field(..., description="Bucket de datos")
    retention_policy: str = Field(default="30d", description="Política de retención")
    batch_size: int = Field(default=1000, ge=1, description="Tamaño del lote")
    flush_interval: int = Field(default=10, ge=1, description="Intervalo de flush en segundos")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("La URL de InfluxDB debe comenzar con http:// o https://")
        return v
    
    @field_validator('token')
    @classmethod
    def validate_token(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("El token de InfluxDB no puede estar vacío")
        return v


class PostgreSQLConfig(BaseModel):
    """Configuración de PostgreSQL"""
    host: str = Field(..., description="Host de PostgreSQL")
    port: int = Field(..., ge=1, le=65535, description="Puerto de PostgreSQL")
    database: str = Field(..., description="Nombre de la base de datos")
    username: str = Field(..., description="Usuario de la base de datos")
    password: str = Field(..., description="Contraseña de la base de datos")
    db_schema: str = Field(default="iot_schema", description="Esquema de la base de datos")
    pool_size: int = Field(default=10, ge=1, description="Tamaño del pool de conexiones")
    max_overflow: int = Field(default=20, ge=0, description="Máximo overflow del pool")
    pool_timeout: int = Field(default=30, ge=1, description="Timeout del pool en segundos")
    pool_recycle: int = Field(default=3600, ge=1, description="Reciclaje del pool en segundos")
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("El host de PostgreSQL no puede estar vacío")
        return v
    
    @field_validator('database', 'username', 'password')
    @classmethod
    def validate_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Los campos database, username y password no pueden estar vacíos")
        return v


class APIConfig(BaseModel):
    """Configuración de la API"""
    host: str = Field(default="0.0.0.0", description="Host de la API")
    port: int = Field(default=8000, ge=1, le=65535, description="Puerto de la API")
    debug: bool = Field(default=False, description="Modo debug de la API")
    cors: Dict[str, Any] = Field(default_factory=dict, description="Configuración CORS")
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        if not v:
            raise ValueError("El host de la API no puede estar vacío")
        return v


class LoggingConfig(BaseModel):
    """Configuración de logging"""
    level: str = Field(default="INFO", description="Nivel de logging")
    format: str = Field(default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", 
                       description="Formato de logging")
    file: Optional[str] = Field(default=None, description="Archivo de log")
    max_size: str = Field(default="100MB", description="Tamaño máximo del archivo de log")
    backup_count: int = Field(default=5, ge=0, description="Número de archivos de backup")
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Nivel de logging inválido. Debe ser uno de: {valid_levels}")
        return v.upper()


class ProcessingConfig(BaseModel):
    """Configuración de procesamiento de datos"""
    batch_size: int = Field(default=100, ge=1, description="Tamaño del lote de procesamiento")
    max_workers: int = Field(default=4, ge=1, description="Número máximo de workers")
    timeout: int = Field(default=30, ge=1, description="Timeout de procesamiento en segundos")
    retry_attempts: int = Field(default=3, ge=0, description="Número de intentos de reintento")
    retry_delay: int = Field(default=5, ge=1, description="Delay entre reintentos en segundos")


class NormalizerConfig(BaseModel):
    """Configuración de normalizadores de datos"""
    temperature: Dict[str, Any] = Field(default_factory=dict, description="Configuración de temperatura")
    humidity: Dict[str, Any] = Field(default_factory=dict, description="Configuración de humedad")
    pressure: Dict[str, Any] = Field(default_factory=dict, description="Configuración de presión")


class StorageConfig(BaseModel):
    """Configuración de almacenamiento"""
    timeseries: Dict[str, Any] = Field(..., description="Configuración de series temporales")
    relational: Dict[str, Any] = Field(..., description="Configuración de datos relacionales")
    metadata: Dict[str, Any] = Field(..., description="Configuración de metadatos")


class SecurityConfig(BaseModel):
    """Configuración de seguridad"""
    mqtt: Dict[str, Any] = Field(default_factory=dict, description="Seguridad MQTT")
    api: Dict[str, Any] = Field(default_factory=dict, description="Seguridad de la API")
    database: Dict[str, Any] = Field(default_factory=dict, description="Seguridad de la base de datos")


class MonitoringConfig(BaseModel):
    """Configuración de monitoreo"""
    health_check_interval: int = Field(default=30, ge=1, description="Intervalo de health check en segundos")
    metrics_collection: bool = Field(default=True, description="Habilitar recolección de métricas")
    alerting: Dict[str, Any] = Field(default_factory=dict, description="Configuración de alertas")


class RabbitMQConfig(BaseModel):
    """Configuración de RabbitMQ para comunicación asíncrona"""
    host: str = Field(default="localhost", description="Host de RabbitMQ")
    port: int = Field(default=5672, ge=1, le=65535, description="Puerto de RabbitMQ")
    username: str = Field(default="guest", description="Usuario de RabbitMQ")
    password: str = Field(default="guest", description="Contraseña de RabbitMQ")
    virtual_host: str = Field(default="/", description="Virtual host de RabbitMQ")
    exchange: str = Field(default="iot_middleware", description="Exchange principal")
    queue_prefix: str = Field(default="iot", description="Prefijo para las colas")
    heartbeat: int = Field(default=600, ge=0, description="Heartbeat en segundos")
    connection_attempts: int = Field(default=3, ge=1, description="Intentos de conexión")
    retry_delay: int = Field(default=5, ge=1, description="Delay entre reintentos en segundos")
    enable_monitoring: bool = Field(default=True, description="Habilitar publicación de métricas")
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("El host de RabbitMQ no puede estar vacío")
        return v


class IoTMiddlewareConfig(BaseModel):
    """Configuración principal del IoT Middleware"""
    mqtt: MQTTConfig = Field(..., description="Configuración MQTT")
    influxdb: InfluxDBConfig = Field(..., description="Configuración de InfluxDB")
    postgresql: PostgreSQLConfig = Field(..., description="Configuración de PostgreSQL")
    api: APIConfig = Field(..., description="Configuración de la API")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Configuración de logging")
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig, description="Configuración de procesamiento")
    normalizers: NormalizerConfig = Field(default_factory=NormalizerConfig, description="Configuración de normalizadores")
    storage: StorageConfig = Field(..., description="Configuración de almacenamiento")
    ingesta: Dict[str, Any] = Field(default_factory=dict, description="Configuración de ingesta")
    security: SecurityConfig = Field(default_factory=SecurityConfig, description="Configuración de seguridad")
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig, description="Configuración de monitoreo")
    rabbitmq: RabbitMQConfig = Field(default_factory=RabbitMQConfig, description="Configuración de RabbitMQ")
    
    model_config = ConfigDict(extra="ignore")  # Ignorar campos adicionales no definidos


class ConfigLoader:
    """Cargador de configuración del IoT Middleware"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializar el cargador de configuración
        
        Args:
            config_path: Ruta al archivo de configuración. Si es None, se buscará automáticamente
        """
        self.config_path = config_path
        self.config: Optional[IoTMiddlewareConfig] = None
        self._raw_config: Optional[Dict[str, Any]] = None
    
    def find_config_file(self, search_paths: Optional[List[str]] = None) -> str:
        """
        Buscar automáticamente el archivo de configuración
        
        Args:
            search_paths: Lista de rutas donde buscar. Si es None, se usan rutas por defecto
        
        Returns:
            Ruta al archivo de configuración encontrado
            
        Raises:
            FileNotFoundError: Si no se encuentra ningún archivo de configuración
        """
        if search_paths is None:
            search_paths = [
                "config.yaml",
                "config.yml",
                "examples/config_test.yaml",
                "examples/config_simple.yaml",
                "examples/config_with_postgresql.yaml",
                "../examples/config_test.yaml",
                "../examples/config_simple.yaml",
                "../examples/config_with_postgresql.yaml"
            ]
        
        for path in search_paths:
            if os.path.exists(path):
                logger.info(f"Archivo de configuración encontrado: {path}")
                return path
        
        raise FileNotFoundError(
            f"No se encontró ningún archivo de configuración en las rutas: {search_paths}"
        )
    
    def load_config(self, config_path: Optional[str] = None, validate: bool = True) -> IoTMiddlewareConfig:
        """
        Cargar la configuración desde un archivo YAML
        
        Args:
            config_path: Ruta al archivo de configuración. Si es None, se usa self.config_path
            validate: Si se debe validar la configuración cargada
        
        Returns:
            Configuración validada del IoT Middleware
            
        Raises:
            FileNotFoundError: Si no se encuentra el archivo de configuración
            yaml.YAMLError: Si hay un error al parsear el YAML
            ValidationError: Si la configuración no es válida
        """
        # Determinar la ruta del archivo de configuración
        if config_path is None:
            if self.config_path is None:
                config_path = self.find_config_file()
            else:
                config_path = self.config_path
        
        # Verificar que el archivo existe
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
        
        # Cargar el archivo YAML
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self._raw_config = yaml.safe_load(file)
                logger.info(f"Configuración cargada desde: {config_path}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error al parsear el archivo YAML {config_path}: {e}")
        except Exception as e:
            raise Exception(f"Error inesperado al cargar la configuración: {e}")
        
        # Validar la configuración si se solicita
        if validate:
            try:
                self.config = IoTMiddlewareConfig(**self._raw_config)
                logger.info("Configuración validada exitosamente")
            except ValidationError as e:
                logger.error("Error de validación en la configuración:")
                for error in e.errors():
                    logger.error(f"  - {error['loc']}: {error['msg']}")
                raise  # Re-lanzar la excepción original
        
        return self.config
    
    def get_config(self) -> IoTMiddlewareConfig:
        """
        Obtener la configuración cargada
        
        Returns:
            Configuración del IoT Middleware
            
        Raises:
            RuntimeError: Si la configuración no ha sido cargada
        """
        if self.config is None:
            raise RuntimeError("La configuración no ha sido cargada. Llama a load_config() primero.")
        return self.config
    
    def get_raw_config(self) -> Dict[str, Any]:
        """
        Obtener la configuración raw (sin validar)
        
        Returns:
            Configuración raw del archivo YAML
            
        Raises:
            RuntimeError: Si la configuración no ha sido cargada
        """
        if self._raw_config is None:
            raise RuntimeError("La configuración no ha sido cargada. Llama a load_config() primero.")
        return self._raw_config
    
    def reload_config(self) -> IoTMiddlewareConfig:
        """
        Recargar la configuración desde el archivo
        
        Returns:
            Configuración recargada y validada
        """
        if self.config_path is None:
            raise RuntimeError("No se puede recargar la configuración sin una ruta específica")
        
        return self.load_config(self.config_path)
    
    def validate_config(self) -> bool:
        """
        Validar la configuración actual
        
        Returns:
            True si la configuración es válida
            
        Raises:
            RuntimeError: Si la configuración no ha sido cargada
        """
        if self.config is None:
            raise RuntimeError("La configuración no ha sido cargada. Llama a load_config() primero.")
        
        try:
            # La validación ya se hizo al cargar, pero podemos hacer validaciones adicionales aquí
            logger.info("Configuración validada exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error en la validación: {e}")
            return False
    
    def get_mqtt_config(self) -> MQTTConfig:
        """Obtener configuración MQTT"""
        return self.get_config().mqtt
    
    def get_influxdb_config(self) -> InfluxDBConfig:
        """Obtener configuración de InfluxDB"""
        return self.get_config().influxdb
    
    def get_postgresql_config(self) -> PostgreSQLConfig:
        """Obtener configuración de PostgreSQL"""
        return self.get_config().postgresql
    
    def get_api_config(self) -> APIConfig:
        """Obtener configuración de la API"""
        return self.get_config().api
    
    def get_logging_config(self) -> LoggingConfig:
        """Obtener configuración de logging"""
        return self.get_config().logging
    
    def get_processing_config(self) -> ProcessingConfig:
        """Obtener configuración de procesamiento"""
        return self.get_config().processing
    
    def get_storage_config(self) -> StorageConfig:
        """Obtener configuración de almacenamiento"""
        return self.get_config().storage
    
    def get_security_config(self) -> SecurityConfig:
        """Obtener configuración de seguridad"""
        return self.get_config().security
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Obtener configuración de monitoreo"""
        return self.get_config().monitoring


def load_config(config_path: Optional[str] = None) -> IoTMiddlewareConfig:
    """
    Función de conveniencia para cargar configuración rápidamente
    
    Args:
        config_path: Ruta al archivo de configuración
        
    Returns:
        Configuración cargada y validada
    """
    loader = ConfigLoader(config_path)
    return loader.load_config()


def validate_config_file(config_path: str) -> bool:
    """
    Validar un archivo de configuración sin cargarlo
    
    Args:
        config_path: Ruta al archivo de configuración
        
    Returns:
        True si el archivo es válido, False en caso contrario
    """
    try:
        loader = ConfigLoader(config_path)
        loader.load_config()
        return True
    except Exception as e:
        logger.error(f"Archivo de configuración inválido: {e}")
        return False


# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging básico
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Cargar configuración
        config = load_config()
        print("✅ Configuración cargada exitosamente")
        
        # Mostrar información básica
        print(f"📡 Broker MQTT: {config.mqtt.broker['host']}:{config.mqtt.broker['port']}")
        print(f"🗄️  InfluxDB: {config.influxdb.url}")
        print(f"🐘 PostgreSQL: {config.postgresql.host}:{config.postgresql.port}")
        print(f"🌐 API: {config.api.host}:{config.api.port}")
        
    except Exception as e:
        print(f"❌ Error al cargar la configuración: {e}")
        exit(1)
