"""
Router de Proyectos
===================

Este módulo define los endpoints para gestión de proyectos,
con control de acceso basado en roles y scoping automático.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from typing import Optional, List
import logging

from ..models.common_models import (
    PaginatedResponse,
    SuccessResponse,
    ErrorResponse,
    PaginationParams
)
from ..models.data_models import TimeSeriesRequest, TimeSeriesResponse
from ..auth import AuthMiddleware, RoleChecker, ScopeHandler, JWTHandler
from ...storage.db_handler import create_database_handler
from ...storage.repositories import ProyectoRepository, CanalRepository, RegistroDatosRepository
from ...models.entities import Usuario, Proyecto
from ...models.enums import RolUsuario

# Configurar logging
logger = logging.getLogger(__name__)


def _get_db_handler(request: Request):
    return create_database_handler(config=request.app.state.config)


def _metadata_value(record):
    return getattr(record, "metadatos", getattr(record, "metadata", None))

# Crear router
projects_router = APIRouter(
    prefix="/proyectos",
    tags=["Proyectos"],
    responses={
        401: {"model": ErrorResponse, "description": "No autorizado"},
        403: {"model": ErrorResponse, "description": "Acceso denegado"},
        404: {"model": ErrorResponse, "description": "Recurso no encontrado"},
        422: {"model": ErrorResponse, "description": "Error de validación"}
    }
)


@projects_router.get("/", response_model=PaginatedResponse)
async def get_projects(
    request: Request,
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    cliente_id: Optional[str] = Query(None, description="Filtrar por cliente"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Obtener lista de proyectos con paginación y filtros
    
    - **page**: Número de página
    - **size**: Tamaño de página
    - **cliente_id**: Filtrar por cliente específico
    - **estado**: Filtrar por estado del proyecto
    - **activo**: Filtrar por estado activo
    """
    try:
        # Obtener configuración y repositorios
        db_handler = _get_db_handler(request)
        proyecto_repo = ProyectoRepository(db_handler)
        scope_handler = ScopeHandler()
        
        # Construir filtros base
        base_filters = {}
        if cliente_id:
            base_filters['cliente_id'] = cliente_id
        if estado:
            base_filters['estado'] = estado
        if activo is not None:
            base_filters['activo'] = activo
        
        # Aplicar scope del usuario
        scope_filters = scope_handler.get_user_scope_filters(current_user)
        combined_filters = scope_handler.apply_scope_to_filters(base_filters, current_user)
        
        # Obtener proyectos con filtros aplicados
        proyectos = proyecto_repo.find_by_criteria(
            combined_filters,
            limit=size
        )
        
        # Contar total para paginación
        total = proyecto_repo.count(combined_filters)
        
        # Aplicar paginación
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        proyectos_paginados = proyectos[start_idx:end_idx]
        
        # Convertir a formato de respuesta
        proyectos_data = []
        for proyecto in proyectos_paginados:
            proyectos_data.append({
                "id": str(proyecto.id),
                "nombre": proyecto.nombre,
                "descripcion": proyecto.descripcion,
                "estado": proyecto.estado,
                "fecha_inicio": proyecto.fecha_inicio.isoformat() if proyecto.fecha_inicio else None,
                "fecha_fin": proyecto.fecha_fin.isoformat() if proyecto.fecha_fin else None,
                "presupuesto": float(proyecto.presupuesto) if proyecto.presupuesto else None,
                "prioridad": proyecto.prioridad,
                "activo": proyecto.activo,
                "cliente_id": str(proyecto.cliente_id) if proyecto.cliente_id else None,
                "creado_en": proyecto.creado_en.isoformat() if proyecto.creado_en else None
            })
        
        # Crear información de paginación
        from ..models.common_models import PaginationInfo
        pagination_info = PaginationInfo.from_total(page, size, total)
        
        return {
            "success": True,
            "message": "Proyectos obtenidos exitosamente",
            "data": proyectos_data,
            "pagination": pagination_info
        }
        
    except Exception as e:
        logger.error(f"Error al obtener proyectos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@projects_router.get("/{proyecto_id}", response_model=SuccessResponse)
async def get_project(
    proyecto_id: str,
    request: Request,
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Obtener proyecto específico por ID
    
    - **proyecto_id**: ID único del proyecto
    """
    try:
        # Obtener configuración y repositorios
        db_handler = _get_db_handler(request)
        proyecto_repo = ProyectoRepository(db_handler)
        scope_handler = ScopeHandler()
        
        # Obtener proyecto
        proyecto = proyecto_repo.get_by_id(proyecto_id)
        if not proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado"
            )
        
        # Verificar acceso según scope del usuario
        if not scope_handler.validate_resource_access(current_user, {
            'cliente_id': str(proyecto.cliente_id) if proyecto.cliente_id else None,
            'proyecto_id': str(proyecto.id)
        }):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado al proyecto"
            )
        
        # Obtener detalles completos del proyecto
        detalles = proyecto_repo.get_project_details(proyecto_id)
        
        return {
            "success": True,
            "message": "Proyecto obtenido exitosamente",
            "data": detalles
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener proyecto {proyecto_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@projects_router.get("/{proyecto_id}/series", response_model=TimeSeriesResponse)
async def get_project_time_series(
    proyecto_id: str,
    request: Request,
    canal_id: str = Query(..., description="ID del canal"),
    desde: str = Query(..., description="Fecha de inicio (ISO 8601)"),
    hasta: str = Query(..., description="Fecha de fin (ISO 8601)"),
    freq: str = Query("1m", description="Frecuencia de muestreo"),
    limit: int = Query(1000, ge=1, le=10000, description="Límite de registros"),
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Obtener serie temporal de datos para un proyecto específico
    
    - **proyecto_id**: ID del proyecto
    - **canal_id**: ID del canal
    - **desde**: Fecha de inicio
    - **hasta**: Fecha de fin
    - **freq**: Frecuencia de muestreo
    - **limit**: Límite de registros
    """
    try:
        from datetime import datetime
        
        # Parsear fechas
        try:
            desde_dt = datetime.fromisoformat(desde.replace('Z', '+00:00'))
            hasta_dt = datetime.fromisoformat(hasta.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)"
            )
        
        # Validar rango de fechas
        if hasta_dt <= desde_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha de fin debe ser posterior a la de inicio"
            )
        
        # Obtener configuración y repositorios
        db_handler = _get_db_handler(request)
        proyecto_repo = ProyectoRepository(db_handler)
        canal_repo = CanalRepository(db_handler)
        registro_repo = RegistroDatosRepository(db_handler)
        scope_handler = ScopeHandler()
        
        # Verificar que el proyecto existe y es accesible
        proyecto = proyecto_repo.get_by_id(proyecto_id)
        if not proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado"
            )
        
        # Verificar acceso según scope del usuario
        if not scope_handler.validate_resource_access(current_user, {
            'cliente_id': str(proyecto.cliente_id) if proyecto.cliente_id else None,
            'proyecto_id': str(proyecto.id)
        }):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado al proyecto"
            )
        
        # Verificar que el canal pertenece al proyecto
        canales_proyecto = canal_repo.get_channels_by_project(proyecto_id)
        canal_encontrado = None
        for canal in canales_proyecto:
            if str(canal.id) == canal_id:
                canal_encontrado = canal
                break
        
        if not canal_encontrado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Canal no encontrado en el proyecto"
            )
        
        # Obtener datos de la serie temporal
        registros = registro_repo.get_records_by_canal(
            canal_id=canal_id,
            start_time=desde_dt,
            end_time=hasta_dt,
            limit=limit
        )
        
        # Convertir a formato de respuesta
        series_data = []
        for registro in registros:
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
            
            series_data.append({
                "timestamp": registro.ts.isoformat(),
                "valor": valor,
                "calidad": registro.calidad,
                "calidad_porcentaje": registro.calidad_porcentaje,
                "metadata": _metadata_value(registro)
            })
        
        # Crear respuesta
        response_data = {
            "canal_id": canal_id,
            "canal_nombre": canal_encontrado.nombre,
            "tipo_dato": canal_encontrado.tipo,
            "unidad_medida": canal_encontrado.unidad_medida,
            "desde": desde,
            "hasta": hasta,
            "freq": freq,
            "total_puntos": len(series_data),
            "series": series_data
        }
        
        return {
            "success": True,
            "message": "Serie temporal obtenida exitosamente",
            "data": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener serie temporal del proyecto {proyecto_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@projects_router.post("/", response_model=SuccessResponse)
async def create_project(
    request: Request,
    project_data: dict,
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Crear nuevo proyecto (solo administradores y técnicos)
    
    - **project_data**: Datos del proyecto a crear
    """
    try:
        # Verificar permisos
        role_checker = RoleChecker(AuthMiddleware(JWTHandler(), _get_db_handler(request)))
        if not role_checker.check_permission(current_user, "project_management"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para crear proyectos"
            )
        
        # Obtener configuración y repositorios
        db_handler = _get_db_handler(request)
        proyecto_repo = ProyectoRepository(db_handler)
        
        # Crear proyecto
        proyecto_creado = proyecto_repo.create(project_data)
        
        if not proyecto_creado:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear el proyecto"
            )
        
        return {
            "success": True,
            "message": "Proyecto creado exitosamente",
            "data": {
                "id": str(proyecto_creado.id),
                "nombre": proyecto_creado.nombre
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear proyecto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@projects_router.put("/{proyecto_id}", response_model=SuccessResponse)
async def update_project(
    proyecto_id: str,
    request: Request,
    project_data: dict,
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Actualizar proyecto existente
    
    - **proyecto_id**: ID del proyecto a actualizar
    - **project_data**: Datos a actualizar
    """
    try:
        # Obtener configuración y repositorios
        db_handler = _get_db_handler(request)
        proyecto_repo = ProyectoRepository(db_handler)
        scope_handler = ScopeHandler()
        
        # Verificar que el proyecto existe
        proyecto = proyecto_repo.get_by_id(proyecto_id)
        if not proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado"
            )
        
        # Verificar permisos
        role_checker = RoleChecker(AuthMiddleware(JWTHandler(), _get_db_handler(request)))
        if not role_checker.check_permission(current_user, "project_management", proyecto_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para actualizar este proyecto"
            )
        
        # Actualizar proyecto
        proyecto_actualizado = proyecto_repo.update(proyecto_id, project_data)
        
        if not proyecto_actualizado:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar el proyecto"
            )
        
        return {
            "success": True,
            "message": "Proyecto actualizado exitosamente",
            "data": {
                "id": str(proyecto_actualizado.id),
                "nombre": proyecto_actualizado.nombre
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar proyecto {proyecto_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@projects_router.delete("/{proyecto_id}", response_model=SuccessResponse)
async def delete_project(
    proyecto_id: str,
    request: Request,
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Eliminar proyecto (solo administradores)
    
    - **proyecto_id**: ID del proyecto a eliminar
    """
    try:
        # Verificar permisos (solo administradores)
        if current_user.rol != RolUsuario.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los administradores pueden eliminar proyectos"
            )
        
        # Obtener configuración y repositorios
        db_handler = _get_db_handler(request)
        proyecto_repo = ProyectoRepository(db_handler)
        
        # Verificar que el proyecto existe
        proyecto = proyecto_repo.get_by_id(proyecto_id)
        if not proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado"
            )
        
        # Eliminar proyecto
        eliminado = proyecto_repo.delete(proyecto_id)
        
        if not eliminado:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar el proyecto"
            )
        
        return {
            "success": True,
            "message": "Proyecto eliminado exitosamente",
            "data": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar proyecto {proyecto_id}: {e}")
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
