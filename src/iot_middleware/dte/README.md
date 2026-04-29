# Digital Twin Engine (DTE)

Modular runtime to execute digital twins in:

- `SIMULATION` mode (no hardware)
- `HYBRID` mode (sim + device synchronization)
- `REAL` mode (device-driven state)

## Architecture

```text
dte/
  core/
    entity.py        # Base twin entity
    events.py        # Event bus + filtering
    state_machine.py # Per-entity FSM
    scheduler.py     # Priority scheduler (HIGH/MEDIUM/LOW)
    engine.py        # Main runtime loop
    registry.py      # Pluggable model registry
  infrastructure/
    mqtt_adapter.py  # MQTT integration (twins/{id}/state|command|events)
    persistence.py   # SQLite persistence
    rule_engine.py   # Basic if/then rule engine
  models/
    mixing_unit.py   # Mandatory use case
    tank.py
    energy_node.py
    conveyor.py
  loader/
    plant_loader.py  # JSON plant parser and wiring
  api/
    app.py           # FastAPI bootstrap + background engine
    routes.py        # REST endpoints
    schemas.py       # API contracts
  examples/
    plant_mixing.json
```

## API

- `GET /twins`
- `GET /twins/{id}`
- `POST /twins/{id}/command`
- `GET /events`
- `GET /plants`
- Bonus: `POST /engine/speed`

## Run

From repo root:

```bash
PYTHONPATH=src uvicorn iot_middleware.dte.api.app:app --host 0.0.0.0 --port 8010
```

Optional environment variables:

- `DTE_MODE=SIMULATION|HYBRID|REAL`
- `DTE_TICK_RATE=2.0`
- `DTE_SQLITE_PATH=data/dte_engine.sqlite3`
- `DTE_PLANT_CONFIG=path/to/plant.json`
- `MQTT_HOST`, `MQTT_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`, `MQTT_QOS`

## Plant JSON contract

```json
{
  "plant_id": "plant_1",
  "units": [
    {
      "type": "mixing_unit",
      "id": "mix_1",
      "config": {"target_ratio": 0.6}
    }
  ],
  "connections": [
    {"from": "mix_1.mix", "to": "tank_1.inflow"}
  ]
}
```

## Persistence

SQLite tables:

- `event_logs`
- `state_history`
- `snapshots`

## Notes

- The engine is multi-plant and isolates twins by `plant_id`.
- Model schemas (`config_schema`/`io_schema`) are introspectable for future visual editors.
