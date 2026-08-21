"""Deterministic, side-effect-free execution of a READY simulation session."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from parametric_control_engine.adapters.event_adapter import EventDrivenRecommendationAdapter
from parametric_control_engine.contracts.event_adapter_contracts import (
    MonovariableControlBinding, TelemetryStateEvent,
)
from parametric_control_engine.contracts.policy_contracts import StaticPolicyDefinition
from parametric_control_engine.execution_context import SimulationClock, simulation_execution_context
from parametric_control_engine.models.control_models import (
    ActionKind, ControlParameters, ControlledVariableDefinition, SetpointReference,
    ThresholdControlParameters,
)
from parametric_control_engine.policies.static_selector import StaticPolicySelector
from parametric_control_engine.sources.in_memory_policy_source import InMemoryPolicySource
from parametric_control_engine.evaluators.threshold import ThresholdEvaluator

from iot_middleware.storage.simulation_run_repository import (
    SimulationRun, SimulationRunEvent, SimulationRunRepository, StoredSimulationSession,
)


REPLAY_ENGINE_VERSION = "1"
COMPATIBLE_CONTROL_ENGINE_VERSION = "0.1.0"
SUPPORTED_CLOCK_MODEL_VERSION = "1"
MAX_SYNCHRONOUS_RECORDS = 500


class SimulationReplayRejected(ValueError):
    """Raised before execution when a frozen experiment is not eligible."""


@dataclass(frozen=True)
class ReplayDomainOutput:
    sequence: int
    event_id: str
    virtual_timestamp: datetime
    evaluation_outcome: str
    has_recommendation: bool
    actionable: bool
    recommendation_only: bool
    reason_code: str
    recommendation_kind: str | None
    action_label: str | None
    command_value: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1, "sequence": self.sequence, "event_id": self.event_id,
            "virtual_timestamp": self.virtual_timestamp.isoformat(),
            "evaluation_outcome": self.evaluation_outcome,
            "has_recommendation": self.has_recommendation, "actionable": self.actionable,
            "recommendation_only": self.recommendation_only, "reason_code": self.reason_code,
            "recommendation_kind": self.recommendation_kind, "action_label": self.action_label,
            "command_value": self.command_value, "execution_context": "SIMULATION",
            "physical_effects": False,
        }


class SimulationReplayRunner:
    """Runs frozen definitions using the production control domain core only.

    The only policy source constructed here is ``InMemoryPolicySource`` populated
    from the immutable session snapshot.  It is intentionally impossible for this
    class to resolve a PostgreSQL policy, publish a recommendation, or create a
    delivery/outbox record.
    """

    def __init__(self, repository: SimulationRunRepository | None = None) -> None:
        self._repository = repository or SimulationRunRepository()

    def execute(self, *, project_id: str, session_id: str, created_by: str) -> SimulationRun:
        session = self._repository.load_session(project_id, session_id)
        definition = self._validate_ready_definition(session)
        configuration = definition.configuration_snapshot or {}
        engine = configuration["engine"]
        clock_model = configuration["clock"]
        run = self._repository.create(
            project_id=project_id, session_id=session_id, created_by=created_by,
            engine_version=str(engine["version"]), replay_engine_version=REPLAY_ENGINE_VERSION,
            clock_model_version=str(clock_model["model_version"]),
        )
        try:
            self._repository.mark_running(run.id)
            outputs = self.replay(session)
            persisted = [SimulationRunEvent(run_id=run.id, sequence=item.sequence,
                         event_id=item.event_id, virtual_timestamp=item.virtual_timestamp,
                         output=item.as_dict()) for item in outputs]
            return self._repository.complete(run.id, persisted)
        except Exception as exc:
            self._repository.fail(run.id, code=self._failure_code(exc), detail=str(exc))
            raise

    def replay(self, session: StoredSimulationSession) -> list[ReplayDomainOutput]:
        """Pure replay helper used by tests and by the persisted runner."""
        definition = self._validate_ready_definition(session)
        policy_snapshot = definition.policy_snapshot or {}
        topology_snapshot = definition.topology_snapshot or {}
        dataset_snapshot = definition.dataset_snapshot or {}
        configuration = definition.configuration_snapshot or {}
        policy = self._policy_from_snapshot(policy_snapshot, topology_snapshot)
        selector = StaticPolicySelector(InMemoryPolicySource([policy]))
        records = dataset_snapshot["records"]
        initial = self._parse_timestamp(configuration["clock"]["initial_virtual_time"])
        clock = SimulationClock(initial)
        outputs: list[ReplayDomainOutput] = []
        for sequence, record in enumerate(records, start=1):
            virtual_timestamp = self._parse_timestamp(record["timestamp"])
            clock = clock.advance_to(virtual_timestamp)
            context = simulation_execution_context(session_id=session.id, clock=clock)
            # These invariant checks prove the replay context cannot become an
            # operational delivery context before evaluation.
            if context.side_effects.operational_outbox_allowed or context.side_effects.operational_transport_allowed:
                raise SimulationReplayRejected("simulation side effects must remain disabled")
            event = TelemetryStateEvent(
                event_id=str(record["event_id"]), variable_id=str(record["variable"]),
                value=float(record["value"]), observed_at=context.clock.now(),
                quality=str(record.get("quality") or "raw"), source=str(record.get("source") or "simulation"),
                event_kind=str(record.get("event_kind") or "telemetry.observed"),
                metadata=dict(record.get("metadata") or {}), context=dict(record.get("context") or {}),
            )
            selection = selector.resolve_event(event)
            evaluator = ThresholdEvaluator() if selection.policy_type == "threshold" else None
            recommendation = EventDrivenRecommendationAdapter(selection.binding, evaluator).evaluate_event(event)
            kind = recommendation.evaluation.recommendation.kind
            has_recommendation = kind is not ActionKind.HOLD
            actionable = has_recommendation and self._frozen_target_is_actionable(topology_snapshot)
            recommendation_only = has_recommendation and not actionable
            reason = (
                "NO_RECOMMENDATION_HOLD" if not has_recommendation else
                "ACTIONABLE_FROZEN_TARGET" if actionable else
                "RECOMMENDATION_ONLY_NO_FROZEN_TARGET"
            )
            outputs.append(ReplayDomainOutput(
                sequence=sequence, event_id=event.event_id, virtual_timestamp=clock.now(),
                evaluation_outcome="RECOMMENDED" if has_recommendation else "NO_RECOMMENDATION",
                has_recommendation=has_recommendation, actionable=actionable,
                recommendation_only=recommendation_only, reason_code=reason,
                recommendation_kind=kind.value if has_recommendation else None,
                action_label=recommendation.evaluation.recommendation.action_label if has_recommendation else None,
                command_value=recommendation.evaluation.recommendation.command_value if has_recommendation else None,
            ))
        return outputs

    def _validate_ready_definition(self, session: StoredSimulationSession | None) -> StoredSimulationSession:
        if session is None:
            raise SimulationReplayRejected("simulation session not found")
        if session.status != "READY":
            raise SimulationReplayRejected("only READY simulation sessions may be run")
        if not all((session.policy_snapshot, session.topology_snapshot, session.dataset_snapshot,
                    session.configuration_snapshot, session.experiment_fingerprint)):
            raise SimulationReplayRejected("READY session has incomplete frozen experiment definition")
        configuration = session.configuration_snapshot or {}
        engine = configuration.get("engine") if isinstance(configuration, dict) else None
        clock = configuration.get("clock") if isinstance(configuration, dict) else None
        if not isinstance(engine, dict) or engine.get("name") != "parametric-control-engine" or engine.get("version") != COMPATIBLE_CONTROL_ENGINE_VERSION:
            raise SimulationReplayRejected("incompatible frozen control engine version")
        if not isinstance(clock, dict) or str(clock.get("model_version")) != SUPPORTED_CLOCK_MODEL_VERSION:
            raise SimulationReplayRejected("incompatible simulation clock model")
        effects = configuration.get("operational_side_effects")
        if effects != {"outbox": False, "transport": False, "physical_effects": False}:
            raise SimulationReplayRejected("simulation snapshot side-effect policy is invalid")
        records = (session.dataset_snapshot or {}).get("records")
        if not isinstance(records, list) or not records:
            raise SimulationReplayRejected("frozen dataset must contain records")
        if len(records) > MAX_SYNCHRONOUS_RECORDS:
            raise SimulationReplayRejected(f"frozen dataset exceeds synchronous limit {MAX_SYNCHRONOUS_RECORDS}")
        expected = sorted(records, key=lambda item: (str(item.get("timestamp")), str(item.get("event_id"))))
        if records != expected:
            raise SimulationReplayRejected("frozen dataset is not in canonical timestamp,event_id order")
        return session

    def _policy_from_snapshot(self, policy_snapshot: dict[str, Any], topology_snapshot: dict[str, Any]) -> StaticPolicyDefinition:
        policy = policy_snapshot.get("policy")
        if not isinstance(policy, dict) or not policy.get("enabled", False):
            raise SimulationReplayRejected("frozen policy is missing or disabled")
        params = dict(policy.get("params") or {})
        policy_type = str(policy.get("policy_type") or "proportional")
        variable_id = str(policy["variable"])
        variable = ControlledVariableDefinition(
            variable_id=variable_id, name=str(params.get("variable_name") or variable_id),
            unit=str(params.get("variable_unit") or "units"),
            actuator_name=str(params.get("actuator_name") or "control_output"),
            increase_action_label=str(params.get("increase_action_label") or "increase"),
            decrease_action_label=str(params.get("decrease_action_label") or "decrease"),
            hold_action_label=str(params.get("hold_action_label") or "hold"),
            controller_direction=float(params.get("controller_direction") or 1.0),
        )
        if policy_type == "threshold":
            parameter_set = ThresholdControlParameters(
                tolerance=float(params.get("tolerance", 0.5)), increase_step=float(params.get("increase_step", 1.0)),
                decrease_step=float(params.get("decrease_step", 1.0)), hold_signal=float(params.get("hold_signal", 0.0)),
            )
        elif policy_type == "proportional":
            maximum = params.get("max_action")
            parameter_set = ControlParameters(gain=float(params.get("gain", 1.0)),
                deadband=float(params.get("deadband", 0.0)), min_action=float(params.get("min_action", 0.0)),
                max_action=float(maximum) if maximum is not None else None)
        else:
            raise SimulationReplayRejected(f"unsupported frozen policy type {policy_type!r}")
        binding = MonovariableControlBinding(
            variable=variable, setpoint=SetpointReference(value=float(params.get("setpoint_value", 70.0)),
            label=str(params.get("setpoint_label") or "frozen-setpoint")), parameters=parameter_set,
            recommendation_channel="simulation-only", context={"project_id": str(policy["project_id"]),
            "source_asset_id": str(policy["source_asset_id"]), "topology_snapshot": topology_snapshot.get("schema_version")},
        )
        return StaticPolicyDefinition(policy_id=str(policy["id"]), binding=binding,
            required_context=dict(policy.get("context_selector") or {}), priority=int(policy.get("priority") or 0),
            version=int(policy.get("version") or 1), policy_type=policy_type, params=params)

    @staticmethod
    def _frozen_target_is_actionable(topology_snapshot: dict[str, Any]) -> bool:
        binding = topology_snapshot.get("actuation_binding")
        target = topology_snapshot.get("target_asset")
        return bool(isinstance(binding, dict) and binding.get("enabled") is True and binding.get("target_asset_id")
                    and binding.get("control_point") and binding.get("operation") and isinstance(target, dict)
                    and target.get("id") == binding.get("target_asset_id") and target.get("status") not in {"retired", "disabled"})

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if not isinstance(value, str):
            raise SimulationReplayRejected("frozen record timestamp is required")
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise SimulationReplayRejected("frozen record timestamp must include timezone")
        return parsed

    @staticmethod
    def _failure_code(error: Exception) -> str:
        return "SIMULATION_REPLAY_REJECTED" if isinstance(error, SimulationReplayRejected) else "SIMULATION_REPLAY_FAILED"
