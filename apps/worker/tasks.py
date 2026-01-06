from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

import structlog
from redis import Redis
from rq import get_current_job
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db import get_sessionmaker, init_engine
from apps.api.models import Job, JobStatus
from apps.api.settings import load_settings
from apps.worker.common import redis_lock
from apps.task_registry import get_task

log = structlog.get_logger()

def backoff_seconds(attempt: int) -> int:
    # Exponential backoff with cap
    return min(2 ** attempt, 300)


def execute_job(job_id: str) -> None:
    # RQ entrypoint must be sync; we delegate to async
    import asyncio as _asyncio

    _asyncio.run(_execute_job_async(UUID(job_id)))


async def _execute_job_async(job_id: UUID) -> None:
    settings = load_settings()
    init_engine(settings.database_url)
    Session = get_sessionmaker()

    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    lock_key = f"lock:job:{job_id}"

    with redis_lock(redis, lock_key, ttl_seconds=300) as acquired:
        if not acquired:
            log.info("job_lock_not_acquired", job_id=str(job_id))
            return

        async with Session() as session:
            job = await session.get(Job, job_id)
            if not job:
                log.warning("job_not_found", job_id=str(job_id))
                return

            if job.status in {JobStatus.succeeded, JobStatus.failed, JobStatus.cancelled}:
                log.info("job_already_terminal", job_id=str(job_id), status=job.status.value)
                return

            now = datetime.now(timezone.utc)
            if job.next_run_at and job.next_run_at > now:
                # not due; scheduler will enqueue later
                log.info("job_not_due", job_id=str(job_id), next_run_at=str(job.next_run_at))
                return

            job.status = JobStatus.running
            job.attempts += 1
            await session.commit()

            task = get_task(job.task_name)
            if not task:
                job.status = JobStatus.failed
                job.last_error = f"Unknown task_name: {job.task_name}"
                await session.commit()
                log.error("job_unknown_task", job_id=str(job_id), task=job.task_name)
                return

            try:
                result = await task(job.payload)
                job.status = JobStatus.succeeded
                job.last_error = None
                # store result into payload (simple approach); in a real system you'd have a result column/table
                job.payload = {**job.payload, "_result": result}
                await session.commit()
                log.info("job_succeeded", job_id=str(job_id), task=job.task_name, attempts=job.attempts)
            except Exception as e:
                err = f"{type(e).__name__}: {e}"
                remaining = job.attempts < job.max_attempts
                if remaining:
                    delay = backoff_seconds(job.attempts)
                    job.status = JobStatus.retrying
                    job.last_error = err
                    job.next_run_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
                    await session.commit()
                    log.warning(
                        "job_failed_will_retry",
                        job_id=str(job_id),
                        task=job.task_name,
                        attempts=job.attempts,
                        next_run_in_s=delay,
                        error=err,
                    )
                else:
                    job.status = JobStatus.failed
                    job.last_error = err
                    await session.commit()
                    log.error("job_failed_terminal", job_id=str(job_id), task=job.task_name, attempts=job.attempts, error=err)
