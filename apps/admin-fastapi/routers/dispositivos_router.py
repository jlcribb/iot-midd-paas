"""
Router CRUD para Dispositivos del Proyecto
"""

from fastapi import APIRouter, Request, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
from datetime import date
import logging
from uuid import UUID, uuid5, NAMESPACE_DNS

from iot_middleware.storage.repositories import (
    DispositivoProyectoRepository,
    DispositivoRepository,
    ProyectoRepository
)
from iot_middleware.models.enums import ProtocoloComunicacion

logger = logging.getLogger(__name__)

router = APIRouter()


class DispositivoProyectoCreate(BaseModel):
    proyecto_id: str
    dispositivo_id: str
    unidad_id: Optional[str] = None
    nombre_personalizado: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_instalacion: date
    ubicacion_fisica: Optional[str] = None
    responsable: Optional[str] = None
    responsable_email: Optional[str] = None
    responsable_telefono: Optional[str] = None
    configuracion: Dict[str, Any] = {}
    
    @field_validator("unidad_id", mode="before")
    def _coerce_empty_unidad(cls, value):
        if value in ("", None):
            return None
        return value


class DispositivoProyectoUpdate(BaseModel):
    unidad_id: Optional[str] = None
    nombre_personalizado: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_retiro: Optional[date] = None
    estado: Optional[str] = None
    activo: Optional[bool] = None
    ubicacion_fisica: Optional[str] = None
    responsable: Optional[str] = None
    responsable_email: Optional[str] = None
    responsable_telefono: Optional[str] = None
    configuracion: Optional[Dict[str, Any]] = None
    
    @field_validator("unidad_id", mode="before")
    def _coerce_empty_unidad(cls, value):
        if value in ("", None):
            return None
        return value


class DispositivoProyectoResponse(BaseModel):
    id: str
    proyecto_id: str
    dispositivo_id: str
    dispositivo_nombre: Optional[str] = None
    unidad_id: Optional[str]
    nombre_personalizado: Optional[str]
    descripcion: Optional[str]
    fecha_instalacion: date
    fecha_retiro: Optional[date]
    estado: str
    ubicacion_fisica: Optional[str]
    responsable: Optional[str]
    responsable_email: Optional[str]
    responsable_telefono: Optional[str]
    activo: bool
    is_active: bool
    creado_en: str

    class Config:
        from_attributes = True


def get_repositories(request: Request):
    """Obtener repositorios desde el request"""
    db_handler = request.app.state.db_handler
    if not db_handler:
        raise HTTPException(status_code=500, detail="Base de datos no inicializada")
    
    repos = {
        'proyecto': ProyectoRepository(db_handler)
    }
    
    # Repositorios opcionales
    try:
        repos['dispositivo_proyecto'] = DispositivoProyectoRepository(db_handler)
    except:
        repos['dispositivo_proyecto'] = None
    
    try:
        repos['dispositivo'] = DispositivoRepository(db_handler)
    except:
        repos['dispositivo'] = None
    
    return repos


def _resolve_dispositivo_nombre(repos, dispositivo_id: str) -> Optional[str]:
    repo = repos.get('dispositivo')
    if not repo:
        return None
    dispositivo = repo.get_by_id(dispositivo_id)
    if not dispositivo:
        return None
    return (
        dispositivo.modelo
        or dispositivo.tipo
        or dispositivo.identificador_unico
    )


def _estado_to_text(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _is_dispositivo_activo(dispositivo: Any) -> bool:
    return _estado_to_text(getattr(dispositivo, "estado", "")).strip().lower() == "activo"


@router.get("/", response_model=List[DispositivoProyectoResponse])
async def list_dispositivos(
    request: Request,
    proyecto_id: Optional[str] = Query(None),
    unidad_id: Optional[str] = Query(None),
    activo: Optional[bool] = Query(True)
):
    """Listar dispositivos del proyecto"""
    try:
        repos = get_repositories(request)
        
        if not repos['dispositivo_proyecto']:
            return []
        
        if unidad_id:
            dispositivos = repos['dispositivo_proyecto'].get_by_unidad(unidad_id)
        elif proyecto_id:
            dispositivos = repos['dispositivo_proyecto'].get_by_proyecto(proyecto_id)
        else:
            dispositivos = repos['dispositivo_proyecto'].get_all()

        # Filtros combinados
        if proyecto_id:
            dispositivos = [d for d in dispositivos if str(d.proyecto_id) == proyecto_id]
        if unidad_id:
            dispositivos = [d for d in dispositivos if d.unidad_id and str(d.unidad_id) == unidad_id]
        if activo is not None:
            dispositivos = [d for d in dispositivos if _is_dispositivo_activo(d) == activo]
        
        return [
            DispositivoProyectoResponse(
                id=str(d.id),
                proyecto_id=str(d.proyecto_id),
                dispositivo_id=str(d.dispositivo_id),
                dispositivo_nombre=_resolve_dispositivo_nombre(repos, str(d.dispositivo_id)),
                unidad_id=str(d.unidad_id) if d.unidad_id else None,
                nombre_personalizado=d.nombre_personalizado,
                descripcion=d.descripcion,
                fecha_instalacion=d.fecha_instalacion,
                fecha_retiro=d.fecha_retiro,
                estado=_estado_to_text(d.estado),
                ubicacion_fisica=d.ubicacion_fisica,
                responsable=d.responsable,
                responsable_email=d.responsable_email,
                responsable_telefono=d.responsable_telefono,
                activo=_is_dispositivo_activo(d),
                is_active=_is_dispositivo_activo(d),
                creado_en=d.creado_en.isoformat() if d.creado_en else ""
            )
            for d in dispositivos
        ]
    except Exception as e:
        logger.error(f"Error al listar dispositivos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dispositivo_id}", response_model=DispositivoProyectoResponse)
async def get_dispositivo(request: Request, dispositivo_id: str):
    """Obtener un dispositivo por ID"""
    try:
        repos = get_repositories(request)
        
        if not repos['dispositivo_proyecto']:
            raise HTTPException(status_code=500, detail="Repositorio de dispositivos no disponible")
        
        dispositivo = repos['dispositivo_proyecto'].get_by_id(dispositivo_id)
        if not dispositivo:
            raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
        
        return DispositivoProyectoResponse(
            id=str(dispositivo.id),
            proyecto_id=str(dispositivo.proyecto_id),
            dispositivo_id=str(dispositivo.dispositivo_id),
            dispositivo_nombre=_resolve_dispositivo_nombre(repos, str(dispositivo.dispositivo_id)),
            unidad_id=str(dispositivo.unidad_id) if dispositivo.unidad_id else None,
            nombre_personalizado=dispositivo.nombre_personalizado,
            descripcion=dispositivo.descripcion,
            fecha_instalacion=dispositivo.fecha_instalacion,
            fecha_retiro=dispositivo.fecha_retiro,
            estado=_estado_to_text(dispositivo.estado),
            ubicacion_fisica=dispositivo.ubicacion_fisica,
            responsable=dispositivo.responsable,
            responsable_email=dispositivo.responsable_email,
            responsable_telefono=dispositivo.responsable_telefono,
            activo=_is_dispositivo_activo(dispositivo),
            is_active=_is_dispositivo_activo(dispositivo),
            creado_en=dispositivo.creado_en.isoformat() if dispositivo.creado_en else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener dispositivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=DispositivoProyectoResponse)
async def create_dispositivo(request: Request, dispositivo_data: DispositivoProyectoCreate):
    """Crear un nuevo dispositivo en proyecto"""
    try:
        repos = get_repositories(request)
        
        if not repos['dispositivo_proyecto']:
            raise HTTPException(status_code=500, detail="Repositorio de dispositivos no disponible")
        
        # Verificar que el proyecto existe
        proyecto = repos['proyecto'].get_by_id(dispositivo_data.proyecto_id)
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        # Normalizar/crear dispositivo base si hace falta
        if repos.get('dispositivo'):
            raw_dispositivo_id = dispositivo_data.dispositivo_id.strip()
            try:
                dispositivo_uuid = UUID(raw_dispositivo_id)
            except Exception:
                dispositivo_uuid = uuid5(NAMESPACE_DNS, raw_dispositivo_id)
            
            dispositivo_id = str(dispositivo_uuid)
            dispositivo_base = repos['dispositivo'].get_by_id(dispositivo_id)
            if not dispositivo_base:
                dispositivo_base = repos['dispositivo'].create({
                    'id': dispositivo_id,
                    'tipo': 'sensor',
                    'identificador_unico': raw_dispositivo_id,
                    'protocolo': ProtocoloComunicacion.MQTT,
                    'activo': True
                })
            if not dispositivo_base:
                raise HTTPException(status_code=500, detail="No se pudo crear el dispositivo base")
        else:
            dispositivo_id = dispositivo_data.dispositivo_id
        
        data = dispositivo_data.model_dump()
        data['dispositivo_id'] = dispositivo_id
        dispositivo = repos['dispositivo_proyecto'].create(data)
        
        if not dispositivo:
            raise HTTPException(status_code=500, detail="Error al crear dispositivo")
        
        return DispositivoProyectoResponse(
            id=str(dispositivo.id),
            proyecto_id=str(dispositivo.proyecto_id),
            dispositivo_id=str(dispositivo.dispositivo_id),
            dispositivo_nombre=_resolve_dispositivo_nombre(repos, str(dispositivo.dispositivo_id)),
            unidad_id=str(dispositivo.unidad_id) if dispositivo.unidad_id else None,
            nombre_personalizado=dispositivo.nombre_personalizado,
            descripcion=dispositivo.descripcion,
            fecha_instalacion=dispositivo.fecha_instalacion,
            fecha_retiro=dispositivo.fecha_retiro,
            estado=_estado_to_text(dispositivo.estado),
            ubicacion_fisica=dispositivo.ubicacion_fisica,
            responsable=dispositivo.responsable,
            responsable_email=dispositivo.responsable_email,
            responsable_telefono=dispositivo.responsable_telefono,
            activo=_is_dispositivo_activo(dispositivo),
            is_active=_is_dispositivo_activo(dispositivo),
            creado_en=dispositivo.creado_en.isoformat() if dispositivo.creado_en else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear dispositivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{dispositivo_id}", response_model=DispositivoProyectoResponse)
async def update_dispositivo(request: Request, dispositivo_id: str, dispositivo_data: DispositivoProyectoUpdate):
    """Actualizar un dispositivo"""
    try:
        repos = get_repositories(request)
        
        if not repos['dispositivo_proyecto']:
            raise HTTPException(status_code=500, detail="Repositorio de dispositivos no disponible")
        
        data = dispositivo_data.model_dump(exclude_unset=True)
        if 'estado' in data and data['estado']:
            from iot_middleware.models.enums import EstadoDispositivo
            data['estado'] = EstadoDispositivo[data['estado'].upper()]
        if 'activo' in data:
            from iot_middleware.models.enums import EstadoDispositivo
            activo_value = bool(data.pop('activo'))
            data['estado'] = EstadoDispositivo.ACTIVO if activo_value else EstadoDispositivo.INACTIVO
            if not activo_value and 'fecha_retiro' not in data:
                data['fecha_retiro'] = date.today()
        
        dispositivo = repos['dispositivo_proyecto'].update(dispositivo_id, data)
        
        if not dispositivo:
            raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
        
        return DispositivoProyectoResponse(
            id=str(dispositivo.id),
            proyecto_id=str(dispositivo.proyecto_id),
            dispositivo_id=str(dispositivo.dispositivo_id),
            unidad_id=str(dispositivo.unidad_id) if dispositivo.unidad_id else None,
            nombre_personalizado=dispositivo.nombre_personalizado,
            descripcion=dispositivo.descripcion,
            fecha_instalacion=dispositivo.fecha_instalacion,
            fecha_retiro=dispositivo.fecha_retiro,
            estado=_estado_to_text(dispositivo.estado),
            ubicacion_fisica=dispositivo.ubicacion_fisica,
            responsable=dispositivo.responsable,
            responsable_email=dispositivo.responsable_email,
            responsable_telefono=dispositivo.responsable_telefono,
            activo=_is_dispositivo_activo(dispositivo),
            is_active=_is_dispositivo_activo(dispositivo),
            creado_en=dispositivo.creado_en.isoformat() if dispositivo.creado_en else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar dispositivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{dispositivo_id}")
async def delete_dispositivo(request: Request, dispositivo_id: str):
    """Eliminar un dispositivo (soft delete)"""
    try:
        repos = get_repositories(request)
        
        if not repos['dispositivo_proyecto']:
            raise HTTPException(status_code=500, detail="Repositorio de dispositivos no disponible")
        
        dispositivo_actual = repos['dispositivo_proyecto'].get_by_id(dispositivo_id)
        if not dispositivo_actual:
            raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

        from iot_middleware.models.enums import EstadoDispositivo
        data = {'estado': EstadoDispositivo.INACTIVO}
        if not getattr(dispositivo_actual, 'fecha_retiro', None):
            data['fecha_retiro'] = date.today()

        dispositivo = repos['dispositivo_proyecto'].update(dispositivo_id, data)
        
        if not dispositivo:
            raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

        # Si no hay más asociaciones activas para el dispositivo base, marcarlo inactivo.
        if repos.get('dispositivo'):
            same_device_links = [
                item for item in repos['dispositivo_proyecto'].get_all()
                if str(item.dispositivo_id) == str(dispositivo.dispositivo_id)
            ]
            active_links = [item for item in same_device_links if _is_dispositivo_activo(item)]
            if not active_links:
                repos['dispositivo'].update(str(dispositivo.dispositivo_id), {'activo': False})
        
        return {"message": "Dispositivo eliminado exitosamente", "id": dispositivo_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar dispositivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))
