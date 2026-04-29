"""
Repositorio para Dispositivos IoT
=================================

Este módulo maneja operaciones CRUD específicas para dispositivos,
incluyendo búsquedas por identificador único y estado.
"""

from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.exc import SQLAlchemyError
import logging

from .base_repository import BaseRepository
from ...models.entities import Dispositivo

logger = logging.getLogger(__name__)


class DispositivoRepository(BaseRepository[Dispositivo]):
    """Repositorio para dispositivos IoT con métodos especializados."""

    def __init__(self, db_handler):
        super().__init__(db_handler, Dispositivo)

    def get_by_identificador(self, identificador_unico: str) -> Optional[Dispositivo]:
        """Obtener dispositivo por identificador único."""
        try:
            with self.db.get_session() as session:
                query = select(Dispositivo).where(
                    Dispositivo.identificador_unico == identificador_unico
                )
                result = session.execute(query)
                return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener dispositivo por identificador: {e}")
            return None

    def get_active_devices(self) -> List[Dispositivo]:
        """Obtener dispositivos activos."""
        return self.find_by_criteria({'activo': True})

    def search_devices(self, search_term: str) -> List[Dispositivo]:
        """Buscar dispositivos por nombre/fabricante/modelo/identificador."""
        try:
            with self.db.get_session() as session:
                search_pattern = f"%{search_term}%"
                query = select(Dispositivo).where(
                    or_(
                        Dispositivo.tipo.ilike(search_pattern),
                        Dispositivo.fabricante.ilike(search_pattern),
                        Dispositivo.modelo.ilike(search_pattern),
                        Dispositivo.identificador_unico.ilike(search_pattern)
                    )
                )
                result = session.execute(query)
                return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Error en búsqueda de dispositivos: {e}")
            return []
