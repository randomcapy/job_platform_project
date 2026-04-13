"""
routes/resumes.py — Resume upload, retrieval, and deletion.

UPLOAD FLOW:
  1. Validate file is .pdf and within size limit
  2. Generate a unique filename to prevent collisions
  3. Save to uploads/ directory
  4. Extract text with PyMuPDF
  5. Store record (filename, filepath, text, word_count) in DB
  6. Return ResumeResponse with the new ID

COLLISION GUARD:
  If two users upload "resume.pdf", the second would overwrite the first.
  We prefix with the DB-assigned ID after a two-step save (save → get ID →
  rename). Alternatively we use uuid to make filenames unique immediately.
"""

import os
import uuid
import shutil

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Resume
from schemas import ResumeResponse
from ai.resume_parser import extract_text_from_pdf
from config import get_settings

router = APIRouter()
settings = get_settings()

os.makedirs(settings.upload_dir, exist_ok=True)


@router.post("/resumes", response_model=ResumeResponse, tags=["Resumes"],
             summary="Upload a PDF resume")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF resume.

    - Rejects non-PDF files (400)
    - Rejects files over MAX_UPLOAD_SIZE_MB (413)
    - Extracts all text with PyMuPDF
    - Returns the resume ID needed for /match/{id}
    """
    # ── Validate file type ───────────────────────────────────────────────────
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted. Please upload a .pdf resume.",
        )

    # ── Read file into memory and check size ─────────────────────────────────
    contents = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb} MB.",
        )

    # ── Build a unique filename using uuid to avoid collisions ───────────────
    # e.g.  resume.pdf  →  resume_3f8a1b2c.pdf
    stem   = os.path.splitext(file.filename)[0]
    unique = f"{stem}_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(settings.upload_dir, unique)

    # ── Save to disk ─────────────────────────────────────────────────────────
    with open(filepath, "wb") as f_out:
        f_out.write(contents)

    # ── Extract text via PyMuPDF ─────────────────────────────────────────────
    try:
        extracted_text = extract_text_from_pdf(filepath)
    except Exception as exc:
        extracted_text = f"[Text extraction failed: {exc}]"

    word_count = len(extracted_text.split()) if extracted_text else 0

    # ── Persist to database ──────────────────────────────────────────────────
    resume = Resume(
        filename=file.filename,   # Keep the human-readable original name
        filepath=filepath,        # Store the unique path on disk
        extracted_text=extracted_text,
        word_count=word_count,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return resume


@router.get("/resumes", response_model=list[ResumeResponse], tags=["Resumes"],
            summary="List all uploaded resumes")
def list_resumes(db: Session = Depends(get_db)):
    """Return all uploaded resumes, newest first."""
    return db.query(Resume).order_by(Resume.uploaded_at.desc()).all()


@router.get("/resumes/{resume_id}", response_model=ResumeResponse, tags=["Resumes"],
            summary="Get a single resume")
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume {resume_id} not found.")
    return resume


@router.get("/resumes/{resume_id}/text", tags=["Resumes"],
            summary="Preview extracted resume text")
def resume_text(resume_id: int, db: Session = Depends(get_db)):
    """
    Returns the raw text the AI reads from the resume.
    Useful for debugging unexpected match results.
    """
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume {resume_id} not found.")
    text = resume.extracted_text or ""
    return {
        "resume_id": resume_id,
        "filename": resume.filename,
        "char_count": len(text),
        "word_count": resume.word_count or len(text.split()),
        "preview": text[:500] + ("…" if len(text) > 500 else ""),
        "full_text": text,
    }


@router.delete("/resumes/{resume_id}", tags=["Resumes"],
               summary="Delete a resume")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    """Delete a resume record and its file from disk."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume {resume_id} not found.")
    if os.path.exists(resume.filepath):
        os.remove(resume.filepath)
    db.delete(resume)
    db.commit()
    return {"message": f"Resume {resume_id} ({resume.filename}) deleted."}
