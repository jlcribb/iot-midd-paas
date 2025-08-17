"""
Conector MQTT - IoT Middleware
==============================

Extiende la implementación MQTT existente para integrarse con la nueva
arquitectura modular de entrada de datos.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..base_connector import BaseConnector, ConnectorConfig, UnifiedDataFormat, DataQuality, ConnectorStatus

# Importar la implementación MQTT existente
try:
    from ...mqtt.mqtt_client import IoTMQTTClient, MQTTMessage, create_mqtt_client
    from ...config import MQTTConfig
except ImportError as e:
    logging.error(f"No se pudo importar módulos MQTT existentes: {e}")
    # Fallback para desarrollo
    IoTMQTTClient = None
    MQTTMessage = None
    create_mqtt_client = None
    MQTTConfig = None


@dataclass
class MQTTConnectorConfig(ConnectorConfig):
    """Configuración específica para el conector MQTT"""
    broker_host: str = "localhost"
    broker_port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    topics_subscribe: List[str] = None
    topics_publish: List[str] = None
    qos: int = 1
    retain: bool = False
    clean_session: bool = True
    keepalive: int = 60
    ssl_enabled: bool = False
    ssl_ca_certs: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    topic_mapping: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.topics_subscribe is None:
            self.topics_subscribe = ["iot/+/+/+/+"]
        if self.topics_publish is None:
            self.topics_publish = []
        if self.topic_mapping is None:
            self.topic_mapping = {}


class MQTTConnector(BaseConnector):
    """
    Conector MQTT que extiende la implementación existente
    
    Este conector se integra con tu sistema MQTT actual y proporciona
    una interfaz unificada para el procesamiento de datos.
    """
    
    def __init__(self, config: MQTTConnectorConfig, data_callback=None):
        super().__init__(config, data_callback)
        
        # Configuración específica de MQTT
        self.mqtt_config = MQTTConnectorConfig(**config.__dict__) if isinstance(config, ConnectorConfig) else config
        
        # Cliente MQTT
        self.mqtt_client: Optional[IoTMQTTClient] = None
        
        # Estado de suscripciones
        self.subscribed_topics: List[str] = []
        
        # Mapeo de tópicos
        self.topic_mapper = TopicMapper(self.mqtt_config.topic_mapping)
        
        # Logging específico
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def connect(self) -> bool:
        """Establece conexión con el broker MQTT"""
        try:
            self.logger.info(f"🔌 Conectando a broker MQTT {self.mqtt_config.broker_host}:{self.mqtt_config.broker_port}")
            
            # Crear configuración MQTT compatible con tu sistema existente
            mqtt_config_dict = {
                'broker': {
                    'host': self.mqtt_config.broker_host,
                    'port': self.mqtt_config.broker_port,
                    'username': self.mqtt_config.username,
                    'password': self.mqtt_config.password,
                    'client_id': self.mqtt_config.client_id or f"{self.config.name}_{int(time.time())}",
                    'keepalive': self.mqtt_config.keepalive,
                    'clean_session': self.mqtt_config.clean_session
                },
                'topics': {
                    'subscribe': self.mqtt_config.topics_subscribe,
                    'publish': self.mqtt_config.topics_publish
                },
                'qos': self.mqtt_config.qos,
                'retain': self.mqtt_config.retain
            }
            
            # Configuración SSL si está habilitada
            if self.mqtt_config.ssl_enabled:
                mqtt_config_dict['broker'].update({
                    'ssl_enabled': True,
                    'ssl_ca_certs': self.mqtt_config.ssl_ca_certs,
                    'ssl_certfile': self.mqtt_config.ssl_certfile,
                    'ssl_keyfile': self.mqtt_config.ssl_keyfile
                })
            
            # Crear cliente MQTT usando tu implementación existente
            if create_mqtt_client:
                self.mqtt_client = create_mqtt_client(mqtt_config_dict)
                self.mqtt_client.set_message_processor(self._on_mqtt_message)
            else:
                # Fallback para desarrollo
                self.logger.warning("Usando cliente MQTT de desarrollo")
                self.mqtt_client = self._create_development_mqtt_client(mqtt_config_dict)
            
            # Conectar al broker
            if self.mqtt_client.connect():
                self.status = ConnectorStatus.CONNECTED
                self.connected = True
                self.last_connection_time = datetime.now(timezone.utc)
                
                # Suscribirse a tópicos
                self._subscribe_to_topics()
                
                self.logger.info(f"✅ Conectado al broker MQTT {self.mqtt_config.broker_host}:{self.mqtt_config.broker_port}")
                return True
            else:
                self.logger.error(f"❌ No se pudo conectar al broker MQTT")
                self.status = ConnectorStatus.ERROR
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error conectando a MQTT: {e}")
            self.status = ConnectorStatus.ERROR
            self._handle_connection_error(e)
            return False
    
    def disconnect(self) -> bool:
        """Desconecta del broker MQTT"""
        try:
            if self.mqtt_client:
                self.mqtt_client.disconnect()
                self.mqtt_client = None
            
            self.status = ConnectorStatus.DISCONNECTED
            self.connected = False
            self.subscribed_topics.clear()
            
            self.logger.info("✅ Desconectado del broker MQTT")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error desconectando de MQTT: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Verifica si está conectado al broker MQTT"""
        return self.connected and self.mqtt_client and self.mqtt_client._connected
    
    def _receive_data(self) -> Optional[Any]:
        """
        Recibe datos del broker MQTT
        
        Esta implementación depende de tu sistema MQTT existente.
        Los datos se reciben a través del callback _on_mqtt_message.
        """
        # En MQTT, los datos se reciben de forma asíncrona
        # No necesitamos implementar polling aquí
        return None
    
    def _parse_raw_data(self, raw_data: Any) -> Optional[UnifiedDataFormat]:
        """
        Parsea datos MQTT al formato unificado
        
        Args:
            raw_data: Datos MQTT (MQTTMessage o similar)
            
        Returns:
            Datos en formato unificado
        """
        try:
            if hasattr(raw_data, 'topic') and hasattr(raw_data, 'payload'):
                # Es un mensaje MQTT
                topic = raw_data.topic
                payload = raw_data.payload
                timestamp = getattr(raw_data, 'timestamp', datetime.now(timezone.utc))
                
                # Parsear tópico para extraer información
                topic_info = self.topic_mapper.parse_topic(topic)
                
                # Parsear payload
                measurements = self._parse_payload(payload)
                
                # Crear datos unificados
                unified_data = UnifiedDataFormat(
                    device_id=topic_info.get('device_id', 'unknown'),
                    project_id=topic_info.get('project_id', 'default'),
                    timestamp=timestamp,
                    measurements=measurements,
                    metadata={
                        'topic': topic,
                        'qos': getattr(raw_data, 'qos', 1),
                        'retain': getattr(raw_data, 'retain', False),
                        'topic_info': topic_info
                    },
                    quality=DataQuality.VALID,
                    source_protocol='mqtt',
                    source_address=f"{self.mqtt_config.broker_host}:{self.mqtt_config.broker_port}",
                    raw_data=raw_data
                )
                
                return unified_data
            else:
                self.logger.warning(f"Formato de datos MQTT no reconocido: {type(raw_data)}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error parseando datos MQTT: {e}")
            return None
    
    def _parse_payload(self, payload: Any) -> Dict[str, Any]:
        """Parsea el payload MQTT a mediciones"""
        try:
            if isinstance(payload, bytes):
                payload = payload.decode('utf-8')
            
            if isinstance(payload, str):
                # Intentar parsear como JSON
                try:
                    return json.loads(payload)
                except json.JSONDecodeError:
                    # Si no es JSON, tratar como texto simple
                    return {'value': payload}
            
            elif isinstance(payload, dict):
                return payload
            
            elif isinstance(payload, (int, float)):
                return {'value': payload}
            
            else:
                return {'raw_value': str(payload)}
                
        except Exception as e:
            self.logger.error(f"Error parseando payload MQTT: {e}")
            return {'error': str(e)}
    
    def _subscribe_to_topics(self):
        """Se suscribe a los tópicos configurados"""
        try:
            if not self.mqtt_client:
                return
            
            for topic in self.mqtt_config.topics_subscribe:
                try:
                    if self.mqtt_client.subscribe(topic, self.mqtt_config.qos):
                        self.subscribed_topics.append(topic)
                        self.logger.info(f"✅ Suscrito a tópico: {topic}")
                    else:
                        self.logger.warning(f"⚠️  No se pudo suscribir a tópico: {topic}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Error suscribiéndose a tópico {topic}: {e}")
            
            self.logger.info(f"Suscrito a {len(self.subscribed_topics)} tópicos")
            
        except Exception as e:
            self.logger.error(f"Error en suscripciones: {e}")
    
    def _on_mqtt_message(self, message):
        """Callback para mensajes MQTT recibidos"""
        try:
            # Crear datos unificados
            unified_data = self._parse_raw_data(message)
            
            if unified_data:
                # Enviar al callback del conector base
                if self.data_callback:
                    self.data_callback(unified_data)
                
                self.logger.debug(f"📨 Mensaje MQTT procesado: {message.topic}")
            else:
                self.logger.warning(f"No se pudo parsear mensaje MQTT: {message.topic}")
                
        except Exception as e:
            self.logger.error(f"Error procesando mensaje MQTT: {e}")
    
    def publish_message(self, topic: str, payload: Any, qos: int = None, retain: bool = None) -> bool:
        """
        Publica un mensaje en un tópico MQTT
        
        Args:
            topic: Tópico donde publicar
            payload: Contenido del mensaje
            qos: Calidad de servicio (usa el configurado si no se especifica)
            retain: Retener mensaje (usa el configurado si no se especifica)
            
        Returns:
            bool: True si se publicó exitosamente
        """
        try:
            if not self.is_connected():
                self.logger.error("No hay conexión MQTT activa")
                return False
            
            # Usar valores por defecto si no se especifican
            qos = qos if qos is not None else self.mqtt_config.qos
            retain = retain if retain is not None else self.mqtt_config.retain
            
            # Serializar payload si es necesario
            if isinstance(payload, (dict, list)):
                payload = json.dumps(payload)
            elif not isinstance(payload, (str, bytes)):
                payload = str(payload)
            
            # Publicar mensaje
            if self.mqtt_client.publish(topic, payload, qos, retain):
                self.logger.debug(f"📤 Mensaje publicado en {topic}: {payload}")
                return True
            else:
                self.logger.error(f"❌ No se pudo publicar mensaje en {topic}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error publicando mensaje MQTT: {e}")
            return False
    
    def _create_development_mqtt_client(self, config: Dict[str, Any]):
        """Crea un cliente MQTT de desarrollo para testing"""
        # Esta es una implementación básica para desarrollo
        # En producción, usa tu implementación MQTT existente
        class DevelopmentMQTTClient:
            def __init__(self, config):
                self.config = config
                self._connected = False
                self.message_processor = None
                self.subscriptions = {}
            
            def connect(self):
                self._connected = True
                return True
            
            def disconnect(self):
                self._connected = False
            
            def subscribe(self, topic, qos):
                self.subscriptions[topic] = qos
                return True
            
            def publish(self, topic, payload, qos, retain):
                return True
            
            def set_message_processor(self, processor):
                self.message_processor = processor
        
        return DevelopmentMQTTClient(config)
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del conector MQTT"""
        status = super().get_status()
        status.update({
            'broker_host': self.mqtt_config.broker_host,
            'broker_port': self.mqtt_config.broker_port,
            'topics_subscribed': self.subscribed_topics.copy(),
            'mqtt_connected': self.is_connected(),
            'ssl_enabled': self.mqtt_config.ssl_enabled
        })
        return status


class TopicMapper:
    """Mapeador de tópicos MQTT a información estructurada"""
    
    def __init__(self, topic_mapping: Dict[str, Any]):
        self.topic_mapping = topic_mapping
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def parse_topic(self, topic: str) -> Dict[str, Any]:
        """
        Parsea un tópico MQTT y extrae información
        
        Args:
            topic: Tópico MQTT (ej: "iot/proyecto_001/unidad_001/dispositivo_001/canal_001")
            
        Returns:
            Diccionario con información extraída
        """
        try:
            # Patrones de tópicos configurados
            for pattern, mapping in self.topic_mapping.items():
                if self._match_pattern(topic, pattern):
                    return self._extract_from_pattern(topic, pattern, mapping)
            
            # Patrón por defecto: iot/{proyecto}/{unidad}/{dispositivo}/{canal}
            parts = topic.split('/')
            if len(parts) >= 5 and parts[0] == 'iot':
                return {
                    'proyecto_id': parts[1],
                    'unidad_id': parts[2],
                    'dispositivo_id': parts[3],
                    'canal_id': parts[4],
                    'pattern_type': 'default'
                }
            
            # Tópico personalizado
            return {
                'topic_raw': topic,
                'pattern_type': 'custom',
                'device_id': parts[-1] if parts else 'unknown',
                'project_id': 'default'
            }
            
        except Exception as e:
            self.logger.error(f"Error parseando tópico {topic}: {e}")
            return {
                'topic_raw': topic,
                'pattern_type': 'error',
                'device_id': 'unknown',
                'project_id': 'default'
            }
    
    def _match_pattern(self, topic: str, pattern: str) -> bool:
        """Verifica si un tópico coincide con un patrón"""
        try:
            import re
            return bool(re.match(pattern, topic))
        except Exception:
            return pattern in topic
    
    def _extract_from_pattern(self, topic: str, pattern: str, mapping: Dict[str, str]) -> Dict[str, Any]:
        """Extrae información usando un patrón y mapeo específico"""
        try:
            import re
            match = re.match(pattern, topic)
            if match:
                result = {'pattern_type': 'custom'}
                for key, group_name in mapping.items():
                    if group_name in match.groupdict():
                        result[key] = match.group(group_name)
                return result
        except Exception as e:
            self.logger.error(f"Error extraiendo con patrón {pattern}: {e}")
        
        return {'topic_raw': topic, 'pattern_type': 'custom'}
