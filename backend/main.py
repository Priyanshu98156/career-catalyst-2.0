import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure workspace root is in sys.path so 'backend' package imports resolve from any CWD
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.routes.profile_router import router as profile_router
from backend.routes.resume_router import router as resume_router
from backend.routes.auth_router import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schemas on startup if database is accessible
    try:
        init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database connection deferred/not ready: {e}")
    yield


app = FastAPI(
    title="CareerCatalyst API",
    description="Multi-tenant AI-driven SaaS for ATS-optimized resume tailoring",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration for frontend dev & production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount domain routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(resume_router)


@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "active", "message": "CareerCatalyst Backend is running"}
