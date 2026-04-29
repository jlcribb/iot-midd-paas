"""FastAPI app bootstrap for the Digital Twin Engine."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Optional

from fastapi import FastAPI

from ..core.engine import DigitalTwinEngine, EngineMode
from ..core.events import EventType, TwinEvent
from ..core.scheduler import TaskPriority
from ..infrastructure.mqtt_adapter import MQTTAdapter, MQTTConfig
from ..infrastructure.core_schema_sync import sync_plant_to_core_schema
from ..infrastructure.persistence import SQLiteStore
from ..infrastructure.rule_engine import Rule, RuleEngine
from ..loader.plant_loader import PlantLoader
from ..models import build_default_registry
from .routes import router


logger = logging.getLogger(__name__)


def _resolve_mode(raw_mode: str) -> EngineMode:
    normalized = raw_mode.strip().upper()
    try:
        return EngineMode[normalized]
    except KeyError as exc:
        valid = ", ".join([member.name for member in EngineMode])
        raise ValueError(f"Invalid DTE_MODE '{raw_mode}'. Expected one of: {valid}") from exc


def _register_default_tasks(engine: DigitalTwinEngine) -> None:
    # HIGH: safety checks
    def safety_checks(*, engine: DigitalTwinEngine, now, event=None):
        alerts: list[TwinEvent] = []
        for entity in engine.entities.values():
            if entity.state.get("fault"):
                alerts.append(
                    TwinEvent(
                        entity_id=entity.entity_id,
                        plant_id=entity.plant_id,
                        type=EventType.ALERT,
                        payload={"kind": "safety_fault", "state_machine": entity.twin_state.value},
                    )
                )
        return alerts

    # MEDIUM: control loop heartbeat (observable control cadence)
    def control_heartbeat(*, engine: DigitalTwinEngine, now, event=None):
        return []

    # LOW: housekeeping
    def housekeeping(*, engine: DigitalTwinEngine, now, event=None):
        return []

    engine.scheduler.add_periodic_task(
        name="safety_checks",
        interval_seconds=1.0,
        callback=safety_checks,
        priority=TaskPriority.HIGH,
        start_immediately=True,
    )
    engine.scheduler.add_periodic_task(
        name="control_heartbeat",
        interval_seconds=2.0,
        callback=control_heartbeat,
        priority=TaskPriority.MEDIUM,
        start_immediately=True,
    )
    engine.scheduler.add_periodic_task(
        name="housekeeping",
        interval_seconds=5.0,
        callback=housekeeping,
        priority=TaskPriority.LOW,
        start_immediately=False,
    )


def build_engine(
    *,
    mode: Optional[EngineMode] = None,
    tick_rate_hz: Optional[float] = None,
    sqlite_path: Optional[str] = None,
    plant_config_path: Optional[str] = None,
) -> DigitalTwinEngine:
    mode = mode or _resolve_mode(os.getenv("DTE_MODE", "SIMULATION"))
    tick_rate = tick_rate_hz if tick_rate_hz is not None else float(os.getenv("DTE_TICK_RATE", "2.0"))
    sqlite_path = sqlite_path or os.getenv("DTE_SQLITE_PATH", "data/dte_engine.sqlite3")

    store = SQLiteStore(sqlite_path)
    rule_engine = RuleEngine()
    rule_engine.add_rule(
        Rule(
            name="mix-level-critical",
            entity_id=None,
            path="levels.mix",
            op=">=",
            value=98.0,
            then_type=EventType.ALERT,
            then_payload={"kind": "rule_mix_high"},
        )
    )

    engine = DigitalTwinEngine(
        tick_rate_hz=tick_rate,
        mode=mode,
        store=store,
        mqtt_adapter=None,
        rule_engine=rule_engine,
        concurrent_updates=True,
        snapshot_every_ticks=20,
    )

    if mode != EngineMode.SIMULATION:
        mqtt_config = MQTTConfig(
            host=os.getenv("MQTT_HOST", "localhost"),
            port=int(os.getenv("MQTT_PORT", "1883")),
            client_id=os.getenv("DTE_MQTT_CLIENT_ID", "dte-engine"),
            username=os.getenv("MQTT_USERNAME"),
            password=os.getenv("MQTT_PASSWORD"),
            qos=int(os.getenv("MQTT_QOS", "1")),
        )
        engine.mqtt_adapter = MQTTAdapter(
            mqtt_config,
            on_device_state=engine.ingest_device_state,
            on_device_event=lambda entity_id, payload: engine.ingest_device_disconnect(entity_id, payload),
        )

    registry = build_default_registry()
    loader = PlantLoader(registry)
    resolved_plant_path = (
        Path(plant_config_path)
        if plant_config_path
        else Path(os.getenv("DTE_PLANT_CONFIG", Path(__file__).resolve().parent.parent / "examples" / "plant_mixing.json"))
    )
    load_result = loader.load_from_file(resolved_plant_path, engine)
    logger.info("Loaded plant config: %s", load_result)
    try:
        if os.getenv("DTE_SYNC_CORE_SCHEMA", "true").strip().lower() in {"1", "true", "yes", "on"}:
            import json

            with open(resolved_plant_path, "r", encoding="utf-8") as handle:
                plant_payload = json.load(handle)
            core_sync = sync_plant_to_core_schema(plant_payload)
            logger.info("DTE core schema sync OK: %s", core_sync)
    except Exception as exc:
        logger.warning("DTE core schema sync failed (continuing): %s", exc)

    _register_default_tasks(engine)
    return engine


def create_app() -> FastAPI:
    dte_engine = build_engine()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await dte_engine.start()
        task = asyncio.create_task(dte_engine.run_async())
        app.state.dte_engine_task = task
        try:
            yield
        finally:
            await dte_engine.stop()
            with suppress(asyncio.CancelledError):
                task.cancel()
                await task

    app = FastAPI(
        title="Digital Twin Engine API",
        version="0.1.0",
        description="Simulation and real-time orchestration engine for multi-plant digital twins.",
        lifespan=lifespan,
    )
    app.state.dte_engine = dte_engine
    app.include_router(router)
    return app


app = create_app()
