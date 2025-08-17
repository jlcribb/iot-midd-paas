"""
Enums Nativos de PostgreSQL - IoT Middleware
============================================

Este archivo contiene todos los enums nativos de PostgreSQL
usando SQLAlchemy para mantener sincronización con la base de datos.
"""

from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy import Enum as SQLAlchemyEnum

# Enums nativos de PostgreSQL
class EstadoProyecto(SQLAlchemyEnum):
    """Enum para estados de proyectos"""
    __name__ = 'estado_proyecto'
    
    PLANIFICADO = 'planificado'
    ACTIVO = 'activo'
    PAUSADO = 'pausado'
    CERRADO = 'cerrado'
    CANCELADO = 'cancelado'

class ProtocoloComunicacion(SQLAlchemyEnum):
    """Enum para protocolos de comunicación"""
    __name__ = 'protocolo_comunicacion'
    
    MQTT = 'MQTT'
    BLE = 'BLE'
    HTTP = 'HTTP'
    RF = 'RF'
    LORA = 'LoRa'
    MODBUS = 'Modbus'
    OPC_UA = 'OPC_UA'
    OTRO = 'Otro'

class TipoDato(SQLAlchemyEnum):
    """Enum para tipos de datos de canales"""
    __name__ = 'tipo_dato'
    
    INT = 'int'
    FLOAT = 'float'
    BOOL = 'bool'
    STRING = 'string'
    JSON = 'json'
    BINARY = 'binary'
    TIMESTAMP = 'timestamp'

class RolSistema(SQLAlchemyEnum):
    """Enum para roles del sistema"""
    __name__ = 'rol_sistema'
    
    ADMIN = 'admin'
    TECNICO = 'tecnico'
    CLIENTE = 'cliente'
    LECTURA = 'lectura'
    SUPERVISOR = 'supervisor'

class CalidadDato(SQLAlchemyEnum):
    """Enum para calidad de datos (estándar OPC UA)"""
    __name__ = 'calidad_dato'
    
    OK = 'OK'
    GOOD = 'GOOD'
    UNCERTAIN = 'UNCERTAIN'
    BAD = 'BAD'
    SUSPECTO = 'SUSPECTO'
    MALO = 'MALO'

class SeveridadEvento(SQLAlchemyEnum):
    """Enum para severidad de eventos/alarmas"""
    __name__ = 'severidad_evento'
    
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'
    FATAL = 'fatal'

class EstadoDispositivo(SQLAlchemyEnum):
    """Enum para estados de dispositivos"""
    __name__ = 'estado_dispositivo'
    
    ACTIVO = 'activo'
    INACTIVO = 'inactivo'
    MANTENIMIENTO = 'mantenimiento'
    ERROR = 'error'
    DESCONECTADO = 'desconectado'

# Función helper para crear enums nativos de PostgreSQL
def create_postgresql_enum(enum_class, schema='iot_schema'):
    """
    Crea un enum nativo de PostgreSQL usando SQLAlchemy
    
    Args:
        enum_class: Clase enum de SQLAlchemy
        schema: Esquema de la base de datos
    
    Returns:
        ENUM de PostgreSQL configurado
    """
    # Obtener los valores del enum
    enum_values = []
    for attr_name in dir(enum_class):
        if not attr_name.startswith('_') and attr_name.isupper():
            attr_value = getattr(enum_class, attr_name)
            if not callable(attr_value):
                enum_values.append(attr_value)
    
    return ENUM(
        *enum_values,
        name=enum_class.__name__,
        schema=schema,
        create_type=False,  # No crear automáticamente, usar Alembic
        native_enum=True    # Usar enum nativo de PostgreSQL
    )
