import asyncio
import hashlib
import io
import logging
import re
import uuid
from pathlib import Path

from docx import Document
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.factory import get_llm_provider
from app.ai.text_utils import extract_known_skills, unique_skills
from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.models.resume import Resume
from app.schemas.resume import ResumeStructuredProfile
from app.services import candidate_service

logger = logging.getLogger(__name__)
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def extract_resume_text(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("Supported resume types are PDF, DOCX, TXT, and Markdown")

    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    elif suffix == ".docx":
        document = Document(io.BytesIO(data))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    else:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("TXT/Markdown resumes must use UTF-8 encoding") from exc

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise ValueError("No readable text was found in the resume")
    return text


def heuristic_resume_profile(text: str) -> ResumeStructuredProfile:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = None
    for line in lines[:5]:
        if 1 < len(line.split()) <= 5 and "@" not in line and not re.search(r"\d{3,}", line):
            name = line[:200]
            break
    email_match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I)
    phone_match = re.search(r"(?:\+?\d[\d ()-]{7,}\d)", text)
    years = [float(v) for v in re.findall(r"(\d{1,2}(?:\.\d)?)\+?\s+years?", text, re.I)]
    return ResumeStructuredProfile(
        name=name,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0).strip() if phone_match else None,
        years_experience=max(years) if years else None,
        skills=extract_known_skills(text),
    )


async def extract_structured_profile(
    text: str, *, use_ai: bool
) -> tuple[ResumeStructuredProfile, bool]:
    baseline = heuristic_resume_profile(text)
    provider = get_llm_provider() if use_ai else None
    if provider is None:
        return baseline, False
    system_prompt = (
        "Extract only facts explicitly present in the resume. Never invent skills, employers, "
        "degrees, certifications, dates, achievements, or experience. Use null/empty values "
        "when information is unknown."
    )
    try:
        profile = await provider.structured_output(
            f"Extract a structured candidate profile from this resume:\n\n{text[:30000]}",
            ResumeStructuredProfile,
            system_prompt=system_prompt,
        )
        profile.skills = unique_skills([*baseline.skills, *profile.skills])
        return profile, True
    except Exception:
        logger.exception("LLM resume extraction failed; using deterministic extraction")
        return baseline, False


async def create_resume(
    db: AsyncSession,
    *,
    candidate_id: uuid.UUID,
    filename: str,
    content_type: str,
    data: bytes,
    use_ai: bool,
) -> Resume:
    await candidate_service.get_candidate(db, candidate_id)
    settings = get_settings()
    if not data:
        raise ValueError("Resume file is empty")
    if len(data) > settings.max_resume_size_bytes:
        raise ValueError(f"Resume exceeds {settings.max_resume_size_mb} MB upload limit")

    raw_text = await asyncio.to_thread(extract_resume_text, filename, data)
    structured, _ = await extract_structured_profile(raw_text, use_ai=use_ai)
    storage_key: str | None = None
    if settings.store_resume_files:
        directory = Path(settings.resume_storage_path)
        await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
        storage_key = f"{uuid.uuid4()}{Path(filename).suffix.lower()}"
        await asyncio.to_thread((directory / storage_key).write_bytes, data)

    resume = Resume(
        candidate_id=candidate_id,
        filename=Path(filename).name[:255],
        content_type=(content_type or "application/octet-stream")[:100],
        file_size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        raw_text=raw_text,
        structured_data=structured.model_dump(mode="json"),
        storage_key=storage_key,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


async def get_resume(db: AsyncSession, resume_id: uuid.UUID) -> Resume:
    resume = await db.get(Resume, resume_id)
    if resume is None:
        raise NotFoundError("Resume not found")
    return resume


async def list_candidate_resumes(db: AsyncSession, candidate_id: uuid.UUID) -> list[Resume]:
    await candidate_service.get_candidate(db, candidate_id)
    result = await db.execute(
        select(Resume).where(Resume.candidate_id == candidate_id).order_by(Resume.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_resume(db: AsyncSession, resume_id: uuid.UUID) -> None:
    resume = await get_resume(db, resume_id)
    if resume.storage_key:
        path = Path(get_settings().resume_storage_path) / resume.storage_key
        await asyncio.to_thread(path.unlink, missing_ok=True)
    await db.delete(resume)
    await db.commit()
