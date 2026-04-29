"""
Módulo de Mensajería Asíncrona - IoT Middleware
==============================================

Este módulo proporciona comunicación asíncrona entre microservicios usando RabbitMQ.
Permite publicar y consumir eventos de monitoreo en tiempo real.
"""

from .rabbitmq_client import (
    RabbitMQClient,
    create_rabbitmq_client,
    MonitoringEvent,
    EventType
)

__all__ = [
    'RabbitMQClient',
    'create_rabbitmq_client',
    'MonitoringEvent',
    'EventType'
]

__version__ = "1.0.0"
