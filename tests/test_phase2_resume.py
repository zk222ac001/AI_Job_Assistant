from app.services.resume_service import extract_resume_text, heuristic_resume_profile


def test_txt_resume_extraction_and_structuring() -> None:
    data = b"""Zuhair Khan
zuhair@example.com
+45 1234 5678
AI Engineer with 5 years of experience.
Python, FastAPI, Docker, PostgreSQL, LLM and RAG.
"""
    text = extract_resume_text("resume.txt", data)
    profile = heuristic_resume_profile(text)

    assert profile.name == "Zuhair Khan"
    assert str(profile.email) == "zuhair@example.com"
    assert profile.years_experience == 5.0
    assert "python" in profile.skills
    assert "fastapi" in profile.skills
    assert "docker" in profile.skills
    assert "postgresql" in profile.skills
    assert "llm" in profile.skills


def test_unsupported_resume_type_is_rejected() -> None:
    try:
        extract_resume_text("resume.exe", b"not a resume")
    except ValueError as exc:
        assert "PDF, DOCX, TXT, and Markdown" in str(exc)
    else:
        raise AssertionError("Expected unsupported resume type to be rejected")
