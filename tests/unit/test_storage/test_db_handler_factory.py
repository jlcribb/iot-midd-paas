from datetime import datetime, timezone

from iot_middleware.config import InfluxDBConfig, PostgreSQLConfig, StorageConfig
import iot_middleware.config as config_module
from iot_middleware.config.config_loader import IoTMiddlewareConfig
from iot_middleware.storage import db_handler as db_handler_module


def build_config():
    return IoTMiddlewareConfig(
        mqtt={
            "broker": {"host": "localhost", "port": 1883},
            "topics": {"subscribe": ["iot/+/data"], "publish": ["iot/status"]},
        },
        influxdb=InfluxDBConfig(
            url="http://localhost:8086",
            token="dev-token",
            org="test-org",
            bucket="test-bucket",
        ),
        postgresql=PostgreSQLConfig(
            host="localhost",
            port=5432,
            database="iot_middleware",
            username="iot_user",
            password="iot_password",
        ),
        api={"host": "127.0.0.1", "port": 8000, "debug": False, "cors": {}},
        storage=StorageConfig(
            timeseries={"provider": "influxdb", "enabled": True},
            relational={"provider": "postgresql", "enabled": True},
            metadata={"provider": "postgresql", "enabled": True},
        ),
    )


def test_create_database_handler_accepts_full_config(monkeypatch):
    config = build_config()
    captured = {}

    class FakeDatabaseHandler:
        def __init__(self, postgresql_config, influxdb_config, storage_config):
            captured["postgresql"] = postgresql_config
            captured["influxdb"] = influxdb_config
            captured["storage"] = storage_config

    monkeypatch.setattr(db_handler_module, "DatabaseHandler", FakeDatabaseHandler)

    handler = db_handler_module.create_database_handler(config=config)

    assert isinstance(handler, FakeDatabaseHandler)
    assert captured["postgresql"] == config.postgresql
    assert captured["influxdb"] == config.influxdb
    assert captured["storage"] == config.storage


def test_create_database_handler_requires_complete_database_config():
    try:
        db_handler_module.create_database_handler(storage_config=StorageConfig(
            timeseries={"provider": "influxdb", "enabled": True},
            relational={"provider": "postgresql", "enabled": True},
            metadata={"provider": "postgresql", "enabled": True},
        ))
    except ValueError as exc:
        assert "IoTMiddlewareConfig completo" in str(exc)
    else:
        raise AssertionError("create_database_handler debía rechazar configuración incompleta")


def test_control_settings_connection_url_prefers_runtime_env(monkeypatch):
    db_handler_module._get_control_settings_connection_url.cache_clear()
    monkeypatch.setattr(config_module, "load_config", lambda _: build_config())
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5433")
    monkeypatch.setenv("DB_NAME", "iot_runtime")
    monkeypatch.setenv("DB_USER", "runtime_user")
    monkeypatch.setenv("DB_PASSWORD", "runtime_password")

    connection_url = db_handler_module._get_control_settings_connection_url()

    assert connection_url == "postgresql://runtime_user:runtime_password@localhost:5433/iot_runtime"
    db_handler_module._get_control_settings_connection_url.cache_clear()


def test_persist_control_audit_record_serializes_nested_datetimes(monkeypatch):
    captured = {}

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def add(self, record):
            captured["record"] = record

        def commit(self):
            captured["committed"] = True

    monkeypatch.setattr(
        db_handler_module,
        "_get_control_settings_connection_url",
        lambda: "postgresql://runtime_user:runtime_password@localhost:5432/iot_middleware",
    )
    monkeypatch.setattr(
        db_handler_module,
        "_get_control_runtime_session_factory",
        lambda connection_url: (lambda: FakeSession()),
    )

    persisted = db_handler_module.persist_control_audit_record(
        {
            "message_type": "control.audit",
            "timestamp": "2026-04-28T23:46:46.760196+00:00",
            "payload": {
                "project_id": "00000000-0000-0000-0000-000000000001",
                "evaluated_at": "2026-04-28T23:46:46.760196+00:00",
                "evaluation": {
                    "trace": [
                        {
                            "step": "input_received",
                            "data": {
                                "measurement": {
                                    "observed_at": datetime(2026, 4, 28, 23, 46, 46, tzinfo=timezone.utc),
                                }
                            },
                        }
                    ]
                },
            },
        },
        action="CONTROL_RECOMMENDATION_EMITTED",
    )

    assert persisted is True
    assert captured["committed"] is True
    observed_at = captured["record"].cambios["payload"]["evaluation"]["trace"][0]["data"]["measurement"]["observed_at"]
    assert observed_at == "2026-04-28T23:46:46+00:00"
