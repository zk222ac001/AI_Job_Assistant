import uuid
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.job import JobPosting
from app.schemas.phase3 import DiscoveryRequest, DiscoveryResult, SemanticJobResult, SemanticSearchRequest
from app.services.discovery_service import discover_jobs
from app.services.embedding_service import embed_job, semantic_search
from app.workers.celery_app import celery_app
router = APIRouter(prefix="/discovery", tags=["discovery"])
@router.post("/search", response_model=DiscoveryResult)
async def search_jobs(payload: DiscoveryRequest, db: AsyncSession = Depends(get_db)) -> DiscoveryResult: return await discover_jobs(db, payload)
@router.post("/jobs/{job_id}/embed", status_code=status.HTTP_202_ACCEPTED)
async def create_job_embedding(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    job = await db.get(JobPosting, job_id)
    if job is None: return {"embedded": False, "detail": "Job not found"}
    embedding = await embed_job(db, job); return {"embedded": embedding is not None, "job_id": str(job_id)}
@router.post("/semantic-search", response_model=list[SemanticJobResult])
async def search_semantically(payload: SemanticSearchRequest, db: AsyncSession = Depends(get_db)) -> list[SemanticJobResult]: return await semantic_search(db, payload.query, payload.limit)
@router.get("/tasks/{task_id}")
async def task_status(task_id: str) -> dict[str, object]:
    result = AsyncResult(task_id, app=celery_app); return {"task_id": task_id, "state": result.state, "result": result.result if result.ready() else None}
