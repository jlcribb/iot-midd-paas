from iot_middleware.services.operational_control_benchmark import (
    build_operational_benchmark_markdown_report,
    build_operational_benchmark_snapshot,
)


def _sample_result():
    return {
        "benchmark_name": "operational-control-worker-benchmark",
        "generated_at": "2026-04-29T00:00:00+00:00",
        "project_id": "00000000-0000-0000-0000-0000000000b5",
        "variable_id": "tank_level",
        "aggregate_summary": {
            "threshold": {
                "mean_absolute_error": 4.2,
                "mean_signed_error": -1.1,
                "total_applied_effort": 40.0,
                "actions_count": 6,
                "recommendations_emitted": 16,
                "skipped_by_feature_flag": 0,
                "policies_applied": [
                    {
                        "policy_id": "11111111-1111-1111-1111-111111111111",
                        "policy_type": "threshold",
                        "count": 16,
                    }
                ],
            },
            "proportional": {
                "mean_absolute_error": 3.6,
                "mean_signed_error": -0.4,
                "total_applied_effort": 31.0,
                "actions_count": 5,
                "recommendations_emitted": 16,
                "skipped_by_feature_flag": 0,
                "policies_applied": [
                    {
                        "policy_id": "22222222-2222-2222-2222-222222222222",
                        "policy_type": "proportional",
                        "count": 16,
                    }
                ],
            },
            "policy_driven": {
                "mean_absolute_error": 3.1,
                "mean_signed_error": -0.2,
                "total_applied_effort": 33.0,
                "actions_count": 5,
                "recommendations_emitted": 16,
                "skipped_by_feature_flag": 0,
                "policies_applied": [
                    {
                        "policy_id": "33333333-3333-3333-3333-333333333333",
                        "policy_type": "proportional",
                        "count": 8,
                    },
                    {
                        "policy_id": "44444444-4444-4444-4444-444444444444",
                        "policy_type": "threshold",
                        "count": 8,
                    },
                ],
            },
        },
        "aggregate_assessment": {
            "lowest_mean_absolute_error": ["policy_driven"],
            "lowest_effort": ["proportional"],
            "fewest_actions": ["proportional", "policy_driven"],
        },
        "benchmark_table": [
            {
                "scenario_id": "recovery_zone",
                "scenario_label": "Recovery Zone",
                "strategy": "threshold",
                "mean_absolute_error": 4.8,
                "mean_signed_error": -1.4,
                "total_applied_effort": 28.0,
                "actions_count": 5,
                "recommendations_emitted": 8,
                "skipped_by_feature_flag": 0,
                "policy_types": ["threshold"],
            },
            {
                "scenario_id": "recovery_zone",
                "scenario_label": "Recovery Zone",
                "strategy": "policy_driven",
                "mean_absolute_error": 4.8,
                "mean_signed_error": -1.4,
                "total_applied_effort": 28.0,
                "actions_count": 5,
                "recommendations_emitted": 8,
                "skipped_by_feature_flag": 0,
                "policy_types": ["threshold"],
            },
        ],
        "scenario_assessments": [
            {
                "scenario_id": "recovery_zone",
                "scenario_label": "Recovery Zone",
                "lowest_mean_absolute_error": ["threshold", "policy_driven"],
                "lowest_effort": ["proportional"],
                "fewest_actions": ["proportional"],
            }
        ],
        "feature_flag_guard": {
            "scenario_id": "recovery_zone",
            "summary_metrics": {
                "recommendations_emitted": 0,
                "skipped_by_feature_flag": 3,
                "mean_absolute_error": 12.5,
            },
        },
        "scenarios": [
            {
                "scenario": {
                    "scenario_id": "recovery_zone",
                    "label": "Recovery Zone",
                }
            }
        ],
        "interpretation": [
            "policy-driven combines contextual threshold and default proportional behavior."
        ],
    }


def test_build_operational_benchmark_snapshot_contains_required_sections():
    snapshot = build_operational_benchmark_snapshot(_sample_result())

    assert snapshot["benchmark_name"] == "operational-control-worker-benchmark"
    assert "aggregate_rows" in snapshot
    assert "markdown_table" in snapshot
    assert "executive_summary" in snapshot
    assert snapshot["feature_flag_guard"]["summary_metrics"]["skipped_by_feature_flag"] == 3


def test_build_operational_benchmark_markdown_report_contains_regeneration_command():
    snapshot = build_operational_benchmark_snapshot(_sample_result())

    report = build_operational_benchmark_markdown_report(snapshot)

    assert "# Operational Control Benchmark" in report
    assert "## Aggregate Scorecard" in report
    assert "## Feature Flag Guard" in report
    assert "python scripts/export_operational_control_benchmark.py" in report
