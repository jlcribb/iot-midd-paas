"""
Módulo de Modelos SQLAlchemy - IoT Middleware
============================================

Este módulo contiene todos los modelos SQLAlchemy que reflejan
la estructura de la base de datos PostgreSQL del sistema IoT Middleware.
"""

from .base import Base
from .enums import (
    EstadoProyecto,
    ProtocoloComunicacion,
    TipoDato,
    RolSistema,
    RolUsuario,  # Alias para compatibilidad
    CalidadDato,
    CalidadDatoPy,  # Versión Python para Pydantic
    SeveridadEvento,
    EstadoDispositivo
)
from .entities import (
    Cliente,
    Proyecto,
    UnidadProyecto,
    Sesion,
    Dispositivo,
    DispositivoProyecto,
    Canal,
    RegistroDatos,
    EventoAlarma,
    Usuario,
    UsuarioScope,
    ConfigMiddleware,
    Auditoria
)

__all__ = [
    'Base',
    'EstadoProyecto',
    'ProtocoloComunicacion', 
    'TipoDato',
    'RolSistema',
    'RolUsuario',  # Alias para compatibilidad
    'CalidadDato',
    'CalidadDatoPy',  # Versión Python para Pydantic
    'SeveridadEvento',
    'EstadoDispositivo',
    'Cliente',
    'Proyecto',
    'UnidadProyecto',
    'Sesion',
    'Dispositivo',
    'DispositivoProyecto',
    'Canal',
    'RegistroDatos',
    'EventoAlarma',
    'Usuario',
    'UsuarioScope',
    'ConfigMiddleware',
    'Auditoria'
]
