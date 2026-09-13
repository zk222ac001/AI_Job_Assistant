import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.candidate import CandidateProfile
from app.schemas.candidate import CandidateCreate, CandidateUpdate


async def create_candidate(db: AsyncSession, payload: CandidateCreate) -> CandidateProfile:
    candidate = CandidateProfile(**payload.model_dump())
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    return candidate


async def list_candidates(db: AsyncSession, skip: int, limit: int) -> list[CandidateProfile]:
    result = await db.execute(select(CandidateProfile).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_candidate(db: AsyncSession, candidate_id: uuid.UUID) -> CandidateProfile:
    candidate = await db.get(CandidateProfile, candidate_id)
    if candidate is None:
        raise NotFoundError("Candidate not found")
    return candidate


async def update_candidate(
    db: AsyncSession, candidate_id: uuid.UUID, payload: CandidateUpdate
) -> CandidateProfile:
    candidate = await get_candidate(db, candidate_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(candidate, field, value)
    await db.commit()
    await db.refresh(candidate)
    return candidate


async def delete_candidate(db: AsyncSession, candidate_id: uuid.UUID) -> None:
    candidate = await get_candidate(db, candidate_id)
    await db.delete(candidate)
    await db.commit()
