import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobEmbedding(Base):
    __tablename__ = "job_embeddings"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, index=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class JobAlert(Base):
    __tablename__ = "job_alerts"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    locations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    providers: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    remote_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    min_match_score: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class JobAlertMatch(Base):
    __tablename__ = "job_alert_matches"
    __table_args__ = (UniqueConstraint("alert_id", "job_id", name="uq_job_alert_match"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    alert_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_alerts.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(100), nullable=False)
    notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class RecruiterEmailEvent(Base):
    __tablename__ = "recruiter_email_events"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    provider_message_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    thread_id: Mapped[str | None] = mapped_column(String(255))
    sender: Mapped[str] = mapped_column(String(500), nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True)
    company: Mapped[str | None] = mapped_column(String(255))
    role_title: Mapped[str | None] = mapped_column(String(255))
    application_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"), index=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InterviewPreparation(Base):
    __tablename__ = "interview_preparations"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    company_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    role_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    technical_questions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    behavioral_questions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    coding_topics: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    system_design_topics: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    candidate_talking_points: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    questions_to_ask: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    ai_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
