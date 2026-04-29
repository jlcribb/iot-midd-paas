import pytest

from parametric_control_engine.contracts.event_adapter_contracts import MonovariableControlBinding
from parametric_control_engine.contracts.policy_contracts import (
    PolicySelectionRequest,
    StaticPolicyDefinition,
)
from parametric_control_engine.examples.event_driven_demo import build_demo_binding
from parametric_control_engine.models.control_models import ControlParameters, SetpointReference
from parametric_control_engine.policies.static_selector import StaticPolicySelector
from parametric_control_engine.sources.in_memory_policy_source import InMemoryPolicySource


def build_selector() -> StaticPolicySelector:
    base_binding = build_demo_binding()
    startup_binding = MonovariableControlBinding(
        variable=base_binding.variable,
        setpoint=SetpointReference(value=58.0),
        parameters=ControlParameters(gain=1.4, deadband=0.5, min_action=2.0, max_action=12.0),
        recommendation_channel=base_binding.recommendation_channel,
        context=base_binding.context,
    )
    default_binding = MonovariableControlBinding(
        variable=base_binding.variable,
        setpoint=SetpointReference(value=52.0),
        parameters=ControlParameters(gain=0.9, deadband=0.5, min_action=1.5, max_action=8.0),
        recommendation_channel=base_binding.recommendation_channel,
        context=base_binding.context,
    )
    source = InMemoryPolicySource(
        [
            StaticPolicyDefinition(
                policy_id="startup-policy",
                binding=startup_binding,
                required_context={"operation_mode": "startup"},
            ),
            StaticPolicyDefinition(
                policy_id="default-policy",
                binding=default_binding,
            ),
        ]
    )
    return StaticPolicySelector(source)


def test_static_policy_selector_prefers_more_specific_context_match():
    selector = build_selector()

    result = selector.resolve(
        PolicySelectionRequest(
            variable_id="tank-level-01",
            context={"operation_mode": "startup", "project_id": "demo-project"},
            event_id="evt-2001",
        )
    )

    assert result.policy_id == "startup-policy"
    assert result.binding.setpoint.value == pytest.approx(58.0)
    assert result.selection_trace[-1].step == "policy_selected"
    assert result.selection_trace[1].data["policy_source_name"] == "in-memory-policy-source"


def test_static_policy_selector_falls_back_to_default_policy():
    selector = build_selector()

    result = selector.resolve(
        PolicySelectionRequest(
            variable_id="tank-level-01",
            context={"operation_mode": "steady"},
            event_id="evt-2002",
        )
    )

    assert result.policy_id == "default-policy"
    assert result.binding.setpoint.value == pytest.approx(52.0)
    assert result.selector_name == "static-policy-selector"


def test_static_policy_selector_raises_when_no_policy_matches():
    selector = build_selector()

    with pytest.raises(ValueError, match="No static policy found"):
        selector.resolve(
            PolicySelectionRequest(
                variable_id="unknown-variable",
                context={},
                event_id="evt-2003",
            )
        )
