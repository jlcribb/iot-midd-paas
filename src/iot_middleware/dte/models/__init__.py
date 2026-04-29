"""Twin model package and registry bootstrap helpers."""

from __future__ import annotations

from ..core.registry import TwinModelRegistry
from .conveyor import ConveyorTwin
from .energy_node import EnergyNodeTwin
from .mixing_unit import MixingUnitTwin
from .tank import TankTwin


def build_default_registry() -> TwinModelRegistry:
    registry = TwinModelRegistry()
    registry.register(MixingUnitTwin.model_type, MixingUnitTwin)
    registry.register(TankTwin.model_type, TankTwin)
    registry.register(EnergyNodeTwin.model_type, EnergyNodeTwin)
    registry.register(ConveyorTwin.model_type, ConveyorTwin)
    return registry


__all__ = [
    "MixingUnitTwin",
    "TankTwin",
    "EnergyNodeTwin",
    "ConveyorTwin",
    "build_default_registry",
]
