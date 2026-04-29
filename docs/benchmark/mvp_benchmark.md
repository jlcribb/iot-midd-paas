# MVP Benchmark Snapshot

## Executive Summary

Executive summary:
- Proportional achieved lower cumulative absolute error in 1 of 3 benchmark scenarios.
- Threshold achieved lower cumulative absolute error in 2 of 3 benchmark scenarios.
- Proportional delivered lower total applied effort in 3 of 3 scenarios.
- The benchmark shows a clear MVP tradeoff: threshold can reduce error faster in some scenarios, while proportional is generally smoother and more effort-efficient.

## Scorecard

### Large Initial Error

- Winner (absolute error): `proportional`
- Winner (squared error): `proportional`
- Winner (lower effort): `proportional`
- Threshold: abs error `82.361`, sq error `1459.783`, effort `64.0`, avg dist `8.236`
- Proportional: abs error `80.913`, sq error `1325.565`, effort `58.633`, avg dist `8.091`

### Sustained Disturbance

- Winner (absolute error): `threshold`
- Winner (squared error): `threshold`
- Winner (lower effort): `proportional`
- Threshold: abs error `28.362`, sq error `109.231`, effort `56.0`, avg dist `2.836`
- Proportional: abs error `45.497`, sq error `209.808`, effort `45.497`, avg dist `4.55`

### Near Setpoint Operation

- Winner (absolute error): `threshold`
- Winner (squared error): `threshold`
- Winner (lower effort): `proportional`
- Threshold: abs error `25.117`, sq error `83.417`, effort `40.0`, avg dist `2.512`
- Proportional: abs error `35.835`, sq error `135.948`, effort `34.835`, avg dist `3.583`

## Benchmark Table

| Scenario | Strategy | Abs Error | Sq Error | Effort | Avg Dist | Action Changes | Holds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Large Initial Error | threshold | 82.361 | 1459.783 | 64.0 | 8.236 | 4 | 2 |
| Large Initial Error | proportional | 80.913 | 1325.565 | 58.633 | 8.091 | 0 | 0 |
| Sustained Disturbance | threshold | 28.362 | 109.231 | 56.0 | 2.836 | 5 | 3 |
| Sustained Disturbance | proportional | 45.497 | 209.808 | 45.497 | 4.55 | 0 | 0 |
| Near Setpoint Operation | threshold | 25.117 | 83.417 | 40.0 | 2.512 | 8 | 5 |
| Near Setpoint Operation | proportional | 35.835 | 135.948 | 34.835 | 3.583 | 1 | 1 |

## Scenario Breakdown

### Large Initial Error

- Scenario ID: `large_initial_error`
- Description: Empieza muy por debajo del setpoint, sin perturbaciones.
- Setpoint: `55.0`
- Best absolute error: `proportional`
- Best squared error: `proportional`
- Lower effort: `proportional`

### Sustained Disturbance

- Scenario ID: `sustained_disturbance`
- Description: Opera cerca del objetivo pero recibe perturbaciones negativas sostenidas.
- Setpoint: `55.0`
- Best absolute error: `threshold`
- Best squared error: `threshold`
- Lower effort: `proportional`

### Near Setpoint Operation

- Scenario ID: `near_setpoint_operation`
- Description: Opera muy cerca del setpoint con perturbaciones pequeñas.
- Setpoint: `55.0`
- Best absolute error: `threshold`
- Best squared error: `threshold`
- Lower effort: `proportional`

## Regeneration

Regenerate these artifacts with:

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/python -m parametric_control_engine.examples.export_benchmark_artifacts
```

