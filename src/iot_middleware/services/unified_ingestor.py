"""
Servicio Unificado de Ingesta Multiprotocolo - IoT Middleware
===========================================================

Este módulo integra el InputManager (capa multiprotocolo) con el middleware core existente.
Permite que datos de múltiples protocolos (MQTT, HTTP, BLE, LoRa, MIDI, Modbus, ZigBee)
sean procesados por el sistema de ingesta existente sin modificaciones.

Características:
- Integración transparente con MQTTIngestaService existente
- Soporte para todos los protocolos implementados
- Conversión automática de UnifiedDataFormat a formato MQTT
- Mantiene compatibilidad total con el sistema existente
"""

import json
import logging
import time
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from queue import Queue, Full
from contextlib import contextmanager
import signal
import sys

# Importar módulos del proyecto
try:
    from ..input import InputManager, BaseConnector, UnifiedDataFormat
    from ..mqtt.mqtt_client import IoTMQTTClient, MQTTMessage, create_mqtt_client
    from ..storage.db_handler import DatabaseHandler, create_database_handler
    from ..config import load_config, MQTTConfig, StorageConfig
    from ..processing.processor import DataProcessor, create_data_processor
    from ..models.entities import Canal, RegistroDatos, EventoAlarma, Dispositivo, UnidadProyecto
    from ..models.enums import TipoDato, SeveridadEvento, CalidadDato
except ImportError as e:
    logging.error(f"Error al importar módulos: {e}")
    raise

# Configurar logging
logger = logging.getLogger(__name__)


@dataclass
class UnifiedIngestaConfig:
    """Configuración del servicio unificado de ingesta"""
    # Configuración del InputManager
    input_manager: Dict[str, Any] = field(default_factory=lambda: {
        'enabled_protocols': ['mqtt', 'http', 'ble', 'lora', 'midi', 'modbus', 'zigbee'],
        'mqtt_config': {},
        'http_config': {},
        'ble_config': {},
        'lora_config': {},
        'midi_config': {},
        'modbus_config': {},
        'zigbee_config': {}
    })
    
    # Configuración del middleware core
    core_config: Dict[str, Any] = field(default_factory=lambda: {
        'mqtt_broker': 'localhost',
        'mqtt_port': 1883,
        'mqtt_username': None,
        'mqtt_password': None,
        'database_config': {},
        'processing_config': {}
    })
    
    # Configuración de integración
    integration: Dict[str, Any] = field(default_factory=lambda: {
        'enable_protocol_bridge': True,
        'mqtt_topic_prefix': 'iot/unified',
        'auto_create_channels': True,
        'data_validation': True,
        'alarm_thresholds': {},
        'max_queue_size': 1000,
        'batch_size': 100,
        'batch_timeout': 5.0
    })


@dataclass
class UnifiedIngestaMetrics:
    """Métricas del servicio unificado de ingesta"""
    # Métricas del InputManager
    input_messages_received: int = 0
    input_messages_processed: int = 0
    input_messages_failed: int = 0
    
    # Métricas por protocolo
    protocol_metrics: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        'mqtt': {'received': 0, 'processed': 0, 'failed': 0},
        'http': {'received': 0, 'processed': 0, 'failed': 0},
        'ble': {'received': 0, 'processed': 0, 'failed': 0},
        'lora': {'received': 0, 'processed': 0, 'failed': 0},
        'midi': {'received': 0, 'processed': 0, 'failed': 0},
        'modbus': {'received': 0, 'processed': 0, 'failed': 0},
        'zigbee': {'received': 0, 'processed': 0, 'failed': 0}
    })
    
    # Métricas del core
    core_messages_sent: int = 0
    core_messages_processed: int = 0
    core_messages_failed: int = 0
    
    # Métricas generales
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_message_time: Optional[datetime] = None
    uptime_seconds: int = 0


class ProtocolBridge:
    """Puente entre protocolos y el middleware core"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mqtt_client = None
        self.topic_prefix = config.get('mqtt_topic_prefix', 'iot/unified')
        self.auto_create_channels = config.get('auto_create_channels', True)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def initialize(self, mqtt_config: MQTTConfig) -> bool:
        """Inicializa el puente de protocolos"""
        try:
            self.mqtt_client = create_mqtt_client(mqtt_config)
            if not self.mqtt_client.connect():
                self.logger.error("❌ No se pudo conectar al broker MQTT para el puente")
                return False
            
            self.logger.info("✅ Puente de protocolos inicializado")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando puente: {e}")
            return False
    
    def bridge_data(self, unified_data: UnifiedDataFormat) -> bool:
        """
        Convierte datos unificados a formato MQTT y los envía al core
        
        Args:
            unified_data: Datos en formato unificado
            
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        try:
            # Crear tópico MQTT para el core
            topic = self._create_core_topic(unified_data)
            
            # Convertir a formato compatible con el core
            payload = self._convert_to_core_format(unified_data)
            
            # Enviar al broker MQTT
            if self.mqtt_client and self.mqtt_client._connected:
                self.mqtt_client.publish(topic, json.dumps(payload))
                self.logger.debug(f"📤 Datos enviados al core: {topic}")
                return True
            else:
                self.logger.warning("⚠️  Cliente MQTT no conectado")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error en puente de datos: {e}")
            return False
    
    def _create_core_topic(self, unified_data: UnifiedDataFormat) -> str:
        """Crea el tópico MQTT para el core"""
        try:
            # Extraer componentes del device_id y project_id
            device_parts = unified_data.device_id.split('_')
            project_parts = unified_data.project_id.split('_')
            
            # Crear tópico jerárquico
            topic_parts = [
                self.topic_prefix,
                project_parts[0] if project_parts else 'default',
                device_parts[0] if device_parts else 'unknown',
                'data'
            ]
            
            return '/'.join(topic_parts)
            
        except Exception as e:
            self.logger.warning(f"⚠️  Error creando tópico, usando tópico por defecto: {e}")
            return f"{self.topic_prefix}/default/unknown/data"
    
    def _convert_to_core_format(self, unified_data: UnifiedDataFormat) -> Dict[str, Any]:
        """Convierte UnifiedDataFormat a formato compatible con el core"""
        try:
            # Crear payload compatible con el sistema existente
            core_payload = {
                'timestamp': unified_data.timestamp,
                'device_id': unified_data.device_id,
                'project_id': unified_data.project_id,
                'measurements': unified_data.measurements,
                'metadata': {
                    'protocol': unified_data.source_address.split('://')[0] if '://' in unified_data.source_address else 'unknown',
                    'source_address': unified_data.source_address,
                    'data_quality': unified_data.quality.value if hasattr(unified_data.quality, 'value') else 'unknown',
                    'received_at': datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Agregar tags si existen
            if hasattr(unified_data, 'tags') and unified_data.tags:
                core_payload['tags'] = unified_data.tags
            
            return core_payload
            
        except Exception as e:
            self.logger.error(f"❌ Error convirtiendo formato: {e}")
            return {
                'timestamp': unified_data.timestamp,
                'device_id': unified_data.device_id,
                'error': f"Error en conversión: {e}"
            }
    
    def stop(self):
        """Detiene el puente de protocolos"""
        try:
            if self.mqtt_client:
                self.mqtt_client.disconnect()
            self.logger.info("✅ Puente de protocolos detenido")
        except Exception as e:
            self.logger.error(f"❌ Error deteniendo puente: {e}")


class UnifiedIngestaService:
    """Servicio unificado de ingesta multiprotocolo"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = None
        self.input_manager = None
        self.protocol_bridge = None
        
        # Estado del servicio
        self.running = False
        self.metrics = UnifiedIngestaMetrics()
        
        # Señales de control
        self.stop_event = threading.Event()
        
        # Configurar logging
        self._setup_logging()
        
        # Configurar manejo de señales
        self._setup_signal_handlers()
    
    def _setup_logging(self):
        """Configura el logging estructurado"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('unified_ingesta_service.log')
            ]
        )
    
    def _setup_signal_handlers(self):
        """Configura el manejo de señales del sistema"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Manejador de señales del sistema"""
        logger.info(f"Señal {signum} recibida, deteniendo servicio...")
        self.stop()
    
    def initialize(self) -> bool:
        """Inicializa el servicio unificado de ingesta"""
        try:
            logger.info("🚀 Inicializando servicio unificado de ingesta...")
            
            # Cargar configuración
            self.config = load_config(self.config_path)
            logger.info("✅ Configuración cargada")
            
            # Crear InputManager
            self.input_manager = InputManager(self.config.input_manager)
            logger.info("✅ InputManager creado")
            
            # Crear puente de protocolos
            mqtt_config = MQTTConfig(
                broker=self.config.core_config.get('mqtt_broker', 'localhost'),
                port=self.config.core_config.get('mqtt_port', 1883),
                username=self.config.core_config.get('mqtt_username'),
                password=self.config.core_config.get('mqtt_password')
            )
            
            self.protocol_bridge = ProtocolBridge(self.config.integration)
            if not self.protocol_bridge.initialize(mqtt_config):
                logger.error("❌ No se pudo inicializar el puente de protocolos")
                return False
            
            logger.info("✅ Puente de protocolos inicializado")
            
            # Configurar callback para datos unificados
            self.input_manager.set_data_callback(self._on_unified_data)
            
            logger.info("🎯 Servicio unificado de ingesta inicializado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando servicio: {e}")
            return False
    
    def _on_unified_data(self, unified_data: UnifiedDataFormat):
        """Callback para datos unificados del InputManager"""
        try:
            # Actualizar métricas
            self.metrics.input_messages_received += 1
            self.metrics.last_message_time = datetime.now(timezone.utc)
            
            # Extraer protocolo del source_address
            protocol = unified_data.source_address.split('://')[0] if '://' in unified_data.source_address else 'unknown'
            
            # Actualizar métricas del protocolo
            if protocol in self.metrics.protocol_metrics:
                self.metrics.protocol_metrics[protocol]['received'] += 1
            
            # Enviar datos al core a través del puente
            if self.protocol_bridge.bridge_data(unified_data):
                self.metrics.input_messages_processed += 1
                self.metrics.core_messages_sent += 1
                
                if protocol in self.metrics.protocol_metrics:
                    self.metrics.protocol_metrics[protocol]['processed'] += 1
                
                logger.debug(f"📨 Datos procesados de {protocol}: {unified_data.device_id}")
            else:
                self.metrics.input_messages_failed += 1
                self.metrics.core_messages_failed += 1
                
                if protocol in self.metrics.protocol_metrics:
                    self.metrics.protocol_metrics[protocol]['failed'] += 1
                
                logger.warning(f"⚠️  Error procesando datos de {protocol}: {unified_data.device_id}")
            
        except Exception as e:
            logger.error(f"❌ Error en callback de datos unificados: {e}")
            self.metrics.input_messages_failed += 1
    
    def start(self) -> bool:
        """Inicia el servicio unificado de ingesta"""
        try:
            if not self.initialize():
                return False
            
            logger.info("🔌 Iniciando InputManager...")
            
            # Iniciar InputManager
            if not self.input_manager.start():
                logger.error("❌ No se pudo iniciar el InputManager")
                return False
            
            logger.info("✅ InputManager iniciado")
            self.running = True
            
            # Loop principal del servicio
            self._main_loop()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando servicio: {e}")
            return False
    
    def _main_loop(self):
        """Loop principal del servicio"""
        logger.info("🔄 Servicio unificado de ingesta ejecutándose...")
        
        try:
            while self.running and not self.stop_event.is_set():
                # Actualizar métricas
                self._update_metrics()
                
                # Verificar estado del InputManager
                if self.input_manager and not self.input_manager.is_running():
                    logger.warning("⚠️  InputManager no está ejecutándose")
                
                # Esperar antes de la siguiente iteración
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Interrumpido por el usuario")
        except Exception as e:
            logger.error(f"❌ Error en loop principal: {e}")
        finally:
            self._cleanup()
    
    def _update_metrics(self):
        """Actualiza las métricas del servicio"""
        try:
            # Calcular uptime
            now = datetime.now(timezone.utc)
            self.metrics.uptime_seconds = int((now - self.metrics.start_time).total_seconds())
            
            # Log de métricas cada 60 segundos
            if self.metrics.uptime_seconds % 60 == 0:
                logger.info(f"📊 Métricas Unificadas: "
                          f"Input={self.metrics.input_messages_received}/{self.metrics.input_messages_processed}/{self.metrics.input_messages_failed}, "
                          f"Core={self.metrics.core_messages_sent}/{self.metrics.core_messages_processed}/{self.metrics.core_messages_failed}, "
                          f"Uptime={self.metrics.uptime_seconds}s")
                
        except Exception as e:
            logger.error(f"Error actualizando métricas: {e}")
    
    def _cleanup(self):
        """Limpia recursos del servicio"""
        try:
            logger.info("🧹 Limpiando recursos del servicio...")
            
            # Detener InputManager
            if self.input_manager:
                self.input_manager.stop()
            
            # Detener puente de protocolos
            if self.protocol_bridge:
                self.protocol_bridge.stop()
            
            logger.info("✅ Recursos limpiados")
            
        except Exception as e:
            logger.error(f"Error limpiando recursos: {e}")
    
    def stop(self):
        """Detiene el servicio unificado de ingesta"""
        if not self.running:
            return
        
        logger.info("🛑 Deteniendo servicio unificado de ingesta...")
        self.running = False
        self.stop_event.set()
        self._cleanup()
        logger.info("✅ Servicio unificado de ingesta detenido")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del servicio"""
        try:
            status = {
                'service': {
                    'running': self.running,
                    'uptime_seconds': self.metrics.uptime_seconds,
                    'start_time': self.metrics.start_time.isoformat()
                },
                'input_manager': {
                    'running': self.input_manager.is_running() if self.input_manager else False,
                    'protocols': self.input_manager.get_enabled_protocols() if self.input_manager else []
                },
                'protocol_bridge': {
                    'connected': self.protocol_bridge.mqtt_client._connected if self.protocol_bridge and self.protocol_bridge.mqtt_client else False
                },
                'metrics': {
                    'input_received': self.metrics.input_messages_received,
                    'input_processed': self.metrics.input_messages_processed,
                    'input_failed': self.metrics.input_messages_failed,
                    'core_sent': self.metrics.core_messages_sent,
                    'core_processed': self.metrics.core_messages_processed,
                    'core_failed': self.metrics.core_messages_failed
                }
            }
            
            # Agregar métricas por protocolo
            status['protocol_metrics'] = self.metrics.protocol_metrics
            
            return status
            
        except Exception as e:
            logger.error(f"Error obteniendo estado: {e}")
            return {'error': str(e)}


def create_unified_ingesta_service(config_path: Optional[str] = None) -> UnifiedIngestaService:
    """Factory function para crear el servicio unificado de ingesta"""
    return UnifiedIngestaService(config_path)


def main():
    """Función principal para ejecutar el servicio como script independiente"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Servicio Unificado de Ingesta Multiprotocolo')
    parser.add_argument('--config', '-c', help='Ruta al archivo de configuración')
    parser.add_argument('--status', '-s', action='store_true', help='Mostrar estado del servicio')
    
    args = parser.parse_args()
    
    # Crear servicio
    service = create_unified_ingesta_service(args.config)
    
    if args.status:
        # Solo mostrar estado
        status = service.get_status()
        print(json.dumps(status, indent=2, default=str))
        return
    
    try:
        # Iniciar servicio
        if service.start():
            logger.info("🎉 Servicio unificado de ingesta iniciado exitosamente")
        else:
            logger.error("❌ Error iniciando servicio unificado de ingesta")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Servicio interrumpido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error en servicio: {e}")
        sys.exit(1)
    finally:
        service.stop()


if __name__ == "__main__":
    main()
