import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.phase3 import JobAlert, JobAlertMatch
from app.models.resume import Resume
from app.schemas.phase3 import DiscoveryRequest, JobAlertCreate, JobAlertUpdate
from app.services import candidate_service
from app.services.discovery_service import discover_jobs
from app.services.matching_service import match_candidate_to_job

async def create_alert(db: AsyncSession, payload: JobAlertCreate) -> JobAlert:
    await candidate_service.get_candidate(db, payload.candidate_id)
    alert = JobAlert(**payload.model_dump()); db.add(alert); await db.commit(); await db.refresh(alert); return alert

async def list_alerts(db: AsyncSession, candidate_id: uuid.UUID | None = None) -> list[JobAlert]:
    statement = select(JobAlert).order_by(JobAlert.created_at.desc())
    if candidate_id: statement = statement.where(JobAlert.candidate_id == candidate_id)
    return list((await db.execute(statement)).scalars().all())

async def get_alert(db: AsyncSession, alert_id: uuid.UUID) -> JobAlert:
    alert = await db.get(JobAlert, alert_id)
    if alert is None: raise ValueError("Job alert not found")
    return alert

async def update_alert(db: AsyncSession, alert_id: uuid.UUID, payload: JobAlertUpdate) -> JobAlert:
    alert = await get_alert(db, alert_id)
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(alert, key, value)
    await db.commit(); await db.refresh(alert); return alert

async def delete_alert(db: AsyncSession, alert_id: uuid.UUID) -> None:
    alert = await get_alert(db, alert_id); await db.delete(alert); await db.commit()

async def run_alert(db: AsyncSession, alert_id: uuid.UUID) -> list[JobAlertMatch]:
    alert = await get_alert(db, alert_id)
    discovery = await discover_jobs(db, DiscoveryRequest(keywords=alert.keywords, locations=alert.locations, providers=alert.providers, remote_only=alert.remote_only, limit_per_provider=25))
    latest_resume = (await db.execute(select(Resume).where(Resume.candidate_id == alert.candidate_id).order_by(Resume.created_at.desc()).limit(1))).scalar_one_or_none()
    new_matches = []
    for job_id in discovery.job_ids:
        exists = (await db.execute(select(JobAlertMatch).where(JobAlertMatch.alert_id == alert.id, JobAlertMatch.job_id == job_id))).scalar_one_or_none()
        if exists is not None: continue
        match = await match_candidate_to_job(db, candidate_id=alert.candidate_id, job_id=job_id, resume_id=latest_resume.id if latest_resume else None, use_ai=False, persist=True)
        if match.overall_score >= alert.min_match_score:
            record = JobAlertMatch(alert_id=alert.id, job_id=job_id, match_score=match.overall_score, recommendation=match.recommendation)
            db.add(record); new_matches.append(record)
    alert.last_run_at = datetime.now(timezone.utc); await db.commit()
    for record in new_matches: await db.refresh(record)
    return new_matches

async def list_alert_matches(db: AsyncSession, alert_id: uuid.UUID) -> list[JobAlertMatch]:
    await get_alert(db, alert_id)
    return list((await db.execute(select(JobAlertMatch).where(JobAlertMatch.alert_id == alert_id).order_by(JobAlertMatch.created_at.desc()))).scalars().all())
