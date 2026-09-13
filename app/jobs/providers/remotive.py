from datetime import datetime
import re

import httpx

from app.jobs.providers.base import ExternalJob, JobProvider, JobSearchQuery


class RemotiveJobProvider(JobProvider):
    """Remotive public API provider. Keep source attribution and links intact."""

    name = "remotive"
    base_url = "https://remotive.com/api/remote-jobs"

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    async def search_jobs(self, query: JobSearchQuery) -> list[ExternalJob]:
        params: dict[str, str | int] = {"limit": query.limit}
        if query.keywords:
            params["search"] = " ".join(query.keywords)
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            payload = response.json()
        jobs = [self._convert(item) for item in payload.get("jobs", [])]
        return [job for job in jobs if self._matches(job, query)][: query.limit]

    async def get_job(self, external_id: str) -> ExternalJob:
        jobs = await self.search_jobs(JobSearchQuery(limit=100))
        for job in jobs:
            if job.external_id == external_id:
                return job
        raise LookupError(f"Remotive job {external_id} not found")

    @staticmethod
    def _convert(item: dict[str, object]) -> ExternalJob:
        publication = str(item.get("publication_date") or "")
        posted_date = None
        if publication:
            try:
                posted_date = datetime.fromisoformat(publication.replace("Z", "+00:00")).date()
            except ValueError:
                posted_date = None
        url = str(item.get("url") or "") or None
        return ExternalJob(
            external_id=str(item.get("id")), source="remotive",
            title=str(item.get("title") or "Untitled role"),
            company=str(item.get("company_name") or "Unknown company"),
            description=str(item.get("description") or ""), source_url=url, application_url=url,
            location=str(item.get("candidate_required_location") or "Remote"), remote=True,
            employment_type=str(item.get("job_type") or "") or None, posted_date=posted_date,
            tags=[str(item.get("category"))] if item.get("category") else [],
        )

    @staticmethod
    def _matches(job: ExternalJob, query: JobSearchQuery) -> bool:
        haystack = f"{job.title} {job.company} {job.description}".lower()
        if query.keywords and not all(keyword.lower() in haystack for keyword in query.keywords):
            return False
        if query.locations:
            location = (job.location or "").lower()
            if not any(re.search(re.escape(value.lower()), location) for value in query.locations):
                return False
        return True
