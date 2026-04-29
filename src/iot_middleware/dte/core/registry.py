"""Registry for pluggable twin model classes."""

from __future__ import annotations

from typing import Any, Dict, Type

from .entity import DigitalTwinEntity


class TwinModelRegistry:
    def __init__(self) -> None:
        self._models: Dict[str, Type[DigitalTwinEntity]] = {}

    def register(self, model_type: str, model_cls: Type[DigitalTwinEntity]) -> None:
        self._models[model_type] = model_cls

    def get_model(self, model_type: str) -> Type[DigitalTwinEntity]:
        if model_type not in self._models:
            available = ", ".join(sorted(self._models.keys()))
            raise KeyError(f"Unknown twin model '{model_type}'. Available: {available}")
        return self._models[model_type]

    def create(
        self,
        model_type: str,
        *,
        entity_id: str,
        plant_id: str,
        config: Dict[str, Any] | None = None,
        state: Dict[str, Any] | None = None,
    ) -> DigitalTwinEntity:
        model_cls = self.get_model(model_type)
        return model_cls(entity_id=entity_id, plant_id=plant_id, config=config, state=state)

    def list_models(self) -> Dict[str, Dict[str, Any]]:
        return {
            key: {
                "model_type": value.model_type,
                "config_schema": value.config_schema(),
                "io_schema": value.io_schema(),
            }
            for key, value in self._models.items()
        }
