"""Simple storage tank twin model."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable

from ..core.entity import DigitalTwinEntity
from ..core.events import EventType, TwinEvent
from ..core.state_machine import TwinState


class TankTwin(DigitalTwinEntity):
    model_type = "tank"

    def __init__(
        self,
        entity_id: str,
        plant_id: str,
        config: Dict[str, Any] | None = None,
        state: Dict[str, Any] | None = None,
    ) -> None:
        cfg = {
            "capacity": 100.0,
            "low_threshold": 10.0,
            "high_threshold": 90.0,
            "default_outflow": 0.0,
        }
        if config:
            cfg.update(config)
        st = {"level": 0.0, "inflow": 0.0, "outflow": cfg["default_outflow"], "alert_high": False, "alert_low": False}
        if state:
            st.update(state)
        super().__init__(entity_id=entity_id, plant_id=plant_id, config=cfg, state=st)
        self.fsm.force(TwinState.RUNNING)

    @classmethod
    def io_schema(cls) -> Dict[str, Any]:
        return {
            "inputs": {"inflow": {"type": "float"}, "outflow": {"type": "float"}},
            "outputs": {"level": {"type": "float"}},
        }

    def update(self, dt_seconds: float, now: datetime, mode: str) -> Iterable[TwinEvent]:
        events: list[TwinEvent] = []
        inflow = self._to_float(self.inputs.get("inflow", self.state.get("inflow", 0.0)))
        outflow = self._to_float(self.inputs.get("outflow", self.state.get("outflow", 0.0)))
        self.state["inflow"] = inflow
        self.state["outflow"] = outflow

        if mode != "REAL" and self.twin_state in {TwinState.RUNNING, TwinState.CONTROL}:
            self.state["level"] = max(
                0.0,
                min(float(self.config["capacity"]), float(self.state["level"]) + (inflow - outflow) * dt_seconds),
            )

        level = float(self.state["level"])
        if level <= float(self.config["low_threshold"]) and not self.state["alert_low"]:
            self.state["alert_low"] = True
            events.append(self.emit(EventType.ALERT, {"kind": "tank_low", "level": level}))
        elif level > float(self.config["low_threshold"]) and self.state["alert_low"]:
            self.state["alert_low"] = False

        if level >= float(self.config["high_threshold"]) and not self.state["alert_high"]:
            self.state["alert_high"] = True
            events.append(self.emit(EventType.THRESHOLD_CROSSED, {"kind": "tank_high", "level": level}))
        elif level < float(self.config["high_threshold"]) and self.state["alert_high"]:
            self.state["alert_high"] = False

        self.outputs["level"] = level
        return events

    def _to_float(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, dict):
            for key in ("value", "level", "flow", "inflow", "outflow"):
                item = value.get(key)
                if isinstance(item, (int, float)):
                    return float(item)
            return 0.0
        try:
            return float(value)
        except Exception:
            return 0.0
