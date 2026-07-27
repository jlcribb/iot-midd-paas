from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from iot_middleware.config import RabbitMQConfig
from iot_middleware.mqtt.mqtt_client import MQTTMessage
from iot_middleware.services.ingestor import (
    ControlTelemetryPublisher,
    DataValidator,
    IngestaMetrics,
    MessageProcessor,
    TopicMapper,
)


def build_runtime_config():
    return SimpleNamespace(
        ingesta={
            "max_queue_size": 10,
            "batch_size": 2,
            "batch_timeout": 0.1,
            "max_workers": 1,
            "validation_enabled": True,
            "topic_mapping": {
                "^iot/(?P<proyecto>[^/]+)/(?P<unidad>[^/]+)/(?P<dispositivo>[^/]+)/(?P<canal>[^/]+)$": {
                    "proyecto_id": "proyecto",
                    "unidad_id": "unidad",
                    "dispositivo_id": "dispositivo",
                    "canal_id": "canal",
                }
            },
            "control_telemetry_enabled": True,
        },
        rabbitmq=RabbitMQConfig(
            host="localhost",
            port=5672,
            username="guest",
            password="guest",
            virtual_host="/",
            exchange="iot_middleware",
            queue_prefix="iot",
            heartbeat=600,
            connection_attempts=3,
            retry_delay=5,
            enable_monitoring=True,
        ),
    )


def test_control_telemetry_publisher_builds_canonical_event():
    publisher = ControlTelemetryPublisher(build_runtime_config().rabbitmq, ingesta_config={"control_telemetry_enabled": True})

    event = publisher.build_event(
        {
            "project_id": "00000000-0000-0000-0000-000000000001",
            "sensor_type": "tank_level",
            "value": 72.5,
            "timestamp": "2026-06-02T20:00:00+00:00",
            "topic": "iot/project/unit/device/tank_level",
            "unit_id": "unit-1",
            "device_id": "device-1",
            "sector": "tank_A",
            "quality": "good",
        }
    )

    assert event is not None
    assert event["project_id"] == "00000000-0000-0000-0000-000000000001"
    assert event["variable"] == "tank_level"
    assert event["value"] == 72.5
    assert event["metadata"]["topic"] == "iot/project/unit/device/tank_level"
    assert event["context"]["unit_id"] == "unit-1"
    assert event["context"]["device_id"] == "device-1"
    assert event["context"]["sector"] == "tank_A"


def test_control_telemetry_publisher_recreates_rabbitmq_client_after_failed_publish(monkeypatch):
    first_client = MagicMock()
    first_client.publish_json.return_value = False

    second_client = MagicMock()
    second_client.publish_json.return_value = True

    created_clients = [first_client, second_client]
    publisher = ControlTelemetryPublisher(
        build_runtime_config().rabbitmq,
        ingesta_config={"control_telemetry_enabled": True},
    )

    monkeypatch.setattr(
        "iot_middleware.services.ingestor.create_rabbitmq_client",
        lambda rabbitmq_config: created_clients.pop(0),
    )
    first_client.connect.return_value = True
    second_client.connect.return_value = True

    published = publisher.publish_sensor_record(
        {
            "project_id": "00000000-0000-0000-0000-000000000001",
            "sensor_type": "tank_level",
            "value": 72.5,
            "timestamp": "2026-06-02T20:00:00+00:00",
        }
    )

    assert published is True
    first_client.disconnect.assert_called_once()
    second_client.publish_json.assert_called_once()


def test_message_processor_publishes_control_event_after_successful_persistence(monkeypatch):
    monkeypatch.setattr(MessageProcessor, "_start_workers", lambda self: None)

    db_handler = SimpleNamespace(
        influxdb_handler=None,
        insert_sensor_data=MagicMock(return_value=True),
    )
    processor = MessageProcessor(
        build_runtime_config(),
        db_handler,
        TopicMapper(build_runtime_config().ingesta),
        DataValidator(build_runtime_config().ingesta),
        IngestaMetrics(),
    )
    processor.telemetry_publisher.publish_sensor_record = MagicMock(return_value=True)

    message = MQTTMessage(
        topic="iot/00000000-0000-0000-0000-000000000001/unit-1/device-1/tank_level",
        payload={
            "value": 72.5,
            "timestamp": datetime(2026, 6, 2, 20, 0, tzinfo=timezone.utc).isoformat(),
            "sector": "tank_A",
        },
        qos=1,
        retain=False,
        timestamp=datetime(2026, 6, 2, 20, 0, tzinfo=timezone.utc),
    )

    processor._process_single_message(message)

    db_handler.insert_sensor_data.assert_called_once()
    processor.telemetry_publisher.publish_sensor_record.assert_called_once()
    published_record = processor.telemetry_publisher.publish_sensor_record.call_args.args[0]
    assert published_record["project_id"] == "00000000-0000-0000-0000-000000000001"
    assert published_record["sensor_type"] == "tank_level"
    assert published_record["value"] == 72.5
    assert published_record["sector"] == "tank_A"
    processor.stop()


def test_message_processor_skips_control_event_when_validation_fails(monkeypatch):
    monkeypatch.setattr(MessageProcessor, "_start_workers", lambda self: None)

    db_handler = SimpleNamespace(
        influxdb_handler=None,
        insert_sensor_data=MagicMock(return_value=True),
    )
    processor = MessageProcessor(
        build_runtime_config(),
        db_handler,
        TopicMapper(build_runtime_config().ingesta),
        DataValidator(build_runtime_config().ingesta),
        IngestaMetrics(),
    )
    processor.telemetry_publisher.publish_sensor_record = MagicMock(return_value=True)
    processor.data_validator.validate_payload = MagicMock(
        return_value={
            "valid": False,
            "quality": "BAD",
            "errors": ["invalid payload"],
            "warnings": [],
            "alarms": [],
        }
    )

    message = MQTTMessage(
        topic="iot/00000000-0000-0000-0000-000000000001/unit-1/device-1/tank_level",
        payload={"value": 72.5},
        qos=1,
        retain=False,
    )

    processor._process_single_message(message)

    db_handler.insert_sensor_data.assert_called_once()
    processor.telemetry_publisher.publish_sensor_record.assert_not_called()
    processor.stop()
