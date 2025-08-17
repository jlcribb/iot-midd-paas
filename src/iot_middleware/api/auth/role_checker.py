"""
Verificador de Roles para Autorización
======================================

Este módulo implementa la verificación de roles y permisos
para controlar el acceso a diferentes funcionalidades de la API.
"""

from typing import List, Optional, Callable
from functools import wraps
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer
import logging

from ...models.entities import Usuario
from ...models.enums import RolUsuario
from .auth_middleware import AuthMiddleware

# Configurar logging
logger = logging.getLogger(__name__)

# Esquema de autenticación HTTP Bearer
security = HTTPBearer()


class RoleChecker:
    """
    Verificador de roles y permisos para autorización
    """
    
    def __init__(self, auth_middleware: AuthMiddleware):
        """
        Inicializar verificador de roles
        
        Args:
            auth_middleware: Middleware de autenticación
        """
        self.auth_middleware = auth_middleware
    
    def require_roles(self, allowed_roles: List[RolUsuario]):
        """
        Decorador para requerir roles específicos
        
        Args:
            allowed_roles: Lista de roles permitidos
            
        Returns:
            Función decoradora
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Obtener usuario del request
                request = kwargs.get('request')
                if not request:
                    # Buscar en argumentos posicionales
                    for arg in args:
                        if hasattr(arg, 'headers'):
                            request = arg
                            break
                
                if not request:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="No se pudo obtener el request"
                    )
                
                # Obtener usuario autenticado
                usuario = await self.auth_middleware.get_current_active_user(request)
                
                # Verificar rol
                if usuario.rol not in allowed_roles:
                    logger.warning(f"Usuario {usuario.email} con rol {usuario.rol} intentó acceder a endpoint que requiere roles: {allowed_roles}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Acceso denegado. Se requieren roles: {[r.value for r in allowed_roles]}"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_admin(self):
        """
        Decorador para requerir rol de administrador
        
        Returns:
            Función decoradora
        """
        return self.require_roles([RolUsuario.ADMIN])
    
    def require_tecnico_or_admin(self):
        """
        Decorador para requerir rol de técnico o administrador
        
        Returns:
            Función decoradora
        """
        return self.require_roles([RolUsuario.ADMIN, RolUsuario.TECNICO])
    
    def require_cliente_or_above(self):
        """
        Decorador para requerir rol de cliente o superior
        
        Returns:
            Función decoradora
        """
        return self.require_roles([RolUsuario.ADMIN, RolUsuario.TECNICO, RolUsuario.CLIENTE])
    
    def require_lectura_or_above(self):
        """
        Decorador para requerir rol de lectura o superior
        
        Returns:
            Función decoradora
        """
        return self.require_roles([RolUsuario.ADMIN, RolUsuario.TECNICO, RolUsuario.CLIENTE, RolUsuario.LECTURA])
    
    def check_permission(self, usuario: Usuario, required_permission: str, resource_id: Optional[str] = None) -> bool:
        """
        Verificar si un usuario tiene un permiso específico
        
        Args:
            usuario: Usuario a verificar
            required_permission: Permiso requerido
            resource_id: ID del recurso (opcional)
            
        Returns:
            True si el usuario tiene el permiso
        """
        try:
            # Administradores tienen todos los permisos
            if usuario.rol == RolUsuario.ADMIN:
                return True
            
            # Verificar permisos según el rol
            if required_permission == "users_management":
                # Solo administradores pueden gestionar usuarios
                return usuario.rol == RolUsuario.ADMIN
            
            elif required_permission == "roles_management":
                # Solo administradores pueden gestionar roles
                return usuario.rol == RolUsuario.ADMIN
            
            elif required_permission == "system_config":
                # Solo administradores y técnicos pueden configurar el sistema
                return usuario.rol in [RolUsuario.ADMIN, RolUsuario.TECNICO]
            
            elif required_permission == "project_management":
                # Administradores y técnicos pueden gestionar todos los proyectos
                if usuario.rol in [RolUsuario.ADMIN, RolUsuario.TECNICO]:
                    return True
                # Clientes solo pueden gestionar sus propios proyectos
                elif usuario.rol == RolUsuario.CLIENTE:
                    return resource_id and str(usuario.cliente_id) == resource_id
                return False
            
            elif required_permission == "client_management":
                # Administradores y técnicos pueden gestionar todos los clientes
                if usuario.rol in [RolUsuario.ADMIN, RolUsuario.TECNICO]:
                    return True
                # Clientes solo pueden ver su propia información
                elif usuario.rol == RolUsuario.CLIENTE:
                    return resource_id and str(usuario.cliente_id) == resource_id
                return False
            
            elif required_permission == "data_read":
                # Todos los roles pueden leer datos
                return True
            
            elif required_permission == "data_write":
                # Solo administradores, técnicos y clientes pueden escribir datos
                return usuario.rol in [RolUsuario.ADMIN, RolUsuario.TECNICO, RolUsuario.CLIENTE]
            
            elif required_permission == "session_management":
                # Administradores y técnicos pueden gestionar todas las sesiones
                if usuario.rol in [RolUsuario.ADMIN, RolUsuario.TECNICO]:
                    return True
                # Clientes solo pueden gestionar sus propias sesiones
                elif usuario.rol == RolUsuario.CLIENTE:
                    return resource_id and str(usuario.cliente_id) == resource_id
                return False
            
            elif required_permission == "event_management":
                # Administradores y técnicos pueden gestionar todos los eventos
                if usuario.rol in [RolUsuario.ADMIN, RolUsuario.TECNICO]:
                    return True
                # Clientes solo pueden gestionar eventos de sus proyectos
                elif usuario.rol == RolUsuario.CLIENTE:
                    return resource_id and str(usuario.proyecto_id) == resource_id
                return False
            
            # Por defecto, denegar acceso
            return False
            
        except Exception as e:
            logger.error(f"Error al verificar permiso {required_permission} para usuario {usuario.id}: {e}")
            return False
    
    def require_permission(self, permission: str):
        """
        Decorador para requerir un permiso específico
        
        Args:
            permission: Permiso requerido
            
        Returns:
            Función decoradora
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Obtener usuario del request
                request = kwargs.get('request')
                if not request:
                    # Buscar en argumentos posicionales
                    for arg in args:
                        if hasattr(arg, 'headers'):
                            request = arg
                            break
                
                if not request:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="No se pudo obtener el request"
                    )
                
                # Obtener usuario autenticado
                usuario = await self.auth_middleware.get_current_active_user(request)
                
                # Obtener resource_id si está disponible
                resource_id = kwargs.get('resource_id') or kwargs.get('id')
                
                # Verificar permiso
                if not self.check_permission(usuario, permission, resource_id):
                    logger.warning(f"Usuario {usuario.email} con rol {usuario.rol} intentó acceder a recurso que requiere permiso: {permission}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Acceso denegado. Se requiere permiso: {permission}"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_user_scope_filters(self, usuario: Usuario) -> dict:
        """
        Obtener filtros de scope basados en el rol del usuario
        
        Args:
            usuario: Usuario autenticado
            
        Returns:
            Diccionario con filtros de scope
        """
        try:
            scope_filters = {}
            
            # Administradores y técnicos no tienen restricciones de scope
            if usuario.rol in [RolUsuario.ADMIN, RolUsuario.TECNICO]:
                return scope_filters
            
            # Clientes solo pueden acceder a sus propios recursos
            if usuario.rol == RolUsuario.CLIENTE:
                if usuario.cliente_id:
                    scope_filters['cliente_id'] = str(usuario.cliente_id)
                if usuario.proyecto_id:
                    scope_filters['proyecto_id'] = str(usuario.proyecto_id)
                if usuario.unidad_id:
                    scope_filters['unidad_id'] = str(usuario.unidad_id)
            
            # Usuarios de solo lectura tienen las mismas restricciones que los clientes
            elif usuario.rol == RolUsuario.LECTURA:
                if usuario.cliente_id:
                    scope_filters['cliente_id'] = str(usuario.cliente_id)
                if usuario.proyecto_id:
                    scope_filters['proyecto_id'] = str(usuario.proyecto_id)
                if usuario.unidad_id:
                    scope_filters['unidad_id'] = str(usuario.unidad_id)
            
            return scope_filters
            
        except Exception as e:
            logger.error(f"Error al obtener filtros de scope para usuario {usuario.id}: {e}")
            return {}
    
    def apply_scope_filters(self, query_filters: dict, usuario: Usuario) -> dict:
        """
        Aplicar filtros de scope a las consultas existentes
        
        Args:
            query_filters: Filtros de consulta existentes
            usuario: Usuario autenticado
            
        Returns:
            Filtros de consulta con scope aplicado
        """
        try:
            scope_filters = self.get_user_scope_filters(usuario)
            
            # Combinar filtros existentes con filtros de scope
            combined_filters = query_filters.copy()
            combined_filters.update(scope_filters)
            
            logger.debug(f"Filtros de scope aplicados para usuario {usuario.id}: {scope_filters}")
            return combined_filters
            
        except Exception as e:
            logger.error(f"Error al aplicar filtros de scope: {e}")
            return query_filters
