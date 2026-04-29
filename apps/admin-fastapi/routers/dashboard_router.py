"""
Router para Dashboard de Estados de Proyectos
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
import logging

from iot_middleware.storage.repositories import (
    ProyectoRepository,
    UnidadProyectoRepository,
    ClienteRepository,
    DispositivoProyectoRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _estado_value(estado: Any) -> str:
    if hasattr(estado, "value"):
        return str(estado.value)
    return str(estado)


def _dispositivo_activo(dispositivo: Any) -> bool:
    estado = _estado_value(getattr(dispositivo, "estado", ""))
    return estado.strip().lower() == "activo"


class ProyectoEstadoResponse(BaseModel):
    id: str
    nombre: str
    estado: str
    cliente_nombre: str
    total_unidades: int
    unidades_activas: int
    total_dispositivos: int
    dispositivos_activos: int
    fecha_inicio: str
    fecha_fin: str
    activo: bool


class DashboardStatsResponse(BaseModel):
    total_proyectos: int
    proyectos_activos: int
    proyectos_planificados: int
    proyectos_en_curso: int
    proyectos_cerrados: int
    total_unidades: int
    total_dispositivos: int
    proyectos: List[ProyectoEstadoResponse]


def get_repositories(request: Request):
    """Obtener repositorios desde el request"""
    db_handler = request.app.state.db_handler
    if not db_handler:
        raise HTTPException(status_code=500, detail="Base de datos no inicializada")
    
    repos = {
        'proyecto': ProyectoRepository(db_handler),
        'unidad': UnidadProyectoRepository(db_handler),
        'cliente': ClienteRepository(db_handler),
    }
    try:
        repos['dispositivo_proyecto'] = DispositivoProyectoRepository(db_handler)
    except Exception:
        repos['dispositivo_proyecto'] = None
    return repos


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(request: Request):
    """Obtener estadísticas generales del dashboard"""
    try:
        repos = get_repositories(request)
        
        # Obtener todos los proyectos
        proyectos = repos['proyecto'].get_all()
        unidades = repos['unidad'].get_all()
        dispositivos = repos['dispositivo_proyecto'].get_all() if repos.get('dispositivo_proyecto') else []
        
        # Calcular estadísticas
        total_proyectos = len(proyectos)
        proyectos_activos = len([p for p in proyectos if p.activo])
        proyectos_planificados = len([p for p in proyectos if _estado_value(p.estado) == 'planificado'])
        proyectos_en_curso = len([p for p in proyectos if _estado_value(p.estado) == 'activo'])
        proyectos_cerrados = len([p for p in proyectos if _estado_value(p.estado) == 'cerrado'])
        
        total_unidades_activas = len([u for u in unidades if u.activo])
        total_dispositivos_activos = len([d for d in dispositivos if _dispositivo_activo(d)])
        
        # Obtener clientes para nombres
        clientes = {str(c.id): c.nombre for c in repos['cliente'].get_all()}
        
        # Preparar respuesta de proyectos con estados
        proyectos_respuesta = []
        for proyecto in proyectos:
            # Contar unidades del proyecto
            unidades_proyecto = [u for u in unidades if str(u.proyecto_id) == str(proyecto.id)]
            unidades_activas = len([u for u in unidades_proyecto if u.activo])
            
            dispositivos_proyecto = [d for d in dispositivos if str(d.proyecto_id) == str(proyecto.id)]
            total_dispositivos = len(dispositivos_proyecto)
            dispositivos_activos = len([d for d in dispositivos_proyecto if _dispositivo_activo(d)])
            
            proyectos_respuesta.append(ProyectoEstadoResponse(
                id=str(proyecto.id),
                nombre=proyecto.nombre,
                estado=_estado_value(proyecto.estado),
                cliente_nombre=clientes.get(str(proyecto.cliente_id), "Desconocido"),
                total_unidades=len(unidades_proyecto),
                unidades_activas=unidades_activas,
                total_dispositivos=total_dispositivos,
                dispositivos_activos=dispositivos_activos,
                fecha_inicio=proyecto.fecha_inicio.isoformat() if proyecto.fecha_inicio else "",
                fecha_fin=proyecto.fecha_fin.isoformat() if proyecto.fecha_fin else "",
                activo=proyecto.activo
            ))
        
        return DashboardStatsResponse(
            total_proyectos=total_proyectos,
            proyectos_activos=proyectos_activos,
            proyectos_planificados=proyectos_planificados,
            proyectos_en_curso=proyectos_en_curso,
            proyectos_cerrados=proyectos_cerrados,
            total_unidades=total_unidades_activas,
            total_dispositivos=total_dispositivos_activos,
            proyectos=proyectos_respuesta
        )
    except Exception as e:
        logger.error(f"Error al obtener estadísticas del dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proyecto/{proyecto_id}/estado")
async def get_proyecto_estado(request: Request, proyecto_id: str):
    """Obtener estado detallado de un proyecto"""
    try:
        repos = get_repositories(request)
        
        proyecto = repos['proyecto'].get_by_id(proyecto_id)
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        # Obtener unidades del proyecto
        unidades = repos['unidad'].get_by_proyecto(proyecto_id)
        dispositivos = repos['dispositivo_proyecto'].get_by_proyecto(proyecto_id) if repos.get('dispositivo_proyecto') else []
        
        # Obtener cliente
        cliente = repos['cliente'].get_by_id(str(proyecto.cliente_id))
        
        return {
            "proyecto": {
                "id": str(proyecto.id),
                "nombre": proyecto.nombre,
                "estado": _estado_value(proyecto.estado),
                "activo": proyecto.activo,
                "fecha_inicio": proyecto.fecha_inicio.isoformat() if proyecto.fecha_inicio else None,
                "fecha_fin": proyecto.fecha_fin.isoformat() if proyecto.fecha_fin else None
            },
            "cliente": {
                "id": str(cliente.id) if cliente else None,
                "nombre": cliente.nombre if cliente else "Desconocido"
            },
            "unidades": {
                "total": len(unidades),
                "activas": len([u for u in unidades if u.activo]),
                "lista": [
                    {
                        "id": str(u.id),
                        "nombre": u.nombre,
                        "activo": u.activo,
                        "ubicacion": u.ubicacion
                    }
                    for u in unidades
                ]
            },
            "dispositivos": {
                "total": len(dispositivos),
                "activos": len([d for d in dispositivos if _dispositivo_activo(d)])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener estado del proyecto: {e}")
        raise HTTPException(status_code=500, detail=str(e))
