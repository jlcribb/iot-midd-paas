"""Runtime engine for simulation, hybrid and real-time digital twin orchestration."""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, Optional

from .entity import DigitalTwinEntity
from .events import EventBus, EventType, TwinEvent
from .scheduler import PriorityScheduler, ScheduledTask

if False:  # pragma: no cover
    from ..infrastructure.mqtt_adapter import MQTTAdapter
    from ..infrastructure.persistence import SQLiteStore
    from ..infrastructure.rule_engine import RuleEngine


logger = logging.getLogger(__name__)

try:  # Python 3.11+
    from enum import StrEnum
except ImportError:  # pragma: no cover
    class StrEnum(str, Enum):
        pass


class EngineMode(StrEnum):
    SIMULATION = "SIMULATION"
    HYBRID = "HYBRID"
    REAL = "REAL"


@dataclass
class Connection:
    from_entity: str
    from_output: str
    to_entity: str
    to_input: str


@dataclass
class PlantRuntime:
    plant_id: str
    entities: dict[str, DigitalTwinEntity] = field(default_factory=dict)
    connections: list[Connection] = field(default_factory=list)


class DigitalTwinEngine:
    """Main engine orchestrating entities, events, scheduler and integrations."""

    def __init__(
        self,
        *,
        tick_rate_hz: float = 1.0,
        mode: EngineMode = EngineMode.SIMULATION,
        event_bus: Optional[EventBus] = None,
        scheduler: Optional[PriorityScheduler] = None,
        store: Optional["SQLiteStore"] = None,
        mqtt_adapter: Optional["MQTTAdapter"] = None,
        rule_engine: Optional["RuleEngine"] = None,
        concurrent_updates: bool = True,
        snapshot_every_ticks: int = 10,
    ) -> None:
        self.tick_rate_hz = tick_rate_hz
        self.mode = mode
        self.event_bus = event_bus or EventBus()
        self.scheduler = scheduler or PriorityScheduler()
        self.store = store
        self.mqtt_adapter = mqtt_adapter
        self.rule_engine = rule_engine
        self.concurrent_updates = concurrent_updates
        self.snapshot_every_ticks = snapshot_every_ticks

        self.plants: dict[str, PlantRuntime] = {}
        self.entities: dict[str, DigitalTwinEntity] = {}
        self.simulation_speed = 1.0
        self.tick_count = 0

        self._running = False
        self._loop_started_at = time.monotonic()
        self._last_tick_monotonic = self._loop_started_at
        self._event_route_token: Optional[int] = None
        self._event_store_token: Optional[int] = None

        self._register_default_event_listeners()

    def _register_default_event_listeners(self) -> None:
        self._event_route_token = self.event_bus.subscribe(self._route_event_to_entity)
        if self.store is not None:
            self._event_store_token = self.event_bus.subscribe(self._persist_event)

    def set_mode(self, mode: EngineMode) -> None:
        self.mode = mode

    def set_simulation_speed(self, factor: float) -> None:
        if factor <= 0:
            raise ValueError("simulation speed factor must be > 0")
        self.simulation_speed = factor

    def add_plant(self, plant_id: str) -> PlantRuntime:
        if plant_id not in self.plants:
            self.plants[plant_id] = PlantRuntime(plant_id=plant_id)
        return self.plants[plant_id]

    def add_entity(self, entity: DigitalTwinEntity, plant_id: Optional[str] = None) -> None:
        target_plant = plant_id or entity.plant_id
        plant = self.add_plant(target_plant)
        plant.entities[entity.entity_id] = entity
        self.entities[entity.entity_id] = entity

    def add_connection(self, plant_id: str, connection: Connection) -> None:
        plant = self.add_plant(plant_id)
        plant.connections.append(connection)

    def list_twins(self) -> list[dict[str, Any]]:
        return [entity.to_dict() for entity in self.entities.values()]

    def get_twin(self, entity_id: str) -> Optional[DigitalTwinEntity]:
        return self.entities.get(entity_id)

    def list_plants(self) -> list[dict[str, Any]]:
        return [
            {
                "plant_id": plant.plant_id,
                "twin_count": len(plant.entities),
                "connection_count": len(plant.connections),
                "twins": sorted(plant.entities.keys()),
            }
            for plant in self.plants.values()
        ]

    def _persist_event(self, event: TwinEvent) -> None:
        if self.store is not None:
            self.store.persist_event(event)

    def _route_event_to_entity(self, event: TwinEvent) -> None:
        entity = self.entities.get(event.entity_id)
        if entity is None:
            return
        generated = entity.handle_event(event)
        if generated:
            self.event_bus.publish_many(generated)

    def ingest_device_state(self, entity_id: str, payload: dict[str, Any]) -> None:
        entity = self.entities.get(entity_id)
        if entity is None:
            logger.warning("MQTT state received for unknown entity '%s'", entity_id)
            return
        events = entity.ingest_device_state(payload)
        self.event_bus.publish_many(events)

    def ingest_device_disconnect(self, entity_id: str, payload: Optional[dict[str, Any]] = None) -> None:
        self.event_bus.publish(
            TwinEvent(
                entity_id=entity_id,
                plant_id=self.entities.get(entity_id).plant_id if entity_id in self.entities else None,
                type=EventType.DEVICE_DISCONNECTED,
                payload=payload or {"reason": "device_disconnected"},
            )
        )

    async def dispatch_command(
        self, entity_id: str, command: str, payload: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        entity = self.entities.get(entity_id)
        if entity is None:
            raise KeyError(f"Unknown twin '{entity_id}'")

        generated = entity.apply_command(command, payload)
        self.event_bus.publish_many(generated)

        if self.mqtt_adapter is not None and self.mode != EngineMode.SIMULATION:
            self.mqtt_adapter.publish_command(entity_id, {"command": command, "payload": payload or {}})

        return {
            "entity_id": entity_id,
            "command": command,
            "accepted": True,
            "state_machine": entity.twin_state.value,
        }

    async def start(self) -> None:
        if self.mqtt_adapter is not None and self.mode != EngineMode.SIMULATION:
            self.mqtt_adapter.connect()
            self.mqtt_adapter.subscribe_for_twins()
        self._running = True
        self._loop_started_at = time.monotonic()
        self._last_tick_monotonic = self._loop_started_at

    async def stop(self) -> None:
        self._running = False
        if self.mqtt_adapter is not None:
            self.mqtt_adapter.disconnect()

    def _normalize_events(self, result: Any) -> list[TwinEvent]:
        if result is None:
            return []
        if isinstance(result, TwinEvent):
            return [result]
        if isinstance(result, list):
            return [item for item in result if isinstance(item, TwinEvent)]
        if isinstance(result, tuple):
            return [item for item in result if isinstance(item, TwinEvent)]
        if isinstance(result, Iterable):
            return [item for item in result if isinstance(item, TwinEvent)]
        return []

    async def _run_task(self, task: ScheduledTask, *, now: datetime, event: Optional[TwinEvent] = None) -> None:
        try:
            result = task.callback(engine=self, now=now, event=event)
            if inspect.isawaitable(result):
                result = await result
            self.event_bus.publish_many(self._normalize_events(result))
        except Exception as exc:  # pragma: no cover - safety net
            logger.exception("Scheduler task '%s' failed: %s", task.name, exc)

    async def _run_periodic_tasks(self, now: datetime) -> None:
        due_tasks = self.scheduler.due_periodic_tasks()
        for task in due_tasks:
            await self._run_task(task, now=now)
            self.scheduler.reschedule_periodic(task)

    async def _run_event_tasks(self, events: list[TwinEvent], now: datetime) -> None:
        for event in events:
            for task in self.scheduler.tasks_for_event(event.type, event.entity_id):
                await self._run_task(task, now=now, event=event)

    async def _update_entity(self, entity: DigitalTwinEntity, dt_seconds: float, now: datetime) -> list[TwinEvent]:
        result = entity.update(dt_seconds=dt_seconds, now=now, mode=self.mode.value)
        if inspect.isawaitable(result):
            result = await result
        entity.last_updated = now
        return self._normalize_events(result)

    def _wire_connections(self) -> None:
        for plant in self.plants.values():
            for connection in plant.connections:
                source = self.entities.get(connection.from_entity)
                target = self.entities.get(connection.to_entity)
                if source is None or target is None:
                    continue
                target.set_input(connection.to_input, source.get_output(connection.from_output))

    def _persist_states(self, now: datetime) -> None:
        if self.store is None:
            return
        for entity in self.entities.values():
            self.store.persist_state(
                plant_id=entity.plant_id,
                entity_id=entity.entity_id,
                state=entity.state,
                timestamp=now,
            )

    def _persist_snapshot_if_due(self, now: datetime) -> None:
        if self.store is None or self.snapshot_every_ticks <= 0:
            return
        if self.tick_count % self.snapshot_every_ticks != 0:
            return
        self.store.persist_snapshot(
            payload={
                "mode": self.mode.value,
                "tick_count": self.tick_count,
                "timestamp": now.isoformat(),
                "plants": self.list_plants(),
                "twins": self.list_twins(),
            },
            timestamp=now,
        )

    def _publish_mqtt_state(self, events: list[TwinEvent]) -> None:
        if self.mqtt_adapter is None or self.mode == EngineMode.SIMULATION:
            return
        for entity in self.entities.values():
            self.mqtt_adapter.publish_state(entity.entity_id, entity.state)
        for event in events:
            self.mqtt_adapter.publish_event(event.entity_id, event.to_dict())

    def _run_rules(self) -> None:
        if self.rule_engine is None:
            return
        for entity in self.entities.values():
            self.event_bus.publish_many(self.rule_engine.evaluate(entity))

    async def tick(self) -> list[TwinEvent]:
        now = datetime.now(timezone.utc)
        now_monotonic = time.monotonic()
        dt_seconds = max(0.0, now_monotonic - self._last_tick_monotonic) * self.simulation_speed
        self._last_tick_monotonic = now_monotonic

        await self._run_periodic_tasks(now)

        events_from_updates: list[TwinEvent] = []
        if self.concurrent_updates:
            coroutines = [self._update_entity(entity, dt_seconds, now) for entity in self.entities.values()]
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):  # pragma: no cover - safety net
                    logger.exception("Entity update failed: %s", result)
                    continue
                events_from_updates.extend(result)
        else:
            for entity in self.entities.values():
                try:
                    events_from_updates.extend(await self._update_entity(entity, dt_seconds, now))
                except Exception as exc:  # pragma: no cover - safety net
                    logger.exception("Entity '%s' update failed: %s", entity.entity_id, exc)

        self._wire_connections()
        self._persist_states(now)
        self._run_rules()
        self.event_bus.publish_many(events_from_updates)

        processed = await self.event_bus.drain_async(max_events=10_000)
        if processed:
            await self._run_event_tasks(processed, now=now)
            processed.extend(await self.event_bus.drain_async(max_events=10_000))

        self.tick_count += 1
        self._persist_snapshot_if_due(now)
        self._publish_mqtt_state(processed)
        return processed

    async def run_async(self, max_ticks: Optional[int] = None) -> None:
        if not self._running:
            await self.start()
        ticks_done = 0
        while self._running and (max_ticks is None or ticks_done < max_ticks):
            started = time.monotonic()
            await self.tick()
            ticks_done += 1
            elapsed = time.monotonic() - started
            interval = (1.0 / self.tick_rate_hz) if self.tick_rate_hz > 0 else 0.0
            sleep_time = max(0.0, (interval / self.simulation_speed) - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    def run_sync(self, max_ticks: Optional[int] = None) -> None:
        asyncio.run(self.run_async(max_ticks=max_ticks))
