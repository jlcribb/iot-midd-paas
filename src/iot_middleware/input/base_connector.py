"""
Clase Base para Conectores de Protocolos - IoT Middleware
========================================================

Define la interfaz común que deben implementar todos los conectores
para mantener la compatibilidad con el core del sistema.
"""

import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum
from queue import Queue, Full


class ConnectorStatus(Enum):
    """Estados posibles de un conector"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class DataQuality(Enum):
    """Calidad de los datos recibidos"""
    VALID = "valid"
    INVALID = "invalid"
    OUT_OF_RANGE = "out_of_range"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class UnifiedDataFormat:
    """Formato unificado para todos los datos entrantes"""
    device_id: str
    project_id: str
    timestamp: datetime
    measurements: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality: DataQuality = DataQuality.VALID
    source_protocol: str = ""
    source_address: str = ""
    raw_data: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización"""
        return {
            'device_id': self.device_id,
            'project_id': self.project_id,
            'timestamp': self.timestamp.isoformat(),
            'measurements': self.measurements,
            'metadata': self.metadata,
            'quality': self.quality.value,
            'source_protocol': self.source_protocol,
            'source_address': self.source_address,
            'raw_data': str(self.raw_data) if self.raw_data is not None else None
        }
    
    def to_json(self) -> str:
        """Convierte a JSON string"""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class ConnectorConfig:
    """Configuración base para conectores"""
    enabled: bool = True
    name: str = ""
    protocol: str = ""
    auto_reconnect: bool = True
    reconnect_interval: float = 5.0
    max_reconnect_attempts: int = 10
    timeout: float = 30.0
    retry_on_error: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    buffer_size: int = 1000
    batch_size: int = 100
    batch_timeout: float = 5.0


class BaseConnector(ABC):
    """
    Clase base abstracta para todos los conectores de protocolos
    
    Esta clase define la interfaz común que deben implementar todos los conectores
    para mantener la compatibilidad con el core del sistema de procesamiento.
    """
    
    def __init__(self, config: ConnectorConfig, data_callback: Optional[Callable[[UnifiedDataFormat], None]] = None):
        self.config = config
        self.data_callback = data_callback
        
        # Estado del conector
        self.status = ConnectorStatus.DISCONNECTED
        self.connected = False
        self.error_count = 0
        self.reconnect_attempts = 0
        self.last_connection_time: Optional[datetime] = None
        self.last_data_time: Optional[datetime] = None
        
        # Control de reconexión
        self.reconnect_timer: Optional[threading.Timer] = None
        self.stop_event = threading.Event()
        
        # Buffer de datos
        self.data_buffer = Queue(maxsize=config.buffer_size)
        self.batch_timer: Optional[threading.Timer] = None
        
        # Workers de procesamiento
        self.processing_thread: Optional[threading.Thread] = None
        
        # Logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Métricas
        self.metrics = {
            'messages_received': 0,
            'messages_processed': 0,
            'messages_failed': 0,
            'bytes_received': 0,
            'connection_attempts': 0,
            'reconnection_attempts': 0,
            'start_time': datetime.now(timezone.utc)
        }
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establece la conexión con el protocolo específico
        
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Cierra la conexión con el protocolo específico
        
        Returns:
            bool: True si la desconexión fue exitosa, False en caso contrario
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Verifica si el conector está conectado
        
        Returns:
            bool: True si está conectado, False en caso contrario
        """
        pass
    
    @abstractmethod
    def _receive_data(self) -> Optional[Any]:
        """
        Recibe datos del protocolo específico
        
        Returns:
            Any: Datos recibidos o None si no hay datos disponibles
        """
        pass
    
    @abstractmethod
    def _parse_raw_data(self, raw_data: Any) -> Optional[UnifiedDataFormat]:
        """
        Parsea los datos crudos del protocolo al formato unificado
        
        Args:
            raw_data: Datos crudos del protocolo
            
        Returns:
            UnifiedDataFormat: Datos en formato unificado o None si el parsing falla
        """
        pass
    
    def start(self) -> bool:
        """
        Inicia el conector
        
        Returns:
            bool: True si el inicio fue exitoso, False en caso contrario
        """
        try:
            self.logger.info(f"🚀 Iniciando conector {self.config.name} ({self.config.protocol})")
            
            # Conectar al protocolo
            if not self.connect():
                self.logger.error(f"❌ No se pudo conectar al protocolo {self.config.protocol}")
                return False
            
            # Iniciar thread de procesamiento
            self.processing_thread = threading.Thread(
                target=self._processing_loop,
                daemon=True,
                name=f"{self.config.name}_Processor"
            )
            self.processing_thread.start()
            
            # Iniciar timer de lotes
            self._start_batch_timer()
            
            self.logger.info(f"✅ Conector {self.config.name} iniciado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando conector {self.config.name}: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Detiene el conector
        
        Returns:
            bool: True si la detención fue exitosa, False en caso contrario
        """
        try:
            self.logger.info(f"🛑 Deteniendo conector {self.config.name}")
            
            # Señalar parada
            self.stop_event.set()
            
            # Detener timer de lotes
            if self.batch_timer:
                self.batch_timer.cancel()
            
            # Desconectar del protocolo
            if self.connected:
                self.disconnect()
            
            # Esperar a que termine el thread de procesamiento
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5.0)
            
            self.logger.info(f"✅ Conector {self.config.name} detenido")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error deteniendo conector {self.config.name}: {e}")
            return False
    
    def _processing_loop(self):
        """Loop principal de procesamiento de datos"""
        self.logger.info(f"🔄 Iniciando loop de procesamiento para {self.config.name}")
        
        while not self.stop_event.is_set():
            try:
                # Recibir datos del protocolo
                raw_data = self._receive_data()
                
                if raw_data is not None:
                    # Actualizar métricas
                    self.metrics['messages_received'] += 1
                    self.metrics['bytes_received'] += len(str(raw_data))
                    self.metrics['last_data_time'] = datetime.now(timezone.utc)
                    
                    # Parsear datos al formato unificado
                    unified_data = self._parse_raw_data(raw_data)
                    
                    if unified_data:
                        # Agregar al buffer
                        try:
                            self.data_buffer.put_nowait(unified_data)
                            self.metrics['messages_processed'] += 1
                        except Full:
                            self.logger.warning(f"Buffer lleno en {self.config.name}, descartando mensaje")
                            self.metrics['messages_failed'] += 1
                    else:
                        self.logger.warning(f"No se pudo parsear datos en {self.config.name}")
                        self.metrics['messages_failed'] += 1
                
                # Pequeña pausa para no saturar CPU
                time.sleep(0.01)
                
            except Exception as e:
                self.logger.error(f"Error en loop de procesamiento de {self.config.name}: {e}")
                self.metrics['messages_failed'] += 1
                time.sleep(1)
        
        self.logger.info(f"🛑 Loop de procesamiento de {self.config.name} detenido")
    
    def _start_batch_timer(self):
        """Inicia el timer para procesar lotes de datos"""
        if self.batch_timer:
            self.batch_timer.cancel()
        
        self.batch_timer = threading.Timer(
            self.config.batch_timeout,
            self._process_batch
        )
        self.batch_timer.start()
    
    def _process_batch(self):
        """Procesa un lote de datos del buffer"""
        try:
            if self.data_buffer.empty():
                return
            
            # Recolectar datos del lote
            batch_data = []
            while len(batch_data) < self.config.batch_size and not self.data_buffer.empty():
                try:
                    data = self.data_buffer.get_nowait()
                    batch_data.append(data)
                except:
                    break
            
            if batch_data:
                # Enviar datos al callback
                if self.data_callback:
                    for data in batch_data:
                        try:
                            self.data_callback(data)
                        except Exception as e:
                            self.logger.error(f"Error en callback de datos: {e}")
                            self.metrics['messages_failed'] += 1
                
                self.logger.debug(f"Procesado lote de {len(batch_data)} mensajes en {self.config.name}")
            
        except Exception as e:
            self.logger.error(f"Error procesando lote en {self.config.name}: {e}")
        finally:
            # Reiniciar timer para el siguiente lote
            if not self.stop_event.is_set():
                self._start_batch_timer()
    
    def _handle_connection_error(self, error: Exception):
        """Maneja errores de conexión"""
        self.logger.error(f"Error de conexión en {self.config.name}: {error}")
        self.status = ConnectorStatus.ERROR
        self.connected = False
        self.error_count += 1
        
        # Intentar reconexión si está habilitada
        if self.config.auto_reconnect and self.reconnect_attempts < self.config.max_reconnect_attempts:
            self._schedule_reconnect()
    
    def _schedule_reconnect(self):
        """Programa un intento de reconexión"""
        if self.reconnect_timer:
            self.reconnect_timer.cancel()
        
        self.reconnect_attempts += 1
        self.status = ConnectorStatus.RECONNECTING
        
        self.logger.info(f"Programando reconexión #{self.reconnect_attempts} en {self.config.reconnect_interval}s")
        
        self.reconnect_timer = threading.Timer(
            self.config.reconnect_interval,
            self._attempt_reconnect
        )
        self.reconnect_timer.start()
    
    def _attempt_reconnect(self):
        """Intenta reconectar"""
        try:
            self.logger.info(f"Intentando reconexión #{self.reconnect_attempts}")
            self.metrics['reconnection_attempts'] += 1
            
            if self.connect():
                self.logger.info(f"✅ Reconexión exitosa en {self.config.name}")
                self.status = ConnectorStatus.CONNECTED
                self.connected = True
                self.reconnect_attempts = 0
                self.error_count = 0
            else:
                self.logger.warning(f"❌ Reconexión fallida en {self.config.name}")
                if self.reconnect_attempts < self.config.max_reconnect_attempts:
                    self._schedule_reconnect()
                else:
                    self.logger.error(f"Se alcanzó el máximo de intentos de reconexión en {self.config.name}")
                    self.status = ConnectorStatus.ERROR
                    
        except Exception as e:
            self.logger.error(f"Error en intento de reconexión: {e}")
            if self.reconnect_attempts < self.config.max_reconnect_attempts:
                self._schedule_reconnect()
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del conector"""
        return {
            'name': self.config.name,
            'protocol': self.config.protocol,
            'status': self.status.value,
            'connected': self.connected,
            'error_count': self.error_count,
            'reconnect_attempts': self.reconnect_attempts,
            'last_connection_time': self.last_connection_time.isoformat() if self.last_connection_time else None,
            'last_data_time': self.last_data_time.isoformat() if self.last_data_time else None,
            'metrics': self.metrics.copy(),
            'buffer_size': self.data_buffer.qsize(),
            'config': {
                'enabled': self.config.enabled,
                'auto_reconnect': self.config.auto_reconnect,
                'timeout': self.config.timeout
            }
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Obtiene el estado de salud del conector"""
        now = datetime.now(timezone.utc)
        uptime = (now - self.metrics['start_time']).total_seconds()
        
        return {
            'healthy': self.connected and self.status == ConnectorStatus.CONNECTED,
            'uptime_seconds': int(uptime),
            'error_rate': self.error_count / max(1, self.metrics['messages_received']),
            'reconnection_rate': self.reconnect_attempts / max(1, uptime / 3600),  # por hora
            'buffer_usage': self.data_buffer.qsize() / self.config.buffer_size,
            'last_activity': self.metrics.get('last_data_time', 0)
        }
