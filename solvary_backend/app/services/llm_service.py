"""
LLM service abstraction for the AI assistant (design decision #12: reuse
MattChat's BaseLLMService + SSE pattern; the model behind it is whatever
OpenAI-compatible server you point LLM_BASE_URL at — matt_llm/serve.py,
vLLM, OpenAI, Groq…).

Providers (settings.llm_provider):
  - "mock"   → canned streamed replies, no network (dev/tests)
  - "openai" → streaming /chat/completions against settings.llm_base_url
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    role: str  # system | user | assistant
    content: str


@dataclass
class LLMChunk:
    """A single chunk of streamed LLM output."""

    content: str
    done: bool = False


class BaseLLMService(ABC):
    @abstractmethod
    def stream_response(self, messages: list[ChatMessage]) -> AsyncIterator[LLMChunk]:
        """Stream a reply to the given conversation. Must end with done=True."""
        ...


# ── OpenAI-compatible provider ────────────────────────────────────


class OpenAICompatibleLLMService(BaseLLMService):
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.llm_base_url.rstrip("/")
        self._api_key = settings.llm_api_key
        self._model = settings.llm_model
        self._max_tokens = settings.llm_max_tokens
        self._temperature = settings.llm_temperature

    async def stream_response(self, messages: list[ChatMessage]) -> AsyncIterator[LLMChunk]:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
            "stream": True,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            try:
                async with client.stream(
                    "POST", f"{self._base_url}/chat/completions", json=payload, headers=headers
                ) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        logger.error("LLM API error %d: %s", resp.status_code, body[:500])
                        yield LLMChunk(
                            content="Sorry — the assistant backend returned an error."
                        )
                        yield LLMChunk(content="", done=True)
                        return

                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            delta = json.loads(data)["choices"][0].get("delta", {})
                        except (json.JSONDecodeError, KeyError, IndexError) as e:
                            logger.warning("Unparseable LLM chunk %r: %s", data[:200], e)
                            continue
                        content = delta.get("content") or ""
                        if content:
                            yield LLMChunk(content=content)
            except httpx.HTTPError as e:
                logger.error("LLM API unreachable: %s", e)
                yield LLMChunk(content="Sorry — the assistant is unavailable right now.")

        yield LLMChunk(content="", done=True)


# ── Mock provider ─────────────────────────────────────────────────


class MockLLMService(BaseLLMService):
    """Streams a canned, lightly context-aware reply token by token."""

    def __init__(self, token_delay_s: float = 0.005) -> None:
        self._token_delay_s = token_delay_s

    @staticmethod
    def _compose(messages: list[ChatMessage]) -> str:
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        has_code = "```" in last_user
        return (
            "**(mock assistant)** Here's how I'd approach this.\n\n"
            "1. Re-read the input format in the statement and make sure you parse "
            "*exactly* that — most wrong answers on stdin problems are parsing slips.\n"
            "2. Walk the first sample by hand and compare each printed line to the "
            "expected output, including trailing newlines.\n"
            + (
                "3. In your code, check the loop bounds and what you print on the "
                "last iteration — off-by-one errors hide there.\n"
                if has_code
                else "3. Sketch the brute force first, then ask what repeated work a "
                "hash map or a sort could remove.\n"
            )
            + "\nWant a hint for the next step, or should I review a specific line?"
        )

    async def stream_response(self, messages: list[ChatMessage]) -> AsyncIterator[LLMChunk]:
        text = self._compose(messages)
        for i, word in enumerate(text.split(" ")):
            if self._token_delay_s:
                await asyncio.sleep(self._token_delay_s)
            yield LLMChunk(content=("" if i == 0 else " ") + word)
        yield LLMChunk(content="", done=True)


# ── Factory + singleton ───────────────────────────────────────────


def create_llm_service(settings: Settings) -> BaseLLMService:
    provider = settings.llm_provider.lower()
    if provider == "mock":
        return MockLLMService()
    if provider in ("openai", "vllm", "matt_llm"):
        logger.info(
            "Using OpenAI-compatible LLM: model=%s base_url=%s",
            settings.llm_model,
            settings.llm_base_url,
        )
        return OpenAICompatibleLLMService(settings)
    raise ValueError(f"Unknown LLM provider: {provider!r} (use 'mock' or 'openai')")


_llm: BaseLLMService | None = None


def get_llm_service() -> BaseLLMService:
    global _llm
    if _llm is None:
        _llm = create_llm_service(get_settings())
    return _llm
