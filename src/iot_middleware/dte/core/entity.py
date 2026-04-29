"""Base class for pluggable digital twin entities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from .events import EventType, TwinEvent
from .state_machine import StateMachine, TwinState


class DigitalTwinEntity(ABC):
    """Base entity with state/config/input/output/event behavior."""

    model_type: str = "base"

    def __init__(
        self,
        entity_id: str,
        plant_id: str,
        config: Optional[Dict[str, Any]] = None,
        state: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.entity_id = entity_id
        self.plant_id = plant_id
        self.config: Dict[str, Any] = config or {}
        self.state: Dict[str, Any] = state or {}
        self.inputs: Dict[str, Any] = {}
        self.outputs: Dict[str, Any] = {}
        self.events: list[TwinEvent] = []
        self.fsm = StateMachine(current_state=TwinState.IDLE)
        self.last_updated = datetime.now(timezone.utc)
        self._configure_default_fsm()

    @classmethod
    def config_schema(cls) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    @classmethod
    def io_schema(cls) -> Dict[str, Any]:
        return {"inputs": {}, "outputs": {}}

    def _configure_default_fsm(self) -> None:
        self.fsm.add_event_transition(
            event_type=EventType.DEVICE_DISCONNECTED,
            sources={TwinState.IDLE, TwinState.RUNNING, TwinState.CONTROL, TwinState.MAINTENANCE},
            target=TwinState.ERROR,
        )

    @property
    def twin_state(self) -> TwinState:
        return self.fsm.current_state

    def emit(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> TwinEvent:
        event = TwinEvent(
            entity_id=self.entity_id,
            plant_id=self.plant_id,
            type=event_type,
            payload=payload or {},
        )
        self.events.append(event)
        return event

    def set_input(self, key: str, value: Any) -> None:
        self.inputs[key] = value

    def get_output(self, key: str, default: Any = None) -> Any:
        return self.outputs.get(key, default)

    @abstractmethod
    def update(self, dt_seconds: float, now: datetime, mode: str) -> Iterable[TwinEvent]:
        """Advance entity behavior one tick and optionally return events."""

    def apply_command(self, command: str, payload: Optional[Dict[str, Any]] = None) -> list[TwinEvent]:
        payload = payload or {}
        command_lower = command.lower()
        generated: list[TwinEvent] = []

        if command_lower == "start":
            changed, previous, current = self.fsm.force(TwinState.RUNNING)
            if changed:
                generated.append(
                    self.emit(
                        EventType.STATE_CHANGE,
                        {"from": previous.value, "to": current.value, "reason": "command:start"},
                    )
                )
        elif command_lower == "stop":
            changed, previous, current = self.fsm.force(TwinState.IDLE)
            if changed:
                generated.append(
                    self.emit(
                        EventType.STATE_CHANGE,
                        {"from": previous.value, "to": current.value, "reason": "command:stop"},
                    )
                )
        elif command_lower == "maintenance":
            changed, previous, current = self.fsm.force(TwinState.MAINTENANCE)
            if changed:
                generated.append(
                    self.emit(
                        EventType.STATE_CHANGE,
                        {"from": previous.value, "to": current.value, "reason": "command:maintenance"},
                    )
                )
        elif command_lower == "reset_error":
            changed, previous, current = self.fsm.force(TwinState.IDLE)
            if changed:
                generated.append(
                    self.emit(
                        EventType.STATE_CHANGE,
                        {"from": previous.value, "to": current.value, "reason": "command:reset_error"},
                    )
                )
        else:
            generated.append(
                self.emit(
                    EventType.STATE_CHANGE,
                    {"command": command, "payload": payload, "reason": "command:custom"},
                )
            )

        return generated

    def ingest_device_state(self, payload: Dict[str, Any]) -> list[TwinEvent]:
        self.state.update(payload)
        changed, previous, current = self.fsm.evaluate(self, None)
        events = [
            self.emit(
                EventType.STATE_CHANGE,
                {"source": "device", "payload": payload, "state": self.state},
            )
        ]
        if changed:
            events.append(
                self.emit(
                    EventType.STATE_CHANGE,
                    {"from": previous.value, "to": current.value, "reason": "device_state"},
                )
            )
        return events

    def handle_event(self, event: TwinEvent) -> list[TwinEvent]:
        if event.entity_id != self.entity_id:
            return []
        changed, previous, current = self.fsm.evaluate(self, event)
        if not changed:
            return []
        return [
            self.emit(
                EventType.STATE_CHANGE,
                {"from": previous.value, "to": current.value, "reason": f"event:{event.type}"},
            )
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.entity_id,
            "plant_id": self.plant_id,
            "type": self.model_type,
            "state_machine": self.twin_state.value,
            "config": self.config,
            "state": self.state,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "last_updated": self.last_updated.isoformat(),
        }
