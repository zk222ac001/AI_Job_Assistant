# AI Job Assistant — Phase 1 Foundation

A production-oriented Python backend foundation for an AI-assisted job search platform.

## Included in Phase 1

- FastAPI REST API
- PostgreSQL database
- Async SQLAlchemy 2.x
- Alembic migrations
- Candidate profiles
- Job postings
- Application tracking
- Vendor-neutral LLM provider interface
- Vendor-neutral job-provider interface
- Pydantic validation
- Docker + Docker Compose
- pytest integration tests
- Health and readiness endpoints

## Architecture

```text
Client / Frontend
      |
      v
FastAPI REST API
      |
      +--> Service Layer
      |      |
      |      +--> Candidate Service
      |      +--> Job Service
      |      +--> Application Service
      |
      +--> AI Layer (provider abstraction)
      |
      +--> Job Provider Layer
      |
      v
PostgreSQL
```

The AI and external job-source integrations are intentionally abstracted. Phase 2 can add
OpenAI/Ollama/Gemini implementations and permitted job-data providers without coupling the
core application to one vendor.

## Project Structure

```text
ai-job-assistant/
├── app/
│   ├── api/routes/
│   ├── ai/providers/
│   ├── core/
│   ├── db/
│   ├── jobs/providers/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── alembic/
│   └── versions/
├── tests/
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Run with Docker

1. Copy the environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

2. Change `SECRET_KEY` in `.env`.

3. Start the stack:

```bash
docker compose up --build
```

4. Open the API documentation:

```text
http://localhost:8000/docs
```

Health endpoint:

```text
http://localhost:8000/health
```

Readiness endpoint:

```text
http://localhost:8000/ready
```

## Local Development

Create a Python 3.12 virtual environment and install development dependencies:

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Lint:

```bash
ruff check .
```

Type checking:

```bash
mypy app
```

## Main API Endpoints

### System

- `GET /health`
- `GET /ready`

### Candidates

- `POST /api/v1/candidates`
- `GET /api/v1/candidates`
- `GET /api/v1/candidates/{candidate_id}`
- `PATCH /api/v1/candidates/{candidate_id}`
- `DELETE /api/v1/candidates/{candidate_id}`

### Jobs

- `POST /api/v1/jobs`
- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `PATCH /api/v1/jobs/{job_id}`
- `DELETE /api/v1/jobs/{job_id}`

### Applications

- `POST /api/v1/applications`
- `GET /api/v1/applications`
- `GET /api/v1/applications/{application_id}`
- `PATCH /api/v1/applications/{application_id}`
- `DELETE /api/v1/applications/{application_id}`

## Next Phase

Phase 2 should add:

1. Resume PDF/DOCX upload and parsing
2. Structured candidate extraction
3. Job-description requirement extraction
4. Deterministic job-match scoring
5. LLM-assisted semantic matching
6. OpenAI and Ollama provider implementations
7. Resume tailoring with factuality guardrails
8. Cover-letter generation
9. Match explanation endpoint
10. AI evaluation tests

## Safety Design

This project is designed around user-controlled assistance. It should not fabricate candidate
qualifications, bypass CAPTCHAs, or circumvent job-site security controls. Automated application
submission should only be added for integrations that explicitly permit it and should retain an
auditable user-approval step for consequential actions.
