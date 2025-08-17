"""
Router de Eventos
=================

Este módulo define los endpoints para gestión de eventos y alarmas,
con control de acceso basado en roles y scoping automático.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from typing import Optional, List
import logging

from ..models.common_models import (
    PaginatedResponse,
    SuccessResponse,
    ErrorResponse
)
from ..models.data_models import EventFilterRequest, EventsListResponse
from ..auth import AuthMiddleware, RoleChecker, ScopeHandler
from ...storage.db_handler import DatabaseHandler
from ...storage.repositories import EventoAlarmaRepository
from ...models.entities import Usuario, EventoAlarma
from ...models.enums import RolUsuario, SeveridadEvento

# Configurar logging
logger = logging.getLogger(__name__)

# Crear router
events_router = APIRouter(
    prefix="/eventos",
    tags=["Eventos y Alarmas"],
    responses={
        401: {"model": ErrorResponse, "description": "No autorizado"},
        403: {"model": ErrorResponse, "description": "Acceso denegado"},
        404: {"model": ErrorResponse, "description": "Recurso no encontrado"},
        422: {"model": ErrorResponse, "description": "Error de validación"}
    }
)


@events_router.get("/", response_model=EventsListResponse)
async def get_events(
    request: Request,
    proyecto_id: Optional[str] = Query(None, description="Filtrar por proyecto"),
    desde: Optional[str] = Query(None, description="Fecha de inicio (ISO 8601)"),
    hasta: Optional[str] = Query(None, description="Fecha de fin (ISO 8601)"),
    severidad: Optional[str] = Query(None, description="Filtrar por severidad"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de evento"),
    dispositivo_id: Optional[str] = Query(None, description="Filtrar por dispositivo"),
    canal_id: Optional[str] = Query(None, description="Filtrar por canal"),
    activo: Optional[bool] = Query(None, description="Solo eventos activos"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de eventos"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Obtener lista de eventos con filtros y paginación
    
    - **proyecto_id**: Filtrar por proyecto específico
    - **desde**: Fecha de inicio para filtrar
    - **hasta**: Fecha de fin para filtrar
    - **severidad**: Filtrar por nivel de severidad
    - **tipo**: Filtrar por tipo de evento
    - **dispositivo_id**: Filtrar por dispositivo
    - **canal_id**: Filtrar por canal
    - **activo**: Solo eventos activos
    - **limit**: Límite de eventos a retornar
    - **offset**: Desplazamiento para paginación
    """
    try:
        from datetime import datetime
        
        # Parsear fechas si están presentes
        desde_dt = None
        hasta_dt = None
        
        if desde:
            try:
                desde_dt = datetime.fromisoformat(desde.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de fecha 'desde' inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)"
                )
        
        if hasta:
            try:
                hasta_dt = datetime.fromisoformat(hasta.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de fecha 'hasta' inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)"
                )
        
        # Validar rango de fechas si ambas están presentes
        if desde_dt and hasta_dt and hasta_dt <= desde_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha de fin debe ser posterior a la de inicio"
            )
        
        # Obtener configuración y repositorios
        config = request.app.state.config
        db_handler = DatabaseHandler(config['postgresql'])
        evento_repo = EventoAlarmaRepository(db_handler)
        scope_handler = ScopeHandler()
        
        # Construir filtros base
        base_filters = {}
        if proyecto_id:
            base_filters['proyecto_id'] = proyecto_id
        if severidad:
            # Validar severidad
            try:
                SeveridadEvento(severidad)
                base_filters['severidad'] = severidad
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Severidad inválida. Valores permitidos: {[s.value for s in SeveridadEvento]}"
                )
        if tipo:
            base_filters['tipo'] = tipo
        if dispositivo_id:
            base_filters['dispositivo_id'] = dispositivo_id
        if canal_id:
            base_filters['canal_id'] = canal_id
        if activo is not None:
            base_filters['activo'] = activo
        
        # Aplicar scope del usuario
        scope_filters = scope_handler.get_user_scope_filters(current_user)
        combined_filters = scope_handler.apply_scope_to_filters(base_filters, current_user)
        
        # Obtener eventos con filtros aplicados
        eventos = evento_repo.find_by_criteria(
            combined_filters,
            limit=limit
        )
        
        # Aplicar filtros de fecha si están presentes
        eventos_filtrados = []
        for evento in eventos:
            # Filtrar por fecha desde
            if desde_dt and evento.timestamp < desde_dt:
                continue
            
            # Filtrar por fecha hasta
            if hasta_dt and evento.timestamp > hasta_dt:
                continue
            
            eventos_filtrados.append(evento)
        
        # Aplicar paginación
        start_idx = offset
        end_idx = start_idx + limit
        eventos_paginados = eventos_filtrados[start_idx:end_idx]
        
        # Contar total de eventos que coinciden con los filtros
        total = len(eventos_filtrados)
        
        # Convertir a formato de respuesta
        eventos_data = []
        for evento in eventos_paginados:
            eventos_data.append({
                "id": str(evento.id),
                "tipo": evento.tipo,
                "severidad": evento.severidad,
                "mensaje": evento.mensaje,
                "timestamp": evento.timestamp.isoformat(),
                "activo": evento.activo,
                "metadata": evento.metadata,
                "dispositivo_id": str(evento.dispositivo_id) if evento.dispositivo_id else None,
                "canal_id": str(evento.canal_id) if evento.canal_id else None,
                "proyecto_id": str(evento.proyecto_id) if evento.proyecto_id else None,
                "valor_anterior": evento.valor_anterior,
                "valor_actual": evento.valor_actual,
                "umbral": evento.umbral
            })
        
        # Crear respuesta
        return {
            "success": True,
            "message": "Eventos obtenidos exitosamente",
            "data": eventos_data,
            "total": total,
            "filtros_aplicados": {
                "proyecto_id": proyecto_id,
                "desde": desde,
                "hasta": hasta,
                "severidad": severidad,
                "tipo": tipo,
                "dispositivo_id": dispositivo_id,
                "canal_id": canal_id,
                "activo": activo,
                "limit": limit,
                "offset": offset
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener eventos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@events_router.get("/{evento_id}", response_model=SuccessResponse)
async def get_event(
    evento_id: str,
    request: Request,
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Obtener evento específico por ID
    
    - **evento_id**: ID único del evento
    """
    try:
        # Obtener configuración y repositorios
        config = request.app.state.config
        db_handler = DatabaseHandler(config['postgresql'])
        evento_repo = EventoAlarmaRepository(db_handler)
        scope_handler = ScopeHandler()
        
        # Obtener evento
        evento = evento_repo.get_by_id(evento_id)
        if not evento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento no encontrado"
            )
        
        # Verificar acceso según scope del usuario
        if not scope_handler.validate_resource_access(current_user, {
            'proyecto_id': str(evento.proyecto_id) if evento.proyecto_id else None
        }):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado al evento"
            )
        
        # Convertir a formato de respuesta
        evento_data = {
            "id": str(evento.id),
            "tipo": evento.tipo,
            "severidad": evento.severidad,
            "mensaje": evento.mensaje,
            "timestamp": evento.timestamp.isoformat(),
            "activo": evento.activo,
            "metadata": evento.metadata,
            "dispositivo_id": str(evento.dispositivo_id) if evento.dispositivo_id else None,
            "canal_id": str(evento.canal_id) if evento.canal_id else None,
            "proyecto_id": str(evento.proyecto_id) if evento.proyecto_id else None,
            "valor_anterior": evento.valor_anterior,
            "valor_actual": evento.valor_actual,
            "umbral": evento.umbral,
            "creado_en": evento.creado_en.isoformat() if evento.creado_en else None,
            "actualizado_en": evento.actualizado_en.isoformat() if evento.actualizado_en else None
        }
        
        return {
            "success": True,
            "message": "Evento obtenido exitosamente",
            "data": evento_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener evento {evento_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@events_router.post("/", response_model=SuccessResponse)
async def create_event(
    request: Request,
    event_data: dict,
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Crear nuevo evento (solo administradores, técnicos y clientes)
    
    - **event_data**: Datos del evento a crear
    """
    try:
        # Verificar permisos
        role_checker = RoleChecker(AuthMiddleware(JWTHandler(), DatabaseHandler({})))
        if not role_checker.check_permission(current_user, "event_management"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para crear eventos"
            )
        
        # Obtener configuración y repositorios
        config = request.app.state.config
        db_handler = DatabaseHandler(config['postgresql'])
        evento_repo = EventoAlarmaRepository(db_handler)
        
        # Crear evento
        evento_creado = evento_repo.create(event_data)
        
        if not evento_creado:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear el evento"
            )
        
        return {
            "success": True,
            "message": "Evento creado exitosamente",
            "data": {
                "id": str(evento_creado.id),
                "tipo": evento_creado.tipo,
                "severidad": evento_creado.severidad
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear evento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@events_router.put("/{evento_id}", response_model=SuccessResponse)
async def update_event(
    evento_id: str,
    request: Request,
    event_data: dict,
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Actualizar evento existente
    
    - **evento_id**: ID del evento a actualizar
    - **event_data**: Datos a actualizar
    """
    try:
        # Obtener configuración y repositorios
        config = request.app.state.config
        db_handler = DatabaseHandler(config['postgresql'])
        evento_repo = EventoAlarmaRepository(db_handler)
        scope_handler = ScopeHandler()
        
        # Verificar que el evento existe
        evento = evento_repo.get_by_id(evento_id)
        if not evento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento no encontrado"
            )
        
        # Verificar permisos
        role_checker = RoleChecker(AuthMiddleware(JWTHandler(), DatabaseHandler({})))
        if not role_checker.check_permission(current_user, "event_management", evento_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para actualizar este evento"
            )
        
        # Verificar acceso según scope del usuario
        if not scope_handler.validate_resource_access(current_user, {
            'proyecto_id': str(evento.proyecto_id) if evento.proyecto_id else None
        }):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado al evento"
            )
        
        # Actualizar evento
        evento_actualizado = evento_repo.update(evento_id, event_data)
        
        if not evento_actualizado:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar el evento"
            )
        
        return {
            "success": True,
            "message": "Evento actualizado exitosamente",
            "data": {
                "id": str(evento_actualizado.id),
                "tipo": evento_actualizado.tipo,
                "severidad": evento_actualizado.severidad
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar evento {evento_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@events_router.delete("/{evento_id}", response_model=SuccessResponse)
async def delete_event(
    evento_id: str,
    request: Request,
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Eliminar evento (solo administradores y técnicos)
    
    - **evento_id**: ID del evento a eliminar
    """
    try:
        # Verificar permisos (solo administradores y técnicos)
        if current_user.rol not in [RolUsuario.ADMIN, RolUsuario.TECNICO]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los administradores y técnicos pueden eliminar eventos"
            )
        
        # Obtener configuración y repositorios
        config = request.app.state.config
        db_handler = DatabaseHandler(config['postgresql'])
        evento_repo = EventoAlarmaRepository(db_handler)
        
        # Verificar que el evento existe
        evento = evento_repo.get_by_id(evento_id)
        if not evento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento no encontrado"
            )
        
        # Eliminar evento
        eliminado = evento_repo.delete(evento_id)
        
        if not eliminado:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar el evento"
            )
        
        return {
            "success": True,
            "message": "Evento eliminado exitosamente",
            "data": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar evento {evento_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@events_router.post("/{evento_id}/acknowledge", response_model=SuccessResponse)
async def acknowledge_event(
    evento_id: str,
    request: Request,
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Reconocer evento (marcar como atendido)
    
    - **evento_id**: ID del evento a reconocer
    """
    try:
        # Obtener configuración y repositorios
        config = request.app.state.config
        db_handler = DatabaseHandler(config['postgresql'])
        evento_repo = EventoAlarmaRepository(db_handler)
        scope_handler = ScopeHandler()
        
        # Verificar que el evento existe
        evento = evento_repo.get_by_id(evento_id)
        if not evento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento no encontrado"
            )
        
        # Verificar acceso según scope del usuario
        if not scope_handler.validate_resource_access(current_user, {
            'proyecto_id': str(evento.proyecto_id) if evento.proyecto_id else None
        }):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado al evento"
            )
        
        # Actualizar evento como reconocido
        update_data = {
            "activo": False,
            "metadata": {
                **evento.metadata or {},
                "acknowledged_by": str(current_user.id),
                "acknowledged_at": datetime.utcnow().isoformat(),
                "acknowledged_by_name": current_user.nombre
            }
        }
        
        evento_actualizado = evento_repo.update(evento_id, update_data)
        
        if not evento_actualizado:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al reconocer el evento"
            )
        
        return {
            "success": True,
            "message": "Evento reconocido exitosamente",
            "data": {
                "id": str(evento_actualizado.id),
                "acknowledged_by": current_user.nombre,
                "acknowledged_at": update_data["metadata"]["acknowledged_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al reconocer evento {evento_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


# Función auxiliar para obtener usuario actual
async def get_current_user(request: Request) -> Usuario:
    """Obtener usuario actual desde el request"""
    try:
        # Obtener configuración
        config = request.app.state.config
        db_handler = DatabaseHandler(config['postgresql'])
        
        # Inicializar manejadores
        jwt_handler = JWTHandler()
        auth_middleware = AuthMiddleware(jwt_handler, db_handler)
        
        # Obtener usuario autenticado
        return await auth_middleware.get_current_active_user(request)
        
    except Exception as e:
        logger.error(f"Error al obtener usuario actual: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )
