import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.integrations.gmail import GmailMonitor, GmailMessage
from app.models.application import Application
from app.models.enums import ApplicationStatus
from app.models.job import JobPosting
from app.models.phase3 import RecruiterEmailEvent

CATEGORY_RULES = [("OFFER", ("job offer", "offer letter", "pleased to offer", "offer of employment")), ("INTERVIEW", ("interview", "schedule a call", "meet the team", "interview invitation")), ("ASSESSMENT", ("assessment", "coding challenge", "technical test", "take-home")), ("REJECTION", ("unfortunately", "not moving forward", "other candidates", "regret to inform")), ("APPLICATION_CONFIRMATION", ("application received", "thank you for applying", "application submitted")), ("RECRUITER", ("recruiter", "opportunity", "your profile", "position available"))]

def classify_message(message: GmailMessage) -> str:
    text = f"{message.subject} {message.snippet}".lower()
    for category, phrases in CATEGORY_RULES:
        if any(phrase in text for phrase in phrases): return category
    return "OTHER"

async def _match_application(db: AsyncSession, message: GmailMessage) -> tuple[Application | None, JobPosting | None]:
    text = re.sub(r"\s+", " ", f"{message.subject} {message.snippet}").lower()
    rows = await db.execute(select(Application, JobPosting).join(JobPosting, JobPosting.id == Application.job_id))
    best = None; best_score = 0
    for application, job in rows.all():
        score = 2 if job.company.lower() in text else 0
        score += sum(1 for term in re.findall(r"[a-z0-9+#.]+", job.title.lower()) if len(term) > 2 and term in text)
        if score > best_score: best_score = score; best = (application, job)
    return best if best_score >= 2 and best else (None, None)

async def sync_recruiter_email(db: AsyncSession, max_messages: int = 25) -> list[RecruiterEmailEvent]:
    messages = await GmailMonitor().fetch_recent(max_messages); new_events = []
    for message in messages:
        exists = (await db.execute(select(RecruiterEmailEvent).where(RecruiterEmailEvent.provider_message_id == message.message_id))).scalar_one_or_none()
        if exists: continue
        category = classify_message(message); application, job = await _match_application(db, message)
        if application is not None:
            if category == "INTERVIEW": application.status = ApplicationStatus.INTERVIEW
            elif category == "REJECTION": application.status = ApplicationStatus.REJECTED
            elif category == "OFFER": application.status = ApplicationStatus.OFFER
        event = RecruiterEmailEvent(provider_message_id=message.message_id, thread_id=message.thread_id, sender=message.sender, subject=message.subject, snippet=message.snippet, category=category, company=job.company if job else None, role_title=job.title if job else None, application_id=application.id if application else None, received_at=message.received_at)
        db.add(event); new_events.append(event)
    await db.commit()
    for event in new_events: await db.refresh(event)
    return new_events

async def list_email_events(db: AsyncSession, limit: int = 100) -> list[RecruiterEmailEvent]:
    return list((await db.execute(select(RecruiterEmailEvent).order_by(RecruiterEmailEvent.processed_at.desc()).limit(limit))).scalars().all())
