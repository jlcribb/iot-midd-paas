# Transactional simulated-actuation outbox

The governance consumer persists `received -> validated -> ready_to_dispatch` and one outbox event in the same PostgreSQL transaction. Broker publication is outside that transaction and is at-least-once: a crash after publishing but before `published` may result in a safe republication with the same `event_id` and `command_id`.

`pending`, `publishing`, `published`, and `failed` are outbox states. A publisher claim increments the persisted attempt counter and holds a short lease. Expired leases are reclaimable using `FOR UPDATE SKIP LOCKED`; concurrent publishers can claim different rows but not the same row during a lease.

Broker publication failure keeps the event in the outbox with a retry time and error. After bounded retries it becomes `failed` and is retained for manual operational recovery: correct the broker condition, then deliberately reset that row to `pending` with a new `available_at` under an audited operator procedure. There is no automatic infinite replay.

The dispatch DLQ is intentionally separate. Outbox failure means the event was not delivered to the broker. A dispatch DLQ entry means it reached the broker but downstream simulated processing failed terminally. Neither mechanism can produce physical effects; all payloads declare `simulated=true` and `physical_effects=false`.

Operationally, an event is **stuck** when it remains `pending` or `publishing` longer than `ACTUATION_OUTBOX_STUCK_AFTER_SECONDS` (default operational threshold: 300 seconds). The repository exposes counts and `oldest_pending_age_seconds`; polling sleeps for at least 100 ms and defaults to one second.
