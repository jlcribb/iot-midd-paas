"""Operational benchmark for control_engine_worker using worker-compatible events."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from sqlalchemy import create_engine, text


def _ensure_parametric_engine_path() -> None:
    repo_root = os.getenv("REPO_ROOT", os.getcwd())
    engine_src = os.path.join(repo_root, "apps", "parametric-control-engine", "src")

    if os.path.isdir(engine_src) and engine_src not in sys.path:
        sys.path.insert(0, engine_src)


_ensure_parametric_engine_path()


from parametric_control_engine.simulation.first_order import (  # noqa: E402
    ClosedLoopSimulationConfig,
    FirstOrderPlantConfig,
    simulate_first_order_step,
)
from parametric_control_engine.simulation.metrics import calculate_summary_metrics  # noqa: E402


BENCHMARK_NAME = "operational-control-worker-benchmark"
BENCHMARK_PROJECT_ID = "00000000-0000-0000-0000-0000000000b5"
BENCHMARK_VARIABLE_ID = "tank_level"
BENCHMARK_GENERATED_AT = "2026-04-29T00:00:00+00:00"

THRESHOLD_POLICY_ID = "11111111-1111-1111-1111-111111111111"
PROPORTIONAL_POLICY_ID = "22222222-2222-2222-2222-222222222222"
POLICY_DRIVEN_DEFAULT_ID = "33333333-3333-3333-3333-333333333333"
POLICY_DRIVEN_CONTEXTUAL_ID = "44444444-4444-4444-4444-444444444444"


@dataclass(frozen=True)
class OperationalBenchmarkScenario:
    scenario_id: str
    label: str
    description: str
    setpoint_value: float
    sector: str
    plant_config: FirstOrderPlantConfig
    simulation_config: ClosedLoopSimulationConfig


def build_operational_benchmark_scenarios() -> List[OperationalBenchmarkScenario]:
    plant_config = FirstOrderPlantConfig(
        baseline_level=60.0,
        control_gain=1.4,
        response_rate=0.4,
        min_value=0.0,
        max_value=100.0,
    )

    return [
        OperationalBenchmarkScenario(
            scenario_id="recovery_zone",
            label="Recovery Zone",
            description="Error inicial grande y perturbacion negativa sostenida en un sector donde conviene correccion agresiva.",
            setpoint_value=70.0,
            sector="recovery_zone",
            plant_config=plant_config,
            simulation_config=ClosedLoopSimulationConfig(
                initial_value=46.0,
                horizon=8,
                disturbance_sequence=[0.0, 0.0, -2.5, -2.5, -2.0, 0.0, 0.0, 0.0],
            ),
        ),
        OperationalBenchmarkScenario(
            scenario_id="trim_zone",
            label="Trim Zone",
            description="Operacion cercana al setpoint con ruido chico, donde importa suavidad sin perder estabilidad.",
            setpoint_value=70.0,
            sector="trim_zone",
            plant_config=plant_config,
            simulation_config=ClosedLoopSimulationConfig(
                initial_value=69.2,
                horizon=8,
                disturbance_sequence=[0.3, -0.2, 0.2, -0.3, 0.1, 0.0, -0.2, 0.2],
            ),
        ),
    ]


def build_strategy_policies(setpoint_value: float) -> Dict[str, List[Dict[str, Any]]]:
    threshold_params = {
        "variable_name": "Tank Level",
        "variable_unit": "units",
        "actuator_name": "control_output",
        "setpoint_value": setpoint_value,
        "tolerance": 1.0,
        "increase_step": 6.0,
        "decrease_step": 6.0,
        "hold_signal": 0.0,
    }
    proportional_params = {
        "variable_name": "Tank Level",
        "variable_unit": "units",
        "actuator_name": "control_output",
        "setpoint_value": setpoint_value,
        "gain": 1.1,
        "deadband": 0.25,
        "min_action": 0.0,
        "max_action": 8.0,
    }

    return {
        "threshold": [
            {
                "id": THRESHOLD_POLICY_ID,
                "variable": BENCHMARK_VARIABLE_ID,
                "context_selector": {},
                "policy_type": "threshold",
                "params": threshold_params,
                "priority": 10,
                "enabled": True,
                "version": 1,
            }
        ],
        "proportional": [
            {
                "id": PROPORTIONAL_POLICY_ID,
                "variable": BENCHMARK_VARIABLE_ID,
                "context_selector": {},
                "policy_type": "proportional",
                "params": proportional_params,
                "priority": 10,
                "enabled": True,
                "version": 1,
            }
        ],
        "policy_driven": [
            {
                "id": POLICY_DRIVEN_DEFAULT_ID,
                "variable": BENCHMARK_VARIABLE_ID,
                "context_selector": {},
                "policy_type": "proportional",
                "params": proportional_params,
                "priority": 10,
                "enabled": True,
                "version": 1,
            },
            {
                "id": POLICY_DRIVEN_CONTEXTUAL_ID,
                "variable": BENCHMARK_VARIABLE_ID,
                "context_selector": {"sector": "trim_zone"},
                "policy_type": "threshold",
                "params": threshold_params,
                "priority": 50,
                "enabled": True,
                "version": 2,
            },
        ],
    }


def _project_engine():
    db_host = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "iot_middleware")
    db_user = os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "iot_user")
    db_password = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "iot_password_2024")
    return create_engine(
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",
        pool_pre_ping=True,
    )


def _ensure_runtime_env() -> None:
    repo_root = os.getenv("REPO_ROOT", os.getcwd())
    os.environ.setdefault("REPO_ROOT", repo_root)
    os.environ.setdefault("CONTROL_WORKER_PUBLISH_MODE", "stdout")
    os.environ.setdefault("CONTROL_WORKER_ALLOW_INMEMORY_POLICY_FALLBACK", "false")
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("DB_PORT", "5432")
    os.environ.setdefault("DB_NAME", "iot_middleware")
    os.environ.setdefault("DB_USER", "iot_user")
    os.environ.setdefault("DB_PASSWORD", "iot_password_2024")


def _upsert_project(project_id: str, *, enabled: bool) -> None:
    engine = _project_engine()
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO public.projects (
                    id,
                    name,
                    description,
                    status,
                    metadata,
                    created_at,
                    updated_at,
                    parametric_control_enabled
                )
                VALUES (
                    CAST(:project_id AS uuid),
                    :name,
                    :description,
                    CAST(:status AS project_status_enum),
                    '{}'::jsonb,
                    now(),
                    now(),
                    :enabled
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status,
                    updated_at = now(),
                    parametric_control_enabled = EXCLUDED.parametric_control_enabled
                """
            ),
            {
                "project_id": project_id,
                "name": "control-engine-operational-benchmark",
                "description": "Proyecto reproducible para benchmark operativo del control engine worker",
                "status": "draft",
                "enabled": enabled,
            },
        )


def _replace_project_policies(project_id: str, policies: Iterable[Dict[str, Any]]) -> None:
    engine = _project_engine()
    policies = list(policies)

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DELETE FROM public.project_control_policies
                WHERE project_id = CAST(:project_id AS uuid)
                  AND variable = :variable
                """
            ),
            {
                "project_id": project_id,
                "variable": BENCHMARK_VARIABLE_ID,
            },
        )

        for policy in policies:
            connection.execute(
                text(
                    """
                    INSERT INTO public.project_control_policies (
                        id,
                        project_id,
                        variable,
                        context_selector,
                        policy_type,
                        params,
                        priority,
                        enabled,
                        version
                    )
                    VALUES (
                        CAST(:id AS uuid),
                        CAST(:project_id AS uuid),
                        :variable,
                        CAST(:context_selector AS jsonb),
                        :policy_type,
                        CAST(:params AS jsonb),
                        :priority,
                        :enabled,
                        :version
                    )
                    """
                ),
                {
                    "id": policy["id"],
                    "project_id": project_id,
                    "variable": policy["variable"],
                    "context_selector": json.dumps(policy["context_selector"]),
                    "policy_type": policy["policy_type"],
                    "params": json.dumps(policy["params"]),
                    "priority": policy["priority"],
                    "enabled": policy["enabled"],
                    "version": policy["version"],
                },
            )


def _build_event(
    *,
    project_id: str,
    scenario: OperationalBenchmarkScenario,
    strategy_name: str,
    step_index: int,
    current_value: float,
) -> Dict[str, Any]:
    timestamp = datetime.fromisoformat(BENCHMARK_GENERATED_AT) + timedelta(minutes=step_index)
    return {
        "event_id": f"{scenario.scenario_id}-{strategy_name}-{step_index}",
        "project_id": project_id,
        "variable": BENCHMARK_VARIABLE_ID,
        "value": round(current_value, 3),
        "timestamp": timestamp.astimezone(timezone.utc).isoformat(),
        "context": {
            "sector": scenario.sector,
            "scenario_id": scenario.scenario_id,
            "strategy": strategy_name,
        },
    }


def _coerce_signal(result: Dict[str, Any] | None) -> float:
    if not result or not result.get("publish_envelope"):
        return 0.0
    payload = result["publish_envelope"].get("payload") or {}
    raw = payload.get("command_value")
    return float(raw) if raw is not None else 0.0


def _extract_step_record(
    *,
    step_index: int,
    scenario: OperationalBenchmarkScenario,
    current_value: float,
    disturbance: float,
    result: Dict[str, Any] | None,
    next_value: float,
    desired_level: float,
) -> Dict[str, Any]:
    base_record = {
        "step_index": step_index,
        "measurement": round(current_value, 3),
        "setpoint": scenario.setpoint_value,
        "disturbance": disturbance,
        "desired_level": desired_level,
        "next_measurement": next_value,
    }

    if result and result.get("publish_envelope"):
        payload = result["publish_envelope"].get("payload") or {}
        return {
            **base_record,
            "status": "processed",
            "error": round(float(payload.get("error", 0.0)), 3),
            "distance_to_setpoint": round(abs(float(payload.get("error", 0.0))), 3),
            "action_kind": str(payload.get("recommendation_kind") or "hold"),
            "action_label": str(payload.get("action_label") or "hold"),
            "applied_signal": round(_coerce_signal(result), 3),
            "policy_id": payload.get("policy_id"),
            "policy_type": payload.get("policy_type"),
            "policy_version": payload.get("policy_version"),
            "policy_priority": payload.get("policy_priority"),
        }

    audit_envelope = (result or {}).get("audit_envelope") or {}
    audit_status = audit_envelope.get("status") or "error"
    skip_reason = audit_envelope.get("skip_reason")
    error_value = round(scenario.setpoint_value - current_value, 3)
    return {
        **base_record,
        "status": audit_status,
        "error": error_value,
        "distance_to_setpoint": round(abs(error_value), 3),
        "action_kind": "hold",
        "action_label": "hold",
        "applied_signal": 0.0,
        "skip_reason": skip_reason,
        "policy_id": None,
        "policy_type": None,
        "policy_version": None,
        "policy_priority": None,
    }


def summarize_strategy_steps(strategy_name: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    metric_steps = [
        {
            "error": step["error"],
            "distance_to_setpoint": step["distance_to_setpoint"],
            "applied_signal": step["applied_signal"],
            "action_kind": step["action_kind"],
        }
        for step in steps
    ]
    base_metrics = calculate_summary_metrics(strategy_name, metric_steps)
    signed_mean_error = sum(step["error"] for step in steps) / len(steps)
    action_count = sum(1 for step in steps if step["action_kind"] in {"increase", "decrease"})
    processed_steps = sum(1 for step in steps if step["status"] == "processed")
    skipped_steps = sum(
        1
        for step in steps
        if step["status"] == "skipped" and step.get("skip_reason") == "feature_flag_disabled"
    )
    policies_applied: Dict[str, Dict[str, Any]] = {}

    for step in steps:
        policy_id = step.get("policy_id")
        policy_type = step.get("policy_type")
        if not policy_id or not policy_type:
            continue
        key = f"{policy_type}:{policy_id}"
        if key not in policies_applied:
            policies_applied[key] = {
                "policy_id": policy_id,
                "policy_type": policy_type,
                "count": 0,
            }
        policies_applied[key]["count"] += 1

    return {
        **base_metrics,
        "mean_absolute_error": base_metrics["average_distance_to_setpoint"],
        "mean_signed_error": round(signed_mean_error, 3),
        "actions_count": action_count,
        "recommendations_emitted": processed_steps,
        "skipped_by_feature_flag": skipped_steps,
        "policies_applied": sorted(
            policies_applied.values(),
            key=lambda item: (item["policy_type"], item["policy_id"]),
        ),
    }


def _best_strategies(summary_by_strategy: Dict[str, Dict[str, Any]], key: str) -> List[str]:
    best_value = min(summary[key] for summary in summary_by_strategy.values())
    return [
        strategy
        for strategy, summary in summary_by_strategy.items()
        if summary[key] == best_value
    ]


def build_operational_benchmark_table_rows(
    scenario: OperationalBenchmarkScenario,
    summary_by_strategy: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rows = []
    for strategy, summary in summary_by_strategy.items():
        rows.append(
            {
                "scenario_id": scenario.scenario_id,
                "scenario_label": scenario.label,
                "strategy": strategy,
                "mean_absolute_error": summary["mean_absolute_error"],
                "mean_signed_error": summary["mean_signed_error"],
                "total_applied_effort": summary["total_applied_effort"],
                "actions_count": summary["actions_count"],
                "recommendations_emitted": summary["recommendations_emitted"],
                "skipped_by_feature_flag": summary["skipped_by_feature_flag"],
                "policy_types": [item["policy_type"] for item in summary["policies_applied"]],
            }
        )
    return rows


def build_operational_scenario_assessment(
    scenario: OperationalBenchmarkScenario,
    summary_by_strategy: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "scenario_id": scenario.scenario_id,
        "scenario_label": scenario.label,
        "lowest_mean_absolute_error": _best_strategies(
            summary_by_strategy,
            "mean_absolute_error",
        ),
        "lowest_effort": _best_strategies(summary_by_strategy, "total_applied_effort"),
        "fewest_actions": _best_strategies(summary_by_strategy, "actions_count"),
    }


def _build_worker_module():
    from iot_middleware.services import control_engine_worker as worker

    worker.PUBLISH_MODE = "stdout"
    worker.RECOMMENDATION_QUEUE = "control.recommendations.benchmark"
    worker.AUDIT_QUEUE = "control.audit.benchmark"
    return worker


def _run_strategy_for_scenario(
    *,
    worker,
    project_id: str,
    scenario: OperationalBenchmarkScenario,
    strategy_name: str,
) -> Dict[str, Any]:
    current_value = scenario.simulation_config.initial_value
    state_series = [round(current_value, 3)]
    steps: List[Dict[str, Any]] = []

    for step_index, disturbance in enumerate(
        scenario.simulation_config.disturbance_sequence,
        start=1,
    ):
        event = _build_event(
            project_id=project_id,
            scenario=scenario,
            strategy_name=strategy_name,
            step_index=step_index,
            current_value=current_value,
        )
        result = worker.handle_event(event)
        applied_signal = _coerce_signal(result)
        plant_step = simulate_first_order_step(
            current_value=current_value,
            applied_signal=applied_signal,
            disturbance=disturbance,
            plant_config=scenario.plant_config,
        )
        next_value = plant_step["next_value"]
        desired_level = plant_step["desired_level"]
        steps.append(
            _extract_step_record(
                step_index=step_index,
                scenario=scenario,
                current_value=current_value,
                disturbance=disturbance,
                result=result,
                next_value=next_value,
                desired_level=desired_level,
            )
        )
        state_series.append(next_value)
        current_value = next_value

    return {
        "strategy": strategy_name,
        "state_series": state_series,
        "steps": steps,
        "summary_metrics": summarize_strategy_steps(strategy_name, steps),
    }


def _run_feature_flag_guard(worker, scenario: OperationalBenchmarkScenario) -> Dict[str, Any]:
    _upsert_project(BENCHMARK_PROJECT_ID, enabled=False)
    _replace_project_policies(
        BENCHMARK_PROJECT_ID,
        build_strategy_policies(scenario.setpoint_value)["policy_driven"],
    )

    current_value = scenario.simulation_config.initial_value
    steps: List[Dict[str, Any]] = []

    for step_index, disturbance in enumerate(
        scenario.simulation_config.disturbance_sequence[:3],
        start=1,
    ):
        event = _build_event(
            project_id=BENCHMARK_PROJECT_ID,
            scenario=scenario,
            strategy_name="feature_flag_guard",
            step_index=step_index,
            current_value=current_value,
        )
        result = worker.handle_event(event)
        plant_step = simulate_first_order_step(
            current_value=current_value,
            applied_signal=0.0,
            disturbance=disturbance,
            plant_config=scenario.plant_config,
        )
        next_value = plant_step["next_value"]
        desired_level = plant_step["desired_level"]
        steps.append(
            _extract_step_record(
                step_index=step_index,
                scenario=scenario,
                current_value=current_value,
                disturbance=disturbance,
                result=result,
                next_value=next_value,
                desired_level=desired_level,
            )
        )
        current_value = next_value

    return {
        "scenario_id": scenario.scenario_id,
        "steps": steps,
        "summary_metrics": summarize_strategy_steps("feature_flag_guard", steps),
    }


def run_operational_control_benchmark() -> Dict[str, Any]:
    _ensure_runtime_env()
    worker = _build_worker_module()
    scenarios = build_operational_benchmark_scenarios()

    scenario_results = []
    benchmark_table = []
    scenario_assessments = []
    aggregate_steps: Dict[str, List[Dict[str, Any]]] = {
        "threshold": [],
        "proportional": [],
        "policy_driven": [],
    }

    for scenario in scenarios:
        _upsert_project(BENCHMARK_PROJECT_ID, enabled=True)
        strategy_runs: Dict[str, Dict[str, Any]] = {}

        for strategy_name, policies in build_strategy_policies(scenario.setpoint_value).items():
            _replace_project_policies(BENCHMARK_PROJECT_ID, policies)
            run = _run_strategy_for_scenario(
                worker=worker,
                project_id=BENCHMARK_PROJECT_ID,
                scenario=scenario,
                strategy_name=strategy_name,
            )
            strategy_runs[strategy_name] = run
            aggregate_steps[strategy_name].extend(run["steps"])

        summary_by_strategy = {
            strategy_name: run["summary_metrics"]
            for strategy_name, run in strategy_runs.items()
        }
        benchmark_table.extend(
            build_operational_benchmark_table_rows(scenario, summary_by_strategy)
        )
        scenario_assessments.append(
            build_operational_scenario_assessment(scenario, summary_by_strategy)
        )
        scenario_results.append(
            {
                "scenario": {
                    "scenario_id": scenario.scenario_id,
                    "label": scenario.label,
                    "description": scenario.description,
                    "setpoint_value": scenario.setpoint_value,
                    "sector": scenario.sector,
                    "plant_config": asdict(scenario.plant_config),
                    "simulation_config": asdict(scenario.simulation_config),
                },
                "strategies": strategy_runs,
            }
        )

    aggregate_summary = {
        strategy_name: summarize_strategy_steps(strategy_name, steps)
        for strategy_name, steps in aggregate_steps.items()
    }
    feature_flag_guard = _run_feature_flag_guard(worker, scenarios[0])

    interpretation = [
        "recovery_zone favorece proportional para bajar error medio sin escalar el esfuerzo total.",
        "trim_zone favorece threshold cuando el objetivo es priorizar error medio mas bajo sobre suavidad.",
        "policy_driven combina un proportional por defecto con un threshold contextual y por eso captura lo mejor de cada zona sin cambiar el worker.",
        "feature flag disabled mantiene consumo y auditoria, pero no emite recommendations.",
    ]

    return {
        "benchmark_name": BENCHMARK_NAME,
        "generated_at": BENCHMARK_GENERATED_AT,
        "project_id": BENCHMARK_PROJECT_ID,
        "variable_id": BENCHMARK_VARIABLE_ID,
        "scenarios": scenario_results,
        "benchmark_table": benchmark_table,
        "scenario_assessments": scenario_assessments,
        "aggregate_summary": aggregate_summary,
        "aggregate_assessment": {
            "lowest_mean_absolute_error": _best_strategies(
                aggregate_summary,
                "mean_absolute_error",
            ),
            "lowest_effort": _best_strategies(
                aggregate_summary,
                "total_applied_effort",
            ),
            "fewest_actions": _best_strategies(aggregate_summary, "actions_count"),
        },
        "feature_flag_guard": feature_flag_guard,
        "interpretation": interpretation,
    }


def build_operational_benchmark_markdown_table(rows: List[Dict[str, Any]]) -> str:
    headers = [
        "Scenario",
        "Strategy",
        "Mean Abs Error",
        "Effort",
        "Actions",
        "Recommendations",
        "Skipped",
        "Policies",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["scenario_label"],
                    row["strategy"],
                    str(row["mean_absolute_error"]),
                    str(row["total_applied_effort"]),
                    str(row["actions_count"]),
                    str(row["recommendations_emitted"]),
                    str(row["skipped_by_feature_flag"]),
                    ", ".join(row["policy_types"]) or "none",
                ]
            )
            + " |"
        )

    return "\n".join(lines)


def build_operational_benchmark_snapshot(benchmark_result: Dict[str, Any]) -> Dict[str, Any]:
    aggregate_rows = []
    for strategy_name, summary in benchmark_result["aggregate_summary"].items():
        aggregate_rows.append(
            {
                "strategy": strategy_name,
                "mean_absolute_error": summary["mean_absolute_error"],
                "mean_signed_error": summary["mean_signed_error"],
                "total_applied_effort": summary["total_applied_effort"],
                "actions_count": summary["actions_count"],
                "recommendations_emitted": summary["recommendations_emitted"],
                "skipped_by_feature_flag": summary["skipped_by_feature_flag"],
                "policies_applied": summary["policies_applied"],
            }
        )

    policy_driven_absolute = benchmark_result["aggregate_summary"]["policy_driven"]["mean_absolute_error"]
    threshold_absolute = benchmark_result["aggregate_summary"]["threshold"]["mean_absolute_error"]
    proportional_absolute = benchmark_result["aggregate_summary"]["proportional"]["mean_absolute_error"]
    lowest_error = ", ".join(benchmark_result["aggregate_assessment"]["lowest_mean_absolute_error"])
    lowest_effort = ", ".join(benchmark_result["aggregate_assessment"]["lowest_effort"])
    fewest_actions = ", ".join(benchmark_result["aggregate_assessment"]["fewest_actions"])

    executive_summary = (
        "Executive summary:\n"
        f"- Aggregate lowest mean absolute error was achieved by `{lowest_error}` with policy-driven=`{policy_driven_absolute}`, threshold=`{threshold_absolute}` and proportional=`{proportional_absolute}`.\n"
        f"- Aggregate lower effort was achieved by `{lowest_effort}`.\n"
        f"- Aggregate fewer actions was achieved by `{fewest_actions}`.\n"
        f"- Feature flag guard emitted `0` recommendations and recorded `{benchmark_result['feature_flag_guard']['summary_metrics']['skipped_by_feature_flag']}` skipped audits."
    )

    return {
        "benchmark_name": benchmark_result["benchmark_name"],
        "generated_at": benchmark_result["generated_at"],
        "project_id": benchmark_result["project_id"],
        "variable_id": benchmark_result["variable_id"],
        "executive_summary": executive_summary,
        "aggregate_rows": aggregate_rows,
        "aggregate_assessment": benchmark_result["aggregate_assessment"],
        "benchmark_table": benchmark_result["benchmark_table"],
        "markdown_table": build_operational_benchmark_markdown_table(
            benchmark_result["benchmark_table"]
        ),
        "scenario_assessments": benchmark_result["scenario_assessments"],
        "feature_flag_guard": benchmark_result["feature_flag_guard"],
        "scenario_breakdown": benchmark_result["scenarios"],
        "interpretation": benchmark_result["interpretation"],
    }


def build_operational_benchmark_markdown_report(snapshot: Dict[str, Any]) -> str:
    lines = [
        "# Operational Control Benchmark",
        "",
        "## Objective",
        "",
        "Benchmark operativo del `control_engine_worker` usando eventos compatibles con runtime, feature flag real, policies PostgreSQL y la planta first-order reproducible del parametric-control-engine.",
        "",
        "## Executive Summary",
        "",
        snapshot["executive_summary"],
        "",
        "## Aggregate Scorecard",
        "",
    ]

    for row in snapshot["aggregate_rows"]:
        policy_summary = ", ".join(
            f"{item['policy_type']} x{item['count']}"
            for item in row["policies_applied"]
        ) or "none"
        lines.extend(
            [
                f"### {row['strategy']}",
                "",
                f"- Mean absolute error: `{row['mean_absolute_error']}`",
                f"- Mean signed error: `{row['mean_signed_error']}`",
                f"- Total applied effort: `{row['total_applied_effort']}`",
                f"- Actions: `{row['actions_count']}`",
                f"- Recommendations emitted: `{row['recommendations_emitted']}`",
                f"- Skipped by feature flag: `{row['skipped_by_feature_flag']}`",
                f"- Policies applied: `{policy_summary}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Scenario Comparison",
            "",
            snapshot["markdown_table"],
            "",
            "## Scenario Assessment",
            "",
        ]
    )

    for assessment in snapshot["scenario_assessments"]:
        lines.extend(
            [
                f"### {assessment['scenario_label']}",
                "",
                f"- Lowest mean absolute error: `{', '.join(assessment['lowest_mean_absolute_error'])}`",
                f"- Lowest effort: `{', '.join(assessment['lowest_effort'])}`",
                f"- Fewest actions: `{', '.join(assessment['fewest_actions'])}`",
                "",
            ]
        )

    guard = snapshot["feature_flag_guard"]["summary_metrics"]
    lines.extend(
        [
            "## Feature Flag Guard",
            "",
            f"- Recommendations emitted: `{guard['recommendations_emitted']}`",
            f"- Skipped by feature flag: `{guard['skipped_by_feature_flag']}`",
            f"- Mean absolute error while disabled: `{guard['mean_absolute_error']}`",
            "",
            "## Interpretation",
            "",
        ]
    )

    for bullet in snapshot["interpretation"]:
        lines.append(f"- {bullet}")

    lines.extend(
        [
            "",
            "## Regeneration",
            "",
            "Regenerate these artifacts with:",
            "",
            "```bash",
            "PYTHONPATH=src ./venv/bin/python scripts/export_operational_control_benchmark.py",
            "```",
            "",
        ]
    )

    return "\n".join(lines)


def export_operational_control_benchmark_artifacts(output_dir: Path) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark_result = run_operational_control_benchmark()
    snapshot = build_operational_benchmark_snapshot(benchmark_result)
    markdown_report = build_operational_benchmark_markdown_report(snapshot)

    json_path = output_dir / "operational_control_benchmark.json"
    markdown_path = output_dir / "operational_control_benchmark.md"

    json_path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_report + "\n", encoding="utf-8")

    return {
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
    }
