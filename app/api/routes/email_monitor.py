from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.phase3 import EmailSyncRequest, RecruiterEmailEventRead, TaskAccepted
from app.services.email_monitor_service import list_email_events, sync_recruiter_email
from app.workers.tasks import sync_recruiter_email_task
router = APIRouter(prefix="/email-monitor", tags=["email-monitor"])
@router.post("/sync", response_model=list[RecruiterEmailEventRead])
async def sync_email(payload: EmailSyncRequest, db: AsyncSession = Depends(get_db)) -> list[RecruiterEmailEventRead]: return await sync_recruiter_email(db, payload.max_messages)
@router.post("/sync-background", response_model=TaskAccepted, status_code=status.HTTP_202_ACCEPTED)
async def sync_email_background() -> TaskAccepted: task = sync_recruiter_email_task.delay(); return TaskAccepted(task_id=task.id)
@router.get("/events", response_model=list[RecruiterEmailEventRead])
async def email_events(limit: int = Query(default=100, ge=1, le=500), db: AsyncSession = Depends(get_db)) -> list[RecruiterEmailEventRead]: return await list_email_events(db, limit)
