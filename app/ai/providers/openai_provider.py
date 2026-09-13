import json
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.ai.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(LLMProvider):
    """OpenAI implementation using the Responses API and embeddings."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        embedding_model: str,
        embedding_dimensions: int,
        timeout: float,
    ) -> None:
        self.model = model
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)

    async def generate_text(self, prompt: str, *, system_prompt: str | None = None) -> str:
        input_items: list[dict[str, str]] = []
        if system_prompt:
            input_items.append({"role": "system", "content": system_prompt})
        input_items.append({"role": "user", "content": prompt})
        response = await self.client.responses.create(model=self.model, input=input_items)
        return response.output_text.strip()

    async def structured_output(
        self,
        prompt: str,
        schema: type[T],
        *,
        system_prompt: str | None = None,
    ) -> T:
        schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        instruction = f"{prompt}\n\nReturn JSON only. It must validate against this JSON schema:\n{schema_json}"
        raw = await self.generate_text(instruction, system_prompt=system_prompt)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return schema.model_validate_json(cleaned)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        kwargs: dict[str, object] = {"model": self.embedding_model, "input": texts}
        if self.embedding_model.startswith("text-embedding-3"):
            kwargs["dimensions"] = self.embedding_dimensions
        response = await self.client.embeddings.create(**kwargs)  # type: ignore[arg-type]
        return [item.embedding for item in response.data]

    async def healthcheck(self) -> dict[str, object]:
        return {"provider": "openai", "model": self.model, "status": "configured"}
