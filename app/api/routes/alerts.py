import uuid
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.phase3 import JobAlertCreate, JobAlertMatchRead, JobAlertRead, JobAlertUpdate, TaskAccepted
from app.services import alert_service
from app.workers.tasks import run_alert_task
router = APIRouter(prefix="/alerts", tags=["alerts"])
@router.post("", response_model=JobAlertRead, status_code=status.HTTP_201_CREATED)
async def create_alert(payload: JobAlertCreate, db: AsyncSession = Depends(get_db)) -> JobAlertRead: return await alert_service.create_alert(db, payload)
@router.get("", response_model=list[JobAlertRead])
async def list_alerts(candidate_id: uuid.UUID | None = Query(default=None), db: AsyncSession = Depends(get_db)) -> list[JobAlertRead]: return await alert_service.list_alerts(db, candidate_id)
@router.patch("/{alert_id}", response_model=JobAlertRead)
async def update_alert(alert_id: uuid.UUID, payload: JobAlertUpdate, db: AsyncSession = Depends(get_db)) -> JobAlertRead: return await alert_service.update_alert(db, alert_id, payload)
@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Response: await alert_service.delete_alert(db, alert_id); return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{alert_id}/run", response_model=TaskAccepted, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> TaskAccepted: await alert_service.get_alert(db, alert_id); task = run_alert_task.delay(str(alert_id)); return TaskAccepted(task_id=task.id)
@router.get("/{alert_id}/matches", response_model=list[JobAlertMatchRead])
async def alert_matches(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[JobAlertMatchRead]: return await alert_service.list_alert_matches(db, alert_id)
