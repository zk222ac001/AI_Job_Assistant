from functools import lru_cache

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
