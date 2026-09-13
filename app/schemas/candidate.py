import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CandidateBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=200)
    current_title: str | None = Field(default=None, max_length=200)
    professional_summary: str | None = None
    years_experience: float = Field(default=0.0, ge=0, le=80)
    target_roles: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    preferred_technologies: list[str] = Field(default_factory=list)
    work_authorization: str | None = Field(default=None, max_length=200)


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=200)
    current_title: str | None = Field(default=None, max_length=200)
    professional_summary: str | None = None
    years_experience: float | None = Field(default=None, ge=0, le=80)
    target_roles: list[str] | None = None
    skills: list[str] | None = None
    preferred_locations: list[str] | None = None
    preferred_technologies: list[str] | None = None
    work_authorization: str | None = Field(default=None, max_length=200)


class CandidateRead(CandidateBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
