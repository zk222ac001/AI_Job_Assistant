import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class DiscoveryRequest(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    providers: list[str] = Field(default_factory=list)
    remote_only: bool = False
    limit_per_provider: int = Field(default=25, ge=1, le=100)

class DiscoveryResult(BaseModel):
    providers: list[str]; fetched: int; created: int; updated: int; job_ids: list[uuid.UUID]

class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=4000)
    limit: int = Field(default=20, ge=1, le=100)

class SemanticJobResult(BaseModel):
    job_id: uuid.UUID; title: str; company: str; source: str; source_url: str | None; similarity: float

class JobAlertCreate(BaseModel):
    candidate_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    keywords: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    providers: list[str] = Field(default_factory=list)
    remote_only: bool = False
    min_match_score: float = Field(default=70.0, ge=0, le=100)
    active: bool = True

class JobAlertUpdate(BaseModel):
    name: str | None = None; keywords: list[str] | None = None; locations: list[str] | None = None
    providers: list[str] | None = None; remote_only: bool | None = None
    min_match_score: float | None = Field(default=None, ge=0, le=100); active: bool | None = None

class JobAlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; candidate_id: uuid.UUID; name: str; keywords: list[str]; locations: list[str]
    providers: list[str]; remote_only: bool; min_match_score: float; active: bool
    last_run_at: datetime | None; created_at: datetime; updated_at: datetime

class JobAlertMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; alert_id: uuid.UUID; job_id: uuid.UUID; match_score: float
    recommendation: str; notified: bool; created_at: datetime

class EmailSyncRequest(BaseModel):
    max_messages: int = Field(default=25, ge=1, le=100)

class RecruiterEmailEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; provider_message_id: str; thread_id: str | None; sender: str; subject: str
    snippet: str; category: str; company: str | None; role_title: str | None
    application_id: uuid.UUID | None; received_at: datetime | None; processed_at: datetime

class InterviewPrepareRequest(BaseModel):
    candidate_id: uuid.UUID; job_id: uuid.UUID; use_ai: bool = True

class InterviewAIOutput(BaseModel):
    company_summary: str; role_summary: str
    technical_questions: list[str] = Field(default_factory=list)
    behavioral_questions: list[str] = Field(default_factory=list)
    coding_topics: list[str] = Field(default_factory=list)
    system_design_topics: list[str] = Field(default_factory=list)
    candidate_talking_points: list[str] = Field(default_factory=list)
    questions_to_ask: list[str] = Field(default_factory=list)

class InterviewPreparationRead(InterviewAIOutput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; candidate_id: uuid.UUID; job_id: uuid.UUID; ai_used: bool; created_at: datetime

class TaskAccepted(BaseModel):
    task_id: str; status: str = "queued"
