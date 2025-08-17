"""
Repositorio para Clientes
=========================

Este módulo maneja las operaciones CRUD específicas para clientes,
incluyendo búsquedas por sector, industria y relaciones con proyectos.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy import select, and_, or_
from sqlalchemy.exc import SQLAlchemyError
import logging

from .base_repository import BaseRepository
from ...models.entities import Cliente, Proyecto

# Configurar logging
logger = logging.getLogger(__name__)


class ClienteRepository(BaseRepository[Cliente]):
    """
    Repositorio para clientes con métodos especializados
    """
    
    def __init__(self, db_handler):
        super().__init__(db_handler, Cliente)
    
    def get_by_sector(self, sector: str) -> List[Cliente]:
        """
        Obtener clientes por sector
        
        Args:
            sector: Sector de la industria
            
        Returns:
            Lista de clientes del sector
        """
        return self.find_by_criteria({'sector': sector})
    
    def get_by_industria(self, industria: str) -> List[Cliente]:
        """
        Obtener clientes por industria
        
        Args:
            industria: Tipo de industria
            
        Returns:
            Lista de clientes de la industria
        """
        return self.find_by_criteria({'industria': industria})
    
    def get_active_clients(self) -> List[Cliente]:
        """
        Obtener solo clientes activos
        
        Returns:
            Lista de clientes activos
        """
        return self.find_by_criteria({'activo': True})
    
    def get_clients_with_projects(self) -> List[Cliente]:
        """
        Obtener clientes que tienen proyectos activos
        
        Returns:
            Lista de clientes con proyectos
        """
        try:
            with self.db.get_session() as session:
                query = select(Cliente).join(Proyecto).where(
                    and_(Cliente.activo == True, Proyecto.activo == True)
                ).distinct()
                
                result = session.execute(query)
                clients = result.scalars().all()
                
                logger.debug(f"Obtenidos {len(clients)} clientes con proyectos activos")
                return clients
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener clientes con proyectos: {e}")
            return []
    
    def search_clients(self, search_term: str) -> List[Cliente]:
        """
        Buscar clientes por término de búsqueda (nombre, sector, industria)
        
        Args:
            search_term: Término de búsqueda
            
        Returns:
            Lista de clientes que coinciden
        """
        try:
            with self.db.get_session() as session:
                search_pattern = f"%{search_term}%"
                query = select(Cliente).where(
                    or_(
                        Cliente.nombre.ilike(search_pattern),
                        Cliente.sector.ilike(search_pattern),
                        Cliente.industria.ilike(search_pattern)
                    )
                )
                
                result = session.execute(query)
                clients = result.scalars().all()
                
                logger.debug(f"Búsqueda '{search_term}' retornó {len(clients)} clientes")
                return clients
                
        except SQLAlchemyError as e:
            logger.error(f"Error en búsqueda de clientes: {e}")
            return []
    
    def get_client_summary(self, cliente_id: str) -> Dict[str, Any]:
        """
        Obtener resumen completo de un cliente incluyendo estadísticas
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Diccionario con resumen del cliente
        """
        try:
            cliente = self.get_by_id(cliente_id)
            if not cliente:
                return {}
            
            with self.db.get_session() as session:
                # Contar proyectos
                proyectos_count = session.query(Proyecto).filter(
                    Proyecto.cliente_id == cliente_id
                ).count()
                
                # Contar proyectos activos
                proyectos_activos_count = session.query(Proyecto).filter(
                    and_(Proyecto.cliente_id == cliente_id, Proyecto.activo == True)
                ).count()
                
                # Obtener proyectos recientes
                proyectos_recientes = session.query(Proyecto).filter(
                    Proyecto.cliente_id == cliente_id
                ).order_by(Proyecto.creado_en.desc()).limit(5).all()
                
                summary = {
                    'cliente': {
                        'id': str(cliente.id),
                        'nombre': cliente.nombre,
                        'sector': cliente.sector,
                        'industria': cliente.industria,
                        'activo': cliente.activo,
                        'creado_en': cliente.creado_en.isoformat() if cliente.creado_en else None
                    },
                    'estadisticas': {
                        'total_proyectos': proyectos_count,
                        'proyectos_activos': proyectos_activos_count,
                        'proyectos_inactivos': proyectos_count - proyectos_activos_count
                    },
                    'proyectos_recientes': [
                        {
                            'id': str(p.id),
                            'nombre': p.nombre,
                            'estado': p.estado,
                            'fecha_inicio': p.fecha_inicio.isoformat() if p.fecha_inicio else None,
                            'activo': p.activo
                        }
                        for p in proyectos_recientes
                    ]
                }
                
                return summary
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener resumen del cliente {cliente_id}: {e}")
            return {}
    
    def update_client_status(self, cliente_id: str, activo: bool) -> bool:
        """
        Actualizar el estado activo/inactivo de un cliente
        
        Args:
            cliente_id: ID del cliente
            activo: Nuevo estado
            
        Returns:
            True si se actualizó exitosamente
        """
        return self.update(cliente_id, {'activo': activo}) is not None
    
    def get_clients_by_contact(self, contact_info: Dict[str, Any]) -> List[Cliente]:
        """
        Buscar clientes por información de contacto
        
        Args:
            contact_info: Diccionario con información de contacto
            
        Returns:
            Lista de clientes que coinciden
        """
        try:
            with self.db.get_session() as session:
                query = select(Cliente)
                
                # Buscar en contacto_principal
                if 'email' in contact_info:
                    query = query.where(
                        Cliente.contacto_principal['email'].astext == contact_info['email']
                    )
                
                if 'telefono' in contact_info:
                    query = query.where(
                        Cliente.contacto_principal['telefono'].astext == contact_info['telefono']
                    )
                
                result = session.execute(query)
                clients = result.scalars().all()
                
                logger.debug(f"Búsqueda por contacto retornó {len(clients)} clientes")
                return clients
                
        except SQLAlchemyError as e:
            logger.error(f"Error en búsqueda por contacto: {e}")
            return []
