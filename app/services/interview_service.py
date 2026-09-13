import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.providers.factory import get_llm_provider
from app.models.candidate import CandidateProfile
from app.models.job import JobPosting
from app.models.phase3 import InterviewPreparation
from app.schemas.phase3 import InterviewAIOutput
from app.services import candidate_service, job_service

def _fallback(candidate: CandidateProfile, job: JobPosting) -> InterviewAIOutput:
    skills = job.required_skills or job.preferred_skills or candidate.skills
    return InterviewAIOutput(company_summary=f"Prepare to discuss {job.company}, its products, customers, and engineering context.", role_summary=f"{job.title}: focus on the responsibilities and requirements in the job description.", technical_questions=[f"Explain your experience with {skill}." for skill in skills[:6]] or ["Describe a technically difficult project you delivered."], behavioral_questions=["Tell me about a difficult problem you solved.", "Describe a disagreement with a teammate and how you handled it.", "Tell me about a time you had to learn a technology quickly.", "Describe a project that did not go as planned and what you changed."], coding_topics=skills[:5], system_design_topics=["API design", "scalability", "reliability", "observability"], candidate_talking_points=[f"Connect your verified experience to {job.title}.", "Use measurable outcomes only when they are present in your real experience.", "Prepare one STAR story for delivery, collaboration, and problem solving."], questions_to_ask=["What would success look like in the first 90 days?", "What are the most important technical challenges for this role?", "How does the team measure engineering quality?", "How is feedback and career development handled?"])

async def prepare_interview(db: AsyncSession, *, candidate_id: uuid.UUID, job_id: uuid.UUID, use_ai: bool) -> InterviewPreparation:
    candidate = await candidate_service.get_candidate(db, candidate_id); job = await job_service.get_job(db, job_id)
    content = _fallback(candidate, job); ai_used = False
    provider = get_llm_provider() if use_ai else None
    if provider is not None:
        prompt = f"""Create a factual interview preparation package. Do not invent candidate qualifications, employers, achievements, certifications, or metrics. Company facts not present in the job posting must be framed as research items.\nCANDIDATE\nTitle: {candidate.current_title or 'Not provided'}\nSummary: {candidate.professional_summary or 'Not provided'}\nSkills: {', '.join(candidate.skills)}\nYears experience: {candidate.years_experience}\nJOB\nCompany: {job.company}\nTitle: {job.title}\nRequired skills: {', '.join(job.required_skills)}\nPreferred skills: {', '.join(job.preferred_skills)}\nDescription: {job.description[:12000]}"""
        try:
            content = await provider.structured_output(prompt, InterviewAIOutput, system_prompt="You are a senior technical interview coach. Be accurate and practical."); ai_used = True
        except Exception: ai_used = False
    record = InterviewPreparation(candidate_id=candidate_id, job_id=job_id, ai_used=ai_used, **content.model_dump()); db.add(record); await db.commit(); await db.refresh(record); return record

async def list_interview_preparations(db: AsyncSession, candidate_id: uuid.UUID, limit: int = 50) -> list[InterviewPreparation]:
    await candidate_service.get_candidate(db, candidate_id)
    return list((await db.execute(select(InterviewPreparation).where(InterviewPreparation.candidate_id == candidate_id).order_by(InterviewPreparation.created_at.desc()).limit(limit))).scalars().all())
