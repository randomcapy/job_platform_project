"""
database.py — Sets up the SQLite database connection using SQLAlchemy.

WHY THIS EXISTS:
SQLAlchemy is an ORM (Object-Relational Mapper). Instead of writing raw SQL,
we define Python classes that map to database tables. SQLite is used because
it's serverless, file-based, and perfect for demos and MSc projects — no
separate DB installation required.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database file will be created in the backend folder
DATABASE_URL = "sqlite:///./job_platform.db"

# create_engine sets up the connection to SQLite
# check_same_thread=False is required for SQLite with FastAPI's async behavior
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# SessionLocal is a factory for database sessions (one per request)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class for all our ORM models
Base = declarative_base()


def get_db():
    """
    Dependency function used by FastAPI routes.
    Yields a database session and ensures it closes after each request.
    This is the standard pattern for safe DB session management.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
