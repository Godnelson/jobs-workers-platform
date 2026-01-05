# Jobs/Workers Platform (FastAPI + Postgres + Redis)

A production-style **asynchronous job execution platform** with:
- **FastAPI** API to create/query jobs
- **Postgres** as source of truth (idempotency, status, attempts, errors)
- **Redis + RQ** for queueing
- **Worker** process executing tasks with **distributed lock** and **idempotent** execution
- **Scheduler** process for delayed jobs / cron-like triggers
- Structured logging (JSON) + optional OpenTelemetry hooks

> Goal: portfolio project that demonstrates real backend concerns: retries, idempotency, observability, multi-process execution, deployability.

## Quick start (Docker)
1. Copy env:
```bash
cp .env.example .env
```
2. Start stack:
```bash
docker compose up --build
```
3. Create a job:
```bash
curl -X POST http://localhost:8080/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "echo",
    "payload": {"message": "hello"},
    "idempotency_key": "demo-echo-1",
    "max_attempts": 5
  }'
```

4. List jobs:
```bash
curl http://localhost:8080/v1/jobs
```

## Endpoints
- `POST /v1/jobs` create a job (supports idempotency)
- `GET /v1/jobs/{job_id}` read status/details
- `GET /v1/jobs` list jobs (filters by status)

## Local dev (without Docker)
- Requires Postgres + Redis
- Install deps:
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
- Run migrations:
```bash
alembic upgrade head
```
- Run API:
```bash
uvicorn apps.api.main:app --reload --port 8080
```
- Run worker:
```bash
python -m apps.worker.worker
```
- Run scheduler:
```bash
python -m apps.scheduler.scheduler
```

## Architecture (high level)
- API writes job row to Postgres in `jobs`
- API enqueues job id to Redis queue via RQ
- Worker pulls job id, acquires a **Redis lock** (`lock:job:{id}`), then:
  - loads job from DB
  - ensures **idempotency** (won't execute terminal states)
  - runs task implementation
  - updates DB status + attempts + error
  - retries by re-enqueueing if allowed

See: `docs/architecture.md`

## Notes
This is intentionally a **portfolio-grade skeleton**:
- It’s runnable as-is
- It includes senior-ish patterns (idempotency, lock, retries, migrations, structured logs)
- You can expand it with DLQ, outbox, OpenTelemetry export, RBAC, rate limiting, dashboards, etc.
