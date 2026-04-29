"""
Repositorio para Dispositivos en Proyectos
==========================================

Este módulo maneja operaciones CRUD específicas para dispositivos asociados
a proyectos y unidades.
"""

from typing import List
from sqlalchemy import select, or_
from sqlalchemy.exc import SQLAlchemyError
import logging

from .base_repository import BaseRepository
from ...models.entities import DispositivoProyecto
from ...models.enums import EstadoDispositivo

logger = logging.getLogger(__name__)


class DispositivoProyectoRepository(BaseRepository[DispositivoProyecto]):
    """Repositorio para dispositivos en proyectos con métodos especializados."""

    def __init__(self, db_handler):
        super().__init__(db_handler, DispositivoProyecto)

    def get_by_proyecto(self, proyecto_id: str) -> List[DispositivoProyecto]:
        """Obtener dispositivos asociados a un proyecto."""
        return self.find_by_criteria({'proyecto_id': proyecto_id})

    def get_by_unidad(self, unidad_id: str) -> List[DispositivoProyecto]:
        """Obtener dispositivos asociados a una unidad."""
        return self.find_by_criteria({'unidad_id': unidad_id})

    def get_active_devices(self) -> List[DispositivoProyecto]:
        """Obtener dispositivos activos."""
        try:
            with self.db.get_session() as session:
                query = select(DispositivoProyecto).where(
                    DispositivoProyecto.estado == EstadoDispositivo.ACTIVO
                )
                result = session.execute(query)
                return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo dispositivos activos del proyecto: {e}")
            return []

    def search_devices(self, search_term: str) -> List[DispositivoProyecto]:
        """Buscar dispositivos por nombre personalizado o descripción."""
        try:
            with self.db.get_session() as session:
                search_pattern = f"%{search_term}%"
                query = select(DispositivoProyecto).where(
                    or_(
                        DispositivoProyecto.nombre_personalizado.ilike(search_pattern),
                        DispositivoProyecto.descripcion.ilike(search_pattern)
                    )
                )
                result = session.execute(query)
                return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Error en búsqueda de dispositivos del proyecto: {e}")
            return []
