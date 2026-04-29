"""
Modelos Pydantic para Autenticación
==================================

Este módulo define los modelos Pydantic para las operaciones
de autenticación de la API.
"""

from typing import Optional, Union
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from datetime import datetime

from ...models.enums import RolUsuario, rol_to_pydantic


class LoginRequest(BaseModel):
    """Modelo para solicitud de login"""
    
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=6, description="Contraseña del usuario")


class UserInfo(BaseModel):
    """Información del usuario para respuestas de API"""
    
    id: str = Field(..., description="ID único del usuario")
    email: EmailStr = Field(..., description="Email del usuario")
    nombre: str = Field(..., description="Nombre completo del usuario")
    rol: Union[RolUsuario, str] = Field(..., description="Rol del usuario en el sistema")
    cliente_id: Optional[str] = Field(None, description="ID del cliente asociado")
    proyecto_id: Optional[str] = Field(None, description="ID del proyecto asociado")
    unidad_id: Optional[str] = Field(None, description="ID de la unidad asociada")
    activo: bool = Field(..., description="Estado activo del usuario")
    ultimo_acceso: Optional[datetime] = Field(None, description="Último acceso del usuario")
    
    @field_validator('rol', mode='before')
    @classmethod
    def convert_rol(cls, v):
        """Convierte rol de SQLAlchemy a enum de Python para Pydantic"""
        return rol_to_pydantic(v)
    
    model_config = ConfigDict(from_attributes=True)


class TokenInfo(BaseModel):
    """Información de tokens de autenticación"""
    
    access_token: str = Field(..., description="Token de acceso JWT")
    refresh_token: str = Field(..., description="Token de refresco JWT")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")


class LoginResponse(BaseModel):
    """Respuesta de login exitoso"""
    
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo de la respuesta")
    data: dict = Field(..., description="Datos de la respuesta")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "success": True,
                "message": "Autenticación exitosa",
                "data": {
                    "user": {
                        "id": "uuid-usuario",
                        "email": "usuario@example.com",
                        "nombre": "Usuario Ejemplo",
                        "rol": "cliente",
                        "cliente_id": "uuid-cliente",
                        "proyecto_id": "uuid-proyecto",
                        "unidad_id": "uuid-unidad",
                        "activo": True,
                        "ultimo_acceso": "2025-08-16T00:00:00Z"
                    },
                    "tokens": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "token_type": "bearer",
                        "expires_in": 1800
                    }
                }
            }
        })


class RefreshTokenRequest(BaseModel):
    """Solicitud para refrescar token de acceso"""
    
    refresh_token: str = Field(..., description="Token de refresco válido")


class RefreshTokenResponse(BaseModel):
    """Respuesta de refresco de token exitoso"""
    
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo de la respuesta")
    data: TokenInfo = Field(..., description="Nuevo token de acceso")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "success": True,
                "message": "Token refrescado exitosamente",
                "data": {
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "token_type": "bearer",
                    "expires_in": 1800
                }
            }
        })


class LogoutRequest(BaseModel):
    """Solicitud de logout"""
    
    refresh_token: str = Field(..., description="Token de refresco a invalidar")


class LogoutResponse(BaseModel):
    """Respuesta de logout exitoso"""
    
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo de la respuesta")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "success": True,
                "message": "Logout exitoso"
            }
        })


class ChangePasswordRequest(BaseModel):
    """Solicitud para cambiar contraseña"""
    
    current_password: str = Field(..., min_length=6, description="Contraseña actual")
    new_password: str = Field(..., min_length=6, description="Nueva contraseña")
    confirm_password: str = Field(..., min_length=6, description="Confirmación de nueva contraseña")
    
    def validate_passwords(self):
        """Validar que las contraseñas coincidan"""
        if self.new_password != self.confirm_password:
            raise ValueError("Las contraseñas no coinciden")
        if self.current_password == self.new_password:
            raise ValueError("La nueva contraseña debe ser diferente a la actual")


class ChangePasswordResponse(BaseModel):
    """Respuesta de cambio de contraseña exitoso"""
    
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo de la respuesta")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "success": True,
                "message": "Contraseña cambiada exitosamente"
            }
        })
