from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis import Redis
from rq import Queue
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.logging import configure_logging
from apps.api.db import get_sessionmaker, init_engine
from apps.api.models import Job, JobStatus
from apps.api.settings import load_settings

log = structlog.get_logger()


async def enqueue_due_jobs() -> None:
    settings = load_settings()
    init_engine(settings.database_url)
    Session = get_sessionmaker()

    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    q = Queue(settings.rq_queue_name, connection=redis)

    now = datetime.now(timezone.utc)

    async with Session() as session:
        stmt = (
            select(Job)
            .where(Job.status.in_([JobStatus.queued, JobStatus.retrying]))
            .where((Job.next_run_at.is_(None)) | (Job.next_run_at <= now))
            .order_by(Job.created_at.asc())
            .limit(200)
        )
        jobs = (await session.scalars(stmt)).all()

    for j in jobs:
        q.enqueue("apps.worker.tasks.execute_job", str(j.id), job_timeout=600)

    if jobs:
        log.info("scheduler_enqueued", count=len(jobs))


async def run_scheduler() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(enqueue_due_jobs, "interval", seconds=5, id="enqueue_due")
    scheduler.start()

    log.info("scheduler_started")
    await asyncio.Event().wait()


def main() -> None:
    asyncio.run(run_scheduler())


if __name__ == "__main__":
    main()
