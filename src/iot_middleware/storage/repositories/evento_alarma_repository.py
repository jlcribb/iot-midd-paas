"""
Repositorio para eventos y alarmas.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError

from .base_repository import BaseRepository
from ...models.entities import EventoAlarma


class EventoAlarmaRepository(BaseRepository[EventoAlarma]):
    """Repositorio especializado para eventos y alarmas."""

    def __init__(self, db_handler):
        super().__init__(db_handler, EventoAlarma)

    def list_events(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[EventoAlarma]:
        """Obtiene eventos aplicando filtros compatibles con el modelo actual."""
        filters = filters or {}

        try:
            with self.db.get_session() as session:
                query = select(EventoAlarma)

                if filters.get("proyecto_id"):
                    query = query.where(EventoAlarma.proyecto_id == filters["proyecto_id"])
                if filters.get("canal_id"):
                    query = query.where(EventoAlarma.canal_id == filters["canal_id"])
                if filters.get("dispositivo_id"):
                    query = query.where(EventoAlarma.dispositivo_id == filters["dispositivo_id"])
                if filters.get("severidad"):
                    query = query.where(EventoAlarma.severidad == filters["severidad"])
                if filters.get("tipo"):
                    query = query.where(EventoAlarma.codigo == filters["tipo"])
                if filters.get("activo") is True:
                    query = query.where(EventoAlarma.estado == "activa")
                if filters.get("activo") is False:
                    query = query.where(EventoAlarma.estado != "activa")
                if filters.get("desde"):
                    query = query.where(EventoAlarma.ts >= filters["desde"])
                if filters.get("hasta"):
                    query = query.where(EventoAlarma.ts <= filters["hasta"])

                query = query.order_by(desc(EventoAlarma.ts))

                if offset:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)

                result = session.execute(query)
                return result.scalars().all()

        except SQLAlchemyError:
            return []

    def count_events(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Cuenta eventos con el mismo contrato de filtros de `list_events`."""
        return len(self.list_events(filters=filters))
