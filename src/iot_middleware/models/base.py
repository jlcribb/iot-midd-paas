"""
Configuración Base de SQLAlchemy - IoT Middleware
================================================

Este archivo contiene la configuración base de SQLAlchemy
y la clase Base para todos los modelos.
"""

from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData
import uuid

# Configuración de metadatos para PostgreSQL
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

# Clase base para todos los modelos
Base = declarative_base(metadata=metadata)

# Función helper para generar UUIDs
def generate_uuid():
    """Genera un UUID v4 para usar como valor por defecto"""
    return uuid.uuid4()

# Función helper para UUID con uuid_generate_v4() de PostgreSQL
def uuid_generate_v4():
    """Retorna la función uuid_generate_v4() de PostgreSQL"""
    return uuid.uuid4()
