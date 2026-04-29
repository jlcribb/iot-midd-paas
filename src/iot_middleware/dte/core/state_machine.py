"""Finite state machine primitives for twin entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from .events import TwinEvent

try:  # Python 3.11+
    from enum import StrEnum
except ImportError:  # pragma: no cover
    class StrEnum(str, Enum):
        pass


class TwinState(StrEnum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    CONTROL = "CONTROL"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"


Condition = Callable[[object, Optional[TwinEvent]], bool]


@dataclass
class TransitionRule:
    name: str
    sources: set[TwinState]
    target: TwinState
    condition: Condition

    def applies(self, current: TwinState, entity: object, event: Optional[TwinEvent]) -> bool:
        if self.sources and current not in self.sources:
            return False
        return bool(self.condition(entity, event))


@dataclass
class EventTransition:
    event_type: str
    sources: set[TwinState]
    target: TwinState
    condition: Optional[Condition] = None

    def applies(self, event: TwinEvent, current: TwinState, entity: object) -> bool:
        if event.type != self.event_type:
            return False
        if self.sources and current not in self.sources:
            return False
        if self.condition and not self.condition(entity, event):
            return False
        return True


@dataclass
class StateMachine:
    current_state: TwinState = TwinState.IDLE
    transitions: list[TransitionRule] = field(default_factory=list)
    event_transitions: list[EventTransition] = field(default_factory=list)

    def add_transition(
        self,
        name: str,
        sources: set[TwinState],
        target: TwinState,
        condition: Condition,
    ) -> None:
        self.transitions.append(
            TransitionRule(name=name, sources=sources, target=target, condition=condition)
        )

    def add_event_transition(
        self,
        event_type: str,
        sources: set[TwinState],
        target: TwinState,
        condition: Optional[Condition] = None,
    ) -> None:
        self.event_transitions.append(
            EventTransition(
                event_type=event_type,
                sources=sources,
                target=target,
                condition=condition,
            )
        )

    def force(self, state: TwinState) -> tuple[bool, TwinState, TwinState]:
        if state == self.current_state:
            return False, self.current_state, self.current_state
        previous = self.current_state
        self.current_state = state
        return True, previous, self.current_state

    def evaluate(self, entity: object, event: Optional[TwinEvent] = None) -> tuple[bool, TwinState, TwinState]:
        previous = self.current_state

        if event is not None:
            for transition in self.event_transitions:
                if transition.applies(event=event, current=self.current_state, entity=entity):
                    self.current_state = transition.target
                    return True, previous, self.current_state

        for rule in self.transitions:
            if rule.applies(current=self.current_state, entity=entity, event=event):
                self.current_state = rule.target
                return True, previous, self.current_state

        return False, previous, self.current_state
