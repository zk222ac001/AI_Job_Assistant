import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.phase3 import InterviewPreparationRead, InterviewPrepareRequest
from app.services.interview_service import list_interview_preparations, prepare_interview
router = APIRouter(prefix="/interviews", tags=["interviews"])
@router.post("/prepare", response_model=InterviewPreparationRead, status_code=status.HTTP_201_CREATED)
async def prepare(payload: InterviewPrepareRequest, db: AsyncSession = Depends(get_db)) -> InterviewPreparationRead: return await prepare_interview(db, candidate_id=payload.candidate_id, job_id=payload.job_id, use_ai=payload.use_ai)
@router.get("/{candidate_id}", response_model=list[InterviewPreparationRead])
async def list_preparations(candidate_id: uuid.UUID, limit: int = Query(default=50, ge=1, le=100), db: AsyncSession = Depends(get_db)) -> list[InterviewPreparationRead]: return await list_interview_preparations(db, candidate_id, limit)
