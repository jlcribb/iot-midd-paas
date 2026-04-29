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
from .canal_repository import CanalRepository
from .registro_datos_repository import RegistroDatosRepository

# Repositorios opcionales (crear cuando se necesiten)
try:
    from .sesion_repository import SesionRepository
except ImportError:
    SesionRepository = None

try:
    from .dispositivo_repository import DispositivoRepository
except ImportError:
    DispositivoRepository = None

try:
    from .dispositivo_proyecto_repository import DispositivoProyectoRepository
except ImportError:
    DispositivoProyectoRepository = None

try:
    from .evento_alarma_repository import EventoAlarmaRepository
except ImportError:
    EventoAlarmaRepository = None

try:
    from .config_middleware_repository import ConfigMiddlewareRepository
except ImportError:
    ConfigMiddlewareRepository = None

__all__ = [
    'BaseRepository',
    'ClienteRepository',
    'ProyectoRepository',
    'UnidadProyectoRepository',
    'CanalRepository',
    'RegistroDatosRepository',
]

# Agregar repositorios opcionales si existen
if SesionRepository is not None:
    __all__.append('SesionRepository')
if DispositivoRepository is not None:
    __all__.append('DispositivoRepository')
if DispositivoProyectoRepository is not None:
    __all__.append('DispositivoProyectoRepository')
if EventoAlarmaRepository is not None:
    __all__.append('EventoAlarmaRepository')
if ConfigMiddlewareRepository is not None:
    __all__.append('ConfigMiddlewareRepository')
