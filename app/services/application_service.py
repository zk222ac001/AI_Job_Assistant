import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.application import Application
from app.models.candidate import CandidateProfile
from app.models.job import JobPosting
from app.schemas.application import ApplicationCreate, ApplicationUpdate


async def create_application(db: AsyncSession, payload: ApplicationCreate) -> Application:
    if await db.get(CandidateProfile, payload.candidate_id) is None:
        raise NotFoundError("Candidate not found")
    if await db.get(JobPosting, payload.job_id) is None:
        raise NotFoundError("Job not found")

    application = Application(**payload.model_dump())
    db.add(application)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError("Application already exists for this candidate and job") from exc
    await db.refresh(application)
    return application


async def list_applications(db: AsyncSession, skip: int, limit: int) -> list[Application]:
    result = await db.execute(select(Application).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_application(db: AsyncSession, application_id: uuid.UUID) -> Application:
    application = await db.get(Application, application_id)
    if application is None:
        raise NotFoundError("Application not found")
    return application


async def update_application(
    db: AsyncSession, application_id: uuid.UUID, payload: ApplicationUpdate
) -> Application:
    application = await get_application(db, application_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(application, field, value)
    await db.commit()
    await db.refresh(application)
    return application


async def delete_application(db: AsyncSession, application_id: uuid.UUID) -> None:
    application = await get_application(db, application_id)
    await db.delete(application)
    await db.commit()
