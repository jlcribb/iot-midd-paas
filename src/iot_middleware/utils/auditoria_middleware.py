"""
Middleware de Auditoría para FastAPI - IoT Middleware
====================================================

Este middleware captura automáticamente el contexto de auditoría
de las peticiones HTTP, incluyendo usuario, IP, headers, etc.
"""

import logging
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Importar utilidades de auditoría
try:
    from .auditoria import AuditoriaService, ContextoAuditoria, create_auditoria_service
except ImportError:
    # Fallback para importación directa
    from iot_middleware.utils.auditoria import AuditoriaService, ContextoAuditoria, create_auditoria_service

# Configurar logging
logger = logging.getLogger(__name__)


class AuditoriaMiddleware(BaseHTTPMiddleware):
    """Middleware de FastAPI para auditoría automática"""
    
    def __init__(self, app: ASGIApp, 
                 auditoria_service: Optional[AuditoriaService] = None,
                 exclude_paths: Optional[list] = None,
                 include_headers: Optional[list] = None):
        super().__init__(app)
        self.auditoria_service = auditoria_service
        self.exclude_paths = exclude_paths or [
            '/health', '/metrics', '/docs', '/redoc', '/openapi.json'
        ]
        self.include_headers = include_headers or [
            'user-agent', 'referer', 'origin', 'x-forwarded-for',
            'x-real-ip', 'x-request-id', 'authorization'
        ]
        
        # Configurar logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa la petición HTTP y captura contexto de auditoría"""
        
        # Verificar si la ruta debe ser excluida
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        # Capturar información de la petición
        contexto = await self._capturar_contexto(request)
        
        # Establecer contexto de auditoría
        if self.auditoria_service:
            self.auditoria_service.set_contexto(contexto)
        
        # Procesar petición
        start_time = datetime.now(timezone.utc)
        
        try:
            response = await call_next(request)
            
            # Registrar auditoría de petición exitosa
            await self._auditar_peticion(request, response, contexto, start_time, success=True)
            
            return response
            
        except Exception as e:
            # Registrar auditoría de petición fallida
            await self._auditar_peticion(request, None, contexto, start_time, success=False, error=str(e))
            raise
        
        finally:
            # Limpiar contexto de auditoría
            if self.auditoria_service:
                self.auditoria_service.clear_contexto()
    
    def _should_exclude_path(self, path: str) -> bool:
        """Verifica si una ruta debe ser excluida de la auditoría"""
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False
    
    async def _capturar_contexto(self, request: Request) -> ContextoAuditoria:
        """Captura el contexto de auditoría de la petición"""
        try:
            # Obtener IP de origen
            ip_origen = self._obtener_ip_origen(request)
            
            # Obtener headers relevantes
            headers = self._obtener_headers_relevantes(request)
            
            # Obtener usuario autenticado (si existe)
            usuario_id = await self._obtener_usuario_id(request)
            
            # Obtener parámetros de la petición
            parametros = self._obtener_parametros(request)
            
            # Crear contexto de auditoría
            contexto = ContextoAuditoria(
                usuario_id=usuario_id,
                ip_origen=ip_origen,
                user_agent=request.headers.get('user-agent'),
                sesion_id=request.headers.get('x-session-id'),
                request_id=request.headers.get('x-request-id'),
                endpoint=str(request.url.path),
                metodo_http=request.method,
                headers=headers,
                parametros=parametros,
                timestamp=datetime.now(timezone.utc)
            )
            
            return contexto
            
        except Exception as e:
            self.logger.error(f"Error capturando contexto: {e}")
            # Retornar contexto básico en caso de error
            return ContextoAuditoria(
                ip_origen='0.0.0.0',
                endpoint=str(request.url.path),
                metodo_http=request.method,
                timestamp=datetime.now(timezone.utc)
            )
    
    def _obtener_ip_origen(self, request: Request) -> str:
        """Obtiene la IP de origen real de la petición"""
        # Probar diferentes headers para obtener IP real
        headers_ip = [
            'x-forwarded-for',
            'x-real-ip',
            'x-client-ip',
            'cf-connecting-ip',  # Cloudflare
            'x-forwarded',
            'forwarded-for',
            'forwarded'
        ]
        
        for header in headers_ip:
            if header in request.headers:
                ip = request.headers[header]
                # x-forwarded-for puede contener múltiples IPs
                if header == 'x-forwarded-for':
                    ip = ip.split(',')[0].strip()
                if ip and ip != 'unknown':
                    return ip
        
        # Fallback a la IP del cliente
        if request.client:
            return request.client.host
        
        return '0.0.0.0'
    
    def _obtener_headers_relevantes(self, request: Request) -> Dict[str, str]:
        """Obtiene headers relevantes para auditoría"""
        headers = {}
        
        for header_name in self.include_headers:
            if header_name in request.headers:
                # Sanitizar headers sensibles
                if header_name.lower() in ['authorization', 'cookie']:
                    headers[header_name] = '***SENSIBLE***'
                else:
                    headers[header_name] = request.headers[header_name]
        
        return headers
    
    async def _obtener_usuario_id(self, request: Request) -> Optional[str]:
        """Obtiene el ID del usuario autenticado"""
        try:
            # Verificar si hay usuario en el estado de la petición
            if hasattr(request.state, 'usuario') and request.state.usuario:
                return str(request.state.usuario.get('id'))
            
            # Verificar en headers de autorización
            auth_header = request.headers.get('authorization')
            if auth_header and auth_header.startswith('Bearer '):
                # Aquí se podría decodificar el JWT para obtener el usuario
                # Por ahora retornamos None
                pass
            
            return None
            
        except Exception as e:
            self.logger.debug(f"No se pudo obtener usuario: {e}")
            return None
    
    def _obtener_parametros(self, request: Request) -> Dict[str, Any]:
        """Obtiene parámetros de la petición"""
        parametros = {}
        
        try:
            # Parámetros de query
            if request.query_params:
                parametros['query'] = dict(request.query_params)
            
            # Parámetros de path
            if request.path_params:
                parametros['path'] = dict(request.path_params)
            
            # Body (solo para métodos que lo permiten)
            if request.method in ['POST', 'PUT', 'PATCH']:
                # No incluimos el body completo por seguridad
                parametros['body_size'] = request.headers.get('content-length', 'unknown')
                parametros['content_type'] = request.headers.get('content-type', 'unknown')
            
        except Exception as e:
            self.logger.debug(f"Error obteniendo parámetros: {e}")
        
        return parametros
    
    async def _auditar_peticion(self, 
                               request: Request, 
                               response: Optional[Response],
                               contexto: ContextoAuditoria,
                               start_time: datetime,
                               success: bool = True,
                               error: Optional[str] = None):
        """Audita la petición HTTP"""
        try:
            if not self.auditoria_service:
                return
            
            # Calcular duración
            end_time = datetime.now(timezone.utc)
            duracion_ms = (end_time - start_time).total_seconds() * 1000
            
            # Preparar cambios para auditoría
            cambios = {
                'antes': {
                    'timestamp_inicio': start_time.isoformat(),
                    'metodo': request.method,
                    'endpoint': str(request.url.path),
                    'query_params': dict(request.query_params) if request.query_params else None
                },
                'despues': {
                    'timestamp_fin': end_time.isoformat(),
                    'duracion_ms': round(duracion_ms, 2),
                    'status_code': response.status_code if response else None,
                    'exitoso': success
                }
            }
            
            # Agregar error si existe
            if error:
                cambios['despues']['error'] = error
            
            # Registrar en auditoría
            self.auditoria_service.registrar_cambio(
                entidad='http_request',
                entidad_id=None,
                accion='PROCESAR',
                cambios=cambios,
                contexto_adicional={
                    'duracion_ms': duracion_ms,
                    'exitoso': success,
                    'error': error
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error auditando petición: {e}")


class AuditoriaRequestMiddleware:
    """Middleware alternativo para auditoría de peticiones"""
    
    def __init__(self, 
                 auditoria_service: AuditoriaService,
                 exclude_paths: Optional[list] = None):
        self.auditoria_service = auditoria_service
        self.exclude_paths = exclude_paths or [
            '/health', '/metrics', '/docs', '/redoc', '/openapi.json'
        ]
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def __call__(self, request: Request, call_next: Callable):
        """Middleware callable para FastAPI"""
        
        # Verificar si la ruta debe ser excluida
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        # Capturar contexto
        contexto = await self._capturar_contexto_simple(request)
        self.auditoria_service.set_contexto(contexto)
        
        # Procesar petición
        start_time = datetime.now(timezone.utc)
        
        try:
            response = await call_next(request)
            await self._auditar_peticion_simple(request, response, contexto, start_time, True)
            return response
        except Exception as e:
            await self._auditar_peticion_simple(request, None, contexto, start_time, False, str(e))
            raise
        finally:
            self.auditoria_service.clear_contexto()
    
    def _should_exclude_path(self, path: str) -> bool:
        """Verifica si una ruta debe ser excluida"""
        return any(path.startswith(exclude) for exclude in self.exclude_paths)
    
    async def _capturar_contexto_simple(self, request: Request) -> ContextoAuditoria:
        """Captura contexto simplificado"""
        return ContextoAuditoria(
            usuario_id=None,  # Se puede implementar lógica de autenticación
            ip_origen=request.client.host if request.client else '0.0.0.0',
            user_agent=request.headers.get('user-agent'),
            endpoint=str(request.url.path),
            metodo_http=request.method,
            timestamp=datetime.now(timezone.utc)
        )
    
    async def _auditar_peticion_simple(self, 
                                     request: Request, 
                                     response: Optional[Response],
                                     contexto: ContextoAuditoria,
                                     start_time: datetime,
                                     success: bool,
                                     error: Optional[str] = None):
        """Audita petición de forma simplificada"""
        try:
            duracion_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            cambios = {
                'antes': {'endpoint': str(request.url.path), 'metodo': request.method},
                'despues': {
                    'status_code': response.status_code if response else None,
                    'duracion_ms': round(duracion_ms, 2),
                    'exitoso': success
                }
            }
            
            if error:
                cambios['despues']['error'] = error
            
            self.auditoria_service.registrar_cambio(
                entidad='http_request',
                entidad_id=None,
                accion='PROCESAR',
                cambios=cambios
            )
            
        except Exception as e:
            self.logger.error(f"Error en auditoría simple: {e}")


# Función de conveniencia para crear middleware
def create_auditoria_middleware(auditoria_service: AuditoriaService,
                               exclude_paths: Optional[list] = None) -> AuditoriaRequestMiddleware:
    """
    Crea un middleware de auditoría
    
    Args:
        auditoria_service: Servicio de auditoría
        exclude_paths: Rutas a excluir de la auditoría
    
    Returns:
        Middleware de auditoría
    """
    return AuditoriaRequestMiddleware(auditoria_service, exclude_paths)


# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    print("🔍 Middleware de Auditoría - IoT Middleware")
    print("=" * 50)
    
    print("✅ Middleware de auditoría cargado exitosamente")
    print("📚 Funcionalidades disponibles:")
    print("   - Captura automática de contexto HTTP")
    print("   - Auditoría de peticiones y respuestas")
    print("   - Filtrado de rutas sensibles")
    print("   - Sanitización de datos sensibles")
    print("   - Integración con FastAPI")
