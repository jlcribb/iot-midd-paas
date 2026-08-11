"""At-least-once publisher for persisted simulated dispatch events."""
from __future__ import annotations
import os,time
from iot_middleware.storage.actuation_outbox_repository import ActuationOutboxRepository

class ActuationOutboxPublisher:
    def __init__(self, repository=None, client=None, max_attempts=3): self.repository=repository or ActuationOutboxRepository(); self.client=client; self.max_attempts=max_attempts
    def publish_once(self, limit=20):
        if self.client is None:
            from iot_middleware.services.control_engine_worker import _load_rabbitmq_client
            self.client,_=_load_rabbitmq_client()
        result=[]
        for event in self.repository.claim(limit=limit):
            try:
                if not self.client.publish_json(routing_key=event.routing_key, payload=event.payload): raise ConnectionError('broker_publish_false')
                self.repository.mark_published(event.event_id); result.append(('published',event.event_id))
            except Exception as exc:
                self.repository.retry_or_fail(event.event_id,exc,self.max_attempts); result.append(('retry',event.event_id))
        return result
def main():
    publisher=ActuationOutboxPublisher(); interval=float(os.getenv('ACTUATION_OUTBOX_POLL_INTERVAL_SECONDS','1'))
    while True: publisher.publish_once(); time.sleep(max(.1,interval))
if __name__=='__main__': main()
