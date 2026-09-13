import json
from typing import TypeVar

import httpx
from pydantic import BaseModel

from app.ai.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class OllamaProvider(LLMProvider):
    """Ollama implementation for local/private inference."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        embedding_model: str,
        timeout: float,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.embedding_model = embedding_model
        self.timeout = timeout

    async def generate_text(self, prompt: str, *, system_prompt: str | None = None) -> str:
        payload: dict[str, object] = {"model": self.model, "prompt": prompt, "stream": False}
        if system_prompt:
            payload["system"] = system_prompt
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
        return str(data.get("response", "")).strip()

    async def structured_output(
        self,
        prompt: str,
        schema: type[T],
        *,
        system_prompt: str | None = None,
    ) -> T:
        payload: dict[str, object] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": schema.model_json_schema(),
        }
        if system_prompt:
            payload["system"] = system_prompt
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
        return schema.model_validate(json.loads(str(data.get("response", "{}"))))

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json={"model": self.embedding_model, "input": texts},
            )
            response.raise_for_status()
            data = response.json()
        return [[float(value) for value in vector] for vector in data.get("embeddings", [])]

    async def healthcheck(self) -> dict[str, object]:
        try:
            async with httpx.AsyncClient(timeout=min(self.timeout, 5.0)) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
            status = "ok"
        except httpx.HTTPError:
            status = "unavailable"
        return {"provider": "ollama", "model": self.model, "status": status}
