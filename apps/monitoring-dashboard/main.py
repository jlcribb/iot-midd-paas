#!/usr/bin/env python3
"""
Dashboard de Monitoreo - Punto de Entrada
==========================================

Servicio independiente de dashboard que consume eventos de RabbitMQ
y los muestra en tiempo real mediante WebSocket.

Incluye runtime de demo para el gemelo digital con control por:
- Proyecto
- Unidad
- Dispositivo
"""

import os
import sys
import json
import math
import time
import copy
import base64
import csv
import io
import logging
import asyncio
import threading
from collections import deque
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib import request as urllib_request
from urllib import error as urllib_error
from urllib import parse as urllib_parse

# Agregar src al path (subir 2 niveles desde apps/monitoring-dashboard/ para llegar a la raíz)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from iot_middleware.messaging import (
    RabbitMQClient,
    MonitoringEvent,
    EventType,
    create_rabbitmq_client
)
from iot_middleware.config import RabbitMQConfig, MQTTConfig, load_config
from iot_middleware.mqtt import create_mqtt_client

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="IoT Middleware Dashboard",
    description="Dashboard de monitoreo en tiempo real",
    version="1.1.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Almacenar conexiones WebSocket activas
active_connections: List[WebSocket] = []

# Cliente RabbitMQ consumidor (para mostrar eventos en dashboard)
rabbitmq_client: Optional[RabbitMQClient] = None
rabbitmq_thread: Optional[threading.Thread] = None
rabbitmq_config: Optional[RabbitMQConfig] = None

# Cliente RabbitMQ publicador (runtime de gemelo)
runtime_publisher_client: Optional[RabbitMQClient] = None

# Cliente MQTT publicador (runtime -> ingestor)
runtime_mqtt_client: Optional[Any] = None

# Configuración completa cargada (para resolver Influx/Rabbit en panel infra)
dashboard_app_config: Optional[Any] = None

# Buffer de eventos DATA para analítica de concordancia RabbitMQ vs InfluxDB
FLOW_EVENT_MAXLEN = 20000
flow_events_lock = threading.Lock()
flow_events: deque[Dict[str, Any]] = deque(maxlen=FLOW_EVENT_MAXLEN)


def _slug(value: str) -> str:
    text = (value or "").strip().lower()
    cleaned = []
    for ch in text:
        if ch.isalnum():
            cleaned.append(ch)
        else:
            cleaned.append("_")
    result = "".join(cleaned).strip("_")
    while "__" in result:
        result = result.replace("__", "_")
    return result or "item"


class DemoTwinRuntime:
    """
    Runtime de simulación para demo del gemelo digital.

    Genera eventos DATA y METRIC en RabbitMQ cuando se activa
    a nivel proyecto, unidad o dispositivo.
    """

    def __init__(
        self,
        *,
        admin_api_base_url: str,
        publisher_client: RabbitMQClient,
        mqtt_client: Optional[Any] = None,
        tick_seconds: float = 2.0,
        hierarchy_refresh_seconds: float = 20.0,
    ) -> None:
        self.admin_api_base_url = admin_api_base_url.rstrip("/")
        self.publisher_client = publisher_client
        self.mqtt_client = mqtt_client
        self.tick_seconds = max(0.5, tick_seconds)
        self.hierarchy_refresh_seconds = max(5.0, hierarchy_refresh_seconds)

        self._lock = threading.Lock()
        self._publish_lock = threading.Lock()
        self._mqtt_publish_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._tick = 0
        self._started_at = time.time()
        self._last_refresh_monotonic = 0.0

        self._project_index: Dict[str, Dict[str, Any]] = {}
        self._unit_index: Dict[str, Dict[str, Any]] = {}
        self._device_index: Dict[str, Dict[str, Any]] = {}
        self._project_device_map: Dict[str, set[str]] = {}
        self._unit_device_map: Dict[str, set[str]] = {}
        self._hierarchy_payload: Dict[str, Any] = {"projects": [], "updated_at": None}

        self.active_projects: set[str] = set()
        self.active_units: set[str] = set()
        self.active_devices: set[str] = set()

        self.metrics: Dict[str, int] = {
            "messages_processed": 0,
            "messages_failed": 0,
            "database_operations": 0,
            "active_protocols": 0,
            "active_devices": 0,
            "uptime_seconds": 0,
        }

    def _admin_get_json(self, path: str) -> Any:
        url = f"{self.admin_api_base_url}/{path.lstrip('/')}"
        req = urllib_request.Request(url, headers={"Accept": "application/json"})
        with urllib_request.urlopen(req, timeout=8) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)

    def refresh_hierarchy(self) -> Dict[str, Any]:
        projects = self._admin_get_json("core/projects?active=true")
        units = self._admin_get_json("core/sectors?active=true")
        devices = self._admin_get_json("core/assets?active=true")

        project_index: Dict[str, Dict[str, Any]] = {}
        unit_index: Dict[str, Dict[str, Any]] = {}
        device_index: Dict[str, Dict[str, Any]] = {}
        project_device_map: Dict[str, set[str]] = {}
        unit_device_map: Dict[str, set[str]] = {}

        for p in projects:
            pid = str(p["id"])
            project_index[pid] = {
                "id": pid,
                "name": p.get("name") or pid,
                "units": [],
                "devices_without_unit": [],
            }
            project_device_map[pid] = set()

        for u in units:
            uid = str(u["id"])
            pid = str(u["project_id"])
            if pid not in project_index:
                continue
            unit_payload = {
                "id": uid,
                "name": u.get("name") or uid,
                "project_id": pid,
                "devices": [],
            }
            project_index[pid]["units"].append(unit_payload)
            unit_index[uid] = unit_payload
            unit_device_map[uid] = set()

        for d in devices:
            did = str(d["id"])  # ID en assets
            pid = str(d["project_id"])
            uid = str(d["sector_id"]) if d.get("sector_id") else None
            if pid not in project_index:
                continue

            d_payload = {
                "id": did,
                "project_id": pid,
                "project_name": project_index[pid]["name"],
                "unit_id": uid,
                "unit_name": unit_index[uid]["name"] if uid and uid in unit_index else None,
                "device_ref_id": str(d.get("legacy_dispositivo_proyecto_id")) if d.get("legacy_dispositivo_proyecto_id") else None,
                "device_name": d.get("name") or did,
                "device_model": d.get("subtype") or d.get("asset_type") or "",
            }

            if uid and uid in unit_index:
                unit_index[uid]["devices"].append(d_payload)
                unit_device_map[uid].add(did)
            else:
                project_index[pid]["devices_without_unit"].append(d_payload)

            project_device_map[pid].add(did)
            device_index[did] = d_payload

        for project in project_index.values():
            project["units"] = sorted(project["units"], key=lambda x: x["name"].lower())
            for unit in project["units"]:
                unit["devices"] = sorted(unit["devices"], key=lambda x: x["device_name"].lower())
            project["devices_without_unit"] = sorted(
                project["devices_without_unit"],
                key=lambda x: x["device_name"].lower(),
            )

        projects_payload = sorted(project_index.values(), key=lambda x: x["name"].lower())
        payload = {
            "projects": projects_payload,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source": self.admin_api_base_url,
        }

        with self._lock:
            self._project_index = project_index
            self._unit_index = unit_index
            self._device_index = device_index
            self._project_device_map = project_device_map
            self._unit_device_map = unit_device_map
            self._hierarchy_payload = payload
            self._last_refresh_monotonic = time.monotonic()

            valid_projects = set(project_index.keys())
            valid_units = set(unit_index.keys())
            valid_devices = set(device_index.keys())

            self.active_projects.intersection_update(valid_projects)
            self.active_units.intersection_update(valid_units)
            self.active_devices.intersection_update(valid_devices)

        return copy.deepcopy(payload)

    def get_hierarchy(self) -> Dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._hierarchy_payload)

    def _publish(self, event: MonitoringEvent) -> None:
        with self._publish_lock:
            if not self.publisher_client.connected:
                self.publisher_client.connect()
            self.publisher_client.publish_event(event)

    def _publish_mqtt(self, topic: str, payload: Dict[str, Any]) -> None:
        if not self.mqtt_client:
            return
        with self._mqtt_publish_lock:
            if not self.mqtt_client._connected:
                self.mqtt_client.connect()
            if not self.mqtt_client.publish(topic, payload):
                raise RuntimeError(f"No se pudo publicar muestra MQTT en tópico {topic}")

    def _publish_status(self, status: str, scope: str, scope_id: str, message: str) -> None:
        event = MonitoringEvent(
            event_type=EventType.STATUS,
            service="digital_twin_runtime",
            timestamp=datetime.now(timezone.utc),
            data={
                "status": status,
                "scope": scope,
                "scope_id": scope_id,
                "message": message,
            },
            severity="info" if status in {"started", "stopped"} else "warning",
        )
        self._publish(event)

    def _set_scope(self, *, scope: str, scope_id: str, enable: bool) -> Dict[str, Any]:
        with self._lock:
            if scope == "project":
                if scope_id not in self._project_index:
                    raise KeyError(f"Proyecto no encontrado: {scope_id}")
                target_set = self.active_projects
            elif scope == "unit":
                if scope_id not in self._unit_index:
                    raise KeyError(f"Sector no encontrado: {scope_id}")
                target_set = self.active_units
            elif scope == "device":
                if scope_id not in self._device_index:
                    raise KeyError(f"Asset no encontrado: {scope_id}")
                target_set = self.active_devices
            else:
                raise KeyError(f"Scope inválido: {scope}")

            if enable:
                target_set.add(scope_id)
            else:
                target_set.discard(scope_id)

            state = {
                "scope": scope,
                "scope_id": scope_id,
                "enabled": enable,
                "active_projects_count": len(self.active_projects),
                "active_units_count": len(self.active_units),
                "active_devices_count": len(self.active_devices),
            }

        action = "started" if enable else "stopped"
        self._publish_status(
            action,
            scope,
            scope_id,
            f"Gemelo {action} para {scope}:{scope_id}",
        )
        return state

    def start_project(self, project_id: str) -> Dict[str, Any]:
        return self._set_scope(scope="project", scope_id=project_id, enable=True)

    def stop_project(self, project_id: str) -> Dict[str, Any]:
        return self._set_scope(scope="project", scope_id=project_id, enable=False)

    def start_unit(self, unit_id: str) -> Dict[str, Any]:
        return self._set_scope(scope="unit", scope_id=unit_id, enable=True)

    def stop_unit(self, unit_id: str) -> Dict[str, Any]:
        return self._set_scope(scope="unit", scope_id=unit_id, enable=False)

    def start_device(self, device_id: str) -> Dict[str, Any]:
        return self._set_scope(scope="device", scope_id=device_id, enable=True)

    def stop_device(self, device_id: str) -> Dict[str, Any]:
        return self._set_scope(scope="device", scope_id=device_id, enable=False)

    def _resolve_active_device_ids(self) -> set[str]:
        with self._lock:
            resolved = set(self.active_devices)

            for unit_id in self.active_units:
                resolved.update(self._unit_device_map.get(unit_id, set()))

            for project_id in self.active_projects:
                resolved.update(self._project_device_map.get(project_id, set()))

            return resolved

    def _generate_signal_value(self, device_payload: Dict[str, Any], tick: int) -> tuple[str, Any, str]:
        descriptor = (
            f"{device_payload.get('device_name', '')} "
            f"{device_payload.get('device_model', '')}"
        ).lower()
        phase = (abs(hash(device_payload["id"])) % 360) * math.pi / 180.0
        t = tick / 4.0

        if "nivel" in descriptor or "ultra" in descriptor or "sensor" in descriptor:
            value = max(0.0, min(100.0, 50.0 + 42.0 * math.sin(t + phase)))
            return "level_percent", round(value, 2), "%"

        if "servo" in descriptor or "motor" in descriptor:
            value = max(0.0, min(180.0, 90.0 + 90.0 * math.sin(t + phase)))
            return "servo_angle", round(value, 1), "deg"

        if "valvula" in descriptor or "electro" in descriptor or "ev_" in descriptor:
            state = ((tick + abs(hash(device_payload["id"]))) % 2) == 0
            return "open", state, "bool"

        value = 20.0 + 5.0 * math.sin(t + phase)
        return "value", round(value, 2), "unit"

    def _publish_device_data(self, device_payload: Dict[str, Any], tick: int) -> None:
        signal_name, value, unit = self._generate_signal_value(device_payload, tick)
        timestamp = datetime.now(timezone.utc)

        topic = (
            f"iot/{_slug(device_payload.get('project_name', 'proyecto'))}"
            f"/{_slug(device_payload.get('unit_name') or 'sin_unidad')}"
            f"/{_slug(device_payload.get('device_name', 'dispositivo'))}"
            f"/{_slug(signal_name)}"
            f"/value"
        )

        payload = {
            "kind": "digital_twin_sample",
            "project_id": device_payload.get("project_id"),
            "project_name": device_payload.get("project_name"),
            "unit_id": device_payload.get("unit_id"),
            "unit_name": device_payload.get("unit_name"),
            "device_id": device_payload.get("id"),
            "device_ref_id": device_payload.get("device_ref_id"),
            "device_name": device_payload.get("device_name"),
            "signal": signal_name,
            "value": value,
            "unit": unit,
            "topic": topic,
            "tick": tick,
            "timestamp": timestamp.isoformat(),
        }

        event = MonitoringEvent(
            event_type=EventType.DATA,
            service="digital_twin_runtime",
            timestamp=timestamp,
            data=payload,
            severity="info",
        )
        self._publish(event)

        try:
            self._publish_mqtt(topic, payload)
        except Exception as exc:
            logger.warning(f"⚠️  Falló publicación MQTT de muestra: {exc}")

    def _publish_metrics(self, processed_delta: int, active_devices_count: int) -> None:
        with self._lock:
            self.metrics["messages_processed"] += processed_delta
            self.metrics["database_operations"] += processed_delta
            self.metrics["active_devices"] = active_devices_count
            self.metrics["active_protocols"] = 1 if active_devices_count > 0 else 0
            self.metrics["uptime_seconds"] = int(time.time() - self._started_at)
            metrics_snapshot = dict(self.metrics)

        metric_items = [
            ("system.messages_processed", metrics_snapshot["messages_processed"]),
            ("system.messages_failed", metrics_snapshot["messages_failed"]),
            ("system.database_operations", metrics_snapshot["database_operations"]),
            ("system.active_protocols", metrics_snapshot["active_protocols"]),
            ("system.active_devices", metrics_snapshot["active_devices"]),
            ("system.uptime_seconds", metrics_snapshot["uptime_seconds"]),
            ("dte.active_projects", len(self.active_projects)),
            ("dte.active_units", len(self.active_units)),
            ("dte.active_device_targets", len(self.active_devices)),
        ]

        for metric_name, metric_value in metric_items:
            event = MonitoringEvent(
                event_type=EventType.METRIC,
                service="digital_twin_runtime",
                timestamp=datetime.now(timezone.utc),
                data={"metric": metric_name, "value": metric_value},
                severity="info",
            )
            self._publish(event)

    def get_state(self) -> Dict[str, Any]:
        active_resolved = self._resolve_active_device_ids()
        with self._lock:
            return {
                "running": self._running,
                "tick": self._tick,
                "admin_api_base_url": self.admin_api_base_url,
                "active_projects": sorted(list(self.active_projects)),
                "active_units": sorted(list(self.active_units)),
                "active_devices": sorted(list(self.active_devices)),
                "active_projects_count": len(self.active_projects),
                "active_units_count": len(self.active_units),
                "active_devices_count": len(self.active_devices),
                "resolved_devices_count": len(active_resolved),
                "metrics": dict(self.metrics),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

    def _loop(self) -> None:
        logger.info("🧠 DemoTwinRuntime iniciado")
        self._started_at = time.time()

        while not self._stop_event.is_set():
            try:
                now_monotonic = time.monotonic()
                if (now_monotonic - self._last_refresh_monotonic) >= self.hierarchy_refresh_seconds:
                    try:
                        self.refresh_hierarchy()
                    except Exception as exc:
                        logger.warning(f"⚠️  No se pudo refrescar jerarquía del runtime: {exc}")

                active_device_ids = self._resolve_active_device_ids()
                processed = 0

                with self._lock:
                    tick = self._tick
                    device_index_snapshot = dict(self._device_index)

                for device_id in sorted(active_device_ids):
                    payload = device_index_snapshot.get(device_id)
                    if not payload:
                        continue
                    self._publish_device_data(payload, tick)
                    processed += 1

                self._publish_metrics(processed, len(active_device_ids))

                with self._lock:
                    self._tick += 1

            except Exception as exc:
                logger.error(f"❌ Error en loop del runtime: {exc}")

            self._stop_event.wait(self.tick_seconds)

        logger.info("🛑 DemoTwinRuntime detenido")

    def start(self) -> None:
        if self._running:
            return
        self.refresh_hierarchy()
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="DemoTwinRuntime",
            daemon=True,
        )
        self._running = True
        self._thread.start()

    def stop(self) -> None:
        if not self._running:
            return
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._running = False


twin_runtime: Optional[DemoTwinRuntime] = None


def load_dashboard_config() -> Optional[RabbitMQConfig]:
    """Carga la configuración de RabbitMQ para el dashboard"""
    global dashboard_app_config
    try:
        config_path = os.getenv("DASHBOARD_CONFIG", "config.yaml")

        if os.path.exists(config_path):
            config = load_config(config_path)
            dashboard_app_config = config
            if config and hasattr(config, 'rabbitmq'):
                return config.rabbitmq

        dashboard_app_config = None
        return RabbitMQConfig(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            username=os.getenv("RABBITMQ_USERNAME", "guest"),
            password=os.getenv("RABBITMQ_PASSWORD", "guest"),
            virtual_host=os.getenv("RABBITMQ_VHOST", "/"),
            exchange=os.getenv("RABBITMQ_EXCHANGE", "iot_middleware"),
            queue_prefix=os.getenv("RABBITMQ_QUEUE_PREFIX", "iot"),
            enable_monitoring=True
        )
    except Exception as e:
        logger.error(f"❌ Error cargando configuración: {e}")
        return None


def load_dashboard_mqtt_config() -> Optional[MQTTConfig]:
    """Carga la configuración MQTT para publicar muestras del runtime."""
    try:
        if dashboard_app_config and hasattr(dashboard_app_config, "mqtt"):
            mqtt_cfg = dashboard_app_config.mqtt.model_copy(deep=True)
        else:
            broker = {
                "host": os.getenv("MQTT_HOST", "mosquitto"),
                "port": _safe_int(os.getenv("MQTT_PORT", "1883"), default=1883),
                "keepalive": _safe_int(os.getenv("MQTT_KEEPALIVE", "60"), default=60),
                "tls_enabled": False,
            }
            username = os.getenv("MQTT_USERNAME")
            password = os.getenv("MQTT_PASSWORD")
            if username and password:
                broker["username"] = username
                broker["password"] = password

            mqtt_cfg = MQTTConfig(
                broker=broker,
                topics={
                    "subscribe": ["iot/+/+/+/+"],
                    "publish": ["iot/+/+/+/+/+"],
                },
                qos=1,
                retain=False,
            )

        # El runtime del dashboard sólo publica muestras hacia MQTT.
        # No necesita suscribirse (evita spam de logs por mensajes entrantes).
        mqtt_cfg.topics["subscribe"] = []

        publish_topics = list(mqtt_cfg.topics.get("publish") or [])
        if "iot/+/+/+/+/+" not in publish_topics:
            publish_topics.append("iot/+/+/+/+/+")
        mqtt_cfg.topics["publish"] = publish_topics

        return mqtt_cfg
    except Exception as exc:
        logger.error(f"❌ Error cargando configuración MQTT del dashboard: {exc}")
        return None


def initialize_rabbitmq_consumer() -> bool:
    """Inicializa la conexión consumidora de RabbitMQ para dashboard."""
    global rabbitmq_client, rabbitmq_thread, rabbitmq_config

    try:
        rabbitmq_config = load_dashboard_config()
        if not rabbitmq_config or not rabbitmq_config.enable_monitoring:
            logger.warning("⚠️  RabbitMQ no está habilitado")
            return False

        logger.info(f"🔌 Conectando consumidor RabbitMQ: {rabbitmq_config.host}:{rabbitmq_config.port}")
        rabbitmq_client = create_rabbitmq_client(rabbitmq_config)

        if not rabbitmq_client.connect():
            logger.error("❌ No se pudo conectar consumidor RabbitMQ")
            return False

        rabbitmq_client.subscribe_to_events(
            event_types=list(EventType),
            callback=_on_rabbitmq_event
        )

        def consumer_worker():
            try:
                rabbitmq_client.start_consuming()
            except Exception as e:
                logger.error(f"❌ Error en consumidor RabbitMQ: {e}")

        rabbitmq_thread = threading.Thread(
            target=consumer_worker,
            name="RabbitMQConsumer",
            daemon=True
        )
        rabbitmq_thread.start()

        logger.info("✅ Consumidor RabbitMQ inicializado")
        return True

    except Exception as e:
        logger.error(f"❌ Error inicializando consumidor RabbitMQ: {e}")
        return False


def _on_rabbitmq_event(event: MonitoringEvent):
    """Callback cuando llega un evento de RabbitMQ"""
    try:
        message = event.to_dict()
        _record_flow_event(message)
        _broadcast_message(message)
    except Exception as e:
        logger.error(f"❌ Error procesando evento RabbitMQ: {e}")


def _broadcast_message(message: Dict[str, Any]):
    """Envía un mensaje a todas las conexiones WebSocket activas"""
    disconnected = []

    for connection in active_connections:
        try:
            if connection.client_state.name == "CONNECTED":
                asyncio.run(connection.send_json(message))
            else:
                disconnected.append(connection)
        except Exception:
            disconnected.append(connection)

    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)


def _get_runtime() -> DemoTwinRuntime:
    if twin_runtime is None:
        raise HTTPException(status_code=503, detail="Runtime de gemelo no inicializado")
    return twin_runtime


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _compact_error_message(text: str, limit: int = 220) -> str:
    normalized = (text or "").strip().replace("\n", " ").replace("\r", " ")
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def _http_request(
    *,
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[bytes] = None,
    timeout: float = 4.0,
) -> tuple[int, Dict[str, str], bytes]:
    req = urllib_request.Request(
        url=url,
        method=method,
        headers=headers or {},
        data=payload,
    )
    with urllib_request.urlopen(req, timeout=timeout) as response:
        return response.getcode(), dict(response.headers.items()), response.read()


def _http_get_json(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 4.0,
) -> Any:
    _, _, body = _http_request(url=url, method="GET", headers=headers, timeout=timeout)
    text = body.decode("utf-8", errors="ignore")
    return json.loads(text) if text else {}


def _resolve_rabbitmq_management_settings() -> Dict[str, Any]:
    host = (
        os.getenv("RABBITMQ_MANAGEMENT_HOST")
        or os.getenv("RABBITMQ_MGMT_HOST")
        or os.getenv("RABBITMQ_HOST")
        or (rabbitmq_config.host if rabbitmq_config else None)
        or "rabbitmq"
    )
    port = _safe_int(
        os.getenv("RABBITMQ_MANAGEMENT_PORT") or os.getenv("RABBITMQ_MGMT_PORT") or "15672",
        default=15672,
    )
    scheme = os.getenv("RABBITMQ_MANAGEMENT_SCHEME", "http")
    base_url = (os.getenv("RABBITMQ_MANAGEMENT_URL") or f"{scheme}://{host}:{port}").rstrip("/")
    username = os.getenv("RABBITMQ_USERNAME") or (rabbitmq_config.username if rabbitmq_config else "guest")
    password = os.getenv("RABBITMQ_PASSWORD") or (rabbitmq_config.password if rabbitmq_config else "guest")
    vhost = os.getenv("RABBITMQ_VHOST") or (rabbitmq_config.virtual_host if rabbitmq_config else "/")
    return {
        "base_url": base_url,
        "username": username,
        "password": password,
        "vhost": vhost,
    }


def _resolve_influx_settings() -> Dict[str, Optional[str]]:
    influx_cfg = getattr(dashboard_app_config, "influxdb", None) if dashboard_app_config else None
    url = os.getenv("INFLUX_URL") or (getattr(influx_cfg, "url", None) if influx_cfg else None) or "http://influxdb:8086"
    token = os.getenv("INFLUX_TOKEN") or (getattr(influx_cfg, "token", None) if influx_cfg else None)
    org = os.getenv("INFLUX_ORG") or (getattr(influx_cfg, "org", None) if influx_cfg else None)
    bucket = os.getenv("INFLUX_BUCKET") or (getattr(influx_cfg, "bucket", None) if influx_cfg else None)
    return {
        "url": (url or "").rstrip("/"),
        "token": token,
        "org": org,
        "bucket": bucket,
    }


def _parse_influx_count_csv(csv_text: str) -> int:
    total = 0.0
    value_index: Optional[int] = None
    reader = csv.reader(io.StringIO(csv_text))

    for row in reader:
        if not row:
            continue
        if row[0].startswith("#"):
            continue
        if "_value" in row:
            value_index = row.index("_value")
            continue
        if value_index is None or value_index >= len(row):
            continue

        raw = (row[value_index] or "").strip()
        if not raw:
            continue
        try:
            total += float(raw)
        except ValueError:
            continue

    return int(total)


def _parse_datetime_utc(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _record_flow_event(message: Dict[str, Any]) -> None:
    event_type = str(message.get("event_type") or "").lower()
    if event_type != EventType.DATA.value:
        return

    payload = message.get("data") if isinstance(message.get("data"), dict) else {}
    if not payload:
        return

    timestamp = _parse_datetime_utc(payload.get("timestamp") or message.get("timestamp"))
    if not timestamp:
        timestamp = datetime.now(timezone.utc)

    entry = {
        "timestamp": timestamp,
        "project_id": str(payload.get("project_id")) if payload.get("project_id") else None,
        "unit_id": str(payload.get("unit_id")) if payload.get("unit_id") else None,
        "device_id": str(payload.get("device_id")) if payload.get("device_id") else None,
        "device_ref_id": str(payload.get("device_ref_id")) if payload.get("device_ref_id") else None,
    }
    with flow_events_lock:
        flow_events.append(entry)


def _build_minute_slots(minutes: int) -> List[datetime]:
    safe_minutes = max(5, min(180, _safe_int(minutes, 15)))
    end_slot = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start_slot = end_slot - timedelta(minutes=safe_minutes - 1)
    return [start_slot + timedelta(minutes=idx) for idx in range(safe_minutes)]


def _entry_matches_scope(entry: Dict[str, Any], scope: str, scope_id: str, scope_ref_id: Optional[str]) -> bool:
    if scope == "project":
        return entry.get("project_id") == scope_id
    if scope == "unit":
        return entry.get("unit_id") == scope_id
    if scope == "device":
        if entry.get("device_id") == scope_id:
            return True
        if scope_ref_id and entry.get("device_ref_id") == scope_ref_id:
            return True
        return entry.get("device_ref_id") == scope_id
    return False


def _build_rabbit_count_map(
    *,
    scope: str,
    scope_id: str,
    scope_ref_id: Optional[str],
    slots: List[datetime],
) -> Dict[datetime, int]:
    counts: Dict[datetime, int] = {slot: 0 for slot in slots}
    if not slots:
        return counts
    start = slots[0]
    end = slots[-1] + timedelta(minutes=1)

    with flow_events_lock:
        snapshot = list(flow_events)

    for entry in snapshot:
        ts = entry.get("timestamp")
        if not isinstance(ts, datetime):
            continue
        if ts < start or ts >= end:
            continue
        if not _entry_matches_scope(entry, scope, scope_id, scope_ref_id):
            continue
        bucket = ts.replace(second=0, microsecond=0)
        if bucket in counts:
            counts[bucket] += 1
    return counts


def _parse_influx_series_csv(csv_text: str) -> Dict[datetime, int]:
    series: Dict[datetime, int] = {}
    time_index: Optional[int] = None
    value_index: Optional[int] = None
    reader = csv.reader(io.StringIO(csv_text))

    for row in reader:
        if not row or row[0].startswith("#"):
            continue
        if "_time" in row and "_value" in row:
            time_index = row.index("_time")
            value_index = row.index("_value")
            continue
        if time_index is None or value_index is None:
            continue
        if time_index >= len(row) or value_index >= len(row):
            continue

        ts = _parse_datetime_utc((row[time_index] or "").strip())
        if not ts:
            continue
        raw_value = (row[value_index] or "").strip()
        if not raw_value:
            continue
        try:
            value = int(float(raw_value))
        except ValueError:
            continue

        bucket = ts.replace(second=0, microsecond=0)
        series[bucket] = series.get(bucket, 0) + value
    return series


def _escape_flux_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _query_influx_count_map(
    *,
    scope: str,
    scope_id: str,
    scope_ref_id: Optional[str],
    slots: List[datetime],
    range_start: Optional[datetime] = None,
) -> tuple[Dict[datetime, int], str, Optional[str]]:
    settings = _resolve_influx_settings()
    base_url = settings["url"] or "http://influxdb:8086"
    token = settings["token"]
    org = settings["org"]
    bucket = settings["bucket"]

    if not token or not org or not bucket:
        return {}, "skipped_missing_config", "Faltan parámetros Influx (token/org/bucket)"

    minutes = len(slots) if slots else 15
    if range_start:
        range_start_utc = range_start.astimezone(timezone.utc).replace(microsecond=0)
        range_start_expr = f'time(v: "{range_start_utc.isoformat().replace("+00:00", "Z")}")'
    else:
        range_start_expr = f"-{minutes}m"
    bucket_escaped = _escape_flux_string(bucket)
    scope_id_escaped = _escape_flux_string(scope_id)
    scope_ref_id_escaped = _escape_flux_string(scope_ref_id) if scope_ref_id else ""

    if scope == "project":
        scope_filter = f'|> filter(fn: (r) => r.project_id == "{scope_id_escaped}") '
    elif scope == "unit":
        scope_filter = f'|> filter(fn: (r) => r.unit_id == "{scope_id_escaped}") '
    else:
        if scope_ref_id_escaped:
            scope_filter = (
                f'|> filter(fn: (r) => '
                f'r.device_ref_id == "{scope_ref_id_escaped}" or r.device_id == "{scope_ref_id_escaped}") '
            )
        else:
            scope_filter = (
                f'|> filter(fn: (r) => '
                f'r.device_ref_id == "{scope_id_escaped}" or r.device_id == "{scope_id_escaped}") '
            )

    flux_query = (
        f'from(bucket: "{bucket_escaped}") '
        f'|> range(start: {range_start_expr}) '
        '|> filter(fn: (r) => r._measurement == "sensor_data") '
        '|> filter(fn: (r) => r._field == "value_num" or r._field == "value") '
        + scope_filter +
        '|> aggregateWindow(every: 1m, fn: count, createEmpty: true) '
        '|> group(columns: ["_time"]) '
        '|> sum(column: "_value") '
        '|> group() '
        '|> sort(columns: ["_time"])'
    )

    try:
        query_url = f"{base_url}/api/v2/query?org={urllib_parse.quote(org)}"
        _, _, raw_csv = _http_request(
            url=query_url,
            method="POST",
            headers={
                "Authorization": f"Token {token}",
                "Accept": "application/csv",
                "Content-Type": "application/vnd.flux",
            },
            payload=flux_query.encode("utf-8"),
            timeout=6.0,
        )
        return _parse_influx_series_csv(raw_csv.decode("utf-8", errors="ignore")), "ok", None
    except urllib_error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        return {}, "error", _compact_error_message(f"HTTP {exc.code} Influx query: {exc.reason}. {body}")
    except urllib_error.URLError as exc:
        return {}, "error", _compact_error_message(f"No se pudo consultar InfluxDB: {exc}")
    except Exception as exc:
        return {}, "error", _compact_error_message(str(exc))


def _fetch_rabbitmq_infra_status() -> Dict[str, Any]:
    settings = _resolve_rabbitmq_management_settings()
    base_url = settings["base_url"]
    vhost_encoded = urllib_parse.quote(settings["vhost"] or "/", safe="")
    basic_token = base64.b64encode(
        f"{settings['username']}:{settings['password']}".encode("utf-8")
    ).decode("ascii")
    headers = {
        "Accept": "application/json",
        "Authorization": f"Basic {basic_token}",
    }

    payload: Dict[str, Any] = {
        "status": "unknown",
        "management_url": base_url,
        "amqp_connected": bool(rabbitmq_client and rabbitmq_client.connected),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        overview = _http_get_json(f"{base_url}/api/overview", headers=headers, timeout=4.0)
        queues_raw = _http_get_json(f"{base_url}/api/queues/{vhost_encoded}", headers=headers, timeout=4.0)
        queues = queues_raw if isinstance(queues_raw, list) else []

        object_totals = overview.get("object_totals") or {}
        queue_totals = overview.get("queue_totals") or {}
        message_stats = overview.get("message_stats") or {}

        queues_active = [
            item for item in queues
            if _safe_int(item.get("consumers"), 0) > 0
        ]
        pending_total = sum(_safe_int(item.get("messages"), 0) for item in queues)
        pending_active = sum(_safe_int(item.get("messages"), 0) for item in queues_active)
        ready_total = sum(_safe_int(item.get("messages_ready"), 0) for item in queues)
        ready_active = sum(_safe_int(item.get("messages_ready"), 0) for item in queues_active)
        unack_total = sum(_safe_int(item.get("messages_unacknowledged"), 0) for item in queues)
        unack_active = sum(_safe_int(item.get("messages_unacknowledged"), 0) for item in queues_active)

        top_queues = []
        queues_for_top = queues_active if queues_active else queues
        sorted_queues = sorted(
            queues_for_top,
            key=lambda item: (_safe_int(item.get("messages"), 0), str(item.get("name") or "")),
            reverse=True,
        )
        for queue_item in sorted_queues[:5]:
            top_queues.append(
                {
                    "name": queue_item.get("name"),
                    "messages": _safe_int(queue_item.get("messages"), 0),
                    "messages_ready": _safe_int(queue_item.get("messages_ready"), 0),
                    "consumers": _safe_int(queue_item.get("consumers"), 0),
                }
            )

        payload.update(
            {
                "status": "up",
                "cluster_name": overview.get("cluster_name"),
                "rabbitmq_version": overview.get("rabbitmq_version"),
                "connections": _safe_int(object_totals.get("connections"), 0),
                "channels": _safe_int(object_totals.get("channels"), 0),
                "consumers": _safe_int(object_totals.get("consumers"), 0),
                "queues": _safe_int(object_totals.get("queues"), len(queues)),
                "queues_total": len(queues),
                "queues_active": len(queues_active),
                "messages_pending": pending_active,
                "messages_pending_active": pending_active,
                "messages_pending_total": _safe_int(queue_totals.get("messages"), pending_total),
                "messages_ready": ready_active,
                "messages_ready_active": ready_active,
                "messages_ready_total": _safe_int(queue_totals.get("messages_ready"), ready_total),
                "messages_unacknowledged": unack_active,
                "messages_unacknowledged_active": unack_active,
                "messages_unacknowledged_total": _safe_int(queue_totals.get("messages_unacknowledged"), unack_total),
                "publish_rate": round(_safe_float((message_stats.get("publish_details") or {}).get("rate"), 0.0), 2),
                "deliver_rate": round(_safe_float((message_stats.get("deliver_get_details") or {}).get("rate"), 0.0), 2),
                "ack_rate": round(_safe_float((message_stats.get("ack_details") or {}).get("rate"), 0.0), 2),
                "top_queues": top_queues,
            }
        )
        return payload

    except urllib_error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        payload.update(
            {
                "status": "error",
                "error": _compact_error_message(
                    f"HTTP {exc.code} al consultar RabbitMQ Management: {exc.reason}. {body}"
                ),
            }
        )
        return payload
    except urllib_error.URLError as exc:
        payload.update(
            {
                "status": "error",
                "error": _compact_error_message(f"No se pudo conectar a RabbitMQ Management: {exc}"),
            }
        )
        return payload
    except Exception as exc:
        payload.update(
            {
                "status": "error",
                "error": _compact_error_message(str(exc)),
            }
        )
        return payload


def _fetch_influx_infra_status() -> Dict[str, Any]:
    settings = _resolve_influx_settings()
    base_url = settings["url"] or "http://influxdb:8086"
    token = settings["token"]
    org = settings["org"]
    bucket = settings["bucket"]

    payload: Dict[str, Any] = {
        "status": "unknown",
        "url": base_url,
        "org": org,
        "bucket": bucket,
        "token_configured": bool(token),
        "health_status": "unknown",
        "activity": {
            "points_last_5m": None,
            "query_status": "not_run",
            "error": None,
        },
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        health = _http_get_json(
            f"{base_url}/health",
            headers={"Accept": "application/json"},
            timeout=4.0,
        )
        health_status = str(health.get("status") or health.get("state") or "unknown").lower()
        payload["health"] = health
        payload["health_status"] = health_status
        payload["status"] = "up" if health_status in {"pass", "ready", "healthy", "ok"} else "degraded"
    except urllib_error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        payload.update(
            {
                "status": "error",
                "error": _compact_error_message(
                    f"HTTP {exc.code} al consultar health de InfluxDB: {exc.reason}. {body}"
                ),
            }
        )
        return payload
    except urllib_error.URLError as exc:
        payload.update(
            {
                "status": "error",
                "error": _compact_error_message(f"No se pudo conectar a InfluxDB: {exc}"),
            }
        )
        return payload
    except Exception as exc:
        payload.update(
            {
                "status": "error",
                "error": _compact_error_message(str(exc)),
            }
        )
        return payload

    if not token or not org or not bucket:
        missing = []
        if not token:
            missing.append("token")
        if not org:
            missing.append("org")
        if not bucket:
            missing.append("bucket")
        payload["activity"]["query_status"] = "skipped_missing_config"
        payload["activity"]["error"] = f"Faltan parámetros para query: {', '.join(missing)}"
        return payload

    try:
        bucket_escaped = bucket.replace("\\", "\\\\").replace('"', '\\"')
        flux_query = (
            f'from(bucket: "{bucket_escaped}") '
            '|> range(start: -5m) '
            '|> filter(fn: (r) => r._measurement == "sensor_data") '
            '|> filter(fn: (r) => r._field == "value_num" or r._field == "value") '
            '|> count() '
            '|> group() '
            '|> sum(column: "_value")'
        )
        query_url = f"{base_url}/api/v2/query?org={urllib_parse.quote(org)}"
        _, _, raw_csv = _http_request(
            url=query_url,
            method="POST",
            headers={
                "Authorization": f"Token {token}",
                "Accept": "application/csv",
                "Content-Type": "application/vnd.flux",
            },
            payload=flux_query.encode("utf-8"),
            timeout=6.0,
        )
        points_last_5m = _parse_influx_count_csv(raw_csv.decode("utf-8", errors="ignore"))
        payload["activity"]["points_last_5m"] = points_last_5m
        payload["activity"]["query_status"] = "ok"
        return payload
    except urllib_error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        payload["activity"]["query_status"] = "error"
        payload["activity"]["error"] = _compact_error_message(
            f"HTTP {exc.code} al ejecutar query InfluxDB: {exc.reason}. {body}"
        )
        return payload
    except urllib_error.URLError as exc:
        payload["activity"]["query_status"] = "error"
        payload["activity"]["error"] = _compact_error_message(
            f"No se pudo consultar actividad de InfluxDB: {exc}"
        )
        return payload
    except Exception as exc:
        payload["activity"]["query_status"] = "error"
        payload["activity"]["error"] = _compact_error_message(str(exc))
        return payload


def _compute_infra_global_status(rabbit_status: str, influx_status: str) -> str:
    statuses = {rabbit_status, influx_status}
    if statuses == {"up"}:
        return "up"
    if "error" in statuses:
        return "error"
    if "degraded" in statuses or "unknown" in statuses:
        return "degraded"
    return "unknown"


@app.on_event("startup")
async def startup_event():
    """Evento ejecutado al iniciar la aplicación"""
    global runtime_publisher_client, runtime_mqtt_client, twin_runtime
    logger.info("🚀 Iniciando Dashboard de Monitoreo...")

    if not initialize_rabbitmq_consumer():
        logger.warning("⚠️  Dashboard iniciado sin consumidor RabbitMQ (modo limitado)")
        return

    try:
        if rabbitmq_config is None:
            logger.warning("⚠️  RabbitMQ config no disponible para runtime")
            return

        runtime_publisher_client = create_rabbitmq_client(rabbitmq_config)
        if not runtime_publisher_client.connect():
            logger.warning("⚠️  Runtime publisher sin conexión a RabbitMQ")

        mqtt_config = load_dashboard_mqtt_config()
        if mqtt_config:
            runtime_mqtt_client = create_mqtt_client(
                mqtt_config,
                client_id=f"dte_dashboard_runtime_{int(time.time())}",
            )
            if runtime_mqtt_client.connect():
                logger.info("✅ Runtime publisher MQTT conectado")
            else:
                logger.warning("⚠️  Runtime publisher MQTT sin conexión")
        else:
            logger.warning("⚠️  No se pudo cargar configuración MQTT para runtime")

        admin_api_base_url = os.getenv("ADMIN_API_BASE_URL", "http://iotmw-admin:9000/api")
        twin_runtime = DemoTwinRuntime(
            admin_api_base_url=admin_api_base_url,
            publisher_client=runtime_publisher_client,
            mqtt_client=runtime_mqtt_client,
            tick_seconds=float(os.getenv("DTE_DEMO_TICK_SECONDS", "2.0")),
            hierarchy_refresh_seconds=float(os.getenv("DTE_DEMO_HIERARCHY_REFRESH_SECONDS", "20.0")),
        )
        twin_runtime.start()
        logger.info("✅ Runtime de gemelo inicializado")

    except Exception as exc:
        logger.error(f"❌ Error inicializando runtime de gemelo: {exc}")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento ejecutado al detener la aplicación"""
    logger.info("🛑 Deteniendo Dashboard de Monitoreo...")

    if twin_runtime:
        try:
            twin_runtime.stop()
        except Exception as e:
            logger.error(f"❌ Error deteniendo runtime de gemelo: {e}")

    if runtime_publisher_client:
        try:
            runtime_publisher_client.disconnect()
        except Exception as e:
            logger.error(f"❌ Error desconectando runtime publisher: {e}")

    if runtime_mqtt_client:
        try:
            runtime_mqtt_client.disconnect()
        except Exception as e:
            logger.error(f"❌ Error desconectando runtime publisher MQTT: {e}")

    if rabbitmq_client:
        try:
            rabbitmq_client.stop_consuming()
            rabbitmq_client.disconnect()
            logger.info("✅ RabbitMQ desconectado")
        except Exception as e:
            logger.error(f"❌ Error desconectando RabbitMQ: {e}")


@app.get("/api/runtime/hierarchy")
async def runtime_hierarchy():
    runtime = _get_runtime()
    return runtime.get_hierarchy()


@app.get("/api/runtime/state")
async def runtime_state():
    runtime = _get_runtime()
    return runtime.get_state()


@app.post("/api/runtime/refresh")
async def runtime_refresh():
    runtime = _get_runtime()
    try:
        return runtime.refresh_hierarchy()
    except urllib_error.URLError as exc:
        raise HTTPException(status_code=502, detail=f"No se pudo consultar admin API: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/runtime/start/project/{project_id}")
async def runtime_start_project(project_id: str):
    runtime = _get_runtime()
    try:
        state = runtime.start_project(project_id)
        return {"ok": True, "message": f"Proyecto {project_id} iniciado", "state": state}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/runtime/stop/project/{project_id}")
async def runtime_stop_project(project_id: str):
    runtime = _get_runtime()
    try:
        state = runtime.stop_project(project_id)
        return {"ok": True, "message": f"Proyecto {project_id} detenido", "state": state}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/runtime/start/unidad/{unidad_id}")
async def runtime_start_unit(unidad_id: str):
    runtime = _get_runtime()
    try:
        state = runtime.start_unit(unidad_id)
        return {"ok": True, "message": f"Sector {unidad_id} iniciado", "state": state}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/runtime/stop/unidad/{unidad_id}")
async def runtime_stop_unit(unidad_id: str):
    runtime = _get_runtime()
    try:
        state = runtime.stop_unit(unidad_id)
        return {"ok": True, "message": f"Sector {unidad_id} detenido", "state": state}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/runtime/start/dispositivo/{dispositivo_id}")
async def runtime_start_device(dispositivo_id: str):
    runtime = _get_runtime()
    try:
        state = runtime.start_device(dispositivo_id)
        return {"ok": True, "message": f"Asset {dispositivo_id} iniciado", "state": state}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/runtime/stop/dispositivo/{dispositivo_id}")
async def runtime_stop_device(dispositivo_id: str):
    runtime = _get_runtime()
    try:
        state = runtime.stop_device(dispositivo_id)
        return {"ok": True, "message": f"Asset {dispositivo_id} detenido", "state": state}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/infra/status")
def infra_status():
    rabbit = _fetch_rabbitmq_infra_status()
    influx = _fetch_influx_infra_status()
    return {
        "status": _compute_infra_global_status(rabbit.get("status", "unknown"), influx.get("status", "unknown")),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "rabbitmq": rabbit,
        "influxdb": influx,
    }


@app.get("/api/analytics/flow")
def analytics_flow(scope: str, scope_id: str, minutes: int = 15, scope_ref_id: Optional[str] = None):
    normalized_scope = (scope or "").strip().lower()
    if normalized_scope not in {"project", "unit", "device"}:
        raise HTTPException(status_code=400, detail="scope debe ser project, unit o device")

    normalized_scope_id = (scope_id or "").strip()
    if not normalized_scope_id:
        raise HTTPException(status_code=400, detail="scope_id es obligatorio")

    slots = _build_minute_slots(minutes)
    rabbit_map = _build_rabbit_count_map(
        scope=normalized_scope,
        scope_id=normalized_scope_id,
        scope_ref_id=(scope_ref_id or "").strip() or None,
        slots=slots,
    )
    rabbit_active_slots = [slot for slot in slots if rabbit_map.get(slot, 0) > 0]
    influx_range_start = rabbit_active_slots[0] if rabbit_active_slots else slots[0]
    influx_map, influx_query_status, influx_query_error = _query_influx_count_map(
        scope=normalized_scope,
        scope_id=normalized_scope_id,
        scope_ref_id=(scope_ref_id or "").strip() or None,
        slots=slots,
        range_start=influx_range_start,
    )

    series: List[Dict[str, Any]] = []
    rabbit_total = 0
    influx_total = 0
    for slot in slots:
        rabbit_value = rabbit_map.get(slot, 0)
        influx_value = influx_map.get(slot, 0)
        rabbit_total += rabbit_value
        influx_total += influx_value
        series.append(
            {
                "time": slot.isoformat(),
                "rabbitmq": rabbit_value,
                "influxdb": influx_value,
            }
        )

    return {
        "scope": normalized_scope,
        "scope_id": normalized_scope_id,
        "scope_ref_id": (scope_ref_id or "").strip() or None,
        "minutes": len(slots),
        "series": series,
        "totals": {
            "rabbitmq": rabbit_total,
            "influxdb": influx_total,
            "delta": rabbit_total - influx_total,
        },
        "query_status": {
            "rabbitmq": "ok",
            "influxdb": influx_query_status,
            "influxdb_error": influx_query_error,
        },
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/")
async def dashboard_page():
    """Página HTML del dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IoT Middleware - Dashboard de Monitoreo y Control</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%);
                color: #333;
                padding: 20px;
                min-height: 100vh;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
            }

            .header {
                background: white;
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 20px;
                box-shadow: 0 10px 24px rgba(0,0,0,0.16);
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 12px;
            }

            .header h1 {
                color: #1d4ed8;
                margin: 0;
                font-size: 1.6rem;
            }

            .status {
                display: inline-block;
                padding: 8px 20px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 14px;
            }

            .status.connected {
                background: #22c55e;
                color: white;
            }

            .status.disconnected {
                background: #ef4444;
                color: white;
            }

            .controls-panel {
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 10px 24px rgba(0,0,0,0.16);
            }

            .controls-panel h2 {
                color: #1d4ed8;
                font-size: 1.25rem;
            }

            .section-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 10px;
                margin-bottom: 12px;
            }

            .section-toggle {
                border: none;
                border-radius: 999px;
                background: #e2e8f0;
                color: #0f172a;
                padding: 6px 12px;
                font-size: 0.75rem;
                font-weight: 700;
                letter-spacing: 0.02em;
                cursor: pointer;
                text-transform: uppercase;
            }

            .section-panel.section-collapsed .section-body {
                display: none;
            }

            .section-panel.section-collapsed .section-toggle {
                background: #bfdbfe;
                color: #1e3a8a;
            }

            .runtime-summary {
                background: #eff6ff;
                border: 1px solid #bfdbfe;
                padding: 10px 12px;
                border-radius: 8px;
                margin-bottom: 12px;
                color: #1e3a8a;
                font-size: 0.95rem;
            }

            .runtime-message {
                font-size: 0.88rem;
                color: #334155;
                margin-bottom: 14px;
            }

            .control-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 14px;
            }

            .control-card {
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 12px;
                background: #f8fafc;
            }

            .control-card h3 {
                font-size: 0.95rem;
                color: #0f172a;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }

            .control-select {
                width: 100%;
                padding: 8px 10px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                margin-bottom: 10px;
                background: white;
            }

            .control-actions {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }

            .btn {
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
                cursor: pointer;
            }

            .btn-start {
                background: #16a34a;
                color: white;
            }

            .btn-stop {
                background: #dc2626;
                color: white;
            }

            .btn-refresh {
                background: #1d4ed8;
                color: white;
            }

            .infra-panel {
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 10px 24px rgba(0,0,0,0.16);
            }

            .infra-panel h2 {
                color: #1d4ed8;
                font-size: 1.2rem;
            }

            .infra-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 14px;
            }

            .infra-card {
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 12px;
                background: #f8fafc;
            }

            .infra-card-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 8px;
                gap: 8px;
            }

            .infra-card-header h3 {
                font-size: 0.96rem;
                color: #0f172a;
            }

            .infra-pill {
                border-radius: 999px;
                padding: 4px 10px;
                font-size: 0.76rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.03em;
            }

            .infra-up {
                background: #dcfce7;
                color: #166534;
            }

            .infra-degraded {
                background: #fef3c7;
                color: #92400e;
            }

            .infra-error {
                background: #fee2e2;
                color: #991b1b;
            }

            .infra-unknown {
                background: #e2e8f0;
                color: #334155;
            }

            .infra-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 8px;
                padding: 5px 0;
                border-bottom: 1px dashed #e2e8f0;
                font-size: 0.9rem;
            }

            .infra-row:last-child {
                border-bottom: none;
            }

            .infra-row span {
                color: #475569;
            }

            .infra-row strong {
                color: #0f172a;
                font-size: 0.9rem;
                text-align: right;
                max-width: 60%;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .infra-message {
                margin-top: 12px;
                font-size: 0.84rem;
                color: #334155;
            }

            .analytics-panel {
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 10px 24px rgba(0,0,0,0.16);
            }

            .analytics-panel h2 {
                color: #1d4ed8;
                font-size: 1.2rem;
            }

            .analytics-note {
                color: #475569;
                font-size: 0.9rem;
                margin-bottom: 14px;
            }

            .plugin-toolbar {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 10px;
                flex-wrap: wrap;
            }

            .plugin-label {
                font-size: 0.78rem;
                font-weight: 700;
                color: #334155;
                text-transform: uppercase;
                letter-spacing: 0.03em;
            }

            .plugin-select {
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 5px 9px;
                font-size: 0.82rem;
                background: white;
                color: #0f172a;
            }

            .plugin-hint {
                font-size: 0.75rem;
                color: #64748b;
            }

            .analytics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 14px;
            }

            .analytics-card {
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 12px;
                background: #f8fafc;
            }

            .analytics-card h3 {
                font-size: 0.95rem;
                color: #0f172a;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }

            .analytics-meta {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 8px;
                margin-bottom: 10px;
                font-size: 0.82rem;
                color: #334155;
            }

            .chart-wrap {
                position: relative;
                height: 190px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background: white;
                padding: 8px;
            }

            .chart-wrap canvas {
                width: 100%;
                height: 100%;
                display: block;
            }

            .chart-legend {
                display: flex;
                gap: 12px;
                margin-top: 10px;
                font-size: 0.78rem;
                color: #475569;
            }

            .chart-legend span::before {
                content: "";
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 999px;
                margin-right: 6px;
                vertical-align: middle;
            }

            .legend-rabbit::before {
                background: #2563eb;
            }

            .legend-influx::before {
                background: #16a34a;
            }

            .chart-empty {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100%;
                color: #94a3b8;
                font-size: 0.86rem;
            }

            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 16px;
            }

            .metrics-panel {
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 10px 24px rgba(0,0,0,0.14);
            }

            .metrics-panel h2 {
                color: #1d4ed8;
                font-size: 1.2rem;
            }

            .metric-card {
                background: white;
                padding: 18px;
                border-radius: 12px;
                box-shadow: 0 10px 24px rgba(0,0,0,0.14);
                transition: transform 0.2s, box-shadow 0.2s;
            }

            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 14px 30px rgba(0,0,0,0.18);
            }

            .metric-card h3 {
                color: #64748b;
                font-size: 12px;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 0.06em;
            }

            .metric-value {
                font-size: 30px;
                font-weight: 700;
                color: #1d4ed8;
                margin-bottom: 4px;
            }

            .metric-progress {
                height: 10px;
                border-radius: 999px;
                background: #e2e8f0;
                overflow: hidden;
                margin: 6px 0 8px;
                display: none;
            }

            .metric-progress-fill {
                height: 100%;
                width: 0%;
                background: linear-gradient(90deg, #2563eb 0%, #22c55e 100%);
                transition: width 0.25s ease;
            }

            .metric-spark {
                height: 56px;
                margin: 6px 0 8px;
                display: none;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background: #f8fafc;
                padding: 4px;
            }

            .metric-spark canvas {
                width: 100%;
                height: 100%;
                display: block;
            }

            .metric-card[data-plugin="progress"] .metric-progress {
                display: block;
            }

            .metric-card[data-plugin="sparkline"] .metric-spark {
                display: block;
            }

            .metric-change {
                font-size: 12px;
                color: #64748b;
            }

            .events-panel {
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 10px 24px rgba(0,0,0,0.14);
                max-height: 560px;
                overflow-y: auto;
            }

            .events-panel h2 {
                color: #1d4ed8;
                font-size: 1.25rem;
            }

            .event-item {
                padding: 12px;
                border-left: 4px solid #1d4ed8;
                margin-bottom: 10px;
                background: #f8fafc;
                border-radius: 6px;
            }

            .event-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 6px;
            }

            .event-type {
                font-weight: bold;
                color: #1d4ed8;
                font-size: 13px;
                text-transform: uppercase;
            }

            .event-time {
                color: #64748b;
                font-size: 12px;
            }

            .event-service {
                color: #475569;
                font-size: 12px;
                margin-bottom: 4px;
            }

            .event-data {
                margin-top: 6px;
                font-size: 12px;
                color: #334155;
                font-family: 'Courier New', monospace;
                background: white;
                padding: 8px;
                border-radius: 4px;
                overflow-x: auto;
            }

            .severity-info { border-left-color: #0ea5e9; }
            .severity-warning { border-left-color: #f59e0b; }
            .severity-error { border-left-color: #ef4444; }
            .severity-critical { border-left-color: #7c3aed; }

            .empty-state {
                text-align: center;
                padding: 30px;
                color: #94a3b8;
            }

            @media (max-width: 780px) {
                .header {
                    flex-direction: column;
                    align-items: flex-start;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Dashboard de Monitoreo + Control</h1>
                <span id="connectionStatus" class="status disconnected">Desconectado</span>
            </div>

            <div class="controls-panel section-panel" data-section-key="control">
                <div class="section-header">
                    <h2>🎛️ Control de Ejecución</h2>
                    <button type="button" class="section-toggle" data-action="toggle-section">Colapsar</button>
                </div>
                <div class="section-body">
                    <div id="runtimeSummary" class="runtime-summary">Cargando estado del runtime...</div>
                    <div id="runtimeMessage" class="runtime-message"></div>
                    <div style="margin-bottom: 10px;">
                        <button class="btn btn-refresh" onclick="manualRefresh()">Refrescar jerarquía</button>
                    </div>
                    <div class="control-grid">
                        <div class="control-card">
                            <h3>Proyecto</h3>
                            <select id="projectSelect" class="control-select"></select>
                            <div class="control-actions">
                                <button class="btn btn-start" onclick="controlScope('project', 'start')">Iniciar Proyecto</button>
                                <button class="btn btn-stop" onclick="controlScope('project', 'stop')">Detener Proyecto</button>
                            </div>
                        </div>

                        <div class="control-card">
                            <h3>Sector</h3>
                            <select id="unitSelect" class="control-select"></select>
                            <div class="control-actions">
                                <button class="btn btn-start" onclick="controlScope('unit', 'start')">Iniciar Sector</button>
                                <button class="btn btn-stop" onclick="controlScope('unit', 'stop')">Detener Sector</button>
                            </div>
                        </div>

                        <div class="control-card">
                            <h3>Asset</h3>
                            <select id="deviceSelect" class="control-select"></select>
                            <div class="control-actions">
                                <button class="btn btn-start" onclick="controlScope('device', 'start')">Iniciar Asset</button>
                                <button class="btn btn-stop" onclick="controlScope('device', 'stop')">Detener Asset</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="infra-panel section-panel" data-section-key="infra">
                <div class="section-header">
                    <h2>🔎 Control Cruzado Infra (Broker + InfluxDB)</h2>
                    <button type="button" class="section-toggle" data-action="toggle-section">Colapsar</button>
                </div>
                <div class="section-body">
                    <div class="infra-grid">
                        <div class="infra-card">
                            <div class="infra-card-header">
                                <h3>RabbitMQ Broker</h3>
                                <span id="rabbitStatusPill" class="infra-pill infra-unknown">UNKNOWN</span>
                            </div>
                            <div class="infra-row"><span>Conexiones</span><strong id="rabbitConnections">-</strong></div>
                            <div class="infra-row"><span>Canales</span><strong id="rabbitChannels">-</strong></div>
                            <div class="infra-row"><span>Colas (tot/act)</span><strong id="rabbitQueues">-</strong></div>
                            <div class="infra-row"><span>Pendientes activas</span><strong id="rabbitPending">-</strong></div>
                            <div class="infra-row"><span>Pendientes totales</span><strong id="rabbitPendingTotal">-</strong></div>
                            <div class="infra-row"><span>Publish/s</span><strong id="rabbitPublishRate">-</strong></div>
                            <div class="infra-row"><span>Deliver/s</span><strong id="rabbitDeliverRate">-</strong></div>
                            <div class="infra-row"><span>Top queue</span><strong id="rabbitTopQueue">-</strong></div>
                            <div class="infra-row"><span>Error</span><strong id="rabbitError">-</strong></div>
                        </div>
                        <div class="infra-card">
                            <div class="infra-card-header">
                                <h3>InfluxDB</h3>
                                <span id="influxStatusPill" class="infra-pill infra-unknown">UNKNOWN</span>
                            </div>
                            <div class="infra-row"><span>Health</span><strong id="influxHealth">-</strong></div>
                            <div class="infra-row"><span>Org</span><strong id="influxOrg">-</strong></div>
                            <div class="infra-row"><span>Bucket</span><strong id="influxBucket">-</strong></div>
                            <div class="infra-row"><span>Muestras (últ. 5m)</span><strong id="influxPoints5m">-</strong></div>
                            <div class="infra-row"><span>Estado query</span><strong id="influxQueryStatus">-</strong></div>
                            <div class="infra-row"><span>Error query</span><strong id="influxQueryError">-</strong></div>
                        </div>
                    </div>
                    <div id="infraMessage" class="infra-message">Consultando actividad de infraestructura...</div>
                </div>
            </div>

            <div class="analytics-panel section-panel" data-section-key="concordancia">
                <div class="section-header">
                    <h2>📈 Concordancia de Flujo (RabbitMQ vs InfluxDB)</h2>
                    <button type="button" class="section-toggle" data-action="toggle-section">Colapsar</button>
                </div>
                <div class="section-body">
                    <div class="analytics-note">
                        Conteo por minuto (ventana móvil de 15 min) para validar que lo publicado por el runtime
                        llega y se persiste en InfluxDB por proyecto, sector y asset.
                    </div>
                    <div class="analytics-grid">
                        <div class="analytics-card">
                            <h3>Proyecto</h3>
                            <div class="plugin-toolbar">
                                <label class="plugin-label" for="projectFlowPlugin">Plugin</label>
                                <select id="projectFlowPlugin" class="plugin-select"></select>
                            </div>
                            <div class="analytics-meta">
                                <span id="projectFlowSummary">Selecciona un proyecto</span>
                                <span id="projectFlowStatus">-</span>
                            </div>
                            <div class="chart-wrap"><canvas id="projectFlowChart"></canvas></div>
                            <div class="chart-legend">
                                <span class="legend-rabbit">RabbitMQ</span>
                                <span class="legend-influx">InfluxDB</span>
                            </div>
                        </div>
                        <div class="analytics-card">
                            <h3>Sector</h3>
                            <div class="plugin-toolbar">
                                <label class="plugin-label" for="unitFlowPlugin">Plugin</label>
                                <select id="unitFlowPlugin" class="plugin-select"></select>
                            </div>
                            <div class="analytics-meta">
                                <span id="unitFlowSummary">Selecciona un sector</span>
                                <span id="unitFlowStatus">-</span>
                            </div>
                            <div class="chart-wrap"><canvas id="unitFlowChart"></canvas></div>
                            <div class="chart-legend">
                                <span class="legend-rabbit">RabbitMQ</span>
                                <span class="legend-influx">InfluxDB</span>
                            </div>
                        </div>
                        <div class="analytics-card">
                            <h3>Asset</h3>
                            <div class="plugin-toolbar">
                                <label class="plugin-label" for="deviceFlowPlugin">Plugin</label>
                                <select id="deviceFlowPlugin" class="plugin-select"></select>
                            </div>
                            <div class="analytics-meta">
                                <span id="deviceFlowSummary">Selecciona un asset</span>
                                <span id="deviceFlowStatus">-</span>
                            </div>
                            <div class="chart-wrap"><canvas id="deviceFlowChart"></canvas></div>
                            <div class="chart-legend">
                                <span class="legend-rabbit">RabbitMQ</span>
                                <span class="legend-influx">InfluxDB</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="metrics-panel section-panel" data-section-key="metricas">
                <div class="section-header">
                    <h2>📊 Métricas del Sistema</h2>
                    <button type="button" class="section-toggle" data-action="toggle-section">Colapsar</button>
                </div>
                <div class="section-body">
                    <div class="plugin-toolbar">
                        <label class="plugin-label" for="metricsPluginSelect">Plugin de Métricas</label>
                        <select id="metricsPluginSelect" class="plugin-select"></select>
                        <span class="plugin-hint">Se ofrecen sólo visualizaciones para dato escalar.</span>
                    </div>
                    <div class="metrics-grid">
                        <div class="metric-card" data-metric-key="messagesProcessed">
                            <h3>Mensajes Procesados</h3>
                            <div class="metric-value" id="messagesProcessed">0</div>
                            <div class="metric-progress"><div class="metric-progress-fill" id="messagesProcessedProgress"></div></div>
                            <div class="metric-spark"><canvas id="messagesProcessedSpark"></canvas></div>
                            <div class="metric-change" id="messagesProcessedMeta">Total acumulado</div>
                        </div>
                        <div class="metric-card" data-metric-key="messagesFailed">
                            <h3>Mensajes Fallidos</h3>
                            <div class="metric-value" id="messagesFailed">0</div>
                            <div class="metric-progress"><div class="metric-progress-fill" id="messagesFailedProgress"></div></div>
                            <div class="metric-spark"><canvas id="messagesFailedSpark"></canvas></div>
                            <div class="metric-change" id="messagesFailedMeta">Errores detectados</div>
                        </div>
                        <div class="metric-card" data-metric-key="databaseOps">
                            <h3>Operaciones BD</h3>
                            <div class="metric-value" id="databaseOps">0</div>
                            <div class="metric-progress"><div class="metric-progress-fill" id="databaseOpsProgress"></div></div>
                            <div class="metric-spark"><canvas id="databaseOpsSpark"></canvas></div>
                            <div class="metric-change" id="databaseOpsMeta">Operaciones reportadas</div>
                        </div>
                        <div class="metric-card" data-metric-key="activeProtocols">
                            <h3>Protocolos Activos</h3>
                            <div class="metric-value" id="activeProtocols">0</div>
                            <div class="metric-progress"><div class="metric-progress-fill" id="activeProtocolsProgress"></div></div>
                            <div class="metric-spark"><canvas id="activeProtocolsSpark"></canvas></div>
                            <div class="metric-change" id="activeProtocolsMeta">Conectores activos</div>
                        </div>
                        <div class="metric-card" data-metric-key="activeDevices">
                            <h3>Assets Activos</h3>
                            <div class="metric-value" id="activeDevices">0</div>
                            <div class="metric-progress"><div class="metric-progress-fill" id="activeDevicesProgress"></div></div>
                            <div class="metric-spark"><canvas id="activeDevicesSpark"></canvas></div>
                            <div class="metric-change" id="activeDevicesMeta">En ejecución</div>
                        </div>
                        <div class="metric-card" data-metric-key="uptime">
                            <h3>Uptime (segundos)</h3>
                            <div class="metric-value" id="uptime">0</div>
                            <div class="metric-progress"><div class="metric-progress-fill" id="uptimeProgress"></div></div>
                            <div class="metric-spark"><canvas id="uptimeSpark"></canvas></div>
                            <div class="metric-change" id="uptimeMeta">Tiempo de funcionamiento</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="events-panel section-panel" data-section-key="eventos">
                <div class="section-header">
                    <h2>📡 Eventos en Tiempo Real</h2>
                    <button type="button" class="section-toggle" data-action="toggle-section">Colapsar</button>
                </div>
                <div class="section-body">
                    <div id="eventsContainer">
                        <div class="empty-state">Esperando eventos...</div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            const eventsContainer = document.getElementById('eventsContainer');
            const statusEl = document.getElementById('connectionStatus');
            const runtimeSummaryEl = document.getElementById('runtimeSummary');
            const runtimeMessageEl = document.getElementById('runtimeMessage');
            const projectSelect = document.getElementById('projectSelect');
            const unitSelect = document.getElementById('unitSelect');
            const deviceSelect = document.getElementById('deviceSelect');
            const infraMessageEl = document.getElementById('infraMessage');
            const rabbitStatusPillEl = document.getElementById('rabbitStatusPill');
            const influxStatusPillEl = document.getElementById('influxStatusPill');
            const metricsPluginSelect = document.getElementById('metricsPluginSelect');
            const flowCards = {
                project: {
                    summaryEl: document.getElementById('projectFlowSummary'),
                    statusEl: document.getElementById('projectFlowStatus'),
                    canvasEl: document.getElementById('projectFlowChart'),
                    pluginEl: document.getElementById('projectFlowPlugin')
                },
                unit: {
                    summaryEl: document.getElementById('unitFlowSummary'),
                    statusEl: document.getElementById('unitFlowStatus'),
                    canvasEl: document.getElementById('unitFlowChart'),
                    pluginEl: document.getElementById('unitFlowPlugin')
                },
                device: {
                    summaryEl: document.getElementById('deviceFlowSummary'),
                    statusEl: document.getElementById('deviceFlowStatus'),
                    canvasEl: document.getElementById('deviceFlowChart'),
                    pluginEl: document.getElementById('deviceFlowPlugin')
                }
            };

            let hierarchy = { projects: [] };

            const pluginRegistry = {
                'timeseries.compare': [
                    { id: 'line', label: 'Líneas comparativas' },
                    { id: 'area', label: 'Área comparativa' },
                    { id: 'bars', label: 'Barras agrupadas' }
                ],
                scalar: [
                    { id: 'kpi', label: 'KPI clásico' },
                    { id: 'progress', label: 'Barra de progreso' },
                    { id: 'sparkline', label: 'Sparkline en tendencia' }
                ]
            };

            const flowCardState = {
                project: { label: 'Selecciona un proyecto', payload: null },
                unit: { label: 'Selecciona un sector', payload: null },
                device: { label: 'Selecciona un asset', payload: null }
            };

            const flowPluginStoragePrefix = 'iotmw.dashboard.plugin.flow.';
            const metricPluginStorageKey = 'iotmw.dashboard.plugin.metrics';

            const metrics = {
                messagesProcessed: 0,
                messagesFailed: 0,
                databaseOps: 0,
                activeProtocols: 0,
                activeDevices: 0,
                uptime: 0
            };

            const metricHistory = {
                messagesProcessed: [],
                messagesFailed: [],
                databaseOps: [],
                activeProtocols: [],
                activeDevices: [],
                uptime: []
            };

            const metricEventToKey = {
                'system.messages_processed': 'messagesProcessed',
                'system.messages_failed': 'messagesFailed',
                'system.database_operations': 'databaseOps',
                'system.active_protocols': 'activeProtocols',
                'system.active_devices': 'activeDevices',
                'system.uptime_seconds': 'uptime'
            };

            const metricConfigs = {
                messagesProcessed: {
                    cardEl: document.querySelector('[data-metric-key="messagesProcessed"]'),
                    valueEl: document.getElementById('messagesProcessed'),
                    progressEl: document.getElementById('messagesProcessedProgress'),
                    sparkEl: document.getElementById('messagesProcessedSpark'),
                    changeEl: document.getElementById('messagesProcessedMeta'),
                    baseHint: 'Total acumulado',
                    baseTarget: 1000,
                    color: '#2563eb'
                },
                messagesFailed: {
                    cardEl: document.querySelector('[data-metric-key="messagesFailed"]'),
                    valueEl: document.getElementById('messagesFailed'),
                    progressEl: document.getElementById('messagesFailedProgress'),
                    sparkEl: document.getElementById('messagesFailedSpark'),
                    changeEl: document.getElementById('messagesFailedMeta'),
                    baseHint: 'Errores detectados',
                    baseTarget: 100,
                    color: '#dc2626'
                },
                databaseOps: {
                    cardEl: document.querySelector('[data-metric-key="databaseOps"]'),
                    valueEl: document.getElementById('databaseOps'),
                    progressEl: document.getElementById('databaseOpsProgress'),
                    sparkEl: document.getElementById('databaseOpsSpark'),
                    changeEl: document.getElementById('databaseOpsMeta'),
                    baseHint: 'Operaciones reportadas',
                    baseTarget: 1000,
                    color: '#0ea5e9'
                },
                activeProtocols: {
                    cardEl: document.querySelector('[data-metric-key="activeProtocols"]'),
                    valueEl: document.getElementById('activeProtocols'),
                    progressEl: document.getElementById('activeProtocolsProgress'),
                    sparkEl: document.getElementById('activeProtocolsSpark'),
                    changeEl: document.getElementById('activeProtocolsMeta'),
                    baseHint: 'Conectores activos',
                    baseTarget: 10,
                    color: '#7c3aed'
                },
                activeDevices: {
                    cardEl: document.querySelector('[data-metric-key="activeDevices"]'),
                    valueEl: document.getElementById('activeDevices'),
                    progressEl: document.getElementById('activeDevicesProgress'),
                    sparkEl: document.getElementById('activeDevicesSpark'),
                    changeEl: document.getElementById('activeDevicesMeta'),
                    baseHint: 'En ejecución',
                    baseTarget: 50,
                    color: '#16a34a'
                },
                uptime: {
                    cardEl: document.querySelector('[data-metric-key="uptime"]'),
                    valueEl: document.getElementById('uptime'),
                    progressEl: document.getElementById('uptimeProgress'),
                    sparkEl: document.getElementById('uptimeSpark'),
                    changeEl: document.getElementById('uptimeMeta'),
                    baseHint: 'Tiempo de funcionamiento',
                    baseTarget: 86400,
                    color: '#f59e0b'
                }
            };

            const metricHistoryMaxPoints = 60;
            let selectedMetricsPlugin = 'kpi';

            function setRuntimeMessage(message, isError = false) {
                runtimeMessageEl.textContent = message || '';
                runtimeMessageEl.style.color = isError ? '#dc2626' : '#334155';
            }

            function setInfraMessage(message, isError = false) {
                infraMessageEl.textContent = message || '';
                infraMessageEl.style.color = isError ? '#dc2626' : '#334155';
            }

            function setInfraPill(element, status) {
                const normalized = (status || 'unknown').toLowerCase();
                element.className = 'infra-pill';
                if (normalized === 'up') {
                    element.classList.add('infra-up');
                } else if (normalized === 'degraded') {
                    element.classList.add('infra-degraded');
                } else if (normalized === 'error') {
                    element.classList.add('infra-error');
                } else {
                    element.classList.add('infra-unknown');
                }
                element.textContent = normalized.toUpperCase();
            }

            function setText(id, value) {
                const el = document.getElementById(id);
                el.textContent = value == null || value === '' ? '-' : value;
            }

            function formatNumber(value, digits = 0) {
                if (value == null || value === '') {
                    return '-';
                }
                const num = Number(value);
                if (Number.isNaN(num)) {
                    return String(value);
                }
                return num.toLocaleString(undefined, {
                    minimumFractionDigits: digits,
                    maximumFractionDigits: digits
                });
            }

            async function fetchJson(url, options = {}) {
                const response = await fetch(url, options);
                if (!response.ok) {
                    let detail = '';
                    try {
                        const payload = await response.json();
                        detail = payload.detail || payload.message || JSON.stringify(payload);
                    } catch (_) {
                        detail = await response.text();
                    }
                    throw new Error(detail || `HTTP ${response.status}`);
                }
                return response.json();
            }

            function getPluginOptions(dataType) {
                return pluginRegistry[dataType] || [];
            }

            function normalizePluginChoice(dataType, choice, fallbackId) {
                const options = getPluginOptions(dataType);
                if (options.length === 0) {
                    return '';
                }
                if (options.some((option) => option.id === choice)) {
                    return choice;
                }
                if (options.some((option) => option.id === fallbackId)) {
                    return fallbackId;
                }
                return options[0].id;
            }

            function populatePluginSelect(selectEl, dataType, selectedId) {
                if (!selectEl) return;
                const options = getPluginOptions(dataType);
                selectEl.innerHTML = options
                    .map((option) => `<option value="${option.id}">${option.label}</option>`)
                    .join('');
                selectEl.value = normalizePluginChoice(dataType, selectedId, options[0]?.id || '');
            }

            function getSelectedFlowPlugin(scope) {
                const card = flowCards[scope];
                const choice = card?.pluginEl?.value || '';
                return normalizePluginChoice('timeseries.compare', choice, 'line');
            }

            function initializePluginSelectors() {
                Object.entries(flowCards).forEach(([scope, card]) => {
                    if (!card.pluginEl) return;
                    const storageKey = `${flowPluginStoragePrefix}${scope}`;
                    let stored = '';
                    try {
                        stored = localStorage.getItem(storageKey) || '';
                    } catch (_) {
                        stored = '';
                    }
                    const selected = normalizePluginChoice('timeseries.compare', stored, 'line');
                    populatePluginSelect(card.pluginEl, 'timeseries.compare', selected);
                    card.pluginEl.addEventListener('change', () => {
                        const normalized = getSelectedFlowPlugin(scope);
                        card.pluginEl.value = normalized;
                        try {
                            localStorage.setItem(storageKey, normalized);
                        } catch (_) {
                            // Ignorar errores de storage.
                        }
                        const latestState = flowCardState[scope] || {};
                        renderFlowCard(scope, latestState.label || '-', latestState.payload || null);
                    });
                });

                let storedMetricPlugin = '';
                try {
                    storedMetricPlugin = localStorage.getItem(metricPluginStorageKey) || '';
                } catch (_) {
                    storedMetricPlugin = '';
                }
                selectedMetricsPlugin = normalizePluginChoice('scalar', storedMetricPlugin, 'kpi');
                if (metricsPluginSelect) {
                    populatePluginSelect(metricsPluginSelect, 'scalar', selectedMetricsPlugin);
                    metricsPluginSelect.value = selectedMetricsPlugin;
                    metricsPluginSelect.addEventListener('change', () => {
                        selectedMetricsPlugin = normalizePluginChoice('scalar', metricsPluginSelect.value, 'kpi');
                        metricsPluginSelect.value = selectedMetricsPlugin;
                        try {
                            localStorage.setItem(metricPluginStorageKey, selectedMetricsPlugin);
                        } catch (_) {
                            // Ignorar errores de storage.
                        }
                        renderAllMetrics();
                    });
                }
            }

            function initializeCollapsibleSections() {
                const storagePrefix = 'iotmw.dashboard.section.';
                const sections = Array.from(document.querySelectorAll('.section-panel[data-section-key]'));

                sections.forEach((section) => {
                    const key = section.dataset.sectionKey;
                    const button = section.querySelector('[data-action="toggle-section"]');
                    if (!key || !button) {
                        return;
                    }

                    const applyState = (collapsed) => {
                        section.classList.toggle('section-collapsed', collapsed);
                        button.textContent = collapsed ? 'Expandir' : 'Colapsar';
                        button.setAttribute('aria-expanded', String(!collapsed));
                    };

                    let collapsed = false;
                    try {
                        collapsed = localStorage.getItem(`${storagePrefix}${key}`) === '1';
                    } catch (_) {
                        collapsed = false;
                    }
                    applyState(collapsed);

                    button.addEventListener('click', () => {
                        const nowCollapsed = !section.classList.contains('section-collapsed');
                        applyState(nowCollapsed);
                        try {
                            localStorage.setItem(`${storagePrefix}${key}`, nowCollapsed ? '1' : '0');
                        } catch (_) {
                            // Ignorar errores de storage (modo privado / restricciones)
                        }
                    });
                });
            }

            function selectedOptionLabel(selectEl, fallback) {
                if (!selectEl) return fallback;
                const idx = selectEl.selectedIndex;
                if (idx == null || idx < 1) return fallback;
                return (selectEl.options[idx]?.textContent || fallback).trim();
            }

            function clearFlowCanvas(canvasEl, message) {
                if (!canvasEl) return;
                const ctx = canvasEl.getContext('2d');
                const width = canvasEl.clientWidth || 320;
                const height = canvasEl.clientHeight || 170;
                const dpr = window.devicePixelRatio || 1;
                canvasEl.width = Math.floor(width * dpr);
                canvasEl.height = Math.floor(height * dpr);
                ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
                ctx.clearRect(0, 0, width, height);
                ctx.fillStyle = '#94a3b8';
                ctx.font = '12px sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(message || 'Sin datos', width / 2, height / 2);
            }

            function drawFlowChart(canvasEl, series, pluginId = 'line') {
                if (!canvasEl) return;
                if (!Array.isArray(series) || series.length === 0) {
                    clearFlowCanvas(canvasEl, 'Sin datos');
                    return;
                }

                const width = canvasEl.clientWidth || 320;
                const height = canvasEl.clientHeight || 170;
                const dpr = window.devicePixelRatio || 1;
                canvasEl.width = Math.floor(width * dpr);
                canvasEl.height = Math.floor(height * dpr);

                const ctx = canvasEl.getContext('2d');
                ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
                ctx.clearRect(0, 0, width, height);

                const rabbitValues = series.map((point) => Number(point.rabbitmq || 0));
                const influxValues = series.map((point) => Number(point.influxdb || 0));
                const maxValue = Math.max(1, ...rabbitValues, ...influxValues);
                const selectedPlugin = normalizePluginChoice('timeseries.compare', pluginId, 'line');

                const margin = { top: 8, right: 8, bottom: 24, left: 30 };
                const chartWidth = Math.max(1, width - margin.left - margin.right);
                const chartHeight = Math.max(1, height - margin.top - margin.bottom);

                const xAt = (idx) => {
                    if (series.length <= 1) return margin.left;
                    return margin.left + (idx * chartWidth) / (series.length - 1);
                };
                const yAt = (value) => margin.top + chartHeight - (value / maxValue) * chartHeight;
                const baseLineY = yAt(0);

                ctx.strokeStyle = '#e2e8f0';
                ctx.lineWidth = 1;
                for (let step = 0; step <= 4; step += 1) {
                    const y = margin.top + (chartHeight * step) / 4;
                    ctx.beginPath();
                    ctx.moveTo(margin.left, y);
                    ctx.lineTo(margin.left + chartWidth, y);
                    ctx.stroke();
                }

                const drawLine = (values, color) => {
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    values.forEach((value, idx) => {
                        const x = xAt(idx);
                        const y = yAt(value);
                        if (idx === 0) {
                            ctx.moveTo(x, y);
                        } else {
                            ctx.lineTo(x, y);
                        }
                    });
                    ctx.stroke();
                };

                const drawArea = (values, strokeColor, fillColor) => {
                    ctx.fillStyle = fillColor;
                    ctx.beginPath();
                    values.forEach((value, idx) => {
                        const x = xAt(idx);
                        const y = yAt(value);
                        if (idx === 0) {
                            ctx.moveTo(x, y);
                        } else {
                            ctx.lineTo(x, y);
                        }
                    });
                    const endX = xAt(values.length - 1);
                    const startX = xAt(0);
                    ctx.lineTo(endX, baseLineY);
                    ctx.lineTo(startX, baseLineY);
                    ctx.closePath();
                    ctx.fill();
                    drawLine(values, strokeColor);
                };

                const drawBars = () => {
                    const safeLen = Math.max(series.length, 1);
                    const groupWidth = chartWidth / safeLen;
                    const barWidth = Math.max(2, Math.min(14, (groupWidth * 0.72) / 2));
                    rabbitValues.forEach((value, idx) => {
                        const centerX = xAt(idx);
                        const rabbitY = yAt(value);
                        const influxY = yAt(influxValues[idx]);
                        ctx.fillStyle = '#2563eb';
                        ctx.fillRect(centerX - barWidth - 1, rabbitY, barWidth, baseLineY - rabbitY);
                        ctx.fillStyle = '#16a34a';
                        ctx.fillRect(centerX + 1, influxY, barWidth, baseLineY - influxY);
                    });
                };

                if (selectedPlugin === 'bars') {
                    drawBars();
                } else if (selectedPlugin === 'area') {
                    drawArea(rabbitValues, '#2563eb', 'rgba(37, 99, 235, 0.16)');
                    drawArea(influxValues, '#16a34a', 'rgba(22, 163, 74, 0.14)');
                } else {
                    drawLine(rabbitValues, '#2563eb');
                    drawLine(influxValues, '#16a34a');
                }

                ctx.fillStyle = '#475569';
                ctx.font = '11px sans-serif';
                ctx.textAlign = 'left';
                ctx.fillText(`max ${formatNumber(maxValue)}`, margin.left, margin.top + 10);

                const firstTime = series[0]?.time ? new Date(series[0].time) : null;
                const lastTime = series[series.length - 1]?.time ? new Date(series[series.length - 1].time) : null;
                ctx.textAlign = 'left';
                ctx.fillText(firstTime ? firstTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-', margin.left, height - 6);
                ctx.textAlign = 'right';
                ctx.fillText(lastTime ? lastTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-', margin.left + chartWidth, height - 6);
            }

            function trimMetricHistory(metricKey) {
                const history = metricHistory[metricKey] || [];
                if (history.length <= metricHistoryMaxPoints) return history;
                history.splice(0, history.length - metricHistoryMaxPoints);
                return history;
            }

            function drawSparkline(canvasEl, points, color) {
                if (!canvasEl) return;
                const width = canvasEl.clientWidth || 180;
                const height = canvasEl.clientHeight || 44;
                const dpr = window.devicePixelRatio || 1;
                canvasEl.width = Math.floor(width * dpr);
                canvasEl.height = Math.floor(height * dpr);
                const ctx = canvasEl.getContext('2d');
                ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
                ctx.clearRect(0, 0, width, height);

                if (!Array.isArray(points) || points.length === 0) {
                    return;
                }

                const maxValue = Math.max(1, ...points);
                const minValue = Math.min(...points);
                const span = Math.max(1, maxValue - minValue);
                const xAt = (idx) => {
                    if (points.length <= 1) return 0;
                    return (idx * width) / (points.length - 1);
                };
                const yAt = (value) => height - ((value - minValue) / span) * (height - 2) - 1;

                ctx.strokeStyle = color;
                ctx.lineWidth = 2;
                ctx.beginPath();
                points.forEach((point, idx) => {
                    const x = xAt(idx);
                    const y = yAt(point);
                    if (idx === 0) {
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                    }
                });
                ctx.stroke();
            }

            function renderMetricCard(metricKey) {
                const config = metricConfigs[metricKey];
                if (!config) return;
                const value = Number(metrics[metricKey] || 0);
                const history = trimMetricHistory(metricKey);
                const pluginMode = normalizePluginChoice('scalar', selectedMetricsPlugin, 'kpi');
                if (config.cardEl) {
                    config.cardEl.dataset.plugin = pluginMode;
                }
                if (config.valueEl) {
                    config.valueEl.textContent = value.toLocaleString();
                }
                if (config.progressEl) {
                    const maxHistory = history.length ? Math.max(...history) : value;
                    const target = Math.max(config.baseTarget, Math.ceil(maxHistory * 1.1), 1);
                    const percent = Math.max(0, Math.min(100, (value / target) * 100));
                    config.progressEl.style.width = `${percent.toFixed(1)}%`;
                }
                if (config.sparkEl) {
                    drawSparkline(config.sparkEl, history, config.color);
                }
                if (config.changeEl) {
                    if (pluginMode === 'progress') {
                        config.changeEl.textContent = `${config.baseHint} · progreso relativo`;
                    } else if (pluginMode === 'sparkline') {
                        config.changeEl.textContent = `${config.baseHint} · tendencia reciente`;
                    } else {
                        config.changeEl.textContent = config.baseHint;
                    }
                }
            }

            function renderAllMetrics() {
                Object.keys(metricConfigs).forEach((metricKey) => {
                    renderMetricCard(metricKey);
                });
            }

            function updateMetricValue(metricKey, rawValue) {
                const value = Number(rawValue || 0);
                if (!Object.prototype.hasOwnProperty.call(metrics, metricKey)) {
                    return;
                }
                metrics[metricKey] = value;
                metricHistory[metricKey].push(value);
                renderMetricCard(metricKey);
            }

            function renderFlowCard(scope, label, payload) {
                const card = flowCards[scope];
                if (!card) return;
                flowCardState[scope] = { label: label || '-', payload: payload || null };

                if (!payload) {
                    card.summaryEl.textContent = label;
                    card.statusEl.textContent = '-';
                    card.statusEl.style.color = '#64748b';
                    clearFlowCanvas(card.canvasEl, 'Sin selección');
                    return;
                }

                const totals = payload.totals || {};
                const rabbitTotal = Number(totals.rabbitmq || 0);
                const influxTotal = Number(totals.influxdb || 0);
                const delta = rabbitTotal - influxTotal;
                const ratio = rabbitTotal > 0 ? (influxTotal / rabbitTotal) : null;
                const ratioLabel = ratio == null ? '-' : `${ratio.toFixed(2)}x`;

                card.summaryEl.textContent = `${label} | Rabbit ${formatNumber(rabbitTotal)} | Influx ${formatNumber(influxTotal)} | ratio ${ratioLabel} | Δ ${formatNumber(delta)}`;
                const influxQueryStatus = payload.query_status?.influxdb || 'unknown';
                if (influxQueryStatus === 'ok') {
                    if (rabbitTotal === 0 && influxTotal === 0) {
                        card.statusEl.textContent = 'SIN DATOS';
                        card.statusEl.style.color = '#64748b';
                    } else if (rabbitTotal === 0 || ratio < 0.7 || ratio > 1.5) {
                        card.statusEl.textContent = 'DESFASADO';
                        card.statusEl.style.color = '#b45309';
                    } else {
                        card.statusEl.textContent = 'ALINEADO';
                        card.statusEl.style.color = '#166534';
                    }
                } else {
                    card.statusEl.textContent = influxQueryStatus.toUpperCase();
                    card.statusEl.style.color = '#b45309';
                }

                drawFlowChart(card.canvasEl, payload.series || [], getSelectedFlowPlugin(scope));
            }

            async function loadScopeFlow(scope, scopeId, scopeRefId, labelWhenSelected, labelWhenEmpty) {
                if (!scopeId) {
                    renderFlowCard(scope, labelWhenEmpty, null);
                    return;
                }

                try {
                    const params = new URLSearchParams({
                        scope: scope,
                        scope_id: scopeId,
                        minutes: '15'
                    });
                    if (scopeRefId) {
                        params.set('scope_ref_id', scopeRefId);
                    }
                    const payload = await fetchJson(`/api/analytics/flow?${params.toString()}`);
                    renderFlowCard(scope, labelWhenSelected, payload);
                } catch (error) {
                    const card = flowCards[scope];
                    if (!card) return;
                    card.summaryEl.textContent = `${labelWhenSelected} | Error`;
                    card.statusEl.textContent = 'ERROR';
                    card.statusEl.style.color = '#b91c1c';
                    flowCardState[scope] = { label: `${labelWhenSelected} | Error`, payload: null };
                    clearFlowCanvas(card.canvasEl, error.message || 'Error');
                }
            }

            async function loadFlowAnalytics() {
                const selectedProjectId = projectSelect.value;
                const selectedUnitId = unitSelect.value;
                const selectedDeviceId = deviceSelect.value;
                const selectedDevice = flattenDevices().find((item) => String(item.id) === String(selectedDeviceId));
                const selectedDeviceRefId = selectedDevice?.device_ref_id ? String(selectedDevice.device_ref_id) : '';

                const tasks = [
                    loadScopeFlow(
                        'project',
                        selectedProjectId,
                        '',
                        selectedOptionLabel(projectSelect, 'Proyecto'),
                        'Selecciona un proyecto'
                    ),
                    loadScopeFlow(
                        'unit',
                        selectedUnitId,
                        '',
                        selectedOptionLabel(unitSelect, 'Sector'),
                        'Selecciona un sector'
                    ),
                    loadScopeFlow(
                        'device',
                        selectedDeviceId,
                        selectedDeviceRefId,
                        selectedOptionLabel(deviceSelect, 'Asset'),
                        'Selecciona un asset'
                    )
                ];
                await Promise.all(tasks);
            }

            function flattenUnits() {
                const units = [];
                (hierarchy.projects || []).forEach((project) => {
                    (project.units || []).forEach((unit) => {
                        units.push({
                            ...unit,
                            project_id: project.id,
                            project_name: project.name
                        });
                    });
                });
                return units;
            }

            function flattenDevices() {
                const devices = [];
                (hierarchy.projects || []).forEach((project) => {
                    (project.units || []).forEach((unit) => {
                        (unit.devices || []).forEach((device) => {
                            devices.push({
                                ...device,
                                project_id: project.id,
                                project_name: project.name,
                                unit_id: unit.id,
                                unit_name: unit.name
                            });
                        });
                    });
                    (project.devices_without_unit || []).forEach((device) => {
                        devices.push({
                            ...device,
                            project_id: project.id,
                            project_name: project.name,
                            unit_id: null,
                            unit_name: 'Sin sector'
                        });
                    });
                });
                return devices;
            }

            function renderProjectSelect() {
                const previous = projectSelect.value;
                const options = ['<option value="">Selecciona proyecto</option>'];
                (hierarchy.projects || []).forEach((project) => {
                    options.push(`<option value="${project.id}">${project.name}</option>`);
                });
                projectSelect.innerHTML = options.join('');
                projectSelect.value = (hierarchy.projects || []).some((p) => String(p.id) === String(previous))
                    ? previous
                    : '';
            }

            function renderUnitSelect() {
                const selectedProjectId = projectSelect.value;
                const previous = unitSelect.value;
                const units = flattenUnits().filter((u) => !selectedProjectId || String(u.project_id) === String(selectedProjectId));
                const options = ['<option value="">Selecciona sector</option>'];
                units.forEach((unit) => {
                    options.push(`<option value="${unit.id}">${unit.name} (${unit.project_name})</option>`);
                });
                unitSelect.innerHTML = options.join('');
                unitSelect.value = units.some((u) => String(u.id) === String(previous)) ? previous : '';
            }

            function renderDeviceSelect() {
                const selectedProjectId = projectSelect.value;
                const selectedUnitId = unitSelect.value;
                const previous = deviceSelect.value;
                let devices = flattenDevices();

                if (selectedProjectId) {
                    devices = devices.filter((d) => String(d.project_id) === String(selectedProjectId));
                }
                if (selectedUnitId) {
                    devices = devices.filter((d) => String(d.unit_id) === String(selectedUnitId));
                }

                const options = ['<option value="">Selecciona asset</option>'];
                devices.forEach((device) => {
                    const unitLabel = device.unit_name || 'Sin sector';
                    options.push(
                        `<option value="${device.id}">${device.device_name} (${unitLabel})</option>`
                    );
                });
                deviceSelect.innerHTML = options.join('');
                deviceSelect.value = devices.some((d) => String(d.id) === String(previous)) ? previous : '';
            }

            async function loadHierarchy() {
                hierarchy = await fetchJson('/api/runtime/hierarchy');
                renderProjectSelect();
                renderUnitSelect();
                renderDeviceSelect();
            }

            function updateRuntimeSummary(state) {
                runtimeSummaryEl.textContent =
                    `Runtime ${state.running ? 'activo' : 'detenido'} | ` +
                    `Scopes activos -> Proyectos: ${state.active_projects_count}, ` +
                    `Sectores: ${state.active_units_count}, ` +
                    `Assets: ${state.active_devices_count}, ` +
                    `Resueltos: ${state.resolved_devices_count}`;
            }

            async function loadRuntimeState() {
                const state = await fetchJson('/api/runtime/state');
                updateRuntimeSummary(state);
                if (state.metrics) {
                    updateMetricValue('messagesProcessed', state.metrics.messages_processed || 0);
                    updateMetricValue('messagesFailed', state.metrics.messages_failed || 0);
                    updateMetricValue('databaseOps', state.metrics.database_operations || 0);
                    updateMetricValue('activeProtocols', state.metrics.active_protocols || 0);
                    updateMetricValue('activeDevices', state.metrics.active_devices || 0);
                    updateMetricValue('uptime', state.metrics.uptime_seconds || 0);
                }
                return state;
            }

            async function loadInfraStatus() {
                const infra = await fetchJson('/api/infra/status');
                const rabbit = infra.rabbitmq || {};
                const influx = infra.influxdb || {};
                const topQueue = (rabbit.top_queues || [])[0];
                const influxActivity = influx.activity || {};

                setInfraPill(rabbitStatusPillEl, rabbit.status || 'unknown');
                setInfraPill(influxStatusPillEl, influx.status || 'unknown');

                const queuesTotal = rabbit.queues_total ?? rabbit.queues ?? 0;
                const queuesActive = rabbit.queues_active ?? 0;
                setText('rabbitConnections', formatNumber(rabbit.connections || 0));
                setText('rabbitChannels', formatNumber(rabbit.channels || 0));
                setText('rabbitQueues', `${formatNumber(queuesTotal)} / ${formatNumber(queuesActive)}`);
                setText('rabbitPending', formatNumber(rabbit.messages_pending_active ?? rabbit.messages_pending ?? 0));
                setText('rabbitPendingTotal', formatNumber(rabbit.messages_pending_total ?? rabbit.messages_pending ?? 0));
                setText('rabbitPublishRate', formatNumber(rabbit.publish_rate || 0, 2));
                setText('rabbitDeliverRate', formatNumber(rabbit.deliver_rate || 0, 2));
                setText(
                    'rabbitTopQueue',
                    topQueue ? `${topQueue.name || 'n/a'} (${formatNumber(topQueue.messages || 0)})` : 'n/a'
                );
                setText('rabbitError', rabbit.error || '-');

                setText('influxHealth', influx.health_status || '-');
                setText('influxOrg', influx.org || '-');
                setText('influxBucket', influx.bucket || '-');
                setText('influxPoints5m', formatNumber(influxActivity.points_last_5m));
                setText('influxQueryStatus', influxActivity.query_status || '-');
                setText('influxQueryError', influxActivity.error || '-');

                const checkedAt = infra.checked_at
                    ? new Date(infra.checked_at).toLocaleTimeString()
                    : new Date().toLocaleTimeString();
                setInfraMessage(`Última verificación: ${checkedAt} | Estado global: ${(infra.status || 'unknown').toUpperCase()}`);
            }

            async function controlScope(scope, action) {
                const scopeToApi = {
                    project: 'project',
                    unit: 'unidad',
                    device: 'dispositivo'
                };
                const scopeLabelMap = {
                    project: 'proyecto',
                    unit: 'sector',
                    device: 'asset'
                };

                const selectorMap = {
                    project: projectSelect,
                    unit: unitSelect,
                    device: deviceSelect
                };

                const selectedId = selectorMap[scope].value;
                if (!selectedId) {
                    setRuntimeMessage(`Selecciona un ${scopeLabelMap[scope]} antes de ejecutar la acción.`, true);
                    return;
                }

                try {
                    const endpoint = `/api/runtime/${action}/${scopeToApi[scope]}/${encodeURIComponent(selectedId)}`;
                    const result = await fetchJson(endpoint, { method: 'POST' });
                    setRuntimeMessage(result.message || 'Acción aplicada');
                    await loadRuntimeState();
                    await loadFlowAnalytics();
                } catch (error) {
                    setRuntimeMessage(`Error en acción ${action} ${scopeLabelMap[scope]}: ${error.message}`, true);
                }
            }

            async function manualRefresh() {
                try {
                    await fetchJson('/api/runtime/refresh', { method: 'POST' });
                    await loadHierarchy();
                    await loadRuntimeState();
                    await loadFlowAnalytics();
                    setRuntimeMessage('Jerarquía actualizada desde admin.');
                } catch (error) {
                    setRuntimeMessage(`No se pudo refrescar jerarquía: ${error.message}`, true);
                }
            }

            async function ensureRuntimeAutostart() {
                const state = await loadRuntimeState();
                if ((state.active_projects_count || 0) > 0) {
                    return;
                }

                const projects = hierarchy.projects || [];
                if (projects.length !== 1) {
                    return;
                }

                const onlyProjectId = String(projects[0].id || '');
                if (!onlyProjectId) {
                    return;
                }

                try {
                    await fetchJson(`/api/runtime/start/project/${encodeURIComponent(onlyProjectId)}`, { method: 'POST' });
                    projectSelect.value = onlyProjectId;
                    renderUnitSelect();
                    renderDeviceSelect();
                    await loadRuntimeState();
                    await loadFlowAnalytics();
                    setRuntimeMessage(`Autoarranque aplicado para demo: proyecto ${projects[0].name || onlyProjectId}.`);
                } catch (error) {
                    setRuntimeMessage(`No se pudo autoarrancar proyecto demo: ${error.message}`, true);
                }
            }

            projectSelect.addEventListener('change', () => {
                renderUnitSelect();
                renderDeviceSelect();
                loadFlowAnalytics();
            });

            unitSelect.addEventListener('change', () => {
                renderDeviceSelect();
                loadFlowAnalytics();
            });

            deviceSelect.addEventListener('change', () => {
                loadFlowAnalytics();
            });

            ws.onopen = () => {
                statusEl.textContent = 'Conectado';
                statusEl.className = 'status connected';
                if (eventsContainer.querySelector('.empty-state')) {
                    eventsContainer.innerHTML = '';
                }
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'welcome') {
                    return;
                }
                handleEvent(data);
            };

            ws.onerror = () => {
                statusEl.textContent = 'Error';
                statusEl.className = 'status disconnected';
            };

            ws.onclose = () => {
                statusEl.textContent = 'Desconectado';
                statusEl.className = 'status disconnected';
                setTimeout(() => location.reload(), 3000);
            };

            function handleEvent(event) {
                if (event.event_type === 'metric') {
                    const metric = event.data.metric;
                    const value = event.data.value;
                    const metricKey = metricEventToKey[metric];
                    if (metricKey) {
                        updateMetricValue(metricKey, value);
                    }
                }
                addEventToPanel(event);
            }

            function addEventToPanel(event) {
                if (eventsContainer.querySelector('.empty-state')) {
                    eventsContainer.innerHTML = '';
                }

                const eventDiv = document.createElement('div');
                eventDiv.className = `event-item severity-${event.severity || 'info'}`;
                const time = new Date(event.timestamp).toLocaleTimeString();

                eventDiv.innerHTML = `
                    <div class="event-header">
                        <span class="event-type">${(event.event_type || 'event').toUpperCase()}</span>
                        <span class="event-time">${time}</span>
                    </div>
                    <div class="event-service">Servicio: ${event.service || 'n/a'}</div>
                    <div class="event-data">${JSON.stringify(event.data || {}, null, 2)}</div>
                `;

                eventsContainer.insertBefore(eventDiv, eventsContainer.firstChild);
                while (eventsContainer.children.length > 120) {
                    eventsContainer.removeChild(eventsContainer.lastChild);
                }
            }

            async function bootstrap() {
                try {
                    await loadHierarchy();
                    await ensureRuntimeAutostart();
                    await loadInfraStatus();
                    await loadFlowAnalytics();
                    setRuntimeMessage('Runtime listo para iniciar por proyecto, sector o asset.');
                } catch (error) {
                    setRuntimeMessage(`Error inicializando controles: ${error.message}`, true);
                    setInfraMessage(`Error consultando infraestructura: ${error.message}`, true);
                }
            }

            initializePluginSelectors();
            renderAllMetrics();
            initializeCollapsibleSections();
            bootstrap();
            setInterval(loadRuntimeState, 5000);
            setInterval(loadInfraStatus, 7000);
            setInterval(loadFlowAnalytics, 10000);
            setInterval(async () => {
                await loadHierarchy();
                await loadFlowAnalytics();
            }, 30000);

            setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send('ping');
                }
            }, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para el dashboard de monitoreo"""
    await websocket.accept()
    active_connections.append(websocket)

    logger.info(f"✅ Cliente WebSocket conectado. Total: {len(active_connections)}")

    try:
        await websocket.send_json({
            "type": "welcome",
            "message": "Conectado al dashboard de monitoreo",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        logger.info("🔌 Cliente WebSocket desconectado")
    except Exception as e:
        logger.error(f"❌ Error en WebSocket: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"📊 Conexiones WebSocket activas: {len(active_connections)}")


@app.get("/health")
async def health_check():
    """Verifica el estado del dashboard"""
    runtime_state = twin_runtime.get_state() if twin_runtime else None
    return {
        "status": "healthy" if rabbitmq_client and rabbitmq_client.connected else "degraded",
        "rabbitmq": rabbitmq_client.health_check() if rabbitmq_client else None,
        "mqtt_runtime_connected": bool(runtime_mqtt_client and runtime_mqtt_client._connected),
        "runtime": runtime_state,
        "active_connections": len(active_connections),
        "service": "dashboard"
    }


def main():
    """Función principal"""
    port = int(os.getenv("DASHBOARD_PORT", "8080"))
    host = os.getenv("DASHBOARD_HOST", "0.0.0.0")

    logger.info("🚀 Iniciando Dashboard de Monitoreo...")
    logger.info(f"📡 Escuchando en {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
