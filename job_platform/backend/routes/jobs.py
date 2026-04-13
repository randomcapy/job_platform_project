"""
routes/jobs.py — API routes for job posting creation and retrieval.

WHY THIS EXISTS:
This module handles the job posting side of the platform. In a real system,
recruiters would use this to post openings. For the demo, you can add
sample jobs via the UI or the /docs Swagger interface.

The more descriptive the job posting (especially the description field),
the better the semantic matching will perform — because Sentence-BERT
has more context to work with.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Job
from schemas import JobCreate, JobResponse

router = APIRouter()


@router.post("/jobs", response_model=JobResponse, tags=["Jobs"])
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """
    Create a new job posting.

    The description field is the most important for semantic matching —
    write it with rich detail about responsibilities and expectations.

    Args:
        job: JobCreate Pydantic model (validated request body)
        db: Database session

    Returns:
        The created Job record with its assigned ID
    """
    db_job = Job(
        title=job.title,
        company=job.company,
        skills=job.skills,
        experience=job.experience,
        description=job.description
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@router.get("/jobs", response_model=List[JobResponse], tags=["Jobs"])
def list_jobs(db: Session = Depends(get_db)):
    """
    Return all job postings in the database.
    Used by the UI to display available positions.
    """
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Fetch a single job posting by its ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found.")
    return job


@router.delete("/jobs/{job_id}", tags=["Jobs"])
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a job posting by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found.")
    db.delete(job)
    db.commit()
    return {"message": f"Job {job_id} deleted successfully."}
