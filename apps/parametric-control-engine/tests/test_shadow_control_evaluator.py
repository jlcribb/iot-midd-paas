import pytest

from parametric_control_engine.evaluators.shadow_control import ShadowControlEvaluationError, evaluate_shadow_control


def test_shadow_evaluation_uses_canonical_evaluator_and_bounds_without_actuation():
    result = evaluate_shadow_control(strategy_type="proportional", configuration={"parameters": {"gain": 2, "setpoint_value": 50, "deadband": 0, "min_action": 0, "max_action": 20}}, input_snapshot={"level": 40}, required_inputs=["level"], limits={"min_output": -5, "max_output": 5})
    assert result["raw_output"] == {"value": 20}
    assert result["bounded_output"] == {"value": 5}
    assert result["constraint_results"]["physical_effects"] is False
    assert result["evaluator"]["name"] == "proportional"


def test_shadow_evaluation_fails_closed_when_required_input_is_missing():
    with pytest.raises(ShadowControlEvaluationError, match="INPUT_UNAVAILABLE"):
        evaluate_shadow_control(strategy_type="proportional", configuration={"parameters": {}}, input_snapshot={}, required_inputs=["level"], limits={"min_output": -1, "max_output": 1})
