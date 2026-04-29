"""Simple conveyor twin model."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable

from ..core.entity import DigitalTwinEntity
from ..core.events import EventType, TwinEvent
from ..core.state_machine import TwinState


class ConveyorTwin(DigitalTwinEntity):
    model_type = "conveyor"

    def __init__(
        self,
        entity_id: str,
        plant_id: str,
        config: Dict[str, Any] | None = None,
        state: Dict[str, Any] | None = None,
    ) -> None:
        cfg = {"max_speed": 1.5, "default_speed": 0.4}
        if config:
            cfg.update(config)
        st = {"speed": float(cfg["default_speed"]), "running": True}
        if state:
            st.update(state)
        super().__init__(entity_id=entity_id, plant_id=plant_id, config=cfg, state=st)
        self.fsm.force(TwinState.RUNNING)

    @classmethod
    def io_schema(cls) -> Dict[str, Any]:
        return {"inputs": {"speed": {"type": "float"}}, "outputs": {"speed": {"type": "float"}}}

    def update(self, dt_seconds: float, now: datetime, mode: str) -> Iterable[TwinEvent]:
        events: list[TwinEvent] = []
        requested = float(self.inputs.get("speed", self.state["speed"]))
        self.state["speed"] = max(0.0, min(float(self.config["max_speed"]), requested))
        self.outputs["speed"] = self.state["speed"]

        if self.state["speed"] == 0.0 and self.twin_state != TwinState.IDLE:
            changed, previous, current = self.fsm.force(TwinState.IDLE)
            if changed:
                events.append(
                    self.emit(EventType.STATE_CHANGE, {"from": previous.value, "to": current.value, "reason": "stopped"})
                )
        elif self.state["speed"] > 0.0 and self.twin_state == TwinState.IDLE:
            changed, previous, current = self.fsm.force(TwinState.RUNNING)
            if changed:
                events.append(
                    self.emit(EventType.STATE_CHANGE, {"from": previous.value, "to": current.value, "reason": "running"})
                )
        return events
