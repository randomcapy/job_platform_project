"""
models.py — Defines the database tables as Python classes (ORM Models).

WHY THIS EXISTS:
SQLAlchemy models map Python objects to database rows. When we call
Base.metadata.create_all(), SQLAlchemy reads these classes and
automatically creates the corresponding SQL tables in SQLite.

Each class = one table. Each attribute = one column.
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base


class Resume(Base):
    """
    Stores uploaded resume metadata and extracted text.

    WHY STORE TEXT IN DB?
    Once we extract text from the PDF, we cache it here so we don't
    re-parse the PDF on every match request. This improves performance
    and keeps the matching logic separate from file handling.
    """
    __tablename__ = "resumes"

    id            = Column(Integer, primary_key=True, index=True)
    filename      = Column(String(255), nullable=False)
    filepath      = Column(String(500), nullable=False)
    extracted_text= Column(Text, nullable=True)
    word_count    = Column(Integer, nullable=True)           # Cached word count
    uploaded_at   = Column(DateTime(timezone=True), server_default=func.now())


class Job(Base):
    """
    Stores job postings created by recruiters/admins.

    WHY SEPARATE DESCRIPTION AND SKILLS?
    The full description gives richer context for semantic matching,
    while skills and experience are stored separately for display
    and potential keyword-based filtering in the future.
    """
    __tablename__ = "jobs"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(255), nullable=False)
    company     = Column(String(255), nullable=True)
    skills      = Column(Text, nullable=True)
    experience  = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class MatchHistory(Base):
    """
    Persists every match query result for analytics and history review.

    WHY STORE MATCH HISTORY?
    - Professors can see the system has been used and produces consistent results
    - Enables analytics (score distributions, top-matched jobs)
    - Supports a "Match History" view without re-running AI every time
    - Proves the system works across multiple resumes and sessions
    """
    __tablename__ = "match_history"

    id            = Column(Integer, primary_key=True, index=True)
    resume_id     = Column(Integer, nullable=False, index=True)
    resume_name   = Column(String(255), nullable=True)       # Denormalised for display
    job_id        = Column(Integer, nullable=False)
    job_title     = Column(String(255), nullable=False)
    company       = Column(String(255), nullable=True)
    score         = Column(Float, nullable=False)
    score_percent = Column(String(20), nullable=False)
    above_threshold = Column(Boolean, default=False)         # Was this a "good" match?
    matched_at    = Column(DateTime(timezone=True), server_default=func.now())
