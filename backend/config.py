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

# ---------------------------------------------------------------------------
# JWT & Authentication Settings (Double Token Strategy)
# ---------------------------------------------------------------------------
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "careercatalyst_super_secret_jwt_key_change_in_production")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
