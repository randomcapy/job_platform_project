"""
routes/analytics.py — Platform analytics and match history endpoints.

WHY THIS EXISTS:
For an MSc demo, being able to show statistics about the system's usage
is very compelling. Professors can see:
  - How many resumes have been processed
  - Score distributions (how well resume content maps to jobs)
  - Which jobs get matched most often (demand signals)
  - Full history of every match query made

These endpoints also demonstrate that the system persists state,
not just computes one-off results.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional

from database import get_db
from models import Resume, Job, MatchHistory
from schemas import MatchHistoryItem, AnalyticsSummary

router = APIRouter()


@router.get("/analytics", response_model=AnalyticsSummary, tags=["Analytics"])
def get_analytics(db: Session = Depends(get_db)):
    """
    Return platform-wide analytics:
      - Total resumes, jobs, match queries
      - Score distribution (high / medium / low)
      - Top 5 most-matched jobs

    This demonstrates the system has been actively used and
    gives a statistical view of resume-job alignment quality.
    """
    total_resumes = db.query(func.count(Resume.id)).scalar() or 0
    total_jobs    = db.query(func.count(Job.id)).scalar() or 0

    # Each match query stores one row per job compared, so we count
    # distinct (resume_id, matched_at) pairs as "queries run"
    # For simplicity we count total history rows / avg jobs as a proxy
    total_history_rows = db.query(func.count(MatchHistory.id)).scalar() or 0

    # Score distribution buckets
    high_matches   = db.query(func.count(MatchHistory.id)).filter(MatchHistory.score >= 0.6).scalar() or 0
    medium_matches = db.query(func.count(MatchHistory.id)).filter(
        MatchHistory.score >= 0.4, MatchHistory.score < 0.6
    ).scalar() or 0
    low_matches    = db.query(func.count(MatchHistory.id)).filter(MatchHistory.score < 0.4).scalar() or 0

    # Average of the TOP score per match session
    # (We use above_threshold=True rows to represent meaningful match events)
    avg_result = db.query(func.avg(MatchHistory.score)).filter(
        MatchHistory.above_threshold == True
    ).scalar()
    avg_top_score = round(float(avg_result), 3) if avg_result else 0.0

    # Top 5 most-matched jobs (by number of times they appeared in results)
    top_jobs_query = (
        db.query(
            MatchHistory.job_title,
            MatchHistory.company,
            func.count(MatchHistory.id).label("match_count"),
            func.avg(MatchHistory.score).label("avg_score"),
        )
        .group_by(MatchHistory.job_id)
        .order_by(desc("avg_score"))
        .limit(5)
        .all()
    )
    top_matched_jobs = [
        {
            "title": row.job_title,
            "company": row.company or "N/A",
            "match_count": row.match_count,
            "avg_score": f"{row.avg_score * 100:.1f}%",
        }
        for row in top_jobs_query
    ]

    return AnalyticsSummary(
        total_resumes=total_resumes,
        total_jobs=total_jobs,
        total_matches_run=total_history_rows,
        avg_top_score=avg_top_score,
        high_matches=high_matches,
        medium_matches=medium_matches,
        low_matches=low_matches,
        top_matched_jobs=top_matched_jobs,
    )


@router.get("/history", response_model=List[MatchHistoryItem], tags=["Analytics"])
def get_match_history(
    resume_id: Optional[int] = Query(None, description="Filter by resume ID"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """
    Return past match results, optionally filtered by resume.

    Useful for:
    - Reviewing what happened when a specific resume was matched
    - Showing professors a log of system activity
    - Debugging unexpected match scores
    """
    query = db.query(MatchHistory)
    if resume_id is not None:
        query = query.filter(MatchHistory.resume_id == resume_id)
    results = query.order_by(desc(MatchHistory.matched_at)).limit(limit).all()
    return results


@router.delete("/history", tags=["Analytics"])
def clear_history(db: Session = Depends(get_db)):
    """Clear all match history. Useful for resetting a demo."""
    deleted = db.query(MatchHistory).delete()
    db.commit()
    return {"message": f"Cleared {deleted} history records."}
