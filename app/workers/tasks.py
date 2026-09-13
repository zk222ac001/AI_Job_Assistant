import asyncio
import uuid
from sqlalchemy import select
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.phase3 import JobAlert
from app.schemas.phase3 import DiscoveryRequest
from app.services.alert_service import run_alert
from app.services.discovery_service import discover_jobs
from app.services.email_monitor_service import sync_recruiter_email
from app.services.embedding_service import embed_jobs
from app.workers.celery_app import celery_app

async def _discover_default_jobs() -> int:
    async with AsyncSessionLocal() as db:
        result = await discover_jobs(db, DiscoveryRequest(limit_per_provider=50))
        if get_settings().llm_provider != "none": await embed_jobs(db, result.job_ids)
        return result.created + result.updated
@celery_app.task(name="phase3.discover_default_jobs")
def discover_default_jobs_task() -> int: return asyncio.run(_discover_default_jobs())
async def _run_alert(alert_id: uuid.UUID) -> int:
    async with AsyncSessionLocal() as db: return len(await run_alert(db, alert_id))
@celery_app.task(name="phase3.run_alert")
def run_alert_task(alert_id: str) -> int: return asyncio.run(_run_alert(uuid.UUID(alert_id)))
async def _run_all_alerts() -> int:
    async with AsyncSessionLocal() as db: ids = list((await db.execute(select(JobAlert.id).where(JobAlert.active.is_(True)))).scalars().all())
    total = 0
    for alert_id in ids: total += await _run_alert(alert_id)
    return total
@celery_app.task(name="phase3.run_all_alerts")
def run_all_alerts_task() -> int: return asyncio.run(_run_all_alerts())
async def _sync_email() -> int:
    if not get_settings().gmail_access_token: return 0
    async with AsyncSessionLocal() as db: return len(await sync_recruiter_email(db))
@celery_app.task(name="phase3.sync_recruiter_email")
def sync_recruiter_email_task() -> int: return asyncio.run(_sync_email())
