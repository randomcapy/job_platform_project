# 🧠 ResumeMatch AI — Intelligent Job Recommendation Platform

> **MSc Data Science Project** | Semantic NLP Matching with Sentence-BERT + Cosine Similarity

---

## 📌 Project Overview

ResumeMatch AI is a full-stack platform where candidates upload PDF resumes and receive **semantically ranked job recommendations** powered by AI. Unlike keyword-based search, it uses **Sentence-BERT** to encode the *meaning* of text into 384-dimensional vectors, then measures closeness with **cosine similarity**.

The system also persists every match query, exposing a **Match History log** and an **Analytics dashboard** showing score distributions and top-matched roles — making it demo-ready for academic presentations.

---

## 🧠 Why Semantic Matching? (The Core Idea)

### The Problem with Keywords

```
Resume:  "Python developer with ML experience"
Job:     "Machine Learning Engineer using Python"

Keyword match → FAIL  (words differ)
Semantic match → 0.91 ✅  (meaning is the same)
```

### How It Works — 3 Steps

**Step 1 — Text → Vector**

Sentence-BERT (a fine-tuned transformer) converts any text into a fixed-size
384-dimensional vector where semantically similar sentences cluster together:

```
"Python ML developer"        → [0.12, -0.45, 0.83, ...]   (384 numbers)
"Machine learning engineer"  → [0.14, -0.42, 0.81, ...]   (very close!)
"Executive pastry chef"      → [-0.55, 0.21, -0.33, ...]  (very different)
```

**Step 2 — Cosine Similarity**

Measures the angle between two vectors:

```
similarity = (A · B) / (||A|| × ||B||)   ∈  [0.0, 1.0]
```

Result = 1.0 → identical meaning. Result = 0.0 → unrelated.

Why cosine and not Euclidean distance? A short resume and a long resume
about the same career will have different vector *lengths* but point in
the same *direction*. Cosine only cares about direction.

**Step 3 — Threshold & Rank**

Jobs are sorted by score (highest first). Jobs below `SIMILARITY_THRESHOLD`
(default: 0.35) trigger a "no suitable match" response with external platform
suggestions — preventing irrelevant results from being shown as matches.

---

## 📁 Complete Project Structure

```
job_platform/
│
├── Dockerfile                   ← Container build definition
├── docker-compose.yml           ← One-command startup with volumes
├── Makefile                     ← Short commands: make run, make test, etc.
├── requirements.txt             ← All Python dependencies with pinned versions
├── seed_jobs.py                 ← Populate 8 sample jobs for the demo
├── .env.example                 ← Configuration template
├── .gitignore                   ← Excludes secrets, DB files, uploads
├── .dockerignore                ← Keeps Docker image lean
│
├── backend/
│   ├── main.py                  ← FastAPI app, lifespan startup, routers
│   ├── run.py                   ← Convenient server launcher (python run.py)
│   ├── config.py                ← All settings in one place (reads .env)
│   ├── database.py              ← SQLite engine + session factory
│   ├── models.py                ← SQLAlchemy ORM: Resume, Job, MatchHistory
│   ├── schemas.py               ← Pydantic schemas for request/response
│   │
│   ├── routes/
│   │   ├── resumes.py           ← Upload, list, preview text, delete
│   │   ├── jobs.py              ← Create, list, get, delete job postings
│   │   ├── match.py             ← Semantic matching + history persistence
│   │   └── analytics.py        ← Analytics summary + history log endpoints
│   │
│   ├── ai/
│   │   ├── resume_parser.py     ← PDF → text via PyMuPDF (fitz)
│   │   └── job_matcher.py      ← SBERT batch embedding + cosine similarity
│   │
│   ├── templates/
│   │   └── index.html          ← Single-page dashboard (3 tabs, glassmorphism)
│   │
│   ├── static/                  ← CSS, images (served at /static)
│   └── uploads/                 ← Uploaded PDFs (auto-created, git-ignored)
│
└── tests/
    └── test_platform.py         ← 40+ pytest tests across 6 test classes
```

---

## ⚙️ Tech Stack

| Layer       | Technology                    | Why chosen                                         |
|-------------|-------------------------------|----------------------------------------------------|
| Backend     | FastAPI (Python 3.11)         | Async, fast, auto Swagger docs, type safety         |
| Database    | SQLite + SQLAlchemy ORM       | Zero-config, file-based, full ORM support          |
| AI/NLP      | Sentence-BERT `all-MiniLM-L6-v2` | 22MB, fast, 384-dim, fine-tuned for semantic search |
| Similarity  | sklearn `cosine_similarity`   | Vectorised, stable, well-tested                    |
| PDF Parsing | PyMuPDF (fitz)                | Fast, accurate, handles multi-column layouts        |
| Config      | pydantic-settings             | Type-safe settings with `.env` file support        |
| Frontend    | Vanilla HTML + CSS + JS       | No framework overhead, fully explainable            |
| Container   | Docker + Docker Compose       | Reproducible, one-command deployment                |
| Testing     | pytest + FastAPI TestClient   | Real HTTP tests, isolated test database             |

---

## 🚀 Quick Start — 3 Ways to Run

### Option A: Python (Recommended for Development)

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
cd backend
python run.py
# OR: uvicorn main:app --reload

# 4. Seed sample jobs (new terminal, server must be running)
cd ..
python seed_jobs.py
```

Open **http://localhost:8000**

---

### Option B: Make (shorthand commands)

```bash
make install    # install deps
make run        # start server
make test       # run tests
make seed       # seed sample jobs
make clean      # remove cache and test DBs
```

---

### Option C: Docker (One Command)

```bash
docker-compose up
```

Builds the image, downloads the model, starts the server.
Visit **http://localhost:8000**. Uploaded files and the database persist in `./data/`.

---

## 📱 UI Features (3-Tab Dashboard)

### Tab 1: Dashboard
- **Drag-and-drop PDF upload** with live filename preview
- **Job posting form** — create postings directly from the browser
- **Match section** — enter Resume ID, get ranked results instantly
- Score bars (🟢 green ≥60%, 🟡 amber 40–59%, 🔴 red <40%)
- Platform suggestions when no jobs match the threshold
- Live job list with inline delete buttons

### Tab 2: Match History
- Every match ever run, sorted by time
- Filter by Resume ID to see a specific candidate's history
- Shows job title, company, score, and timestamp
- Clear all history button (useful for demo resets)

### Tab 3: Analytics
- Total resumes uploaded, jobs posted, match queries run
- Average match score across all sessions
- Score distribution bar chart (High / Medium / Low)
- Top 5 highest-scoring jobs across all match sessions

---

## 🔌 All API Endpoints

| Method   | Endpoint                    | Description                                    |
|----------|-----------------------------|------------------------------------------------|
| `GET`    | `/`                         | HTML dashboard                                 |
| `GET`    | `/health`                   | Server status + active settings                |
| `POST`   | `/resumes`                  | Upload a PDF resume (multipart/form-data)       |
| `GET`    | `/resumes`                  | List all resumes                               |
| `GET`    | `/resumes/{id}`             | Get one resume by ID                           |
| `GET`    | `/resumes/{id}/text`        | Preview the extracted text the AI reads        |
| `DELETE` | `/resumes/{id}`             | Delete resume record + file from disk          |
| `POST`   | `/jobs`                     | Create a job posting                           |
| `GET`    | `/jobs`                     | List all job postings                          |
| `GET`    | `/jobs/{id}`                | Get one job by ID                              |
| `DELETE` | `/jobs/{id}`                | Delete a job posting                           |
| `GET`    | `/match/{resume_id}`        | Semantic match — returns ranked jobs + history |
| `GET`    | `/analytics`                | Platform-wide statistics summary               |
| `GET`    | `/history`                  | Full match history log (filterable)            |
| `DELETE` | `/history`                  | Clear all history (demo reset)                 |

Full interactive docs: **http://localhost:8000/docs**  
ReDoc alternative: **http://localhost:8000/redoc**

---

## ⚙️ Configuration (`.env`)

Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

| Variable              | Default             | Description                                         |
|-----------------------|---------------------|-----------------------------------------------------|
| `SBERT_MODEL_NAME`    | `all-MiniLM-L6-v2`  | Swap to `all-mpnet-base-v2` for higher accuracy      |
| `SIMILARITY_THRESHOLD`| `0.35`              | Minimum score to be shown as a "match"              |
| `MAX_RESULTS`         | `10`                | Maximum ranked results returned per query           |
| `MAX_UPLOAD_SIZE_MB`  | `10`                | Reject PDFs larger than this                        |
| `DATABASE_URL`        | `sqlite:///./job_platform.db` | Switch to PostgreSQL for production      |
| `UPLOAD_DIR`          | `uploads`           | Where PDFs are stored on disk                       |

All settings are read once at startup and cached — no restart needed if using environment variables directly.

---

## 🧪 Running Tests

```bash
cd backend
pytest ../tests/ -v
```

**40+ tests across 6 classes:**

| Class               | Tests | What it covers                                           |
|---------------------|-------|----------------------------------------------------------|
| `TestHealth`        | 3     | Server running, response schema, HTML delivery           |
| `TestJobCreation`   | 5     | Valid, minimal, missing fields, multiple jobs            |
| `TestJobRetrieval`  | 5     | List, get by ID, delete, 404 handling                    |
| `TestResumeUpload`  | 7     | Valid PDF, non-PDF rejection, size rejection, text preview|
| `TestMatching`      | 7     | No-jobs fallback, schema, sorted scores, above_threshold |
| `TestAIModules`     | 5     | Embedding dimensions, similar vs dissimilar texts        |
| `TestAnalytics`     | 9     | History persistence, filter, clear, analytics structure  |

Tests use an isolated in-memory SQLite DB — they never touch your real data.

---

## 🎓 Academic Talking Points

### For Your MSc Presentation

**1. Why Sentence-BERT over vanilla BERT?**
Vanilla BERT's `[CLS]` token embedding is not optimised for semantic similarity.
Sentence-BERT (Reimers & Gurevych, 2019) uses a Siamese network trained on
NLI + STS datasets, producing embeddings where `cosine(A, B)` meaningfully
reflects textual similarity. `all-MiniLM-L6-v2` is distilled from a larger
model — only 22MB but retains ~96% of its accuracy.

**2. Cosine vs Euclidean Distance**
Cosine similarity is direction-invariant: a 200-word resume and a 2000-word
resume about the same career produce vectors of different magnitude but
pointing in the same direction. Euclidean distance would unfairly penalise
the shorter document. For high-dimensional sparse-ish data, cosine is
standard practice.

**3. Threshold as a Hyperparameter**
The 0.35 threshold is a design choice. In a production system you'd evaluate
it using precision/recall on a labelled dataset of (resume, job, relevant?)
triples. Lowering it increases recall but reduces precision; raising it does
the opposite. The fallback to external platforms when below threshold prevents
false positives from damaging user trust.

**4. Batch Encoding Optimisation**
Naively encoding N jobs in a loop = N model forward passes.
Our implementation uses `model.encode(job_texts, batch_size=32)` to process
all jobs in a single batched call, then vectorises all cosine similarities
with `sklearn.metrics.pairwise.cosine_similarity`. This is O(1) model calls
regardless of job count.

**5. Limitations & Future Work**
- Embeddings are recomputed on every query (could pre-compute and cache)
- No user authentication or multi-tenant isolation
- Could add FAISS approximate nearest-neighbour for 100k+ job scale
- Hybrid approach: keyword pre-filter → semantic re-rank
- Fine-tune SBERT on domain-specific (resume, job) sentence pairs

---

## 📚 References

- Reimers, N., & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*. EMNLP. https://arxiv.org/abs/1908.10084
- Devlin, J. et al. (2018). *BERT: Pre-training of Deep Bidirectional Transformers*. https://arxiv.org/abs/1810.04805
- Hugging Face Sentence-Transformers: https://www.sbert.net/
