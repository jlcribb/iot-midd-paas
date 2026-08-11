# Governed simulated actuation bindings

## Scope

This capability binds an existing policy source asset to one explicit target asset and one declared control point. It only governs the existing simulated actuation consumer. It does not publish MQTT commands, operate hardware, or add an outbox.

## Data model

`project_control_policies.bound_asset_id` remains the source asset used for policy selection. A policy can optionally have one active row in `project_control_policy_actuation_bindings` with source/target assets, a control point, operation, immutable binding identifier, and incrementing version.

The composite foreign keys enforce the project boundary in PostgreSQL. The service also checks scope before persisting. Existing rows are not inferred or migrated: policies without this row remain recommendation-only.

## Target eligibility and capabilities

Only `actuator`, `relay_module`, and `programmable_node` assets can be targets. Source equals target is allowed only for `programmable_node`.

The target must declare capabilities in `assets.metadata`:

```json
{
  "control_capabilities": [
    { "key": "relay_1", "operations": ["set", "toggle"] }
  ]
}
```

Allowed operations are `set`, `increase`, `decrease`, and `toggle`. The API and UI validate this declaration. The consumer rereads the active binding and capability before creating a delivery intent; a missing, stale, mismatched, or unsupported target is terminal and enters the existing simulated DLQ.

## Runtime behavior

When a selected policy has an active binding, the worker copies binding identity and version into the recommendation envelope and may publish it to the simulated queue. Delivery idempotency includes target asset, control point, and binding version. Audit records retain the same fields.

A valid recommendation without an active target binding is audited as `CONTROL_ACTUATION_RECOMMENDATION_ONLY`; it creates no delivery intent, is not dispatched, and does not enter the DLQ.

## Administration and RBAC

Policy create/update already requires `edit_policies` (operator or admin in the scoped project). The control-policy UI loads assets only for the selected project, offers eligible target types, and reads control points from metadata. Leaving the target empty removes the optional binding and returns the policy to recommendation-only behavior.
