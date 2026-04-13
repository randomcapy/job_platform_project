# ──────────────────────────────────────────────────────────────────────────────
# Makefile — Common development tasks for ResumeMatch AI
#
# WHY A MAKEFILE?
#   Instead of remembering long commands, you type short memorable targets:
#     make run       → start the server
#     make test      → run the full test suite
#     make seed      → populate sample jobs
#     make docker    → build and start with Docker
#
# USAGE:  make <target>
# ──────────────────────────────────────────────────────────────────────────────

.PHONY: install run test seed lint clean docker docker-down help

# Default target — show help
help:
	@echo ""
	@echo "  ResumeMatch AI — Available Commands"
	@echo "  ─────────────────────────────────────────────────────"
	@echo "  make install    Install all Python dependencies"
	@echo "  make run        Start the FastAPI development server"
	@echo "  make test       Run the full pytest test suite"
	@echo "  make seed       Populate the database with sample jobs"
	@echo "  make lint       Run code style checks (flake8)"
	@echo "  make clean      Remove __pycache__, .pyc files, test DB"
	@echo "  make docker     Build and start with Docker Compose"
	@echo "  make docker-down Stop and remove Docker containers"
	@echo "  ─────────────────────────────────────────────────────"
	@echo ""

install:
	pip install -r requirements.txt
	@echo "✅  Dependencies installed."

run:
	cd backend && python run.py

test:
	cd backend && pytest ../tests/ -v --tb=short

seed:
	@echo "Starting server in background..."
	cd backend && uvicorn main:app --host 127.0.0.1 --port 8000 &
	@sleep 5
	python seed_jobs.py
	@echo "✅  Sample jobs seeded."

lint:
	flake8 backend/ --max-line-length=100 --exclude=__pycache__

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -f backend/job_platform.db backend/test_job_platform.db
	@echo "✅  Cleaned."

docker:
	docker-compose up --build

docker-down:
	docker-compose down
