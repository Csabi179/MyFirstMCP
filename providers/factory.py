import os

from providers.base import LLMProvider
from providers.groq_provider import GroqProvider


def create_provider() -> LLMProvider:
    provider_name = os.getenv(
        "LLM_PROVIDER",
        "groq",
    ).strip().lower()

    model_name = os.getenv(
        "LLM_MODEL",
        "openai/gpt-oss-120b",
    ).strip()

    if provider_name == "groq":
        return GroqProvider(
            model_name=model_name,
        )

    raise ValueError(
        f"Unsupported LLM provider: {provider_name}"
    )