from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class JobSearchQuery:
    keywords: list[str]
    locations: list[str]
    remote_only: bool = False
    page: int = 1


@dataclass(slots=True)
class ExternalJob:
    external_id: str
    source: str
    title: str
    company: str
    description: str
    source_url: str | None = None
    location: str | None = None


class JobProvider(ABC):
    """Common interface for permitted job data sources."""

    @abstractmethod
    async def search_jobs(self, query: JobSearchQuery) -> list[ExternalJob]:
        raise NotImplementedError

    @abstractmethod
    async def get_job(self, external_id: str) -> ExternalJob:
        raise NotImplementedError
