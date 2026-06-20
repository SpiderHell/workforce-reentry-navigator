"""Pydantic settings for the Workforce Re-entry Navigator."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Anthropic
    anthropic_api_key: str
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    # App
    app_env: str = "development"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./data/reentry_navigator.db"
    log_level: str = "INFO"

    # Job matching
    min_match_threshold: float = 0.65
    max_matches: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
