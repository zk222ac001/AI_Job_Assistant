from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Job Assistant"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://jobassistant:jobassistant@db:5432/jobassistant"
    secret_key: str = Field(default="change-me-before-production", min_length=16)
    cors_origins: str = "http://localhost:3000,http://localhost:8501"

    llm_provider: Literal["none", "openai", "ollama"] = "none"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-luna"
    openai_embedding_model: str = "text-embedding-3-small"
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3.2"
    ollama_embedding_model: str = "nomic-embed-text"
    llm_timeout_seconds: float = Field(default=60.0, gt=0, le=300)
    embedding_dimension: int = Field(default=768, ge=1, le=4096)

    max_resume_size_mb: int = Field(default=10, ge=1, le=50)
    store_resume_files: bool = False
    resume_storage_path: str = "/tmp/ai-job-assistant/resumes"

    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    job_providers: str = "remotive,arbeitnow"
    job_provider_timeout_seconds: float = Field(default=30.0, gt=0, le=120)

    gmail_access_token: str | None = None
    gmail_user_id: str = "me"
    gmail_monitor_query: str = "newer_than:7d (interview OR recruiter OR application OR offer OR assessment)"
    email_provider_timeout_seconds: float = Field(default=30.0, gt=0, le=120)

    @field_validator("secret_key")
    @classmethod
    def reject_default_secret_in_production(cls, value: str, info):  # type: ignore[no-untyped-def]
        app_env = info.data.get("app_env", "development")
        if app_env == "production" and value == "change-me-before-production":
            raise ValueError("SECRET_KEY must be changed in production")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def job_provider_list(self) -> list[str]:
        return [provider.strip().lower() for provider in self.job_providers.split(",") if provider.strip()]

    @property
    def max_resume_size_bytes(self) -> int:
        return self.max_resume_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
