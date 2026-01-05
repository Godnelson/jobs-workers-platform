from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CreateJobRequest(BaseModel):
    task_name: str = Field(min_length=1, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=3, max_length=200)
    max_attempts: int = Field(default=3, ge=1, le=50)
    run_at: datetime | None = None  # optional delayed execution


class JobResponse(BaseModel):
    id: UUID
    status: str
    task_name: str
    payload: dict[str, Any]
    idempotency_key: str
    attempts: int
    max_attempts: int
    next_run_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
