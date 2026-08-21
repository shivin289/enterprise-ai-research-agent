"""
Central application configuration.
All environment-driven settings live here so the rest of the app
never touches os.environ directly.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 1440

    database_url: str = "postgresql+psycopg://research_user:research_pass@localhost:5432/research_agent"

    redis_url: str = "redis://localhost:6379/0"

    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    
    # Groq -- OpenAI-compatible free-tier provider, no billing required
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    search_provider: str = "mock"
    tavily_api_key: str = ""
    serpapi_api_key: str = ""

    cache_ttl_seconds: int = 86400


@lru_cache
def get_settings() -> Settings:
    return Settings()
