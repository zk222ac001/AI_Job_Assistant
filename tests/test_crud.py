import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_candidate_job_application_flow(client: AsyncClient) -> None:
    candidate_response = await client.post(
        "/api/v1/candidates",
        json={
            "name": "Demo Candidate",
            "email": "demo@example.com",
            "current_title": "AI Engineer",
            "years_experience": 5,
            "target_roles": ["AI Engineer", "LLM Engineer"],
            "skills": ["Python", "FastAPI", "Docker"],
        },
    )
    assert candidate_response.status_code == 201
    candidate_id = candidate_response.json()["id"]

    job_response = await client.post(
        "/api/v1/jobs",
        json={
            "company": "Example AI",
            "title": "Senior AI Engineer",
            "description": "Build production AI systems using Python and FastAPI.",
            "required_skills": ["Python", "FastAPI"],
            "preferred_skills": ["Kubernetes"],
            "remote_status": "REMOTE",
        },
    )
    assert job_response.status_code == 201
    job_id = job_response.json()["id"]

    application_response = await client.post(
        "/api/v1/applications",
        json={
            "candidate_id": candidate_id,
            "job_id": job_id,
            "status": "MATCHED",
            "match_score": 88.5,
        },
    )
    assert application_response.status_code == 201
    payload = application_response.json()
    assert payload["status"] == "MATCHED"
    assert payload["match_score"] == 88.5

    duplicate = await client.post(
        "/api/v1/applications",
        json={"candidate_id": candidate_id, "job_id": job_id},
    )
    assert duplicate.status_code == 409
