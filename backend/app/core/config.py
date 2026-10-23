# app/core/config.py
# Loads all environment variables for CampusHire via pydantic-settings.

from __future__ import annotations

from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS — stored as a comma-separated string in .env, e.g.:
    #   CORS_ORIGINS=http://localhost:5173,https://campushire.app
    # We keep it as a plain str here so pydantic-settings does NOT try
    # to JSON-decode it, then parse it ourselves in the validator below.
    CORS_ORIGINS: str = "http://localhost:5173"

    # File uploads
    UPLOAD_DIRECTORY: str = "uploads"

    # AI — Embeddings
    # SentenceTransformer model to use for semantic embeddings.
    # Defaults to a small, CPU-friendly model.
    # Override in .env: EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # AI — Job Recommendations
    # Number of top jobs returned by GET /students/recommended-jobs.
    # Override in .env: RECOMMENDATION_TOP_N=5
    RECOMMENDATION_TOP_N: int = 5

    # AI — Resume Content Validation
    # Set to False to skip the resume content check (useful during testing).
    # Override in .env: RESUME_VALIDATION_ENABLED=false
    RESUME_VALIDATION_ENABLED: bool = True

    # Minimum heuristic score (0-10) for a document to be accepted as a resume.
    # Raise this to make the gate stricter; lower it to be more permissive.
    # Override in .env: RESUME_VALIDATION_MIN_SCORE=6
    RESUME_VALIDATION_MIN_SCORE: float = 6.0

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS_ORIGINS as a list, splitting on commas."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


# Singleton — import this everywhere.
settings = Settings()
