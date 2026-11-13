"""
Claude client for the interviewer agent (SOLVARY_INTERVIEWER_DESIGN.md §9).

One request per turn, streamed. The real client wraps the official
`anthropic` SDK (built per call with the resolved key — keys are per user).
The fake client scripts replies for tests; a reply may be `[silent]`, and a
dict reply scripts a refusal or an API error.

Providers (settings.interviewer_provider): "anthropic" | "fake".
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

# Server-side refusal fallback (`fallbacks: "default"` needs this beta header)
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class ClaudeError(Exception):
    """A request to the Claude API failed before or during the stream."""

    def __init__(self, detail: str, status: int | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status = status


@dataclass
class ClaudeChunk:
    text: str = ""
    done: bool = False  # terminal chunk: stop_reason / usage / model are set
    stop_reason: str | None = None
    model: str | None = None
    usage: dict[str, int] = field(default_factory=dict)


class ClaudeClient(ABC):
    @abstractmethod
    def stream_turn(
        self,
        api_key: str,
        system: list[dict],
        messages: list[dict],
        *,
        model: str,
        effort: str,
        max_tokens: int,
    ) -> AsyncIterator[ClaudeChunk]:
        """Text chunks, then exactly one chunk with done=True."""
        ...

    @abstractmethod
    async def ping(self, api_key: str, model: str) -> str:
        """One tiny request to validate a key; returns the model that answered."""
        ...


# ── real provider ─────────────────────────────────────────────────


def _usage_dict(usage: object) -> dict[str, int]:
    out: dict[str, int] = {}
    for name in (
        "input_tokens",
        "output_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
    ):
        value = getattr(usage, name, None)
        if isinstance(value, int):
            out[name] = value
    return out


def _describe(exc: Exception, status: int | None) -> str:
    if status == 401:
        return "Anthropic rejected the API key (401). Check it under Interviews -> Interviewer."
    if status == 403:
        return "The API key is not allowed to use this model (403)."
    if status == 404:
        return "The configured interviewer model was not found (404)."
    if status == 429:
        return "Anthropic rate limit reached (429); try again in a moment."
    if status is not None and status >= 500:
        return f"The Claude API is having trouble right now ({status})."
    message = getattr(exc, "message", None) or str(exc)
    return f"Claude API error: {message[:300]}"


class AnthropicClaudeClient(ClaudeClient):
    def __init__(self, timeout_s: float = 60.0, max_retries: int = 2) -> None:
        self._timeout_s = timeout_s
        self._max_retries = max_retries
        self._fallbacks_ok = True  # flipped off once the API rejects the parameter

    def _client(self, api_key: str):
        import anthropic

        return anthropic.AsyncAnthropic(
            api_key=api_key, timeout=self._timeout_s, max_retries=self._max_retries
        )

    async def _run(self, client, kwargs: dict, fallbacks: bool) -> AsyncIterator[ClaudeChunk]:
        extra = {"betas": [FALLBACK_BETA], "fallbacks": "default"} if fallbacks else {}
        # `fallbacks` / `betas` live on the beta namespace only
        async with client.beta.messages.stream(**kwargs, **extra) as stream:
            async for text in stream.text_stream:
                yield ClaudeChunk(text=text)
            final = await stream.get_final_message()
        yield ClaudeChunk(
            done=True,
            stop_reason=final.stop_reason,
            model=final.model,
            usage=_usage_dict(final.usage),
        )

    async def stream_turn(
        self,
        api_key: str,
        system: list[dict],
        messages: list[dict],
        *,
        model: str,
        effort: str,
        max_tokens: int,
    ) -> AsyncIterator[ClaudeChunk]:
        import anthropic

        client = self._client(api_key)
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
            "output_config": {"effort": effort},
            # thinking omitted → adaptive by default on current models
        }
        try:
            if self._fallbacks_ok:
                try:
                    async for chunk in self._run(client, kwargs, fallbacks=True):
                        yield chunk
                    return
                except anthropic.BadRequestError as e:
                    # A 400 arrives before any text, so nothing has been yielded yet
                    if "fallback" not in str(e).lower():
                        raise
                    logger.warning(
                        "Claude API rejected server-side fallbacks for %s; "
                        "continuing without them (%s)",
                        model,
                        e,
                    )
                    self._fallbacks_ok = False
            async for chunk in self._run(client, kwargs, fallbacks=False):
                yield chunk
        except anthropic.APIStatusError as e:
            raise ClaudeError(_describe(e, e.status_code), e.status_code) from e
        except anthropic.APIConnectionError as e:
            raise ClaudeError("Could not reach the Claude API", None) from e
        finally:
            await client.close()

    async def ping(self, api_key: str, model: str) -> str:
        import anthropic

        client = self._client(api_key)
        try:
            message = await client.messages.create(
                model=model,
                max_tokens=8,
                messages=[{"role": "user", "content": "Reply with the single word: ok"}],
            )
            return message.model
        except anthropic.APIStatusError as e:
            raise ClaudeError(_describe(e, e.status_code), e.status_code) from e
        except anthropic.APIConnectionError as e:
            raise ClaudeError("Could not reach the Claude API", None) from e
        finally:
            await client.close()


# ── fake provider (tests, offline dev) ─────────────────────────────


class FakeClaudeClient(ClaudeClient):
    """Scripted replies. `queue("…", "[silent]", {"stop_reason": "refusal"},
    {"error": "boom", "status": 500})`; an empty queue answers with a canned
    line. Every call is recorded in `calls` so tests can inspect the prompt.
    Keys ending in `-bad` are rejected like a 401."""

    def __init__(self, chunk_chars: int = 3, delay_s: float = 0.0) -> None:
        self.replies: deque[str | dict] = deque()
        self.calls: list[dict] = []
        self.pings: list[tuple[str, str]] = []
        self._chunk_chars = chunk_chars
        self._delay_s = delay_s

    def queue(self, *replies: str | dict) -> None:
        self.replies.extend(replies)

    def reset(self) -> None:
        self.replies.clear()
        self.calls.clear()
        self.pings.clear()

    @staticmethod
    def _default_reply(messages: list[dict]) -> str:
        last = messages[-1]["content"] if messages else ""
        if isinstance(last, list):
            last = "\n".join(b.get("text", "") for b in last if isinstance(b, dict))
        for line in str(last).splitlines():
            line = line.strip()
            if line.startswith("- ") and "::" in line:
                name = line[2:].split(" ")[0]
                return f"(fake interviewer) Let's look at {name} — what does it expect?"
        return "(fake interviewer) Walk me through the approach you have on screen."

    async def stream_turn(
        self,
        api_key: str,
        system: list[dict],
        messages: list[dict],
        *,
        model: str,
        effort: str,
        max_tokens: int,
    ) -> AsyncIterator[ClaudeChunk]:
        self.calls.append(
            {
                "api_key": api_key,
                "system": system,
                "messages": messages,
                "model": model,
                "effort": effort,
                "max_tokens": max_tokens,
            }
        )
        if api_key.endswith("-bad"):
            raise ClaudeError(_describe(Exception("unauthorized"), 401), 401)
        scripted = self.replies.popleft() if self.replies else self._default_reply(messages)
        if isinstance(scripted, dict):
            if "error" in scripted:
                raise ClaudeError(str(scripted["error"]), scripted.get("status"))
            text = str(scripted.get("text", ""))
            stop_reason = str(scripted.get("stop_reason", "end_turn"))
        else:
            text, stop_reason = scripted, "end_turn"
        for i in range(0, len(text), self._chunk_chars):
            if self._delay_s:
                await asyncio.sleep(self._delay_s)
            yield ClaudeChunk(text=text[i : i + self._chunk_chars])
        yield ClaudeChunk(
            done=True,
            stop_reason=stop_reason,
            model=model,
            usage={
                "input_tokens": 100,
                "output_tokens": max(1, len(text.split())),
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
            },
        )

    async def ping(self, api_key: str, model: str) -> str:
        self.pings.append((api_key, model))
        if api_key.endswith("-bad"):
            raise ClaudeError(_describe(Exception("unauthorized"), 401), 401)
        return model


# ── factory + singleton ───────────────────────────────────────────


def create_claude_client(settings: Settings) -> ClaudeClient:
    provider = settings.interviewer_provider.lower()
    if provider == "fake":
        return FakeClaudeClient()
    if provider == "anthropic":
        return AnthropicClaudeClient()
    raise ValueError(f"Unknown interviewer provider: {provider!r} (use 'anthropic' or 'fake')")


_client: ClaudeClient | None = None


def get_claude_client() -> ClaudeClient:
    global _client
    if _client is None:
        _client = create_claude_client(get_settings())
    return _client
