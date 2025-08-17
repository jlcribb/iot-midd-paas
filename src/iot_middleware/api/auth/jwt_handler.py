"""
Manejador JWT para Autenticación
================================

Este módulo maneja la creación, validación y decodificación de tokens JWT
para el sistema de autenticación del IoT Middleware.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
import logging

from ...models.entities import Usuario
from ...models.enums import RolUsuario

# Configurar logging
logger = logging.getLogger(__name__)

# Configuración de seguridad
SECRET_KEY = "iot_middleware_secret_key_2024_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Contexto para hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTHandler:
    """
    Manejador para operaciones JWT (JSON Web Tokens)
    """
    
    def __init__(self, secret_key: Optional[str] = None, algorithm: str = ALGORITHM):
        """
        Inicializar el manejador JWT
        
        Args:
            secret_key: Clave secreta para firmar tokens
            algorithm: Algoritmo de firma
        """
        self.secret_key = secret_key or SECRET_KEY
        self.algorithm = algorithm
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Crear token de acceso JWT
        
        Args:
            data: Datos a incluir en el token
            expires_delta: Tiempo de expiración personalizado
            
        Returns:
            Token JWT firmado
        """
        try:
            to_encode = data.copy()
            
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            
            to_encode.update({"exp": expire})
            
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Token de acceso creado para usuario: {data.get('sub', 'unknown')}")
            
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Error al crear token de acceso: {e}")
            raise
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Crear token de refresco JWT
        
        Args:
            data: Datos a incluir en el token
            
        Returns:
            Token JWT de refresco
        """
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            to_encode.update({"exp": expire, "type": "refresh"})
            
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Token de refresco creado para usuario: {data.get('sub', 'unknown')}")
            
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Error al crear token de refresco: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verificar y decodificar un token JWT
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            Datos decodificados del token o None si es inválido
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verificar que no haya expirado
            if datetime.fromtimestamp(payload.get("exp", 0)) < datetime.utcnow():
                logger.warning("Token expirado")
                return None
            
            logger.debug(f"Token verificado para usuario: {payload.get('sub', 'unknown')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Token JWT inválido: {e}")
            return None
        except Exception as e:
            logger.error(f"Error al verificar token: {e}")
            return None
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decodificar token sin verificar firma (solo para debugging)
        
        Args:
            token: Token JWT a decodificar
            
        Returns:
            Datos decodificados del token
        """
        try:
            # Decodificar sin verificar para debugging
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception as e:
            logger.error(f"Error al decodificar token: {e}")
            return None
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verificar contraseña plana contra hash
        
        Args:
            plain_password: Contraseña en texto plano
            hashed_password: Contraseña hasheada
            
        Returns:
            True si la contraseña coincide
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error al verificar contraseña: {e}")
            return False
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Generar hash de contraseña
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash de la contraseña
        """
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Error al generar hash de contraseña: {e}")
            raise
    
    def create_user_tokens(self, usuario: Usuario) -> Dict[str, str]:
        """
        Crear tokens de acceso y refresco para un usuario
        
        Args:
            usuario: Usuario para el cual crear tokens
            
        Returns:
            Diccionario con tokens de acceso y refresco
        """
        try:
            # Datos del token
            token_data = {
                "sub": str(usuario.id),
                "email": usuario.email,
                "rol": usuario.rol,
                "cliente_id": str(usuario.cliente_id) if usuario.cliente_id else None,
                "proyecto_id": str(usuario.proyecto_id) if usuario.proyecto_id else None,
                "unidad_id": str(usuario.unidad_id) if usuario.unidad_id else None,
                "activo": usuario.activo,
                "type": "access"
            }
            
            # Crear tokens
            access_token = self.create_access_token(token_data)
            refresh_token = self.create_refresh_token(token_data)
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
            
        except Exception as e:
            logger.error(f"Error al crear tokens para usuario {usuario.id}: {e}")
            raise
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Refrescar token de acceso usando token de refresco
        
        Args:
            refresh_token: Token de refresco válido
            
        Returns:
            Nuevo token de acceso o None si hay error
        """
        try:
            # Verificar token de refresco
            payload = self.verify_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                return None
            
            # Crear nuevo token de acceso
            token_data = {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "rol": payload.get("rol"),
                "cliente_id": payload.get("cliente_id"),
                "proyecto_id": payload.get("proyecto_id"),
                "unidad_id": payload.get("unidad_id"),
                "activo": payload.get("activo"),
                "type": "access"
            }
            
            new_access_token = self.create_access_token(token_data)
            logger.info(f"Token de acceso refrescado para usuario: {payload.get('sub')}")
            
            return new_access_token
            
        except Exception as e:
            logger.error(f"Error al refrescar token de acceso: {e}")
            return None
