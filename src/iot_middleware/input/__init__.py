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

__all__ = [
    'BaseConnector',
    'UnifiedDataFormat',
    'DataQuality'
]
