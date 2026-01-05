from apps.api.schemas import JobResponse
from apps.api.models import Job


def to_job_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        status=job.status.value,
        task_name=job.task_name,
        payload=job.payload,
        idempotency_key=job.idempotency_key,
        attempts=job.attempts,
        max_attempts=job.max_attempts,
        next_run_at=job.next_run_at,
        last_error=job.last_error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
