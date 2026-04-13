"""
config.py — Centralised application configuration.

WHY THIS EXISTS:
Rather than scattering magic numbers and strings across modules,
all tunable parameters live here. For an MSc project this makes it
easy to run experiments (e.g. "what happens when I raise the threshold?")
without hunting through multiple files.

In production you'd load these from environment variables or a .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────
    app_title: str = "ResumeMatch AI"
    app_version: str = "1.0.0"
    debug: bool = True

    # ── Database ──────────────────────────────────────────────────
    database_url: str = "sqlite:///./job_platform.db"

    # ── File Upload ───────────────────────────────────────────────
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10          # Files over this size are rejected

    # ── AI Model ──────────────────────────────────────────────────
    sbert_model_name: str = "all-MiniLM-L6-v2"

    # ── Matching ──────────────────────────────────────────────────
    # Cosine similarity score below which a job is NOT recommended.
    # Range: 0.0 (accept everything) → 1.0 (only exact matches).
    # 0.35 is a sensible default for diverse resume/job text.
    similarity_threshold: float = 0.35

    # Maximum number of matches to return even when results are found
    max_results: int = 10

    # ── External Platforms (shown when no match found) ─────────────
    external_platforms: list[str] = [
        "LinkedIn (linkedin.com/jobs)",
        "Internshala (internshala.com)",
        "Wellfound / AngelList (wellfound.com)",
        "Indeed (indeed.com)",
        "Naukri (naukri.com)",
        "Glassdoor (glassdoor.com)",
        "Monster (monster.com)",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",           # Optionally override via .env file
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    lru_cache ensures the .env file is only read once, not on every request.
    """
    return Settings()
