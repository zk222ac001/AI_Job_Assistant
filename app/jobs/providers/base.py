from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass(slots=True)
class JobSearchQuery:
    keywords: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    remote_only: bool = False
    page: int = 1
    limit: int = 25


@dataclass(slots=True)
class ExternalJob:
    external_id: str
    source: str
    title: str
    company: str
    description: str
    source_url: str | None = None
    application_url: str | None = None
    location: str | None = None
    country: str | None = None
    remote: bool = False
    employment_type: str | None = None
    posted_date: date | None = None
    tags: list[str] = field(default_factory=list)


class JobProvider(ABC):
    """Common interface for permitted job data sources."""

    @abstractmethod
    async def search_jobs(self, query: JobSearchQuery) -> list[ExternalJob]:
        raise NotImplementedError

    @abstractmethod
    async def get_job(self, external_id: str) -> ExternalJob:
        raise NotImplementedError
