import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.candidate import CandidateCreate, CandidateRead, CandidateUpdate
from app.services import candidate_service

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post("", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    payload: CandidateCreate, db: AsyncSession = Depends(get_db)
) -> CandidateRead:
    return await candidate_service.create_candidate(db, payload)


@router.get("", response_model=list[CandidateRead])
async def list_candidates(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[CandidateRead]:
    return await candidate_service.list_candidates(db, skip, limit)


@router.get("/{candidate_id}", response_model=CandidateRead)
async def get_candidate(candidate_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> CandidateRead:
    return await candidate_service.get_candidate(db, candidate_id)


@router.patch("/{candidate_id}", response_model=CandidateRead)
async def update_candidate(
    candidate_id: uuid.UUID,
    payload: CandidateUpdate,
    db: AsyncSession = Depends(get_db),
) -> CandidateRead:
    return await candidate_service.update_candidate(db, candidate_id, payload)


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate(
    candidate_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> Response:
    await candidate_service.delete_candidate(db, candidate_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
