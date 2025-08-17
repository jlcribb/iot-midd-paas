"""
API REST para Consulta de Datos de Sensores - IoT Middleware
============================================================

Este módulo proporciona endpoints REST para consultar datos de sensores
almacenados en la base de datos, con filtros por tópico y rango de fechas.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import json

# Importar módulos del proyecto
try:
    from ..models.entities import RegistroDatos, Canal, Dispositivo, UnidadProyecto, Proyecto
    from ..models.enums import CalidadDato
    from ..storage.db_handler import DatabaseHandler, create_database_handler
    from ..config import load_config
    from ..utils.auditoria import create_auditoria_service, ContextoAuditoria
except ImportError:
    # Fallback para importación directa
    from iot_middleware.models.entities import RegistroDatos, Canal, Dispositivo, UnidadProyecto, Proyecto
    from iot_middleware.models.enums import CalidadDato
    from iot_middleware.storage.db_handler import DatabaseHandler, create_database_handler
    from iot_middleware.config import load_config
    from iot_middleware.utils.auditoria import create_auditoria_service, ContextoAuditoria

# Configurar logging
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="IoT Middleware API",
    description="API REST para consulta de datos de sensores IoT",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar según necesidades de producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales
db_handler: Optional[DatabaseHandler] = None
auditoria_service = None


# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class SensorDataResponse(BaseModel):
    """Respuesta estándar para datos de sensores"""
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    data: List[Dict[str, Any]] = Field(..., description="Lista de registros de datos")
    metadata: Dict[str, Any] = Field(..., description="Metadatos de la consulta")
    pagination: Optional[Dict[str, Any]] = Field(None, description="Información de paginación")
    error: Optional[str] = Field(None, description="Mensaje de error si success=False")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": [
                    {
                        "id": 1,
                        "canal_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "valor": 25.5,
                        "tipo_valor": "numeric",
                        "calidad": "OK",
                        "calidad_porcentaje": 100,
                        "topic": "iot/proyecto_001/unidad_001/dispositivo_001/canal_temperatura",
                        "metadatos": {"unidad": "celsius", "ubicacion": "sala_principal"}
                    }
                ],
                "metadata": {
                    "total_registros": 1,
                    "filtros_aplicados": {
                        "topic": "iot/proyecto_001/+/+/+/canal_temperatura",
                        "fecha_desde": "2024-01-15T00:00:00Z",
                        "fecha_hasta": "2024-01-15T23:59:59Z"
                    },
                    "timestamp_consulta": "2024-01-15T10:35:00Z"
                },
                "pagination": {
                    "pagina_actual": 1,
                    "total_paginas": 1,
                    "registros_por_pagina": 100,
                    "total_registros": 1
                }
            }
        }


class ErrorResponse(BaseModel):
    """Respuesta estándar para errores"""
    success: bool = Field(False, description="Siempre False para errores")
    error: str = Field(..., description="Mensaje de error")
    error_code: str = Field(..., description="Código de error")
    timestamp: str = Field(..., description="Timestamp del error")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales del error")

    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": "Parámetros de consulta inválidos",
                "error_code": "INVALID_PARAMETERS",
                "timestamp": "2024-01-15T10:35:00Z",
                "details": {
                    "fecha_desde": "Formato de fecha inválido",
                    "fecha_hasta": "Debe ser posterior a fecha_desde"
                }
            }
        }


class HealthResponse(BaseModel):
    """Respuesta para el endpoint de salud"""
    status: str = Field(..., description="Estado del servicio")
    timestamp: str = Field(..., description="Timestamp de la verificación")
    version: str = Field(..., description="Versión de la API")
    database_status: str = Field(..., description="Estado de la base de datos")
    uptime_seconds: int = Field(..., description="Tiempo de funcionamiento en segundos")


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def get_db_session() -> Session:
    """Obtiene una sesión de base de datos"""
    if not db_handler:
        raise HTTPException(status_code=500, detail="Base de datos no inicializada")
    
    try:
        with db_handler.get_session() as session:
            yield session
    except Exception as e:
        logger.error(f"Error obteniendo sesión de BD: {e}")
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")


def get_auditoria_service():
    """Obtiene el servicio de auditoría"""
    return auditoria_service


def parse_topic_filter(topic_filter: str) -> Dict[str, str]:
    """
    Parsea un filtro de tópico y extrae componentes
    
    Args:
        topic_filter: Filtro de tópico (ej: "iot/proyecto_001/+/+/+/canal_temperatura")
    
    Returns:
        Diccionario con componentes del tópico
    """
    try:
        parts = topic_filter.split('/')
        if len(parts) >= 5:
            return {
                'proyecto': parts[1] if parts[1] != '+' else None,
                'unidad': parts[2] if parts[2] != '+' else None,
                'dispositivo': parts[3] if parts[3] != '+' else None,
                'canal': parts[4] if parts[4] != '+' else None,
                'pattern': topic_filter
            }
        return {'pattern': topic_filter}
    except Exception as e:
        logger.error(f"Error parseando filtro de tópico: {e}")
        return {'pattern': topic_filter}


def build_topic_query(session: Session, topic_filter: str) -> List[RegistroDatos]:
    """
    Construye la consulta SQL basada en el filtro de tópico
    
    Args:
        session: Sesión de base de datos
        topic_filter: Filtro de tópico
    
    Returns:
        Lista de registros que coinciden con el filtro
    """
    try:
        # Parsear el filtro de tópico
        topic_components = parse_topic_filter(topic_filter)
        
        # Construir consulta base
        query = session.query(RegistroDatos).join(Canal)
        
        # Aplicar filtros por componentes del tópico
        if topic_components.get('proyecto'):
            query = query.join(Dispositivo).join(UnidadProyecto).join(Proyecto)
            query = query.filter(Proyecto.nombre == topic_components['proyecto'])
        
        if topic_components.get('unidad'):
            if 'UnidadProyecto' not in [str(join) for join in query._join_entities]:
                query = query.join(Dispositivo).join(UnidadProyecto)
            query = query.filter(UnidadProyecto.nombre == topic_components['unidad'])
        
        if topic_components.get('dispositivo'):
            if 'Dispositivo' not in [str(join) for join in query._join_entities]:
                query = query.join(Dispositivo)
            query = query.filter(Dispositivo.nombre == topic_components['dispositivo'])
        
        if topic_components.get('canal'):
            query = query.filter(Canal.nombre == topic_components['canal'])
        
        return query
        
    except Exception as e:
        logger.error(f"Error construyendo consulta de tópico: {e}")
        raise HTTPException(status_code=500, detail="Error construyendo consulta de tópico")


def format_sensor_data(registro: RegistroDatos, topic: str) -> Dict[str, Any]:
    """
    Formatea un registro de datos de sensor para la respuesta
    
    Args:
        registro: Registro de datos de la base de datos
        topic: Tópico del registro
    
    Returns:
        Diccionario formateado para la respuesta
    """
    try:
        # Determinar el valor y tipo
        valor = None
        tipo_valor = None
        
        if registro.valor_num is not None:
            valor = registro.valor_num
            tipo_valor = "numeric"
        elif registro.valor_int is not None:
            valor = registro.valor_int
            tipo_valor = "integer"
        elif registro.valor_bool is not None:
            valor = registro.valor_bool
            tipo_valor = "boolean"
        elif registro.valor_text is not None:
            valor = registro.valor_text
            tipo_valor = "text"
        elif registro.valor_json is not None:
            valor = registro.valor_json
            tipo_valor = "json"
        
        # Formatear timestamp
        timestamp = registro.ts.isoformat() if registro.ts else None
        
        # Formatear metadatos
        metadatos = {}
        if registro.metadatos:
            metadatos = registro.metadatos
        
        # Agregar información del canal si está disponible
        if registro.canal:
            if not metadatos.get('unidad_medida') and registro.canal.unidad_medida:
                metadatos['unidad_medida'] = registro.canal.unidad_medida
            if not metadatos.get('descripcion') and registro.canal.descripcion:
                metadatos['descripcion'] = registro.canal.descripcion
        
        return {
            "id": registro.id,
            "canal_id": str(registro.canal_id) if registro.canal_id else None,
            "timestamp": timestamp,
            "valor": valor,
            "tipo_valor": tipo_valor,
            "calidad": registro.calidad.value if registro.calidad else None,
            "calidad_porcentaje": registro.calidad_porcentaje,
            "topic": topic,
            "metadatos": metadatos,
            "procesado": registro.procesado,
            "validado": registro.validado
        }
        
    except Exception as e:
        logger.error(f"Error formateando datos de sensor: {e}")
        return {
            "id": registro.id,
            "error": f"Error formateando datos: {e}"
        }


def get_topic_from_registro(registro: RegistroDatos, session: Session) -> str:
    """
    Obtiene el tópico completo para un registro
    
    Args:
        registro: Registro de datos
        session: Sesión de base de datos
    
    Returns:
        Tópico completo del registro
    """
    try:
        if not registro.canal:
            return "unknown/topic"
        
        # Construir tópico desde las relaciones
        topic_parts = ["iot"]
        
        # Obtener proyecto
        if registro.canal.dispositivo and registro.canal.dispositivo.unidad_proyecto:
            proyecto = registro.canal.dispositivo.unidad_proyecto.proyecto
            if proyecto:
                topic_parts.append(proyecto.nombre or "unknown")
            else:
                topic_parts.append("unknown")
        else:
            topic_parts.append("unknown")
        
        # Obtener unidad
        if registro.canal.dispositivo and registro.canal.dispositivo.unidad_proyecto:
            unidad = registro.canal.dispositivo.unidad_proyecto
            topic_parts.append(unidad.nombre or "unknown")
        else:
            topic_parts.append("unknown")
        
        # Obtener dispositivo
        if registro.canal.dispositivo:
            topic_parts.append(registro.canal.dispositivo.nombre or "unknown")
        else:
            topic_parts.append("unknown")
        
        # Obtener canal
        topic_parts.append(registro.canal.nombre or "unknown")
        
        return "/".join(topic_parts)
        
    except Exception as e:
        logger.error(f"Error obteniendo tópico: {e}")
        return "unknown/topic"


# ============================================================================
# ENDPOINTS DE LA API
# ============================================================================

@app.get("/", response_model=Dict[str, str])
async def root():
    """Endpoint raíz de la API"""
    return {
        "message": "IoT Middleware API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint de verificación de salud del servicio"""
    try:
        # Verificar estado de la base de datos
        db_status = "unknown"
        if db_handler:
            try:
                with db_handler.get_session() as session:
                    session.execute("SELECT 1")
                    db_status = "healthy"
            except Exception:
                db_status = "unhealthy"
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(timezone.utc).isoformat(),
            version="1.0.0",
            database_status=db_status,
            uptime_seconds=0  # Se puede implementar tracking de uptime
        )
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=500, detail="Error en health check")


@app.get("/data", response_model=SensorDataResponse)
async def get_sensor_data(
    topic: Optional[str] = Query(None, description="Filtro de tópico (ej: iot/proyecto_001/+/+/+/canal_temperatura)"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (ISO 8601)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (ISO 8601)"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a retornar"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    calidad: Optional[str] = Query(None, description="Filtrar por calidad de datos (OK, WARNING, ERROR)"),
    procesado: Optional[bool] = Query(None, description="Filtrar por estado de procesamiento"),
    validado: Optional[bool] = Query(None, description="Filtrar por estado de validación"),
    session: Session = Depends(get_db_session),
    request: Request = None
):
    """
    Obtiene los últimos N registros de datos de sensores
    
    Permite filtrar por:
    - Tópico (con comodines + para cualquier valor)
    - Rango de fechas
    - Calidad de datos
    - Estado de procesamiento y validación
    
    Retorna los datos en formato JSON estándar con metadatos y paginación.
    """
    try:
        # Registrar consulta en auditoría si está disponible
        if auditoria_service and request:
            try:
                # Obtener IP del cliente
                client_ip = request.client.host if request.client else "unknown"
                
                # Crear contexto de auditoría
                contexto = ContextoAuditoria(
                    usuario_id=None,  # Se puede implementar autenticación
                    ip_origen=client_ip,
                    user_agent=request.headers.get("user-agent"),
                    endpoint=str(request.url.path),
                    metodo_http=request.method,
                    parametros={
                        "topic": topic,
                        "fecha_desde": fecha_desde,
                        "fecha_hasta": fecha_hasta,
                        "limit": limit,
                        "offset": offset,
                        "calidad": calidad,
                        "procesado": procesado,
                        "validado": validado
                    }
                )
                
                auditoria_service.set_contexto(contexto)
                
                # Registrar consulta
                auditoria_service.registrar_cambio(
                    entidad="api_query",
                    entidad_id=None,
                    accion="CONSULTAR",
                    cambios={
                        "antes": {},
                        "despues": {
                            "endpoint": "/data",
                            "parametros": {
                                "topic": topic,
                                "fecha_desde": fecha_desde,
                                "fecha_hasta": fecha_hasta,
                                "limit": limit,
                                "offset": offset
                            }
                        }
                    }
                )
                
                auditoria_service.clear_contexto()
                
            except Exception as e:
                logger.warning(f"Error en auditoría de consulta: {e}")
        
        # Construir consulta base
        if topic:
            query = build_topic_query(session, topic)
        else:
            query = session.query(RegistroDatos)
        
        # Aplicar filtros de fecha
        if fecha_desde:
            try:
                fecha_desde_dt = datetime.fromisoformat(fecha_desde.replace('Z', '+00:00'))
                query = query.filter(RegistroDatos.ts >= fecha_desde_dt)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Formato de fecha inválido para fecha_desde: {fecha_desde}. Use formato ISO 8601."
                )
        
        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.fromisoformat(fecha_hasta.replace('Z', '+00:00'))
                query = query.filter(RegistroDatos.ts <= fecha_hasta_dt)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Formato de fecha inválido para fecha_hasta: {fecha_hasta}. Use formato ISO 8601."
                )
        
        # Validar que fecha_hasta sea posterior a fecha_desde
        if fecha_desde and fecha_hasta:
            if fecha_desde_dt >= fecha_hasta_dt:
                raise HTTPException(
                    status_code=400,
                    detail="fecha_hasta debe ser posterior a fecha_desde"
                )
        
        # Aplicar filtros adicionales
        if calidad:
            try:
                calidad_enum = CalidadDato(calidad.upper())
                query = query.filter(RegistroDatos.calidad == calidad_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Calidad inválida: {calidad}. Valores válidos: {[c.value for c in CalidadDato]}"
                )
        
        if procesado is not None:
            query = query.filter(RegistroDatos.procesado == procesado)
        
        if validado is not None:
            query = query.filter(RegistroDatos.validado == validado)
        
        # Obtener total de registros para paginación
        total_count = query.count()
        
        # Aplicar ordenamiento y paginación
        query = query.order_by(desc(RegistroDatos.ts))
        query = query.offset(offset).limit(limit)
        
        # Ejecutar consulta
        registros = query.all()
        
        # Formatear datos de respuesta
        datos_formateados = []
        for registro in registros:
            topic_registro = get_topic_from_registro(registro, session)
            datos_formateados.append(format_sensor_data(registro, topic_registro))
        
        # Calcular información de paginación
        total_paginas = (total_count + limit - 1) // limit if limit > 0 else 1
        pagina_actual = (offset // limit) + 1 if limit > 0 else 1
        
        # Construir metadatos
        metadatos = {
            "total_registros": total_count,
            "filtros_aplicados": {
                "topic": topic,
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
                "calidad": calidad,
                "procesado": procesado,
                "validado": validado
            },
            "timestamp_consulta": datetime.now(timezone.utc).isoformat()
        }
        
        # Construir información de paginación
        paginacion = {
            "pagina_actual": pagina_actual,
            "total_paginas": total_paginas,
            "registros_por_pagina": limit,
            "total_registros": total_count,
            "offset": offset
        }
        
        # Retornar respuesta
        return SensorDataResponse(
            success=True,
            data=datos_formateados,
            metadata=metadatos,
            pagination=paginacion
        )
        
    except HTTPException:
        # Re-lanzar excepciones HTTP
        raise
    except Exception as e:
        logger.error(f"Error obteniendo datos de sensores: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )


@app.get("/data/{canal_id}", response_model=SensorDataResponse)
async def get_sensor_data_by_canal(
    canal_id: str,
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (ISO 8601)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (ISO 8601)"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a retornar"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    session: Session = Depends(get_db_session)
):
    """
    Obtiene datos de sensores para un canal específico
    
    Args:
        canal_id: ID del canal
        fecha_desde: Fecha desde (ISO 8601)
        fecha_hasta: Fecha hasta (ISO 8601)
        limit: Número máximo de registros
        offset: Número de registros a omitir
    
    Returns:
        Datos del canal en formato JSON estándar
    """
    try:
        # Construir consulta para el canal específico
        query = session.query(RegistroDatos).filter(RegistroDatos.canal_id == canal_id)
        
        # Aplicar filtros de fecha
        if fecha_desde:
            try:
                fecha_desde_dt = datetime.fromisoformat(fecha_desde.replace('Z', '+00:00'))
                query = query.filter(RegistroDatos.ts >= fecha_desde_dt)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Formato de fecha inválido para fecha_desde: {fecha_desde}"
                )
        
        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.fromisoformat(fecha_hasta.replace('Z', '+00:00'))
                query = query.filter(RegistroDatos.ts <= fecha_hasta_dt)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Formato de fecha inválido para fecha_hasta: {fecha_hasta}"
                )
        
        # Obtener total de registros
        total_count = query.count()
        
        # Aplicar ordenamiento y paginación
        query = query.order_by(desc(RegistroDatos.ts))
        query = query.offset(offset).limit(limit)
        
        # Ejecutar consulta
        registros = query.all()
        
        # Formatear datos
        datos_formateados = []
        for registro in registros:
            topic_registro = get_topic_from_registro(registro, session)
            datos_formateados.append(format_sensor_data(registro, topic_registro))
        
        # Construir respuesta
        return SensorDataResponse(
            success=True,
            data=datos_formateados,
            metadata={
                "total_registros": total_count,
                "canal_id": canal_id,
                "filtros_aplicados": {
                    "fecha_desde": fecha_desde,
                    "fecha_hasta": fecha_hasta
                },
                "timestamp_consulta": datetime.now(timezone.utc).isoformat()
            },
            pagination={
                "pagina_actual": (offset // limit) + 1 if limit > 0 else 1,
                "total_paginas": (total_count + limit - 1) // limit if limit > 0 else 1,
                "registros_por_pagina": limit,
                "total_registros": total_count,
                "offset": offset
            }
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo datos del canal {canal_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo datos del canal: {str(e)}"
        )


@app.get("/topics", response_model=Dict[str, Any])
async def get_available_topics(
    session: Session = Depends(get_db_session)
):
    """
    Obtiene la lista de tópicos disponibles en el sistema
    
    Returns:
        Lista de tópicos disponibles
    """
    try:
        # Consultar canales únicos con información de dispositivo y proyecto
        query = session.query(
            Canal.id,
            Canal.nombre.label('canal_nombre'),
            Dispositivo.nombre.label('dispositivo_nombre'),
            UnidadProyecto.nombre.label('unidad_nombre'),
            Proyecto.nombre.label('proyecto_nombre')
        ).join(
            Dispositivo, Canal.dispositivo_id == Dispositivo.id
        ).join(
            UnidadProyecto, Dispositivo.unidad_proyecto_id == UnidadProyecto.id
        ).join(
            Proyecto, UnidadProyecto.proyecto_id == Proyecto.id
        ).filter(
            Canal.activo == True,
            Dispositivo.activo == True,
            UnidadProyecto.activo == True,
            Proyecto.activo == True
        )
        
        resultados = query.all()
        
        # Construir tópicos
        topics = []
        for resultado in resultados:
            topic = f"iot/{resultado.proyecto_nombre}/{resultado.unidad_nombre}/{resultado.dispositivo_nombre}/{resultado.canal_nombre}"
            topics.append({
                "topic": topic,
                "canal_id": str(resultado.id),
                "proyecto": resultado.proyecto_nombre,
                "unidad": resultado.unidad_nombre,
                "dispositivo": resultado.dispositivo_nombre,
                "canal": resultado.canal_nombre
            })
        
        return {
            "success": True,
            "topics": topics,
            "total_topics": len(topics),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo tópicos disponibles: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo tópicos: {str(e)}"
        )


@app.get("/stats", response_model=Dict[str, Any])
async def get_sensor_data_stats(
    topic: Optional[str] = Query(None, description="Filtro de tópico"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (ISO 8601)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (ISO 8601)"),
    session: Session = Depends(get_db_session)
):
    """
    Obtiene estadísticas de los datos de sensores
    
    Returns:
        Estadísticas de los datos
    """
    try:
        # Construir consulta base
        if topic:
            query = build_topic_query(session, topic)
        else:
            query = session.query(RegistroDatos)
        
        # Aplicar filtros de fecha
        if fecha_desde:
            fecha_desde_dt = datetime.fromisoformat(fecha_desde.replace('Z', '+00:00'))
            query = query.filter(RegistroDatos.ts >= fecha_desde_dt)
        
        if fecha_hasta:
            fecha_hasta_dt = datetime.fromisoformat(fecha_hasta.replace('Z', '+00:00'))
            query = query.filter(RegistroDatos.ts <= fecha_hasta_dt)
        
        # Obtener estadísticas
        total_registros = query.count()
        
        # Estadísticas por calidad
        stats_calidad = session.query(
            RegistroDatos.calidad,
            func.count(RegistroDatos.id).label('count')
        ).filter(
            query.whereclause if query.whereclause else True
        ).group_by(RegistroDatos.calidad).all()
        
        # Estadísticas por tipo de valor
        stats_tipo = session.query(
            func.count(RegistroDatos.valor_num).label('numeric'),
            func.count(RegistroDatos.valor_int).label('integer'),
            func.count(RegistroDatos.valor_bool).label('boolean'),
            func.count(RegistroDatos.valor_text).label('text'),
            func.count(RegistroDatos.valor_json).label('json')
        ).filter(
            query.whereclause if query.whereclause else True
        ).first()
        
        # Estadísticas de procesamiento
        stats_procesamiento = session.query(
            func.count(RegistroDatos.id).label('total'),
            func.count(RegistroDatos.id).filter(RegistroDatos.procesado == True).label('procesados'),
            func.count(RegistroDatos.id).filter(RegistroDatos.validado == True).label('validados')
        ).filter(
            query.whereclause if query.whereclause else True
        ).first()
        
        return {
            "success": True,
            "stats": {
                "total_registros": total_registros,
                "por_calidad": {str(stat.calidad): stat.count for stat in stats_calidad},
                "por_tipo": {
                    "numeric": stats_tipo.numeric,
                    "integer": stats_tipo.integer,
                    "boolean": stats_tipo.boolean,
                    "text": stats_tipo.text,
                    "json": stats_tipo.json
                },
                "procesamiento": {
                    "total": stats_procesamiento.total,
                    "procesados": stats_procesamiento.procesados,
                    "validados": stats_procesamiento.validados,
                    "porcentaje_procesados": (stats_procesamiento.procesados / stats_procesamiento.total * 100) if stats_procesamiento.total > 0 else 0,
                    "porcentaje_validados": (stats_procesamiento.validados / stats_procesamiento.total * 100) if stats_procesamiento.total > 0 else 0
                }
            },
            "filtros_aplicados": {
                "topic": topic,
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )


# ============================================================================
# MANEJADORES DE ERRORES
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejador de excepciones HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            timestamp=datetime.now(timezone.utc).isoformat()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejador de excepciones generales"""
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error="Error interno del servidor",
            error_code="INTERNAL_ERROR",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details={"exception_type": type(exc).__name__}
        ).dict()
    )


# ============================================================================
# FUNCIONES DE INICIALIZACIÓN
# ============================================================================

def initialize_api(config_path: str = None):
    """Inicializa la API con configuración"""
    global db_handler, auditoria_service
    
    try:
        # Cargar configuración
        if config_path:
            config = load_config(config_path)
        else:
            config = load_config()
        
        # Crear manejador de base de datos
        db_handler = create_database_handler(config.storage)
        logger.info("✅ Base de datos inicializada")
        
        # Crear servicio de auditoría
        auditoria_service = create_auditoria_service(db_handler)
        logger.info("✅ Servicio de auditoría inicializado")
        
        logger.info("🚀 API inicializada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando API: {e}")
        raise


# ============================================================================
# EVENTOS DE LA APLICACIÓN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Evento ejecutado al iniciar la aplicación"""
    logger.info("🚀 Iniciando IoT Middleware API...")
    
    # Intentar inicialización automática
    try:
        initialize_api()
    except Exception as e:
        logger.warning(f"⚠️  Inicialización automática falló: {e}")
        logger.info("💡 Use initialize_api() manualmente o configure la aplicación")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento ejecutado al detener la aplicación"""
    logger.info("🛑 Deteniendo IoT Middleware API...")
    
    # Cerrar conexiones de base de datos
    if db_handler:
        try:
            db_handler.close()
            logger.info("✅ Conexiones de base de datos cerradas")
        except Exception as e:
            logger.error(f"❌ Error cerrando conexiones: {e}")


# ============================================================================
# EJECUCIÓN DIRECTA
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 IoT Middleware API")
    print("=" * 50)
    
    try:
        # Inicializar API
        initialize_api()
        
        # Ejecutar servidor
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Asegúrate de que la configuración sea correcta")
        exit(1)
