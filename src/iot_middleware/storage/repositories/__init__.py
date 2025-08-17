"""
Repositorios CRUD para el sistema IoT Middleware
================================================

Este paquete contiene los repositorios para todas las entidades del sistema,
incluyendo validación de tipos y lógica de negocio para registros_datos.
"""

from .base_repository import BaseRepository
from .cliente_repository import ClienteRepository
from .proyecto_repository import ProyectoRepository
from .unidad_proyecto_repository import UnidadProyectoRepository
from .sesion_repository import SesionRepository
from .dispositivo_repository import DispositivoRepository
from .dispositivo_proyecto_repository import DispositivoProyectoRepository
from .canal_repository import CanalRepository
from .evento_alarma_repository import EventoAlarmaRepository
from .config_middleware_repository import ConfigMiddlewareRepository
from .registro_datos_repository import RegistroDatosRepository

__all__ = [
    'BaseRepository',
    'ClienteRepository',
    'ProyectoRepository',
    'UnidadProyectoRepository',
    'SesionRepository',
    'DispositivoRepository',
    'DispositivoProyectoRepository',
    'CanalRepository',
    'EventoAlarmaRepository',
    'ConfigMiddlewareRepository',
    'RegistroDatosRepository',
]
