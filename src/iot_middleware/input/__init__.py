"""
Módulo de Entrada de Datos - IoT Middleware
===========================================

Este módulo implementa conectores para múltiples protocolos IoT:
- MQTT (ya implementado)
- BLE (Bluetooth Low Energy)
- LoRa (LoRaWAN)
- MIDI (música)
- Modbus (industria)
- ZigBee/Z-Wave (domótica)
- HTTP/REST directo

Cada conector traduce los datos a un formato unificado antes de entrar al core.
"""

from .base_connector import BaseConnector, UnifiedDataFormat, DataQuality
from .connector_factory import ConnectorFactory
from .input_manager import InputManager
from .protocols.mqtt_connector import MQTTConnector
from .protocols.ble_connector import BLEConnector
from .protocols.lora_connector import LoRaConnector
from .protocols.midi_connector import MIDIConnector
from .protocols.modbus_connector import ModbusConnector
from .protocols.zigbee_connector import ZigBeeConnector
from .protocols.http_connector import HTTPConnector

__all__ = [
    'BaseConnector',
    'UnifiedDataFormat',
    'DataQuality',
    'ConnectorFactory',
    'InputManager',
    'MQTTConnector',
    'BLEConnector',
    'LoRaConnector',
    'MIDIConnector',
    'ModbusConnector',
    'ZigBeeConnector',
    'HTTPConnector'
]
