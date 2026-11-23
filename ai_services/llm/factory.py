from backend.app.core.config import Settings

from ai_services.llm.base import LLMProvider
from ai_services.llm.gemini_provider import GeminiProvider
from ai_services.llm.ollama_provider import OllamaProvider
from ai_services.llm.openai_provider import OpenAIProvider


def get_llm_provider(settings: Settings) -> LLMProvider:
    """Instantiate the configured LLMProvider from application settings."""
    provider = (settings.llm_provider or "ollama").strip().lower()
    if provider == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
        )
    if provider == "openai":
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            base_url=settings.openai_base_url,
        )
    if provider == "gemini":
        return GeminiProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )
    raise ValueError(f"Unsupported llm_provider: {settings.llm_provider!r}")
