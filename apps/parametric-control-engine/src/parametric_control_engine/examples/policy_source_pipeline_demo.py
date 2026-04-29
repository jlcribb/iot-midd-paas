"""Pipeline demo showing policy source -> selector -> evaluator -> sink."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

from ..adapters.event_adapter import EventDrivenRecommendationAdapter
from ..adapters.recommendation_sink_adapter import RecommendationSinkAdapter
from ..contracts.event_adapter_contracts import MonovariableControlBinding, TelemetryStateEvent
from ..contracts.policy_contracts import StaticPolicyDefinition
from ..contracts.policy_source_contracts import PolicySourceRequest
from ..examples.event_driven_demo import build_demo_binding
from ..models.control_models import ControlParameters, SetpointReference
from ..policies.static_selector import StaticPolicySelector
from ..sources.in_memory_policy_source import InMemoryPolicySource


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported value for JSON serialization: {type(value)!r}")


def build_policy_source() -> InMemoryPolicySource:
    base_binding = build_demo_binding()
    startup_binding = MonovariableControlBinding(
        variable=base_binding.variable,
        setpoint=SetpointReference(value=58.0, metadata={"recipe": "batch-startup"}),
        parameters=ControlParameters(gain=1.4, deadband=0.5, min_action=2.0, max_action=12.0),
        recommendation_channel=base_binding.recommendation_channel,
        context=base_binding.context,
    )
    steady_binding = MonovariableControlBinding(
        variable=base_binding.variable,
        setpoint=SetpointReference(value=52.0, metadata={"recipe": "steady-state"}),
        parameters=ControlParameters(gain=0.9, deadband=0.5, min_action=1.5, max_action=8.0),
        recommendation_channel=base_binding.recommendation_channel,
        context=base_binding.context,
    )
    return InMemoryPolicySource(
        [
            StaticPolicyDefinition(
                policy_id="tank-level-startup",
                binding=startup_binding,
                required_context={"operation_mode": "startup"},
                description="Politica para carga inicial del tanque",
            ),
            StaticPolicyDefinition(
                policy_id="tank-level-default",
                binding=steady_binding,
                description="Politica estatica por defecto",
            ),
        ]
    )


def build_demo_event() -> TelemetryStateEvent:
    return TelemetryStateEvent(
        event_id="evt-3001",
        variable_id="tank-level-01",
        value=44.5,
        source="mqtt://plant/tank-A/level",
        quality="validated",
        metadata={"asset_id": "tank-A", "topic": "plant/tank-A/level"},
        context={
            "operation_mode": "startup",
            "ingestion_path": "mqtt",
            "correlation_id": "corr-128",
        },
    )


def main() -> None:
    event = build_demo_event()
    policy_source = build_policy_source()
    source_result = policy_source.load_policies(
        PolicySourceRequest(
            variable_id=event.variable_id,
            context=event.context,
            event_id=event.event_id,
        )
    )
    selector = StaticPolicySelector(policy_source)
    selection = selector.resolve_event(event)
    event_adapter = EventDrivenRecommendationAdapter(selection.binding)
    sink_adapter = RecommendationSinkAdapter()
    recommendation = event_adapter.evaluate_event(event)
    sink_output = sink_adapter.build_sink_output(recommendation)
    payload = {
        "event": asdict(event),
        "policy_source": {
            "source_name": source_result.source_name,
            "candidate_policy_ids": [policy.policy_id for policy in source_result.policies],
            "source_trace": [asdict(entry) for entry in source_result.source_trace],
        },
        "policy_selection": {
            "policy_id": selection.policy_id,
            "selector_name": selection.selector_name,
            "selection_trace": [asdict(entry) for entry in selection.selection_trace],
        },
        "sink_output": asdict(sink_output),
    }
    print(json.dumps(payload, indent=2, default=_json_default))


if __name__ == "__main__":
    main()
