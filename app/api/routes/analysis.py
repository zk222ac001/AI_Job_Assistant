import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.analysis import (
    CoverLetterRequest,
    CoverLetterResponse,
    JobAnalysisResponse,
    JobMatchRead,
    MatchRequest,
    MatchResult,
    TailoredResume,
    TailorResumeRequest,
)
from app.services import document_service, job_analysis_service, matching_service

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/jobs/{job_id}", response_model=JobAnalysisResponse)
async def analyze_job(
    job_id: uuid.UUID,
    use_ai: bool = Query(default=True),
    persist: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> JobAnalysisResponse:
    requirements, ai_used = await job_analysis_service.analyze_job(
        db, job_id, use_ai=use_ai, persist=persist
    )
    return JobAnalysisResponse(
        job_id=job_id,
        requirements=requirements,
        ai_used=ai_used,
        persisted=persist,
    )


@router.post("/match", response_model=MatchResult)
async def match_candidate(
    payload: MatchRequest,
    db: AsyncSession = Depends(get_db),
) -> MatchResult:
    try:
        return await matching_service.match_candidate_to_job(
            db,
            candidate_id=payload.candidate_id,
            job_id=payload.job_id,
            resume_id=payload.resume_id,
            use_ai=payload.use_ai,
            persist=payload.persist,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/matches/{candidate_id}", response_model=list[JobMatchRead])
async def list_matches(
    candidate_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[JobMatchRead]:
    matches = await matching_service.list_matches(db, candidate_id, limit=limit)
    return [JobMatchRead.model_validate(match) for match in matches]


@router.post("/tailor-resume", response_model=TailoredResume)
async def tailor_resume(
    payload: TailorResumeRequest,
    db: AsyncSession = Depends(get_db),
) -> TailoredResume:
    try:
        return await document_service.tailor_resume(
            db,
            candidate_id=payload.candidate_id,
            job_id=payload.job_id,
            resume_id=payload.resume_id,
            use_ai=payload.use_ai,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/cover-letter", response_model=CoverLetterResponse)
async def cover_letter(
    payload: CoverLetterRequest,
    db: AsyncSession = Depends(get_db),
) -> CoverLetterResponse:
    try:
        return await document_service.generate_cover_letter(
            db,
            candidate_id=payload.candidate_id,
            job_id=payload.job_id,
            resume_id=payload.resume_id,
            tone=payload.tone,
            use_ai=payload.use_ai,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
