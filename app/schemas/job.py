import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import RemoteStatus


class JobBase(BaseModel):
    external_id: str | None = Field(default=None, max_length=255)
    source: str = Field(default="manual", min_length=1, max_length=100)
    source_url: str | None = None
    company: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, max_length=100)
    remote_status: RemoteStatus = RemoteStatus.UNSPECIFIED
    description: str = Field(min_length=1)
    responsibilities: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=10)
    employment_type: str | None = Field(default=None, max_length=100)
    posted_date: date | None = None
    closing_date: date | None = None
    application_url: str | None = None

    @model_validator(mode="after")
    def validate_salary_range(self) -> "JobBase":
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValueError("salary_min cannot be greater than salary_max")
        return self


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    external_id: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, min_length=1, max_length=100)
    source_url: str | None = None
    company: str | None = Field(default=None, min_length=1, max_length=255)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, max_length=100)
    remote_status: RemoteStatus | None = None
    description: str | None = Field(default=None, min_length=1)
    responsibilities: list[str] | None = None
    required_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=10)
    employment_type: str | None = Field(default=None, max_length=100)
    posted_date: date | None = None
    closing_date: date | None = None
    application_url: str | None = None


class JobRead(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
