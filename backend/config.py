import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# AI Model Configurations (Configurable via .env)
# ---------------------------------------------------------------------------
# Default LLM model for parsing, JD analysis, and resume synthesis
GEMINI_CHAT_MODEL: str = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")

# Default Embedding model for pgvector semantic search
GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")

# ---------------------------------------------------------------------------
# Database & Vector Store Configurations
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://admin:password123@localhost:5432/resumes_db",
)

VECTOR_COLLECTION_NAME: str = os.getenv("VECTOR_COLLECTION_NAME", "user_experiences")

# ---------------------------------------------------------------------------
# Application Settings
# ---------------------------------------------------------------------------
APP_ENV: str = os.getenv("APP_ENV", "development")
APP_VERSION: str = "2.0.0"
