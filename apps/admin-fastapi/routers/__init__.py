"""
Routers para la interfaz de administración
"""

from . import admin_router
from . import proyectos_router
from . import unidades_router
from . import dispositivos_router
from . import usuarios_router
from . import dashboard_router
from . import core_router

__all__ = [
    'admin_router',
    'proyectos_router',
    'unidades_router',
    'dispositivos_router',
    'usuarios_router',
    'dashboard_router',
    'core_router'
]
