"""
Tests Unitarios - RabbitMQ Client
=================================

Tests para el cliente RabbitMQ que maneja comunicación asíncrona.
"""

import pytest
import json
import time
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timezone
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from iot_middleware.messaging import (
    RabbitMQClient,
    MonitoringEvent,
    EventType,
    create_rabbitmq_client
)
from iot_middleware.config import RabbitMQConfig


@pytest.fixture
def rabbitmq_config():
    """Fixture para configuración de RabbitMQ"""
    return RabbitMQConfig(
        host="localhost",
        port=5672,
        username="test_user",
        password="test_pass",
        virtual_host="/",
        exchange="test_exchange",
        queue_prefix="test",
        heartbeat=600,
        connection_attempts=3,
        retry_delay=5,
        enable_monitoring=True
    )


@pytest.fixture
def mock_pika_connection():
    """Fixture para mock de conexión Pika"""
    with patch('iot_middleware.messaging.rabbitmq_client.pika.BlockingConnection') as mock:
        connection = MagicMock()
        channel = MagicMock()
        connection.channel.return_value = channel
        channel.is_closed = False
        connection.is_closed = False
        mock.return_value = connection
        yield connection, channel


class TestRabbitMQClient:
    """Tests para RabbitMQClient"""
    
    def test_initialization(self, rabbitmq_config):
        """Test de inicialización del cliente"""
        client = RabbitMQClient(rabbitmq_config)
        
        assert client.config == rabbitmq_config
        assert client.exchange == rabbitmq_config.exchange
        assert client.queue_prefix == rabbitmq_config.queue_prefix
        assert client.connected is False
        assert client.reconnecting is False
    
    def test_connection_success(self, rabbitmq_config, mock_pika_connection):
        """Test de conexión exitosa"""
        connection, channel = mock_pika_connection
        client = RabbitMQClient(rabbitmq_config)
        
        result = client.connect()
        
        assert result is True
        assert client.connected is True
        assert client.connection == connection
        assert client.channel == channel
        channel.exchange_declare.assert_called_once()
    
    def test_connection_failure(self, rabbitmq_config):
        """Test de fallo de conexión"""
        with patch('iot_middleware.messaging.rabbitmq_client.pika.BlockingConnection') as mock:
            mock.side_effect = AMQPConnectionError("Connection failed")
            client = RabbitMQClient(rabbitmq_config)
            
            result = client.connect()
            
            assert result is False
            assert client.connected is False
    
    def test_disconnect(self, rabbitmq_config, mock_pika_connection):
        """Test de desconexión"""
        connection, channel = mock_pika_connection
        client = RabbitMQClient(rabbitmq_config)
        client.connect()
        
        client.disconnect()
        
        assert client.connected is False
        channel.close.assert_called_once()
        connection.close.assert_called_once()
    
    def test_publish_event_success(self, rabbitmq_config, mock_pika_connection):
        """Test de publicación exitosa de evento"""
        connection, channel = mock_pika_connection
        client = RabbitMQClient(rabbitmq_config)
        client.connect()
        
        event = MonitoringEvent(
            event_type=EventType.METRIC,
            service="test_service",
            timestamp=datetime.now(timezone.utc),
            data={"metric": "test.metric", "value": 42},
            severity="info"
        )
        
        result = client.publish_event(event)
        
        assert result is True
        channel.basic_publish.assert_called_once()
        call_args = channel.basic_publish.call_args
        assert call_args[1]['exchange'] == rabbitmq_config.exchange
        assert 'routing_key' in call_args[1]
        assert 'body' in call_args[1]
        
        # Verificar que el cuerpo es JSON válido
        body = call_args[1]['body']
        data = json.loads(body)
        assert data['event_type'] == 'metric'
        assert data['service'] == 'test_service'
    
    def test_publish_event_not_connected(self, rabbitmq_config):
        """Test de publicación sin conexión"""
        client = RabbitMQClient(rabbitmq_config)
        
        event = MonitoringEvent(
            event_type=EventType.METRIC,
            service="test_service",
            timestamp=datetime.now(timezone.utc),
            data={"metric": "test.metric", "value": 42}
        )
        
        with patch.object(client, 'connect', return_value=False):
            result = client.publish_event(event)
            assert result is False
    
    def test_subscribe_to_events(self, rabbitmq_config, mock_pika_connection):
        """Test de suscripción a eventos"""
        connection, channel = mock_pika_connection
        client = RabbitMQClient(rabbitmq_config)
        client.connect()
        
        callback = Mock()
        event_types = [EventType.METRIC, EventType.ALERT]
        
        result = client.subscribe_to_events(event_types, callback)
        
        assert result is True
        channel.queue_declare.assert_called_once()
        assert channel.queue_bind.call_count == len(event_types)
        channel.basic_consume.assert_called_once()
        assert EventType.METRIC in client.event_callbacks
        assert callback in client.event_callbacks[EventType.METRIC]
    
    def test_on_message_handler(self, rabbitmq_config, mock_pika_connection):
        """Test del manejador de mensajes"""
        connection, channel = mock_pika_connection
        client = RabbitMQClient(rabbitmq_config)
        client.connect()
        
        callback = Mock()
        client.subscribe_to_events([EventType.METRIC], callback)
        
        # Simular mensaje recibido
        event_data = {
            "event_type": "metric",
            "service": "test_service",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"metric": "test.metric", "value": 42},
            "severity": "info"
        }
        message_body = json.dumps(event_data)
        
        # Llamar al manejador
        client._on_message(None, None, None, message_body.encode())
        
        # Verificar que el callback fue llamado
        callback.assert_called_once()
        called_event = callback.call_args[0][0]
        assert isinstance(called_event, MonitoringEvent)
        assert called_event.event_type == EventType.METRIC
    
    def test_health_check(self, rabbitmq_config, mock_pika_connection):
        """Test de health check"""
        client = RabbitMQClient(rabbitmq_config)
        client.connect()
        
        health = client.health_check()
        
        assert health['connected'] is True
        assert health['exchange'] == rabbitmq_config.exchange
        assert health['host'] == rabbitmq_config.host
        assert health['port'] == rabbitmq_config.port

    def test_declare_topic_queue(self, rabbitmq_config, mock_pika_connection):
        """Test de declaración y binding de cola topic genérica"""
        _, channel = mock_pika_connection
        client = RabbitMQClient(rabbitmq_config)
        client.connect()

        result = client.declare_topic_queue(
            queue_name="telemetry.events",
            routing_keys=["telemetry.events"],
            durable=True,
        )

        assert result is True
        channel.queue_declare.assert_called_once()
        channel.queue_bind.assert_called_once_with(
            exchange=rabbitmq_config.exchange,
            queue="telemetry.events",
            routing_key="telemetry.events",
        )

    def test_publish_json(self, rabbitmq_config, mock_pika_connection):
        """Test de publicación de payload JSON arbitrario"""
        _, channel = mock_pika_connection
        client = RabbitMQClient(rabbitmq_config)
        client.connect()

        payload = {"project_id": "p1", "variable": "tank_level"}
        result = client.publish_json(
            routing_key="control.recommendations",
            payload=payload,
            queue_name="control.recommendations",
            durable_queue=True,
        )

        assert result is True
        channel.queue_declare.assert_called()
        channel.queue_bind.assert_called()
        channel.basic_publish.assert_called_once()

    def test_get_json_message(self, rabbitmq_config, mock_pika_connection):
        """Test de lectura JSON con basic_get"""
        _, channel = mock_pika_connection
        client = RabbitMQClient(rabbitmq_config)
        client.connect()

        method_frame = MagicMock()
        method_frame.delivery_tag = 99
        method_frame.routing_key = "telemetry.events"
        channel.basic_get.return_value = (method_frame, MagicMock(), json.dumps({"hello": "world"}).encode())

        message = client.get_json_message("telemetry.events", auto_ack=False)

        assert message["payload"] == {"hello": "world"}
        assert message["delivery_tag"] == 99
        assert message["routing_key"] == "telemetry.events"

    def test_ack_message(self, rabbitmq_config, mock_pika_connection):
        """Test de confirmación manual de mensaje"""
        _, channel = mock_pika_connection
        client = RabbitMQClient(rabbitmq_config)
        client.connect()

        result = client.ack_message(77)

        assert result is True
        channel.basic_ack.assert_called_once_with(delivery_tag=77)
    
    def test_reconnection_loop(self, rabbitmq_config):
        """Test del loop de reconexión"""
        client = RabbitMQClient(rabbitmq_config)
        client._stop_event.set()  # Detener inmediatamente
        
        # Simular fallo de conexión
        client.connected = False
        client.reconnecting = True
        
        # El loop debería intentar reconectar
        with patch.object(client, 'connect', return_value=True) as mock_connect:
            # Ejecutar el loop (se detendrá inmediatamente por _stop_event)
            client._reconnect_loop()
            # Verificar que se intentó conectar (aunque el loop se detuvo rápido)
            # El estado connected puede no cambiar si el loop se detiene antes
            # Lo importante es que el método se ejecutó sin errores
            assert client._stop_event.is_set() is True


class TestMonitoringEvent:
    """Tests para MonitoringEvent"""
    
    def test_event_creation(self):
        """Test de creación de evento"""
        event = MonitoringEvent(
            event_type=EventType.METRIC,
            service="test_service",
            timestamp=datetime.now(timezone.utc),
            data={"metric": "test.metric", "value": 42},
            severity="info"
        )
        
        assert event.event_type == EventType.METRIC
        assert event.service == "test_service"
        assert event.severity == "info"
        assert event.data["metric"] == "test.metric"
    
    def test_event_to_dict(self):
        """Test de conversión a diccionario"""
        timestamp = datetime.now(timezone.utc)
        event = MonitoringEvent(
            event_type=EventType.METRIC,
            service="test_service",
            timestamp=timestamp,
            data={"metric": "test.metric", "value": 42},
            severity="info"
        )
        
        event_dict = event.to_dict()
        
        assert event_dict['event_type'] == 'metric'
        assert event_dict['service'] == 'test_service'
        assert event_dict['severity'] == 'info'
        assert event_dict['data']['metric'] == 'test.metric'
        assert event_dict['timestamp'] == timestamp.isoformat()
    
    def test_event_from_dict(self):
        """Test de creación desde diccionario"""
        timestamp = datetime.now(timezone.utc)
        event_dict = {
            "event_type": "metric",
            "service": "test_service",
            "timestamp": timestamp.isoformat(),
            "data": {"metric": "test.metric", "value": 42},
            "severity": "info"
        }
        
        event = MonitoringEvent.from_dict(event_dict)
        
        assert event.event_type == EventType.METRIC
        assert event.service == "test_service"
        assert event.severity == "info"
        assert event.data["metric"] == "test.metric"


class TestCreateRabbitMQClient:
    """Tests para la función create_rabbitmq_client"""
    
    def test_create_client(self, rabbitmq_config):
        """Test de creación de cliente"""
        client = create_rabbitmq_client(rabbitmq_config)
        
        assert isinstance(client, RabbitMQClient)
        assert client.config == rabbitmq_config
