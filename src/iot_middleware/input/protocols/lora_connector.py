"""
Conector LoRa (LoRaWAN) - IoT Middleware
=========================================

Permite recibir datos desde dispositivos LoRaWAN a través de gateways
como ChirpStack o The Things Stack. Los gateways exponen los datos
vía MQTT o HTTP Webhooks.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..base_connector import BaseConnector, ConnectorConfig, UnifiedDataFormat, DataQuality, ConnectorStatus


@dataclass
class LoRaConnectorConfig(ConnectorConfig):
    """Configuración específica para el conector LoRa"""
    # Configuración del gateway LoRa
    gateway_type: str = "chirpstack"  # "chirpstack", "tts", "custom"
    gateway_address: str = "localhost"
    gateway_port: int = 1883
    
    # Configuración MQTT del gateway
    mqtt_topic: str = "application/+/device/+/event/+"
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    
    # Configuración HTTP del gateway
    http_endpoint: str = "/webhook"
    http_auth_token: Optional[str] = None
    
    # Configuración de aplicaciones LoRa
    application_whitelist: List[str] = None  # IDs de aplicaciones permitidas
    device_whitelist: List[str] = None  # DevEUI de dispositivos permitidos
    device_blacklist: List[str] = None  # DevEUI de dispositivos bloqueados
    
    # Configuración de datos
    parse_payload: bool = True
    decode_base64: bool = True
    parse_metadata: bool = True
    parse_rx_info: bool = True
    
    def __post_init__(self):
        if self.application_whitelist is None:
            self.application_whitelist = []
        if self.device_whitelist is None:
            self.device_whitelist = []
        if self.device_blacklist is None:
            self.device_blacklist = []


class LoRaConnector(BaseConnector):
    """
    Conector LoRa que recibe datos desde gateways LoRaWAN
    
    Este conector se conecta a gateways LoRaWAN (ChirpStack, The Things Stack)
    que reciben datos de dispositivos LoRa y los exponen vía MQTT o HTTP.
    """
    
    def __init__(self, config: LoRaConnectorConfig, data_callback=None):
        super().__init__(config, data_callback)
        
        # Configuración específica de LoRa
        self.lora_config = LoRaConnectorConfig(**config.__dict__) if isinstance(config, ConnectorConfig) else config
        
        # Gateway LoRa (MQTT o HTTP)
        self.gateway_connector = None
        
        # Estado de dispositivos LoRa
        self.discovered_devices: Dict[str, Dict[str, Any]] = {}
        self.active_applications: Dict[str, Dict[str, Any]] = {}
        
        # Logging específico
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def connect(self) -> bool:
        """Conecta al gateway LoRa"""
        try:
            self.logger.info(f"🔌 Conectando al gateway LoRa ({self.lora_config.gateway_type}) en {self.lora_config.gateway_address}")
            
            # Crear conector del gateway según el tipo
            if self.lora_config.gateway_type.lower() in ["chirpstack", "tts", "custom"]:
                # Todos usan MQTT por defecto
                self.gateway_connector = self._create_mqtt_gateway()
            else:
                self.logger.error(f"Tipo de gateway no soportado: {self.lora_config.gateway_type}")
                return False
            
            if not self.gateway_connector:
                self.logger.error("No se pudo crear el conector del gateway")
                return False
            
            # Conectar al gateway
            if self.gateway_connector.connect():
                self.status = ConnectorStatus.CONNECTED
                self.connected = True
                self.last_connection_time = datetime.now(timezone.utc)
                
                self.logger.info(f"✅ Conectado al gateway LoRa en {self.lora_config.gateway_address}")
                return True
            else:
                self.logger.error("❌ No se pudo conectar al gateway LoRa")
                self.status = ConnectorStatus.ERROR
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error conectando al gateway LoRa: {e}")
            self.status = ConnectorStatus.ERROR
            self._handle_connection_error(e)
            return False
    
    def disconnect(self) -> bool:
        """Desconecta del gateway LoRa"""
        try:
            if self.gateway_connector:
                self.gateway_connector.disconnect()
                self.gateway_connector = None
            
            self.status = ConnectorStatus.DISCONNECTED
            self.connected = False
            self.discovered_devices.clear()
            self.active_applications.clear()
            
            self.logger.info("✅ Desconectado del gateway LoRa")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error desconectando del gateway LoRa: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Verifica si está conectado al gateway LoRa"""
        return self.connected and self.gateway_connector and self.gateway_connector.is_connected()
    
    def _receive_data(self) -> Optional[Any]:
        """
        Recibe datos del gateway LoRa
        
        Los datos se reciben de forma asíncrona a través del gateway.
        No necesitamos implementar polling aquí.
        """
        return None
    
    def _parse_raw_data(self, raw_data: Any) -> Optional[UnifiedDataFormat]:
        """
        Parsea datos LoRa al formato unificado
        
        Args:
            raw_data: Datos LoRa del gateway
            
        Returns:
            Datos en formato unificado
        """
        try:
            if not isinstance(raw_data, dict):
                self.logger.warning(f"Formato de datos LoRa no reconocido: {type(raw_data)}")
                return None
            
            # Extraer información básica del mensaje LoRa
            application_id = raw_data.get('applicationID', 'unknown')
            device_eui = raw_data.get('devEUI', 'unknown')
            device_name = raw_data.get('deviceName', 'unknown')
            
            # Verificar filtros de aplicaciones y dispositivos
            if not self._is_application_allowed(application_id):
                self.logger.debug(f"Aplicación {application_id} bloqueada por filtros")
                return None
            
            if not self._is_device_allowed(device_eui):
                self.logger.debug(f"Dispositivo {device_eui} bloqueado por filtros")
                return None
            
            # Parsear datos según el tipo de evento
            event_type = raw_data.get('event', 'unknown')
            measurements = self._parse_lora_event(raw_data, event_type)
            
            # Actualizar estado del dispositivo y aplicación
            self._update_device_status(device_eui, device_name, application_id, event_type)
            
            # Crear datos unificados
            unified_data = UnifiedDataFormat(
                device_id=device_eui,
                project_id=application_id,
                timestamp=datetime.now(timezone.utc),
                measurements=measurements,
                metadata={
                    'device_name': device_name,
                    'device_eui': device_eui,
                    'application_id': application_id,
                    'event_type': event_type,
                    'gateway_type': self.lora_config.gateway_type,
                    'gateway_address': self.lora_config.gateway_address,
                    'lora_data': raw_data
                },
                quality=DataQuality.VALID,
                source_protocol='lora',
                source_address=device_eui,
                raw_data=raw_data
            )
            
            return unified_data
            
        except Exception as e:
            self.logger.error(f"Error parseando datos LoRa: {e}")
            return None
    
    def _parse_lora_event(self, lora_data: Dict[str, Any], event_type: str) -> Dict[str, Any]:
        """Parsea un evento LoRa específico"""
        try:
            measurements = {}
            
            if event_type == "up":
                # Mensaje uplink del dispositivo
                measurements.update(self._parse_uplink_data(lora_data))
            elif event_type == "join":
                # Dispositivo se unió a la red
                measurements.update(self._parse_join_data(lora_data))
            elif event_type == "ack":
                # Acknowledgment
                measurements.update(self._parse_ack_data(lora_data))
            elif event_type == "error":
                # Error en el dispositivo
                measurements.update(self._parse_error_data(lora_data))
            else:
                # Evento desconocido
                measurements['event_type'] = event_type
                measurements['raw_data'] = lora_data
            
            return measurements
            
        except Exception as e:
            self.logger.error(f"Error parseando evento LoRa {event_type}: {e}")
            return {'error': str(e)}
    
    def _parse_uplink_data(self, lora_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parsea datos de mensaje uplink"""
        try:
            measurements = {}
            
            # Datos del payload
            if self.lora_config.parse_payload:
                payload = lora_data.get('data', '')
                if payload and self.lora_config.decode_base64:
                    try:
                        import base64
                        decoded_payload = base64.b64decode(payload).decode('utf-8')
                        measurements['payload'] = decoded_payload
                        
                        # Intentar parsear como JSON
                        try:
                            json_payload = json.loads(decoded_payload)
                            measurements.update(json_payload)
                        except json.JSONDecodeError:
                            measurements['payload_text'] = decoded_payload
                    except Exception:
                        measurements['payload_raw'] = payload
                else:
                    measurements['payload'] = payload
            
            # Metadatos del mensaje
            if self.lora_config.parse_metadata:
                if 'fCnt' in lora_data:
                    measurements['frame_counter'] = lora_data['fCnt']
                if 'fPort' in lora_data:
                    measurements['frame_port'] = lora_data['fPort']
                if 'adr' in lora_data:
                    measurements['adr_enabled'] = lora_data['adr']
                if 'dr' in lora_data:
                    measurements['data_rate'] = lora_data['dr']
            
            # Información de recepción
            if self.lora_config.parse_rx_info:
                rx_info = lora_data.get('rxInfo', [])
                if rx_info:
                    # Usar información del primer gateway que recibió el mensaje
                    first_gateway = rx_info[0]
                    measurements['gateway_id'] = first_gateway.get('gatewayID', 'unknown')
                    measurements['rssi'] = first_gateway.get('rssi', 0)
                    measurements['snr'] = first_gateway.get('loRaSNR', 0)
                    measurements['channel'] = first_gateway.get('channel', 0)
                    measurements['rf_chain'] = first_gateway.get('rfChain', 0)
            
            return measurements
            
        except Exception as e:
            self.logger.error(f"Error parseando datos uplink: {e}")
            return {'error': str(e)}
    
    def _parse_join_data(self, lora_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parsea datos de evento de unión"""
        try:
            measurements = {
                'event_type': 'join',
                'join_status': 'success'
            }
            
            # Información de la unión
            if 'devAddr' in lora_data:
                measurements['device_address'] = lora_data['devAddr']
            
            return measurements
            
        except Exception as e:
            self.logger.error(f"Error parseando datos de unión: {e}")
            return {'error': str(e)}
    
    def _parse_ack_data(self, lora_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parsea datos de acknowledgment"""
        try:
            measurements = {
                'event_type': 'ack',
                'ack_status': 'received'
            }
            
            # Información del ACK
            if 'fCnt' in lora_data:
                measurements['frame_counter'] = lora_data['fCnt']
            
            return measurements
            
        except Exception as e:
            self.logger.error(f"Error parseando datos de ACK: {e}")
            return {'error': str(e)}
    
    def _parse_error_data(self, lora_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parsea datos de error"""
        try:
            measurements = {
                'event_type': 'error',
                'error_status': 'detected'
            }
            
            # Información del error
            if 'error' in lora_data:
                measurements['error_message'] = lora_data['error']
            
            return measurements
            
        except Exception as e:
            self.logger.error(f"Error parseando datos de error: {e}")
            return {'error': str(e)}
    
    def _is_application_allowed(self, application_id: str) -> bool:
        """Verifica si una aplicación está permitida"""
        try:
            # Si hay whitelist, solo permitir aplicaciones en ella
            if self.lora_config.application_whitelist:
                return application_id in self.lora_config.application_whitelist
            
            # Si no hay whitelist, permitir todas
            return True
            
        except Exception as e:
            self.logger.error(f"Error verificando filtros de aplicación: {e}")
            return False
    
    def _is_device_allowed(self, device_eui: str) -> bool:
        """Verifica si un dispositivo está permitido"""
        try:
            # Verificar blacklist
            if device_eui in self.lora_config.device_blacklist:
                return False
            
            # Si hay whitelist, solo permitir dispositivos en ella
            if self.lora_config.device_whitelist:
                return device_eui in self.lora_config.device_whitelist
            
            # Si no hay whitelist, permitir todos (excepto los de blacklist)
            return True
            
        except Exception as e:
            self.logger.error(f"Error verificando filtros de dispositivo: {e}")
            return False
    
    def _update_device_status(self, device_eui: str, device_name: str, application_id: str, event_type: str):
        """Actualiza el estado de un dispositivo LoRa"""
        try:
            device_info = {
                'name': device_name,
                'application_id': application_id,
                'last_event': event_type,
                'last_seen': datetime.now(timezone.utc),
                'status': 'active'
            }
            
            self.discovered_devices[device_eui] = device_info
            
            # Actualizar aplicaciones activas
            if application_id not in self.active_applications:
                self.active_applications[application_id] = {
                    'devices': [],
                    'last_activity': datetime.now(timezone.utc)
                }
            
            if device_eui not in self.active_applications[application_id]['devices']:
                self.active_applications[application_id]['devices'].append(device_eui)
            
            self.active_applications[application_id]['last_activity'] = datetime.now(timezone.utc)
            
            # Log de nuevos dispositivos
            if event_type == "join":
                self.logger.info(f"🆕 Nuevo dispositivo LoRa unido: {device_name} ({device_eui}) en aplicación {application_id}")
                
        except Exception as e:
            self.logger.error(f"Error actualizando estado del dispositivo {device_eui}: {e}")
    
    def _create_mqtt_gateway(self):
        """Crea un conector MQTT para el gateway LoRa"""
        try:
            from .mqtt_connector import MQTTConnector, MQTTConnectorConfig
            
            # Crear configuración MQTT para el gateway
            mqtt_config = MQTTConnectorConfig(
                enabled=True,
                name=f"{self.config.name}_mqtt_gateway",
                protocol="mqtt",
                broker_host=self.lora_config.gateway_address,
                broker_port=self.lora_config.gateway_port,
                username=self.lora_config.mqtt_username,
                password=self.lora_config.mqtt_password,
                topics_subscribe=[self.lora_config.mqtt_topic],
                topics_publish=[],
                qos=1,
                retain=False
            )
            
            # Crear conector MQTT
            mqtt_connector = MQTTConnector(mqtt_config, self._on_gateway_data)
            return mqtt_connector
            
        except ImportError:
            self.logger.error("No se pudo importar el conector MQTT")
            return None
        except Exception as e:
            self.logger.error(f"Error creando conector MQTT para gateway: {e}")
            return None
    
    def _on_gateway_data(self, data):
        """Callback para datos recibidos del gateway LoRa"""
        try:
            # Crear datos unificados
            unified_data = self._parse_raw_data(data)
            
            if unified_data:
                # Enviar al callback del conector base
                if self.data_callback:
                    self.data_callback(unified_data)
                
                self.logger.debug(f"📨 Datos LoRa procesados: {unified_data.device_id}")
            else:
                self.logger.warning(f"No se pudo parsear datos del gateway LoRa")
                
        except Exception as e:
            self.logger.error(f"Error procesando datos del gateway LoRa: {e}")
    
    def get_discovered_devices(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene la lista de dispositivos LoRa descubiertos"""
        return self.discovered_devices.copy()
    
    def get_active_applications(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene la lista de aplicaciones LoRa activas"""
        return self.active_applications.copy()
    
    def add_device_to_whitelist(self, device_eui: str) -> bool:
        """Agrega un dispositivo a la whitelist"""
        try:
            if device_eui not in self.lora_config.device_whitelist:
                self.lora_config.device_whitelist.append(device_eui)
                self.logger.info(f"✅ Dispositivo {device_eui} agregado a whitelist")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error agregando dispositivo a whitelist: {e}")
            return False
    
    def remove_device_from_whitelist(self, device_eui: str) -> bool:
        """Remueve un dispositivo de la whitelist"""
        try:
            if device_eui in self.lora_config.device_whitelist:
                self.lora_config.device_whitelist.remove(device_eui)
                self.logger.info(f"✅ Dispositivo {device_eui} removido de whitelist")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error removiendo dispositivo de whitelist: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del conector LoRa"""
        status = super().get_status()
        status.update({
            'gateway_type': self.lora_config.gateway_type,
            'gateway_address': self.lora_config.gateway_address,
            'discovered_devices': len(self.discovered_devices),
            'active_applications': len(self.active_applications),
            'application_whitelist': self.lora_config.application_whitelist.copy(),
            'device_whitelist': self.lora_config.device_whitelist.copy(),
            'device_blacklist': self.lora_config.device_blacklist.copy(),
            'parse_payload': self.lora_config.parse_payload,
            'decode_base64': self.lora_config.decode_base64
        })
        return status
