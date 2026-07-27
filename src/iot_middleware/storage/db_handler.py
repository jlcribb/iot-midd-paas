"""
Módulo de Manejo de Base de Datos - IoT Middleware
==================================================

Este módulo proporciona funcionalidades para la persistencia de datos IoT
en diferentes tipos de bases de datos (PostgreSQL e InfluxDB), incluyendo
manejo de conexiones, reconexión automática y funciones de inserción.

Segmentación interna actual:

- official runtime infrastructure:
  - configuración, conexiones, sesiones, métricas y health checks
- transition telemetry write path:
  - escritura de telemetría híbrida PostgreSQL + InfluxDB
- legacy bootstrap/compatibility:
  - bootstrap de esquema en runtime
  - helper module-level `insert_sensor_data(...)`
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
import threading
from contextlib import contextmanager

# Importar configuración
try:
    from ..config import IoTMiddlewareConfig, PostgreSQLConfig, InfluxDBConfig, StorageConfig
except ImportError:
    # Fallback para importación directa
    from iot_middleware.config import IoTMiddlewareConfig, PostgreSQLConfig, InfluxDBConfig, StorageConfig

# Configurar logging
logger = logging.getLogger(__name__)

DEFAULT_SCHEMA_BOOTSTRAP_MODE = "alembic"

OFFICIAL_RUNTIME_SURFACE = (
    "DatabaseType",
    "ConnectionStatus",
    "DatabaseMetrics",
    "PostgreSQLHandler._connect",
    "PostgreSQLHandler.get_session",
    "PostgreSQLHandler.get_connection_status",
    "PostgreSQLHandler.get_metrics",
    "PostgreSQLHandler.close",
    "InfluxDBHandler._connect",
    "InfluxDBHandler.get_connection_status",
    "InfluxDBHandler.get_metrics",
    "InfluxDBHandler.close",
    "DatabaseHandler._determine_database_type",
    "DatabaseHandler.get_connection_status",
    "DatabaseHandler.get_metrics",
    "DatabaseHandler.health_check",
    "DatabaseHandler.get_session",
    "DatabaseHandler.is_connected",
    "DatabaseHandler.close",
    "_resolve_database_configs",
    "create_database_handler",
    "get_project_control_settings",
    "list_project_control_policies",
    "persist_control_audit_record",
)

TRANSITION_TELEMETRY_SURFACE = (
    "PostgreSQLHandler.write_legacy_sensor_record",
    "PostgreSQLHandler.insert_sensor_data",
    "InfluxDBHandler.write_telemetry_point",
    "InfluxDBHandler.insert_influxdb",
    "DatabaseHandler.write_telemetry",
    "DatabaseHandler.insert_sensor_data",
)

LEGACY_COMPATIBILITY_SURFACE = (
    "get_schema_bootstrap_mode",
    "PostgreSQLHandler._bootstrap_schema_if_needed",
    "PostgreSQLHandler._create_tables",
    "_build_legacy_default_configs",
    "insert_sensor_data",
)


def get_schema_bootstrap_mode() -> str:
    """Retorna el modo de bootstrap de esquema para PostgreSQL.

    Modos soportados:
    - `alembic`: no crea tablas en runtime, se asume migración previa.
    - `legacy`: mantiene el comportamiento histórico (create tables/create_all).
    - `none`: no inicializa esquema automáticamente.
    """
    mode = os.getenv("IOT_MW_SCHEMA_BOOTSTRAP_MODE", DEFAULT_SCHEMA_BOOTSTRAP_MODE).strip().lower()
    if mode in {"alembic", "legacy", "none"}:
        return mode
    logger.warning(
        "Modo IOT_MW_SCHEMA_BOOTSTRAP_MODE inválido: %s. Usando %s",
        mode,
        DEFAULT_SCHEMA_BOOTSTRAP_MODE,
    )
    return DEFAULT_SCHEMA_BOOTSTRAP_MODE


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
            
            # Crear session factory (no expirar objetos tras commit)
            self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
            
            # Probar conexión
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.connection_status = ConnectionStatus.CONNECTED
            self.metrics.last_connection = datetime.now(timezone.utc)
            self.metrics.connection_attempts += 1
            
            self.logger.info("✅ Conexión exitosa a PostgreSQL")
            
            # Bootstrap de esquema en modo explícito.
            self._bootstrap_schema_if_needed()
            
            return True
            
        except Exception as e:
            self.connection_status = ConnectionStatus.ERROR
            self.logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            return False
    
    def _bootstrap_schema_if_needed(self):
        """Inicializa esquema según el modo configurado.

        Legacy/bootstrap boundary:
        este comportamiento existe para compatibilidad transicional y no
        representa la estrategia canonica del runtime, que debe apoyarse en Alembic.
        """
        mode = get_schema_bootstrap_mode()
        if mode in {"alembic", "none"}:
            self.logger.info(
                "⏭️  Bootstrap de esquema omitido (modo=%s). "
                "Asegúrate de aplicar migraciones Alembic.",
                mode,
            )
            return
        self._create_tables()

    def _create_tables(self):
        """Crear tablas necesarias en modo legacy.

        Legacy/bootstrap boundary:
        incluye tablas historicas (`sensor_data`, `devices`, `sensors`) y
        `Base.metadata.create_all(...)` para compatibilidad con entornos previos.
        """
        try:
            from sqlalchemy import text
            from ..models.base import Base
            from ..models import entities  # noqa: F401
            from ..models.enums import (
                EstadoProyecto,
                ProtocoloComunicacion,
                TipoDato,
                RolSistema,
                CalidadDato,
                SeveridadEvento,
                EstadoDispositivo,
            )
            
            def enum_values(enum_class: Any) -> List[str]:
                values: List[str] = []
                for attr_name in dir(enum_class):
                    if not attr_name.startswith('_') and attr_name.isupper():
                        attr_value = getattr(enum_class, attr_name)
                        if not callable(attr_value):
                            values.append(str(attr_value))
                return values
            
            with self.engine.connect() as conn:
                # Crear esquema si no existe
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.config.db_schema}"))
                
                # Extensiones necesarias (citext para emails)
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
                
                # Crear enums de PostgreSQL requeridos por los modelos ORM
                for enum_class in (
                    EstadoProyecto,
                    ProtocoloComunicacion,
                    TipoDato,
                    RolSistema,
                    CalidadDato,
                    SeveridadEvento,
                    EstadoDispositivo,
                ):
                    enum_name = enum_class.__name__
                    values = enum_values(enum_class)
                    def _escape_enum_value(value: str) -> str:
                        return "'" + value.replace("'", "''") + "'"
                    
                    values_sql = ", ".join([_escape_enum_value(value) for value in values])
                    conn.execute(text(f"""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1
                                FROM pg_type t
                                JOIN pg_namespace n ON n.oid = t.typnamespace
                                WHERE t.typname = '{enum_name}'
                                  AND n.nspname = '{self.config.db_schema}'
                            ) THEN
                                CREATE TYPE {self.config.db_schema}."{enum_name}" AS ENUM ({values_sql});
                            END IF;
                        END $$;
                    """))
                
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
            
            # Crear tablas definidas por los modelos ORM (proyectos, clientes, etc.)
            Base.metadata.create_all(self.engine)
            self.logger.info("✅ Tablas ORM creadas/verificadas en PostgreSQL")
                
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
    
    def write_legacy_sensor_record(self, data_dict: Dict[str, Any]) -> bool:
        """
        Transition telemetry boundary: persistencia legacy de telemetría en PostgreSQL.

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

    def insert_sensor_data(self, data_dict: Dict[str, Any]) -> bool:
        """Alias transicional preservado para el runtime actual de ingesta."""
        return self.write_legacy_sensor_record(data_dict)
    
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
    
    def write_telemetry_point(self, data_dict: Dict[str, Any]) -> bool:
        """
        Transition telemetry boundary: persistencia de telemetría en InfluxDB.

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

            # Evitar conflictos de tipo en Influx:
            # el campo legacy "value" pudo quedar tipado booleano en datos anteriores.
            # Escribimos nuevo campo estable por tipo.
            field_name = "value_num"
            field_value: Any
            if isinstance(value, bool):
                field_value = 1.0 if value else 0.0
            elif isinstance(value, (int, float)):
                field_value = float(value)
            elif isinstance(value, str):
                text = value.strip()
                try:
                    field_value = float(text)
                    field_name = "value_num"
                except ValueError:
                    field_name = "value_text"
                    field_value = value
            else:
                field_name = "value_text"
                field_value = str(value)

            point = Point("sensor_data") \
                .tag("device_id", device_id) \
                .tag("sensor_type", sensor_type) \
                .tag("topic", topic) \
                .field(field_name, field_value) \
                .time(timestamp)
            
            # Agregar metadatos como tags y sólo valores escalares numéricos como fields
            # para evitar mezclar series textuales con la telemetría principal.
            base_keys = {'device_id', 'sensor_type', 'value', 'timestamp', 'topic'}
            metadata_tag_keys = {
                'project_id',
                'project_name',
                'unit_id',
                'unit_name',
                'device_ref_id',
                'device_name',
                'kind',
                'signal',
                'quality',
            }

            for key, val in data_dict.items():
                if key in base_keys or val is None:
                    continue

                if key in metadata_tag_keys:
                    point = point.tag(key, str(val))
                    continue

                if key == "tick":
                    try:
                        point = point.field(key, int(val))
                    except (TypeError, ValueError):
                        pass
                    continue

                if isinstance(val, bool):
                    point = point.field(key, 1 if val else 0)
                    continue

                if isinstance(val, int):
                    point = point.field(key, int(val))
                    continue

                if isinstance(val, float):
                    point = point.field(key, float(val))
                    continue

                if isinstance(val, str):
                    text = val.strip()
                    if not text:
                        continue
                    try:
                        if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
                            point = point.field(key, int(text))
                        else:
                            point = point.field(key, float(text))
                    except ValueError:
                        # Ignorar strings libres para mantener esquema de fields numérico.
                        continue
            
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

    def insert_influxdb(self, data_dict: Dict[str, Any]) -> bool:
        """Alias transicional preservado para compatibilidad con el runtime actual."""
        return self.write_telemetry_point(data_dict)
    
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
    """Manejador principal de bases de datos.

    Official runtime boundary:
    conexiones, sesiones, health checks y métricas.

    Transition boundary:
    mantiene el fan-out de escritura de telemetría hacia PostgreSQL e InfluxDB
    mediante aliases conservados por compatibilidad.
    """
    
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
    
    def write_telemetry(self, data_dict: Dict[str, Any]) -> bool:
        """
        Transition telemetry boundary: escritura híbrida de telemetría.
        
        Args:
            data_dict: Diccionario con datos del sensor
            
        Returns:
            True si la inserción fue exitosa en al menos una base de datos
        """
        success = False
        
        # Insertar en PostgreSQL si está disponible
        if self.postgresql_handler and self.postgresql_handler.get_connection_status() == ConnectionStatus.CONNECTED:
            try:
                if self.postgresql_handler.write_legacy_sensor_record(data_dict):
                    success = True
                    self.logger.debug("✅ Datos insertados en PostgreSQL")
            except Exception as e:
                self.logger.error(f"❌ Error en PostgreSQL: {e}")
        
        # Insertar en InfluxDB si está disponible
        if self.influxdb_handler and self.influxdb_handler.get_connection_status() == ConnectionStatus.CONNECTED:
            try:
                if self.influxdb_handler.write_telemetry_point(data_dict):
                    success = True
                    self.logger.debug("✅ Datos insertados en InfluxDB")
            except Exception as e:
                self.logger.error(f"❌ Error en InfluxDB: {e}")
        
        if success:
            self.logger.info("✅ Datos de sensor insertados exitosamente")
        else:
            self.logger.error("❌ No se pudo insertar en ninguna base de datos")
        
        return success

    def insert_sensor_data(self, data_dict: Dict[str, Any]) -> bool:
        """Alias transicional preservado para api.py, ingestor y callers existentes."""
        return self.write_telemetry(data_dict)
    
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
    
    def get_session(self):
        """
        Obtener sesión de base de datos PostgreSQL
        
        Returns:
            Context manager para la sesión de base de datos
        """
        if not self.postgresql_handler:
            raise ConnectionError("PostgreSQL handler no está inicializado")
        
        return self.postgresql_handler.get_session()
    
    def is_connected(self) -> bool:
        """
        Verificar si hay conexión activa a la base de datos
        
        Returns:
            True si PostgreSQL está conectado, False en caso contrario
        """
        if self.postgresql_handler:
            return self.postgresql_handler.get_connection_status() == ConnectionStatus.CONNECTED
        return False
    
    def close(self):
        """Cerrar todas las conexiones"""
        if self.postgresql_handler:
            self.postgresql_handler.close()
        
        if self.influxdb_handler:
            self.influxdb_handler.close()
        
        self.logger.info("🔌 Todas las conexiones de base de datos cerradas")


# ============================================================================
# OFFICIAL RUNTIME INFRASTRUCTURE FACTORY
# ============================================================================

# Función de conveniencia para crear manejador de base de datos
def _resolve_database_configs(
    config: Optional[IoTMiddlewareConfig] = None,
    postgresql_config: Optional[PostgreSQLConfig] = None,
    influxdb_config: Optional[InfluxDBConfig] = None,
    storage_config: Optional[StorageConfig] = None,
) -> Tuple[PostgreSQLConfig, InfluxDBConfig, StorageConfig]:
    """Normaliza las variantes de configuración soportadas por el factory."""
    if config is not None:
        postgresql_config = config.postgresql
        influxdb_config = config.influxdb
        storage_config = config.storage

    if not all([postgresql_config, influxdb_config, storage_config]):
        raise ValueError(
            "Se requiere IoTMiddlewareConfig completo o postgresql_config, "
            "influxdb_config y storage_config explícitos"
        )

    return postgresql_config, influxdb_config, storage_config


def create_database_handler(
    config: Optional[IoTMiddlewareConfig] = None,
    postgresql_config: Optional[PostgreSQLConfig] = None,
    influxdb_config: Optional[InfluxDBConfig] = None,
    storage_config: Optional[StorageConfig] = None,
) -> DatabaseHandler:
    """
    Crear una instancia del manejador de base de datos
    
    Args:
        config: Configuración completa del middleware
        postgresql_config: Configuración de PostgreSQL
        influxdb_config: Configuración de InfluxDB
        storage_config: Configuración de almacenamiento
    
    Returns:
        Instancia del manejador de base de datos
    """
    resolved_postgresql, resolved_influxdb, resolved_storage = _resolve_database_configs(
        config=config,
        postgresql_config=postgresql_config,
        influxdb_config=influxdb_config,
        storage_config=storage_config,
    )

    return DatabaseHandler(resolved_postgresql, resolved_influxdb, resolved_storage)


def _resolve_runtime_config_path() -> Optional[str]:
    """Resuelve la ruta de configuración para lecturas runtime livianas."""
    config_path = (
        os.getenv("IOT_MW_CONFIG_PATH")
        or os.getenv("CONTROL_WORKER_CONFIG_PATH")
    )
    if config_path:
        return config_path

    repo_root = os.getenv("REPO_ROOT")
    if repo_root:
        candidate = os.path.join(repo_root, "config.yaml")
        if os.path.exists(candidate):
            return candidate

    return None


def _resolve_runtime_postgres_value(
    configured_value: Any,
    *,
    env_names: Tuple[str, ...],
    cast=None,
):
    """Permite que el runtime local sobrescriba PostgreSQL vía env vars."""
    for env_name in env_names:
        raw_value = os.getenv(env_name)
        if raw_value is None or str(raw_value).strip() == "":
            continue
        if cast is None:
            return raw_value
        return cast(raw_value)
    return configured_value


@lru_cache(maxsize=1)
def _get_control_settings_connection_url() -> str:
    """Construye una URL PostgreSQL cacheada para lecturas de feature flags."""
    try:
        from ..config import load_config
    except ImportError:
        from iot_middleware.config import load_config

    config = load_config(_resolve_runtime_config_path())
    postgres = config.postgresql
    host = _resolve_runtime_postgres_value(
        postgres.host,
        env_names=("DB_HOST", "POSTGRES_HOST"),
    )
    port = _resolve_runtime_postgres_value(
        postgres.port,
        env_names=("DB_PORT", "POSTGRES_PORT"),
        cast=int,
    )
    database = _resolve_runtime_postgres_value(
        postgres.database,
        env_names=("DB_NAME", "POSTGRES_DB"),
    )
    username = _resolve_runtime_postgres_value(
        postgres.username,
        env_names=("DB_USER", "POSTGRES_USER"),
    )
    password = _resolve_runtime_postgres_value(
        postgres.password,
        env_names=("DB_PASSWORD", "POSTGRES_PASSWORD"),
    )
    return (
        f"postgresql://{username}:{password}"
        f"@{host}:{port}/{database}"
    )


@lru_cache(maxsize=1)
def _get_control_settings_engine(connection_url: str):
    """Crea un engine liviano y reutilizable para lecturas runtime de proyectos."""
    from sqlalchemy import create_engine

    return create_engine(
        connection_url,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
        echo=False,
    )


@lru_cache(maxsize=1)
def _get_control_runtime_session_factory(connection_url: str):
    """Session factory reutilizable para lecturas/escrituras runtime livianas."""
    from sqlalchemy.orm import sessionmaker

    engine = _get_control_settings_engine(connection_url)
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_project_control_settings(project_id: str) -> Dict[str, Any]:
    """
    Return project-level control settings from the official operational-domain table.

    Safe default:
    parametric_control_enabled = False
    """
    default_settings = {
        "project_id": project_id,
        "parametric_control_enabled": False,
    }

    try:
        uuid.UUID(str(project_id))
    except (TypeError, ValueError):
        logger.warning(
            "project_id inválido para get_project_control_settings: %s",
            project_id,
        )
        return default_settings

    try:
        from sqlalchemy import text

        engine = _get_control_settings_engine(_get_control_settings_connection_url())
        query = text(
            """
            SELECT
                id::text AS project_id,
                COALESCE(parametric_control_enabled, FALSE) AS parametric_control_enabled
            FROM public.projects
            WHERE id = CAST(:project_id AS uuid)
            LIMIT 1
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {"project_id": str(project_id)},
            ).mappings().first()

        if not row:
            logger.info(
                "Proyecto no encontrado en public.projects para feature flag de control: %s",
                project_id,
            )
            return default_settings

        return {
            "project_id": row["project_id"],
            "parametric_control_enabled": bool(row["parametric_control_enabled"]),
        }

    except Exception as exc:
        logger.warning(
            "No se pudo leer parametric_control_enabled para project_id=%s: %s",
            project_id,
            exc,
        )
        return default_settings


def list_project_control_policies(project_id: str, variable_id: str) -> List[Dict[str, Any]]:
    """Carga políticas persistidas candidatas para un proyecto y variable."""
    try:
        project_uuid = str(uuid.UUID(str(project_id)))
    except (TypeError, ValueError):
        logger.warning(
            "project_id inválido para list_project_control_policies: %s",
            project_id,
        )
        return []

    if not variable_id or not str(variable_id).strip():
        logger.warning("variable_id inválido para list_project_control_policies: %s", variable_id)
        return []

    try:
        from sqlalchemy import text

        engine = _get_control_settings_engine(_get_control_settings_connection_url())
        query = text(
            """
            SELECT
                id::text AS id,
                project_id::text AS project_id,
                variable,
                context_selector,
                policy_type,
                params,
                priority,
                enabled,
                version,
                created_at,
                updated_at
            FROM public.project_control_policies
            WHERE project_id = CAST(:project_id AS uuid)
              AND variable = :variable
              AND enabled = TRUE
            ORDER BY priority DESC, version DESC, updated_at DESC, created_at DESC
            """
        )

        with engine.connect() as connection:
            rows = connection.execute(
                query,
                {
                    "project_id": project_uuid,
                    "variable": str(variable_id),
                },
            ).mappings().all()

        return [dict(row) for row in rows]
    except Exception as exc:
        logger.warning(
            "No se pudieron cargar project_control_policies project_id=%s variable=%s: %s",
            project_id,
            variable_id,
            exc,
        )
        return []


def _parse_runtime_audit_timestamp(raw_timestamp: Optional[Any]) -> datetime:
    """Normaliza timestamps ISO del worker para persistencia en auditoría."""
    if isinstance(raw_timestamp, datetime):
        return raw_timestamp.astimezone(timezone.utc)
    if isinstance(raw_timestamp, str) and raw_timestamp.strip():
        return datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00")).astimezone(timezone.utc)
    return datetime.now(timezone.utc)


def _json_safe_runtime_value(value: Any) -> Any:
    """Convierte payloads runtime a una estructura segura para JSONB."""
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, dict):
        return {key: _json_safe_runtime_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe_runtime_value(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe_runtime_value(item) for item in value]
    return value


def _merge_runtime_audit_persistence_metadata(
    audit_envelope: Dict[str, Any],
    persistence_metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """Actualiza la metadata de persistencia preservando compatibilidad del envelope."""
    safe_envelope = _json_safe_runtime_value(audit_envelope)
    payload = safe_envelope.setdefault("payload", {})
    delivery = payload.setdefault("delivery", {})

    current = delivery.get("audit_persistence")
    current = current if isinstance(current, dict) else {}
    delivery["audit_persistence"] = {
        **current,
        **_json_safe_runtime_value(persistence_metadata),
    }
    return safe_envelope


def persist_control_audit_record(
    audit_envelope: Dict[str, Any],
    *,
    action: str,
    entity: str = "control_engine_worker",
) -> Dict[str, Any]:
    """
    Persiste el audit envelope del worker en `iot_schema.auditoria`.

    Este helper reutiliza la infraestructura runtime liviana ya usada para
    feature flags y evita acoplar el worker a servicios de auditoría HTTP/UI.
    """
    try:
        from ..models.entities import Auditoria
    except ImportError:
        from iot_middleware.models.entities import Auditoria

    payload = audit_envelope.get("payload") if isinstance(audit_envelope, dict) else None
    payload = payload if isinstance(payload, dict) else {}

    project_id = (
        payload.get("project_id")
        or audit_envelope.get("project_id")
        or payload.get("input_event", {}).get("project_id")
    )
    variable_id = (
        payload.get("variable_id")
        or audit_envelope.get("variable")
        or payload.get("input_event", {}).get("variable")
    )
    event_id = (
        payload.get("event_id")
        or payload.get("input_event", {}).get("event_id")
    )
    timestamp = _parse_runtime_audit_timestamp(
        payload.get("evaluated_at")
        or audit_envelope.get("timestamp")
    )

    entity_id = None
    if project_id:
        try:
            entity_id = uuid.UUID(str(project_id))
        except (TypeError, ValueError):
            entity_id = None

    audit_context = {
        "source": "control_engine_worker",
        "action": action,
        "project_id": project_id,
        "variable_id": variable_id,
        "event_id": event_id,
        "message_type": audit_envelope.get("message_type"),
    }
    safe_audit_envelope = _json_safe_runtime_value(audit_envelope)
    attempted_at = (
        safe_audit_envelope.get("payload", {})
        .get("delivery", {})
        .get("audit_persistence", {})
        .get("attempted_at")
    )
    attempted_at = attempted_at or datetime.now(timezone.utc).isoformat()

    session_factory = _get_control_runtime_session_factory(_get_control_settings_connection_url())
    try:
        with session_factory() as session:
            record = Auditoria(
                usuario_id=None,
                entidad=entity,
                entidad_id=entity_id,
                accion=action,
                cambios=safe_audit_envelope,
                contexto={k: v for k, v in audit_context.items() if v is not None},
                ts=timestamp,
            )
            session.add(record)
            session.flush()

            completed_at = datetime.now(timezone.utc).isoformat()
            persistence_result = {
                "status": "persisted",
                "attempted": True,
                "backend": "postgresql",
                "store": "iot_schema.auditoria",
                "table": "iot_schema.auditoria",
                "action": action,
                "attempted_at": attempted_at,
                "completed_at": completed_at,
                "row_id": record.id,
                "rows_affected": 1,
            }
            record.cambios = _merge_runtime_audit_persistence_metadata(
                safe_audit_envelope,
                persistence_result,
            )
            session.commit()
            return persistence_result
    except Exception as exc:
        logger.warning("No se pudo persistir control audit action=%s: %s", action, exc)
        return {
            "status": "failed",
            "attempted": True,
            "backend": "postgresql",
            "store": "iot_schema.auditoria",
            "table": "iot_schema.auditoria",
            "action": action,
            "attempted_at": attempted_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "rows_affected": 0,
            "error": str(exc),
        }


# ============================================================================
# LEGACY BOOTSTRAP / COMPATIBILITY HELPERS
# ============================================================================

def _build_legacy_default_configs() -> Tuple[PostgreSQLConfig, InfluxDBConfig, StorageConfig]:
    """Construye configuración legacy por defecto para helpers de compatibilidad.

    Legacy boundary:
    estos defaults hardcodeados no deben considerarse parte del runtime oficial.
    """
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

    return default_postgresql_config, default_influxdb_config, default_storage_config


# Función principal insert_sensor_data para compatibilidad
def insert_sensor_data(data_dict: Dict[str, Any], **kwargs) -> bool:
    """
    Función principal para insertar datos de sensor (compatibilidad con código existente).

    Legacy boundary:
    usa configuración local hardcodeada y se conserva solo para callers viejos
    o pruebas manuales.
    
    Args:
        data_dict: Datos del sensor a insertar
        **kwargs: Argumentos adicionales
    
    Returns:
        True si la inserción fue exitosa, False en caso contrario
    """
    default_postgresql_config, default_influxdb_config, default_storage_config = _build_legacy_default_configs()
    
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
        # Crear configuración legacy por defecto para la demo manual del módulo.
        postgresql_config, influxdb_config, storage_config = _build_legacy_default_configs()
        
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
