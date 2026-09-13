import logging
import math
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.factory import get_llm_provider
from app.ai.text_utils import normalize_skill, unique_skills
from app.models.candidate import CandidateProfile
from app.models.enums import RemoteStatus
from app.models.job import JobPosting
from app.models.resume import JobMatch, Resume
from app.schemas.analysis import JobRequirements, MatchResult
from app.schemas.resume import ResumeStructuredProfile
from app.services import candidate_service, job_service, resume_service
from app.services.job_analysis_service import analyze_job

logger = logging.getLogger(__name__)


def _token_similarity(left: str, right: str) -> float:
    left_tokens = set(re.findall(r"[a-z0-9+#.]+", left.lower()))
    right_tokens = set(re.findall(r"[a-z0-9+#.]+", right.lower()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(-1.0, min(1.0, dot / (left_norm * right_norm)))


def _recommendation(score: float) -> str:
    if score >= 85:
        return "Strong Match"
    if score >= 70:
        return "Good Match"
    if score >= 55:
        return "Possible Match"
    return "Weak Match"


def deterministic_match(
    candidate: CandidateProfile,
    job: JobPosting,
    requirements: JobRequirements,
    resume_profile: ResumeStructuredProfile | None = None,
) -> MatchResult:
    candidate_skills = unique_skills(
        [*candidate.skills, *(resume_profile.skills if resume_profile else [])]
    )
    candidate_skill_set = {normalize_skill(skill) for skill in candidate_skills}
    required = unique_skills(requirements.required_skills)
    preferred = unique_skills(requirements.preferred_skills)

    matched_required = [
        skill for skill in required if normalize_skill(skill) in candidate_skill_set
    ]
    missing_required = [
        skill for skill in required if normalize_skill(skill) not in candidate_skill_set
    ]
    matched_preferred = [
        skill for skill in preferred if normalize_skill(skill) in candidate_skill_set
    ]

    required_ratio = len(matched_required) / len(required) if required else 1.0
    preferred_ratio = len(matched_preferred) / len(preferred) if preferred else 1.0
    if required and preferred:
        skill_score = 100 * (0.85 * required_ratio + 0.15 * preferred_ratio)
    elif required:
        skill_score = 100 * required_ratio
    elif preferred:
        skill_score = 100 * preferred_ratio
    else:
        skill_score = 100.0

    candidate_years = candidate.years_experience
    if resume_profile and resume_profile.years_experience is not None:
        candidate_years = max(candidate_years, resume_profile.years_experience)
    if requirements.min_years_experience:
        experience_score = min(
            100.0,
            100 * candidate_years / requirements.min_years_experience,
        )
    else:
        experience_score = 100.0

    role_options = [candidate.current_title or "", *candidate.target_roles]
    role_score = max(
        (_token_similarity(role, job.title) * 100 for role in role_options),
        default=0.0,
    )
    if not any(role_options):
        role_score = 50.0

    if job.remote_status == RemoteStatus.REMOTE:
        location_score = 100.0
    else:
        locations = [candidate.location or "", *candidate.preferred_locations]
        target = " ".join(filter(None, [job.location, job.country]))
        best = max((_token_similarity(location, target) for location in locations), default=0.0)
        location_score = 100.0 if best >= 0.5 else (70.0 if best > 0 else 50.0)

    overall = (
        0.55 * skill_score
        + 0.20 * experience_score
        + 0.15 * role_score
        + 0.10 * location_score
    )
    strengths = [f"Matched required skill: {skill}" for skill in matched_required[:8]]
    gaps = [f"Missing required skill: {skill}" for skill in missing_required[:8]]
    explanation = (
        f"{_recommendation(overall)}. Matched {len(matched_required)} of {len(required)} "
        f"required skills. Skill score {skill_score:.1f}, experience {experience_score:.1f}, "
        f"role alignment {role_score:.1f}, location {location_score:.1f}."
    )
    return MatchResult(
        overall_score=round(overall, 1),
        skill_score=round(skill_score, 1),
        experience_score=round(experience_score, 1),
        role_score=round(role_score, 1),
        location_score=round(location_score, 1),
        matched_skills=matched_required,
        missing_required_skills=missing_required,
        matched_preferred_skills=matched_preferred,
        strengths=strengths,
        gaps=gaps,
        recommendation=_recommendation(overall),
        explanation=explanation,
        ai_used=False,
    )


async def _semantic_score(
    candidate: CandidateProfile,
    job: JobPosting,
    resume: Resume | None,
) -> float | None:
    provider = get_llm_provider()
    if provider is None:
        return None
    candidate_text = "\n".join(
        filter(
            None,
            [
                candidate.current_title,
                candidate.professional_summary,
                "Skills: " + ", ".join(candidate.skills),
                resume.raw_text[:12000] if resume else None,
            ],
        )
    )
    job_text = f"{job.title}\n{job.description[:12000]}"
    try:
        vectors = await provider.embed([candidate_text, job_text])
        if len(vectors) != 2:
            return None
        return round(max(0.0, _cosine_similarity(vectors[0], vectors[1])) * 100, 1)
    except Exception:
        logger.exception("Semantic matching failed; continuing without embeddings")
        return None


async def match_candidate_to_job(
    db: AsyncSession,
    *,
    candidate_id: uuid.UUID,
    job_id: uuid.UUID,
    resume_id: uuid.UUID | None,
    use_ai: bool,
    persist: bool,
) -> MatchResult:
    candidate = await candidate_service.get_candidate(db, candidate_id)
    job = await job_service.get_job(db, job_id)
    resume: Resume | None = None
    resume_profile: ResumeStructuredProfile | None = None
    if resume_id:
        resume = await resume_service.get_resume(db, resume_id)
        if resume.candidate_id != candidate_id:
            raise ValueError("Resume does not belong to the selected candidate")
        resume_profile = ResumeStructuredProfile.model_validate(resume.structured_data)

    requirements, analysis_ai_used = await analyze_job(
        db, job_id, use_ai=use_ai, persist=False
    )
    result = deterministic_match(candidate, job, requirements, resume_profile)

    semantic_score = await _semantic_score(candidate, job, resume) if use_ai else None
    if semantic_score is not None:
        overall = (
            0.45 * result.skill_score
            + 0.18 * result.experience_score
            + 0.12 * result.role_score
            + 0.10 * result.location_score
            + 0.15 * semantic_score
        )
        result.overall_score = round(overall, 1)
        result.semantic_score = semantic_score
        result.recommendation = _recommendation(overall)
        result.explanation += f" Semantic similarity: {semantic_score:.1f}."
        result.ai_used = True
    elif analysis_ai_used:
        result.ai_used = True

    if persist:
        record = JobMatch(
            candidate_id=candidate_id,
            job_id=job_id,
            resume_id=resume_id,
            overall_score=result.overall_score,
            skill_score=result.skill_score,
            experience_score=result.experience_score,
            role_score=result.role_score,
            location_score=result.location_score,
            semantic_score=result.semantic_score,
            ai_used=result.ai_used,
            matched_skills=result.matched_skills,
            missing_required_skills=result.missing_required_skills,
            matched_preferred_skills=result.matched_preferred_skills,
            strengths=result.strengths,
            gaps=result.gaps,
            recommendation=result.recommendation,
            explanation=result.explanation,
        )
        db.add(record)
        await db.commit()

    return result


async def list_matches(
    db: AsyncSession,
    candidate_id: uuid.UUID,
    *,
    limit: int = 50,
) -> list[JobMatch]:
    await candidate_service.get_candidate(db, candidate_id)
    result = await db.execute(
        select(JobMatch)
        .where(JobMatch.candidate_id == candidate_id)
        .order_by(JobMatch.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
