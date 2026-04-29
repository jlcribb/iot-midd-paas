"""MixingUnit digital twin model (mandatory example use case)."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, Iterable

from ..core.entity import DigitalTwinEntity
from ..core.events import EventType, TwinEvent
from ..core.state_machine import TwinState


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


class MixingUnitTwin(DigitalTwinEntity):
    model_type = "mixing_unit"

    def __init__(
        self,
        entity_id: str,
        plant_id: str,
        config: Dict[str, Any] | None = None,
        state: Dict[str, Any] | None = None,
    ) -> None:
        default_config = {
            "target_ratio": 0.6,
            "ratio_tolerance": 0.05,
            "max_level": 100.0,
            "low_level_threshold": 10.0,
            "overflow_threshold": 95.0,
            "feed_rate": 1.2,
            "mix_rate": 1.0,
            "drain_rate": 0.25,
            "auto_start": True,
        }
        merged_config = _deep_merge(default_config, config or {})
        default_state = {
            "levels": {"blue": 50.0, "red": 50.0, "mix": 0.0},
            "ratio": 0.5,
            "valves": {"blue": True, "red": True, "outlet": False},
            "alerts": {"low_level": False, "overflow": False},
            "fault": False,
            "mix_components": {"blue": 0.0, "red": 0.0},
            "metrics": {"last_batch_blue": 0.0, "last_batch_red": 0.0},
            "_ratio_out": False,
        }
        merged_state = _deep_merge(default_state, state or {})

        super().__init__(entity_id=entity_id, plant_id=plant_id, config=merged_config, state=merged_state)
        if self.config.get("auto_start", True):
            self.fsm.force(TwinState.RUNNING)
        self._configure_fsm()

    @classmethod
    def config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "target_ratio": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "ratio_tolerance": {"type": "number", "minimum": 0.0, "maximum": 0.5},
                "max_level": {"type": "number", "minimum": 1},
                "low_level_threshold": {"type": "number", "minimum": 0},
                "overflow_threshold": {"type": "number", "minimum": 0},
                "feed_rate": {"type": "number", "minimum": 0},
                "mix_rate": {"type": "number", "minimum": 0},
                "drain_rate": {"type": "number", "minimum": 0},
                "auto_start": {"type": "boolean"},
            },
        }

    @classmethod
    def io_schema(cls) -> Dict[str, Any]:
        return {
            "inputs": {
                "blue": {"type": "float", "description": "External blue liquid inflow"},
                "red": {"type": "float", "description": "External red liquid inflow"},
            },
            "outputs": {
                "mix": {"type": "object", "description": "Current mix level and ratio"},
                "alerts": {"type": "object", "description": "Active alert flags"},
            },
        }

    def _configure_fsm(self) -> None:
        self.fsm.add_transition(
            name="ratio_out_of_tolerance",
            sources={TwinState.RUNNING},
            target=TwinState.CONTROL,
            condition=lambda entity, event: abs(entity.state["ratio"] - entity.config["target_ratio"])
            > entity.config["ratio_tolerance"],
        )
        self.fsm.add_transition(
            name="ratio_stable_again",
            sources={TwinState.CONTROL},
            target=TwinState.RUNNING,
            condition=lambda entity, event: abs(entity.state["ratio"] - entity.config["target_ratio"])
            <= entity.config["ratio_tolerance"],
        )
        self.fsm.add_transition(
            name="fault_detected",
            sources={TwinState.IDLE, TwinState.RUNNING, TwinState.CONTROL},
            target=TwinState.ERROR,
            condition=lambda entity, event: bool(entity.state.get("fault", False)),
        )

    def _clamp(self, value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))

    def _apply_external_inputs(self, dt_seconds: float) -> None:
        levels = self.state["levels"]
        max_level = float(self.config["max_level"])
        blue_in = float(self.inputs.get("blue", 0.0))
        red_in = float(self.inputs.get("red", 0.0))
        levels["blue"] = self._clamp(levels["blue"] + (blue_in * dt_seconds), 0.0, max_level)
        levels["red"] = self._clamp(levels["red"] + (red_in * dt_seconds), 0.0, max_level)

    def _control_valves(self) -> bool:
        valves = self.state["valves"]
        previous = dict(valves)
        target = float(self.config["target_ratio"])
        tolerance = float(self.config["ratio_tolerance"])
        ratio = float(self.state["ratio"])

        if ratio < target - tolerance:
            valves["blue"] = True
            valves["red"] = False
        elif ratio > target + tolerance:
            valves["blue"] = False
            valves["red"] = True
        else:
            valves["blue"] = True
            valves["red"] = True

        # Open outlet if mixing tank is high enough.
        valves["outlet"] = self.state["levels"]["mix"] >= (0.85 * float(self.config["overflow_threshold"]))
        return previous != valves

    def _mix_step(self, dt_seconds: float) -> None:
        levels = self.state["levels"]
        components = self.state["mix_components"]

        target_ratio = float(self.config["target_ratio"])
        mix_rate = float(self.config["mix_rate"]) * dt_seconds
        drain_rate = float(self.config["drain_rate"]) * dt_seconds

        blue_weight = target_ratio if self.state["valves"]["blue"] else 0.0
        red_weight = (1.0 - target_ratio) if self.state["valves"]["red"] else 0.0
        total_weight = blue_weight + red_weight
        if total_weight <= 0:
            blue_weight, red_weight = 0.5, 0.5
        else:
            blue_weight /= total_weight
            red_weight /= total_weight

        desired_blue = mix_rate * blue_weight
        desired_red = mix_rate * red_weight
        take_blue = min(levels["blue"], desired_blue)
        take_red = min(levels["red"], desired_red)

        levels["blue"] -= take_blue
        levels["red"] -= take_red
        levels["mix"] += take_blue + take_red
        components["blue"] += take_blue
        components["red"] += take_red

        if self.state["valves"]["outlet"] and levels["mix"] > 0:
            drained = min(levels["mix"], drain_rate)
            levels["mix"] -= drained
            total_components = components["blue"] + components["red"]
            if total_components > 0:
                blue_fraction = components["blue"] / total_components
                components["blue"] = max(0.0, components["blue"] - (drained * blue_fraction))
                components["red"] = max(0.0, components["red"] - (drained * (1.0 - blue_fraction)))

        self.state["metrics"]["last_batch_blue"] = take_blue
        self.state["metrics"]["last_batch_red"] = take_red

    def _recompute_ratio(self) -> None:
        components = self.state["mix_components"]
        total = float(components["blue"] + components["red"])
        if total <= 0:
            self.state["ratio"] = 0.5
            return
        self.state["ratio"] = float(components["blue"] / total)

    def _check_alerts(self) -> list[TwinEvent]:
        events: list[TwinEvent] = []
        levels = self.state["levels"]
        alerts = self.state["alerts"]
        low_threshold = float(self.config["low_level_threshold"])
        overflow_threshold = float(self.config["overflow_threshold"])

        low_active = levels["blue"] <= low_threshold or levels["red"] <= low_threshold
        overflow_active = levels["mix"] >= overflow_threshold

        if low_active and not alerts["low_level"]:
            alerts["low_level"] = True
            events.append(
                self.emit(
                    EventType.ALERT,
                    {"kind": "low_level", "levels": dict(levels), "threshold": low_threshold},
                )
            )
        elif not low_active and alerts["low_level"]:
            alerts["low_level"] = False
            events.append(
                self.emit(
                    EventType.STATE_CHANGE,
                    {"kind": "low_level_cleared", "levels": dict(levels)},
                )
            )

        if overflow_active and not alerts["overflow"]:
            alerts["overflow"] = True
            self.state["fault"] = True
            events.append(
                self.emit(
                    EventType.ALERT,
                    {"kind": "overflow", "levels": dict(levels), "threshold": overflow_threshold},
                )
            )
        elif not overflow_active and alerts["overflow"]:
            alerts["overflow"] = False
            events.append(
                self.emit(
                    EventType.STATE_CHANGE,
                    {"kind": "overflow_cleared", "levels": dict(levels)},
                )
            )

        ratio_error = abs(float(self.state["ratio"]) - float(self.config["target_ratio"]))
        ratio_out = ratio_error > float(self.config["ratio_tolerance"])
        if ratio_out and not self.state.get("_ratio_out", False):
            events.append(
                self.emit(
                    EventType.THRESHOLD_CROSSED,
                    {
                        "kind": "ratio",
                        "ratio": self.state["ratio"],
                        "target_ratio": self.config["target_ratio"],
                        "ratio_error": ratio_error,
                    },
                )
            )
        self.state["_ratio_out"] = ratio_out
        return events

    def update(self, dt_seconds: float, now: datetime, mode: str) -> Iterable[TwinEvent]:
        events: list[TwinEvent] = []

        if mode != "REAL" and self.twin_state in {TwinState.RUNNING, TwinState.CONTROL}:
            self._apply_external_inputs(dt_seconds)
            changed = self._control_valves()
            if changed:
                events.append(
                    self.emit(
                        EventType.STATE_CHANGE,
                        {"kind": "valve_change", "valves": dict(self.state["valves"])},
                    )
                )
            self._mix_step(dt_seconds)

        self._recompute_ratio()
        events.extend(self._check_alerts())

        changed, previous, current = self.fsm.evaluate(self, None)
        if changed:
            events.append(
                self.emit(
                    EventType.STATE_CHANGE,
                    {"from": previous.value, "to": current.value, "reason": "fsm_rule"},
                )
            )

        self.outputs["mix"] = {"level": self.state["levels"]["mix"], "ratio": self.state["ratio"]}
        self.outputs["alerts"] = dict(self.state["alerts"])
        return events

    def apply_command(self, command: str, payload: Dict[str, Any] | None = None) -> list[TwinEvent]:
        payload = payload or {}
        command_lower = command.lower()
        events: list[TwinEvent] = []

        if command_lower == "set_target_ratio":
            ratio = float(payload.get("target_ratio", self.config["target_ratio"]))
            self.config["target_ratio"] = self._clamp(ratio, 0.0, 1.0)
            events.append(
                self.emit(
                    EventType.STATE_CHANGE,
                    {"kind": "target_ratio_updated", "target_ratio": self.config["target_ratio"]},
                )
            )
        elif command_lower in {"open_valve", "close_valve"}:
            valve_name = payload.get("valve")
            if valve_name in self.state["valves"]:
                self.state["valves"][valve_name] = command_lower == "open_valve"
                events.append(
                    self.emit(
                        EventType.STATE_CHANGE,
                        {"kind": "manual_valve_change", "valves": dict(self.state["valves"])},
                    )
                )
        elif command_lower == "drain_mix":
            amount = max(0.0, float(payload.get("amount", 0.0)))
            drain_amount = min(self.state["levels"]["mix"], amount)
            self.state["levels"]["mix"] -= drain_amount
            events.append(
                self.emit(
                    EventType.STATE_CHANGE,
                    {"kind": "manual_drain", "drained": drain_amount, "mix_level": self.state["levels"]["mix"]},
                )
            )
        elif command_lower == "ack_alerts":
            self.state["alerts"] = {"low_level": False, "overflow": False}
            self.state["fault"] = False
            events.append(self.emit(EventType.STATE_CHANGE, {"kind": "alerts_acknowledged"}))
        else:
            events.extend(super().apply_command(command, payload))

        changed, previous, current = self.fsm.evaluate(self, None)
        if changed:
            events.append(
                self.emit(
                    EventType.STATE_CHANGE,
                    {"from": previous.value, "to": current.value, "reason": "command"},
                )
            )
        return events

    def ingest_device_state(self, payload: Dict[str, Any]) -> list[TwinEvent]:
        levels = payload.get("levels")
        valves = payload.get("valves")
        if isinstance(levels, dict):
            self.state["levels"] = _deep_merge(self.state["levels"], levels)
        if isinstance(valves, dict):
            self.state["valves"] = _deep_merge(self.state["valves"], valves)
        if "ratio" in payload:
            self.state["ratio"] = float(payload["ratio"])
        if payload.get("fault") is not None:
            self.state["fault"] = bool(payload.get("fault"))

        events = [
            self.emit(
                EventType.STATE_CHANGE,
                {"source": "device", "payload": payload},
            )
        ]
        changed, previous, current = self.fsm.evaluate(self, None)
        if changed:
            events.append(
                self.emit(
                    EventType.STATE_CHANGE,
                    {"from": previous.value, "to": current.value, "reason": "device_sync"},
                )
            )
        return events

    def handle_event(self, event: TwinEvent) -> list[TwinEvent]:
        if event.entity_id == self.entity_id and event.type == EventType.DEVICE_DISCONNECTED:
            self.state["fault"] = True
        return super().handle_event(event)
