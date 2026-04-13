"""
tests/test_platform.py — Test suite for the AI Job Recommendation Platform.

WHY THIS EXISTS:
Tests prove your system works correctly and make it easy to catch
regressions when you change code. For an MSc project, a test suite
demonstrates professional software engineering practice.

Running tests:
  cd backend
  pytest ../tests/test_platform.py -v

Requirements:
  pip install pytest httpx
"""

import os
import sys
import pytest
import tempfile

# Make sure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── In-memory SQLite for tests (does not touch the real database) ──────────────
TEST_DATABASE_URL = "sqlite:///./test_job_platform.db"

# Import app AFTER path setup
from main import app
from database import Base, get_db
from models import Job, Resume

# Create a test-specific database engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override the database dependency to use our test database."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply the override so API calls hit the test DB, not production
app.dependency_overrides[get_db] = override_get_db

# Create all tables in the test database
Base.metadata.create_all(bind=test_engine)

# FastAPI test client (sends real HTTP requests without a running server)
client = TestClient(app)


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES — reusable setup helpers
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def clean_database():
    """Wipe all tables before each test to guarantee isolation."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield  # test runs here
    # teardown (nothing needed — next test will reset anyway)


@pytest.fixture
def sample_job_payload():
    return {
        "title": "Machine Learning Engineer",
        "company": "TestCorp",
        "skills": "Python, PyTorch, NLP",
        "experience": "2-4 years",
        "description": (
            "We need a machine learning engineer with deep expertise in Python, "
            "PyTorch, and natural language processing. You will design transformer "
            "models, fine-tune BERT, and deploy ML pipelines at scale."
        )
    }


@pytest.fixture
def created_job(sample_job_payload):
    """Creates a job and returns the response JSON."""
    resp = client.post("/jobs", json=sample_job_payload)
    assert resp.status_code == 200
    return resp.json()


@pytest.fixture
def sample_pdf_path():
    """Creates a minimal valid PDF in a temp file for upload tests."""
    # Minimal PDF structure — enough for PyMuPDF to open successfully
    pdf_content = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
  /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj << /Length 120 >>
stream
BT /F1 12 Tf 50 750 Td
(Python Machine Learning Engineer Resume) Tj 0 -20 Td
(Skills: Python, TensorFlow, NLP, Data Science) Tj
ET
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000000446 00000 n
trailer << /Size 6 /Root 1 0 R >>
startxref
525
%%EOF"""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_content)
        return f.name


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestHealth:
    def test_health_endpoint_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_response_structure(self):
        resp = client.get("/health")
        data = resp.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "model" in data
        assert "version" in data

    def test_root_returns_html(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]


# ══════════════════════════════════════════════════════════════════════════════
# JOB CREATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestJobCreation:
    def test_create_job_success(self, sample_job_payload):
        resp = client.post("/jobs", json=sample_job_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == sample_job_payload["title"]
        assert data["company"] == sample_job_payload["company"]
        assert "id" in data
        assert isinstance(data["id"], int)

    def test_create_job_minimal_fields(self):
        """Only title and description are required."""
        resp = client.post("/jobs", json={
            "title": "Data Analyst",
            "description": "Analyse data using SQL and Python."
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Data Analyst"
        assert data["company"] is None
        assert data["skills"] is None

    def test_create_job_missing_title_fails(self):
        resp = client.post("/jobs", json={"description": "Some description"})
        assert resp.status_code == 422  # Pydantic validation error

    def test_create_job_missing_description_fails(self):
        resp = client.post("/jobs", json={"title": "Engineer"})
        assert resp.status_code == 422

    def test_create_multiple_jobs(self, sample_job_payload):
        for i in range(3):
            payload = {**sample_job_payload, "title": f"Job {i}"}
            resp = client.post("/jobs", json=payload)
            assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# JOB LISTING & RETRIEVAL TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestJobRetrieval:
    def test_list_jobs_empty(self):
        resp = client.get("/jobs")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_jobs_after_creation(self, sample_job_payload):
        client.post("/jobs", json=sample_job_payload)
        resp = client.get("/jobs")
        assert resp.status_code == 200
        jobs = resp.json()
        assert len(jobs) == 1
        assert jobs[0]["title"] == sample_job_payload["title"]

    def test_get_job_by_id(self, created_job):
        job_id = created_job["id"]
        resp = client.get(f"/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == job_id

    def test_get_nonexistent_job_returns_404(self):
        resp = client.get("/jobs/99999")
        assert resp.status_code == 404

    def test_delete_job(self, created_job):
        job_id = created_job["id"]
        # Delete it
        del_resp = client.delete(f"/jobs/{job_id}")
        assert del_resp.status_code == 200
        # Confirm it's gone
        get_resp = client.get(f"/jobs/{job_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_job_returns_404(self):
        resp = client.delete("/jobs/99999")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# RESUME UPLOAD TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestResumeUpload:
    def test_upload_valid_pdf(self, sample_pdf_path):
        with open(sample_pdf_path, "rb") as f:
            resp = client.post(
                "/resumes",
                files={"file": ("test_resume.pdf", f, "application/pdf")}
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["filename"] == "test_resume.pdf"

    def test_upload_non_pdf_rejected(self):
        resp = client.post(
            "/resumes",
            files={"file": ("resume.txt", b"plain text content", "text/plain")}
        )
        assert resp.status_code == 400
        assert "PDF" in resp.json()["detail"]

    def test_upload_docx_rejected(self):
        resp = client.post(
            "/resumes",
            files={"file": ("resume.docx", b"fake docx bytes", "application/vnd.openxmlformats")}
        )
        assert resp.status_code == 400

    def test_list_resumes_empty(self):
        resp = client.get("/resumes")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_resumes_after_upload(self, sample_pdf_path):
        with open(sample_pdf_path, "rb") as f:
            client.post("/resumes", files={"file": ("cv.pdf", f, "application/pdf")})
        resp = client.get("/resumes")
        assert len(resp.json()) == 1

    def test_get_resume_text_preview(self, sample_pdf_path):
        with open(sample_pdf_path, "rb") as f:
            upload_resp = client.post(
                "/resumes",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        resume_id = upload_resp.json()["id"]
        resp = client.get(f"/resumes/{resume_id}/text")
        assert resp.status_code == 200
        data = resp.json()
        assert "extracted_text" in data
        assert "word_count" in data
        assert "char_count" in data

    def test_get_nonexistent_resume_returns_404(self):
        resp = client.get("/resumes/99999")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# MATCHING TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestMatching:
    def test_match_nonexistent_resume_returns_404(self):
        resp = client.get("/match/99999")
        assert resp.status_code == 404

    def test_match_with_no_jobs_returns_suggestions(self, sample_pdf_path):
        """When no jobs exist, should return platform suggestions."""
        with open(sample_pdf_path, "rb") as f:
            upload = client.post("/resumes", files={"file": ("cv.pdf", f, "application/pdf")})
        resume_id = upload.json()["id"]

        resp = client.get(f"/match/{resume_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["suggestions"] is not None
        assert len(data["suggestions"]) > 0

    def test_match_returns_response_structure(self, sample_pdf_path, created_job):
        """Match response must have the correct schema."""
        with open(sample_pdf_path, "rb") as f:
            upload = client.post("/resumes", files={"file": ("cv.pdf", f, "application/pdf")})
        resume_id = upload.json()["id"]

        resp = client.get(f"/match/{resume_id}")
        assert resp.status_code == 200
        data = resp.json()

        assert "resume_id" in data
        assert "matches" in data
        assert "message" in data
        assert data["resume_id"] == resume_id

    def test_match_scores_are_between_0_and_1(self, sample_pdf_path, created_job):
        """Cosine similarity must always be in [0, 1]."""
        with open(sample_pdf_path, "rb") as f:
            upload = client.post("/resumes", files={"file": ("cv.pdf", f, "application/pdf")})
        resume_id = upload.json()["id"]

        resp = client.get(f"/match/{resume_id}")
        data = resp.json()

        for match in data["matches"]:
            assert 0.0 <= match["score"] <= 1.0, f"Score out of range: {match['score']}"

    def test_match_results_sorted_descending(self, sample_pdf_path):
        """Results must be sorted highest score first."""
        # Create multiple jobs with varying relevance
        jobs = [
            {"title": "Python ML Engineer", "description": "Machine learning with Python, PyTorch, NLP, deep learning, transformers"},
            {"title": "Chef", "description": "Prepare gourmet meals, manage kitchen inventory, supervise culinary staff"},
            {"title": "Data Scientist", "description": "Statistical analysis, Python programming, machine learning algorithms"},
        ]
        for j in jobs:
            client.post("/jobs", json=j)

        with open(sample_pdf_path, "rb") as f:
            upload = client.post("/resumes", files={"file": ("cv.pdf", f, "application/pdf")})
        resume_id = upload.json()["id"]

        resp = client.get(f"/match/{resume_id}")
        data = resp.json()
        scores = [m["score"] for m in data["matches"]]

        # Verify descending order
        assert scores == sorted(scores, reverse=True), "Results are not sorted by score"

    def test_match_score_percent_format(self, sample_pdf_path, created_job):
        """score_percent must end with '%'."""
        with open(sample_pdf_path, "rb") as f:
            upload = client.post("/resumes", files={"file": ("cv.pdf", f, "application/pdf")})
        resume_id = upload.json()["id"]

        resp = client.get(f"/match/{resume_id}")
        for match in resp.json()["matches"]:
            assert match["score_percent"].endswith("%")


# ══════════════════════════════════════════════════════════════════════════════
# AI MODULE UNIT TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestAIModules:
    def test_get_embedding_returns_array(self):
        from ai.job_matcher import get_embedding
        embedding = get_embedding("Python developer with machine learning skills")
        assert embedding is not None
        assert len(embedding) == 384  # all-MiniLM-L6-v2 produces 384-dim vectors

    def test_similar_texts_have_high_cosine_similarity(self):
        """The core semantic matching assumption — similar text → high score."""
        from ai.job_matcher import get_embedding
        from sklearn.metrics.pairwise import cosine_similarity

        text_a = "Python machine learning engineer with NLP experience"
        text_b = "ML developer skilled in Python and natural language processing"

        emb_a = get_embedding(text_a).reshape(1, -1)
        emb_b = get_embedding(text_b).reshape(1, -1)
        score = cosine_similarity(emb_a, emb_b)[0][0]

        assert score > 0.7, f"Expected high similarity for semantically similar texts, got {score:.3f}"

    def test_dissimilar_texts_have_low_cosine_similarity(self):
        """Unrelated texts should produce low similarity scores."""
        from ai.job_matcher import get_embedding
        from sklearn.metrics.pairwise import cosine_similarity

        text_a = "Python machine learning engineer with deep learning expertise"
        text_b = "Executive pastry chef specialising in French cuisine and desserts"

        emb_a = get_embedding(text_a).reshape(1, -1)
        emb_b = get_embedding(text_b).reshape(1, -1)
        score = cosine_similarity(emb_a, emb_b)[0][0]

        assert score < 0.5, f"Expected low similarity for unrelated texts, got {score:.3f}"

    def test_pdf_parser_raises_on_missing_file(self):
        from ai.resume_parser import extract_text_from_pdf
        with pytest.raises(FileNotFoundError):
            extract_text_from_pdf("/nonexistent/path/resume.pdf")

    def test_pdf_parser_extracts_text(self, sample_pdf_path):
        from ai.resume_parser import extract_text_from_pdf
        text = extract_text_from_pdf(sample_pdf_path)
        assert isinstance(text, str)
        assert len(text) > 0


# ══════════════════════════════════════════════════════════════════════════════
# CLEANUP
# ══════════════════════════════════════════════════════════════════════════════

def teardown_module(module):
    """Remove test database file after all tests finish."""
    test_db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "backend", "test_job_platform.db"
    )
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    # Also clean up any test PDFs from uploads/
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "uploads")
    if os.path.exists(uploads_dir):
        for f in os.listdir(uploads_dir):
            if f.startswith("test") or f.startswith("cv"):
                try:
                    os.remove(os.path.join(uploads_dir, f))
                except Exception:
                    pass


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS & HISTORY TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestAnalytics:
    def test_analytics_empty_database(self):
        """Analytics should return zeros when DB is empty."""
        resp = client.get("/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_resumes"] == 0
        assert data["total_jobs"] == 0
        assert data["total_matches_run"] == 0

    def test_analytics_after_job_creation(self, sample_job_payload):
        client.post("/jobs", json=sample_job_payload)
        resp = client.get("/analytics")
        assert resp.json()["total_jobs"] == 1

    def test_analytics_structure(self):
        resp = client.get("/analytics")
        data = resp.json()
        required_keys = ["total_resumes","total_jobs","total_matches_run",
                         "avg_top_score","high_matches","medium_matches",
                         "low_matches","top_matched_jobs"]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"

    def test_history_empty(self):
        resp = client.get("/history")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_history_populated_after_match(self, sample_pdf_path, sample_job_payload):
        """Running a match should create MatchHistory rows."""
        client.post("/jobs", json=sample_job_payload)
        with open(sample_pdf_path,"rb") as f:
            upload = client.post("/resumes", files={"file":("cv.pdf",f,"application/pdf")})
        resume_id = upload.json()["id"]
        client.get(f"/match/{resume_id}")   # triggers history save

        resp = client.get("/history")
        assert resp.status_code == 200
        history = resp.json()
        assert len(history) >= 1
        assert history[0]["resume_id"] == resume_id

    def test_history_filter_by_resume_id(self, sample_pdf_path, sample_job_payload):
        client.post("/jobs", json=sample_job_payload)
        # Upload two resumes and run matches for both
        for name in ["cv1.pdf","cv2.pdf"]:
            with open(sample_pdf_path,"rb") as f:
                up = client.post("/resumes", files={"file":(name,f,"application/pdf")})
            client.get(f"/match/{up.json()['id']}")

        all_hist = client.get("/history").json()
        first_id = all_hist[0]["resume_id"]
        filtered = client.get(f"/history?resume_id={first_id}").json()
        assert all(h["resume_id"] == first_id for h in filtered)

    def test_clear_history(self, sample_pdf_path, sample_job_payload):
        client.post("/jobs", json=sample_job_payload)
        with open(sample_pdf_path,"rb") as f:
            up = client.post("/resumes", files={"file":("cv.pdf",f,"application/pdf")})
        client.get(f"/match/{up.json()['id']}")
        assert len(client.get("/history").json()) >= 1

        client.delete("/history")
        assert client.get("/history").json() == []

    def test_match_response_includes_resume_name(self, sample_pdf_path, sample_job_payload):
        """MatchResponse should carry the resume filename."""
        client.post("/jobs", json=sample_job_payload)
        with open(sample_pdf_path,"rb") as f:
            up = client.post("/resumes", files={"file":("myresume.pdf",f,"application/pdf")})
        resp = client.get(f"/match/{up.json()['id']}").json()
        assert resp["resume_name"] == "myresume.pdf"

    def test_match_response_includes_total_compared(self, sample_pdf_path):
        """total_jobs_compared should reflect the number of jobs in DB."""
        for i in range(3):
            client.post("/jobs", json={"title":f"Job {i}","description":f"Description for job {i} involving Python and data."})
        with open(sample_pdf_path,"rb") as f:
            up = client.post("/resumes", files={"file":("cv.pdf",f,"application/pdf")})
        resp = client.get(f"/match/{up.json()['id']}").json()
        assert resp["total_jobs_compared"] == 3

    def test_above_threshold_flag_in_matches(self, sample_pdf_path, sample_job_payload):
        """Each match item should carry the above_threshold boolean."""
        client.post("/jobs", json=sample_job_payload)
        with open(sample_pdf_path,"rb") as f:
            up = client.post("/resumes", files={"file":("cv.pdf",f,"application/pdf")})
        resp = client.get(f"/match/{up.json()['id']}").json()
        for match in resp["matches"]:
            assert "above_threshold" in match
            assert isinstance(match["above_threshold"], bool)
