"""
Repositorio para Unidades de Proyecto
=====================================

Este módulo maneja las operaciones CRUD específicas para unidades de proyecto,
incluyendo búsquedas por proyecto y ubicación.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy import select, and_, or_
from sqlalchemy.exc import SQLAlchemyError
import logging

from .base_repository import BaseRepository
from ...models.entities import UnidadProyecto, Proyecto

# Configurar logging
logger = logging.getLogger(__name__)


class UnidadProyectoRepository(BaseRepository[UnidadProyecto]):
    """
    Repositorio para unidades de proyecto con métodos especializados
    """
    
    def __init__(self, db_handler):
        super().__init__(db_handler, UnidadProyecto)
    
    def get_by_proyecto(self, proyecto_id: str) -> List[UnidadProyecto]:
        """
        Obtener unidades por proyecto
        
        Args:
            proyecto_id: ID del proyecto
            
        Returns:
            Lista de unidades del proyecto
        """
        return self.find_by_criteria({'proyecto_id': proyecto_id})
    
    def get_by_ubicacion(self, ubicacion: str) -> List[UnidadProyecto]:
        """
        Obtener unidades por ubicación
        
        Args:
            ubicacion: Ubicación de la unidad
            
        Returns:
            Lista de unidades en la ubicación
        """
        return self.find_by_criteria({'ubicacion': ubicacion})
    
    def get_active_units(self) -> List[UnidadProyecto]:
        """
        Obtener solo unidades activas
        
        Returns:
            Lista de unidades activas
        """
        return self.find_by_criteria({'activo': True})
    
    def search_units(self, search_term: str) -> List[UnidadProyecto]:
        """
        Buscar unidades por término de búsqueda
        
        Args:
            search_term: Término de búsqueda
            
        Returns:
            Lista de unidades que coinciden
        """
        try:
            with self.db.get_session() as session:
                search_pattern = f"%{search_term}%"
                query = select(UnidadProyecto).where(
                    or_(
                        UnidadProyecto.nombre.ilike(search_pattern),
                        UnidadProyecto.ubicacion.ilike(search_pattern),
                        UnidadProyecto.responsable.ilike(search_pattern)
                    )
                )
                
                result = session.execute(query)
                units = result.scalars().all()
                
                logger.debug(f"Búsqueda '{search_term}' retornó {len(units)} unidades")
                return units
                
        except SQLAlchemyError as e:
            logger.error(f"Error en búsqueda de unidades: {e}")
            return []
    
    def get_units_by_proyecto(self, proyecto_id: str) -> List[UnidadProyecto]:
        """
        Obtener todas las unidades de un proyecto
        
        Args:
            proyecto_id: ID del proyecto
            
        Returns:
            Lista de unidades del proyecto
        """
        return self.get_by_proyecto(proyecto_id)
    
    def update_unit_status(self, unidad_id: str, activo: bool) -> bool:
        """
        Actualizar el estado activo/inactivo de una unidad
        
        Args:
            unidad_id: ID de la unidad
            activo: Nuevo estado
            
        Returns:
            True si se actualizó exitosamente
        """
        return self.update(unidad_id, {'activo': activo}) is not None
