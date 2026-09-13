import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.factory import get_llm_provider
from app.ai.text_utils import unique_skills
from app.schemas.analysis import CoverLetterResponse, TailoredResume
from app.schemas.resume import ResumeStructuredProfile
from app.services import candidate_service, job_service, resume_service
from app.services.job_analysis_service import heuristic_job_requirements

logger = logging.getLogger(__name__)


async def tailor_resume(
    db: AsyncSession,
    *,
    candidate_id: uuid.UUID,
    job_id: uuid.UUID,
    resume_id: uuid.UUID,
    use_ai: bool,
) -> TailoredResume:
    candidate = await candidate_service.get_candidate(db, candidate_id)
    job = await job_service.get_job(db, job_id)
    resume = await resume_service.get_resume(db, resume_id)
    if resume.candidate_id != candidate_id:
        raise ValueError("Resume does not belong to the selected candidate")

    profile = ResumeStructuredProfile.model_validate(resume.structured_data)
    requirements = heuristic_job_requirements(job)
    candidate_skills = unique_skills([*candidate.skills, *profile.skills])
    matched = [skill for skill in requirements.required_skills if skill in candidate_skills]
    warnings = [
        f"Do not add {skill} unless the candidate confirms this skill."
        for skill in requirements.required_skills
        if skill not in candidate_skills
    ]
    summary = candidate.professional_summary or profile.professional_summary or (
        f"{candidate.current_title or 'Candidate'} with "
        f"{candidate.years_experience:g} years of experience."
    )
    baseline = TailoredResume(
        professional_summary=summary,
        prioritized_skills=matched,
        experience_emphasis=[],
        ats_keywords=requirements.keywords,
        verification_required=warnings,
        ai_used=False,
    )

    provider = get_llm_provider() if use_ai else None
    if provider is None:
        return baseline

    system_prompt = (
        "Tailor resumes using only verified candidate facts. Never invent employers, skills, "
        "degrees, certifications, projects, dates, achievements, or metrics. Put uncertain "
        "suggestions in verification_required."
    )
    prompt = (
        f"Candidate title: {candidate.current_title}\n"
        f"Candidate years: {candidate.years_experience}\n"
        f"Verified skills: {candidate_skills}\n"
        f"Parsed resume: {profile.model_dump_json()}\n\n"
        f"Target job: {job.title} at {job.company}\n{job.description[:20000]}"
    )
    try:
        tailored = await provider.structured_output(
            prompt, TailoredResume, system_prompt=system_prompt
        )
        tailored.ai_used = True
        tailored.verification_required = list(
            dict.fromkeys([*tailored.verification_required, *warnings])
        )
        return tailored
    except Exception:
        logger.exception("LLM resume tailoring failed; returning deterministic plan")
        return baseline


async def generate_cover_letter(
    db: AsyncSession,
    *,
    candidate_id: uuid.UUID,
    job_id: uuid.UUID,
    resume_id: uuid.UUID | None,
    tone: str,
    use_ai: bool,
) -> CoverLetterResponse:
    candidate = await candidate_service.get_candidate(db, candidate_id)
    job = await job_service.get_job(db, job_id)
    profile: ResumeStructuredProfile | None = None
    if resume_id:
        resume = await resume_service.get_resume(db, resume_id)
        if resume.candidate_id != candidate_id:
            raise ValueError("Resume does not belong to the selected candidate")
        profile = ResumeStructuredProfile.model_validate(resume.structured_data)

    skills = unique_skills([*candidate.skills, *(profile.skills if profile else [])])
    requirements = heuristic_job_requirements(job)
    matched = [skill for skill in requirements.required_skills if skill in skills]
    facts = [
        f"Current title: {candidate.current_title}" if candidate.current_title else "",
        f"Years of experience: {candidate.years_experience:g}",
        f"Verified matching skills: {', '.join(matched)}" if matched else "",
    ]
    facts = [fact for fact in facts if fact]

    provider = get_llm_provider() if use_ai else None
    if provider is None:
        skill_sentence = f"My background includes {', '.join(matched[:6])}." if matched else ""
        content = (
            f"Dear Hiring Team,\n\nI am writing to apply for the {job.title} position at "
            f"{job.company}. {skill_sentence} I would welcome the opportunity to discuss how "
            f"my verified experience aligns with your needs.\n\nSincerely,\n{candidate.name}"
        )
        return CoverLetterResponse(
            content=content,
            facts_used=facts,
            warnings=["Generated without an LLM; review before use."],
            ai_used=False,
        )

    system_prompt = (
        "Write a factual cover letter using only supplied candidate facts. Do not invent "
        "employers, skills, achievements, education, certifications, metrics, or dates."
    )
    prompt = (
        f"Tone: {tone}\nCandidate: {candidate.name}\nCurrent title: {candidate.current_title}\n"
        f"Years experience: {candidate.years_experience}\nVerified skills: {skills}\n"
        f"Resume facts: {profile.model_dump_json() if profile else 'No resume selected'}\n\n"
        f"Job: {job.title} at {job.company}\n{job.description[:20000]}"
    )
    try:
        content = await provider.generate_text(prompt, system_prompt=system_prompt)
        return CoverLetterResponse(
            content=content,
            facts_used=facts,
            warnings=["Review the letter before submitting an application."],
            ai_used=True,
        )
    except Exception:
        logger.exception("LLM cover-letter generation failed; using fallback")
        return await generate_cover_letter(
            db,
            candidate_id=candidate_id,
            job_id=job_id,
            resume_id=resume_id,
            tone=tone,
            use_ai=False,
        )
