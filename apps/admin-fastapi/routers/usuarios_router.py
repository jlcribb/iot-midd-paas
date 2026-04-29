"""
Router CRUD para Usuarios
"""

from fastapi import APIRouter, Request, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class UsuarioCreate(BaseModel):
    email: EmailStr
    nombre: str
    apellido: Optional[str] = None
    password: str
    rol: str = "lectura"
    activo: bool = True
    configuracion: Dict[str, Any] = {}


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    password: Optional[str] = None
    rol: Optional[str] = None
    activo: Optional[bool] = None
    configuracion: Optional[Dict[str, Any]] = None


class UsuarioResponse(BaseModel):
    id: str
    email: str
    nombre: str
    apellido: Optional[str]
    rol: str
    activo: bool
    ultimo_login: Optional[str]
    creado_en: str

    class Config:
        from_attributes = True


def get_usuario_repository(request: Request):
    """Obtener repositorio de usuarios"""
    db_handler = request.app.state.db_handler
    if not db_handler:
        raise HTTPException(status_code=500, detail="Base de datos no inicializada")
    
    # Intentar importar repositorio de usuarios
    try:
        from iot_middleware.storage.repositories.usuario_repository import UsuarioRepository
        return UsuarioRepository(db_handler)
    except ImportError:
        # Si no existe, crear uno básico
        from iot_middleware.storage.repositories.base_repository import BaseRepository
        from iot_middleware.models.entities import Usuario
        return BaseRepository(db_handler, Usuario)


@router.get("/", response_model=List[UsuarioResponse])
async def list_usuarios(request: Request, activo: Optional[bool] = Query(None)):
    """Listar usuarios"""
    try:
        usuario_repo = get_usuario_repository(request)
        usuarios = usuario_repo.get_all()
        
        if activo is not None:
            usuarios = [u for u in usuarios if u.activo == activo]
        
        return [
            UsuarioResponse(
                id=str(u.id),
                email=u.email,
                nombre=u.nombre,
                apellido=u.apellido,
                rol=u.rol.value if hasattr(u.rol, 'value') else str(u.rol),
                activo=u.activo,
                ultimo_login=u.ultimo_login.isoformat() if u.ultimo_login else None,
                creado_en=u.creado_en.isoformat() if u.creado_en else ""
            )
            for u in usuarios
        ]
    except Exception as e:
        logger.error(f"Error al listar usuarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def get_usuario(request: Request, usuario_id: str):
    """Obtener un usuario por ID"""
    try:
        usuario_repo = get_usuario_repository(request)
        usuario = usuario_repo.get_by_id(usuario_id)
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return UsuarioResponse(
            id=str(usuario.id),
            email=usuario.email,
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            rol=usuario.rol.value if hasattr(usuario.rol, 'value') else str(usuario.rol),
            activo=usuario.activo,
            ultimo_login=usuario.ultimo_login.isoformat() if usuario.ultimo_login else None,
            creado_en=usuario.creado_en.isoformat() if usuario.creado_en else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=UsuarioResponse)
async def create_usuario(request: Request, usuario_data: UsuarioCreate):
    """Crear un nuevo usuario"""
    try:
        usuario_repo = get_usuario_repository(request)
        
        # Hash de contraseña
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password_hash = pwd_context.hash(usuario_data.password)
        
        # Preparar datos
        data = usuario_data.model_dump(exclude={'password'})
        data['password_hash'] = password_hash
        
        # Convertir rol
        from iot_middleware.models.enums import RolSistema
        data['rol'] = RolSistema[usuario_data.rol.upper()]
        
        usuario = usuario_repo.create(data)
        
        if not usuario:
            raise HTTPException(status_code=500, detail="Error al crear usuario")
        
        return UsuarioResponse(
            id=str(usuario.id),
            email=usuario.email,
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            rol=usuario.rol.value if hasattr(usuario.rol, 'value') else str(usuario.rol),
            activo=usuario.activo,
            ultimo_login=usuario.ultimo_login.isoformat() if usuario.ultimo_login else None,
            creado_en=usuario.creado_en.isoformat() if usuario.creado_en else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(request: Request, usuario_id: str, usuario_data: UsuarioUpdate):
    """Actualizar un usuario"""
    try:
        usuario_repo = get_usuario_repository(request)
        data = usuario_data.model_dump(exclude_unset=True)
        
        # Hash de contraseña si se proporciona
        if 'password' in data:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            data['password_hash'] = pwd_context.hash(data.pop('password'))
        
        # Convertir rol si se proporciona
        if 'rol' in data:
            from iot_middleware.models.enums import RolSistema
            data['rol'] = RolSistema[data['rol'].upper()]
        
        usuario = usuario_repo.update(usuario_id, data)
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return UsuarioResponse(
            id=str(usuario.id),
            email=usuario.email,
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            rol=usuario.rol.value if hasattr(usuario.rol, 'value') else str(usuario.rol),
            activo=usuario.activo,
            ultimo_login=usuario.ultimo_login.isoformat() if usuario.ultimo_login else None,
            creado_en=usuario.creado_en.isoformat() if usuario.creado_en else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{usuario_id}")
async def delete_usuario(request: Request, usuario_id: str):
    """Eliminar un usuario (soft delete)"""
    try:
        usuario_repo = get_usuario_repository(request)
        usuario = usuario_repo.update(usuario_id, {'activo': False})
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {"message": "Usuario eliminado exitosamente", "id": usuario_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))
