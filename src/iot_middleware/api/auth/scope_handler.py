"""
Manejador de Scope para Filtrado Automático
==========================================

Este módulo maneja el filtrado automático de consultas basado en el scope
del usuario autenticado (cliente_id, proyecto_id, unidad_id).
"""

from typing import Dict, Any, Optional, List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
import logging

from ...models.entities import Usuario, Cliente, Proyecto, UnidadProyecto
from ...models.enums import RolUsuario

# Configurar logging
logger = logging.getLogger(__name__)


class ScopeHandler:
    """
    Manejador de scope para filtrado automático de consultas
    """
    
    def __init__(self):
        """Inicializar manejador de scope"""
        pass
    
    def get_user_scope(self, usuario: Usuario) -> Dict[str, Any]:
        """
        Obtener scope completo del usuario
        
        Args:
            usuario: Usuario autenticado
            
        Returns:
            Diccionario con información del scope del usuario
        """
        try:
            scope = {
                'user_id': str(usuario.id),
                'rol': usuario.rol,
                'cliente_id': str(usuario.cliente_id) if usuario.cliente_id else None,
                'proyecto_id': str(usuario.proyecto_id) if usuario.proyecto_id else None,
                'unidad_id': str(usuario.unidad_id) if usuario.unidad_id else None,
                'restrictions': []
            }
            
            # Determinar restricciones según el rol
            if usuario.rol == RolUsuario.ADMIN:
                scope['restrictions'] = ['none']
                scope['description'] = 'Acceso completo a todos los recursos'
            elif usuario.rol == RolUsuario.TECNICO:
                scope['restrictions'] = ['none']
                scope['description'] = 'Acceso completo a todos los recursos'
            elif usuario.rol == RolUsuario.CLIENTE:
                if usuario.cliente_id:
                    scope['restrictions'].append('cliente_scope')
                if usuario.proyecto_id:
                    scope['restrictions'].append('proyecto_scope')
                if usuario.unidad_id:
                    scope['restrictions'].append('unidad_scope')
                scope['description'] = 'Acceso limitado a recursos del cliente/proyecto/unidad'
            elif usuario.rol == RolUsuario.LECTURA:
                if usuario.cliente_id:
                    scope['restrictions'].append('cliente_scope')
                if usuario.proyecto_id:
                    scope['restrictions'].append('proyecto_scope')
                if usuario.unidad_id:
                    scope['restrictions'].append('unidad_scope')
                scope['restrictions'].append('read_only')
                scope['description'] = 'Solo lectura de recursos del cliente/proyecto/unidad'
            
            return scope
            
        except Exception as e:
            logger.error(f"Error al obtener scope del usuario {usuario.id}: {e}")
            return {}
    
    def apply_client_scope(self, query: select, usuario: Usuario, table_alias: Any) -> select:
        """
        Aplicar scope de cliente a una consulta
        
        Args:
            query: Consulta SQLAlchemy
            usuario: Usuario autenticado
            table_alias: Alias de la tabla principal
            
        Returns:
            Consulta con scope aplicado
        """
        try:
            if not usuario.cliente_id:
                return query
            
            # Aplicar filtro de cliente_id si la tabla lo tiene
            if hasattr(table_alias, 'cliente_id'):
                query = query.where(table_alias.cliente_id == usuario.cliente_id)
                logger.debug(f"Scope de cliente aplicado: {usuario.cliente_id}")
            
            return query
            
        except Exception as e:
            logger.error(f"Error al aplicar scope de cliente: {e}")
            return query
    
    def apply_project_scope(self, query: select, usuario: Usuario, table_alias: Any) -> select:
        """
        Aplicar scope de proyecto a una consulta
        
        Args:
            query: Consulta SQLAlchemy
            usuario: Usuario autenticado
            table_alias: Alias de la tabla principal
            
        Returns:
            Consulta con scope aplicado
        """
        try:
            if not usuario.proyecto_id:
                return query
            
            # Aplicar filtro de proyecto_id si la tabla lo tiene
            if hasattr(table_alias, 'proyecto_id'):
                query = query.where(table_alias.proyecto_id == usuario.proyecto_id)
                logger.debug(f"Scope de proyecto aplicado: {usuario.proyecto_id}")
            
            return query
            
        except Exception as e:
            logger.error(f"Error al aplicar scope de proyecto: {e}")
            return query
    
    def apply_unit_scope(self, query: select, usuario: Usuario, table_alias: Any) -> select:
        """
        Aplicar scope de unidad a una consulta
        
        Args:
            query: Consulta SQLAlchemy
            usuario: Usuario autenticado
            table_alias: Alias de la tabla principal
            
        Returns:
            Consulta con scope aplicado
        """
        try:
            if not usuario.unidad_id:
                return query
            
            # Aplicar filtro de unidad_id si la tabla lo tiene
            if hasattr(table_alias, 'unidad_id'):
                query = query.where(table_alias.unidad_id == usuario.unidad_id)
                logger.debug(f"Scope de unidad aplicado: {usuario.unidad_id}")
            
            return query
            
        except Exception as e:
            logger.error(f"Error al aplicar scope de unidad: {e}")
            return query
    
    def apply_full_scope(self, query: select, usuario: Usuario, table_alias: Any) -> select:
        """
        Aplicar scope completo a una consulta
        
        Args:
            query: Consulta SQLAlchemy
            usuario: Usuario autenticado
            table_alias: Alias de la tabla principal
            
        Returns:
            Consulta con scope completo aplicado
        """
        try:
            # Administradores y técnicos no tienen restricciones
            if usuario.rol in [RolUsuario.ADMIN, RolUsuario.TECNICO]:
                return query
            
            # Aplicar scope según el rol del usuario
            if usuario.rol == RolUsuario.CLIENTE:
                query = self.apply_client_scope(query, usuario, table_alias)
                query = self.apply_project_scope(query, usuario, table_alias)
                query = self.apply_unit_scope(query, usuario, table_alias)
            
            elif usuario.rol == RolUsuario.LECTURA:
                query = self.apply_client_scope(query, usuario, table_alias)
                query = self.apply_project_scope(query, usuario, table_alias)
                query = self.apply_unit_scope(query, usuario, table_alias)
            
            return query
            
        except Exception as e:
            logger.error(f"Error al aplicar scope completo: {e}")
            return query
    
    def get_scope_filters(self, usuario: Usuario) -> Dict[str, Any]:
        """
        Obtener filtros de scope como diccionario
        
        Args:
            usuario: Usuario autenticado
            
        Returns:
            Diccionario con filtros de scope
        """
        try:
            filters = {}
            
            # Administradores y técnicos no tienen restricciones
            if usuario.rol in [RolUsuario.ADMIN, RolUsuario.TECNICO]:
                return filters
            
            # Aplicar filtros según el rol
            if usuario.rol in [RolUsuario.CLIENTE, RolUsuario.LECTURA]:
                if usuario.cliente_id:
                    filters['cliente_id'] = str(usuario.cliente_id)
                if usuario.proyecto_id:
                    filters['proyecto_id'] = str(usuario.proyecto_id)
                if usuario.unidad_id:
                    filters['unidad_id'] = str(usuario.unidad_id)
            
            return filters
            
        except Exception as e:
            logger.error(f"Error al obtener filtros de scope: {e}")
            return {}
    
    def apply_scope_to_filters(self, base_filters: Dict[str, Any], usuario: Usuario) -> Dict[str, Any]:
        """
        Aplicar filtros de scope a filtros existentes
        
        Args:
            base_filters: Filtros base de la consulta
            usuario: Usuario autenticado
            
        Returns:
            Filtros combinados con scope aplicado
        """
        try:
            scope_filters = self.get_scope_filters(usuario)
            
            # Combinar filtros
            combined_filters = base_filters.copy()
            combined_filters.update(scope_filters)
            
            logger.debug(f"Filtros de scope aplicados: {scope_filters}")
            return combined_filters
            
        except Exception as e:
            logger.error(f"Error al aplicar scope a filtros: {e}")
            return base_filters
    
    def validate_resource_access(self, usuario: Usuario, resource_data: Dict[str, Any]) -> bool:
        """
        Validar si un usuario puede acceder a un recurso específico
        
        Args:
            usuario: Usuario autenticado
            resource_data: Datos del recurso a validar
            
        Returns:
            True si el usuario puede acceder al recurso
        """
        try:
            # Administradores y técnicos pueden acceder a todo
            if usuario.rol in [RolUsuario.ADMIN, RolUsuario.TECNICO]:
                return True
            
            # Validar acceso según el rol
            if usuario.rol in [RolUsuario.CLIENTE, RolUsuario.LECTURA]:
                # Verificar cliente_id
                if usuario.cliente_id and 'cliente_id' in resource_data:
                    if str(usuario.cliente_id) != str(resource_data['cliente_id']):
                        return False
                
                # Verificar proyecto_id
                if usuario.proyecto_id and 'proyecto_id' in resource_data:
                    if str(usuario.proyecto_id) != str(resource_data['proyecto_id']):
                        return False
                
                # Verificar unidad_id
                if usuario.unidad_id and 'unidad_id' in resource_data:
                    if str(usuario.unidad_id) != str(resource_data['unidad_id']):
                        return False
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error al validar acceso al recurso: {e}")
            return False
    
    def get_user_accessible_projects(self, usuario: Usuario, session: Session) -> List[str]:
        """
        Obtener lista de proyectos a los que puede acceder un usuario
        
        Args:
            usuario: Usuario autenticado
            session: Sesión de base de datos
            
        Returns:
            Lista de IDs de proyectos accesibles
        """
        try:
            # Administradores y técnicos pueden acceder a todos los proyectos
            if usuario.rol in [RolUsuario.ADMIN, RolUsuario.TECNICO]:
                proyectos = session.query(Proyecto.id).all()
                return [str(p.id) for p in proyectos]
            
            # Clientes y usuarios de lectura solo pueden acceder a sus proyectos
            if usuario.rol in [RolUsuario.CLIENTE, RolUsuario.LECTURA]:
                if usuario.proyecto_id:
                    return [str(usuario.proyecto_id)]
                elif usuario.cliente_id:
                    # Obtener proyectos del cliente
                    proyectos = session.query(Proyecto.id).filter(
                        Proyecto.cliente_id == usuario.cliente_id
                    ).all()
                    return [str(p.id) for p in proyectos]
            
            return []
            
        except Exception as e:
            logger.error(f"Error al obtener proyectos accesibles: {e}")
            return []
    
    def get_user_accessible_clients(self, usuario: Usuario, session: Session) -> List[str]:
        """
        Obtener lista de clientes a los que puede acceder un usuario
        
        Args:
            usuario: Usuario autenticado
            session: Sesión de base de datos
            
        Returns:
            Lista de IDs de clientes accesibles
        """
        try:
            # Administradores y técnicos pueden acceder a todos los clientes
            if usuario.rol in [RolUsuario.ADMIN, RolUsuario.TECNICO]:
                clientes = session.query(Cliente.id).all()
                return [str(c.id) for c in clientes]
            
            # Clientes y usuarios de lectura solo pueden acceder a su propio cliente
            if usuario.rol in [RolUsuario.CLIENTE, RolUsuario.LECTURA]:
                if usuario.cliente_id:
                    return [str(usuario.cliente_id)]
            
            return []
            
        except Exception as e:
            logger.error(f"Error al obtener clientes accesibles: {e}")
            return []
