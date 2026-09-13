import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.resume import ResumeRead
from app.services import resume_service

router = APIRouter(tags=["resumes"])


@router.post(
    "/candidates/{candidate_id}/resumes",
    response_model=ResumeRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    candidate_id: uuid.UUID,
    file: UploadFile = File(...),
    use_ai: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
) -> ResumeRead:
    data = await file.read()
    try:
        resume = await resume_service.create_resume(
            db,
            candidate_id=candidate_id,
            filename=file.filename or "resume",
            content_type=file.content_type or "application/octet-stream",
            data=data,
            use_ai=use_ai,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ResumeRead.model_validate(resume)


@router.get("/candidates/{candidate_id}/resumes", response_model=list[ResumeRead])
async def list_resumes(
    candidate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ResumeRead]:
    resumes = await resume_service.list_candidate_resumes(db, candidate_id)
    return [ResumeRead.model_validate(resume) for resume in resumes]


@router.get("/resumes/{resume_id}", response_model=ResumeRead)
async def get_resume(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ResumeRead:
    return ResumeRead.model_validate(await resume_service.get_resume(db, resume_id))


@router.delete("/resumes/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Response:
    await resume_service.delete_resume(db, resume_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
