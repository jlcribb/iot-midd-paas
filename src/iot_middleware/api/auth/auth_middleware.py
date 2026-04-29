"""
Middleware de Autenticación para FastAPI
=======================================

Este módulo proporciona middleware de autenticación JWT
para proteger endpoints de la API.
"""

from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from .jwt_handler import JWTHandler
from ...models.entities import Usuario
from ...storage.db_handler import DatabaseHandler

# Configurar logging
logger = logging.getLogger(__name__)

# Esquema de autenticación HTTP Bearer
security = HTTPBearer()


def _role_value(role):
    """Normaliza roles a string para comparar payload JWT y modelo."""
    return role.value if hasattr(role, "value") else role


class AuthMiddleware:
    """
    Middleware de autenticación JWT para FastAPI
    """
    
    def __init__(self, jwt_handler: JWTHandler, db_handler: DatabaseHandler):
        """
        Inicializar middleware de autenticación
        
        Args:
            jwt_handler: Manejador JWT
            db_handler: Manejador de base de datos
        """
        self.jwt_handler = jwt_handler
        self.db = db_handler
    
    async def authenticate_user(self, credentials: HTTPAuthorizationCredentials) -> Optional[Usuario]:
        """
        Autenticar usuario usando token JWT
        
        Args:
            credentials: Credenciales HTTP Bearer
            
        Returns:
            Usuario autenticado o None si falla
        """
        try:
            token = credentials.credentials
            
            # Verificar token
            payload = self.jwt_handler.verify_token(token)
            if not payload:
                logger.warning("Token JWT inválido o expirado")
                return None
            
            # Obtener usuario de la base de datos
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("Token no contiene ID de usuario")
                return None
            
            # Verificar que el usuario existe y está activo
            with self.db.get_session() as session:
                usuario = session.get(Usuario, user_id)
                if not usuario or not usuario.activo:
                    logger.warning(f"Usuario {user_id} no encontrado o inactivo")
                    return None
                
                # Verificar que el rol en el token coincida con el de la BD
                if _role_value(usuario.rol) != payload.get("rol"):
                    logger.warning(f"Rol del token no coincide con el de la BD para usuario {user_id}")
                    return None
                
                logger.debug(f"Usuario autenticado: {usuario.email} (ID: {usuario.id})")
                return usuario
                
        except Exception as e:
            logger.error(f"Error en autenticación: {e}")
            return None
    
    async def get_current_user(self, request: Request) -> Usuario:
        """
        Obtener usuario actual desde el request
        
        Args:
            request: Request de FastAPI
            
        Returns:
            Usuario autenticado
            
        Raises:
            HTTPException: Si la autenticación falla
        """
        try:
            # Obtener credenciales del header Authorization
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales de autenticación requeridas",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Extraer token
            token = auth_header.split(" ")[1]
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
            
            # Autenticar usuario
            usuario = await self.authenticate_user(credentials)
            if not usuario:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido o expirado",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return usuario
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error al obtener usuario actual: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del servidor"
            )
    
    async def get_current_active_user(self, request: Request) -> Usuario:
        """
        Obtener usuario activo actual
        
        Args:
            request: Request de FastAPI
            
        Returns:
            Usuario activo
            
        Raises:
            HTTPException: Si el usuario no está activo
        """
        usuario = await self.get_current_user(request)
        
        if not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario inactivo"
            )
        
        return usuario
    
    def get_user_from_token(self, token: str) -> Optional[dict]:
        """
        Obtener información del usuario desde un token (sin verificar BD)
        
        Args:
            token: Token JWT
            
        Returns:
            Payload del token o None si es inválido
        """
        try:
            return self.jwt_handler.verify_token(token)
        except Exception as e:
            logger.error(f"Error al obtener usuario desde token: {e}")
            return None
    
    def create_auth_response(self, usuario: Usuario) -> dict:
        """
        Crear respuesta de autenticación con tokens
        
        Args:
            usuario: Usuario autenticado
            
        Returns:
            Respuesta con tokens y información del usuario
        """
        try:
            tokens = self.jwt_handler.create_user_tokens(usuario)
            
            return {
                "success": True,
                "message": "Autenticación exitosa",
                "data": {
                    "user": {
                        "id": str(usuario.id),
                        "email": usuario.email,
                        "nombre": usuario.nombre,
                        "rol": _role_value(usuario.rol),
                        "cliente_id": str(usuario.cliente_id) if usuario.cliente_id else None,
                        "proyecto_id": str(usuario.proyecto_id) if usuario.proyecto_id else None,
                        "unidad_id": str(usuario.unidad_id) if usuario.unidad_id else None,
                        "activo": usuario.activo
                    },
                    "tokens": tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Error al crear respuesta de autenticación: {e}")
            raise
    
    def validate_refresh_token(self, refresh_token: str) -> Optional[dict]:
        """
        Validar token de refresco
        
        Args:
            refresh_token: Token de refresco
            
        Returns:
            Nuevo token de acceso o None si falla
        """
        try:
            new_access_token = self.jwt_handler.refresh_access_token(refresh_token)
            if new_access_token:
                return {
                    "access_token": new_access_token,
                    "token_type": "bearer",
                    "expires_in": 30 * 60  # 30 minutos
                }
            return None
            
        except Exception as e:
            logger.error(f"Error al validar token de refresco: {e}")
            return None
