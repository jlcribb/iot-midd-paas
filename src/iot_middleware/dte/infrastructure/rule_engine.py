"""Lightweight rule engine (if/then) for twin states."""

from __future__ import annotations

import operator
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from ..core.entity import DigitalTwinEntity
from ..core.events import EventType, TwinEvent


OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}


@dataclass
class Rule:
    name: str
    entity_id: Optional[str]
    path: str
    op: str
    value: Any
    then_type: str = EventType.ALERT
    then_payload: Dict[str, Any] = field(default_factory=dict)

    def applies(self, entity: DigitalTwinEntity) -> bool:
        if self.entity_id and self.entity_id != entity.entity_id:
            return False
        current = _get_nested(entity.state, self.path)
        compare = OPERATORS.get(self.op)
        if compare is None:
            return False
        try:
            return bool(compare(current, self.value))
        except Exception:
            return False


def _get_nested(data: dict[str, Any], dotted_path: str) -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


class RuleEngine:
    def __init__(self) -> None:
        self._rules: list[Rule] = []

    def add_rule(self, rule: Rule) -> None:
        self._rules.append(rule)

    def evaluate(self, entity: DigitalTwinEntity) -> list[TwinEvent]:
        events: list[TwinEvent] = []
        for rule in self._rules:
            if not rule.applies(entity):
                continue
            payload = {"rule": rule.name, "path": rule.path, "op": rule.op, "value": rule.value}
            payload.update(rule.then_payload)
            events.append(
                TwinEvent(
                    entity_id=entity.entity_id,
                    plant_id=entity.plant_id,
                    type=rule.then_type,
                    payload=payload,
                )
            )
        return events
