"""
routes/match.py — Semantic matching endpoint with history persistence.

Returns ranked job matches. If no job scores above the threshold,
the response includes external platform suggestions shown as a
rich alert card directly in the UI.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database import get_db
from models import Resume, Job, MatchHistory
from schemas import MatchResponse, JobMatch, JobResponse
from ai.job_matcher import match_resume_to_jobs
from config import get_settings

router   = APIRouter()
settings = get_settings()
log      = logging.getLogger("match")


@router.get("/match/{resume_id}", response_model=MatchResponse, tags=["Matching"])
def match_resume(resume_id: int, db: Session = Depends(get_db)):
    """
    Match a resume against all jobs using Sentence-BERT + cosine similarity.
    Results saved to match_history for the Analytics and History tabs.
    If no match is found, suggestions are returned for the portal alert card.
    """
    # ── 1. Fetch resume ──────────────────────────────────────────────────────
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume {resume_id} not found.")

    if not resume.extracted_text or not resume.extracted_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from this resume. Try a text-based PDF."
        )

    # ── 2. Fetch all jobs ────────────────────────────────────────────────────
    jobs    = db.query(Job).all()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if not jobs:
        return MatchResponse(
            resume_id=resume_id,
            resume_name=resume.filename,
            matches=[],
            total_jobs_compared=0,
            suggestions=settings.external_platforms,
            message="No job postings exist yet. Add some jobs first.",
            matched_at=now_str,
        )

    # ── 3. Run AI matching ───────────────────────────────────────────────────
    raw_matches, all_results, found_matches = match_resume_to_jobs(
        resume.extracted_text, jobs
    )

    # ── 4. Persist ALL results to MatchHistory ───────────────────────────────
    for result in all_results:
        db.add(MatchHistory(
            resume_id=resume_id,
            resume_name=resume.filename,
            job_id=result["job"].id,
            job_title=result["job"].title,
            company=result["job"].company,
            score=result["score"],
            score_percent=result["score_percent"],
            above_threshold=result["score"] >= settings.similarity_threshold,
        ))
    db.commit()

    # ── 5. Build Pydantic response ───────────────────────────────────────────
    job_matches = [
        JobMatch(
            job=JobResponse.model_validate(m["job"]),
            score=m["score"],
            score_percent=m["score_percent"],
            above_threshold=m["score"] >= settings.similarity_threshold,
        )
        for m in raw_matches
    ]

    # ── 6. Return result — UI handles the alert card for no-match ────────────
    if found_matches:
        return MatchResponse(
            resume_id=resume_id,
            resume_name=resume.filename,
            matches=job_matches,
            total_jobs_compared=len(jobs),
            suggestions=None,
            message=f"Found {len(job_matches)} relevant job(s) from {len(jobs)} postings.",
            matched_at=now_str,
        )
    else:
        return MatchResponse(
            resume_id=resume_id,
            resume_name=resume.filename,
            matches=job_matches,
            total_jobs_compared=len(jobs),
            suggestions=settings.external_platforms,
            message=f"No strong matches found across {len(jobs)} postings.",
            matched_at=now_str,
        )
