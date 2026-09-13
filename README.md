# AI Job Assistant — Phase 2 AI Pipeline

A production-oriented Python backend for an AI-assisted job search platform.

Phase 1 established FastAPI, PostgreSQL, SQLAlchemy, Alembic, candidate profiles, job postings, and application tracking. Phase 2 adds resume processing, explainable job matching, skill-gap analysis, OpenAI/Ollama integrations, resume tailoring, and cover-letter assistance with deterministic fallbacks.

## Phase 2 Features

- Upload PDF, DOCX, TXT, and Markdown resumes
- Extract resume text and structured candidate facts
- Optional LLM-based structured resume extraction
- Analyze job descriptions and extract requirements
- Deterministic, explainable 0–100 job matching
- Required/preferred skill-gap analysis
- Optional embedding-based semantic match scoring
- OpenAI provider
- Ollama provider for local/private inference
- Persist match history
- ATS-focused resume tailoring plan with factuality guardrails
- Cover-letter generation with user-review warnings
- Phase 2 Alembic migration and tests

## Architecture

```text
                         FastAPI
                            |
          +-----------------+------------------+
          |                 |                  |
          v                 v                  v
   Candidate API        Jobs API          Resume API
          |                 |                  |
          +-----------------+------------------+
                            |
                            v
                       Analysis API
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
        Resume Parser  Job Analyzer   Match Engine
              |             |             |
              +-------------+-------------+
                            |
                    Optional AI Layer
                      /            \
                     v              v
                  OpenAI          Ollama
                            |
                            v
                       PostgreSQL
```

The core application does not require an LLM. With `LLM_PROVIDER=none`, resume parsing, job analysis, and matching still work using deterministic logic.

## Setup

Copy the environment file:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Put it in `.env`:

```env
SECRET_KEY=your-generated-secret
```

Start the stack:

```bash
docker compose up --build
```

Swagger UI:

```text
http://localhost:8000/docs
```

## AI Provider Configuration

### Deterministic mode

```env
LLM_PROVIDER=none
```

### OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-5.6-luna
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Ollama

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

Example local setup:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

## Resume Privacy

Original resume files are not stored by default:

```env
STORE_RESUME_FILES=false
```

Extracted text and structured resume data are stored in PostgreSQL so matching can run. For development-only original-file storage:

```env
STORE_RESUME_FILES=true
RESUME_STORAGE_PATH=/tmp/ai-job-assistant/resumes
```

For production SaaS, replace local file storage with encrypted object storage and explicit retention/deletion policies.

## Phase 2 Endpoints

### Resume processing

```text
POST   /api/v1/candidates/{candidate_id}/resumes
GET    /api/v1/candidates/{candidate_id}/resumes
GET    /api/v1/resumes/{resume_id}
DELETE /api/v1/resumes/{resume_id}
```

### Job analysis

```text
POST /api/v1/analysis/jobs/{job_id}?use_ai=true&persist=false
```

### Candidate/job matching

```text
POST /api/v1/analysis/match
GET  /api/v1/analysis/matches/{candidate_id}
```

Example request:

```json
{
  "candidate_id": "candidate-uuid",
  "job_id": "job-uuid",
  "resume_id": "resume-uuid",
  "use_ai": true,
  "persist": true
}
```

### Resume tailoring

```text
POST /api/v1/analysis/tailor-resume
```

### Cover letter

```text
POST /api/v1/analysis/cover-letter
```

## Match Scoring

Without embeddings:

```text
55% skill match
20% experience match
15% role/title alignment
10% location/remote alignment
```

With embeddings:

```text
45% skill match
18% experience match
12% role/title alignment
10% location/remote alignment
15% semantic similarity
```

The output always includes matched skills, missing required skills, component scores, recommendation, and explanation.

## Database Migration

Phase 2 adds:

```text
resumes
job_matches
```

Docker runs migrations automatically. Locally:

```bash
alembic upgrade head
```

## Local Development

```bash
python -m venv .venv
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

Type check:

```bash
mypy app
```

## Safety and Factuality

The system is designed to:

- never invent candidate skills, employers, degrees, certifications, projects, dates, or achievements;
- keep unknown resume values empty rather than guessing;
- show missing job requirements as gaps;
- require review of generated resume and cover-letter content;
- avoid CAPTCHA bypasses and platform security circumvention;
- keep automatic application submission outside this Phase 2 pipeline.

## Recommended Phase 3

1. Job-source connectors using permitted APIs/feeds
2. PostgreSQL `pgvector` for persistent embeddings
3. Background workers with Redis/Celery or equivalent
4. Job alerts and notifications
5. Recruiter/interview email classification
6. Interview preparation assistant
7. Authentication and per-user ownership controls
8. Production object storage for resumes
9. LLM evaluation datasets and regression tests
10. Frontend dashboard
