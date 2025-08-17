"""
Repositorio Base para operaciones CRUD genéricas
===============================================

Este módulo proporciona la funcionalidad base para todos los repositorios
del sistema IoT Middleware, incluyendo operaciones CRUD estándar.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError
import logging

from ..db_handler import DatabaseHandler
from ...models.base import Base

# Configurar logging
logger = logging.getLogger(__name__)

# Tipo genérico para las entidades
T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T], ABC):
    """
    Repositorio base que proporciona operaciones CRUD genéricas
    
    Args:
        db_handler: Manejador de base de datos
        model_class: Clase del modelo SQLAlchemy
    """
    
    def __init__(self, db_handler: DatabaseHandler, model_class: Type[T]):
        self.db = db_handler
        self.model_class = model_class
        self.table_name = model_class.__tablename__
        self.schema = getattr(model_class.__table_args__, 'schema', 'public')
    
    def create(self, data: Dict[str, Any]) -> Optional[T]:
        """
        Crear una nueva entidad
        
        Args:
            data: Diccionario con los datos de la entidad
            
        Returns:
            Entidad creada o None si hay error
        """
        try:
            # Crear instancia del modelo
            instance = self.model_class(**data)
            
            # Insertar en la base de datos
            with self.db.get_session() as session:
                session.add(instance)
                session.commit()
                session.refresh(instance)
                logger.info(f"Entidad {self.table_name} creada exitosamente: {instance.id}")
                return instance
                
        except SQLAlchemyError as e:
            logger.error(f"Error al crear entidad {self.table_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al crear entidad {self.table_name}: {e}")
            return None
    
    def get_by_id(self, entity_id: Any) -> Optional[T]:
        """
        Obtener entidad por ID
        
        Args:
            entity_id: ID de la entidad
            
        Returns:
            Entidad encontrada o None
        """
        try:
            with self.db.get_session() as session:
                instance = session.get(self.model_class, entity_id)
                if instance:
                    logger.debug(f"Entidad {self.table_name} encontrada: {entity_id}")
                else:
                    logger.debug(f"Entidad {self.table_name} no encontrada: {entity_id}")
                return instance
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener entidad {self.table_name} por ID {entity_id}: {e}")
            return None
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
        Obtener todas las entidades con paginación opcional
        
        Args:
            limit: Límite de resultados
            offset: Desplazamiento para paginación
            
        Returns:
            Lista de entidades
        """
        try:
            with self.db.get_session() as session:
                query = select(self.model_class)
                
                if offset:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)
                
                result = session.execute(query)
                instances = result.scalars().all()
                
                logger.debug(f"Obtenidas {len(instances)} entidades de {self.table_name}")
                return instances
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener entidades {self.table_name}: {e}")
            return []
    
    def update(self, entity_id: Any, data: Dict[str, Any]) -> Optional[T]:
        """
        Actualizar una entidad existente
        
        Args:
            entity_id: ID de la entidad a actualizar
            data: Diccionario con los datos a actualizar
            
        Returns:
            Entidad actualizada o None si hay error
        """
        try:
            with self.db.get_session() as session:
                # Buscar la entidad
                instance = session.get(self.model_class, entity_id)
                if not instance:
                    logger.warning(f"Entidad {self.table_name} no encontrada para actualizar: {entity_id}")
                    return None
                
                # Actualizar campos
                for key, value in data.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                
                session.commit()
                session.refresh(instance)
                
                logger.info(f"Entidad {self.table_name} actualizada exitosamente: {entity_id}")
                return instance
                
        except SQLAlchemyError as e:
            logger.error(f"Error al actualizar entidad {self.table_name} {entity_id}: {e}")
            return None
    
    def delete(self, entity_id: Any) -> bool:
        """
        Eliminar una entidad
        
        Args:
            entity_id: ID de la entidad a eliminar
            
        Returns:
            True si se eliminó exitosamente, False en caso contrario
        """
        try:
            with self.db.get_session() as session:
                instance = session.get(self.model_class, entity_id)
                if not instance:
                    logger.warning(f"Entidad {self.table_name} no encontrada para eliminar: {entity_id}")
                    return False
                
                session.delete(instance)
                session.commit()
                
                logger.info(f"Entidad {self.table_name} eliminada exitosamente: {entity_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error al eliminar entidad {self.table_name} {entity_id}: {e}")
            return False
    
    def find_by_criteria(self, criteria: Dict[str, Any], limit: Optional[int] = None) -> List[T]:
        """
        Buscar entidades por criterios específicos
        
        Args:
            criteria: Diccionario con criterios de búsqueda
            limit: Límite de resultados
            
        Returns:
            Lista de entidades que coinciden con los criterios
        """
        try:
            with self.db.get_session() as session:
                query = select(self.model_class)
                
                # Aplicar criterios de búsqueda
                for key, value in criteria.items():
                    if hasattr(self.model_class, key):
                        if isinstance(value, (list, tuple)):
                            query = query.where(getattr(self.model_class, key).in_(value))
                        else:
                            query = query.where(getattr(self.model_class, key) == value)
                
                if limit:
                    query = query.limit(limit)
                
                result = session.execute(query)
                instances = result.scalars().all()
                
                logger.debug(f"Encontradas {len(instances)} entidades de {self.table_name} con criterios: {criteria}")
                return instances
                
        except SQLAlchemyError as e:
            logger.error(f"Error al buscar entidades {self.table_name} con criterios {criteria}: {e}")
            return []
    
    def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """
        Contar entidades que coinciden con criterios opcionales
        
        Args:
            criteria: Criterios de búsqueda opcionales
            
        Returns:
            Número de entidades que coinciden
        """
        try:
            with self.db.get_session() as session:
                query = select(self.model_class)
                
                if criteria:
                    for key, value in criteria.items():
                        if hasattr(self.model_class, key):
                            if isinstance(value, (list, tuple)):
                                query = query.where(getattr(self.model_class, key).in_(value))
                            else:
                                query = query.where(getattr(self.model_class, key) == value)
                
                result = session.execute(query)
                count = len(result.scalars().all())
                
                logger.debug(f"Contadas {count} entidades de {self.table_name}")
                return count
                
        except SQLAlchemyError as e:
            logger.error(f"Error al contar entidades {self.table_name}: {e}")
            return 0
    
    def exists(self, entity_id: Any) -> bool:
        """
        Verificar si existe una entidad con el ID especificado
        
        Args:
            entity_id: ID de la entidad
            
        Returns:
            True si existe, False en caso contrario
        """
        try:
            with self.db.get_session() as session:
                instance = session.get(self.model_class, entity_id)
                return instance is not None
                
        except SQLAlchemyError as e:
            logger.error(f"Error al verificar existencia de entidad {self.table_name} {entity_id}: {e}")
            return False
