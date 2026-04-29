"""
Router de Autenticación
=======================

Este módulo define los endpoints de autenticación para la API,
incluyendo login, logout y refresh de tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
import logging
from datetime import datetime

from ..models.auth_models import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    LogoutResponse,
    ChangePasswordRequest,
    ChangePasswordResponse
)
from ..models.common_models import ErrorResponse
from ..auth import JWTHandler, AuthMiddleware
from ...storage.db_handler import create_database_handler
from ...models.entities import Usuario

# Configurar logging
logger = logging.getLogger(__name__)


def _get_db_handler(request: Request):
    """Construye el manejador de base de datos desde la configuración cargada."""
    return create_database_handler(config=request.app.state.config)

# Crear router
auth_router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
    responses={
        401: {"model": ErrorResponse, "description": "No autorizado"},
        422: {"model": ErrorResponse, "description": "Error de validación"}
    }
)

# Esquema de autenticación HTTP Bearer
security = HTTPBearer()


@auth_router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request
):
    """
    Autenticar usuario y obtener tokens de acceso
    
    - **email**: Email del usuario
    - **password**: Contraseña del usuario
    """
    try:
        # Obtener configuración
        db_handler = _get_db_handler(request)
        
        # Inicializar manejadores
        jwt_handler = JWTHandler()
        auth_middleware = AuthMiddleware(jwt_handler, db_handler)
        
        # Buscar usuario por email
        with db_handler.get_session() as session:
            usuario = session.query(Usuario).filter(
                Usuario.email == login_data.email
            ).first()
            
            if not usuario:
                logger.warning(f"Intento de login con email inexistente: {login_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales inválidas"
                )
            
            if not usuario.activo:
                logger.warning(f"Intento de login con usuario inactivo: {login_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario inactivo"
                )
            
            # Verificar contraseña
            if not JWTHandler.verify_password(login_data.password, usuario.password_hash):
                logger.warning(f"Intento de login con contraseña incorrecta: {login_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales inválidas"
                )
            
            # Actualizar último acceso
            usuario.ultimo_login = datetime.utcnow()
            session.commit()
            
            # Crear respuesta de autenticación
            response_data = auth_middleware.create_auth_response(usuario)
            
            logger.info(f"Login exitoso para usuario: {usuario.email}")
            return response_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@auth_router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request
):
    """
    Refrescar token de acceso usando token de refresco
    
    - **refresh_token**: Token de refresco válido
    """
    try:
        # Obtener configuración
        db_handler = _get_db_handler(request)
        
        # Inicializar manejadores
        jwt_handler = JWTHandler()
        auth_middleware = AuthMiddleware(jwt_handler, db_handler)
        
        # Validar token de refresco
        new_token_data = auth_middleware.validate_refresh_token(refresh_data.refresh_token)
        
        if not new_token_data:
            logger.warning("Intento de refresh con token inválido")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de refresco inválido o expirado"
            )
        
        logger.info("Token refrescado exitosamente")
        return {
            "success": True,
            "message": "Token refrescado exitosamente",
            "data": new_token_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al refrescar token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@auth_router.post("/logout", response_model=LogoutResponse)
async def logout(
    logout_data: LogoutRequest,
    request: Request
):
    """
    Cerrar sesión e invalidar token de refresco
    
    - **refresh_token**: Token de refresco a invalidar
    """
    try:
        # Obtener configuración
        db_handler = _get_db_handler(request)
        
        # Inicializar manejadores
        jwt_handler = JWTHandler()
        auth_middleware = AuthMiddleware(jwt_handler, db_handler)
        
        # Verificar token de refresco
        token_payload = auth_middleware.get_user_from_token(logout_data.refresh_token)
        
        if not token_payload:
            logger.warning("Intento de logout con token inválido")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de refresco inválido"
            )
        
        # Aquí se podría implementar una lista negra de tokens
        # Por ahora, solo logueamos el logout
        
        user_id = token_payload.get("sub")
        logger.info(f"Logout exitoso para usuario: {user_id}")
        
        return {
            "success": True,
            "message": "Logout exitoso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@auth_router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    request: Request,
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Cambiar contraseña del usuario autenticado
    
    - **current_password**: Contraseña actual
    - **new_password**: Nueva contraseña
    - **confirm_password**: Confirmación de nueva contraseña
    """
    try:
        # Validar contraseñas
        password_data.validate_passwords()
        
        # Obtener configuración
        db_handler = _get_db_handler(request)
        
        # Verificar contraseña actual
        if not JWTHandler.verify_password(password_data.current_password, current_user.password_hash):
            logger.warning(f"Intento de cambio de contraseña con contraseña incorrecta: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta"
            )
        
        # Generar nuevo hash de contraseña
        new_password_hash = JWTHandler.get_password_hash(password_data.new_password)
        
        # Actualizar contraseña en la base de datos
        with db_handler.get_session() as session:
            usuario = session.get(Usuario, current_user.id)
            usuario.password_hash = new_password_hash
            session.commit()
            
            logger.info(f"Contraseña cambiada exitosamente para usuario: {usuario.email}")
            
            return {
                "success": True,
                "message": "Contraseña cambiada exitosamente"
            }
            
    except ValueError as e:
        logger.warning(f"Error de validación en cambio de contraseña: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al cambiar contraseña: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@auth_router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: Usuario = Depends(lambda req: get_current_user(req))
):
    """
    Obtener información del usuario autenticado
    """
    try:
        return {
            "success": True,
            "message": "Información del usuario obtenida exitosamente",
            "data": {
                "id": str(current_user.id),
                "email": current_user.email,
                "nombre": current_user.nombre,
                "rol": current_user.rol,
                "cliente_id": str(current_user.cliente_id) if current_user.cliente_id else None,
                "proyecto_id": str(current_user.proyecto_id) if current_user.proyecto_id else None,
                "unidad_id": str(current_user.unidad_id) if current_user.unidad_id else None,
                "activo": current_user.activo,
                "ultimo_acceso": current_user.ultimo_acceso.isoformat() if current_user.ultimo_acceso else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error al obtener información del usuario: {e}")
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
