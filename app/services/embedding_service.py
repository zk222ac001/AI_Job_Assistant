import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.factory import get_llm_provider
from app.core.config import get_settings
from app.models.job import JobPosting
from app.models.phase3 import JobEmbedding
from app.schemas.phase3 import SemanticJobResult


def _job_text(job: JobPosting) -> str:
    return "\n".join([
        job.title, job.company, job.location or "",
        "Required skills: " + ", ".join(job.required_skills),
        "Preferred skills: " + ", ".join(job.preferred_skills),
        job.description[:16000],
    ])


async def embed_job(db: AsyncSession, job: JobPosting) -> JobEmbedding | None:
    provider = get_llm_provider()
    if provider is None:
        return None
    settings = get_settings()
    text = _job_text(job)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    existing = (await db.execute(select(JobEmbedding).where(JobEmbedding.job_id == job.id))).scalar_one_or_none()
    if existing is not None and existing.text_hash == digest:
        return existing
    vectors = await provider.embed([text])
    if not vectors:
        return None
    vector = vectors[0]
    if len(vector) != settings.embedding_dimension:
        raise ValueError(f"Embedding dimension {len(vector)} does not match configured pgvector dimension {settings.embedding_dimension}.")
    model_name = settings.openai_embedding_model if settings.llm_provider == "openai" else settings.ollama_embedding_model
    if existing is None:
        existing = JobEmbedding(job_id=job.id, embedding=vector, model_name=model_name, text_hash=digest)
        db.add(existing)
    else:
        existing.embedding = vector; existing.model_name = model_name; existing.text_hash = digest
    await db.commit(); await db.refresh(existing)
    return existing


async def embed_jobs(db: AsyncSession, job_ids: list) -> int:
    count = 0
    for job_id in job_ids:
        job = await db.get(JobPosting, job_id)
        if job is not None and await embed_job(db, job) is not None:
            count += 1
    return count


async def semantic_search(db: AsyncSession, query: str, limit: int) -> list[SemanticJobResult]:
    provider = get_llm_provider()
    if provider is None:
        raise ValueError("Semantic search requires LLM_PROVIDER=openai or ollama")
    settings = get_settings()
    vectors = await provider.embed([query])
    if not vectors:
        return []
    query_vector = vectors[0]
    if len(query_vector) != settings.embedding_dimension:
        raise ValueError("Query embedding dimension does not match EMBEDDING_DIMENSION")
    distance = JobEmbedding.embedding.cosine_distance(query_vector)
    rows = await db.execute(select(JobEmbedding, JobPosting, distance.label("distance"))
        .join(JobPosting, JobPosting.id == JobEmbedding.job_id).order_by(distance).limit(limit))
    results = []
    for _embedding, job, raw_distance in rows.all():
        similarity = max(0.0, min(1.0, 1.0 - float(raw_distance)))
        results.append(SemanticJobResult(job_id=job.id, title=job.title, company=job.company,
            source=job.source, source_url=job.source_url, similarity=round(similarity * 100, 1)))
    return results
