import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class WorkExperience(BaseModel):
    employer: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    skills: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    graduation_date: str | None = None


class ProjectItem(BaseModel):
    name: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)


class ResumeStructuredProfile(BaseModel):
    """Facts extracted from a resume. Unknown values remain empty."""

    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    location: str | None = None
    current_title: str | None = None
    professional_summary: str | None = None
    years_experience: float | None = Field(default=None, ge=0, le=80)
    skills: list[str] = Field(default_factory=list)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class ResumeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    filename: str
    content_type: str
    file_size: int
    sha256: str
    structured_data: dict[str, object]
    parser_version: str
    storage_key: str | None
    created_at: datetime
