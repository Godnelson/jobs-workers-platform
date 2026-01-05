# ADR-0001: Redis + RQ for queueing

## Context
We need a simple, production-proven queue to run jobs asynchronously, with easy local dev.

## Decision
Use **Redis** as broker and **RQ** as queue implementation.

## Consequences
- Great DX and easy Docker setup
- Retry support exists, but we keep retry state in Postgres as source of truth
- Future: migrate to Redis Streams, Celery, or Kafka if needed
