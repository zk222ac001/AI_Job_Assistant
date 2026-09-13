import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.job import JobPosting
from app.schemas.job import JobCreate, JobUpdate


async def create_job(db: AsyncSession, payload: JobCreate) -> JobPosting:
    job = JobPosting(**payload.model_dump())
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def list_jobs(db: AsyncSession, skip: int, limit: int) -> list[JobPosting]:
    result = await db.execute(select(JobPosting).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_job(db: AsyncSession, job_id: uuid.UUID) -> JobPosting:
    job = await db.get(JobPosting, job_id)
    if job is None:
        raise NotFoundError("Job not found")
    return job


async def update_job(db: AsyncSession, job_id: uuid.UUID, payload: JobUpdate) -> JobPosting:
    job = await get_job(db, job_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(job, field, value)
    await db.commit()
    await db.refresh(job)
    return job


async def delete_job(db: AsyncSession, job_id: uuid.UUID) -> None:
    job = await get_job(db, job_id)
    await db.delete(job)
    await db.commit()
