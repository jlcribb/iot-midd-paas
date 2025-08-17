"""
Módulo de Manejo de Base de Datos - IoT Middleware
==================================================

Este módulo proporciona funcionalidades para la persistencia de datos IoT
en diferentes tipos de bases de datos (PostgreSQL e InfluxDB), incluyendo
manejo de conexiones, reconexión automática y funciones de inserción.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from contextlib import contextmanager

# Importar configuración
try:
    from ..config import PostgreSQLConfig, InfluxDBConfig, StorageConfig
except ImportError:
    # Fallback para importación directa
    from iot_middleware.config import PostgreSQLConfig, InfluxDBConfig, StorageConfig

# Configurar logging
logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Tipos de base de datos soportados"""
    POSTGRESQL = "postgresql"
    INFLUXDB = "influxdb"
    HYBRID = "hybrid"  # Usar ambas bases de datos


class ConnectionStatus(Enum):
    """Estado de la conexión a la base de datos"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


@dataclass
class DatabaseMetrics:
    """Métricas de la base de datos"""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    last_operation: Optional[datetime] = None
    connection_attempts: int = 0
    last_connection: Optional[datetime] = None
    uptime_seconds: int = 0
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PostgreSQLHandler:
    """Manejador de conexiones a PostgreSQL usando SQLAlchemy"""
    
    def __init__(self, config: PostgreSQLConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.engine = None
        self.session_factory = None
        self.metrics = DatabaseMetrics()
        self._lock = threading.Lock()
        self._reconnect_thread = None
        self._stop_reconnect = threading.Event()
        
        # Intentar conexión inicial
        self._connect()
    
    def _connect(self) -> bool:
        """Establecer conexión a PostgreSQL"""
        try:
            self.connection_status = ConnectionStatus.CONNECTING
            self.logger.info("Conectando a PostgreSQL...")
            
            # Importar SQLAlchemy solo cuando sea necesario
            try:
                from sqlalchemy import create_engine, text
                from sqlalchemy.orm import sessionmaker
                from sqlalchemy.exc import SQLAlchemyError
            except ImportError as e:
                self.logger.error(f"SQLAlchemy no está instalado: {e}")
                self.logger.error("Instalar con: pip install sqlalchemy psycopg2-binary")
                self.connection_status = ConnectionStatus.ERROR
                return False
            
            # Construir URL de conexión
            connection_url = (
                f"postgresql://{self.config.username}:{self.config.password}"
                f"@{self.config.host}:{self.config.port}/{self.config.database}"
            )
            
            # Crear engine con configuración de pool
            self.engine = create_engine(
                connection_url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=False  # Deshabilitar logging SQL
            )
            
            # Crear session factory
            self.session_factory = sessionmaker(bind=self.engine)
            
            # Probar conexión
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.connection_status = ConnectionStatus.CONNECTED
            self.metrics.last_connection = datetime.now(timezone.utc)
            self.metrics.connection_attempts += 1
            
            self.logger.info("✅ Conexión exitosa a PostgreSQL")
            
            # Crear tablas si no existen
            self._create_tables()
            
            return True
            
        except Exception as e:
            self.connection_status = ConnectionStatus.ERROR
            self.logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            return False
    
    def _create_tables(self):
        """Crear tablas necesarias si no existen"""
        try:
            with self.engine.connect() as conn:
                # Crear esquema si no existe
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.config.db_schema}"))
                
                # Crear tabla sensor_data
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {self.config.db_schema}.sensor_data (
                        id SERIAL PRIMARY KEY,
                        topic VARCHAR(255) NOT NULL,
                        value JSONB NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                        device_id VARCHAR(100),
                        sensor_type VARCHAR(100),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """))
                
                # Crear índices para mejor rendimiento
                conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_sensor_data_timestamp 
                    ON {self.config.db_schema}.sensor_data (timestamp);
                """))
                
                conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_sensor_data_device_id 
                    ON {self.config.db_schema}.sensor_data (device_id);
                """))
                
                conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_sensor_data_sensor_type 
                    ON {self.config.db_schema}.sensor_data (sensor_type);
                """))
                
                # Crear tabla de dispositivos
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {self.config.db_schema}.devices (
                        id SERIAL PRIMARY KEY,
                        device_id VARCHAR(100) UNIQUE NOT NULL,
                        name VARCHAR(255),
                        type VARCHAR(100),
                        location VARCHAR(255),
                        status VARCHAR(50) DEFAULT 'active',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """))
                
                # Crear tabla de sensores
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {self.config.db_schema}.sensors (
                        id SERIAL PRIMARY KEY,
                        sensor_id VARCHAR(100) UNIQUE NOT NULL,
                        device_id VARCHAR(100) REFERENCES {self.config.db_schema}.devices(device_id),
                        name VARCHAR(255),
                        type VARCHAR(100),
                        unit VARCHAR(50),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """))
                
                conn.commit()
                self.logger.info("✅ Tablas creadas/verificadas en PostgreSQL")
                
        except Exception as e:
            self.logger.error(f"❌ Error creando tablas: {e}")
            # No lanzar excepción, solo log del error
    
    def _reconnect(self):
        """Reconectar a PostgreSQL en background"""
        while not self._stop_reconnect.is_set():
            if self.connection_status == ConnectionStatus.ERROR:
                self.logger.info("🔄 Intentando reconexión a PostgreSQL...")
                if self._connect():
                    self.logger.info("✅ Reconexión exitosa")
                    break
                else:
                    self.logger.warning("⚠️  Reconexión fallida, reintentando en 30 segundos...")
                    time.sleep(30)
            else:
                break
    
    def start_reconnect_monitor(self):
        """Iniciar monitor de reconexión en background"""
        if self._reconnect_thread is None or not self._reconnect_thread.is_alive():
            self._reconnect_thread = threading.Thread(target=self._reconnect, daemon=True)
            self._reconnect_thread.start()
            self.logger.info("🔄 Monitor de reconexión iniciado")
    
    def stop_reconnect_monitor(self):
        """Detener monitor de reconexión"""
        self._stop_reconnect.set()
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            self._reconnect_thread.join(timeout=5)
        self.logger.info("🔄 Monitor de reconexión detenido")
    
    @contextmanager
    def get_session(self):
        """Context manager para obtener sesión de base de datos"""
        if self.connection_status != ConnectionStatus.CONNECTED:
            raise ConnectionError("No hay conexión activa a PostgreSQL")
        
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def insert_sensor_data(self, data_dict: Dict[str, Any]) -> bool:
        """
        Insertar datos de sensor en PostgreSQL
        
        Args:
            data_dict: Diccionario con datos del sensor
            
        Returns:
            True si la inserción fue exitosa, False en caso contrario
        """
        try:
            self.metrics.total_operations += 1
            self.metrics.last_operation = datetime.now(timezone.utc)
            
            # Extraer campos del diccionario
            topic = data_dict.get('topic', 'unknown')
            value = data_dict.get('value', data_dict)  # Usar todo el dict si no hay campo 'value'
            timestamp = data_dict.get('timestamp')
            device_id = data_dict.get('device_id')
            sensor_type = data_dict.get('sensor_type')
            
            # Convertir timestamp si es string
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.now(timezone.utc)
            elif timestamp is None:
                timestamp = datetime.now(timezone.utc)
            
            # Preparar datos para inserción
            insert_data = {
                'topic': topic,
                'value': json.dumps(value, default=str),
                'timestamp': timestamp,
                'device_id': device_id,
                'sensor_type': sensor_type
            }
            
            with self.get_session() as session:
                from sqlalchemy import text
                
                # Insertar datos
                result = session.execute(text(f"""
                    INSERT INTO {self.config.db_schema}.sensor_data 
                    (topic, value, timestamp, device_id, sensor_type)
                    VALUES (:topic, :value, :timestamp, :device_id, :sensor_type)
                    RETURNING id;
                """), insert_data)
                
                inserted_id = result.scalar()
                self.logger.info(f"✅ Datos insertados en PostgreSQL con ID: {inserted_id}")
                
                self.metrics.successful_operations += 1
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error insertando datos en PostgreSQL: {e}")
            self.metrics.failed_operations += 1
            
            # Marcar como error de conexión si es apropiado
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                self.connection_status = ConnectionStatus.ERROR
                self.start_reconnect_monitor()
            
            return False
    
    def get_connection_status(self) -> ConnectionStatus:
        """Obtener estado de la conexión"""
        return self.connection_status
    
    def get_metrics(self) -> DatabaseMetrics:
        """Obtener métricas de la base de datos"""
        if self.connection_status == ConnectionStatus.CONNECTED:
            self.metrics.uptime_seconds = int(
                (datetime.now(timezone.utc) - self.metrics.start_time).total_seconds()
            )
        return self.metrics
    
    def close(self):
        """Cerrar conexiones a PostgreSQL"""
        self.stop_reconnect_monitor()
        if self.engine:
            self.engine.dispose()
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.logger.info("🔌 Conexiones a PostgreSQL cerradas")


class InfluxDBHandler:
    """Manejador de conexiones a InfluxDB"""
    
    def __init__(self, config: InfluxDBConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.client = None
        self.write_api = None
        self.metrics = DatabaseMetrics()
        self._lock = threading.Lock()
        
        # Intentar conexión inicial
        self._connect()
    
    def _connect(self) -> bool:
        """Establecer conexión a InfluxDB"""
        try:
            self.connection_status = ConnectionStatus.CONNECTING
            self.logger.info("Conectando a InfluxDB...")
            
            # Importar cliente InfluxDB solo cuando sea necesario
            try:
                from influxdb_client import InfluxDBClient
                from influxdb_client.client.write_api import SYNCHRONOUS
            except ImportError as e:
                self.logger.error(f"Cliente InfluxDB no está instalado: {e}")
                self.logger.error("Instalar con: pip install influxdb-client")
                self.connection_status = ConnectionStatus.ERROR
                return False
            
            # Crear cliente
            self.client = InfluxDBClient(
                url=self.config.url,
                token=self.config.token,
                org=self.config.org
            )
            
            # Crear API de escritura
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            
            # Probar conexión
            health = self.client.health()
            if health.status == 'pass':
                self.connection_status = ConnectionStatus.CONNECTED
                self.metrics.last_connection = datetime.now(timezone.utc)
                self.metrics.connection_attempts += 1
                
                self.logger.info("✅ Conexión exitosa a InfluxDB")
                return True
            else:
                raise ConnectionError(f"InfluxDB no está saludable: {health.message}")
                
        except Exception as e:
            self.connection_status = ConnectionStatus.ERROR
            self.logger.error(f"❌ Error conectando a InfluxDB: {e}")
            return False
    
    def insert_influxdb(self, data_dict: Dict[str, Any]) -> bool:
        """
        Insertar datos en InfluxDB
        
        Args:
            data_dict: Diccionario con datos a insertar
            
        Returns:
            True si la inserción fue exitosa, False en caso contrario
        """
        try:
            self.metrics.total_operations += 1
            self.metrics.last_operation = datetime.now(timezone.utc)
            
            # Extraer campos del diccionario
            device_id = data_dict.get('device_id', 'unknown')
            sensor_type = data_dict.get('sensor_type', 'unknown')
            value = data_dict.get('value')
            timestamp = data_dict.get('timestamp')
            topic = data_dict.get('topic', 'unknown')
            
            # Convertir timestamp si es string
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.now(timezone.utc)
            elif timestamp is None:
                timestamp = datetime.now(timezone.utc)
            
            # Preparar punto para InfluxDB
            from influxdb_client import Point
            
            point = Point("sensor_data") \
                .tag("device_id", device_id) \
                .tag("sensor_type", sensor_type) \
                .tag("topic", topic) \
                .field("value", value) \
                .time(timestamp)
            
            # Agregar campos adicionales si están disponibles
            for key, val in data_dict.items():
                if key not in ['device_id', 'sensor_type', 'value', 'timestamp', 'topic']:
                    if isinstance(val, (int, float, str, bool)):
                        point = point.field(key, val)
            
            # Escribir punto
            self.write_api.write(bucket=self.config.bucket, record=point)
            
            self.logger.info(f"✅ Datos insertados en InfluxDB: {device_id}.{sensor_type}")
            
            self.metrics.successful_operations += 1
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error insertando datos en InfluxDB: {e}")
            self.metrics.failed_operations += 1
            
            # Marcar como error de conexión si es apropiado
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                self.connection_status = ConnectionStatus.ERROR
            
            return False
    
    def get_connection_status(self) -> ConnectionStatus:
        """Obtener estado de la conexión"""
        return self.connection_status
    
    def get_metrics(self) -> DatabaseMetrics:
        """Obtener métricas de la base de datos"""
        if self.connection_status == ConnectionStatus.CONNECTED:
            self.metrics.uptime_seconds = int(
                (datetime.now(timezone.utc) - self.metrics.start_time).total_seconds()
            )
        return self.metrics
    
    def close(self):
        """Cerrar conexiones a InfluxDB"""
        if self.write_api:
            self.write_api.close()
        if self.client:
            self.client.close()
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.logger.info("🔌 Conexiones a InfluxDB cerradas")


class DatabaseHandler:
    """Manejador principal de bases de datos"""
    
    def __init__(self, postgresql_config: PostgreSQLConfig, 
                 influxdb_config: InfluxDBConfig, 
                 storage_config: StorageConfig):
        self.postgresql_config = postgresql_config
        self.influxdb_config = influxdb_config
        self.storage_config = storage_config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Determinar tipo de base de datos a usar
        self.db_type = self._determine_database_type()
        
        # Inicializar manejadores según el tipo
        self.postgresql_handler = None
        self.influxdb_handler = None
        
        if self.db_type in [DatabaseType.POSTGRESQL, DatabaseType.HYBRID]:
            self.postgresql_handler = PostgreSQLHandler(postgresql_config)
        
        if self.db_type in [DatabaseType.INFLUXDB, DatabaseType.HYBRID]:
            self.influxdb_handler = InfluxDBHandler(influxdb_config)
        
        self.logger.info(f"🗄️  Manejador de base de datos inicializado: {self.db_type.value}")
    
    def _determine_database_type(self) -> DatabaseType:
        """Determinar qué tipo de base de datos usar basado en la configuración"""
        timeseries_provider = self.storage_config.timeseries.get('provider', '').lower()
        relational_provider = self.storage_config.relational.get('provider', '').lower()
        
        if timeseries_provider == 'influxdb' and relational_provider == 'postgresql':
            return DatabaseType.HYBRID
        elif timeseries_provider == 'influxdb':
            return DatabaseType.INFLUXDB
        elif relational_provider == 'postgresql':
            return DatabaseType.POSTGRESQL
        else:
            # Por defecto, usar PostgreSQL
            return DatabaseType.POSTGRESQL
    
    def insert_sensor_data(self, data_dict: Dict[str, Any]) -> bool:
        """
        Insertar datos de sensor en la base de datos apropiada
        
        Args:
            data_dict: Diccionario con datos del sensor
            
        Returns:
            True si la inserción fue exitosa en al menos una base de datos
        """
        success = False
        
        # Insertar en PostgreSQL si está disponible
        if self.postgresql_handler and self.postgresql_handler.get_connection_status() == ConnectionStatus.CONNECTED:
            try:
                if self.postgresql_handler.insert_sensor_data(data_dict):
                    success = True
                    self.logger.debug("✅ Datos insertados en PostgreSQL")
            except Exception as e:
                self.logger.error(f"❌ Error en PostgreSQL: {e}")
        
        # Insertar en InfluxDB si está disponible
        if self.influxdb_handler and self.influxdb_handler.get_connection_status() == ConnectionStatus.CONNECTED:
            try:
                if self.influxdb_handler.insert_influxdb(data_dict):
                    success = True
                    self.logger.debug("✅ Datos insertados en InfluxDB")
            except Exception as e:
                self.logger.error(f"❌ Error en InfluxDB: {e}")
        
        if success:
            self.logger.info("✅ Datos de sensor insertados exitosamente")
        else:
            self.logger.error("❌ No se pudo insertar en ninguna base de datos")
        
        return success
    
    def get_connection_status(self) -> Dict[str, ConnectionStatus]:
        """Obtener estado de todas las conexiones"""
        status = {}
        
        if self.postgresql_handler:
            status['postgresql'] = self.postgresql_handler.get_connection_status()
        
        if self.influxdb_handler:
            status['influxdb'] = self.influxdb_handler.get_connection_status()
        
        return status
    
    def get_metrics(self) -> Dict[str, DatabaseMetrics]:
        """Obtener métricas de todas las bases de datos"""
        metrics = {}
        
        if self.postgresql_handler:
            metrics['postgresql'] = self.postgresql_handler.get_metrics()
        
        if self.influxdb_handler:
            metrics['influxdb'] = self.influxdb_handler.get_metrics()
        
        return metrics
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar salud de todas las bases de datos"""
        health = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'databases': {}
        }
        
        # Verificar PostgreSQL
        if self.postgresql_handler:
            pg_status = self.postgresql_handler.get_connection_status()
            pg_metrics = self.postgresql_handler.get_metrics()
            
            health['databases']['postgresql'] = {
                'status': pg_status.value,
                'connected': pg_status == ConnectionStatus.CONNECTED,
                'metrics': {
                    'total_operations': pg_metrics.total_operations,
                    'successful_operations': pg_metrics.successful_operations,
                    'failed_operations': pg_metrics.failed_operations,
                    'uptime_seconds': pg_metrics.uptime_seconds
                }
            }
            
            if pg_status != ConnectionStatus.CONNECTED:
                health['status'] = 'degraded'
        
        # Verificar InfluxDB
        if self.influxdb_handler:
            inf_status = self.influxdb_handler.get_connection_status()
            inf_metrics = self.influxdb_handler.get_metrics()
            
            health['databases']['influxdb'] = {
                'status': inf_status.value,
                'connected': inf_status == ConnectionStatus.CONNECTED,
                'metrics': {
                    'total_operations': inf_metrics.total_operations,
                    'successful_operations': inf_metrics.successful_operations,
                    'failed_operations': inf_metrics.failed_operations,
                    'uptime_seconds': inf_metrics.uptime_seconds
                }
            }
            
            if inf_status != ConnectionStatus.CONNECTED:
                health['status'] = 'degraded'
        
        # Si ninguna base de datos está conectada, marcar como no saludable
        if not any(db['connected'] for db in health['databases'].values()):
            health['status'] = 'unhealthy'
        
        return health
    
    def close(self):
        """Cerrar todas las conexiones"""
        if self.postgresql_handler:
            self.postgresql_handler.close()
        
        if self.influxdb_handler:
            self.influxdb_handler.close()
        
        self.logger.info("🔌 Todas las conexiones de base de datos cerradas")


# Función de conveniencia para crear manejador de base de datos
def create_database_handler(postgresql_config: PostgreSQLConfig, 
                           influxdb_config: InfluxDBConfig,
                           storage_config: StorageConfig) -> DatabaseHandler:
    """
    Crear una instancia del manejador de base de datos
    
    Args:
        postgresql_config: Configuración de PostgreSQL
        influxdb_config: Configuración de InfluxDB
        storage_config: Configuración de almacenamiento
    
    Returns:
        Instancia del manejador de base de datos
    """
    return DatabaseHandler(postgresql_config, influxdb_config, storage_config)


# Función principal insert_sensor_data para compatibilidad
def insert_sensor_data(data_dict: Dict[str, Any], **kwargs) -> bool:
    """
    Función principal para insertar datos de sensor (compatibilidad con código existente)
    
    Args:
        data_dict: Datos del sensor a insertar
        **kwargs: Argumentos adicionales
    
    Returns:
        True si la inserción fue exitosa, False en caso contrario
    """
    # Crear configuración por defecto si no se proporciona
    try:
        from iot_middleware.config import PostgreSQLConfig, InfluxDBConfig, StorageConfig
    except ImportError:
        # Fallback para importación directa
        from iot_middleware.config import PostgreSQLConfig, InfluxDBConfig, StorageConfig
    
    # Configuración por defecto
    default_postgresql_config = PostgreSQLConfig(
        host="localhost",
        port=5432,
        database="iot_middleware",
        username="iot_user",
        password="iot_password"
    )
    
    default_influxdb_config = InfluxDBConfig(
        url="http://localhost:8086",
        token="dev-token",
        org="my-org",
        bucket="iot"
    )
    
    default_storage_config = StorageConfig(
        timeseries={"provider": "influxdb"},
        relational={"provider": "postgresql"},
        metadata={"provider": "postgresql"}
    )
    
    # Crear manejador
    handler = create_database_handler(
        default_postgresql_config, 
        default_influxdb_config, 
        default_storage_config
    )
    
    try:
        # Insertar datos
        return handler.insert_sensor_data(data_dict)
    finally:
        # Cerrar conexiones
        handler.close()


# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Crear configuración por defecto
        from iot_middleware.config import PostgreSQLConfig, InfluxDBConfig, StorageConfig
        
        postgresql_config = PostgreSQLConfig(
            host="localhost",
            port=5432,
            database="iot_middleware",
            username="iot_user",
            password="iot_password"
        )
        
        influxdb_config = InfluxDBConfig(
            url="http://localhost:8086",
            token="dev-token",
            org="my-org",
            bucket="iot"
        )
        
        storage_config = StorageConfig(
            timeseries={"provider": "influxdb"},
            relational={"provider": "postgresql"},
            metadata={"provider": "postgresql"}
        )
        
        # Crear manejador
        handler = create_database_handler(postgresql_config, influxdb_config, storage_config)
        
        # Datos de ejemplo
        test_data = {
            "topic": "iot/sensor_001/temperature",
            "device_id": "sensor_001",
            "sensor_type": "temperature",
            "value": 24.5,
            "unit": "celsius",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print("🧪 Probando inserción de datos...")
        print(f"📨 Datos: {json.dumps(test_data, indent=2, default=str)}")
        
        # Insertar datos
        success = handler.insert_sensor_data(test_data)
        
        if success:
            print("✅ Datos insertados exitosamente")
        else:
            print("❌ Error insertando datos")
        
        # Mostrar estado de conexión
        status = handler.get_connection_status()
        print(f"\n📊 Estado de conexiones: {status}")
        
        # Mostrar métricas
        metrics = handler.get_metrics()
        print(f"\n📈 Métricas:")
        for db_name, db_metrics in metrics.items():
            print(f"   {db_name}: {db_metrics.total_operations} operaciones, "
                  f"{db_metrics.successful_operations} exitosas")
        
        # Health check
        health = handler.health_check()
        print(f"\n🏥 Health Check: {health['status']}")
        
        # Cerrar conexiones
        handler.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
