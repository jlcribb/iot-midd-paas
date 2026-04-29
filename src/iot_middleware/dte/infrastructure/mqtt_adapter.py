"""MQTT adapter for bidirectional twin-device synchronization."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional

import paho.mqtt.client as mqtt


logger = logging.getLogger(__name__)


@dataclass
class MQTTConfig:
    host: str = "localhost"
    port: int = 1883
    client_id: str = "dte-engine"
    username: Optional[str] = None
    password: Optional[str] = None
    keepalive: int = 60
    qos: int = 1


class MQTTAdapter:
    """Paho MQTT wrapper using standardized twin topics."""

    def __init__(
        self,
        config: MQTTConfig,
        *,
        on_device_state: Optional[Callable[[str, dict[str, Any]], None]] = None,
        on_device_event: Optional[Callable[[str, dict[str, Any]], None]] = None,
    ) -> None:
        self.config = config
        self.on_device_state = on_device_state
        self.on_device_event = on_device_event
        self._connected = False

        self._client = mqtt.Client(client_id=config.client_id)
        if config.username:
            self._client.username_pw_set(config.username, config.password)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    def connect(self) -> None:
        self._client.connect(self.config.host, self.config.port, self.config.keepalive)
        self._client.loop_start()

    def disconnect(self) -> None:
        try:
            self._client.loop_stop()
            self._client.disconnect()
        finally:
            self._connected = False

    def subscribe_for_twins(self) -> None:
        self._client.subscribe("twins/+/state", qos=self.config.qos)
        self._client.subscribe("twins/+/events", qos=self.config.qos)

    def publish_state(self, entity_id: str, payload: dict[str, Any]) -> None:
        self._publish_json(f"twins/{entity_id}/state", payload)

    def publish_command(self, entity_id: str, payload: dict[str, Any]) -> None:
        self._publish_json(f"twins/{entity_id}/command", payload)

    def publish_event(self, entity_id: str, payload: dict[str, Any]) -> None:
        self._publish_json(f"twins/{entity_id}/events", payload)

    def _publish_json(self, topic: str, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        self._client.publish(topic, body, qos=self.config.qos, retain=False)

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Any, rc: Any, properties: Any = None) -> None:
        self._connected = True
        logger.info("MQTT connected to %s:%s (rc=%s)", self.config.host, self.config.port, rc)

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: Any, properties: Any = None) -> None:
        self._connected = False
        logger.warning("MQTT disconnected (rc=%s)", rc)

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            payload = {"raw": msg.payload.decode("utf-8", errors="replace")}

        parts = topic.split("/")
        if len(parts) != 3 or parts[0] != "twins":
            logger.debug("Ignoring non-standard topic '%s'", topic)
            return

        entity_id = parts[1]
        channel = parts[2]
        if channel == "state" and self.on_device_state:
            self.on_device_state(entity_id, payload)
            return
        if channel == "events" and self.on_device_event:
            self.on_device_event(entity_id, payload)
