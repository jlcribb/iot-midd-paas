from datetime import datetime, timezone
from types import SimpleNamespace

from iot_middleware.api.routers.data_router import _metadata_value
from iot_middleware.api.routers.events_router import _event_metadata, _serialize_event, _normalize_event_payload


def test_data_router_prefers_metadatos_field():
    registro = SimpleNamespace(metadatos={"source": "sensor"}, metadata={"legacy": True})

    assert _metadata_value(registro) == {"source": "sensor"}


def test_events_router_supports_current_model_fields():
    ts = datetime.now(timezone.utc)
    evento = SimpleNamespace(
        ts=ts,
        metadatos={"ack": True},
        codigo="TEMP_HIGH",
        titulo="Temperatura alta",
        severidad="warning",
        estado="activa",
        dispositivo_id=None,
        canal_id=None,
        proyecto_id=None,
        id="evt-1",
    )

    assert _event_metadata(evento) == {"ack": True}
    serialized = _serialize_event(evento)
    assert serialized["tipo"] == "TEMP_HIGH"
    assert serialized["mensaje"] == "Temperatura alta"
    assert serialized["timestamp"] == ts


def test_events_router_normalizes_legacy_payload():
    normalized = _normalize_event_payload(
        {
            "tipo": "TEMP_HIGH",
            "mensaje": "Temperatura alta",
            "timestamp": "2025-01-01T00:00:00Z",
            "metadata": {"legacy": True},
            "activo": True,
        }
    )

    assert normalized["codigo"] == "TEMP_HIGH"
    assert normalized["titulo"] == "Temperatura alta"
    assert normalized["ts"] == "2025-01-01T00:00:00Z"
    assert normalized["metadatos"] == {"legacy": True}
    assert normalized["estado"] == "activa"
