"""
Modelos Pydantic para la API
============================

Este paquete contiene los modelos Pydantic para las respuestas
y requests de la API del IoT Middleware.
"""

from .auth_models import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    UserInfo
)
from .common_models import (
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
    PaginationParams
)
from .data_models import (
    TimeSeriesRequest,
    TimeSeriesResponse,
    EventFilterRequest,
    EventResponse
)

__all__ = [
    'LoginRequest',
    'LoginResponse', 
    'RefreshTokenRequest',
    'RefreshTokenResponse',
    'UserInfo',
    'PaginatedResponse',
    'ErrorResponse',
    'SuccessResponse',
    'PaginationParams',
    'TimeSeriesRequest',
    'TimeSeriesResponse',
    'EventFilterRequest',
    'EventResponse',
]
