"""
Utilidad de Auditoría - IoT Middleware
======================================

Este módulo implementa un sistema completo de auditoría que registra
todos los cambios en entidades críticas del sistema:
- config_middleware
- canales
- eventos_alarmas

Cada cambio se estructura como {antes: {}, despues: {}} y se guarda
con información del usuario e IP de origen.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import threading
from functools import wraps

# Importar modelos
try:
    from ..models.entities import Auditoria, Usuario
    from ..models.enums import TipoDato, SeveridadEvento
    from ..storage.db_handler import DatabaseHandler
except ImportError:
    # Fallback para importación directa
    from iot_middleware.models.entities import Auditoria, Usuario
    from iot_middleware.models.enums import TipoDato, SeveridadEvento
    from iot_middleware.storage.db_handler import DatabaseHandler

# Configurar logging
logger = logging.getLogger(__name__)


class AccionAuditoria(Enum):
    """Tipos de acciones auditables"""
    CREAR = "CREAR"
    ACTUALIZAR = "ACTUALIZAR"
    ELIMINAR = "ELIMINAR"
    ACTIVAR = "ACTIVAR"
    DESACTIVAR = "DESACTIVAR"
    CONFIGURAR = "CONFIGURAR"
    VALIDAR = "VALIDAR"
    PROCESAR = "PROCESAR"
    RECONOCER = "RECONOCER"
    RESOLVER = "RESOLVER"


class EntidadAuditable(Enum):
    """Entidades que pueden ser auditadas"""
    CONFIG_MIDDLEWARE = "config_middleware"
    CANAL = "canal"
    EVENTO_ALARMA = "evento_alarma"
    DISPOSITIVO = "dispositivo"
    PROYECTO = "proyecto"
    USUARIO = "usuario"
    CLIENTE = "cliente"


@dataclass
class ContextoAuditoria:
    """Contexto de auditoría para una operación"""
    usuario_id: Optional[str] = None
    ip_origen: Optional[str] = None
    user_agent: Optional[str] = None
    sesion_id: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    metodo_http: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None
    parametros: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AuditoriaService:
    """Servicio principal de auditoría"""
    
    def __init__(self, db_handler: DatabaseHandler):
        self.db_handler = db_handler
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Contexto de auditoría por thread
        self._contexto_thread_local = threading.local()
        
        # Configuración
        self.auditoria_habilitada = True
        self.auditoria_sensible = True
        self.max_tamano_cambios = 10000  # 10KB máximo por registro
        
        # Cache de entidades auditadas
        self._entidades_cache = set()
    
    def set_contexto(self, contexto: ContextoAuditoria):
        """Establece el contexto de auditoría para el thread actual"""
        self._contexto_thread_local.contexto = contexto
    
    def get_contexto(self) -> Optional[ContextoAuditoria]:
        """Obtiene el contexto de auditoría del thread actual"""
        return getattr(self._contexto_thread_local, 'contexto', None)
    
    def clear_contexto(self):
        """Limpia el contexto de auditoría del thread actual"""
        if hasattr(self._contexto_thread_local, 'contexto'):
            delattr(self._contexto_thread_local, 'contexto')
    
    def registrar_cambio(self, 
                        entidad: Union[str, EntidadAuditable],
                        entidad_id: Optional[str],
                        accion: Union[str, AccionAuditoria],
                        cambios: Dict[str, Any],
                        contexto_adicional: Optional[Dict[str, Any]] = None) -> bool:
        """
        Registra un cambio en la base de datos de auditoría
        
        Args:
            entidad: Nombre de la entidad auditada
            entidad_id: ID de la entidad (opcional para operaciones de creación)
            accion: Tipo de acción realizada
            cambios: Diccionario con cambios {antes: {}, despues: {}}
            contexto_adicional: Información adicional del contexto
        
        Returns:
            True si se registró exitosamente, False en caso contrario
        """
        try:
            if not self.auditoria_habilitada:
                return True
            
            # Obtener contexto actual
            contexto = self.get_contexto()
            if not contexto:
                self.logger.warning("⚠️  No hay contexto de auditoría disponible")
                return False
            
            # Validar entidad
            if isinstance(entidad, EntidadAuditable):
                entidad_str = entidad.value
            else:
                entidad_str = str(entidad)
            
            # Validar acción
            if isinstance(accion, AccionAuditoria):
                accion_str = accion.value
            else:
                accion_str = str(accion)
            
            # Preparar datos de auditoría
            datos_auditoria = {
                'usuario_id': contexto.usuario_id,
                'entidad': entidad_str,
                'entidad_id': entidad_id,
                'accion': accion_str,
                'cambios': self._sanitizar_cambios(cambios),
                'ip_origen': contexto.ip_origen,
                'user_agent': contexto.user_agent,
                'contexto': self._preparar_contexto(contexto, contexto_adicional),
                'ts': contexto.timestamp
            }
            
            # Insertar en base de datos
            return self._insertar_auditoria(datos_auditoria)
            
        except Exception as e:
            self.logger.error(f"❌ Error registrando auditoría: {e}")
            return False
    
    def _sanitizar_cambios(self, cambios: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitiza y valida los cambios antes de guardarlos"""
        try:
            # Verificar estructura básica
            if not isinstance(cambios, dict):
                return {'error': 'Formato de cambios inválido'}
            
            # Limitar tamaño
            cambios_json = json.dumps(cambios, ensure_ascii=False)
            if len(cambios_json) > self.max_tamano_cambios:
                cambios = {
                    'antes': {'_truncado': True, 'tamano_original': len(cambios_json)},
                    'despues': {'_truncado': True, 'tamano_original': len(cambios_json)},
                    'mensaje': 'Cambios truncados por tamaño excesivo'
                }
            
            # Sanitizar datos sensibles
            if self.auditoria_sensible:
                cambios = self._sanitizar_datos_sensibles(cambios)
            
            return cambios
            
        except Exception as e:
            self.logger.error(f"Error sanitizando cambios: {e}")
            return {'error': f'Error sanitizando cambios: {e}'}
    
    def _sanitizar_datos_sensibles(self, cambios: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitiza datos sensibles como contraseñas y tokens"""
        campos_sensibles = {
            'password', 'passwd', 'pwd', 'secret', 'token', 'api_key',
            'private_key', 'certificate', 'credential', 'auth'
        }
        
        def sanitizar_objeto(obj):
            if isinstance(obj, dict):
                return {k: '***SENSIBLE***' if k.lower() in campos_sensibles else sanitizar_objeto(v) 
                       for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitizar_objeto(item) for item in obj]
            else:
                return obj
        
        return sanitizar_objeto(cambios)
    
    def _preparar_contexto(self, contexto: ContextoAuditoria, 
                          contexto_adicional: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepara el contexto para almacenamiento"""
        contexto_dict = {
            'sesion_id': contexto.sesion_id,
            'request_id': contexto.request_id,
            'endpoint': contexto.endpoint,
            'metodo_http': contexto.metodo_http,
            'timestamp': contexto.timestamp.isoformat()
        }
        
        # Agregar contexto adicional si existe
        if contexto_adicional:
            contexto_dict.update(contexto_adicional)
        
        # Filtrar valores None
        return {k: v for k, v in contexto_dict.items() if v is not None}
    
    def _insertar_auditoria(self, datos: Dict[str, Any]) -> bool:
        """Inserta el registro de auditoría en la base de datos"""
        try:
            # Crear objeto de auditoría
            auditoria = Auditoria(**datos)
            
            # Insertar en base de datos
            with self.db_handler.get_session() as session:
                session.add(auditoria)
                session.commit()
            
            self.logger.debug(f"✅ Auditoría registrada: {datos['entidad']} - {datos['accion']}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error insertando auditoría: {e}")
            return False
    
    def auditar_config_middleware(self, 
                                 config_id: str,
                                 accion: AccionAuditoria,
                                 antes: Optional[Dict[str, Any]] = None,
                                 despues: Optional[Dict[str, Any]] = None) -> bool:
        """Audita cambios en config_middleware"""
        cambios = {
            'antes': antes or {},
            'despues': despues or {}
        }
        
        return self.registrar_cambio(
            entidad=EntidadAuditable.CONFIG_MIDDLEWARE,
            entidad_id=config_id,
            accion=accion,
            cambios=cambios
        )
    
    def auditar_canal(self, 
                      canal_id: str,
                      accion: AccionAuditoria,
                      antes: Optional[Dict[str, Any]] = None,
                      despues: Optional[Dict[str, Any]] = None) -> bool:
        """Audita cambios en canales"""
        cambios = {
            'antes': antes or {},
            'despues': despues or {}
        }
        
        return self.registrar_cambio(
            entidad=EntidadAuditable.CANAL,
            entidad_id=canal_id,
            accion=accion,
            cambios=cambios
        )
    
    def auditar_evento_alarma(self, 
                              evento_id: str,
                              accion: AccionAuditoria,
                              antes: Optional[Dict[str, Any]] = None,
                              despues: Optional[Dict[str, Any]] = None) -> bool:
        """Audita cambios en eventos de alarma"""
        cambios = {
            'antes': antes or {},
            'despues': despues or {}
        }
        
        return self.registrar_cambio(
            entidad=EntidadAuditable.EVENTO_ALARMA,
            entidad_id=evento_id,
            accion=accion,
            cambios=cambios
        )
    
    def auditar_dispositivo(self, 
                            dispositivo_id: str,
                            accion: AccionAuditoria,
                            antes: Optional[Dict[str, Any]] = None,
                            despues: Optional[Dict[str, Any]] = None) -> bool:
        """Audita cambios en dispositivos"""
        cambios = {
            'antes': antes or {},
            'despues': despues or {}
        }
        
        return self.registrar_cambio(
            entidad=EntidadAuditable.DISPOSITIVO,
            entidad_id=dispositivo_id,
            accion=accion,
            cambios=cambios
        )
    
    def auditar_proyecto(self, 
                          proyecto_id: str,
                          accion: AccionAuditoria,
                          antes: Optional[Dict[str, Any]] = None,
                          despues: Optional[Dict[str, Any]] = None) -> bool:
        """Audita cambios en proyectos"""
        cambios = {
            'antes': antes or {},
            'despues': despues or {}
        }
        
        return self.registrar_cambio(
            entidad=EntidadAuditable.PROYECTO,
            entidad_id=proyecto_id,
            accion=accion,
            cambios=cambios
        )
    
    def auditar_usuario(self, 
                        usuario_id: str,
                        accion: AccionAuditoria,
                        antes: Optional[Dict[str, Any]] = None,
                        despues: Optional[Dict[str, Any]] = None) -> bool:
        """Audita cambios en usuarios"""
        cambios = {
            'antes': antes or {},
            'despues': despues or {}
        }
        
        return self.registrar_cambio(
            entidad=EntidadAuditable.USUARIO,
            entidad_id=usuario_id,
            accion=accion,
            cambios=cambios
        )
    
    def auditar_cliente(self, 
                        cliente_id: str,
                        accion: AccionAuditoria,
                        antes: Optional[Dict[str, Any]] = None,
                        despues: Optional[Dict[str, Any]] = None) -> bool:
        """Audita cambios en clientes"""
        cambios = {
            'antes': antes or {},
            'despues': despues or {}
        }
        
        return self.registrar_cambio(
            entidad=EntidadAuditable.CLIENTE,
            entidad_id=cliente_id,
            accion=accion,
            cambios=cambios
        )
    
    def obtener_auditoria(self, 
                          entidad: Optional[str] = None,
                          entidad_id: Optional[str] = None,
                          usuario_id: Optional[str] = None,
                          accion: Optional[str] = None,
                          fecha_desde: Optional[datetime] = None,
                          fecha_hasta: Optional[datetime] = None,
                          limite: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene registros de auditoría con filtros
        
        Args:
            entidad: Filtrar por entidad
            entidad_id: Filtrar por ID de entidad
            usuario_id: Filtrar por usuario
            accion: Filtrar por acción
            fecha_desde: Fecha desde
            fecha_hasta: Fecha hasta
            limite: Límite de resultados
        
        Returns:
            Lista de registros de auditoría
        """
        try:
            with self.db_handler.get_session() as session:
                query = session.query(Auditoria)
                
                # Aplicar filtros
                if entidad:
                    query = query.filter(Auditoria.entidad == entidad)
                if entidad_id:
                    query = query.filter(Auditoria.entidad_id == entidad_id)
                if usuario_id:
                    query = query.filter(Auditoria.usuario_id == usuario_id)
                if accion:
                    query = query.filter(Auditoria.accion == accion)
                if fecha_desde:
                    query = query.filter(Auditoria.ts >= fecha_desde)
                if fecha_hasta:
                    query = query.filter(Auditoria.ts <= fecha_hasta)
                
                # Ordenar por timestamp descendente
                query = query.order_by(Auditoria.ts.desc())
                
                # Limitar resultados
                query = query.limit(limite)
                
                # Ejecutar consulta
                resultados = query.all()
                
                # Convertir a diccionarios
                return [self._auditoria_to_dict(auditoria) for auditoria in resultados]
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo auditoría: {e}")
            return []
    
    def _auditoria_to_dict(self, auditoria: Auditoria) -> Dict[str, Any]:
        """Convierte un objeto Auditoria a diccionario"""
        return {
            'id': auditoria.id,
            'usuario_id': str(auditoria.usuario_id) if auditoria.usuario_id else None,
            'entidad': auditoria.entidad,
            'entidad_id': str(auditoria.entidad_id) if auditoria.entidad_id else None,
            'accion': auditoria.accion,
            'cambios': auditoria.cambios,
            'ip_origen': str(auditoria.ip_origen) if auditoria.ip_origen else None,
            'user_agent': auditoria.user_agent,
            'contexto': auditoria.contexto,
            'timestamp': auditoria.ts.isoformat() if auditoria.ts else None
        }
    
    def generar_reporte_auditoria(self, 
                                 fecha_desde: datetime,
                                 fecha_hasta: datetime,
                                 formato: str = 'json') -> Union[str, Dict[str, Any]]:
        """
        Genera un reporte de auditoría para un período
        
        Args:
            fecha_desde: Fecha desde
            fecha_hasta: Fecha hasta
            formato: Formato del reporte ('json', 'csv', 'html')
        
        Returns:
            Reporte en el formato especificado
        """
        if formato not in {'json', 'csv', 'html'}:
            raise ValueError(f"Formato no soportado: {formato}")

        try:
            # Obtener datos de auditoría
            registros = self.obtener_auditoria(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                limite=10000  # Límite alto para reportes
            )
            
            # Generar estadísticas
            estadisticas = self._generar_estadisticas(registros)
            
            # Generar reporte según formato
            if formato == 'json':
                return {
                    'periodo': {
                        'desde': fecha_desde.isoformat(),
                        'hasta': fecha_hasta.isoformat()
                    },
                    'estadisticas': estadisticas,
                    'registros': registros
                }
            elif formato == 'csv':
                return self._generar_csv(registros, estadisticas)
            elif formato == 'html':
                return self._generar_html(registros, estadisticas)
            raise AssertionError("validated report format was not handled")
                
        except Exception as e:
            self.logger.error(f"❌ Error generando reporte: {e}")
            return f"Error generando reporte: {e}"
    
    def _generar_estadisticas(self, registros: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Genera estadísticas de los registros de auditoría"""
        if not registros:
            return {}
        
        # Contar por entidad
        entidades = {}
        acciones = {}
        usuarios = {}
        
        for registro in registros:
            # Contar entidades
            entidad = registro['entidad']
            entidades[entidad] = entidades.get(entidad, 0) + 1
            
            # Contar acciones
            accion = registro['accion']
            acciones[accion] = acciones.get(accion, 0) + 1
            
            # Contar usuarios
            usuario = registro['usuario_id']
            if usuario:
                usuarios[usuario] = usuarios.get(usuario, 0) + 1
        
        return {
            'total_registros': len(registros),
            'entidades': entidades,
            'acciones': acciones,
            'usuarios_unicos': len(usuarios),
            'usuario_mas_activo': max(usuarios.items(), key=lambda x: x[1]) if usuarios else None
        }
    
    def _generar_csv(self, registros: List[Dict[str, Any]], 
                     estadisticas: Dict[str, Any]) -> str:
        """Genera reporte en formato CSV"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow([
            'ID', 'Usuario', 'Entidad', 'Entidad_ID', 'Acción', 
            'IP_Origen', 'Timestamp', 'Cambios'
        ])
        
        # Datos
        for registro in registros:
            cambios_str = json.dumps(registro['cambios'], ensure_ascii=False)
            writer.writerow([
                registro['id'],
                registro['usuario_id'] or '',
                registro['entidad'],
                registro['entidad_id'] or '',
                registro['accion'],
                registro['ip_origen'] or '',
                registro['timestamp'] or '',
                cambios_str
            ])
        
        return output.getvalue()
    
    def _generar_html(self, registros: List[Dict[str, Any]], 
                      estadisticas: Dict[str, Any]) -> str:
        """Genera reporte en formato HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Reporte de Auditoría</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .stats {{ margin: 20px 0; padding: 15px; background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>Reporte de Auditoría</h1>
            
            <div class="stats">
                <h2>Estadísticas</h2>
                <p><strong>Total de registros:</strong> {estadisticas.get('total_registros', 0)}</p>
                <p><strong>Usuarios únicos:</strong> {estadisticas.get('usuarios_unicos', 0)}</p>
            </div>
            
            <table>
                <tr>
                    <th>ID</th>
                    <th>Usuario</th>
                    <th>Entidad</th>
                    <th>Entidad ID</th>
                    <th>Acción</th>
                    <th>IP Origen</th>
                    <th>Timestamp</th>
                </tr>
        """
        
        for registro in registros:
            html += f"""
                <tr>
                    <td>{registro['id']}</td>
                    <td>{registro['usuario_id'] or ''}</td>
                    <td>{registro['entidad']}</td>
                    <td>{registro['entidad_id'] or ''}</td>
                    <td>{registro['accion']}</td>
                    <td>{registro['ip_origen'] or ''}</td>
                    <td>{registro['timestamp'] or ''}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html


# Decoradores para auditoría automática
def auditar_cambios(entidad: EntidadAuditable, accion: AccionAuditoria):
    """
    Decorador para auditar cambios automáticamente
    
    Args:
        entidad: Entidad a auditar
        accion: Acción a auditar
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener servicio de auditoría del primer argumento (self)
            if args and hasattr(args[0], 'auditoria_service'):
                auditoria_service = args[0].auditoria_service
                
                # Ejecutar función original
                resultado = func(*args, **kwargs)
                
                # Auditar cambio
                try:
                    # Extraer ID de la entidad de los argumentos o resultado
                    entidad_id = None
                    if 'id' in kwargs:
                        entidad_id = kwargs['id']
                    elif args and len(args) > 1:
                        entidad_id = str(args[1])
                    
                    if entidad_id:
                        auditoria_service.registrar_cambio(
                            entidad=entidad,
                            entidad_id=entidad_id,
                            accion=accion,
                            cambios={'operacion': func.__name__, 'args': str(args), 'kwargs': str(kwargs)}
                        )
                except Exception as e:
                    logger.warning(f"⚠️  Error en auditoría automática: {e}")
                
                return resultado
            else:
                # No hay servicio de auditoría, ejecutar función sin auditar
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Context manager para auditoría
@contextmanager
def contexto_auditoria(auditoria_service: AuditoriaService, 
                       usuario_id: str,
                       ip_origen: Optional[str] = None,
                       **kwargs):
    """
    Context manager para establecer contexto de auditoría
    
    Args:
        auditoria_service: Servicio de auditoría
        usuario_id: ID del usuario
        ip_origen: IP de origen
        **kwargs: Otros parámetros del contexto
    """
    contexto = ContextoAuditoria(
        usuario_id=usuario_id,
        ip_origen=ip_origen,
        **kwargs
    )
    
    try:
        auditoria_service.set_contexto(contexto)
        yield auditoria_service
    finally:
        auditoria_service.clear_contexto()


# Función de conveniencia para crear servicio de auditoría
def create_auditoria_service(db_handler: DatabaseHandler) -> AuditoriaService:
    """
    Crea una instancia del servicio de auditoría
    
    Args:
        db_handler: Manejador de base de datos
    
    Returns:
        Instancia del servicio de auditoría
    """
    return AuditoriaService(db_handler)


# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    print("🔍 Servicio de Auditoría - IoT Middleware")
    print("=" * 50)
    
    # Ejemplo de uso básico
    print("✅ Módulo de auditoría cargado exitosamente")
    print("📚 Funcionalidades disponibles:")
    print("   - Auditoría automática de cambios")
    print("   - Registro de contexto (usuario, IP, etc.)")
    print("   - Generación de reportes")
    print("   - Decoradores para auditoría automática")
    print("   - Context managers para auditoría")
