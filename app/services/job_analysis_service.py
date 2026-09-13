import logging
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.factory import get_llm_provider
from app.ai.text_utils import extract_known_skills, unique_skills
from app.models.job import JobPosting
from app.schemas.analysis import JobRequirements
from app.services import job_service

logger = logging.getLogger(__name__)


def heuristic_job_requirements(job: JobPosting) -> JobRequirements:
    text = f"{job.title}\n{job.description}\n" + "\n".join(job.responsibilities)
    discovered = extract_known_skills(text)
    required = unique_skills([*job.required_skills, *discovered])
    preferred = unique_skills(job.preferred_skills)
    years = [
        float(value)
        for value in re.findall(
            r"(?:at least|min(?:imum)?\s*)?(\d{1,2}(?:\.\d)?)\+?\s+years?",
            text,
            re.I,
        )
    ]
    return JobRequirements(
        title=job.title,
        required_skills=required,
        preferred_skills=preferred,
        responsibilities=job.responsibilities,
        min_years_experience=max(years) if years else None,
        keywords=unique_skills([*required, *preferred]),
    )


async def analyze_job(
    db: AsyncSession,
    job_id: uuid.UUID,
    *,
    use_ai: bool,
    persist: bool,
) -> tuple[JobRequirements, bool]:
    job = await job_service.get_job(db, job_id)
    baseline = heuristic_job_requirements(job)
    requirements = baseline
    ai_used = False

    provider = get_llm_provider() if use_ai else None
    if provider is not None:
        system_prompt = (
            "Extract job requirements using only the supplied posting. Separate mandatory "
            "requirements from preferred requirements and do not invent requirements."
        )
        prompt = (
            f"Job title: {job.title}\nCompany: {job.company}\n\n"
            f"Job description:\n{job.description[:30000]}"
        )
        try:
            extracted = await provider.structured_output(
                prompt, JobRequirements, system_prompt=system_prompt
            )
            extracted.required_skills = unique_skills(
                [*baseline.required_skills, *extracted.required_skills]
            )
            extracted.preferred_skills = unique_skills(
                [*baseline.preferred_skills, *extracted.preferred_skills]
            )
            extracted.keywords = unique_skills(
                [*extracted.keywords, *extracted.required_skills, *extracted.preferred_skills]
            )
            if extracted.title is None:
                extracted.title = job.title
            if not extracted.responsibilities:
                extracted.responsibilities = baseline.responsibilities
            requirements = extracted
            ai_used = True
        except Exception:
            logger.exception("LLM job analysis failed; using deterministic requirements")

    if persist:
        job.required_skills = requirements.required_skills
        job.preferred_skills = requirements.preferred_skills
        if requirements.responsibilities:
            job.responsibilities = requirements.responsibilities
        await db.commit()
        await db.refresh(job)

    return requirements, ai_used
