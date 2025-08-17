"""
Conector ZigBee - IoT Middleware
================================

Permite recibir datos desde dispositivos ZigBee de domótica a través de
coordinadores como Zigbee2MQTT. Los coordinadores exponen los datos vía MQTT.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..base_connector import BaseConnector, ConnectorConfig, UnifiedDataFormat, DataQuality, ConnectorStatus


@dataclass
class ZigBeeConnectorConfig(ConnectorConfig):
    """Configuración específica para el conector ZigBee"""
    # Configuración del coordinador ZigBee
    coordinator_type: str = "zigbee2mqtt"  # "zigbee2mqtt", "deconz", "custom"
    coordinator_address: str = "localhost"
    coordinator_port: int = 1883
    
    # Configuración MQTT del coordinador
    mqtt_topic: str = "zigbee2mqtt/+/+"
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    
    # Configuración de dispositivos ZigBee
    device_whitelist: List[str] = None  # Nombres de dispositivos permitidos
    device_blacklist: List[str] = None  # Nombres de dispositivos bloqueados
    device_types: List[str] = None  # Tipos de dispositivos a procesar
    
    # Configuración de datos
    parse_device_info: bool = True
    parse_sensor_data: bool = True
    parse_battery: bool = True
    parse_availability: bool = True
    parse_actions: bool = True
    
    def __post_init__(self):
        if self.device_whitelist is None:
            self.device_whitelist = []
        if self.device_blacklist is None:
            self.device_blacklist = []
        if self.device_types is None:
            self.device_types = ["sensor", "switch", "light", "thermostat", "lock"]


class ZigBeeConnector(BaseConnector):
    """
    Conector ZigBee que recibe datos desde coordinadores ZigBee
    
    Este conector se conecta a coordinadores ZigBee (Zigbee2MQTT, deCONZ)
    que reciben datos de dispositivos de domótica y los exponen vía MQTT.
    """
    
    def __init__(self, config: ZigBeeConnectorConfig, data_callback=None):
        super().__init__(config, data_callback)
        
        # Configuración específica de ZigBee
        self.zigbee_config = ZigBeeConnectorConfig(**config.__dict__) if isinstance(config, ConnectorConfig) else config
        
        # Coordinador ZigBee (MQTT)
        self.coordinator_connector = None
        
        # Estado de dispositivos ZigBee
        self.discovered_devices: Dict[str, Dict[str, Any]] = {}
        self.active_devices: Dict[str, Dict[str, Any]] = {}
        self.device_states: Dict[str, Dict[str, Any]] = {}
        
        # Logging específico
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def connect(self) -> bool:
        """Conecta al coordinador ZigBee"""
        try:
            self.logger.info(f"🔌 Conectando al coordinador ZigBee ({self.zigbee_config.coordinator_type}) en {self.zigbee_config.coordinator_address}")
            
            # Crear conector MQTT para el coordinador
            self.coordinator_connector = self._create_mqtt_coordinator()
            
            if not self.coordinator_connector:
                self.logger.error("No se pudo crear el conector del coordinador")
                return False
            
            # Conectar al coordinador
            if self.coordinator_connector.connect():
                self.status = ConnectorStatus.CONNECTED
                self.connected = True
                self.last_connection_time = datetime.now(timezone.utc)
                
                self.logger.info(f"✅ Conectado al coordinador ZigBee en {self.zigbee_config.coordinator_address}")
                return True
            else:
                self.logger.error("❌ No se pudo conectar al coordinador ZigBee")
                self.status = ConnectorStatus.ERROR
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error conectando al coordinador ZigBee: {e}")
            self.status = ConnectorStatus.ERROR
            self._handle_connection_error(e)
            return False
    
    def disconnect(self) -> bool:
        """Desconecta del coordinador ZigBee"""
        try:
            if self.coordinator_connector:
                self.coordinator_connector.disconnect()
                self.coordinator_connector = None
            
            self.status = ConnectorStatus.DISCONNECTED
            self.connected = False
            self.discovered_devices.clear()
            self.active_devices.clear()
            self.device_states.clear()
            
            self.logger.info("✅ Desconectado del coordinador ZigBee")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error desconectando del coordinador ZigBee: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Verifica si está conectado al coordinador ZigBee"""
        return self.connected and self.coordinator_connector and self.coordinator_connector.is_connected()
    
    def _receive_data(self) -> Optional[Any]:
        """
        Recibe datos del coordinador ZigBee
        
        Los datos se reciben de forma asíncrona a través del coordinador.
        No necesitamos implementar polling aquí.
        """
        return None
    
    def _parse_raw_data(self, raw_data: Any) -> Optional[UnifiedDataFormat]:
        """
        Parsea datos ZigBee al formato unificado
        
        Args:
            raw_data: Datos ZigBee del coordinador
            
        Returns:
            Datos en formato unificado
        """
        try:
            if not isinstance(raw_data, dict):
                self.logger.warning(f"Formato de datos ZigBee no reconocido: {type(raw_data)}")
                return None
            
            # Extraer información básica del mensaje ZigBee
            topic = raw_data.get('topic', '')
            payload = raw_data.get('payload', {})
            
            # Parsear tópico para extraer información del dispositivo
            device_info = self._parse_zigbee_topic(topic)
            if not device_info:
                return None
            
            device_name = device_info.get('device_name', 'unknown')
            device_type = device_info.get('device_type', 'unknown')
            
            # Verificar filtros de dispositivos
            if not self._is_device_allowed(device_name):
                self.logger.debug(f"Dispositivo {device_name} bloqueado por filtros")
                return None
            
            # Parsear payload según el tipo de dispositivo
            measurements = self._parse_zigbee_payload(payload, device_type)
            
            # Actualizar estado del dispositivo
            self._update_device_status(device_name, device_type, measurements, payload)
            
            # Crear datos unificados
            unified_data = UnifiedDataFormat(
                device_id=device_name,
                project_id="home_automation",
                timestamp=datetime.now(timezone.utc),
                measurements=measurements,
                metadata={
                    'device_name': device_name,
                    'device_type': device_type,
                    'topic': topic,
                    'coordinator_type': self.zigbee_config.coordinator_type,
                    'coordinator_address': self.zigbee_config.coordinator_address,
                    'zigbee_data': payload
                },
                quality=DataQuality.VALID,
                source_protocol='zigbee',
                source_address=device_name,
                raw_data=raw_data
            )
            
            return unified_data
            
        except Exception as e:
            self.logger.error(f"Error parseando datos ZigBee: {e}")
            return None
    
    def _parse_zigbee_topic(self, topic: str) -> Optional[Dict[str, str]]:
        """Parsea el tópico ZigBee para extraer información del dispositivo"""
        try:
            # Formato típico: zigbee2mqtt/device_name/action
            parts = topic.split('/')
            if len(parts) >= 2 and parts[0] == 'zigbee2mqtt':
                device_name = parts[1]
                action = parts[2] if len(parts) > 2 else 'state'
                
                # Determinar tipo de dispositivo basado en el nombre o configuración
                device_type = self._determine_device_type(device_name)
                
                return {
                    'device_name': device_name,
                    'device_type': device_type,
                    'action': action
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parseando tópico ZigBee {topic}: {e}")
            return None
    
    def _determine_device_type(self, device_name: str) -> str:
        """Determina el tipo de dispositivo basado en su nombre"""
        try:
            device_name_lower = device_name.lower()
            
            # Patrones comunes en nombres de dispositivos
            if any(word in device_name_lower for word in ['sensor', 'temp', 'humidity', 'motion']):
                return 'sensor'
            elif any(word in device_name_lower for word in ['switch', 'button', 'relay']):
                return 'switch'
            elif any(word in device_name_lower for word in ['light', 'bulb', 'lamp', 'strip']):
                return 'light'
            elif any(word in device_name_lower for word in ['thermostat', 'hvac']):
                return 'thermostat'
            elif any(word in device_name_lower for word in ['lock', 'door']):
                return 'lock'
            elif any(word in device_name_lower for word in ['plug', 'outlet']):
                return 'plug'
            else:
                return 'unknown'
                
        except Exception:
            return 'unknown'
    
    def _parse_zigbee_payload(self, payload: Dict[str, Any], device_type: str) -> Dict[str, Any]:
        """Parsea el payload ZigBee según el tipo de dispositivo"""
        try:
            measurements = {}
            
            # Información básica del dispositivo
            if self.zigbee_config.parse_device_info:
                if 'friendly_name' in payload:
                    measurements['friendly_name'] = payload['friendly_name']
                if 'model' in payload:
                    measurements['model'] = payload['model']
                if 'manufacturer' in payload:
                    measurements['manufacturer'] = payload['manufacturer']
            
            # Datos de sensores
            if self.zigbee_config.parse_sensor_data:
                if device_type == 'sensor':
                    measurements.update(self._parse_sensor_data(payload))
                elif device_type == 'thermostat':
                    measurements.update(self._parse_thermostat_data(payload))
            
            # Estado de batería
            if self.zigbee_config.parse_battery:
                if 'battery' in payload:
                    measurements['battery'] = payload['battery']
                if 'battery_low' in payload:
                    measurements['battery_low'] = payload['battery_low']
            
            # Disponibilidad del dispositivo
            if self.zigbee_config.parse_availability:
                if 'last_seen' in payload:
                    measurements['last_seen'] = payload['last_seen']
                if 'linkquality' in payload:
                    measurements['link_quality'] = payload['linkquality']
            
            # Acciones del dispositivo
            if self.zigbee_config.parse_actions:
                if device_type == 'switch':
                    measurements.update(self._parse_switch_data(payload))
                elif device_type == 'light':
                    measurements.update(self._parse_light_data(payload))
                elif device_type == 'lock':
                    measurements.update(self._parse_lock_data(payload))
            
            # Datos personalizados
            if 'custom_data' in payload:
                measurements.update(payload['custom_data'])
            
            return measurements
            
        except Exception as e:
            self.logger.error(f"Error parseando payload ZigBee: {e}")
            return {'error': str(e)}
    
    def _parse_sensor_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parsea datos de sensores"""
        try:
            sensor_data = {}
            
            # Temperatura
            if 'temperature' in payload:
                sensor_data['temperature'] = payload['temperature']
            
            # Humedad
            if 'humidity' in payload:
                sensor_data['humidity'] = payload['humidity']
            
            # Presión
            if 'pressure' in payload:
                sensor_data['pressure'] = payload['pressure']
            
            # Movimiento
            if 'occupancy' in payload:
                sensor_data['motion_detected'] = payload['occupancy']
            
            # Iluminación
            if 'illuminance' in payload:
                sensor_data['illuminance'] = payload['illuminance']
            
            # Voltaje
            if 'voltage' in payload:
                sensor_data['voltage'] = payload['voltage']
            
            return sensor_data
            
        except Exception as e:
            self.logger.error(f"Error parseando datos de sensor: {e}")
            return {'error': str(e)}
    
    def _parse_thermostat_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parsea datos de termostatos"""
        try:
            thermostat_data = {}
            
            # Temperatura actual
            if 'current_heating_setpoint' in payload:
                thermostat_data['current_setpoint'] = payload['current_heating_setpoint']
            
            # Temperatura objetivo
            if 'occupied_heating_setpoint' in payload:
                thermostat_data['target_setpoint'] = payload['occupied_heating_setpoint']
            
            # Modo del sistema
            if 'system_mode' in payload:
                thermostat_data['system_mode'] = payload['system_mode']
            
            # Estado del sistema
            if 'running_state' in payload:
                thermostat_data['running_state'] = payload['running_state']
            
            return thermostat_data
            
        except Exception as e:
            self.logger.error(f"Error parseando datos de termostato: {e}")
            return {'error': str(e)}
    
    def _parse_switch_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parsea datos de interruptores"""
        try:
            switch_data = {}
            
            # Estado del interruptor
            if 'state' in payload:
                switch_data['state'] = payload['state']
            
            # Acción del botón
            if 'action' in payload:
                switch_data['action'] = payload['action']
            
            # Click del botón
            if 'click' in payload:
                switch_data['click'] = payload['click']
            
            return switch_data
            
        except Exception as e:
            self.logger.error(f"Error parseando datos de interruptor: {e}")
            return {'error': str(e)}
    
    def _parse_light_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parsea datos de luces"""
        try:
            light_data = {}
            
            # Estado de la luz
            if 'state' in payload:
                light_data['state'] = payload['state']
            
            # Brillo
            if 'brightness' in payload:
                light_data['brightness'] = payload['brightness']
            
            # Color
            if 'color' in payload:
                light_data['color'] = payload['color']
            
            # Temperatura de color
            if 'color_temp' in payload:
                light_data['color_temperature'] = payload['color_temp']
            
            # Efecto
            if 'effect' in payload:
                light_data['effect'] = payload['effect']
            
            return light_data
            
        except Exception as e:
            self.logger.error(f"Error parseando datos de luz: {e}")
            return {'error': str(e)}
    
    def _parse_lock_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parsea datos de cerraduras"""
        try:
            lock_data = {}
            
            # Estado de la cerradura
            if 'lock_state' in payload:
                lock_data['lock_state'] = payload['lock_state']
            
            # Estado del pestillo
            if 'bolt_state' in payload:
                lock_data['bolt_state'] = payload['bolt_state']
            
            # Estado de la puerta
            if 'door_state' in payload:
                lock_data['door_state'] = payload['door_state']
            
            return lock_data
            
        except Exception as e:
            self.logger.error(f"Error parseando datos de cerradura: {e}")
            return {'error': str(e)}
    
    def _is_device_allowed(self, device_name: str) -> bool:
        """Verifica si un dispositivo está permitido según los filtros"""
        try:
            # Verificar blacklist
            if device_name in self.zigbee_config.device_blacklist:
                return False
            
            # Si hay whitelist, solo permitir dispositivos en ella
            if self.zigbee_config.device_whitelist:
                return device_name in self.zigbee_config.device_whitelist
            
            # Si no hay whitelist, permitir todos (excepto los de blacklist)
            return True
            
        except Exception as e:
            self.logger.error(f"Error verificando filtros de dispositivo: {e}")
            return False
    
    def _update_device_status(self, device_name: str, device_type: str, measurements: Dict[str, Any], payload: Dict[str, Any]):
        """Actualiza el estado de un dispositivo ZigBee"""
        try:
            device_info = {
                'type': device_type,
                'last_seen': datetime.now(timezone.utc),
                'last_measurements': measurements.copy(),
                'status': 'active'
            }
            
            self.discovered_devices[device_name] = device_info
            
            # Actualizar dispositivos activos
            if device_name in self.active_devices:
                self.active_devices[device_name].update(device_info)
            else:
                self.active_devices[device_name] = device_info.copy()
                self.logger.info(f"🆕 Nuevo dispositivo ZigBee descubierto: {device_name} ({device_type})")
            
            # Actualizar estado del dispositivo
            self.device_states[device_name] = {
                'type': device_type,
                'state': measurements.copy(),
                'last_update': datetime.now(timezone.utc)
            }
                
        except Exception as e:
            self.logger.error(f"Error actualizando estado del dispositivo {device_name}: {e}")
    
    def _create_mqtt_coordinator(self):
        """Crea un conector MQTT para el coordinador ZigBee"""
        try:
            from .mqtt_connector import MQTTConnector, MQTTConnectorConfig
            
            # Crear configuración MQTT para el coordinador
            mqtt_config = MQTTConnectorConfig(
                enabled=True,
                name=f"{self.config.name}_mqtt_coordinator",
                protocol="mqtt",
                broker_host=self.zigbee_config.coordinator_address,
                broker_port=self.zigbee_config.coordinator_port,
                username=self.zigbee_config.mqtt_username,
                password=self.zigbee_config.mqtt_password,
                topics_subscribe=[self.zigbee_config.mqtt_topic],
                topics_publish=[],
                qos=1,
                retain=False
            )
            
            # Crear conector MQTT
            mqtt_connector = MQTTConnector(mqtt_config, self._on_coordinator_data)
            return mqtt_connector
            
        except ImportError:
            self.logger.error("No se pudo importar el conector MQTT")
            return None
        except Exception as e:
            self.logger.error(f"Error creando conector MQTT para coordinador: {e}")
            return None
    
    def _on_coordinator_data(self, data):
        """Callback para datos recibidos del coordinador ZigBee"""
        try:
            # Crear datos unificados
            unified_data = self._parse_raw_data(data)
            
            if unified_data:
                # Enviar al callback del conector base
                if self.data_callback:
                    self.data_callback(unified_data)
                
                self.logger.debug(f"📨 Datos ZigBee procesados: {unified_data.device_id}")
            else:
                self.logger.debug(f"Datos ZigBee filtrados o no parseables")
                
        except Exception as e:
            self.logger.error(f"Error procesando datos del coordinador ZigBee: {e}")
    
    def get_discovered_devices(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene la lista de dispositivos ZigBee descubiertos"""
        return self.discovered_devices.copy()
    
    def get_active_devices(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene la lista de dispositivos ZigBee activos"""
        return self.active_devices.copy()
    
    def get_device_states(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene el estado actual de todos los dispositivos"""
        return self.device_states.copy()
    
    def get_device_state(self, device_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado de un dispositivo específico"""
        return self.device_states.get(device_name)
    
    def add_device_to_whitelist(self, device_name: str) -> bool:
        """Agrega un dispositivo a la whitelist"""
        try:
            if device_name not in self.zigbee_config.device_whitelist:
                self.zigbee_config.device_whitelist.append(device_name)
                self.logger.info(f"✅ Dispositivo {device_name} agregado a whitelist")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error agregando dispositivo a whitelist: {e}")
            return False
    
    def remove_device_from_whitelist(self, device_name: str) -> bool:
        """Remueve un dispositivo de la whitelist"""
        try:
            if device_name in self.zigbee_config.device_whitelist:
                self.zigbee_config.device_whitelist.remove(device_name)
                self.logger.info(f"✅ Dispositivo {device_name} removido de whitelist")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error removiendo dispositivo de whitelist: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del conector ZigBee"""
        status = super().get_status()
        status.update({
            'coordinator_type': self.zigbee_config.coordinator_type,
            'coordinator_address': self.zigbee_config.coordinator_address,
            'discovered_devices': len(self.discovered_devices),
            'active_devices': len(self.active_devices),
            'device_whitelist': self.zigbee_config.device_whitelist.copy(),
            'device_blacklist': self.zigbee_config.device_blacklist.copy(),
            'device_types': self.zigbee_config.device_types.copy(),
            'parse_device_info': self.zigbee_config.parse_device_info,
            'parse_sensor_data': self.zigbee_config.parse_sensor_data,
            'parse_battery': self.zigbee_config.parse_battery
        })
        return status
