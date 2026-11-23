import time

import httpx

from ai_services.llm.base import (
    LLMResponse,
    LLMUnavailableError,
    format_provider_error,
    health_probe_timeout,
)


class OllamaProvider:
    """Local Ollama chat completion adapter via HTTP REST API."""

    provider_name: str = "ollama"

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5:1.5b",
        timeout_seconds: float = 45.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model
        self.timeout_seconds = float(timeout_seconds)

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Send a non-streaming chat request to Ollama `/api/chat`."""
        payload: dict[str, object] = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if json_mode:
            payload["format"] = "json"

        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise LLMUnavailableError(format_provider_error("ollama", exc)) from exc

        message = data.get("message") if isinstance(data, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise LLMUnavailableError("ollama provider returned malformed response payload.")

        latency_ms = int((time.perf_counter() - start) * 1000)
        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model=self.model_name,
            latency_ms=latency_ms,
        )

    def health_check(self) -> bool:
        """Check whether the Ollama daemon responds within <= 2 seconds."""
        try:
            with httpx.Client(timeout=health_probe_timeout(self.timeout_seconds)) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
