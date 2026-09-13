import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_resume_upload_and_match_flow(client: AsyncClient) -> None:
    candidate_response = await client.post(
        "/api/v1/candidates",
        json={
            "name": "Test Engineer",
            "email": "test@example.com",
            "current_title": "AI Engineer",
            "years_experience": 5,
            "target_roles": ["Senior AI Engineer"],
            "skills": ["Python", "FastAPI", "Docker", "LLM"],
            "preferred_locations": ["Copenhagen"],
            "preferred_technologies": ["Python"],
        },
    )
    assert candidate_response.status_code == 201
    candidate_id = candidate_response.json()["id"]

    resume_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/resumes?use_ai=false",
        files={
            "file": (
                "resume.txt",
                b"Test Engineer\ntest@example.com\n5 years Python FastAPI Docker LLM experience",
                "text/plain",
            )
        },
    )
    assert resume_response.status_code == 201
    resume_id = resume_response.json()["id"]
    assert "python" in resume_response.json()["structured_data"]["skills"]

    job_response = await client.post(
        "/api/v1/jobs",
        json={
            "company": "Example AI",
            "title": "Senior AI Engineer",
            "location": "Copenhagen",
            "country": "Denmark",
            "remote_status": "HYBRID",
            "description": "Need 5 years Python FastAPI Docker Kubernetes and LLM experience.",
            "required_skills": ["Python", "FastAPI", "Docker", "Kubernetes", "LLM"],
            "preferred_skills": ["AWS"],
        },
    )
    assert job_response.status_code == 201
    job_id = job_response.json()["id"]

    match_response = await client.post(
        "/api/v1/analysis/match",
        json={
            "candidate_id": candidate_id,
            "job_id": job_id,
            "resume_id": resume_id,
            "use_ai": False,
            "persist": True,
        },
    )
    assert match_response.status_code == 200
    body = match_response.json()
    assert 0 <= body["overall_score"] <= 100
    assert "kubernetes" in body["missing_required_skills"]

    history_response = await client.get(f"/api/v1/analysis/matches/{candidate_id}")
    assert history_response.status_code == 200
    assert len(history_response.json()) == 1
