from app.core.config import get_settings
from app.jobs.providers.arbeitnow import ArbeitnowJobProvider
from app.jobs.providers.base import JobProvider
from app.jobs.providers.remotive import RemotiveJobProvider


def get_job_provider(name: str) -> JobProvider:
    settings = get_settings()
    normalized = name.strip().lower()
    if normalized == "remotive":
        return RemotiveJobProvider(timeout=settings.job_provider_timeout_seconds)
    if normalized == "arbeitnow":
        return ArbeitnowJobProvider(timeout=settings.job_provider_timeout_seconds)
    raise ValueError(f"Unsupported job provider: {name}")


def configured_job_providers() -> list[str]:
    return get_settings().job_provider_list
