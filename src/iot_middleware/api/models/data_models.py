"""
Modelos Pydantic para Datos y Series Temporales
===============================================

Este módulo define los modelos Pydantic para las operaciones
de datos, series temporales y eventos de la API.
"""

from typing import Optional, List, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime

from ...models.enums import CalidadDatoPy, calidad_to_pydantic


class TimeSeriesRequest(BaseModel):
    """Solicitud para obtener series temporales"""
    
    canal_id: str = Field(..., description="ID del canal")
    desde: datetime = Field(..., description="Fecha y hora de inicio")
    hasta: datetime = Field(..., description="Fecha y hora de fin")
    freq: Optional[str] = Field(default="1m", description="Frecuencia de muestreo (1m, 5m, 1h, 1d)")
    limit: Optional[int] = Field(default=1000, ge=1, le=10000, description="Límite de registros")
    
    @field_validator('hasta')
    @classmethod
    def validate_date_range(cls, v, info):
        """Validar que la fecha de fin sea posterior a la de inicio"""
        if info.data and 'desde' in info.data and v <= info.data['desde']:
            raise ValueError('La fecha de fin debe ser posterior a la de inicio')
        return v
    
    @field_validator('freq')
    @classmethod
    def validate_frequency(cls, v):
        """Validar formato de frecuencia"""
        valid_freqs = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
        if v not in valid_freqs:
            raise ValueError(f'Frecuencia debe ser una de: {valid_freqs}')
        return v


class TimeSeriesPoint(BaseModel):
    """Punto de una serie temporal"""
    
    timestamp: datetime = Field(..., description="Timestamp del punto")
    valor: Union[float, int, bool, str, dict] = Field(..., description="Valor del punto")
    calidad: Union[CalidadDatoPy, str] = Field(..., description="Calidad del dato")
    calidad_porcentaje: Optional[int] = Field(None, description="Porcentaje de calidad")
    metadata: Optional[dict] = Field(None, description="Metadatos adicionales")
    
    @field_validator('calidad', mode='before')
    @classmethod
    def convert_calidad(cls, v):
        """Convierte calidad de SQLAlchemy a enum de Python para Pydantic"""
        return calidad_to_pydantic(v)


class TimeSeriesResponse(BaseModel):
    """Respuesta de serie temporal"""
    
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo de la respuesta")
    data: dict = Field(..., description="Datos de la serie temporal")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "success": True,
                "message": "Serie temporal obtenida exitosamente",
                "data": {
                    "canal_id": "uuid-canal",
                    "canal_nombre": "Temperatura_Sensor_1",
                    "tipo_dato": "float",
                    "unidad_medida": "°C",
                    "desde": "2025-08-16T00:00:00Z",
                    "hasta": "2025-08-16T23:59:59Z",
                    "freq": "1m",
                    "total_puntos": 1440,
                    "series": [
                        {
                            "timestamp": "2025-08-16T00:00:00Z",
                            "valor": 25.5,
                            "calidad": "OK",
                            "calidad_porcentaje": 100,
                            "metadata": {"source": "sensor_1"}
                        }
                    ]
                }
            }
        })


class EventFilterRequest(BaseModel):
    """Solicitud para filtrar eventos"""
    
    proyecto_id: Optional[str] = Field(None, description="ID del proyecto")
    desde: Optional[datetime] = Field(None, description="Fecha y hora de inicio")
    hasta: Optional[datetime] = Field(None, description="Fecha y hora de fin")
    severidad: Optional[str] = Field(None, description="Nivel de severidad del evento")
    tipo: Optional[str] = Field(None, description="Tipo de evento")
    dispositivo_id: Optional[str] = Field(None, description="ID del dispositivo")
    canal_id: Optional[str] = Field(None, description="ID del canal")
    activo: Optional[bool] = Field(None, description="Solo eventos activos")
    limit: Optional[int] = Field(default=100, ge=1, le=1000, description="Límite de eventos")
    offset: Optional[int] = Field(default=0, ge=0, description="Desplazamiento para paginación")
    
    @field_validator('hasta')
    @classmethod
    def validate_date_range(cls, v, info):
        """Validar que la fecha de fin sea posterior a la de inicio si ambas están presentes"""
        if v and info.data and 'desde' in info.data and info.data['desde'] and v <= info.data['desde']:
            raise ValueError('La fecha de fin debe ser posterior a la de inicio')
        return v


class EventResponse(BaseModel):
    """Respuesta de evento individual"""
    
    id: str = Field(..., description="ID único del evento")
    tipo: str = Field(..., description="Tipo de evento")
    severidad: str = Field(..., description="Nivel de severidad")
    mensaje: str = Field(..., description="Mensaje descriptivo del evento")
    timestamp: datetime = Field(..., description="Timestamp del evento")
    activo: bool = Field(..., description="Estado activo del evento")
    metadata: Optional[dict] = Field(None, description="Metadatos adicionales")
    
    # Campos opcionales según el tipo de evento
    dispositivo_id: Optional[str] = Field(None, description="ID del dispositivo relacionado")
    canal_id: Optional[str] = Field(None, description="ID del canal relacionado")
    proyecto_id: Optional[str] = Field(None, description="ID del proyecto")
    valor_anterior: Optional[Union[float, int, bool, str]] = Field(None, description="Valor anterior")
    valor_actual: Optional[Union[float, int, bool, str]] = Field(None, description="Valor actual")
    umbral: Optional[Union[float, int]] = Field(None, description="Umbral que se superó")
    
    model_config = ConfigDict(from_attributes=True)


class EventsListResponse(BaseModel):
    """Respuesta de lista de eventos"""
    
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo de la respuesta")
    data: List[EventResponse] = Field(..., description="Lista de eventos")
    total: int = Field(..., description="Total de eventos encontrados")
    filtros_aplicados: dict = Field(..., description="Filtros aplicados a la consulta")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "success": True,
                "message": "Eventos obtenidos exitosamente",
                "data": [],
                "total": 50,
                "filtros_aplicados": {
                    "proyecto_id": "uuid-proyecto",
                    "desde": "2025-08-16T00:00:00Z",
                    "hasta": "2025-08-16T23:59:59Z",
                    "severidad": "alta"
                }
            }
        })


class DataPoint(BaseModel):
    """Punto de datos individual"""
    
    id: str = Field(..., description="ID único del registro")
    canal_id: str = Field(..., description="ID del canal")
    timestamp: datetime = Field(..., description="Timestamp del dato")
    valor: Union[float, int, bool, str, dict] = Field(..., description="Valor del dato")
    tipo_valor: str = Field(..., description="Tipo del valor (num, int, bool, text, json)")
    calidad: Union[CalidadDatoPy, str] = Field(..., description="Calidad del dato")
    calidad_porcentaje: Optional[int] = Field(None, description="Porcentaje de calidad")
    metadata: Optional[dict] = Field(None, description="Metadatos adicionales")
    procesado: bool = Field(..., description="Indica si el dato fue procesado")
    validado: bool = Field(..., description="Indica si el dato fue validado")
    
    @field_validator('calidad', mode='before')
    @classmethod
    def convert_calidad(cls, v):
        """Convierte calidad de SQLAlchemy a enum de Python para Pydantic"""
        return calidad_to_pydantic(v)
    
    model_config = ConfigDict(from_attributes=True)


class DataInsertRequest(BaseModel):
    """Solicitud para insertar datos"""
    
    canal_id: str = Field(..., description="ID del canal")
    valor: Union[float, int, bool, str, dict] = Field(..., description="Valor a insertar")
    timestamp: Optional[datetime] = Field(None, description="Timestamp del dato (por defecto ahora)")
    calidad: Optional[Union[CalidadDatoPy, str]] = Field(CalidadDatoPy.OK, description="Calidad del dato")
    calidad_porcentaje: Optional[int] = Field(100, ge=0, le=100, description="Porcentaje de calidad")
    metadata: Optional[dict] = Field(None, description="Metadatos adicionales")
    
    @field_validator('calidad', mode='before')
    @classmethod
    def convert_calidad(cls, v):
        """Convierte calidad de SQLAlchemy a enum de Python para Pydantic"""
        if v is None:
            return CalidadDatoPy.OK
        return calidad_to_pydantic(v)
    
    # Metadatos opcionales que se pueden incluir
    qos: Optional[int] = Field(None, ge=0, le=2, description="Calidad de servicio MQTT")
    ip: Optional[str] = Field(None, description="IP del dispositivo")
    source: Optional[str] = Field(None, description="Fuente del dato")


class DataInsertResponse(BaseModel):
    """Respuesta de inserción de datos"""
    
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo de la respuesta")
    data: dict = Field(..., description="Datos del registro insertado")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "success": True,
                "message": "Dato insertado exitosamente",
                "data": {
                    "id": "uuid-registro",
                    "canal_id": "uuid-canal",
                    "timestamp": "2025-08-16T00:00:00Z",
                    "valor": 25.5,
                    "tipo_valor": "num",
                    "calidad": "OK",
                    "calidad_porcentaje": 100,
                    "metadata": {"source": "sensor_1", "qos": 1}
                }
            }
        })


class AggregationRequest(BaseModel):
    """Solicitud para agregación de datos"""
    
    canal_id: str = Field(..., description="ID del canal")
    desde: datetime = Field(..., description="Fecha y hora de inicio")
    hasta: datetime = Field(..., description="Fecha y hora de fin")
    funcion: str = Field(..., description="Función de agregación (avg, min, max, sum, count)")
    intervalo: str = Field(..., description="Intervalo de agregación (1m, 5m, 1h, 1d)")
    
    @field_validator('funcion')
    @classmethod
    def validate_aggregation_function(cls, v):
        """Validar función de agregación"""
        valid_funcs = ['avg', 'min', 'max', 'sum', 'count', 'std', 'var']
        if v not in valid_funcs:
            raise ValueError(f'Función debe ser una de: {valid_funcs}')
        return v
    
    @field_validator('intervalo')
    @classmethod
    def validate_interval(cls, v):
        """Validar intervalo de agregación"""
        valid_intervals = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
        if v not in valid_intervals:
            raise ValueError(f'Intervalo debe ser uno de: {valid_intervals}')
        return v


class AggregatedPoint(BaseModel):
    """Punto de datos agregado"""
    
    timestamp: datetime = Field(..., description="Timestamp del intervalo")
    valor: Union[float, int] = Field(..., description="Valor agregado")
    count: int = Field(..., description="Número de puntos en el intervalo")
    min_valor: Optional[Union[float, int]] = Field(None, description="Valor mínimo del intervalo")
    max_valor: Optional[Union[float, int]] = Field(None, description="Valor máximo del intervalo")
    std_dev: Optional[float] = Field(None, description="Desviación estándar del intervalo")


class AggregationResponse(BaseModel):
    """Respuesta de agregación de datos"""
    
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo de la respuesta")
    data: dict = Field(..., description="Datos de la agregación")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "success": True,
                "message": "Agregación completada exitosamente",
                "data": {
                    "canal_id": "uuid-canal",
                    "funcion": "avg",
                    "intervalo": "1h",
                    "desde": "2025-08-16T00:00:00Z",
                    "hasta": "2025-08-16T23:59:59Z",
                    "total_intervalos": 24,
                    "puntos": [
                        {
                            "timestamp": "2025-08-16T00:00:00Z",
                            "valor": 25.5,
                            "count": 60,
                            "min_valor": 24.0,
                            "max_valor": 27.0,
                            "std_dev": 0.8
                        }
                    ]
                }
            }
        })
