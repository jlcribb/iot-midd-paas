"""Broker consumer for outbox-produced simulated dispatch events only."""
from __future__ import annotations
import json, time
from parametric_control_engine.contracts.actuation_contracts import ActuationRequest
from iot_middleware.services.simulated_actuation_consumer import SimulatedActuationConsumer

DISPATCH_QUEUE='control.actuation.simulated.dispatch.v1'

def main():
    from iot_middleware.services.control_engine_worker import _load_rabbitmq_client
    client,_=_load_rabbitmq_client(); client.declare_topic_queue(DISPATCH_QUEUE,routing_keys=[DISPATCH_QUEUE],durable=True)
    consumer=SimulatedActuationConsumer(dispatch_immediately=True)
    while True:
        message=client.get_raw_message(DISPATCH_QUEUE,auto_ack=False)
        if not message: time.sleep(1); continue
        try:
            event=json.loads(message['body'].decode()); payload=event['payload']
            request=ActuationRequest(**payload)
            intent=consumer.repository.get_by_command_id(request.command_id)
            if intent is None: raise ValueError('intent_missing')
            outcome=consumer._dispatch(intent,request,from_statuses={'ready_to_dispatch'})
            client.ack_message(message['delivery_tag'])
        except Exception:
            client.nack_message(message['delivery_tag'],requeue=False)

if __name__=='__main__': main()
