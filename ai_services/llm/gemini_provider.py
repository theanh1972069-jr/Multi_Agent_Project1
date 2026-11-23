import time

import httpx

from ai_services.llm.base import (
    LLMResponse,
    LLMUnavailableError,
    format_provider_error,
    health_probe_timeout,
)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _to_gemini_payload(
    messages: list[dict[str, str]],
    temperature: float,
    json_mode: bool,
) -> dict[str, object]:
    """Convert OpenAI-style chat messages to Gemini generateContent payload."""
    system_parts: list[dict[str, str]] = []
    contents: list[dict[str, object]] = []

    for msg in messages:
        role = (msg.get("role") or "user").strip().lower()
        text = msg.get("content") or ""
        if role == "system":
            if text:
                system_parts.append({"text": text})
            continue
        gemini_role = "model" if role == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": text}]})

    if not contents:
        contents.append({"role": "user", "parts": [{"text": ""}]})

    generation_config: dict[str, object] = {"temperature": temperature}
    if json_mode:
        generation_config["responseMimeType"] = "application/json"

    payload: dict[str, object] = {
        "contents": contents,
        "generationConfig": generation_config,
    }
    if system_parts:
        payload["systemInstruction"] = {"parts": system_parts}
    return payload


class GeminiProvider:
    """Google Gemini REST API adapter."""

    provider_name: str = "gemini"

    def __init__(
        self,
        api_key: str | None,
        model: str = "gemini-2.5-flash",
        timeout_seconds: float = 45.0,
    ) -> None:
        self._api_key = (api_key or "").strip()
        self.model_name = model
        self.timeout_seconds = float(timeout_seconds)

    def _headers(self) -> dict[str, str]:
        return {
            "x-goog-api-key": self._api_key,
            "Content-Type": "application/json",
        }

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Call Gemini `generateContent` endpoint and return normalized LLMResponse."""
        if not self._api_key:
            raise LLMUnavailableError("gemini API key is not configured.")

        url = f"{GEMINI_API_BASE}/models/{self.model_name}:generateContent"
        payload = _to_gemini_payload(messages, temperature=temperature, json_mode=json_mode)

        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(url, headers=self._headers(), json=payload)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise LLMUnavailableError(
                format_provider_error("gemini", exc, secret=self._api_key)
            ) from exc

        try:
            parts = data["candidates"][0]["content"]["parts"]
            text_chunks = [part["text"] for part in parts if isinstance(part.get("text"), str)]
            content = "".join(text_chunks)
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMUnavailableError(
                "gemini provider returned malformed response payload."
            ) from exc

        if not text_chunks:
            raise LLMUnavailableError("gemini provider returned empty response content.")

        latency_ms = int((time.perf_counter() - start) * 1000)
        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model=self.model_name,
            latency_ms=latency_ms,
        )

    def health_check(self) -> bool:
        """Verify Gemini model endpoint reachability within <= 2 seconds."""
        if not self._api_key:
            return False
        url = f"{GEMINI_API_BASE}/models/{self.model_name}"
        try:
            with httpx.Client(timeout=health_probe_timeout(self.timeout_seconds)) as client:
                response = client.get(url, headers={"x-goog-api-key": self._api_key})
                return response.status_code == 200
        except Exception:
            return False
