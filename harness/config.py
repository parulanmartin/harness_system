import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    llm_provider: str = "openrouter"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str = ""
    openrouter_app_name: str = "Harness Requirements System"
    llm_model: str = "anthropic/claude-3.5-sonnet"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    llm_temperature: float = 0.0

    @classmethod
    def from_env(cls) -> "Config":
        provider = os.getenv("LLM_PROVIDER", "openrouter").lower()
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        gemini_key = os.getenv("GEMINI_API_KEY", "")

        default_model = "anthropic/claude-3.5-sonnet" if provider == "openrouter" else "gpt-4o"

        return cls(
            llm_provider=provider,
            openrouter_api_key=openrouter_key,
            openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            openrouter_site_url=os.getenv("OPENROUTER_SITE_URL", ""),
            openrouter_app_name=os.getenv("OPENROUTER_APP_NAME", "Harness Requirements System"),
            llm_model=os.getenv("LLM_MODEL", default_model),
            openai_api_key=openai_key,
            anthropic_api_key=anthropic_key,
            gemini_api_key=gemini_key,
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
        )
