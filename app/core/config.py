"""Central application settings, loaded from environment variables / .env."""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_name: str = "AI Budget Tracker API"
    debug: bool = False
    default_currency: str = "THB"
    currency_symbol: str = "฿"
    app_timezone: str = "Asia/Bangkok"

    # Database (Supabase PostgreSQL) - required, no default on purpose
    database_url: str

    # Auth - required; min_length forces a reasonably strong secret
    secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # CORS (comma-separated string; see cors_origin_list)
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # AI (Groq)
    ai_provider: Literal["groq", "mock", "none"] = "none"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    ai_timeout_seconds: float = 20.0

    # OCR
    ocr_provider: Literal["paddle", "mock", "none"] = "none"
    upload_dir: Path = Path("uploads")
    max_upload_mb: int = 5

    # Algorithm tuning
    anomaly_min_samples: int = 8
    forecast_window_days: int = 5

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Supabase gives postgres:// or postgresql://; SQLAlchemy needs a driver."""
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+psycopg2://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()