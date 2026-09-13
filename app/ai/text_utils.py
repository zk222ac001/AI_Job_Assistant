import re

SKILL_VOCABULARY = {
    "python", "fastapi", "django", "flask", "sql", "postgresql", "mysql", "sqlite",
    "redis", "mongodb", "docker", "kubernetes", "terraform", "aws", "azure", "gcp",
    "linux", "git", "github actions", "ci/cd", "rest", "graphql", "microservices",
    "machine learning", "deep learning", "artificial intelligence", "ai", "llm", "llms",
    "rag", "retrieval augmented generation", "prompt engineering", "openai", "ollama",
    "langchain", "langgraph", "pydantic", "sqlalchemy", "pandas", "numpy", "scikit-learn",
    "pytorch", "tensorflow", "opencv", "computer vision", "nlp", "transformers",
    "embeddings", "vector database", "pgvector", "faiss", "pinecone", "qdrant",
    "javascript", "typescript", "react", "next.js", "node.js", "java", "c#", "c++", "c",
    "pytest", "unit testing", "integration testing", "api", "oauth", "jwt", "agile", "scrum",
}

ALIASES = {
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "ml": "machine learning",
    "genai": "artificial intelligence",
    "generative ai": "artificial intelligence",
    "large language models": "llm",
    "large language model": "llm",
    "llms": "llm",
    "rest api": "rest",
    "restful api": "rest",
    "github action": "github actions",
}


def normalize_skill(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    return ALIASES.get(normalized, normalized)


def unique_skills(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = normalize_skill(value)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def extract_known_skills(text: str) -> list[str]:
    haystack = text.lower()
    found: list[str] = []
    for skill in sorted(SKILL_VOCABULARY, key=len, reverse=True):
        pattern = r"(?<![\w+#.])" + re.escape(skill) + r"(?![\w+#.])"
        if re.search(pattern, haystack):
            found.append(skill)
    return unique_skills(found)
