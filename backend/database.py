import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://admin:password123@localhost:5432/resumes_db"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency for yielding database sessions with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and pgvector extension."""
    with engine.begin() as conn:
        # Enable pgvector extension if using PostgreSQL
        if "postgresql" in DATABASE_URL:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            except Exception as e:
                print(f"Notice: pgvector extension creation check: {e}")
        Base.metadata.create_all(bind=conn)
