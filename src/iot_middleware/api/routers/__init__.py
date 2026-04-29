"""
Routers de la API FastAPI legacy.

Estado actual del runtime:

- Activo en `src/iot_middleware/api/api.py`:
  - `dashboard_router`
- Dormant / no montado en el runtime efectivo actual:
  - `auth_router`
  - `projects_router`
  - `data_router`
  - `events_router`

Estos routers se conservan por trazabilidad y compatibilidad transicional,
pero no forman parte de la superficie activa del contenedor `api`.
"""

from .auth_router import auth_router
from .projects_router import projects_router
from .data_router import data_router
from .events_router import events_router
from . import dashboard_router

ACTIVE_RUNTIME_ROUTERS = ("dashboard_router",)
DORMANT_LEGACY_ROUTERS = (
    "auth_router",
    "projects_router",
    "data_router",
    "events_router",
)

# Router de administración (opcional)
try:
    from .admin_router import admin_router
except ImportError:
    admin_router = None

__all__ = [
    'ACTIVE_RUNTIME_ROUTERS',
    'DORMANT_LEGACY_ROUTERS',
    'auth_router',
    'projects_router',
    'data_router',
    'events_router',
    'dashboard_router',
]

# Agregar admin_router si existe
if admin_router is not None:
    __all__.append('admin_router')
