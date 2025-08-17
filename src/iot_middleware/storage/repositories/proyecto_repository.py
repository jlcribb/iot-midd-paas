"""
Repositorio para Proyectos
==========================

Este módulo maneja las operaciones CRUD específicas para proyectos,
incluyendo búsquedas por estado, cliente y gestión de fechas.
"""

from typing import Dict, Any, Optional, List
from datetime import date, datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.exc import SQLAlchemyError
import logging

from .base_repository import BaseRepository
from ...models.entities import Proyecto, Cliente, UnidadProyecto, DispositivoProyecto
from ...models.enums import EstadoProyecto

# Configurar logging
logger = logging.getLogger(__name__)


class ProyectoRepository(BaseRepository[Proyecto]):
    """
    Repositorio para proyectos con métodos especializados
    """
    
    def __init__(self, db_handler):
        super().__init__(db_handler, Proyecto)
    
    def get_by_cliente(self, cliente_id: str) -> List[Proyecto]:
        """
        Obtener proyectos por cliente
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Lista de proyectos del cliente
        """
        return self.find_by_criteria({'cliente_id': cliente_id})
    
    def get_by_estado(self, estado: EstadoProyecto) -> List[Proyecto]:
        """
        Obtener proyectos por estado
        
        Args:
            estado: Estado del proyecto
            
        Returns:
            Lista de proyectos con el estado especificado
        """
        return self.find_by_criteria({'estado': estado})
    
    def get_active_projects(self) -> List[Proyecto]:
        """
        Obtener solo proyectos activos
        
        Returns:
            Lista de proyectos activos
        """
        return self.find_by_criteria({'activo': True})
    
    def get_projects_by_date_range(self, start_date: date, end_date: date) -> List[Proyecto]:
        """
        Obtener proyectos en un rango de fechas
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Lista de proyectos en el rango
        """
        try:
            with self.db.get_session() as session:
                query = select(Proyecto).where(
                    and_(
                        Proyecto.fecha_inicio >= start_date,
                        Proyecto.fecha_fin <= end_date
                    )
                )
                
                result = session.execute(query)
                projects = result.scalars().all()
                
                logger.debug(f"Obtenidos {len(projects)} proyectos en rango de fechas")
                return projects
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener proyectos por rango de fechas: {e}")
            return []
    
    def get_projects_by_priority(self, min_priority: int = 1, max_priority: int = 5) -> List[Proyecto]:
        """
        Obtener proyectos por rango de prioridad
        
        Args:
            min_priority: Prioridad mínima
            max_priority: Prioridad máxima
            
        Returns:
            Lista de proyectos en el rango de prioridad
        """
        try:
            with self.db.get_session() as session:
                query = select(Proyecto).where(
                    and_(
                        Proyecto.prioridad >= min_priority,
                        Proyecto.prioridad <= max_priority
                    )
                ).order_by(Proyecto.prioridad.desc())
                
                result = session.execute(query)
                projects = result.scalars().all()
                
                logger.debug(f"Obtenidos {len(projects)} proyectos por prioridad")
                return projects
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener proyectos por prioridad: {e}")
            return []
    
    def get_projects_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen general de todos los proyectos
        
        Returns:
            Diccionario con estadísticas de proyectos
        """
        try:
            with self.db.get_session() as session:
                # Contar total de proyectos
                total_projects = session.query(Proyecto).count()
                
                # Contar por estado
                projects_by_status = session.query(
                    Proyecto.estado, func.count(Proyecto.id)
                ).group_by(Proyecto.estado).all()
                
                # Contar proyectos activos
                active_projects = session.query(Proyecto).filter(
                    Proyecto.activo == True
                ).count()
                
                # Proyectos con presupuesto alto (>10000)
                high_budget_projects = session.query(Proyecto).filter(
                    Proyecto.presupuesto > 10000
                ).count()
                
                summary = {
                    'total_proyectos': total_projects,
                    'proyectos_activos': active_projects,
                    'proyectos_inactivos': total_projects - active_projects,
                    'por_estado': dict(projects_by_status),
                    'presupuesto_alto': high_budget_projects
                }
                
                return summary
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener resumen de proyectos: {e}")
            return {}
    
    def get_project_details(self, proyecto_id: str) -> Dict[str, Any]:
        """
        Obtener detalles completos de un proyecto incluyendo relaciones
        
        Args:
            proyecto_id: ID del proyecto
            
        Returns:
            Diccionario con detalles del proyecto
        """
        try:
            proyecto = self.get_by_id(proyecto_id)
            if not proyecto:
                return {}
            
            with self.db.get_session() as session:
                # Obtener cliente
                cliente = session.get(Cliente, proyecto.cliente_id)
                
                # Contar unidades
                unidades_count = session.query(UnidadProyecto).filter(
                    UnidadProyecto.proyecto_id == proyecto_id
                ).count()
                
                # Contar dispositivos
                dispositivos_count = session.query(DispositivoProyecto).filter(
                    DispositivoProyecto.proyecto_id == proyecto_id
                ).count()
                
                # Obtener unidades recientes
                unidades_recientes = session.query(UnidadProyecto).filter(
                    UnidadProyecto.proyecto_id == proyecto_id
                ).order_by(UnidadProyecto.creado_en.desc()).limit(3).all()
                
                details = {
                    'proyecto': {
                        'id': str(proyecto.id),
                        'nombre': proyecto.nombre,
                        'descripcion': proyecto.descripcion,
                        'estado': proyecto.estado,
                        'fecha_inicio': proyecto.fecha_inicio.isoformat() if proyecto.fecha_inicio else None,
                        'fecha_fin': proyecto.fecha_fin.isoformat() if proyecto.fecha_fin else None,
                        'presupuesto': float(proyecto.presupuesto) if proyecto.presupuesto else None,
                        'prioridad': proyecto.prioridad,
                        'activo': proyecto.activo,
                        'creado_en': proyecto.creado_en.isoformat() if proyecto.creado_en else None
                    },
                    'cliente': {
                        'id': str(cliente.id),
                        'nombre': cliente.nombre,
                        'sector': cliente.sector,
                        'industria': cliente.industria
                    } if cliente else None,
                    'estadisticas': {
                        'total_unidades': unidades_count,
                        'total_dispositivos': dispositivos_count
                    },
                    'unidades_recientes': [
                        {
                            'id': str(u.id),
                            'nombre': u.nombre,
                            'ubicacion': u.ubicacion,
                            'responsable': u.responsable
                        }
                        for u in unidades_recientes
                    ]
                }
                
                return details
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener detalles del proyecto {proyecto_id}: {e}")
            return {}
    
    def update_project_status(self, proyecto_id: str, estado: EstadoProyecto) -> bool:
        """
        Actualizar el estado de un proyecto
        
        Args:
            proyecto_id: ID del proyecto
            estado: Nuevo estado
            
        Returns:
            True si se actualizó exitosamente
        """
        return self.update(proyecto_id, {'estado': estado}) is not None
    
    def get_projects_by_budget_range(self, min_budget: float, max_budget: float) -> List[Proyecto]:
        """
        Obtener proyectos por rango de presupuesto
        
        Args:
            min_budget: Presupuesto mínimo
            max_budget: Presupuesto máximo
            
        Returns:
            Lista de proyectos en el rango de presupuesto
        """
        try:
            with self.db.get_session() as session:
                query = select(Proyecto).where(
                    and_(
                        Proyecto.presupuesto >= min_budget,
                        Proyecto.presupuesto <= max_budget
                    )
                ).order_by(Proyecto.presupuesto.desc())
                
                result = session.execute(query)
                projects = result.scalars().all()
                
                logger.debug(f"Obtenidos {len(projects)} proyectos por rango de presupuesto")
                return projects
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener proyectos por presupuesto: {e}")
            return []
    
    def search_projects(self, search_term: str) -> List[Proyecto]:
        """
        Buscar proyectos por término de búsqueda
        
        Args:
            search_term: Término de búsqueda
            
        Returns:
            Lista de proyectos que coinciden
        """
        try:
            with self.db.get_session() as session:
                search_pattern = f"%{search_term}%"
                query = select(Proyecto).where(
                    or_(
                        Proyecto.nombre.ilike(search_pattern),
                        Proyecto.descripcion.ilike(search_pattern)
                    )
                )
                
                result = session.execute(query)
                projects = result.scalars().all()
                
                logger.debug(f"Búsqueda '{search_term}' retornó {len(projects)} proyectos")
                return projects
                
        except SQLAlchemyError as e:
            logger.error(f"Error en búsqueda de proyectos: {e}")
            return []
