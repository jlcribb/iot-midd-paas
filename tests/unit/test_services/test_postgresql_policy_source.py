from parametric_control_engine.contracts.policy_contracts import PolicySelectionRequest
from parametric_control_engine.policies.static_selector import StaticPolicySelector
from parametric_control_engine.contracts.policy_source_contracts import PolicySourceRequest

from iot_middleware.services import postgresql_policy_source as source_module


PROJECT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_PROJECT_ID = "00000000-0000-0000-0000-000000000002"
ASSET_A_ID = "00000000-0000-0000-0000-000000000011"
ASSET_B_ID = "00000000-0000-0000-0000-000000000012"


def build_policy_row(
    *,
    policy_id: str,
    project_id: str = PROJECT_ID,
    variable: str = "tank_level",
    context_selector=None,
    policy_type: str = "proportional",
    params=None,
    priority: int = 0,
    enabled: bool = True,
    version: int = 1,
):
    return {
        "id": policy_id,
        "project_id": project_id,
        "variable": variable,
        "context_selector": context_selector or {},
        "policy_type": policy_type,
        "params": params
        or {
            "variable_name": "Tank Level",
            "variable_unit": "units",
            "actuator_name": "pump",
            "setpoint_value": 70.0,
            "gain": 1.0,
            "deadband": 0.0,
            "min_action": 0.0,
        },
        "priority": priority,
        "enabled": enabled,
        "version": version,
        "created_at": "2026-04-28T00:00:00+00:00",
        "updated_at": "2026-04-28T00:00:00+00:00",
    }


def build_source():
    return source_module.PostgreSQLPolicySource(
        recommendation_channel="control.recommendations",
        defaults={"variable_unit": "units"},
    )


def test_policy_source_loads_matching_policy(monkeypatch):
    monkeypatch.setattr(
        source_module,
        "list_project_control_policies",
        lambda project_id, variable_id, asset_id=None: [
            build_policy_row(
                policy_id="policy-1",
                context_selector={"sector": "tank_A"},
            )
        ],
    )

    source = build_source()
    result = source.load_policies(
        PolicySourceRequest(
            variable_id="tank_level",
            context={"project_id": PROJECT_ID, "sector": "tank_A"},
            event_id="evt-1",
        )
    )

    assert len(result.policies) == 1
    policy = result.policies[0]
    assert policy.policy_id == "policy-1"
    assert policy.required_context == {"sector": "tank_A"}
    assert policy.binding.setpoint.value == 70.0
    assert policy.binding.variable.actuator_name == "pump"


def test_policy_source_skips_disabled_policies(monkeypatch):
    monkeypatch.setattr(
        source_module,
        "list_project_control_policies",
        lambda project_id, variable_id, asset_id=None: [],
    )

    source = build_source()
    result = source.load_policies(
        PolicySourceRequest(
            variable_id="tank_level",
            context={"project_id": PROJECT_ID},
            event_id="evt-2",
        )
    )

    assert result.policies == []


def test_policy_source_isolates_projects(monkeypatch):
    monkeypatch.setattr(
        source_module,
        "list_project_control_policies",
        lambda project_id, variable_id, asset_id=None: [
            build_policy_row(policy_id="policy-main", project_id=project_id),
        ]
        if project_id == PROJECT_ID
        else [
            build_policy_row(policy_id="policy-other", project_id=OTHER_PROJECT_ID),
        ],
    )

    source = build_source()
    result = source.load_policies(
        PolicySourceRequest(
            variable_id="tank_level",
            context={"project_id": PROJECT_ID},
        )
    )

    assert [policy.policy_id for policy in result.policies] == ["policy-main"]


def test_policy_selector_prefers_highest_priority(monkeypatch):
    monkeypatch.setattr(
        source_module,
        "list_project_control_policies",
        lambda project_id, variable_id, asset_id=None: [
            build_policy_row(policy_id="policy-low", priority=5, context_selector={"sector": "tank_A"}),
            build_policy_row(policy_id="policy-high", priority=10, context_selector={"sector": "tank_A"}),
        ],
    )

    source = build_source()
    selection = StaticPolicySelector(source).resolve(
        PolicySelectionRequest(
            variable_id="tank_level",
            context={"project_id": PROJECT_ID, "sector": "tank_A"},
            event_id="evt-3",
        )
    )

    assert selection.policy_id == "policy-high"
    assert selection.priority == 10


def test_policy_source_keeps_latest_version_per_signature(monkeypatch):
    monkeypatch.setattr(
        source_module,
        "list_project_control_policies",
        lambda project_id, variable_id, asset_id=None: [
            build_policy_row(policy_id="policy-v2", version=2, priority=10, context_selector={"sector": "tank_A"}),
            build_policy_row(policy_id="policy-v1", version=1, priority=10, context_selector={"sector": "tank_A"}),
        ],
    )

    source = build_source()
    result = source.load_policies(
        PolicySourceRequest(
            variable_id="tank_level",
            context={"project_id": PROJECT_ID, "sector": "tank_A"},
            event_id="evt-4",
        )
    )

    assert [policy.policy_id for policy in result.policies] == ["policy-v2"]


def test_policy_source_supports_threshold_policy(monkeypatch):
    monkeypatch.setattr(
        source_module,
        "list_project_control_policies",
        lambda project_id, variable_id, asset_id=None: [
            build_policy_row(
                policy_id="policy-threshold",
                policy_type="threshold",
                params={
                    "variable_name": "Tank Level",
                    "variable_unit": "units",
                    "actuator_name": "pump",
                    "setpoint_value": 70.0,
                    "tolerance": 2.0,
                    "increase_step": 1.5,
                    "decrease_step": 2.0,
                },
            )
        ],
    )

    source = build_source()
    result = source.load_policies(
        PolicySourceRequest(
            variable_id="tank_level",
            context={"project_id": PROJECT_ID},
            event_id="evt-5",
        )
    )

    assert len(result.policies) == 1
    assert result.policies[0].policy_type == "threshold"
    assert result.policies[0].binding.parameters.tolerance == 2.0


def test_policy_source_prefers_matching_bound_policy_over_legacy(monkeypatch):
    monkeypatch.setattr(
        source_module,
        "list_project_control_policies",
        lambda project_id, variable_id, asset_id=None: [
            {
                **build_policy_row(policy_id="legacy-policy", priority=99),
                "bound_asset_id": None,
            },
            {
                **build_policy_row(policy_id="asset-a-policy", priority=1),
                "bound_asset_id": ASSET_A_ID,
            },
            {
                **build_policy_row(policy_id="asset-b-policy", priority=50),
                "bound_asset_id": ASSET_B_ID,
            },
        ],
    )

    result = build_source().load_policies(
        PolicySourceRequest(
            variable_id="tank_level",
            context={"project_id": PROJECT_ID, "asset_id": ASSET_A_ID},
        )
    )

    assert [policy.policy_id for policy in result.policies] == ["asset-a-policy"]
    assert result.policies[0].binding.context["bound_asset_id"] == ASSET_A_ID


def test_policy_source_uses_legacy_policy_when_no_bound_asset_matches(monkeypatch):
    monkeypatch.setattr(
        source_module,
        "list_project_control_policies",
        lambda project_id, variable_id, asset_id=None: [
            {
                **build_policy_row(policy_id="legacy-policy"),
                "bound_asset_id": None,
            },
            {
                **build_policy_row(policy_id="asset-a-policy"),
                "bound_asset_id": ASSET_A_ID,
            },
        ],
    )

    result = build_source().load_policies(
        PolicySourceRequest(
            variable_id="tank_level",
            context={"project_id": PROJECT_ID, "asset_id": ASSET_B_ID},
        )
    )

    assert [policy.policy_id for policy in result.policies] == ["legacy-policy"]
