"""
Módulo de Protocolos de Entrada - IoT Middleware
================================================

Implementa conectores específicos para cada protocolo IoT:
- MQTT: Comunicación por mensajería
- BLE: Bluetooth Low Energy
- LoRa: Comunicación de largo alcance
- MIDI: Interfaz digital de instrumentos musicales
- Modbus: Protocolo industrial
- ZigBee: Red de sensores inalámbricos
- HTTP/REST: Comunicación web directa

Cada conector implementa la interfaz BaseConnector y traduce
los datos específicos del protocolo al formato unificado.
"""

from .mqtt_connector import MQTTConnector
from .ble_connector import BLEConnector
from .lora_connector import LoRaConnector
from .midi_connector import MIDIConnector
from .modbus_connector import ModbusConnector
from .zigbee_connector import ZigBeeConnector
from .http_connector import HTTPConnector

__all__ = [
    'MQTTConnector',
    'BLEConnector',
    'LoRaConnector',
    'MIDIConnector',
    'ModbusConnector',
    'ZigBeeConnector',
    'HTTPConnector'
]
