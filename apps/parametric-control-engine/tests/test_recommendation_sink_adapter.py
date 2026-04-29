from parametric_control_engine.adapters.event_adapter import EventDrivenRecommendationAdapter
from parametric_control_engine.adapters.recommendation_sink_adapter import RecommendationSinkAdapter
from parametric_control_engine.examples.event_driven_demo import (
    build_demo_binding,
    build_demo_event,
)


def build_recommendation():
    event_adapter = EventDrivenRecommendationAdapter(build_demo_binding())
    return event_adapter.evaluate_event(build_demo_event())


def test_sink_adapter_builds_publishable_runtime_envelope():
    sink_adapter = RecommendationSinkAdapter()

    output = sink_adapter.build_sink_output(build_recommendation())

    assert output.publish_envelope.envelope_id == "publish::evt-1001::tank-level-01"
    assert output.publish_envelope.channel == "runtime.control.recommendations"
    assert output.publish_envelope.message_type == "control.recommendation"
    assert output.publish_envelope.message_key == "tank-level-01:evt-1001"
    assert output.publish_envelope.payload["recommendation_kind"] == "increase"
    assert output.publish_envelope.payload["binding_channel"] == "runtime.control.recommendations"


def test_sink_adapter_builds_persistable_audit_envelope():
    sink_adapter = RecommendationSinkAdapter()

    output = sink_adapter.build_sink_output(build_recommendation())

    assert output.audit_envelope.audit_id == "audit::evt-1001::tank-level-01"
    assert output.audit_envelope.record_type == "control.recommendation.audit"
    assert output.audit_envelope.partition_key == "tank-level-01"
    assert output.audit_envelope.payload["event_id"] == "evt-1001"
    assert output.audit_envelope.payload["evaluation"]["recommendation"]["kind"] == "increase"
    assert output.audit_envelope.payload["adapter_trace"][-1]["step"] == "control_request_built"


def test_sink_adapter_keeps_output_traceability():
    sink_adapter = RecommendationSinkAdapter()

    output = sink_adapter.build_sink_output(build_recommendation())

    assert output.sink_trace[0].step == "trace_initialized"
    assert output.sink_trace[1].step == "recommendation_received"
    assert output.sink_trace[-1].step == "audit_envelope_built"
