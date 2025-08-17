"""
Módulo de Autenticación y Autorización
======================================

Este paquete maneja la autenticación JWT y autorización por roles
para el sistema IoT Middleware.
"""

from .jwt_handler import JWTHandler
from .auth_middleware import AuthMiddleware
from .role_checker import RoleChecker
from .scope_handler import ScopeHandler

__all__ = [
    'JWTHandler',
    'AuthMiddleware', 
    'RoleChecker',
    'ScopeHandler',
]
