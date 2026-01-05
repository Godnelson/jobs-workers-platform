from datetime import datetime, timezone
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.queue import get_queue
from apps.api.schemas import CreateJobRequest, JobResponse
from apps.api.models import Job, JobStatus
from apps.api.settings import load_settings
from apps.api.utils import to_job_response
from apps.api.deps import get_session

log = structlog.get_logger()
router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(req: CreateJobRequest, session: AsyncSession = Depends(get_session)) -> JobResponse:
    settings = load_settings()
    now = datetime.now(timezone.utc)
    next_run_at = req.run_at or now

    job = Job(
        status=JobStatus.queued if next_run_at <= now else JobStatus.queued,
        task_name=req.task_name,
        payload=req.payload,
        idempotency_key=req.idempotency_key,
        max_attempts=req.max_attempts,
        next_run_at=next_run_at,
    )

    session.add(job)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing = await session.scalar(select(Job).where(Job.idempotency_key == req.idempotency_key))
        if not existing:
            raise
        return to_job_response(existing)

    # enqueue immediately if due; otherwise scheduler will pick it up
    if next_run_at <= now:
        q = get_queue(settings.redis_url, settings.rq_queue_name)
        q.enqueue("apps.worker.tasks.execute_job", str(job.id), job_timeout=600)

    log.info("job_created", job_id=str(job.id), task=job.task_name, run_at=str(next_run_at))
    return to_job_response(job)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: UUID, session: AsyncSession = Depends(get_session)) -> JobResponse:
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return to_job_response(job)


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    status_: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[JobResponse]:
    stmt = select(Job).order_by(Job.created_at.desc()).limit(limit)
    if status_:
        try:
            st = JobStatus(status_)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_}")
        stmt = stmt.where(Job.status == st)

    rows = (await session.scalars(stmt)).all()
    return [to_job_response(j) for j in rows]
