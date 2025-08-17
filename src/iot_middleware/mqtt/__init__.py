"""
Módulo MQTT - IoT Middleware
============================

Este módulo proporciona funcionalidades para la comunicación MQTT,
incluyendo un cliente robusto con reconexión automática y manejo
de mensajes JSON.
"""

from .mqtt_client import (
    IoTMQTTClient,
    MQTTMessage,
    MQTTCallbackHandler,
    create_mqtt_client,
    process_message
)

__all__ = [
    'IoTMQTTClient',
    'MQTTMessage',
    'MQTTCallbackHandler',
    'create_mqtt_client',
    'process_message'
]

__version__ = "1.0.0"
__author__ = "IoT Middleware Team"
