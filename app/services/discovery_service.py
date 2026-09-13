import html
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.providers import JobSearchQuery, configured_job_providers, get_job_provider
from app.models.enums import RemoteStatus
from app.models.job import JobPosting
from app.schemas.phase3 import DiscoveryRequest, DiscoveryResult


def _plain_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


async def discover_jobs(db: AsyncSession, payload: DiscoveryRequest) -> DiscoveryResult:
    providers = payload.providers or configured_job_providers()
    fetched = created = updated = 0
    job_ids = []
    for provider_name in providers:
        provider = get_job_provider(provider_name)
        external_jobs = await provider.search_jobs(JobSearchQuery(
            keywords=payload.keywords, locations=payload.locations,
            remote_only=payload.remote_only, limit=payload.limit_per_provider,
        ))
        fetched += len(external_jobs)
        for external in external_jobs:
            job = (await db.execute(select(JobPosting).where(
                JobPosting.source == external.source,
                JobPosting.external_id == external.external_id,
            ))).scalar_one_or_none()
            fields = {
                "source_url": external.source_url, "company": external.company, "title": external.title,
                "location": external.location, "country": external.country,
                "remote_status": RemoteStatus.REMOTE if external.remote else RemoteStatus.UNSPECIFIED,
                "description": _plain_text(external.description), "preferred_skills": external.tags,
                "employment_type": external.employment_type, "posted_date": external.posted_date,
                "application_url": external.application_url or external.source_url,
            }
            if job is None:
                job = JobPosting(external_id=external.external_id, source=external.source,
                                 required_skills=[], responsibilities=[], **fields)
                db.add(job); await db.flush(); created += 1
            else:
                for key, value in fields.items(): setattr(job, key, value)
                updated += 1
            job_ids.append(job.id)
    await db.commit()
    return DiscoveryResult(providers=providers, fetched=fetched, created=created, updated=updated, job_ids=job_ids)
