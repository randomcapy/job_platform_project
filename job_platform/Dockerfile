# ──────────────────────────────────────────────────────────────────────────────
# Dockerfile — Containerise the ResumeMatch AI platform
#
# WHY DOCKER?
#   Docker packages the app and ALL its dependencies into a single image.
#   Anyone with Docker installed can run the full platform with one command,
#   regardless of their OS or Python version. This is ideal for MSc demos,
#   CI/CD pipelines, and cloud deployment.
#
# BUILD:
#   docker build -t resumematch-ai .
#
# RUN:
#   docker run -p 8000:8000 resumematch-ai
#   Then visit: http://localhost:8000
#
# WITH PERSISTENT STORAGE (so the DB survives container restarts):
#   docker run -p 8000:8000 -v $(pwd)/data:/app/data resumematch-ai
# ──────────────────────────────────────────────────────────────────────────────

# ── Stage 1: base image ────────────────────────────────────────────────────────
# python:3.11-slim is a minimal Debian image with Python 3.11.
# We avoid the full image (~900MB) to keep our final image smaller.
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1   \
    PYTHONUNBUFFERED=1          \
    PIP_NO_CACHE_DIR=1          \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system deps needed by PyMuPDF (libmupdf) and torch
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 2: dependencies ─────────────────────────────────────────────────────
FROM base AS deps

WORKDIR /install

# Copy requirements first — Docker caches this layer so pip only re-runs
# if requirements.txt actually changes (not on every code edit).
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Pre-download the Sentence-BERT model during build so the container
# starts instantly without downloading 22MB on every cold start.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# ── Stage 3: final image ──────────────────────────────────────────────────────
FROM base AS final

WORKDIR /app

# Copy installed packages from the deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy the cached SBERT model
COPY --from=deps /root/.cache /root/.cache

# Copy application source code
COPY backend/ .

# Create directories the app expects at runtime
RUN mkdir -p uploads static templates

# Expose the port uvicorn will listen on
EXPOSE 8000

# Health check — Docker will mark the container unhealthy if this fails
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

# Run the server
# - host 0.0.0.0 listens on all interfaces inside the container
# - reload=False for production stability (use reload=True only in dev)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
