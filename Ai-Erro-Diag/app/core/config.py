"""
Core configuration module.

Loads all settings from environment variables using pydantic-settings.
No secrets are ever hardcoded.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Gemini ──────────────────────────────────────────────────────────────
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_vision_model: str = Field(
        default="gemini-1.5-flash", description="Model used for vision analysis"
    )
    gemini_diagnosis_model: str = Field(
        default="gemini-1.5-flash", description="Model used for diagnosis generation"
    )

    # ── Application ─────────────────────────────────────────────────────────
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")

    # ── File Handling ────────────────────────────────────────────────────────
    max_upload_size_mb: int = Field(default=10)
    uploads_dir: Path = Field(default=Path("uploads"))
    reports_dir: Path = Field(default=Path("reports"))

    # ── RAG / FAISS ──────────────────────────────────────────────────────────
    faiss_index_path: Path = Field(default=Path("faiss_index/errors.index"))
    faiss_metadata_path: Path = Field(default=Path("faiss_index/metadata.json"))
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    top_k_results: int = Field(default=5)

    # ── Knowledge Base ───────────────────────────────────────────────────────
    knowledge_base_dir: Path = Field(default=Path("data/errors"))

    @property
    def max_upload_size_bytes(self) -> int:
        """Return maximum upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    def ensure_directories(self) -> None:
        """Create required runtime directories if they do not exist."""
        for directory in (
            self.uploads_dir,
            self.reports_dir,
            self.faiss_index_path.parent,
        ):
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    settings = Settings()  # type: ignore[call-arg]
    settings.ensure_directories()
    return settings
