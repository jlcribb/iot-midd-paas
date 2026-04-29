"""Simple energy node twin model."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable

from ..core.entity import DigitalTwinEntity
from ..core.events import EventType, TwinEvent
from ..core.state_machine import TwinState


class EnergyNodeTwin(DigitalTwinEntity):
    model_type = "energy_node"

    def __init__(
        self,
        entity_id: str,
        plant_id: str,
        config: Dict[str, Any] | None = None,
        state: Dict[str, Any] | None = None,
    ) -> None:
        cfg = {"max_kw": 50.0, "target_kw": 10.0, "ramp_kw_per_sec": 2.0}
        if config:
            cfg.update(config)
        st = {"kw": 0.0}
        if state:
            st.update(state)
        super().__init__(entity_id=entity_id, plant_id=plant_id, config=cfg, state=st)
        self.fsm.force(TwinState.RUNNING)

    @classmethod
    def io_schema(cls) -> Dict[str, Any]:
        return {"inputs": {"setpoint_kw": {"type": "float"}}, "outputs": {"kw": {"type": "float"}}}

    def update(self, dt_seconds: float, now: datetime, mode: str) -> Iterable[TwinEvent]:
        events: list[TwinEvent] = []
        target = float(self.inputs.get("setpoint_kw", self.config["target_kw"]))
        target = max(0.0, min(float(self.config["max_kw"]), target))

        if mode != "REAL":
            current = float(self.state["kw"])
            delta_limit = float(self.config["ramp_kw_per_sec"]) * dt_seconds
            if target > current:
                current = min(target, current + delta_limit)
            else:
                current = max(target, current - delta_limit)
            self.state["kw"] = current

        if float(self.state["kw"]) >= float(self.config["max_kw"]):
            events.append(self.emit(EventType.THRESHOLD_CROSSED, {"kind": "max_power_reached", "kw": self.state["kw"]}))

        self.outputs["kw"] = float(self.state["kw"])
        return events
