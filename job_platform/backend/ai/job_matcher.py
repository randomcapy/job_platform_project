"""
ai/job_matcher.py — Sentence-BERT semantic matching engine.

Returns both the filtered display list AND the full results list
so the match route can persist everything to MatchHistory.
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Tuple
from config import get_settings

settings = get_settings()

print(f"🤖 Loading Sentence-BERT model ({settings.sbert_model_name})...")
model = SentenceTransformer(settings.sbert_model_name)
print("✅ Model loaded successfully.")


def get_embedding(text: str) -> np.ndarray:
    """Convert text to a 384-dim semantic vector."""
    return model.encode(text, convert_to_numpy=True)


def match_resume_to_jobs(
    resume_text: str,
    jobs: list,
) -> Tuple[List[dict], List[dict], bool]:
    """
    Rank all jobs by cosine similarity to the resume.

    Returns:
        (display_list, all_results, found_matches)
        - display_list: filtered/truncated list for the UI response
        - all_results:  full list of every job with its score (for MatchHistory)
        - found_matches: True if any score >= threshold
    """
    if not jobs:
        return [], [], False

    # ── Embed resume (shape 1×384) ───────────────────────────────────────────
    resume_embedding = get_embedding(resume_text).reshape(1, -1)

    # ── Build rich job texts ─────────────────────────────────────────────────
    job_texts = [
        (
            f"Job Title: {job.title}\n"
            f"Company: {job.company or 'N/A'}\n"
            f"Required Skills: {job.skills or 'N/A'}\n"
            f"Experience Required: {job.experience or 'N/A'}\n"
            f"Job Description: {job.description}"
        )
        for job in jobs
    ]

    # ── Batch encode all jobs in ONE forward pass ────────────────────────────
    job_embeddings = model.encode(job_texts, convert_to_numpy=True, batch_size=32)

    # ── Vectorised cosine similarity: shape (num_jobs,) ──────────────────────
    scores = cosine_similarity(resume_embedding, job_embeddings)[0]

    # ── Build full results list ──────────────────────────────────────────────
    all_results = [
        {
            "job": job,
            "score": round(float(score), 4),
            "score_percent": f"{float(score) * 100:.1f}%",
        }
        for job, score in zip(jobs, scores)
    ]
    all_results.sort(key=lambda x: x["score"], reverse=True)

    # ── Filter by threshold for display ─────────────────────────────────────
    above = [r for r in all_results if r["score"] >= settings.similarity_threshold]
    found = len(above) > 0

    display = above[:settings.max_results] if found else all_results[:5]
    return display, all_results, found
