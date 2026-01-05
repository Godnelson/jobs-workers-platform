# Architecture

## Components
- **API (FastAPI)**: creates jobs, lists/reads jobs.
- **Postgres**: single source of truth for job state & idempotency.
- **Redis**: queue backend.
- **RQ Worker**: executes tasks.
- **Scheduler**: periodically scans DB for due jobs and enqueues them.

## Core patterns
### Idempotency
Client supplies `idempotency_key`. The API enforces a unique constraint so repeated requests return the existing job.

### Distributed lock
Worker acquires Redis lock (`lock:job:{id}`) to prevent double execution across multiple workers.

### Retry
On failure, job status becomes `retrying` and `next_run_at` is scheduled with backoff.
Scheduler will enqueue due jobs (including retries) and delayed jobs.

## Data model (jobs)
- `id`: UUID
- `status`: queued | running | succeeded | failed | cancelled | retrying
- `attempts`, `max_attempts`
- `next_run_at`: when job becomes eligible to run
- `idempotency_key` unique
- `task_name`, `payload` (JSON)

## Growth ideas (to push it beyond)
- Dead Letter Queue (DLQ) for poison jobs
- Outbox pattern for reliable side effects
- OpenTelemetry exporter + dashboards
- RBAC + rate limiting per tenant
- Exactly-once “practical” with dedupe + outbox
