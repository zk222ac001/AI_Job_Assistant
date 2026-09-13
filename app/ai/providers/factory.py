from functools import lru_cache

from app.ai.providers.base import LLMProvider
from app.core.config import get_settings


@lru_cache
def get_llm_provider() -> LLMProvider | None:
    settings = get_settings()
    if settings.llm_provider == "none":
        return None
    if settings.llm_provider == "openai":
        from app.ai.providers.openai_provider import OpenAIProvider

        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            embedding_model=settings.openai_embedding_model,
            embedding_dimensions=settings.embedding_dimension,
            timeout=settings.llm_timeout_seconds,
        )
    if settings.llm_provider == "ollama":
        from app.ai.providers.ollama_provider import OllamaProvider

        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            embedding_model=settings.ollama_embedding_model,
            timeout=settings.llm_timeout_seconds,
        )
    raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")
