"""
Router CRUD para Unidades de Proyecto
"""

from fastapi import APIRouter, Request, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import date
import logging

from iot_middleware.storage.repositories import (
    UnidadProyectoRepository,
    ProyectoRepository,
    DispositivoProyectoRepository,
)
from iot_middleware.models.entities import UnidadProyecto
from iot_middleware.models.enums import EstadoDispositivo

logger = logging.getLogger(__name__)

router = APIRouter()


class UnidadCreate(BaseModel):
    proyecto_id: str
    nombre: str
    descripcion: Optional[str] = None
    ubicacion: Optional[str] = None
    responsable: Optional[str] = None
    responsable_email: Optional[str] = None
    responsable_telefono: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    configuracion: Dict[str, Any] = {}


class UnidadUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    ubicacion: Optional[str] = None
    responsable: Optional[str] = None
    responsable_email: Optional[str] = None
    responsable_telefono: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    activo: Optional[bool] = None
    configuracion: Optional[Dict[str, Any]] = None


class UnidadResponse(BaseModel):
    id: str
    proyecto_id: str
    nombre: str
    descripcion: Optional[str]
    ubicacion: Optional[str]
    responsable: Optional[str]
    responsable_email: Optional[str]
    responsable_telefono: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    activo: bool
    creado_en: str
    actualizado_en: str

    class Config:
        from_attributes = True


def get_repositories(request: Request):
    """Obtener repositorios desde el request"""
    db_handler = request.app.state.db_handler
    if not db_handler:
        raise HTTPException(status_code=500, detail="Base de datos no inicializada")
    
    repos = {
        'unidad': UnidadProyectoRepository(db_handler),
        'proyecto': ProyectoRepository(db_handler),
    }
    try:
        repos['dispositivo_proyecto'] = DispositivoProyectoRepository(db_handler)
    except Exception:
        repos['dispositivo_proyecto'] = None
    return repos


@router.get("/", response_model=List[UnidadResponse])
async def list_unidades(
    request: Request,
    proyecto_id: Optional[str] = Query(None),
    activo: Optional[bool] = Query(True)
):
    """Listar unidades con filtros opcionales"""
    try:
        repos = get_repositories(request)
        unidad_repo = repos['unidad']
        
        if proyecto_id:
            unidades = unidad_repo.get_by_proyecto(proyecto_id)
        else:
            unidades = unidad_repo.get_all()
        if activo is not None:
            unidades = [u for u in unidades if bool(u.activo) == bool(activo)]
        
        return [
            UnidadResponse(
                id=str(u.id),
                proyecto_id=str(u.proyecto_id),
                nombre=u.nombre,
                descripcion=u.descripcion,
                ubicacion=u.ubicacion,
                responsable=u.responsable,
                responsable_email=u.responsable_email,
                responsable_telefono=u.responsable_telefono,
                lat=u.lat,
                lon=u.lon,
                activo=u.activo,
                creado_en=u.creado_en.isoformat() if u.creado_en else "",
                actualizado_en=u.actualizado_en.isoformat() if u.actualizado_en else ""
            )
            for u in unidades
        ]
    except Exception as e:
        logger.error(f"Error al listar unidades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{unidad_id}", response_model=UnidadResponse)
async def get_unidad(request: Request, unidad_id: str):
    """Obtener una unidad por ID"""
    try:
        repos = get_repositories(request)
        unidad = repos['unidad'].get_by_id(unidad_id)
        
        if not unidad:
            raise HTTPException(status_code=404, detail="Unidad no encontrada")
        
        return UnidadResponse(
            id=str(unidad.id),
            proyecto_id=str(unidad.proyecto_id),
            nombre=unidad.nombre,
            descripcion=unidad.descripcion,
            ubicacion=unidad.ubicacion,
            responsable=unidad.responsable,
            responsable_email=unidad.responsable_email,
            responsable_telefono=unidad.responsable_telefono,
            lat=unidad.lat,
            lon=unidad.lon,
            activo=unidad.activo,
            creado_en=unidad.creado_en.isoformat() if unidad.creado_en else "",
            actualizado_en=unidad.actualizado_en.isoformat() if unidad.actualizado_en else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener unidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=UnidadResponse)
async def create_unidad(request: Request, unidad_data: UnidadCreate):
    """Crear una nueva unidad"""
    try:
        repos = get_repositories(request)
        
        # Verificar que el proyecto existe
        proyecto = repos['proyecto'].get_by_id(unidad_data.proyecto_id)
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        unidad = repos['unidad'].create(unidad_data.model_dump())
        
        if not unidad:
            raise HTTPException(status_code=500, detail="Error al crear unidad")
        
        return UnidadResponse(
            id=str(unidad.id),
            proyecto_id=str(unidad.proyecto_id),
            nombre=unidad.nombre,
            descripcion=unidad.descripcion,
            ubicacion=unidad.ubicacion,
            responsable=unidad.responsable,
            responsable_email=unidad.responsable_email,
            responsable_telefono=unidad.responsable_telefono,
            lat=unidad.lat,
            lon=unidad.lon,
            activo=unidad.activo,
            creado_en=unidad.creado_en.isoformat() if unidad.creado_en else "",
            actualizado_en=unidad.actualizado_en.isoformat() if unidad.actualizado_en else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear unidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{unidad_id}", response_model=UnidadResponse)
async def update_unidad(request: Request, unidad_id: str, unidad_data: UnidadUpdate):
    """Actualizar una unidad"""
    try:
        repos = get_repositories(request)
        unidad = repos['unidad'].update(unidad_id, unidad_data.model_dump(exclude_unset=True))
        
        if not unidad:
            raise HTTPException(status_code=404, detail="Unidad no encontrada")
        
        return UnidadResponse(
            id=str(unidad.id),
            proyecto_id=str(unidad.proyecto_id),
            nombre=unidad.nombre,
            descripcion=unidad.descripcion,
            ubicacion=unidad.ubicacion,
            responsable=unidad.responsable,
            responsable_email=unidad.responsable_email,
            responsable_telefono=unidad.responsable_telefono,
            lat=unidad.lat,
            lon=unidad.lon,
            activo=unidad.activo,
            creado_en=unidad.creado_en.isoformat() if unidad.creado_en else "",
            actualizado_en=unidad.actualizado_en.isoformat() if unidad.actualizado_en else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar unidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{unidad_id}")
async def delete_unidad(request: Request, unidad_id: str):
    """Eliminar una unidad (soft delete)"""
    try:
        repos = get_repositories(request)
        unidad = repos['unidad'].update(unidad_id, {'activo': False})
        
        if not unidad:
            raise HTTPException(status_code=404, detail="Unidad no encontrada")

        dispositivos_actualizados = 0
        if repos.get('dispositivo_proyecto'):
            dispositivos = repos['dispositivo_proyecto'].get_by_unidad(unidad_id)
            for dispositivo in dispositivos:
                estado = (
                    str(dispositivo.estado.value).lower()
                    if hasattr(dispositivo.estado, "value")
                    else str(dispositivo.estado).lower()
                )
                if estado == "inactivo":
                    continue
                update_data = {'estado': EstadoDispositivo.INACTIVO}
                if not dispositivo.fecha_retiro:
                    update_data['fecha_retiro'] = date.today()
                updated = repos['dispositivo_proyecto'].update(str(dispositivo.id), update_data)
                if updated:
                    dispositivos_actualizados += 1
        
        return {
            "message": "Unidad eliminada exitosamente",
            "id": unidad_id,
            "dispositivos_actualizados": dispositivos_actualizados,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar unidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))
