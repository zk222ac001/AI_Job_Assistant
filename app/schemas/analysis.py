import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobRequirements(BaseModel):
    title: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    min_years_experience: float | None = Field(default=None, ge=0, le=80)
    education_requirements: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class JobAnalysisResponse(BaseModel):
    job_id: uuid.UUID
    requirements: JobRequirements
    ai_used: bool
    persisted: bool


class MatchRequest(BaseModel):
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    resume_id: uuid.UUID | None = None
    use_ai: bool = True
    persist: bool = True


class MatchResult(BaseModel):
    overall_score: float = Field(ge=0, le=100)
    skill_score: float = Field(ge=0, le=100)
    experience_score: float = Field(ge=0, le=100)
    role_score: float = Field(ge=0, le=100)
    location_score: float = Field(ge=0, le=100)
    semantic_score: float | None = Field(default=None, ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    matched_preferred_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    recommendation: str
    explanation: str
    ai_used: bool = False


class JobMatchRead(MatchResult):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    resume_id: uuid.UUID | None
    created_at: datetime


class TailorResumeRequest(BaseModel):
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    resume_id: uuid.UUID
    use_ai: bool = True


class TailoredResume(BaseModel):
    professional_summary: str
    prioritized_skills: list[str] = Field(default_factory=list)
    experience_emphasis: list[str] = Field(default_factory=list)
    ats_keywords: list[str] = Field(default_factory=list)
    verification_required: list[str] = Field(default_factory=list)
    ai_used: bool = False


class CoverLetterRequest(BaseModel):
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    resume_id: uuid.UUID | None = None
    tone: str = Field(default="professional", max_length=50)
    use_ai: bool = True


class CoverLetterResponse(BaseModel):
    content: str
    facts_used: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    ai_used: bool = False
