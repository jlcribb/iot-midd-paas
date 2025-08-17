"""
Conector BLE (Bluetooth Low Energy) - IoT Middleware
====================================================

Permite recibir datos desde dispositivos Bluetooth Low Energy.
Requiere un nodo cercano (Raspberry Pi, ESP32, smartphone) que actúe de bridge
y envíe los datos al middleware vía MQTT o HTTP.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..base_connector import BaseConnector, ConnectorConfig, UnifiedDataFormat, DataQuality, ConnectorStatus


@dataclass
class BLEConnectorConfig(ConnectorConfig):
    """Configuración específica para el conector BLE"""
    # Configuración del bridge BLE
    bridge_type: str = "mqtt"  # "mqtt" o "http"
    bridge_address: str = "localhost"
    bridge_port: int = 1883
    
    # Configuración MQTT del bridge
    mqtt_topic: str = "ble/data"
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    
    # Configuración HTTP del bridge
    http_endpoint: str = "/ble/data"
    http_auth_token: Optional[str] = None
    
    # Configuración de dispositivos BLE
    device_whitelist: List[str] = None  # MAC addresses permitidas
    device_blacklist: List[str] = None  # MAC addresses bloqueadas
    auto_discovery: bool = True
    scan_interval: float = 10.0  # segundos entre escaneos
    
    # Configuración de datos
    data_format: str = "json"  # "json", "binary", "text"
    parse_manufacturer_data: bool = True
    parse_service_data: bool = True
    
    def __post_init__(self):
        if self.device_whitelist is None:
            self.device_whitelist = []
        if self.device_blacklist is None:
            self.device_blacklist = []


class BLEConnector(BaseConnector):
    """
    Conector BLE que recibe datos desde un bridge BLE
    
    Este conector se conecta a un bridge BLE (como un Raspberry Pi con
    un dongle BLE) que escanea dispositivos cercanos y envía los datos
    al middleware.
    """
    
    def __init__(self, config: BLEConnectorConfig, data_callback=None):
        super().__init__(config, data_callback)
        
        # Configuración específica de BLE
        self.ble_config = BLEConnectorConfig(**config.__dict__) if isinstance(config, ConnectorConfig) else config
        
        # Bridge BLE (MQTT o HTTP)
        self.bridge_connector = None
        
        # Estado de dispositivos BLE
        self.discovered_devices: Dict[str, Dict[str, Any]] = {}
        self.active_devices: Dict[str, Dict[str, Any]] = {}
        
        # Logging específico
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def connect(self) -> bool:
        """Conecta al bridge BLE"""
        try:
            self.logger.info(f"🔌 Conectando al bridge BLE ({self.ble_config.bridge_type}) en {self.ble_config.bridge_address}")
            
            # Crear conector del bridge según el tipo
            if self.ble_config.bridge_type.lower() == "mqtt":
                self.bridge_connector = self._create_mqtt_bridge()
            elif self.ble_config.bridge_type.lower() == "http":
                self.bridge_connector = self._create_http_bridge()
            else:
                self.logger.error(f"Tipo de bridge no soportado: {self.ble_config.bridge_type}")
                return False
            
            if not self.bridge_connector:
                self.logger.error("No se pudo crear el conector del bridge")
                return False
            
            # Conectar al bridge
            if self.bridge_connector.connect():
                self.status = ConnectorStatus.CONNECTED
                self.connected = True
                self.last_connection_time = datetime.now(timezone.utc)
                
                self.logger.info(f"✅ Conectado al bridge BLE en {self.ble_config.bridge_address}")
                return True
            else:
                self.logger.error("❌ No se pudo conectar al bridge BLE")
                self.status = ConnectorStatus.ERROR
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error conectando al bridge BLE: {e}")
            self.status = ConnectorStatus.ERROR
            self._handle_connection_error(e)
            return False
    
    def disconnect(self) -> bool:
        """Desconecta del bridge BLE"""
        try:
            if self.bridge_connector:
                self.bridge_connector.disconnect()
                self.bridge_connector = None
            
            self.status = ConnectorStatus.DISCONNECTED
            self.connected = False
            self.discovered_devices.clear()
            self.active_devices.clear()
            
            self.logger.info("✅ Desconectado del bridge BLE")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error desconectando del bridge BLE: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Verifica si está conectado al bridge BLE"""
        return self.connected and self.bridge_connector and self.bridge_connector.is_connected()
    
    def _receive_data(self) -> Optional[Any]:
        """
        Recibe datos del bridge BLE
        
        Los datos se reciben de forma asíncrona a través del bridge.
        No necesitamos implementar polling aquí.
        """
        return None
    
    def _parse_raw_data(self, raw_data: Any) -> Optional[UnifiedDataFormat]:
        """
        Parsea datos BLE al formato unificado
        
        Args:
            raw_data: Datos BLE del bridge
            
        Returns:
            Datos en formato unificado
        """
        try:
            if not isinstance(raw_data, dict):
                self.logger.warning(f"Formato de datos BLE no reconocido: {type(raw_data)}")
                return None
            
            # Extraer información del dispositivo BLE
            device_mac = raw_data.get('mac_address', 'unknown')
            device_name = raw_data.get('device_name', 'unknown')
            rssi = raw_data.get('rssi', 0)
            timestamp = raw_data.get('timestamp', datetime.now(timezone.utc))
            
            # Verificar filtros de dispositivos
            if not self._is_device_allowed(device_mac):
                self.logger.debug(f"Dispositivo {device_mac} bloqueado por filtros")
                return None
            
            # Parsear datos según el formato
            measurements = self._parse_ble_data(raw_data)
            
            # Actualizar estado del dispositivo
            self._update_device_status(device_mac, device_name, rssi, timestamp)
            
            # Crear datos unificados
            unified_data = UnifiedDataFormat(
                device_id=device_mac,
                project_id=raw_data.get('project_id', 'ble_default'),
                timestamp=timestamp,
                measurements=measurements,
                metadata={
                    'device_name': device_name,
                    'mac_address': device_mac,
                    'rssi': rssi,
                    'bridge_type': self.ble_config.bridge_type,
                    'bridge_address': self.ble_config.bridge_address,
                    'ble_data': raw_data
                },
                quality=DataQuality.VALID,
                source_protocol='ble',
                source_address=device_mac,
                raw_data=raw_data
            )
            
            return unified_data
            
        except Exception as e:
            self.logger.error(f"Error parseando datos BLE: {e}")
            return None
    
    def _parse_ble_data(self, ble_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parsea los datos específicos de BLE"""
        try:
            measurements = {}
            
            # Datos básicos del dispositivo
            if 'battery_level' in ble_data:
                measurements['battery_level'] = ble_data['battery_level']
            
            if 'temperature' in ble_data:
                measurements['temperature'] = ble_data['temperature']
            
            if 'humidity' in ble_data:
                measurements['humidity'] = ble_data['humidity']
            
            if 'pressure' in ble_data:
                measurements['pressure'] = ble_data['pressure']
            
            # Datos de servicios BLE
            if self.ble_config.parse_service_data and 'services' in ble_data:
                for service_uuid, service_data in ble_data['services'].items():
                    if isinstance(service_data, dict):
                        for char_uuid, char_data in service_data.items():
                            key = f"service_{service_uuid[-8:]}_{char_uuid[-8:]}"
                            measurements[key] = char_data
            
            # Datos del fabricante
            if self.ble_config.parse_manufacturer_data and 'manufacturer_data' in ble_data:
                for company_id, data in ble_data['manufacturer_data'].items():
                    key = f"manufacturer_{company_id}"
                    measurements[key] = data
            
            # Datos personalizados
            if 'custom_data' in ble_data:
                measurements.update(ble_data['custom_data'])
            
            # Si no hay mediciones específicas, usar datos crudos
            if not measurements:
                measurements['raw_data'] = ble_data.get('raw_data', {})
                measurements['advertisement_data'] = ble_data.get('advertisement_data', {})
            
            return measurements
            
        except Exception as e:
            self.logger.error(f"Error parseando datos BLE específicos: {e}")
            return {'error': str(e)}
    
    def _is_device_allowed(self, device_mac: str) -> bool:
        """Verifica si un dispositivo está permitido según los filtros"""
        try:
            # Verificar blacklist
            if device_mac in self.ble_config.device_blacklist:
                return False
            
            # Si hay whitelist, solo permitir dispositivos en ella
            if self.ble_config.device_whitelist:
                return device_mac in self.ble_config.device_whitelist
            
            # Si no hay whitelist, permitir todos (excepto los de blacklist)
            return True
            
        except Exception as e:
            self.logger.error(f"Error verificando filtros de dispositivo: {e}")
            return False
    
    def _update_device_status(self, mac: str, name: str, rssi: int, timestamp: datetime):
        """Actualiza el estado de un dispositivo BLE"""
        try:
            device_info = {
                'name': name,
                'last_seen': timestamp,
                'rssi': rssi,
                'status': 'active'
            }
            
            self.discovered_devices[mac] = device_info
            
            # Actualizar dispositivos activos
            if mac in self.active_devices:
                self.active_devices[mac].update(device_info)
            else:
                self.active_devices[mac] = device_info.copy()
                self.logger.info(f"🆕 Nuevo dispositivo BLE descubierto: {name} ({mac})")
                
        except Exception as e:
            self.logger.error(f"Error actualizando estado del dispositivo {mac}: {e}")
    
    def _create_mqtt_bridge(self):
        """Crea un conector MQTT para el bridge BLE"""
        try:
            from .mqtt_connector import MQTTConnector, MQTTConnectorConfig
            
            # Crear configuración MQTT para el bridge
            mqtt_config = MQTTConnectorConfig(
                enabled=True,
                name=f"{self.config.name}_mqtt_bridge",
                protocol="mqtt",
                broker_host=self.ble_config.bridge_address,
                broker_port=self.ble_config.bridge_port,
                username=self.ble_config.mqtt_username,
                password=self.ble_config.mqtt_password,
                topics_subscribe=[self.ble_config.mqtt_topic],
                topics_publish=[],
                qos=1,
                retain=False
            )
            
            # Crear conector MQTT
            mqtt_connector = MQTTConnector(mqtt_config, self._on_bridge_data)
            return mqtt_connector
            
        except ImportError:
            self.logger.error("No se pudo importar el conector MQTT")
            return None
        except Exception as e:
            self.logger.error(f"Error creando conector MQTT para bridge: {e}")
            return None
    
    def _create_http_bridge(self):
        """Crea un conector HTTP para el bridge BLE"""
        try:
            from .http_connector import HTTPConnector, HTTPConnectorConfig
            
            # Crear configuración HTTP para el bridge
            http_config = HTTPConnectorConfig(
                enabled=True,
                name=f"{self.config.name}_http_bridge",
                protocol="http",
                host=self.ble_config.bridge_address,
                port=self.ble_config.bridge_port,
                endpoint=self.ble_config.http_endpoint,
                auth_token=self.ble_config.http_auth_token
            )
            
            # Crear conector HTTP
            http_connector = HTTPConnector(http_config, self._on_bridge_data)
            return http_connector
            
        except ImportError:
            self.logger.error("No se pudo importar el conector HTTP")
            return None
        except Exception as e:
            self.logger.error(f"Error creando conector HTTP para bridge: {e}")
            return None
    
    def _on_bridge_data(self, data):
        """Callback para datos recibidos del bridge BLE"""
        try:
            # Crear datos unificados
            unified_data = self._parse_raw_data(data)
            
            if unified_data:
                # Enviar al callback del conector base
                if self.data_callback:
                    self.data_callback(unified_data)
                
                self.logger.debug(f"📨 Datos BLE procesados: {unified_data.device_id}")
            else:
                self.logger.warning(f"No se pudo parsear datos del bridge BLE")
                
        except Exception as e:
            self.logger.error(f"Error procesando datos del bridge BLE: {e}")
    
    def get_discovered_devices(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene la lista de dispositivos BLE descubiertos"""
        return self.discovered_devices.copy()
    
    def get_active_devices(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene la lista de dispositivos BLE activos"""
        return self.active_devices.copy()
    
    def add_device_to_whitelist(self, mac_address: str) -> bool:
        """Agrega un dispositivo a la whitelist"""
        try:
            if mac_address not in self.ble_config.device_whitelist:
                self.ble_config.device_whitelist.append(mac_address)
                self.logger.info(f"✅ Dispositivo {mac_address} agregado a whitelist")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error agregando dispositivo a whitelist: {e}")
            return False
    
    def remove_device_from_whitelist(self, mac_address: str) -> bool:
        """Remueve un dispositivo de la whitelist"""
        try:
            if mac_address in self.ble_config.device_whitelist:
                self.ble_config.device_whitelist.remove(mac_address)
                self.logger.info(f"✅ Dispositivo {mac_address} removido de whitelist")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error removiendo dispositivo de whitelist: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del conector BLE"""
        status = super().get_status()
        status.update({
            'bridge_type': self.ble_config.bridge_type,
            'bridge_address': self.ble_config.bridge_address,
            'discovered_devices': len(self.discovered_devices),
            'active_devices': len(self.active_devices),
            'device_whitelist': self.ble_config.device_whitelist.copy(),
            'device_blacklist': self.ble_config.device_blacklist.copy(),
            'auto_discovery': self.ble_config.auto_discovery,
            'scan_interval': self.ble_config.scan_interval
        })
        return status
