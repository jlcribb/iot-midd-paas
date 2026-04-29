import pytest

from parametric_control_engine.contracts.event_adapter_contracts import MonovariableControlBinding
from parametric_control_engine.contracts.policy_contracts import StaticPolicyDefinition
from parametric_control_engine.contracts.policy_source_contracts import PolicySourceRequest
from parametric_control_engine.examples.event_driven_demo import build_demo_binding
from parametric_control_engine.models.control_models import ControlParameters, SetpointReference
from parametric_control_engine.sources.in_memory_policy_source import InMemoryPolicySource


def build_source() -> InMemoryPolicySource:
    base_binding = build_demo_binding()
    startup_binding = MonovariableControlBinding(
        variable=base_binding.variable,
        setpoint=SetpointReference(value=58.0),
        parameters=ControlParameters(gain=1.4, deadband=0.5, min_action=2.0, max_action=12.0),
        recommendation_channel=base_binding.recommendation_channel,
        context=base_binding.context,
    )
    pressure_binding = MonovariableControlBinding(
        variable=base_binding.variable.__class__(
            variable_id="pressure-01",
            name="line_pressure",
            unit="bar",
            actuator_name="relief_valve",
            increase_action_label="open_more",
            decrease_action_label="close_some",
            hold_action_label="hold_position",
        ),
        setpoint=SetpointReference(value=5.0),
        parameters=ControlParameters(gain=0.8, deadband=0.1, min_action=0.5, max_action=3.0),
        recommendation_channel="runtime.control.recommendations",
        context={},
    )
    return InMemoryPolicySource(
        [
            StaticPolicyDefinition(policy_id="tank-startup", binding=startup_binding),
            StaticPolicyDefinition(policy_id="pressure-default", binding=pressure_binding),
        ]
    )


def test_in_memory_policy_source_returns_candidates_for_variable():
    source = build_source()

    result = source.load_policies(
        PolicySourceRequest(
            variable_id="tank-level-01",
            context={"operation_mode": "startup"},
            event_id="evt-3001",
        )
    )

    assert result.source_name == "in-memory-policy-source"
    assert [policy.policy_id for policy in result.policies] == ["tank-startup"]
    assert result.source_trace[-1].step == "policy_candidates_loaded"


def test_in_memory_policy_source_returns_empty_list_when_unknown_variable():
    source = build_source()

    result = source.load_policies(
        PolicySourceRequest(
            variable_id="unknown-variable",
            context={},
            event_id="evt-3002",
        )
    )

    assert result.policies == []
    assert result.source_trace[-1].data["candidate_policy_ids"] == []
