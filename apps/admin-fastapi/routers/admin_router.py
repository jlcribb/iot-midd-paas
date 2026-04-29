"""
Router principal de administración
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(request: Request) -> Dict[str, Any]:
    """Verificar salud del servicio de administración"""
    try:
        db_handler = request.app.state.db_handler
        
        return {
            "status": "healthy",
            "database": "connected" if db_handler and db_handler.is_connected() else "disconnected"
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))
