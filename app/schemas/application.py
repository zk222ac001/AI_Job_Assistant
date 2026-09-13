import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ApplicationStatus


class ApplicationCreate(BaseModel):
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    match_score: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    match_score: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    applied_at: datetime | None = None


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    status: ApplicationStatus
    match_score: float | None
    notes: str | None
    applied_at: datetime | None
    created_at: datetime
    updated_at: datetime
