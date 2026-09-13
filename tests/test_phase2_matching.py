from app.models.candidate import CandidateProfile
from app.models.enums import RemoteStatus
from app.models.job import JobPosting
from app.schemas.analysis import JobRequirements
from app.services.matching_service import deterministic_match


def test_deterministic_match_exposes_skill_gap() -> None:
    candidate = CandidateProfile(
        name="AI Engineer",
        current_title="AI Engineer",
        years_experience=5,
        target_roles=["Senior AI Engineer"],
        skills=["Python", "FastAPI", "Docker", "PostgreSQL", "LLM"],
        preferred_locations=["Copenhagen"],
        preferred_technologies=[],
    )
    job = JobPosting(
        company="Example AI",
        title="Senior AI Engineer",
        location="Copenhagen",
        country="Denmark",
        remote_status=RemoteStatus.HYBRID,
        description="Python FastAPI Docker Kubernetes LLM",
        responsibilities=[],
        required_skills=["Python", "FastAPI", "Docker", "Kubernetes", "LLM"],
        preferred_skills=["AWS"],
    )
    requirements = JobRequirements(
        title=job.title,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        min_years_experience=5,
    )

    result = deterministic_match(candidate, job, requirements)

    assert result.overall_score >= 70
    assert "kubernetes" in result.missing_required_skills
    assert "python" in result.matched_skills
    assert result.experience_score == 100
    assert result.recommendation in {"Good Match", "Strong Match"}
