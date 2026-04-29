"""
Enums Nativos de PostgreSQL - IoT Middleware
============================================

Este archivo contiene todos los enums nativos de PostgreSQL
usando SQLAlchemy para mantener sincronización con la base de datos.
"""

from enum import Enum as PyEnum
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

# Enum de Python estándar para uso con Pydantic
class RolSistemaPy(PyEnum):
    """Enum de Python para roles del sistema (compatible con Pydantic)"""
    ADMIN = 'admin'
    TECNICO = 'tecnico'
    CLIENTE = 'cliente'
    LECTURA = 'lectura'
    SUPERVISOR = 'supervisor'

# Enum de SQLAlchemy para base de datos
class RolSistema(SQLAlchemyEnum):
    """Enum para roles del sistema (SQLAlchemy)"""
    __name__ = 'rol_sistema'
    
    ADMIN = 'admin'
    TECNICO = 'tecnico'
    CLIENTE = 'cliente'
    LECTURA = 'lectura'
    SUPERVISOR = 'supervisor'

# Alias para compatibilidad: usar el enum de Python para Pydantic
RolUsuario = RolSistemaPy

# Función helper para convertir entre enums
def rol_to_pydantic(rol_value):
    """Convierte un valor de RolSistema (SQLAlchemy) a RolUsuario (Pydantic)"""
    if rol_value is None:
        return None
    # Si ya es un enum de Python, retornarlo
    if isinstance(rol_value, RolSistemaPy):
        return rol_value
    # Si es un SQLAlchemyEnum, obtener su valor
    if hasattr(rol_value, 'value'):
        value = rol_value.value
    else:
        value = rol_value
    # Convertir a enum de Python
    return RolSistemaPy(value)

def rol_from_pydantic(rol_value):
    """Convierte un valor de RolUsuario (Pydantic) a RolSistema (SQLAlchemy)"""
    if rol_value is None:
        return None
    # Si ya es un SQLAlchemyEnum, retornarlo
    if isinstance(rol_value, RolSistema):
        return rol_value
    # Si es un enum de Python, obtener su valor
    if isinstance(rol_value, RolSistemaPy):
        value = rol_value.value
    else:
        value = rol_value
    # Retornar el valor string (SQLAlchemy lo manejará)
    return value

# Enum de Python estándar para uso con Pydantic
class CalidadDatoPy(PyEnum):
    """Enum de Python para calidad de datos (compatible con Pydantic)"""
    OK = 'OK'
    GOOD = 'GOOD'
    UNCERTAIN = 'UNCERTAIN'
    BAD = 'BAD'
    SUSPECTO = 'SUSPECTO'
    MALO = 'MALO'

# Enum de SQLAlchemy para base de datos
class CalidadDato(SQLAlchemyEnum):
    """Enum para calidad de datos (estándar OPC UA)"""
    __name__ = 'calidad_dato'
    
    OK = 'OK'
    GOOD = 'GOOD'
    UNCERTAIN = 'UNCERTAIN'
    BAD = 'BAD'
    SUSPECTO = 'SUSPECTO'
    MALO = 'MALO'

# Función helper para convertir CalidadDato
def calidad_to_pydantic(calidad_value):
    """Convierte un valor de CalidadDato (SQLAlchemy) a CalidadDatoPy (Pydantic)"""
    if calidad_value is None:
        return None
    if isinstance(calidad_value, CalidadDatoPy):
        return calidad_value
    if hasattr(calidad_value, 'value'):
        value = calidad_value.value
    else:
        value = calidad_value
    return CalidadDatoPy(value)

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
