"""
Conector HTTP/REST - IoT Middleware
===================================

Permite recibir datos IoT directamente vía endpoints HTTP/REST.
Útil para dispositivos que ya envían datos vía POST o para integraciones
con sistemas externos.
"""

import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import ssl

from ..base_connector import BaseConnector, ConnectorConfig, UnifiedDataFormat, DataQuality, ConnectorStatus


@dataclass
class HTTPConnectorConfig(ConnectorConfig):
    """Configuración específica para el conector HTTP"""
    host: str = "0.0.0.0"
    port: int = 8080
    endpoint: str = "/ingest"
    ssl_enabled: bool = False
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    auth_enabled: bool = False
    auth_token: Optional[str] = None
    cors_enabled: bool = True
    max_content_length: int = 1024 * 1024  # 1MB
    allowed_methods: List[str] = None
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # segundos
    
    def __post_init__(self):
        if self.allowed_methods is None:
            self.allowed_methods = ["POST", "GET", "OPTIONS"]


class HTTPConnector(BaseConnector):
    """
    Conector HTTP que expone endpoints para recibir datos IoT
    
    Este conector implementa un servidor HTTP que puede recibir datos
    desde dispositivos o sistemas externos vía POST/GET.
    """
    
    def __init__(self, config: HTTPConnectorConfig, data_callback=None):
        super().__init__(config, data_callback)
        
        # Configuración específica de HTTP
        self.http_config = HTTPConnectorConfig(**config.__dict__) if isinstance(config, ConnectorConfig) else config
        
        # Servidor HTTP
        self.http_server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        
        # Control de rate limiting
        self.request_timestamps: List[float] = []
        self.rate_limit_lock = threading.Lock()
        
        # Logging específico
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def connect(self) -> bool:
        """Inicia el servidor HTTP"""
        try:
            self.logger.info(f"🌐 Iniciando servidor HTTP en {self.http_config.host}:{self.http_config.port}")
            
            # Crear manejador HTTP personalizado
            handler_class = self._create_request_handler_class()
            
            # Crear servidor HTTP
            self.http_server = HTTPServer(
                (self.http_config.host, self.http_config.port),
                handler_class
            )
            
            # Configurar SSL si está habilitado
            if self.http_config.ssl_enabled:
                if not self.http_config.ssl_certfile or not self.http_config.ssl_keyfile:
                    self.logger.error("SSL habilitado pero no se especificaron certificados")
                    return False
                
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_cert_chain(
                    self.http_config.ssl_certfile,
                    self.http_config.ssl_keyfile
                )
                self.http_server.socket = context.wrap_socket(
                    self.http_server.socket,
                    server_side=True
                )
                self.logger.info("🔒 SSL habilitado para el servidor HTTP")
            
            # Iniciar servidor en thread separado
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True,
                name=f"HTTP_Server_{self.config.name}"
            )
            self.server_thread.start()
            
            # Esperar a que el servidor esté listo
            time.sleep(0.5)
            
            if self.http_server:
                self.status = ConnectorStatus.CONNECTED
                self.connected = True
                self.last_connection_time = datetime.now(timezone.utc)
                self.logger.info(f"✅ Servidor HTTP iniciado en {self.http_config.host}:{self.http_config.port}")
                return True
            else:
                self.logger.error("❌ No se pudo iniciar el servidor HTTP")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error iniciando servidor HTTP: {e}")
            self.status = ConnectorStatus.ERROR
            self._handle_connection_error(e)
            return False
    
    def disconnect(self) -> bool:
        """Detiene el servidor HTTP"""
        try:
            if self.http_server:
                self.http_server.shutdown()
                self.http_server.server_close()
                self.http_server = None
            
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=5.0)
            
            self.status = ConnectorStatus.DISCONNECTED
            self.connected = False
            
            self.logger.info("✅ Servidor HTTP detenido")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error deteniendo servidor HTTP: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Verifica si el servidor HTTP está funcionando"""
        return self.connected and self.http_server is not None
    
    def _receive_data(self) -> Optional[Any]:
        """
        Recibe datos del servidor HTTP
        
        En HTTP, los datos se reciben de forma asíncrona a través de
        las solicitudes HTTP. No necesitamos implementar polling aquí.
        """
        return None
    
    def _parse_raw_data(self, raw_data: Any) -> Optional[UnifiedDataFormat]:
        """
        Parsea datos HTTP al formato unificado
        
        Args:
            raw_data: Datos HTTP (dict con headers, body, etc.)
            
        Returns:
            Datos en formato unificado
        """
        try:
            if not isinstance(raw_data, dict):
                self.logger.warning(f"Formato de datos HTTP no reconocido: {type(raw_data)}")
                return None
            
            # Extraer información de la solicitud
            headers = raw_data.get('headers', {})
            body = raw_data.get('body', {})
            method = raw_data.get('method', 'POST')
            path = raw_data.get('path', '')
            query_params = raw_data.get('query_params', {})
            client_ip = raw_data.get('client_ip', 'unknown')
            
            # Parsear cuerpo de la solicitud
            measurements = self._parse_http_body(body, headers)
            
            # Extraer información del dispositivo desde headers o query params
            device_id = (
                headers.get('X-Device-ID') or 
                query_params.get('device_id') or 
                body.get('device_id') or 
                'unknown'
            )
            
            project_id = (
                headers.get('X-Project-ID') or 
                query_params.get('project_id') or 
                body.get('project_id') or 
                'default'
            )
            
            # Crear datos unificados
            unified_data = UnifiedDataFormat(
                device_id=device_id,
                project_id=project_id,
                timestamp=datetime.now(timezone.utc),
                measurements=measurements,
                metadata={
                    'method': method,
                    'path': path,
                    'query_params': query_params,
                    'client_ip': client_ip,
                    'headers': {k: v for k, v in headers.items() if not k.lower().startswith('authorization')},
                    'content_type': headers.get('Content-Type', 'application/json')
                },
                quality=DataQuality.VALID,
                source_protocol='http',
                source_address=f"{client_ip}:{self.http_config.port}",
                raw_data=raw_data
            )
            
            return unified_data
            
        except Exception as e:
            self.logger.error(f"Error parseando datos HTTP: {e}")
            return None
    
    def _parse_http_body(self, body: Any, headers: Dict[str, str]) -> Dict[str, Any]:
        """Parsea el cuerpo de la solicitud HTTP"""
        try:
            content_type = headers.get('Content-Type', '').lower()
            
            if isinstance(body, dict):
                return body
            
            elif isinstance(body, str):
                if 'application/json' in content_type:
                    try:
                        return json.loads(body)
                    except json.JSONDecodeError:
                        self.logger.warning("Cuerpo JSON inválido, tratando como texto")
                        return {'value': body}
                else:
                    return {'value': body}
            
            elif isinstance(body, bytes):
                try:
                    return json.loads(body.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return {'raw_bytes': str(body)}
            
            else:
                return {'raw_value': str(body)}
                
        except Exception as e:
            self.logger.error(f"Error parseando cuerpo HTTP: {e}")
            return {'error': str(e)}
    
    def _run_server(self):
        """Ejecuta el servidor HTTP"""
        try:
            self.logger.info(f"🔄 Servidor HTTP ejecutándose en {self.http_config.host}:{self.http_config.port}")
            self.http_server.serve_forever()
        except Exception as e:
            self.logger.error(f"Error en servidor HTTP: {e}")
        finally:
            self.logger.info("🛑 Servidor HTTP detenido")
    
    def _create_request_handler_class(self):
        """Crea una clase de manejador HTTP personalizada"""
        
        class IoTRequestHandler(BaseHTTPRequestHandler):
            """Manejador personalizado para solicitudes IoT"""
            
            def __init__(self, *args, **kwargs):
                self.connector = self.server.connector
                super().__init__(*args, **kwargs)
            
            def log_message(self, format, *args):
                """Personaliza el logging de solicitudes"""
                self.connector.logger.info(f"HTTP: {format % args}")
            
            def do_OPTIONS(self):
                """Maneja solicitudes OPTIONS para CORS"""
                if self.connector.http_config.cors_enabled:
                    self._send_cors_headers()
                    self.send_response(200)
                    self.end_headers()
                else:
                    self.send_response(405)
                    self.end_headers()
            
            def do_GET(self):
                """Maneja solicitudes GET"""
                if 'GET' not in self.connector.http_config.allowed_methods:
                    self.send_response(405)
                    self.end_headers()
                    return
                
                try:
                    # Verificar rate limiting
                    if not self.connector._check_rate_limit():
                        self.send_response(429)
                        self.end_headers()
                        self.wfile.write(b"Rate limit exceeded")
                        return
                    
                    # Parsear query parameters
                    parsed_url = urlparse(self.path)
                    query_params = parse_qs(parsed_url.query)
                    
                    # Crear datos de la solicitud
                    request_data = {
                        'method': 'GET',
                        'path': self.path,
                        'query_params': {k: v[0] if v else '' for k, v in query_params.items()},
                        'headers': dict(self.headers),
                        'body': {},
                        'client_ip': self.client_address[0]
                    }
                    
                    # Procesar datos
                    self.connector._process_http_request(request_data)
                    
                    # Respuesta exitosa
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    if self.connector.http_config.cors_enabled:
                        self._send_cors_headers()
                    self.end_headers()
                    
                    response = {
                        'status': 'success',
                        'message': 'Data received successfully',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    self.wfile.write(json.dumps(response).encode())
                    
                except Exception as e:
                    self.connector.logger.error(f"Error procesando GET: {e}")
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b"Internal server error")
            
            def do_POST(self):
                """Maneja solicitudes POST"""
                if 'POST' not in self.connector.http_config.allowed_methods:
                    self.send_response(405)
                    self.end_headers()
                    return
                
                try:
                    # Verificar rate limiting
                    if not self.connector._check_rate_limit():
                        self.send_response(429)
                        self.end_headers()
                        self.wfile.write(b"Rate limit exceeded")
                        return
                    
                    # Verificar autenticación
                    if not self.connector._check_auth(self.headers):
                        self.send_response(401)
                        self.end_headers()
                        self.wfile.write(b"Unauthorized")
                        return
                    
                    # Leer cuerpo de la solicitud
                    content_length = int(self.headers.get('Content-Length', 0))
                    if content_length > self.connector.http_config.max_content_length:
                        self.send_response(413)
                        self.end_headers()
                        self.wfile.write(b"Content too large")
                        return
                    
                    body = self.rfile.read(content_length)
                    
                    # Parsear cuerpo según Content-Type
                    content_type = self.headers.get('Content-Type', 'application/json')
                    parsed_body = self.connector._parse_http_body(body, {'Content-Type': content_type})
                    
                    # Crear datos de la solicitud
                    request_data = {
                        'method': 'POST',
                        'path': self.path,
                        'query_params': {},
                        'headers': dict(self.headers),
                        'body': parsed_body,
                        'client_ip': self.client_address[0]
                    }
                    
                    # Procesar datos
                    self.connector._process_http_request(request_data)
                    
                    # Respuesta exitosa
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    if self.connector.http_config.cors_enabled:
                        self._send_cors_headers()
                    self.end_headers()
                    
                    response = {
                        'status': 'success',
                        'message': 'Data ingested successfully',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    self.wfile.write(json.dumps(response).encode())
                    
                except Exception as e:
                    self.connector.logger.error(f"Error procesando POST: {e}")
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b"Internal server error")
            
            def _send_cors_headers(self):
                """Envía headers CORS"""
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Device-ID, X-Project-ID')
        
        # Asignar el conector al servidor para que el handler pueda acceder
        IoTRequestHandler.server.connector = self
        
        return IoTRequestHandler
    
    def _process_http_request(self, request_data: Dict[str, Any]):
        """Procesa una solicitud HTTP recibida"""
        try:
            # Crear datos unificados
            unified_data = self._parse_raw_data(request_data)
            
            if unified_data:
                # Enviar al callback del conector base
                if self.data_callback:
                    self.data_callback(unified_data)
                
                self.logger.debug(f"📨 Solicitud HTTP procesada: {request_data['method']} {request_data['path']}")
            else:
                self.logger.warning(f"No se pudo parsear solicitud HTTP: {request_data['method']} {request_data['path']}")
                
        except Exception as e:
            self.logger.error(f"Error procesando solicitud HTTP: {e}")
    
    def _check_rate_limit(self) -> bool:
        """Verifica si la solicitud está dentro del límite de tasa"""
        if not self.http_config.rate_limit_enabled:
            return True
        
        with self.rate_limit_lock:
            now = time.time()
            
            # Remover timestamps antiguos
            self.request_timestamps = [
                ts for ts in self.request_timestamps 
                if now - ts < self.http_config.rate_limit_window
            ]
            
            # Verificar límite
            if len(self.request_timestamps) >= self.http_config.rate_limit_requests:
                return False
            
            # Agregar timestamp actual
            self.request_timestamps.append(now)
            return True
    
    def _check_auth(self, headers: Dict[str, str]) -> bool:
        """Verifica la autenticación de la solicitud"""
        if not self.http_config.auth_enabled:
            return True
        
        if not self.http_config.auth_token:
            return True
        
        auth_header = headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            return token == self.http_config.auth_token
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del conector HTTP"""
        status = super().get_status()
        status.update({
            'host': self.http_config.host,
            'port': self.http_config.port,
            'endpoint': self.http_config.endpoint,
            'ssl_enabled': self.http_config.ssl_enabled,
            'server_running': self.is_connected(),
            'rate_limit_enabled': self.http_config.rate_limit_enabled,
            'auth_enabled': self.http_config.auth_enabled
        })
        return status
