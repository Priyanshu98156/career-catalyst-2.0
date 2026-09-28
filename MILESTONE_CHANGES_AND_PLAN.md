# CareerCatalyst v2 — Changes Log & Milestone 2 Implementation Plan

---

## Part 1: What Changed in `backend/main.py`

### 1.1 Before & After Comparison

#### **Original `backend/main.py`**
```python
from fastapi import FastAPI

app = FastAPI(title= "CareerCatalyst API", description= "API")

@app.get("/health")
def health_check():
    return {"status": "active", "message" : "Backend is running"}
```

#### **Updated `backend/main.py`**
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db


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


@app.get("/health")
def health_check():
    return {"status": "active", "message": "CareerCatalyst Backend is running"}
```

### 1.2 Summary of Additions & Why They Were Added
1. **`asynccontextmanager` + `lifespan` handler:**
   - Automatically initializes the database tables and ensures the `pgvector` extension is created on startup without blocking startup if the DB container isn't ready.
2. **CORS Middleware (`CORSMiddleware`):**
   - Allows the React/Vite frontend (running on `localhost:5173`) to communicate with the FastAPI backend (running on `localhost:8000`) without being blocked by browser cross-origin policies.
3. **API Metadata:**
   - Added standard versioning and descriptive titles for FastAPI Swagger UI (`/docs`).

---

## Part 2: Overview of All Milestone 1 Additions

| File | Purpose |
| :--- | :--- |
| **`backend/database.py`** | SQLAlchemy 2.0 engine, connection pool with `pre_ping`, session factory `SessionLocal`, `get_db()` dependency for route handlers, and `init_db()` table/extension bootstrapper. |
| **`backend/models/base.py`** | Common base helpers (`generate_uuid`, `get_utc_now`, `Base`). |
| **`backend/models/user.py`** | Multi-tenant `User` model (auth, role, relationships). |
| **`backend/models/profile.py`** | `Profile` model (contact details, summary, education JSON, skills JSON). |
| **`backend/models/experience.py`** | `Experience` and `MasterBullet` models (work history & granular bullet points). |
| **`backend/models/job.py`** | `JobDescription` model (target JD text, extracted primary skills & keywords). |
| **`backend/models/resume.py`** | `TailoredResume` model (synthesized JSON schema, match score, raw LaTeX). |
| **`backend/models/schemas.py`** | Pydantic validation schemas for Auth, Resume Parsing (`ParsedProfile`), Bullet CRUD, and RAG Resume Tailoring. |
| **`backend/models/__init__.py`** | Central module package exports for clean imports across the application. |
| **`backend/requirements.txt`** | Dependency updates including `pydantic[email]`, `email-validator`, `pypdf`, `python-multipart`, `psycopg[binary]`, `pgvector`, and `langchain-google-genai`. |

---

## Part 3: Milestone 2 Implementation (Completed)

| Module / File | Responsibility & Design Decisions | SOLID / DRY Principles Applied |
| :--- | :--- | :--- |
| **`backend/ai_client.py`** | Central factory for Gemini LLMs and text embeddings (`get_chat_model`, `get_embeddings_model`). Normalizes keys (`GEMINI_API_KEY`, `GOOGLE_API_KEY`, `GEMINIAPIKEY`). | **SRP**: Single module for AI provider configuration.<br>**DRY**: Cached singletons via `@lru_cache` to avoid duplicate client instances. |
| **`backend/services/parser_service.py`** | In-memory text extraction from PDF streams (`extract_text_from_pdf`) and Gemini structured output extraction (`parse_resume_text` / `parse_resume_document`). | **SRP**: Only handles document parsing and LLM structured extraction.<br>**Zero file leakage**: Operates directly on byte streams without temporary files. |
| **`backend/services/vector_service.py`** | Multi-tenant `PGVector` document store manager (`ingest_user_bullets`, `search_user_bullets`). | **Tenant Isolation**: Every document stamped with `tenant_id` & `user_id`. Similarity search enforces metadata filtering. |
| **`backend/services/profile_service.py`** | Domain business logic (`create_or_update_profile`, `save_parsed_profile_to_db`, `add_user_master_bullets`, `get_user_master_bullets`). | **DIP**: Depends on database session abstractions.<br>**Graceful Degradation**: Protects relational saves if vector connection is offline. |
| **`backend/routes/profile_router.py`** | REST endpoints: `/upload-resume`, `/save`, `/`, `/bullets`. Injects tenant and user context from headers. | **SOC**: Separates HTTP transport/validation from underlying business logic. |
| **`backend/tests/test_milestone2.py`** | Automated test suite validating in-memory parsing, profile creation, hierarchy persistence, and bullet isolation. | **Testability**: Verifies services cleanly using isolated in-memory DB fixtures. |

---

## Part 4: Milestone 3 Implementation (Completed)

| Module / File | Responsibility & Design Decisions | SOLID / DRY Principles Applied |
| :--- | :--- | :--- |
| **`backend/services/rag_service.py`** | `analyze_job_description` extracts primary skills, responsibilities, and target ATS keywords. `retrieve_candidate_bullets` builds semantic query, queries `pgvector`, and provides relational DB fallback. | **Resilience**: Never fails if vector database is empty or starting up.<br>**Tenant Isolation**: Enforces tenant_id & user_id on all queries. |
| **`backend/services/synthesis_service.py`** | LangChain structured synthesis chain creating STAR-rewritten experiences, ATS score (0-100), matched/missing keywords, and compilable LaTeX source. | **Zero Hallucination**: Guardrailed prompt restricts LLM to candidate's real retrieved achievements. |
| **`backend/routes/resume_router.py`** | Endpoints: `POST /api/resume/analyze-jd`, `POST /api/resume/tailor`, `GET /api/resume/{resume_id}`, `GET /api/resume/history`. | **SOC**: Orchestrates RAG flow, persistence to `tailored_resumes` table, and API response serialization. |
| **`backend/tests/test_milestone3.py`** | Automated test suite verifying validation of empty inputs, candidate bullet retrieval with tenant isolation, and resume persistence. | **Testability**: Independent unit tests using isolated in-memory DB fixtures. All 7 tests pass. |

---

## Part 5: Milestone 4 Implementation (Completed)

| Component / File | Responsibility & Features |
| :--- | :--- |
| **`frontend/src/index.css`** | Complete cyber-dark glassmorphism design system, tokens, typography (Inter & Outfit), responsive utilities, and `@media print` styling for A4 resume generation. |
| **`frontend/src/services/api.ts`** | Centralized Axios API client configured with `X-Tenant-ID` headers and strictly typed interfaces for all profile, RAG, and tailoring endpoints. |
| **`frontend/src/components/Header.tsx`** | Sticky top navigation with active tab switches, tenant badge, and live backend connection pulse indicator. |
| **`frontend/src/components/ProfileVaultView.tsx`** | Drag-and-drop PDF resume uploader, automated Gemini extraction status, profile editor, skills manager, and Master Bullets Vault manager with pgvector sync. |
| **`frontend/src/components/JDTailoringView.tsx`** | Split-screen studio: Left side has JD paste area (with one-click "Load Sample Tech JD" button) and extracted requirements; Right side has ATS score gauge, matched/missing keyword badges, clean ATS printable resume view, tabbed LaTeX code view, and PDF export. |
| **`frontend/src/components/HistoryView.tsx`** | Full history cards for previously synthesized resumes, ATS scores, timestamps, and one-click LaTeX code copy. |
| **`frontend/src/App.tsx`** | Main application hub with background API health polling and smooth tabbed transitions. |

---

## Part 6: Milestone 5 Implementation (Completed)

| File | Purpose |
| :--- | :--- |
| **`backend/Dockerfile`** | Multi-stage production container for FastAPI with non-root security user and health check. |
| **`frontend/Dockerfile`** | Multi-stage production container building static assets with Node.js and serving via lightweight Nginx. |
| **`nginx/nginx.conf`** | High-performance reverse proxy routing `/api/*` to FastAPI and `/*` to React SPA, with gzip compression and SSL certbot readiness. |
| **`docker-compose.prod.yml`** | Production orchestration of `db` (pgvector), `backend`, `frontend`, and `nginx` reverse proxy. |
| **`DEPLOYMENT_OCI.md`** | Step-by-step production deployment guide for Oracle Cloud Infrastructure (OCI) Ampere A1 (ARM64) Always Free Compute with Let's Encrypt SSL. |


