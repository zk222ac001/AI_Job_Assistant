from datetime import datetime
import re

import httpx

from app.jobs.providers.base import ExternalJob, JobProvider, JobSearchQuery


class ArbeitnowJobProvider(JobProvider):
    """Arbeitnow public job-board API provider."""

    name = "arbeitnow"
    base_url = "https://www.arbeitnow.com/api/job-board-api"

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    async def search_jobs(self, query: JobSearchQuery) -> list[ExternalJob]:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(self.base_url, params={"page": max(1, query.page)})
            response.raise_for_status()
            payload = response.json()
        jobs = [self._convert(item) for item in payload.get("data", [])]
        return [job for job in jobs if self._matches(job, query)][: query.limit]

    async def get_job(self, external_id: str) -> ExternalJob:
        for page in range(1, 6):
            jobs = await self.search_jobs(JobSearchQuery(page=page, limit=100))
            for job in jobs:
                if job.external_id == external_id:
                    return job
        raise LookupError(f"Arbeitnow job {external_id} not found")

    @staticmethod
    def _convert(item: dict[str, object]) -> ExternalJob:
        created = item.get("created_at")
        posted_date = None
        if created:
            try:
                if isinstance(created, (int, float)):
                    posted_date = datetime.fromtimestamp(created).date()
                else:
                    posted_date = datetime.fromisoformat(str(created).replace("Z", "+00:00")).date()
            except (ValueError, OSError, TypeError):
                posted_date = None
        url = str(item.get("url") or "") or None
        tags = [str(value) for value in (item.get("tags") or [])]
        job_types = [str(value) for value in (item.get("job_types") or [])]
        return ExternalJob(
            external_id=str(item.get("slug") or url or item.get("title")), source="arbeitnow",
            title=str(item.get("title") or "Untitled role"),
            company=str(item.get("company_name") or "Unknown company"),
            description=str(item.get("description") or ""), source_url=url, application_url=url,
            location=str(item.get("location") or "") or None, remote=bool(item.get("remote", False)),
            employment_type=", ".join(job_types) or None, posted_date=posted_date, tags=tags,
        )

    @staticmethod
    def _matches(job: ExternalJob, query: JobSearchQuery) -> bool:
        if query.remote_only and not job.remote:
            return False
        haystack = f"{job.title} {job.company} {job.description} {' '.join(job.tags)}".lower()
        if query.keywords and not all(keyword.lower() in haystack for keyword in query.keywords):
            return False
        if query.locations:
            location = (job.location or "").lower()
            if not any(re.search(re.escape(value.lower()), location) for value in query.locations):
                return False
        return True
