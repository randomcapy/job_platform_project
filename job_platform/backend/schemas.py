"""
schemas.py — Pydantic models for request validation and response serialization.

WHY THIS EXISTS:
FastAPI uses Pydantic to:
  1. Validate incoming request data
  2. Serialize outgoing response data into clean JSON
  3. Auto-generate Swagger docs at /docs
"""

from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


# ── Job Schemas ──────────────────────────────────────────────────────────────

class JobCreate(BaseModel):
    title: str
    company: Optional[str] = None
    skills: Optional[str] = None
    experience: Optional[str] = None
    description: str

    @field_validator("title", "description")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be blank")
        return v.strip()


class JobResponse(BaseModel):
    id: int
    title: str
    company: Optional[str]
    skills: Optional[str]
    experience: Optional[str]
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Resume Schemas ───────────────────────────────────────────────────────────

class ResumeResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    extracted_text: Optional[str]
    word_count: Optional[int]

    class Config:
        from_attributes = True


# ── Match Schemas ────────────────────────────────────────────────────────────

class JobMatch(BaseModel):
    job: JobResponse
    score: float
    score_percent: str
    above_threshold: bool


class MatchResponse(BaseModel):
    resume_id: int
    resume_name: Optional[str]
    matches: List[JobMatch]
    total_jobs_compared: int
    suggestions: Optional[List[str]] = None
    message: str
    matched_at: str


# ── History Schemas ──────────────────────────────────────────────────────────

class MatchHistoryItem(BaseModel):
    id: int
    resume_id: int
    resume_name: Optional[str]
    job_id: int
    job_title: str
    company: Optional[str]
    score: float
    score_percent: str
    above_threshold: bool
    matched_at: datetime

    class Config:
        from_attributes = True


# ── Analytics Schemas ────────────────────────────────────────────────────────

class AnalyticsSummary(BaseModel):
    total_resumes: int
    total_jobs: int
    total_matches_run: int
    avg_top_score: float
    high_matches: int       # score >= 0.6
    medium_matches: int     # 0.4 <= score < 0.6
    low_matches: int        # score < 0.4
    top_matched_jobs: List[dict]
