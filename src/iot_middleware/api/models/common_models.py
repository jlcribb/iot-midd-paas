"""
Modelos Pydantic Comunes para la API
====================================

Este módulo define los modelos Pydantic comunes utilizados
en toda la API del IoT Middleware.
"""

from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Tipo genérico para los datos de respuesta
T = TypeVar('T')


class PaginationParams(BaseModel):
    """Parámetros de paginación para consultas"""
    
    page: int = Field(default=1, ge=1, description="Número de página")
    size: int = Field(default=20, ge=1, le=100, description="Tamaño de página")
    
    @property
    def offset(self) -> int:
        """Calcular offset para la consulta"""
        return (self.page - 1) * self.size


class PaginationInfo(BaseModel):
    """Información de paginación para respuestas"""
    
    page: int = Field(..., description="Página actual")
    size: int = Field(..., description="Tamaño de página")
    total: int = Field(..., description="Total de elementos")
    pages: int = Field(..., description="Total de páginas")
    has_next: bool = Field(..., description="Indica si hay página siguiente")
    has_prev: bool = Field(..., description="Indica si hay página anterior")
    
    @classmethod
    def from_total(cls, page: int, size: int, total: int) -> 'PaginationInfo':
        """Crear información de paginación desde total"""
        pages = (total + size - 1) // size  # Ceiling division
        return cls(
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica"""
    
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo de la respuesta")
    data: List[T] = Field(..., description="Lista de elementos")
    pagination: PaginationInfo = Field(..., description="Información de paginación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Datos obtenidos exitosamente",
                "data": [],
                "pagination": {
                    "page": 1,
                    "size": 20,
                    "total": 100,
                    "pages": 5,
                    "has_next": True,
                    "has_prev": False
                }
            }
        }


class SuccessResponse(BaseModel, Generic[T]):
    """Respuesta de éxito genérica"""
    
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo de la respuesta")
    data: Optional[T] = Field(None, description="Datos de la respuesta")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operación realizada exitosamente",
                "data": None
            }
        }


class ErrorResponse(BaseModel):
    """Respuesta de error estándar"""
    
    success: bool = Field(default=False, description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo del error")
    error_code: Optional[str] = Field(None, description="Código de error específico")
    details: Optional[dict] = Field(None, description="Detalles adicionales del error")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp del error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Error al procesar la solicitud",
                "error_code": "VALIDATION_ERROR",
                "details": {
                    "field": "email",
                    "issue": "Formato inválido"
                },
                "timestamp": "2025-08-16T00:00:00Z"
            }
        }


class ValidationError(BaseModel):
    """Error de validación específico"""
    
    field: str = Field(..., description="Campo que falló la validación")
    message: str = Field(..., description="Mensaje de error para el campo")
    value: Optional[Any] = Field(None, description="Valor que causó el error")


class ValidationErrorResponse(ErrorResponse):
    """Respuesta de error de validación"""
    
    errors: List[ValidationError] = Field(..., description="Lista de errores de validación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Error de validación",
                "error_code": "VALIDATION_ERROR",
                "errors": [
                    {
                        "field": "email",
                        "message": "Formato de email inválido",
                        "value": "email_invalido"
                    }
                ],
                "timestamp": "2025-08-16T00:00:00Z"
            }
        }


class HealthCheckResponse(BaseModel):
    """Respuesta de verificación de salud del sistema"""
    
    status: str = Field(..., description="Estado del sistema")
    timestamp: datetime = Field(..., description="Timestamp de la verificación")
    version: str = Field(..., description="Versión de la API")
    services: dict = Field(..., description="Estado de los servicios")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-08-16T00:00:00Z",
                "version": "1.0.0",
                "services": {
                    "database": "healthy",
                    "mqtt": "healthy",
                    "storage": "healthy"
                }
            }
        }


class BulkOperationRequest(BaseModel):
    """Solicitud para operaciones en lote"""
    
    operation: str = Field(..., description="Tipo de operación a realizar")
    items: List[dict] = Field(..., description="Lista de elementos para procesar")
    options: Optional[dict] = Field(None, description="Opciones adicionales para la operación")


class BulkOperationResponse(BaseModel):
    """Respuesta de operación en lote"""
    
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo de la respuesta")
    total_items: int = Field(..., description="Total de elementos procesados")
    successful_items: int = Field(..., description="Elementos procesados exitosamente")
    failed_items: int = Field(..., description="Elementos que fallaron")
    errors: Optional[List[dict]] = Field(None, description="Detalles de los errores")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operación en lote completada",
                "total_items": 100,
                "successful_items": 95,
                "failed_items": 5,
                "errors": [
                    {
                        "item_id": "uuid-1",
                        "error": "Elemento no encontrado"
                    }
                ]
            }
        }


class SearchRequest(BaseModel):
    """Solicitud de búsqueda genérica"""
    
    query: str = Field(..., description="Término de búsqueda")
    filters: Optional[dict] = Field(None, description="Filtros adicionales")
    sort_by: Optional[str] = Field(None, description="Campo para ordenar")
    sort_order: str = Field(default="asc", description="Orden de clasificación (asc/desc)")
    pagination: Optional[PaginationParams] = Field(None, description="Parámetros de paginación")


class SearchResponse(BaseModel, Generic[T]):
    """Respuesta de búsqueda genérica"""
    
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo de la respuesta")
    query: str = Field(..., description="Término de búsqueda utilizado")
    results: List[T] = Field(..., description="Resultados de la búsqueda")
    total_results: int = Field(..., description="Total de resultados encontrados")
    pagination: Optional[PaginationInfo] = Field(None, description="Información de paginación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Búsqueda completada exitosamente",
                "query": "temperatura",
                "results": [],
                "total_results": 50,
                "pagination": None
            }
        }
