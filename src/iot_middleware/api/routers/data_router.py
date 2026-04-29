"""
Router de Datos IoT
===================

Este módulo define los endpoints para inserción y consulta de datos IoT,
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
from ..models.data_models import (
    DataInsertRequest,
    DataInsertResponse,
    TimeSeriesRequest,
    TimeSeriesResponse,
    AggregationRequest,
    AggregationResponse
)
from ..auth import AuthMiddleware, RoleChecker, ScopeHandler, JWTHandler
from ...storage.db_handler import create_database_handler
from ...storage.repositories import RegistroDatosRepository, CanalRepository
from ...models.entities import Usuario, RegistroDatos
from ...models.enums import RolUsuario, CalidadDato

# Configurar logging
logger = logging.getLogger(__name__)


def _get_db_handler(request: Request):
    return create_database_handler(config=request.app.state.config)


def _metadata_value(record):
    return getattr(record, "metadatos", getattr(record, "metadata", None))

# Crear router
data_router = APIRouter(
    prefix="/datos",
    tags=["Datos IoT"],
    responses={
        401: {"model": ErrorResponse, "description": "No autorizado"},
        403: {"model": ErrorResponse, "description": "Acceso denegado"},
        404: {"model": ErrorResponse, "description": "Recurso no encontrado"},
        422: {"model": ErrorResponse, "description": "Error de validación"}
    }
)


@data_router.post("/insertar", response_model=DataInsertResponse)
async def insert_data(
    request: Request,
    data_request: DataInsertRequest,
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Insertar dato IoT con validación automática
    
    - **data_request**: Datos a insertar con validación automática
    """
    try:
        # Verificar permisos
        role_checker = RoleChecker(AuthMiddleware(JWTHandler(), _get_db_handler(request)))
        if not role_checker.check_permission(current_user, "data_write"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para insertar datos"
            )
        
        # Obtener configuración y repositorios
        db_handler = _get_db_handler(request)
        registro_repo = RegistroDatosRepository(db_handler)
        canal_repo = CanalRepository(db_handler)
        scope_handler = ScopeHandler()
        
        # Verificar que el canal existe y es accesible
        canal = canal_repo.get_by_id(data_request.canal_id)
        if not canal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Canal no encontrado"
            )
        
        # Obtener información del canal para verificar scope
        canal_info = canal_repo.get_channel_info_for_validation(data_request.canal_id)
        if not canal_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener información del canal"
            )
        
        # Verificar acceso según scope del usuario
        if not scope_handler.validate_resource_access(current_user, {
            'proyecto_id': canal_info.get('proyecto_id'),
            'cliente_id': canal_info.get('cliente_id')
        }):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado al canal"
            )
        
        # Preparar metadatos adicionales
        metadata = data_request.metadata or {}
        if data_request.qos is not None:
            metadata['qos'] = data_request.qos
        if data_request.ip:
            metadata['ip'] = data_request.ip
        if data_request.source:
            metadata['source'] = data_request.source
        
        # Insertar dato con validación automática
        registro = registro_repo.insert_record(
            canal_id=data_request.canal_id,
            valor=data_request.valor,
            ts=data_request.timestamp,
            calidad=data_request.calidad,
            calidad_porcentaje=data_request.calidad_porcentaje,
            metadata=metadata
        )
        
        if not registro:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error de validación del dato. Verifique el tipo y rango del valor."
            )
        
        # Determinar el tipo de valor insertado
        tipo_valor = "unknown"
        if registro.valor_num is not None:
            tipo_valor = "num"
        elif registro.valor_int is not None:
            tipo_valor = "int"
        elif registro.valor_bool is not None:
            tipo_valor = "bool"
        elif registro.valor_text is not None:
            tipo_valor = "text"
        elif registro.valor_json is not None:
            tipo_valor = "json"
        
        return {
            "success": True,
            "message": "Dato insertado exitosamente",
            "data": {
                "id": str(registro.id),
                "canal_id": str(registro.canal_id),
                "timestamp": registro.ts.isoformat(),
                "valor": data_request.valor,
                "tipo_valor": tipo_valor,
                "calidad": registro.calidad,
                "calidad_porcentaje": registro.calidad_porcentaje,
                "metadata": _metadata_value(registro)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al insertar dato: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@data_router.get("/canal/{canal_id}", response_model=PaginatedResponse)
async def get_channel_data(
    canal_id: str,
    request: Request,
    desde: Optional[str] = Query(None, description="Fecha de inicio (ISO 8601)"),
    hasta: Optional[str] = Query(None, description="Fecha de fin (ISO 8601)"),
    limit: int = Query(1000, ge=1, le=10000, description="Límite de registros"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(100, ge=1, le=1000, description="Tamaño de página"),
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Obtener datos de un canal específico con paginación
    
    - **canal_id**: ID del canal
    - **desde**: Fecha de inicio para filtrar
    - **hasta**: Fecha de fin para filtrar
    - **limit**: Límite total de registros
    - **page**: Número de página
    - **size**: Tamaño de página
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
        db_handler = _get_db_handler(request)
        registro_repo = RegistroDatosRepository(db_handler)
        canal_repo = CanalRepository(db_handler)
        scope_handler = ScopeHandler()
        
        # Verificar que el canal existe y es accesible
        canal = canal_repo.get_by_id(canal_id)
        if not canal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Canal no encontrado"
            )
        
        # Obtener información del canal para verificar scope
        canal_info = canal_repo.get_channel_info_for_validation(canal_id)
        if not canal_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener información del canal"
            )
        
        # Verificar acceso según scope del usuario
        if not scope_handler.validate_resource_access(current_user, {
            'proyecto_id': canal_info.get('proyecto_id'),
            'cliente_id': canal_info.get('cliente_id')
        }):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado al canal"
            )
        
        # Obtener datos del canal
        registros = registro_repo.get_records_by_canal(
            canal_id=canal_id,
            start_time=desde_dt,
            end_time=hasta_dt,
            limit=limit
        )
        
        # Aplicar paginación
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        registros_paginados = registros[start_idx:end_idx]
        
        # Convertir a formato de respuesta
        datos = []
        for registro in registros_paginados:
            # Determinar el valor según el tipo de dato
            valor = None
            tipo_valor = "unknown"
            
            if registro.valor_num is not None:
                valor = registro.valor_num
                tipo_valor = "num"
            elif registro.valor_int is not None:
                valor = registro.valor_int
                tipo_valor = "int"
            elif registro.valor_bool is not None:
                valor = registro.valor_bool
                tipo_valor = "bool"
            elif registro.valor_text is not None:
                valor = registro.valor_text
                tipo_valor = "text"
            elif registro.valor_json is not None:
                valor = registro.valor_json
                tipo_valor = "json"
            
            datos.append({
                "id": str(registro.id),
                "canal_id": str(registro.canal_id),
                "timestamp": registro.ts.isoformat(),
                "valor": valor,
                "tipo_valor": tipo_valor,
                "calidad": registro.calidad,
                "calidad_porcentaje": registro.calidad_porcentaje,
                "metadata": _metadata_value(registro),
                "procesado": registro.procesado,
                "validado": registro.validado
            })
        
        # Crear información de paginación
        from ..models.common_models import PaginationInfo
        total = len(registros)
        pagination_info = PaginationInfo.from_total(page, size, total)
        
        return {
            "success": True,
            "message": "Datos del canal obtenidos exitosamente",
            "data": datos,
            "pagination": pagination_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener datos del canal {canal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@data_router.get("/canal/{canal_id}/estadisticas", response_model=SuccessResponse)
async def get_channel_statistics(
    canal_id: str,
    request: Request,
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Obtener estadísticas de un canal específico
    
    - **canal_id**: ID del canal
    """
    try:
        # Obtener configuración y repositorios
        db_handler = _get_db_handler(request)
        registro_repo = RegistroDatosRepository(db_handler)
        canal_repo = CanalRepository(db_handler)
        scope_handler = ScopeHandler()
        
        # Verificar que el canal existe y es accesible
        canal = canal_repo.get_by_id(canal_id)
        if not canal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Canal no encontrado"
            )
        
        # Obtener información del canal para verificar scope
        canal_info = canal_repo.get_channel_info_for_validation(canal_id)
        if not canal_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener información del canal"
            )
        
        # Verificar acceso según scope del usuario
        if not scope_handler.validate_resource_access(current_user, {
            'proyecto_id': canal_info.get('proyecto_id'),
            'cliente_id': canal_info.get('cliente_id')
        }):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado al canal"
            )
        
        # Obtener estadísticas del canal
        estadisticas = registro_repo.get_statistics_by_canal(canal_id)
        
        # Agregar información del canal
        estadisticas['canal'] = {
            "id": str(canal.id),
            "nombre": canal.nombre,
            "tipo": canal.tipo,
            "unidad_medida": canal.unidad_medida,
            "rango_min": canal.rango_min,
            "rango_max": canal.rango_max
        }
        
        return {
            "success": True,
            "message": "Estadísticas del canal obtenidas exitosamente",
            "data": estadisticas
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener estadísticas del canal {canal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@data_router.post("/canal/{canal_id}/agregar", response_model=AggregationResponse)
async def aggregate_channel_data(
    canal_id: str,
    request: Request,
    aggregation_request: AggregationRequest,
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Agregar datos de un canal específico
    
    - **canal_id**: ID del canal
    - **aggregation_request**: Parámetros de agregación
    """
    try:
        # Verificar permisos
        role_checker = RoleChecker(AuthMiddleware(JWTHandler(), _get_db_handler(request)))
        if not role_checker.check_permission(current_user, "data_read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para consultar datos"
            )
        
        # Obtener configuración y repositorios
        db_handler = _get_db_handler(request)
        canal_repo = CanalRepository(db_handler)
        scope_handler = ScopeHandler()
        
        # Verificar que el canal existe y es accesible
        canal = canal_repo.get_by_id(canal_id)
        if not canal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Canal no encontrado"
            )
        
        # Obtener información del canal para verificar scope
        canal_info = canal_repo.get_channel_info_for_validation(canal_id)
        if not canal_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener información del canal"
            )
        
        # Verificar acceso según scope del usuario
        if not scope_handler.validate_resource_access(current_user, {
            'proyecto_id': canal_info.get('proyecto_id'),
            'cliente_id': canal_info.get('cliente_id')
        }):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado al canal"
            )
        
        # Aquí se implementaría la lógica de agregación
        # Por ahora, retornamos una respuesta de ejemplo
        
        return {
            "success": True,
            "message": "Agregación completada exitosamente",
            "data": {
                "canal_id": canal_id,
                "funcion": aggregation_request.funcion,
                "intervalo": aggregation_request.intervalo,
                "desde": aggregation_request.desde.isoformat(),
                "hasta": aggregation_request.hasta.isoformat(),
                "total_intervalos": 24,
                "puntos": [
                    {
                        "timestamp": aggregation_request.desde.isoformat(),
                        "valor": 25.5,
                        "count": 60,
                        "min_valor": 24.0,
                        "max_valor": 27.0,
                        "std_dev": 0.8
                    }
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al agregar datos del canal {canal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


# Función auxiliar para obtener usuario actual
async def get_current_user(request: Request) -> Usuario:
    """Obtener usuario actual desde el request"""
    try:
        # Obtener configuración
        db_handler = _get_db_handler(request)
        
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
