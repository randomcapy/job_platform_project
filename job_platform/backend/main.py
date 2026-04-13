"""
main.py — FastAPI application entry point.

STARTUP SEQUENCE:
  1. Settings loaded from config.py (reads .env if present)
  2. FastAPI app created with title/version from settings
  3. CORS middleware registered
  4. Static files and Jinja2 templates wired up
  5. All four routers included (resumes, jobs, match, analytics)
  6. on_startup event: DB tables created + model pre-warmed
  7. Uvicorn begins accepting connections

WHY PRE-WARM THE MODEL?
  Sentence-BERT loads from disk on first import (~2s on CPU).
  By importing job_matcher inside on_startup, the model is loaded
  before the first real request arrives, so the user never experiences
  a slow first match.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
import models  # noqa — registers ORM models with Base
from routes import resumes, jobs, match, analytics
from config import get_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
log = logging.getLogger("main")

settings = get_settings()


# ── Lifespan (startup / shutdown) ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once at startup (before accepting requests) and once at shutdown.

    Startup tasks:
      1. Create all DB tables (idempotent — safe to run repeatedly)
      2. Pre-load the Sentence-BERT model so the first /match call is fast
    """
    log.info("── Startup ──────────────────────────────────────────")

    # 1. Create tables
    Base.metadata.create_all(bind=engine)
    log.info("✅ Database tables ready.")

    # 2. Pre-warm model (import triggers model download/load at module level)
    from ai.job_matcher import model as sbert_model  # noqa
    log.info(f"✅ Sentence-BERT model ready: {settings.sbert_model_name}")

    # Ensure upload dir exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    log.info(f"✅ Upload directory ready: {settings.upload_dir}/")

    log.info(f"🚀 {settings.app_title} v{settings.app_version} is live.")
    log.info("─────────────────────────────────────────────────────")

    yield  # ← application runs here

    # Shutdown (nothing needed for this project)
    log.info("Server shutting down.")


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_title,
    description=(
        "An MSc Data Science project demonstrating semantic job matching "
        "using Sentence-BERT (all-MiniLM-L6-v2) and cosine similarity.\n\n"
        "**Key endpoints:**\n"
        "- `POST /resumes` — upload a PDF resume\n"
        "- `POST /jobs` — create a job posting\n"
        "- `GET /match/{resume_id}` — rank jobs by semantic similarity\n"
        "- `GET /analytics` — platform statistics\n"
        "- `GET /history` — full match history log\n"
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static Files & Templates ───────────────────────────────────────────────────
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(resumes.router)    # /resumes
app.include_router(jobs.router)       # /jobs
app.include_router(match.router)      # /match/{resume_id}
app.include_router(analytics.router)  # /analytics  /history


# ── HTML Dashboard ─────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ── Health Check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"], summary="Server health check")
def health():
    """Returns server status, model name, and current settings."""
    return {
        "status": "healthy",
        "app": settings.app_title,
        "version": settings.app_version,
        "model": settings.sbert_model_name,
        "similarity_threshold": settings.similarity_threshold,
        "max_results": settings.max_results,
    }
