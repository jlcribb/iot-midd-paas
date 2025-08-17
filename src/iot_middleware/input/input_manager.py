"""
Gestor Principal de Entrada - IoT Middleware
============================================

Coordina todos los conectores de protocolos y proporciona una interfaz unificada
para el procesamiento de datos desde múltiples fuentes.
"""

import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from queue import Queue, Full

from .base_connector import BaseConnector, UnifiedDataFormat, ConnectorStatus
from .connector_factory import ConnectorFactory


@dataclass
class InputManagerConfig:
    """Configuración del gestor de entrada"""
    enabled: bool = True
    name: str = "input_manager"
    max_connectors: int = 50
    health_check_interval: float = 30.0
    metrics_interval: float = 60.0
    data_buffer_size: int = 10000
    enable_data_logging: bool = False
    enable_protocol_logging: bool = True
    auto_start_connectors: bool = True
    graceful_shutdown_timeout: float = 30.0


class InputManager:
    """
    Gestor principal que coordina todos los conectores de entrada
    
    Esta clase actúa como punto central para:
    - Crear y gestionar conectores de diferentes protocolos
    - Coordinar el flujo de datos desde múltiples fuentes
    - Proporcionar métricas y estado unificados
    - Manejar el ciclo de vida de los conectores
    """
    
    def __init__(self, configs: List[Dict[str, Any]], data_callback: Optional[Callable[[UnifiedDataFormat], None]] = None, 
                 manager_config: Optional[InputManagerConfig] = None):
        self.configs = configs
        self.data_callback = data_callback
        self.manager_config = manager_config or InputManagerConfig()
        
        # Estado del gestor
        self.running = False
        self.initialized = False
        
        # Conectores activos
        self.connectors: Dict[str, BaseConnector] = {}
        self.connector_status: Dict[str, Dict[str, Any]] = {}
        
        # Buffer de datos unificado
        self.data_buffer = Queue(maxsize=self.manager_config.data_buffer_size)
        
        # Control de threads
        self.stop_event = threading.Event()
        self.health_check_thread: Optional[threading.Thread] = None
        self.metrics_thread: Optional[threading.Thread] = None
        self.data_processor_thread: Optional[threading.Thread] = None
        
        # Métricas del gestor
        self.metrics = {
            'total_messages': 0,
            'total_bytes': 0,
            'connectors_active': 0,
            'connectors_error': 0,
            'data_buffer_usage': 0.0,
            'start_time': datetime.now(timezone.utc),
            'last_activity': None
        }
        
        # Logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Callback interno para datos de conectores
        self._connector_data_callback = self._on_connector_data
        
        # Inicializar si se solicita
        if self.manager_config.auto_start_connectors:
            self.initialize()
    
    def initialize(self) -> bool:
        """
        Inicializa el gestor de entrada
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            self.logger.info("🚀 Inicializando gestor de entrada...")
            
            # Validar configuraciones
            valid_configs = []
            for config in self.configs:
                validation = ConnectorFactory.validate_config(config)
                if validation['valid']:
                    valid_configs.append(config)
                    if validation['warnings']:
                        self.logger.warning(f"Advertencias en configuración {config.get('name', 'unnamed')}: {validation['warnings']}")
                else:
                    self.logger.error(f"Configuración inválida {config.get('name', 'unnamed')}: {validation['errors']}")
            
            if not valid_configs:
                self.logger.error("❌ No hay configuraciones válidas para inicializar")
                return False
            
            # Crear conectores
            self.connectors = ConnectorFactory.create_connectors_from_config(
                valid_configs, 
                self._connector_data_callback
            )
            
            if not self.connectors:
                self.logger.error("❌ No se pudieron crear conectores")
                return False
            
            # Inicializar estado de conectores
            for name, connector in self.connectors.items():
                self.connector_status[name] = {
                    'status': connector.status.value,
                    'connected': connector.connected,
                    'last_update': datetime.now(timezone.utc)
                }
            
            self.logger.info(f"✅ Gestor de entrada inicializado con {len(self.connectors)} conectores")
            self.initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando gestor de entrada: {e}")
            return False
    
    def start(self) -> bool:
        """
        Inicia el gestor de entrada y todos los conectores
        
        Returns:
            bool: True si el inicio fue exitoso
        """
        try:
            if not self.initialized:
                if not self.initialize():
                    return False
            
            self.logger.info("🔌 Iniciando gestor de entrada...")
            
            # Iniciar conectores
            started_connectors = 0
            for name, connector in self.connectors.items():
                try:
                    if connector.start():
                        started_connectors += 1
                        self.logger.info(f"✅ Conector {name} iniciado")
                    else:
                        self.logger.error(f"❌ No se pudo iniciar conector {name}")
                except Exception as e:
                    self.logger.error(f"❌ Error iniciando conector {name}: {e}")
            
            if started_connectors == 0:
                self.logger.error("❌ No se pudo iniciar ningún conector")
                return False
            
            # Iniciar threads de gestión
            self._start_management_threads()
            
            self.running = True
            self.logger.info(f"🎯 Gestor de entrada iniciado con {started_connectors} conectores activos")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando gestor de entrada: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Detiene el gestor de entrada y todos los conectores
        
        Returns:
            bool: True si la detención fue exitosa
        """
        try:
            self.logger.info("🛑 Deteniendo gestor de entrada...")
            
            # Señalar parada
            self.stop_event.set()
            
            # Detener threads de gestión
            self._stop_management_threads()
            
            # Detener conectores
            stopped_connectors = 0
            for name, connector in self.connectors.items():
                try:
                    if connector.stop():
                        stopped_connectors += 1
                        self.logger.info(f"✅ Conector {name} detenido")
                    else:
                        self.logger.warning(f"⚠️  No se pudo detener conector {name} correctamente")
                except Exception as e:
                    self.logger.error(f"❌ Error deteniendo conector {name}: {e}")
            
            self.running = False
            self.logger.info(f"✅ Gestor de entrada detenido. {stopped_connectors} conectores detenidos")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error deteniendo gestor de entrada: {e}")
            return False
    
    def _start_management_threads(self):
        """Inicia los threads de gestión del gestor"""
        # Thread de verificación de salud
        self.health_check_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True,
            name="InputManager_HealthCheck"
        )
        self.health_check_thread.start()
        
        # Thread de métricas
        self.metrics_thread = threading.Thread(
            target=self._metrics_loop,
            daemon=True,
            name="InputManager_Metrics"
        )
        self.metrics_thread.start()
        
        # Thread de procesamiento de datos
        self.data_processor_thread = threading.Thread(
            target=self._data_processor_loop,
            daemon=True,
            name="InputManager_DataProcessor"
        )
        self.data_processor_thread.start()
        
        self.logger.info("✅ Threads de gestión iniciados")
    
    def _stop_management_threads(self):
        """Detiene los threads de gestión del gestor"""
        # Esperar a que los threads terminen
        threads = [
            self.health_check_thread,
            self.metrics_thread,
            self.data_processor_thread
        ]
        
        for thread in threads:
            if thread and thread.is_alive():
                thread.join(timeout=self.manager_config.graceful_shutdown_timeout)
        
        self.logger.info("✅ Threads de gestión detenidos")
    
    def _health_check_loop(self):
        """Loop de verificación de salud de conectores"""
        self.logger.info("🔄 Iniciando loop de verificación de salud")
        
        while not self.stop_event.is_set():
            try:
                self._check_connectors_health()
                time.sleep(self.manager_config.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error en loop de verificación de salud: {e}")
                time.sleep(5)
        
        self.logger.info("🛑 Loop de verificación de salud detenido")
    
    def _metrics_loop(self):
        """Loop de recolección de métricas"""
        self.logger.info("📊 Iniciando loop de métricas")
        
        while not self.stop_event.is_set():
            try:
                self._update_metrics()
                time.sleep(self.manager_config.metrics_interval)
                
            except Exception as e:
                self.logger.error(f"Error en loop de métricas: {e}")
                time.sleep(10)
        
        self.logger.info("🛑 Loop de métricas detenido")
    
    def _data_processor_loop(self):
        """Loop de procesamiento de datos del buffer"""
        self.logger.info("🔄 Iniciando loop de procesamiento de datos")
        
        while not self.stop_event.is_set():
            try:
                # Procesar datos del buffer
                if not self.data_buffer.empty():
                    data = self.data_buffer.get_nowait()
                    self._process_unified_data(data)
                    self.data_buffer.task_done()
                
                time.sleep(0.01)  # Pequeña pausa para no saturar CPU
                
            except Exception as e:
                self.logger.error(f"Error en loop de procesamiento de datos: {e}")
                time.sleep(1)
        
        self.logger.info("🛑 Loop de procesamiento de datos detenido")
    
    def _check_connectors_health(self):
        """Verifica la salud de todos los conectores"""
        try:
            active_connectors = 0
            error_connectors = 0
            
            for name, connector in self.connectors.items():
                try:
                    # Obtener estado actual
                    status = connector.get_status()
                    health = connector.get_health()
                    
                    # Actualizar estado local
                    self.connector_status[name] = {
                        'status': status['status'],
                        'connected': status['connected'],
                        'last_update': datetime.now(timezone.utc),
                        'health': health
                    }
                    
                    # Contar conectores por estado
                    if health['healthy']:
                        active_connectors += 1
                    else:
                        error_connectors += 1
                    
                    # Log de problemas
                    if not health['healthy']:
                        self.logger.warning(f"⚠️  Conector {name} no está saludable: {health}")
                    
                except Exception as e:
                    self.logger.error(f"Error verificando salud de conector {name}: {e}")
                    error_connectors += 1
            
            # Actualizar métricas
            self.metrics['connectors_active'] = active_connectors
            self.metrics['connectors_error'] = error_connectors
            
        except Exception as e:
            self.logger.error(f"Error en verificación de salud: {e}")
    
    def _update_metrics(self):
        """Actualiza las métricas del gestor"""
        try:
            # Calcular uso del buffer
            buffer_size = self.data_buffer.qsize()
            max_buffer = self.manager_config.data_buffer_size
            self.metrics['data_buffer_usage'] = buffer_size / max_buffer if max_buffer > 0 else 0
            
            # Log de métricas
            self.logger.info(f"📊 Métricas del gestor: "
                           f"Conectores activos={self.metrics['connectors_active']}, "
                           f"Conectores con error={self.metrics['connectors_error']}, "
                           f"Buffer={buffer_size}/{max_buffer} ({self.metrics['data_buffer_usage']:.1%}), "
                           f"Mensajes totales={self.metrics['total_messages']}")
            
        except Exception as e:
            self.logger.error(f"Error actualizando métricas: {e}")
    
    def _on_connector_data(self, data: UnifiedDataFormat):
        """Callback para datos recibidos de conectores"""
        try:
            # Agregar al buffer de datos
            try:
                self.data_buffer.put_nowait(data)
                
                # Actualizar métricas
                self.metrics['total_messages'] += 1
                self.metrics['total_bytes'] += len(data.to_json())
                self.metrics['last_activity'] = datetime.now(timezone.utc)
                
                if self.manager_config.enable_data_logging:
                    self.logger.debug(f"📨 Datos recibidos de {data.source_protocol}: {data.device_id}")
                    
            except Full:
                self.logger.warning("Buffer de datos lleno, mensaje descartado")
                
        except Exception as e:
            self.logger.error(f"Error procesando datos del conector: {e}")
    
    def _process_unified_data(self, data: UnifiedDataFormat):
        """Procesa datos unificados del buffer"""
        try:
            # Enviar al callback principal si existe
            if self.data_callback:
                self.data_callback(data)
            
            if self.manager_config.enable_data_logging:
                self.logger.debug(f"🔄 Procesando datos: {data.device_id} -> {data.measurements}")
                
        except Exception as e:
            self.logger.error(f"Error en callback de datos: {e}")
    
    def get_connector_status(self, connector_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado de un conector específico
        
        Args:
            connector_name: Nombre del conector
            
        Returns:
            Estado del conector o None si no existe
        """
        if connector_name in self.connector_status:
            return self.connector_status[connector_name].copy()
        return None
    
    def get_all_connectors_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene el estado de todos los conectores
        
        Returns:
            Diccionario con el estado de todos los conectores
        """
        return self.connector_status.copy()
    
    def get_manager_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado general del gestor
        
        Returns:
            Estado completo del gestor
        """
        return {
            'name': self.manager_config.name,
            'running': self.running,
            'initialized': self.initialized,
            'total_connectors': len(self.connectors),
            'active_connectors': self.metrics['connectors_active'],
            'error_connectors': self.metrics['connectors_error'],
            'data_buffer_usage': self.metrics['data_buffer_usage'],
            'total_messages': self.metrics['total_messages'],
            'total_bytes': self.metrics['total_bytes'],
            'uptime_seconds': int((datetime.now(timezone.utc) - self.metrics['start_time']).total_seconds()),
            'last_activity': self.metrics['last_activity'].isoformat() if self.metrics['last_activity'] else None,
            'config': {
                'enabled': self.manager_config.enabled,
                'max_connectors': self.manager_config.max_connectors,
                'health_check_interval': self.manager_config.health_check_interval,
                'metrics_interval': self.manager_config.metrics_interval
            }
        }
    
    def restart_connector(self, connector_name: str) -> bool:
        """
        Reinicia un conector específico
        
        Args:
            connector_name: Nombre del conector a reiniciar
            
        Returns:
            bool: True si el reinicio fue exitoso
        """
        try:
            if connector_name not in self.connectors:
                self.logger.error(f"Conector {connector_name} no encontrado")
                return False
            
            connector = self.connectors[connector_name]
            self.logger.info(f"🔄 Reiniciando conector {connector_name}")
            
            # Detener conector
            if not connector.stop():
                self.logger.warning(f"No se pudo detener conector {connector_name} correctamente")
            
            # Esperar un momento
            time.sleep(2)
            
            # Reiniciar conector
            if connector.start():
                self.logger.info(f"✅ Conector {connector_name} reiniciado exitosamente")
                return True
            else:
                self.logger.error(f"❌ No se pudo reiniciar conector {connector_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error reiniciando conector {connector_name}: {e}")
            return False
    
    def add_connector(self, config: Dict[str, Any]) -> bool:
        """
        Agrega un nuevo conector dinámicamente
        
        Args:
            config: Configuración del nuevo conector
            
        Returns:
            bool: True si se agregó exitosamente
        """
        try:
            # Validar configuración
            validation = ConnectorFactory.validate_config(config)
            if not validation['valid']:
                self.logger.error(f"Configuración inválida para nuevo conector: {validation['errors']}")
                return False
            
            # Verificar límite de conectores
            if len(self.connectors) >= self.manager_config.max_connectors:
                self.logger.error(f"No se pueden agregar más conectores. Límite: {self.manager_config.max_connectors}")
                return False
            
            # Crear conector
            connector = ConnectorFactory.create_connector(config, self._connector_data_callback)
            if not connector:
                self.logger.error("No se pudo crear el nuevo conector")
                return False
            
            # Agregar al gestor
            self.connectors[connector.config.name] = connector
            
            # Inicializar estado
            self.connector_status[connector.config.name] = {
                'status': connector.status.value,
                'connected': connector.connected,
                'last_update': datetime.now(timezone.utc)
            }
            
            # Iniciar si el gestor está corriendo
            if self.running:
                if connector.start():
                    self.logger.info(f"✅ Nuevo conector {connector.config.name} agregado e iniciado")
                else:
                    self.logger.warning(f"⚠️  Nuevo conector {connector.config.name} agregado pero no se pudo iniciar")
            else:
                self.logger.info(f"✅ Nuevo conector {connector.config.name} agregado (gestor no iniciado)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error agregando nuevo conector: {e}")
            return False
    
    def remove_connector(self, connector_name: str) -> bool:
        """
        Remueve un conector del gestor
        
        Args:
            connector_name: Nombre del conector a remover
            
        Returns:
            bool: True si se removió exitosamente
        """
        try:
            if connector_name not in self.connectors:
                self.logger.error(f"Conector {connector_name} no encontrado")
                return False
            
            connector = self.connectors[connector_name]
            self.logger.info(f"🗑️  Removiendo conector {connector_name}")
            
            # Detener conector
            if self.running:
                connector.stop()
            
            # Remover del gestor
            del self.connectors[connector_name]
            del self.connector_status[connector_name]
            
            self.logger.info(f"✅ Conector {connector_name} removido exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removiendo conector {connector_name}: {e}")
            return False
