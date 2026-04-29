# Operational Control Benchmark

## Objective

Benchmark operativo del `control_engine_worker` usando eventos compatibles con runtime, feature flag real, policies PostgreSQL y la planta first-order reproducible del parametric-control-engine.

## Executive Summary

Executive summary:
- Aggregate lowest mean absolute error was achieved by `policy_driven` with policy-driven=`5.469`, threshold=`5.805` and proportional=`6.061`.
- Aggregate lower effort was achieved by `proportional`.
- Aggregate fewer actions was achieved by `threshold, policy_driven`.
- Feature flag guard emitted `0` recommendations and recorded `3` skipped audits.

## Aggregate Scorecard

### threshold

- Mean absolute error: `5.805`
- Mean signed error: `5.805`
- Total applied effort: `90.0`
- Actions: `15`
- Recommendations emitted: `16`
- Skipped by feature flag: `0`
- Policies applied: `threshold x16`

### proportional

- Mean absolute error: `6.061`
- Mean signed error: `6.061`
- Total applied effort: `80.31`
- Actions: `16`
- Recommendations emitted: `16`
- Skipped by feature flag: `0`
- Policies applied: `proportional x16`

### policy_driven

- Mean absolute error: `5.469`
- Mean signed error: `5.469`
- Total applied effort: `91.015`
- Actions: `15`
- Recommendations emitted: `16`
- Skipped by feature flag: `0`
- Policies applied: `proportional x8, threshold x8`

## Scenario Comparison

| Scenario | Strategy | Mean Abs Error | Effort | Actions | Recommendations | Skipped | Policies |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Recovery Zone | threshold | 9.239 | 48.0 | 8 | 8 | 0 | threshold |
| Recovery Zone | proportional | 8.567 | 49.015 | 8 | 8 | 0 | proportional |
| Recovery Zone | policy_driven | 8.567 | 49.015 | 8 | 8 | 0 | proportional |
| Trim Zone | threshold | 2.372 | 42.0 | 7 | 8 | 0 | threshold |
| Trim Zone | proportional | 3.556 | 31.295 | 8 | 8 | 0 | proportional |
| Trim Zone | policy_driven | 2.372 | 42.0 | 7 | 8 | 0 | threshold |

## Scenario Assessment

### Recovery Zone

- Lowest mean absolute error: `proportional, policy_driven`
- Lowest effort: `threshold`
- Fewest actions: `threshold, proportional, policy_driven`

### Trim Zone

- Lowest mean absolute error: `threshold, policy_driven`
- Lowest effort: `proportional`
- Fewest actions: `threshold, policy_driven`

## Feature Flag Guard

- Recommendations emitted: `0`
- Skipped by feature flag: `3`
- Mean absolute error while disabled: `19.147`

## Interpretation

- recovery_zone favorece proportional para bajar error medio sin escalar el esfuerzo total.
- trim_zone favorece threshold cuando el objetivo es priorizar error medio mas bajo sobre suavidad.
- policy_driven combina un proportional por defecto con un threshold contextual y por eso captura lo mejor de cada zona sin cambiar el worker.
- feature flag disabled mantiene consumo y auditoria, pero no emite recommendations.

## Regeneration

Regenerate these artifacts with:

```bash
PYTHONPATH=src ./venv/bin/python scripts/export_operational_control_benchmark.py
```

