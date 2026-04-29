"""JSON-based plant loader for dynamic twin instantiation and wiring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from ..core.engine import Connection, DigitalTwinEngine
from ..core.registry import TwinModelRegistry


def _split_ref(ref: str) -> Tuple[str, str]:
    if "." not in ref:
        raise ValueError(f"Invalid connection ref '{ref}'. Expected format '<entity>.<port>'")
    entity_id, port = ref.split(".", 1)
    return entity_id, port


class PlantLoader:
    def __init__(self, registry: TwinModelRegistry) -> None:
        self.registry = registry

    def load_from_file(self, path: str | Path, engine: DigitalTwinEngine) -> dict[str, Any]:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return self.load_from_dict(payload, engine)

    def load_from_dict(self, payload: Dict[str, Any], engine: DigitalTwinEngine) -> dict[str, Any]:
        plant_id = payload.get("plant_id")
        if not plant_id:
            raise ValueError("Plant JSON must include 'plant_id'")

        plant = engine.add_plant(plant_id)
        created_entities: list[str] = []

        for unit in payload.get("units", []):
            model_type = unit.get("type")
            entity_id = unit.get("id")
            if not model_type or not entity_id:
                raise ValueError(f"Invalid unit definition: {unit}")
            entity = self.registry.create(
                model_type,
                entity_id=entity_id,
                plant_id=plant_id,
                config=unit.get("config", {}),
                state=unit.get("state", {}),
            )
            engine.add_entity(entity, plant_id=plant_id)
            created_entities.append(entity_id)

        for connection in payload.get("connections", []):
            from_ref = connection.get("from")
            to_ref = connection.get("to")
            if from_ref and to_ref:
                from_entity, from_output = _split_ref(from_ref)
                to_entity, to_input = _split_ref(to_ref)
            else:
                from_entity = connection["from_entity"]
                from_output = connection["from_output"]
                to_entity = connection["to_entity"]
                to_input = connection["to_input"]
            engine.add_connection(
                plant_id,
                Connection(
                    from_entity=from_entity,
                    from_output=from_output,
                    to_entity=to_entity,
                    to_input=to_input,
                ),
            )

        return {
            "plant_id": plant.plant_id,
            "entities_created": created_entities,
            "connections_created": len(plant.connections),
        }
