"""
Routers de la API FastAPI
=========================

Este paquete contiene todos los routers de la API del IoT Middleware,
organizados por funcionalidad y con control de acceso basado en roles.
"""

from .auth_router import auth_router
from .projects_router import projects_router
from .data_router import data_router
from .events_router import events_router
from .admin_router import admin_router

__all__ = [
    'auth_router',
    'projects_router',
    'data_router',
    'events_router',
    'admin_router',
]
