from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    # Which provider answers AI calls: "ollama" or "openrouter".
    ai_provider: str = "ollama"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # A free model; override in .env. ":free" model ids cost nothing but have rate limits.
    openrouter_model: str = "google/gemma-4-26b-a4b-it:free"
    # Tried in order when the main model is rate-limited or unavailable (comma-separated).
    openrouter_fallback_models: str = "openrouter/free,particle-ai/particle-1:free,google/gemma-4-31b-it:free"
    ollama_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gpt-oss:20b"
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'nextstep.db').as_posix()}"
    cors_origins: str = "http://localhost:5173"
    environment: str = "development"

    @property
    def sqlalchemy_database_url(self) -> str:
        """Normalise hosted Postgres URLs (Neon, Render) to the psycopg2 driver."""
        url = self.database_url.strip()
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg2://" + url[len("postgresql://") :]
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def has_ai_configured(self) -> bool:
        if self.ai_provider.strip().lower() == "openrouter":
            return bool(self.openrouter_api_key)
        return bool(self.ollama_base_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
