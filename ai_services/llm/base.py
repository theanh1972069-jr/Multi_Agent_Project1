from typing import Protocol, runtime_checkable

import httpx
from pydantic import BaseModel

MAX_HEALTH_CHECK_TIMEOUT_SECONDS = 2.0


class LLMResponse(BaseModel):
    """Normalized response returned by any LLMProvider implementation."""

    content: str
    provider: str
    model: str
    latency_ms: int


class LLMUnavailableError(Exception):
    """Raised when the configured LLM provider is unreachable, misconfigured, or errors."""


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for pluggable LLM adapters (Ollama, OpenAI, Gemini)."""

    provider_name: str
    model_name: str

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate a completion from chat-formatted messages."""
        ...

    def health_check(self) -> bool:
        """Probe provider availability with a short timeout (<= 2s). Never raises."""
        ...


def health_probe_timeout(timeout_seconds: float) -> float:
    """Clamp health check timeout to a positive value at most 2.0 seconds."""
    return min(max(float(timeout_seconds), 0.1), MAX_HEALTH_CHECK_TIMEOUT_SECONDS)


def format_provider_error(
    provider: str, exc: Exception, secret: str | None = None
) -> str:
    """Format a concise provider error message without leaking API keys."""
    if isinstance(exc, httpx.HTTPStatusError):
        detail = f"HTTP {exc.response.status_code}"
    elif isinstance(exc, httpx.TimeoutException):
        detail = "request timed out"
    elif isinstance(exc, httpx.RequestError):
        detail = type(exc).__name__
    else:
        detail = str(exc) or type(exc).__name__

    if secret:
        detail = detail.replace(secret, "***")
    return f"{provider} provider unavailable ({detail})."
