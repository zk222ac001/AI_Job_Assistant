from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Vendor-neutral contract for LLM providers."""

    @abstractmethod
    async def generate_text(self, prompt: str, *, system_prompt: str | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    async def structured_output(
        self,
        prompt: str,
        schema: type[T],
        *,
        system_prompt: str | None = None,
    ) -> T:
        raise NotImplementedError

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    async def healthcheck(self) -> dict[str, Any]:
        return {"provider": self.__class__.__name__, "status": "unknown"}
