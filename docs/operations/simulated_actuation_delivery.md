# Simulated actuation delivery reliability

## Scope

`simulated-actuation-consumer` only handles the versioned routing key
`control.recommendations.simulated.v1`. It has no physical adapter, MQTT
command publication, automatic actuation, or DLQ replay capability. The legacy
`control.recommendations` backlog remains isolated and untouched.

## Failure taxonomy and state machine

Validation, schema, target, governance, and unknown adapter errors are
non-retryable. Connection, timeout, and explicitly typed transient adapter
errors are retryable. The persisted intent state machine is:

```text
received -> validated -> ready_to_dispatch -> dispatched -> acknowledged
                                                    |        
                                                    +-> retry_pending -> dispatched
                                                    |                    
                                                    +-> failed_final
```

`received` may also end in `rejected` or `expired`; `retry_pending` may end in
`expired` or `failed_final`. Terminal states are `acknowledged`, `rejected`,
`expired`, and `failed_final`.

The retry policy is bounded by `SIMULATED_ACTUATION_MAX_RETRY_ATTEMPTS`
(default `3` total dispatch attempts). Delay is exponential from
`SIMULATED_ACTUATION_RETRY_BASE_DELAY_SECONDS` (default `1`), capped by
`SIMULATED_ACTUATION_RETRY_MAX_DELAY_SECONDS` (default `30`). Optional jitter
is disabled by default and can be set through
`SIMULATED_ACTUATION_RETRY_JITTER_SECONDS`. Intent rows persist the attempt
count, last error type, last attempt timestamp, and next retry timestamp.

## ACK and DLQ semantics

The consumer never uses `requeue=true`.

- success, duplicate, expiry, and persisted retry scheduling: ACK after the
  durable intent decision;
- permanent failure or retry exhaustion: write the terminal intent, publish a
  minimal dead-letter envelope, then ACK;
- malformed input: publish a minimal dead-letter envelope, then ACK;
- failure to persist or to publish the enriched dead-letter envelope: NACK with
  `requeue=false`, using the queue DLX as the bounded broker fallback.

The simulated main queue declares DLX
`control.actuation.simulated.dlx` and DLQ
`control.actuation.simulated.dlq.v1`. The DLQ is a quarantine: it has no
consumer and no automatic replay. Dead-letter metadata includes reason,
original routing key, known correlation identifiers, command identifier, and
attempt count; it never copies the original payload.

## Auditing and observability

The in-memory consumer metrics reset on restart and include received, valid,
invalid, duplicate, expired, dispatch success/retry/failure, dead-lettered,
intents created/reused, and audit failures. Structured logs preserve command
and correlation identifiers where available. Audited actions cover intent
creation/reuse, dispatch attempts, retry scheduling, acknowledgement,
terminal failure/exhaustion, expiry, malformed input, and dead-lettering.

Audit persistence remains best-effort. A persistence problem is logged and
counted explicitly; it is not represented as an atomic broker-and-database
transaction.

## Outbox boundary

The transition to `ready_to_dispatch` atomically inserts one simulated dispatch
event into `control_actuation_outbox`. A separate at-least-once publisher sends
it to `control.actuation.simulated.dispatch.v1`; a dispatch consumer then uses
the existing simulated adapter and intent idempotency boundary. Broker failure
remains in the outbox; a terminal downstream failure goes to the existing
simulated DLQ. This does not introduce a physical adapter or physical command
publication.

The publisher requires RabbitMQ publisher confirms before marking an outbox
event as `published`. A closed channel is recreated when its connection remains
healthy; a connection reset invalidates both objects so the next polling cycle
creates a fresh connection and channel. The same `event_id` remains eligible
for persisted retry, so this preserves at-least-once delivery and downstream
idempotency rather than claiming exactly-once delivery.
