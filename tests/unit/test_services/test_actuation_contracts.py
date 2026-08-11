from datetime import datetime, timezone

from parametric_control_engine.contracts.actuation_contracts import (
    ACTUATION_REQUEST_SCHEMA_VERSION,
    ActuationRequest,
    expires_at_from,
    stable_idempotency_key,
    stable_recommendation_id,
)


def test_recommendation_identity_is_stable_and_sensitive_to_policy_version():
    common = {
        "project_id": "00000000-0000-0000-0000-000000000001",
        "event_id": "evt-1",
        "variable_id": "tank_level",
        "policy_id": "policy-1",
        "source_asset_id": "00000000-0000-0000-0000-000000000011",
    }
    assert stable_recommendation_id(**common, policy_version=2) == stable_recommendation_id(**common, policy_version=2)
    assert stable_recommendation_id(**common, policy_version=2) != stable_recommendation_id(**common, policy_version=3)


def test_actuation_request_serializes_versioned_contract():
    request = ActuationRequest(
        schema_version=ACTUATION_REQUEST_SCHEMA_VERSION,
        command_id="00000000-0000-0000-0000-000000000021",
        recommendation_id="recommendation::one",
        correlation_id="corr-1",
        project_id="00000000-0000-0000-0000-000000000001",
        policy_id="policy-1",
        policy_version=1,
        source_asset_id=None,
        target_asset_id=None,
        target_kind="simulated",
        target_reference="simulated:pump",
        variable_id="tank_level",
        operation="increase",
        requested_value=3.0,
        created_at="2026-08-11T00:00:00+00:00",
        expires_at="2026-08-11T00:05:00+00:00",
        governance_mode="simulated",
        idempotency_key=stable_idempotency_key(
            project_id="00000000-0000-0000-0000-000000000001",
            recommendation_id="recommendation::one",
            target_kind="simulated",
            target_reference="simulated:pump",
            operation="increase",
            policy_version=1,
        ),
    )
    assert request.to_dict()["schema_version"] == "1.0"
    assert request.to_dict()["simulated"] is True
    assert expires_at_from(datetime(2026, 8, 11, tzinfo=timezone.utc), 60).endswith("+00:00")
