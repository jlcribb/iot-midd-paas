"""Parametric control engine MVP for Midd IOT."""

from .adapters.event_adapter import EventDrivenRecommendationAdapter
from .adapters.recommendation_sink_adapter import RecommendationSinkAdapter
from .contracts.event_adapter_contracts import (
    EventDrivenRecommendation,
    MonovariableControlBinding,
    TelemetryStateEvent,
)
from .contracts.sink_contracts import (
    PublishableRecommendationEnvelope,
    RecommendationAuditEnvelope,
    RecommendationSinkOutput,
)
from .contracts.policy_contracts import (
    PolicySelectionRequest,
    PolicySelectionResult,
    StaticPolicyDefinition,
)
from .contracts.policy_source_contracts import (
    PolicySourceRequest,
    PolicySourceResult,
)
from .contracts.control_contracts import (
    ControlEvaluationRequest,
    ControlEvaluationResponse,
)
from .evaluators.proportional import ProportionalEvaluator
from .evaluators.threshold import ThresholdEvaluator
from .models.control_models import (
    ActionKind,
    ActionRecommendation,
    ControlParameterSet,
    ControlledVariableDefinition,
    ControlParameters,
    MeasurementState,
    SetpointReference,
    ThresholdControlParameters,
    TraceEntry,
)
from .policies.static_selector import StaticPolicySelector
from .simulation.first_order import (
    ClosedLoopSimulationConfig,
    FirstOrderPlantConfig,
    simulate_closed_loop_strategy,
    simulate_first_order_step,
)
from .simulation.benchmark_suite import (
    BenchmarkScenario,
    build_standard_benchmark_scenarios,
    run_closed_loop_benchmark_suite,
)
from .simulation.benchmark_formatter import (
    build_executive_summary,
    build_markdown_table,
    build_presentation_ready_benchmark,
    build_scorecard_view,
)
from .simulation.benchmark_exporter import (
    build_benchmark_markdown_report,
    build_benchmark_snapshot,
    export_benchmark_artifacts,
)
from .simulation.metrics import (
    build_comparison_overview,
    calculate_summary_metrics,
)
from .sources.in_memory_policy_source import InMemoryPolicySource

__all__ = [
    "ActionKind",
    "ActionRecommendation",
    "BenchmarkScenario",
    "build_benchmark_markdown_report",
    "build_benchmark_snapshot",
    "ControlledVariableDefinition",
    "ControlEvaluationRequest",
    "ControlEvaluationResponse",
    "ControlParameters",
    "ControlParameterSet",
    "EventDrivenRecommendation",
    "EventDrivenRecommendationAdapter",
    "FirstOrderPlantConfig",
    "ClosedLoopSimulationConfig",
    "MeasurementState",
    "MonovariableControlBinding",
    "PolicySelectionRequest",
    "PolicySelectionResult",
    "PolicySourceRequest",
    "PolicySourceResult",
    "PublishableRecommendationEnvelope",
    "ProportionalEvaluator",
    "RecommendationAuditEnvelope",
    "RecommendationSinkAdapter",
    "RecommendationSinkOutput",
    "SetpointReference",
    "build_executive_summary",
    "build_markdown_table",
    "build_presentation_ready_benchmark",
    "build_scorecard_view",
    "build_standard_benchmark_scenarios",
    "simulate_closed_loop_strategy",
    "simulate_first_order_step",
    "build_comparison_overview",
    "calculate_summary_metrics",
    "export_benchmark_artifacts",
    "run_closed_loop_benchmark_suite",
    "StaticPolicyDefinition",
    "StaticPolicySelector",
    "InMemoryPolicySource",
    "TelemetryStateEvent",
    "ThresholdControlParameters",
    "ThresholdEvaluator",
    "TraceEntry",
]
