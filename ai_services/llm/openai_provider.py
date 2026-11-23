import time

import httpx

from ai_services.llm.base import (
    LLMResponse,
    LLMUnavailableError,
    format_provider_error,
    health_probe_timeout,
)

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"


class OpenAIProvider:
    """OpenAI (and OpenAI-compatible) chat completions adapter."""

    provider_name: str = "openai"

    def __init__(
        self,
        api_key: str | None,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        timeout_seconds: float = 45.0,
    ) -> None:
        self._api_key = (api_key or "").strip()
        self.model_name = model
        self.base_url = (base_url or DEFAULT_OPENAI_BASE_URL).rstrip("/")
        self.timeout_seconds = float(timeout_seconds)

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Call OpenAI `/chat/completions` and return normalized LLMResponse."""
        if not self._api_key:
            raise LLMUnavailableError("openai API key is not configured.")

        payload: dict[str, object] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._auth_headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise LLMUnavailableError(
                format_provider_error("openai", exc, secret=self._api_key)
            ) from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMUnavailableError(
                "openai provider returned malformed response payload."
            ) from exc

        if not isinstance(content, str):
            raise LLMUnavailableError("openai provider returned non-text content.")

        latency_ms = int((time.perf_counter() - start) * 1000)
        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model=self.model_name,
            latency_ms=latency_ms,
        )

    def health_check(self) -> bool:
        """Verify OpenAI API key and endpoint reachability within <= 2 seconds."""
        if not self._api_key:
            return False
        try:
            with httpx.Client(timeout=health_probe_timeout(self.timeout_seconds)) as client:
                response = client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
                return response.status_code == 200
        except Exception:
            return False
