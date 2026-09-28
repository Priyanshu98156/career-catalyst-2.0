# Multi-Tenant AI Resume SaaS: Architecture & Implementation Roadmap

## 1. Executive Summary & Vision
This platform is a **multi-tenant AI-driven SaaS** that generates tailored, ATS-optimized resumes targeted at specific Job Descriptions (JDs).
Users can provide their profile data in two ways:
1. **Interactive Form:** Filling in personal info, career history, education, and master project bullets.
2. **Resume Upload (PDF/DOCX):** Uploading an existing resume, which is parsed and mapped into the platform automatically.

When a user submits a target Job Description, the system uses **LangChain and RAG (Retrieval-Augmented Generation)** to fetch the most relevant career achievements and synthesize a customized resume that highlights target keywords without hallucinating past experience.

---

## 2. High-Level Architecture

```mermaid
graph TD
    subgraph "1. Ingestion Layer"
        A1[User Form Input] --> C[Profile Ingestion Service]
        A2[Uploaded Resume PDF/DOCX] --> B[LangChain Parser & Extraction]
        B --> C
    end

    subgraph "2. Multi-Tenant Storage & Vector Store"
        C --> D[(PostgreSQL + pgvector)]
        D -. Metadata Filtered (tenant_id, user_id) .-> E[(Isolated Vectors)]
    end

    subgraph "3. RAG Tailoring Pipeline"
        F[Target Job Description] --> G[LangChain JD Analyzer]
        G --> H[RAG Retriever: pgvector Top-K Bullets]
        E --> H
        H --> I[LangChain Resume Synthesizer]
        I --> J[Structured Resume JSON / LaTeX]
    end

    subgraph "4. Output & Export"
        J --> K[Interactive Live Preview (React)]
        J --> L[PDF Generation / LaTeX Compiler]
    end
```

---

## 3. Why RAG for Resume Generation?

### The Challenge with Basic Prompting:
- **Hallucination:** General LLMs often create fake experiences or claim expertise the user does not possess.
- **Context Dilution:** Experienced candidates with 20+ project bullet points and many skills can overwhelm single prompt contexts, leading to generic outputs.

### The RAG Solution:
1. **Master Knowledge Vault:** All user experiences, quantified accomplishments, and skills are stored as individual chunks in `pgvector` with rich metadata.
2. **Target JD as Query:** The JD is analyzed for key technical skills, responsibilities, and seniority level.
3. **Semantic Retrieval:** `pgvector` retrieves the **top-K most relevant real experiences** matching the JD requirements.
4. **STAR Rewriting & Formatting:** LangChain rewrites retrieved real experiences using the **STAR format** (Situation, Task, Action, Result) and ATS-friendly keywords while strictly adhering to real history.

---

## 4. LangChain & RAG Implementation Pipeline

### Step 4.1: Resume Upload & Extraction (Unstructured to Structured)
Extract raw text from PDF/DOCX into a strictly-typed Pydantic profile schema:

```python
# backend/services/parser_service.py
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List, Optional

class ExperienceItem(BaseModel):
    company: str
    role: str
    duration: str
    bullet_points: List[str]
    skills_used: List[str]

class ParsedProfile(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    education: List[dict] = []
    experiences: List[ExperienceItem] = []
    projects: List[dict] = []

def parse_resume_document(file_path: str) -> ParsedProfile:
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    raw_text = "\n".join([doc.page_content for doc in docs])
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    structured_llm = llm.with_structured_output(ParsedProfile)
    
    prompt = f"""
    Extract all resume information from the following text into the structured format.
    Do not invent information not present in the text.
    
    Resume Text:
    {raw_text}
    """
    return structured_llm.invoke(prompt)
```

---

### Step 4.2: Vector Store Ingestion (`pgvector`)
Store candidate bullet points in PostgreSQL with `tenant_id` and `user_id` metadata:

```python
# backend/services/vector_service.py
from langchain_postgres import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document

embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
CONNECTION_STRING = "postgresql+psycopg://admin:password123@localhost:5432/resumes_db"

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="user_experiences",
    connection=CONNECTION_STRING,
    use_jsonb=True,
)

def ingest_user_bullets(tenant_id: str, user_id: str, bullets: list[dict]):
    """
    bullets = [
        {"text": "Architected event-driven microservice in Go reducing p99 latency by 45%", "skills": ["Go", "Kafka", "Docker"]}
    ]
    """
    docs = [
        Document(
            page_content=item["text"],
            metadata={
                "tenant_id": tenant_id,
                "user_id": user_id,
                "skills": item.get("skills", []),
                "type": "experience_bullet"
            }
        )
        for item in bullets
    ]
    vector_store.add_documents(docs)
```

---

### Step 4.3: JD Analysis & Vector Retrieval
Extract required skills and responsibilities from the target JD, then retrieve the best candidate bullets:

```python
# backend/services/rag_service.py
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from typing import List
from backend.services.vector_service import vector_store

class JDAnalysis(BaseModel):
    job_title: str
    primary_skills: List[str]
    core_responsibilities: List[str]
    keywords_to_target: List[str]

def analyze_jd(job_description: str) -> JDAnalysis:
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    structured_llm = llm.with_structured_output(JDAnalysis)
    
    prompt = f"Analyze the following Job Description and identify core requirements:\n\n{job_description}"
    return structured_llm.invoke(prompt)

def retrieve_relevant_bullets(tenant_id: str, user_id: str, jd_analysis: JDAnalysis, top_k: int = 8) -> list[str]:
    search_query = f"{jd_analysis.job_title} " + " ".join(jd_analysis.primary_skills)
    
    # Metadata filter guarantees tenant & user isolation
    filter_criteria = {
        "tenant_id": tenant_id,
        "user_id": user_id
    }
    
    results = vector_store.similarity_search(
        query=search_query,
        k=top_k,
        filter=filter_criteria
    )
    return [doc.page_content for doc in results]
```

---

### Step 4.4: Tailored Resume Synthesis (LangChain LCEL)

```python
# backend/services/synthesis_service.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

def generate_tailored_resume(job_description: str, retrieved_bullets: list[str], user_profile: dict) -> dict:
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an elite technical resume strategist. 
Your goal is to tailor the candidate's real experiences to match the target Job Description.

CRITICAL RULES:
1. Do NOT invent fake companies, metrics, or technologies.
2. Optimize bullet points using strong action verbs, quantifiable metrics, and ATS keywords from the JD.
3. Structure the output as valid JSON matching the resume structure.
"""),
        ("user", """
Target Job Description:
{jd}

Candidate's Real Experiences (Retrieved from Knowledge Vault):
{bullets}

Candidate Profile Info:
{profile}

Generate the final tailored resume in structured JSON.
""")
    ])
    
    chain = prompt | llm | JsonOutputParser()
    return chain.invoke({
        "jd": job_description,
        "bullets": "\n- ".join(retrieved_bullets),
        "profile": user_profile
    })
```

---

## 5. Multi-Tenancy Design

1. **Tenant Identification & Auth:**
   - Every API request carries a JWT containing `tenant_id` and `user_id`.
   - FastAPI dependencies validate the token and inject `tenant_id` into route handlers.
2. **Database Isolation:**
   - Relational Tables: Each table (`users`, `profiles`, `resumes`, `templates`) has a `tenant_id` column.
   - PostgreSQL Row Level Security (RLS) can be enabled to enforce multi-tenant isolation at the engine level.
3. **Vector Store Isolation:**
   - All `pgvector` inserts and queries must include `tenant_id` and `user_id` inside document metadata filters.

---

## 6. Cloud Hosting on Oracle Cloud (OCI) Free Tier

### OCI Always Free Compute Specs:
- **Ampere A1 Compute:** Up to 4 OCPUs and 24 GB RAM (free indefinitely).
- **Storage:** 200 GB Total Block Volume.

### Production Architecture on OCI:

```
[Internet]
    │
    ▼ HTTPS (443)
[Nginx Reverse Proxy + Let's Encrypt SSL]
    ├───> /api/*  ──> [FastAPI Backend Container (Python)]
    │                     ├──> [PostgreSQL + pgvector Container]
    │                     └──> [Google Gemini API / LangChain]
    └───> /*      ──> [Frontend Static Build (React / Vite)]
```

### Deployment Steps:
1. **Create OCI Instance:** Ubuntu 22.04/24.04 (ARM Ampere A1).
2. **Firewall & Security Rules:** Open Ingress Ports `80` (HTTP) and `443` (HTTPS) in OCI VCN Ingress Rules and VM `iptables`/`ufw`.
3. **Install Docker:**
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose
   sudo usermod -aG docker ubuntu
   ```
4. **Deploy Stack:**
   ```bash
   git clone <repo_url>
   cd CareerCatalyst_v2
   # configure .env with GEMINI_API_KEY, DB credentials
   docker compose up -d --build
   ```

---

## 7. Recommended Implementation Milestones

- [x] **Milestone 1: Database Models & Migrations**
  - SQLAlchemy models for Users, Profiles, Master Bullets, Resumes.
  - Setup pgvector extension inside PostgreSQL container.
- [x] **Milestone 2: LangChain Parser & Ingestion Service**
  - PyPDFLoader + Pydantic structured output extractor.
  - Form ingestion endpoint & embedding generator.
- [x] **Milestone 3: RAG Retrieval & Tailoring Engine**
  - JD keyword extractor.
  - pgvector similarity search with tenant filtering.
  - Resume synthesis chain.
- [x] **Milestone 4: Frontend UI & Live Preview**
  - Resume upload component + profile wizard form.
  - JD input & side-by-side tailored resume preview.
  - PDF export (LaTeX or HTML-to-PDF).
- [x] **Milestone 5: Production & OCI Deployment**
  - Multi-container `docker-compose.prod.yml`.
  - Nginx reverse proxy + SSL configuration.
